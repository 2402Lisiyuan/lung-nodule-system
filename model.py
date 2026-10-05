import torch
import torch.nn as nn

class TemporalNoduleRiskNet(nn.Module):
    def __init__(self):
        super().__init__()
        self.feature_extractor = nn.Sequential(
            nn.Conv3d(1, 16, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool3d(2),
            nn.Conv3d(16, 32, kernel_size=3, padding=1),
            nn.ReLU(),

        )
        self.fusion = nn.Sequential(
            nn.Linear(32 + 32 + 1, 64),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(64, 1),
            nn.Sigmoid()
        )
        # 用于 Grad-CAM 的中间变量
        self.feature_map = None
        self.gradient = None

    def forward(self, current_patch, prior_patch, time_diff_months):
        # 提取特征图（保留空间维度）
        feat_map_c = self.feature_extractor(current_patch)
        feat_map_p = self.feature_extractor(prior_patch)

        # 保存当前 CT 的特征图并注册梯度钩子
        self.feature_map = feat_map_c
        if feat_map_c.requires_grad:
            feat_map_c.register_hook(lambda grad: setattr(self, 'gradient', grad))

        # 全局平均池化得到 32 维特征向量
        feat_c = feat_map_c.mean(dim=(2, 3, 4))
        feat_p = feat_map_p.mean(dim=(2, 3, 4))

        combined = torch.cat([feat_c, feat_p, time_diff_months], dim=1)
        return self.fusion(combined)

    def get_grad_cam(self, current_patch, prior_patch, time_diff_months):
        """计算当前 CT 的 Grad-CAM 热力图，现版系统未集成热力图功能"""
        self.zero_grad()
        output = self.forward(current_patch, prior_patch, time_diff_months)
        output.backward()

        if self.feature_map is None or self.gradient is None:
            return None

        feature_map = self.feature_map       # [B, 32, D, H, W]
        gradient = self.gradient              # [B, 32, D, H, W]

        weights = gradient.mean(dim=(2, 3, 4), keepdim=True)
        cam = (weights * feature_map).sum(dim=1, keepdim=True)
        cam = torch.relu(cam)
        cam = cam - cam.min()
        cam = cam / (cam.max() + 1e-8)
        return cam


def load_model(weights_path=None):
    model = TemporalNoduleRiskNet()
    if weights_path:
        model.load_state_dict(torch.load(weights_path, map_location='cpu'))
    model.eval()
    return model