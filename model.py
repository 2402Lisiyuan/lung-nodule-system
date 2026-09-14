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
            nn.AdaptiveAvgPool3d(1)
        )
        self.fusion = nn.Sequential(
            nn.Linear(32 + 32 + 1, 64),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(64, 1),
            nn.Sigmoid()
        )

    def forward(self, current_patch, prior_patch, time_diff_months):
        # current_patch/prior_patch: [batch, 1, D, H, W]
        feat_c = self.feature_extractor(current_patch).view(current_patch.size(0), -1)
        feat_p = self.feature_extractor(prior_patch).view(prior_patch.size(0), -1)
        combined = torch.cat([feat_c, feat_p, time_diff_months], dim=1)
        return self.fusion(combined)

def load_model(weights_path=None):
    model = TemporalNoduleRiskNet()
    if weights_path:
        model.load_state_dict(torch.load(weights_path, map_location='cpu'))
    model.eval()
    return model