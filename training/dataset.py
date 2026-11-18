import os
import glob
import numpy as np
import pandas as pd
import SimpleITK as sitk
import torch
from torch.utils.data import Dataset
from backend.utils import normalize_hu, physical_to_voxel, extract_patch_around_center


class LUNA16Dataset(Dataset):
    """
    从 LUNA16 subset 中加载结节 patch，构造伪时序样本用于训练流程验证。
    每个样本包含：
        - current: 当前 CT 的 64³ patch
        - prior:   先前 CT 的 64³ patch（对当前 patch 加噪声模拟）
        - months:  时间间隔（固定 12 个月）
        - label:   伪标签（直径 > 8mm 为 1，否则 0）
    """
    def __init__(self, data_dir, anno_path, patch_size=64, max_samples=None, augment=False):
        self.data_dir = data_dir
        self.patch_size = patch_size
        self.augment = augment

        # 读取标注
        df = pd.read_csv(anno_path)
        # 只保留 subset 中实际存在的 CT
        mhd_files = glob.glob(os.path.join(data_dir, "*.mhd"))
        available_uids = set(os.path.basename(f).replace(".mhd", "") for f in mhd_files)
        df = df[df['seriesuid'].isin(available_uids)]
        if max_samples:
            df = df.head(max_samples)

        self.samples = []
        for _, row in df.iterrows():
            self.samples.append({
                'uid': row['seriesuid'],
                'coordX': row['coordX'],
                'coordY': row['coordY'],
                'coordZ': row['coordZ'],
                'diameter_mm': row['diameter_mm'],
                'label': 1 if row['diameter_mm'] > 8.0 else 0
            })

    def __len__(self):
        return len(self.samples)

    def _load_ct(self, uid):
        """读取 .mhd 文件，返回归一化 volume、spacing、affine、shape"""
        mhd_path = os.path.join(self.data_dir, uid + ".mhd")
        img = sitk.ReadImage(mhd_path)
        volume = sitk.GetArrayFromImage(img)  # (z, y, x)
        spacing = img.GetSpacing()             # (x, y, z)
        origin = img.GetOrigin()
        direction = np.array(img.GetDirection()).reshape(3, 3)

        # 构造仿射矩阵（nibabel 风格，但 SimpleITK 方向可能不同，这里仅用于坐标转换）
        affine = np.eye(4)
        affine[:3, :3] = direction * np.array(spacing)
        affine[:3, 3] = origin

        # 注意：SimpleITK 返回的 volume 轴顺序为 (z, y, x)，spacing 为 (x, y, z)
        # 为保持与 utils 一致，将 spacing 转为 (z, y, x) 顺序
        spacing_zyx = (spacing[2], spacing[1], spacing[0])
        vol_norm = normalize_hu(volume)
        return vol_norm, spacing_zyx, affine, volume.shape

    def __getitem__(self, idx):
        s = self.samples[idx]
        vol_norm, spacing, affine, shape = self._load_ct(s['uid'])

        # 物理坐标转体素坐标
        voxel_center = physical_to_voxel((s['coordX'], s['coordY'], s['coordZ']), affine, shape)

        # 提取当前 patch
        current = extract_patch_around_center(vol_norm, voxel_center, self.patch_size)

        # 伪时序：先前 patch = 当前 patch + 噪声
        noise = np.random.normal(0, 0.03, current.shape).astype(np.float32)
        prior = np.clip(current + noise, 0, 1)

        # 数据增强（仅训练集）
        if self.augment:
            if np.random.rand() > 0.5:
                current = np.flip(current, axis=0).copy()
                prior = np.flip(prior, axis=0).copy()
            if np.random.rand() > 0.5:
                current = np.flip(current, axis=1).copy()
                prior = np.flip(prior, axis=1).copy()

        # 转为张量
        current_t = torch.tensor(current, dtype=torch.float32).unsqueeze(0)  # (1, D, H, W)
        prior_t = torch.tensor(prior, dtype=torch.float32).unsqueeze(0)
        time_t = torch.tensor([1.0], dtype=torch.float32)  # 固定 12 个月
        label_t = torch.tensor([s['label']], dtype=torch.float32)

        return current_t, prior_t, time_t, label_t