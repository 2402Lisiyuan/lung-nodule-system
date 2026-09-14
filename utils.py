import nibabel as nib
import numpy as np
import pandas as pd

def load_nifti(file_path):
    """加载 NIfTI 文件，返回 volume, spacing, affine"""
    img = nib.load(file_path)
    volume = img.get_fdata().astype(np.float32)
    spacing = img.header.get_zooms()
    affine = img.affine
    return volume, spacing, affine

def extract_patch_around_center(volume, center_voxel, patch_size=64):
    """以体素坐标为中心提取固定大小 patch，边界自动填充"""
    z, y, x = center_voxel
    half = patch_size // 2
    z_start = max(0, z - half)
    z_end = min(volume.shape[0], z + half)
    y_start = max(0, y - half)
    y_end = min(volume.shape[1], y + half)
    x_start = max(0, x - half)
    x_end = min(volume.shape[2], x + half)
    
    sub = volume[z_start:z_end, y_start:y_end, x_start:x_end]
    patch = np.zeros((patch_size, patch_size, patch_size), dtype=volume.dtype)
    
    # 计算在目标 patch 中的放置位置
    dest_z = half - (z - z_start)
    dest_y = half - (y - y_start)
    dest_x = half - (x - x_start)
    
    sz, sy, sx = sub.shape
    patch[dest_z:dest_z+sz, dest_y:dest_y+sy, dest_x:dest_x+sx] = sub
    return patch

def normalize_hu(volume):
    """CT 值归一化到 [0,1]，范围 [-1000, 400] HU"""
    vol = np.clip(volume, -1000, 400)
    return (vol + 1000) / 1400.0

def physical_to_voxel(physical_coords_mm, affine, volume_shape):
    """
    物理坐标 (x, y, z) 毫米 -> 体素坐标 (z, y, x)
    自动裁剪到有效范围
    """
    if len(physical_coords_mm) == 3:
        phys = np.array([physical_coords_mm[0], physical_coords_mm[1], physical_coords_mm[2], 1.0])
    else:
        phys = np.array(physical_coords_mm)
    inv_affine = np.linalg.inv(affine)
    vox = inv_affine @ phys
    vox_idx = np.round(vox[:3]).astype(int)
    # 注意：nibabel 的 affine 映射 (x,y,z) -> (i,j,k)，volume 索引顺序为 (z,y,x)
    x, y, z = vox_idx[0], vox_idx[1], vox_idx[2]
    # 裁剪到有效范围
    z = max(0, min(z, volume_shape[0] - 1))
    y = max(0, min(y, volume_shape[1] - 1))
    x = max(0, min(x, volume_shape[2] - 1))
    return (z, y, x)

def load_annotations(csv_file):
    """加载 LUNA16 格式的 annotations.csv，返回 {seriesuid: {coordX,coordY,coordZ,diameter_mm}}"""
    df = pd.read_csv(csv_file)
    annotations = {}
    for _, row in df.iterrows():
        uid = row['seriesuid']
        if uid not in annotations:
            annotations[uid] = {
                'coordX': row['coordX'],
                'coordY': row['coordY'],
                'coordZ': row['coordZ'],
                'diameter_mm': row['diameter_mm']
            }
    return annotations

def compute_nodule_volume(patch, spacing, hu_threshold=-300):
    """
    从 patch 中分割结节并计算体积 (mm³)
    patch: 三维 numpy 数组 (Z, Y, X)，已归一化到 [0,1] (对应 HU [-1000, 400])
    spacing: (dz, dy, dx) 单位 mm
    hu_threshold: HU 阈值，默认 -300（大致区分软组织与空气/肺实质）
    返回: 体积 (mm³), 分割掩码 (bool 数组)
    """
    # 将归一化值转回 HU
    hu = patch * 1400.0 - 1000.0
    # 阈值分割
    mask = hu > hu_threshold
    # 清除小的孤立区域（去噪）
    from scipy import ndimage
    # 仅保留最大连通域
    labeled, num_features = ndimage.label(mask)
    if num_features == 0:
        return 0.0, mask
    # 计算每个连通域的大小
    sizes = ndimage.sum(mask, labeled, range(1, num_features+1))
    if len(sizes) == 0:
        return 0.0, mask
    max_label = np.argmax(sizes) + 1
    mask = (labeled == max_label)
    # 计算体积：体素数 * 体素真实体积
    voxel_volume = spacing[0] * spacing[1] * spacing[2]  # dz * dy * dx
    volume_mm3 = np.sum(mask) * voxel_volume
    return volume_mm3, mask