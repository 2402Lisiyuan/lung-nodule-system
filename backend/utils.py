import nibabel as nib
import SimpleITK as sitk
import numpy as np
import pandas as pd
from scipy import ndimage


def load_nifti(file_path):
    """
    加载 NIfTI 或 MetaImage(.mhd) 文件，返回 volume, spacing, affine
    """
    if file_path.endswith('.mhd'):
        # 如果是 .mhd 格式，使用 SimpleITK 读取
        img = sitk.ReadImage(file_path)
        volume = sitk.GetArrayFromImage(img)  # 返回的 volume 顺序是 (z, y, x)

        spacing_xyz = img.GetSpacing()
        spacing_zyx = (spacing_xyz[2], spacing_xyz[1], spacing_xyz[0])

        origin = img.GetOrigin()
        direction = np.array(img.GetDirection()).reshape(3, 3)
        affine = np.eye(4)
        affine[:3, :3] = direction * np.array(spacing_xyz)
        affine[:3, 3] = origin

        return volume.astype(np.float32), spacing_zyx, affine
    else:
        # 如果是 .nii 或 .nii.gz 格式，使用 nibabel
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

    dest_z = half - (z - z_start)
    dest_y = half - (y - y_start)
    dest_x = half - (x - x_start)

    sz, sy, sx = sub.shape
    patch[dest_z:dest_z + sz, dest_y:dest_y + sy, dest_x:dest_x + sx] = sub
    return patch


def normalize_hu(volume):
    """CT 值归一化到 [0,1]，范围 [-1000, 400] HU"""
    vol = np.clip(volume, -1000, 400)
    return (vol + 1000) / 1400.0


def physical_to_voxel(physical_coords_mm, affine, volume_shape):
    """物理坐标 (x, y, z) 毫米 -> 体素坐标 (z, y, x)"""
    if len(physical_coords_mm) == 3:
        phys = np.array([physical_coords_mm[0], physical_coords_mm[1], physical_coords_mm[2], 1.0])
    else:
        phys = np.array(physical_coords_mm)
    inv_affine = np.linalg.inv(affine)
    vox = inv_affine @ phys
    vox_idx = np.round(vox[:3]).astype(int)
    x, y, z = vox_idx[0], vox_idx[1], vox_idx[2]
    z = max(0, min(z, volume_shape[0] - 1))
    y = max(0, min(y, volume_shape[1] - 1))
    x = max(0, min(x, volume_shape[2] - 1))
    return (z, y, x)


def compute_nodule_volume(patch, spacing, hu_threshold=-300):
    """从 patch 中分割结节并计算体积 (mm³)"""
    hu = patch * 1400.0 - 1000.0
    mask = hu > hu_threshold
    labeled, num_features = ndimage.label(mask)
    if num_features == 0:
        return 0.0, mask
    sizes = ndimage.sum(mask, labeled, range(1, num_features + 1))
    if len(sizes) == 0:
        return 0.0, mask
    max_label = np.argmax(sizes) + 1
    mask = (labeled == max_label)
    voxel_volume = spacing[0] * spacing[1] * spacing[2]
    volume_mm3 = np.sum(mask) * voxel_volume
    return volume_mm3, mask