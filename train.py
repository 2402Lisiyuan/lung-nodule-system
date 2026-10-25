"""
肺结节时序风险预测模型训练脚本

本脚本在原始版本基础上做了以下优化：
1. 保存逻辑改为基于训练损失（不再依赖验证AUC）
2. 每10个epoch强制保存一次
3. 训练结束后强制保存最终模型
4. validate 函数增加单一类别容错
5. 移除早停逻辑，避免因验证集不可靠而误触发

指令：
    python train.py --data_dir "E:/LUNA16/subset1" --anno_path "E:/LUNA16/annotations.csv" --epochs 30 --lr 1e-3 --batch_size 4 --output "pretrained.pth"
"""

import os
import csv
import argparse
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, random_split
from sklearn.metrics import roc_auc_score

from model import TemporalNoduleRiskNet
from dataset import LUNA16Dataset


# ============================================================
# 一、随机种子设置（保证实验可复现）
# ============================================================
def set_seed(seed=42):
    import random
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False


# ============================================================
# 二、训练一个 epoch
# ============================================================
def train_one_epoch(model, loader, optimizer, criterion, device):
    """训练一个epoch，返回平均损失和AUC"""
    model.train()
    total_loss = 0.0
    all_labels = []
    all_probs = []

    for current, prior, time_diff, label in loader:
        current = current.to(device)
        prior = prior.to(device)
        time_diff = time_diff.to(device)
        label = label.to(device)

        # 前向传播
        optimizer.zero_grad()
        output = model(current, prior, time_diff)

        # 计算损失
        loss = criterion(output, label)

        # 反向传播与参数更新
        loss.backward()
        optimizer.step()

        total_loss += loss.item() * current.size(0)
        all_labels.extend(label.cpu().numpy().flatten())
        all_probs.extend(output.detach().cpu().numpy().flatten())

    avg_loss = total_loss / len(loader.dataset)

    # AUC 容错：如果只有一个类别，返回 0.5
    if len(set(all_labels)) < 2:
        auc = 0.5
    else:
        try:
            auc = roc_auc_score(all_labels, all_probs)
        except ValueError:
            auc = 0.5
    return avg_loss, auc


# ============================================================
# 三、验证
# ============================================================
def validate(model, loader, criterion, device):
    """
    验证集评估，返回平均损失和AUC。
    若验证集为空或只包含单一类别，返回默认值，避免 NaN 或除零。
    """
    if len(loader.dataset) == 0:
        return 0.0, 0.5

    model.eval()
    total_loss = 0.0
    all_labels = []
    all_probs = []

    with torch.no_grad():
        for current, prior, time_diff, label in loader:
            current = current.to(device)
            prior = prior.to(device)
            time_diff = time_diff.to(device)
            label = label.to(device)

            output = model(current, prior, time_diff)
            loss = criterion(output, label)

            total_loss += loss.item() * current.size(0)
            all_labels.extend(label.cpu().numpy().flatten())
            all_probs.extend(output.cpu().numpy().flatten())

    avg_loss = total_loss / len(loader.dataset)

    # AUC 容错：如果只有一个类别，AUC 无定义
    if len(set(all_labels)) < 2:
        auc = 0.5
    else:
        try:
            auc = roc_auc_score(all_labels, all_probs)
        except ValueError:
            auc = 0.5
    return avg_loss, auc


# ============================================================
# 四、主训练流程
# ============================================================
def main(args):
    # 固定随机种子
    set_seed(42)

    # 设备选择
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"使用设备: {device}")

    # ---------- 数据准备 ----------
    print("准备数据...")
    dataset = LUNA16Dataset(
        data_dir=args.data_dir,
        anno_path=args.anno_path,
        patch_size=64,
        max_samples=args.max_samples,
        augment=False
    )
    print(f"总样本数: {len(dataset)}")

    if len(dataset) < 3:
        raise ValueError("样本数过少，无法划分训练/验证/测试集")

    # 划分训练/验证/测试集 (7:1.5:1.5)
    n = len(dataset)
    n_train = max(1, int(n * 0.7))
    n_val = max(1, int(n * 0.15))
    n_test = n - n_train - n_val
    if n_test < 1:
        n_test = 1
        n_train = n - n_val - n_test

    train_set, val_set, test_set = random_split(dataset, [n_train, n_val, n_test])

    # 训练集启用增强
    train_set.dataset.augment = True

    train_loader = DataLoader(train_set, batch_size=args.batch_size, shuffle=True, num_workers=8)
    val_loader = DataLoader(val_set, batch_size=args.batch_size, shuffle=False, num_workers=4)
    test_loader = DataLoader(test_set, batch_size=args.batch_size, shuffle=False, num_workers=4)

    print(f"训练集: {n_train} | 验证集: {n_val} | 测试集: {n_test}")

    # ---------- 模型初始化 ----------
    print("初始化模型...")
    model = TemporalNoduleRiskNet().to(device)

    # 如有预训练权重，加载它
    if args.pretrained and os.path.exists(args.pretrained):
        model.load_state_dict(torch.load(args.pretrained, map_location=device))
        print(f"已加载预训练权重: {args.pretrained}")

    # ---------- 损失函数与优化器 ----------
    criterion = nn.BCELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=args.lr, weight_decay=1e-5)
    scheduler = torch.optim.lr_scheduler.StepLR(optimizer, step_size=20, gamma=0.5)

    # ---------- 训练循环 ----------
    print("开始训练...")
    best_train_loss = float('inf')
    log_records = []

    # 初始化日志文件
    with open("training_log.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["epoch", "train_loss", "train_auc", "val_loss", "val_auc", "lr"])

    for epoch in range(args.epochs):
        # 训练
        train_loss, train_auc = train_one_epoch(model, train_loader, optimizer, criterion, device)

        # 验证（容错处理）
        val_loss, val_auc = validate(model, val_loader, criterion, device)

        # 更新学习率
        scheduler.step()
        current_lr = optimizer.param_groups[0]['lr']

        print(f"Epoch {epoch+1}/{args.epochs} | "
              f"Train Loss: {train_loss:.4f} AUC: {train_auc:.4f} | "
              f"Val Loss: {val_loss:.4f} AUC: {val_auc:.4f} | "
              f"LR: {current_lr:.6f}")

        # 记录日志
        log_records.append({
            "epoch": epoch + 1,
            "train_loss": train_loss,
            "train_auc": train_auc,
            "val_loss": val_loss,
            "val_auc": val_auc,
            "lr": current_lr
        })
        with open("training_log.csv", "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([epoch + 1, train_loss, train_auc, val_loss, val_auc, current_lr])

        # ========== 基于训练损失保存模型 ==========
        if train_loss < best_train_loss:
            best_train_loss = train_loss
            torch.save(model.state_dict(), args.output)
            print(f"  -> 保存模型 (Train Loss: {train_loss:.4f})")

        # 每10个epoch定期保存一次
        if (epoch + 1) % 10 == 0:
            torch.save(model.state_dict(), args.output)
            print(f"  -> 定期保存 (Epoch {epoch+1})")

    # ========== 训练结束后强制保存最终模型 ==========
    torch.save(model.state_dict(), args.output)
    print(f"\n训练结束，最终模型已保存至 {args.output}")

    # ---------- 测试集评估 ----------
    print("\n在测试集上评估...")
    model.load_state_dict(torch.load(args.output, map_location=device))
    test_loss, test_auc = validate(model, test_loader, criterion, device)
    print(f"测试集 | Loss: {test_loss:.4f} | AUC: {test_auc:.4f}")

    # ---------- 推理验证：确认输出随输入变化 ----------
    print("\n推理验证（确认模型输出随输入变化）:")
    model.eval()
    with torch.no_grad():
        risks = []
        for i in range(min(5, len(dataset))):
            current, prior, time_diff, label = dataset[i]
            current = current.unsqueeze(0).to(device)
            prior = prior.unsqueeze(0).to(device)
            time_diff = time_diff.unsqueeze(0).to(device)
            risk = model(current, prior, time_diff).item()
            risks.append(risk)
            print(f"  样本 {i+1}: 风险 = {risk:.4f} | 标签 = {label.item():.0f}")

        if len(risks) > 1 and max(risks) - min(risks) > 0.01:
            print(f"  -> 输出确实随输入变化 (差异 {max(risks) - min(risks):.4f})")
        else:
            print(f"  -> 警告：输出差异过小，模型可能未有效学习")


# ============================================================
# 五、入口
# ============================================================
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data_dir", type=str, default="E:/LUNA16/subset1", help="subset1 文件夹路径")
    parser.add_argument("--anno_path", type=str, default="E:/LUNA16/annotations.csv", help="标注文件路径")
    parser.add_argument("--output", type=str, default="pretrained.pth", help="模型保存路径")
    parser.add_argument("--pretrained", type=str, default=None, help="预训练权重路径")
    parser.add_argument("--batch_size", type=int, default=8)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--epochs", type=int, default=30)
    parser.add_argument("--max_samples", type=int, default=None, help="限制样本数，便于快速测试")
    args = parser.parse_args()

    main(args)