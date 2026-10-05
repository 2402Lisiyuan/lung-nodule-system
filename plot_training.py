import pandas as pd
import matplotlib.pyplot as plt
import os

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'PingFang SC']
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['font.size'] = 12

# 读取训练日志
log_path = "training_log.csv"
if not os.path.exists(log_path):
    raise FileNotFoundError(f"未找到训练日志: {log_path}")

df = pd.read_csv(log_path)

# 创建输出文件夹
os.makedirs("figures", exist_ok=True)

# ========== 图1：损失曲线 ==========
plt.figure(figsize=(8, 5))
plt.plot(df["epoch"], df["train_loss"], label="训练损失", color="#1f77b4", linewidth=2)
plt.plot(df["epoch"], df["val_loss"], label="验证损失", color="#ff7f0e", linewidth=2)
plt.xlabel("Epoch")
plt.ylabel("Loss")
plt.title("训练与验证损失曲线")
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig("figures/loss_curve.png", dpi=300, bbox_inches="tight")
plt.show()

# ========== 图2：AUC曲线 ==========
plt.figure(figsize=(8, 5))
plt.plot(df["epoch"], df["train_auc"], label="训练 AUC", color="#2ca02c", linewidth=2)
plt.plot(df["epoch"], df["val_auc"], label="验证 AUC", color="#d62728", linewidth=2)
plt.axhline(y=0.5, linestyle="--", color="gray", linewidth=1, label="随机水平 (0.5)")
plt.xlabel("Epoch")
plt.ylabel("AUC")
plt.title("训练与验证 AUC 曲线")
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig("figures/auc_curve.png", dpi=300, bbox_inches="tight")
plt.show()

# ========== 图3：学习率变化* ==========
if "lr" in df.columns:
    plt.figure(figsize=(8, 5))
    plt.plot(df["epoch"], df["lr"], color="#9467bd", linewidth=2)
    plt.xlabel("Epoch")
    plt.ylabel("Learning Rate")
    plt.title("学习率变化曲线")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig("figures/lr_curve.png", dpi=300, bbox_inches="tight")
    plt.show()

# ========== 图4：组合图（损失 + AUC） ==========
fig, ax1 = plt.subplots(figsize=(10, 6))

color1 = "#1f77b4"
ax1.set_xlabel("Epoch")
ax1.set_ylabel("Loss", color=color1)
ax1.plot(df["epoch"], df["train_loss"], color=color1, linestyle="-", label="训练损失")
ax1.plot(df["epoch"], df["val_loss"], color=color1, linestyle="--", label="验证损失")
ax1.tick_params(axis="y", labelcolor=color1)
ax1.legend(loc="upper left")
ax1.grid(True, alpha=0.2)

ax2 = ax1.twinx()
color2 = "#d62728"
ax2.set_ylabel("AUC", color=color2)
ax2.plot(df["epoch"], df["train_auc"], color=color2, linestyle="-", label="训练 AUC")
ax2.plot(df["epoch"], df["val_auc"], color=color2, linestyle="--", label="验证 AUC")
ax2.tick_params(axis="y", labelcolor=color2)
ax2.legend(loc="upper right")

plt.title("训练过程综合曲线")
fig.tight_layout()
plt.savefig("figures/combined_curve.png", dpi=300, bbox_inches="tight")
plt.show()

print("图表已保存至 figures/ 文件夹")