import numpy as np
import plotly.graph_objects as go
from skimage import measure
from scipy import ndimage
from skimage.filters import threshold_otsu

def generate_sphere_mask(shape, center, radius_mm, spacing):
    """生成球体 mask（备用）"""
    radius_voxel = radius_mm / np.mean(spacing)
    z, y, x = np.ogrid[:shape[0], :shape[1], :shape[2]]
    dz = (z - center[0]) * spacing[0]
    dy = (y - center[1]) * spacing[1]
    dx = (x - center[2]) * spacing[2]
    distance = np.sqrt(dz**2 + dy**2 + dx**2)
    mask = (distance <= radius_voxel).astype(np.uint8)
    return mask

def extract_nodule_mask(patch, min_volume=100):
    """自动分割（备用）"""
    thresh = threshold_otsu(patch)
    binary = patch > thresh
    labeled, num_features = ndimage.label(binary)
    if num_features == 0:
        return None
    sizes = ndimage.sum(binary, labeled, range(1, num_features+1))
    max_idx = np.argmax(sizes) + 1
    mask = (labeled == max_idx).astype(np.uint8)
    if sizes[max_idx-1] < min_volume:
        return None
    mask = ndimage.binary_closing(mask, structure=np.ones((3,3,3))).astype(np.uint8)
    return mask

def create_3d_nodule_visualization(patch, method='auto', threshold=None, 
                                   sphere_center=None, sphere_radius_mm=None, spacing=(1,1,1)):
    """3D重建（可能失败，作为备用）"""
    if patch is None or patch.size == 0:
        return go.Figure()
    mask = None
    if method == 'sphere' and sphere_center is not None and sphere_radius_mm is not None:
        mask = generate_sphere_mask(patch.shape, sphere_center, sphere_radius_mm, spacing)
    elif method == 'auto':
        mask = extract_nodule_mask(patch)
    if mask is not None:
        try:
            verts, faces, _, _ = measure.marching_cubes(mask, level=0.5)
        except:
            return go.Figure()
    else:
        if threshold is None:
            threshold = np.max(patch) * 0.3
        try:
            verts, faces, _, _ = measure.marching_cubes(patch, level=threshold)
        except:
            return go.Figure()
    fig = go.Figure(data=[go.Mesh3d(x=verts[:,0], y=verts[:,1], z=verts[:,2], i=faces[:,0], j=faces[:,1], k=faces[:,2], color='lightcoral', opacity=0.9)])
    fig.update_layout(scene=dict(xaxis_title='X', yaxis_title='Y', zaxis_title='Z', aspectmode='data'), width=600, height=500)
    return fig

def create_ct_slice_viewer(volume, voxel_spacing=None, slice_axis='axial'):
    """
    显示CT的交互式切片查看器
    """
    if voxel_spacing is None:
        voxel_spacing = (1, 1, 1)
    
    if slice_axis == 'axial':
        n_slices = volume.shape[0]
        get_slice = lambda i: volume[i, :, :]
        title = "横断面 (Axial)"
        xlabel, ylabel = "X (pixel)", "Y (pixel)"
    elif slice_axis == 'coronal':
        n_slices = volume.shape[1]
        get_slice = lambda i: volume[:, i, :]
        title = "冠状面 (Coronal)"
        xlabel, ylabel = "X (pixel)", "Z (pixel)"
    else:  # sagittal
        n_slices = volume.shape[2]
        get_slice = lambda i: volume[:, :, i]
        title = "矢状面 (Sagittal)"
        xlabel, ylabel = "Y (pixel)", "Z (pixel)"
    
    # 默认显示中间层面
    default_slice = n_slices // 2
    slice_data = get_slice(default_slice)
    
    fig = go.Figure()
    fig.add_trace(go.Heatmap(z=slice_data, colorscale='gray', name=title))
    
    # 创建滑动条
    steps = []
    for i in range(0, n_slices, max(1, n_slices//30)):
        step = dict(
            method="update",
            args=[{"z": [get_slice(i)]}, {"title": f"{title} - 层面 {i}"}],
            label=str(i)
        )
        steps.append(step)
    sliders = [dict(active=default_slice, steps=steps, currentvalue={"prefix": "层面: "})]
    
    fig.update_layout(
        title=title,
        width=700, height=600,
        xaxis=dict(title=xlabel),
        yaxis=dict(title=ylabel),
        sliders=sliders,
        coloraxis=dict(colorscale='gray', cmin=volume.min(), cmax=volume.max())
    )
    return fig