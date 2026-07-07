import rasterio
from rasterio.warp import reproject, Resampling

# 1. 路径设置
pet_path = r'D:\临时文件夹\hlh\PET_Mean_2010-2019.tif'
sm_flipped_path = r'D:\临时文件夹\hlh\SM_1980_1989_mean_Flipped.tif'
output_path = r'D:\临时文件夹\hlh\SM_FORCED_CLONE.tif'

with rasterio.open(pet_path) as ref:
    # 彻底克隆 PET 的所有地学属性
    kwargs = ref.meta.copy()
    dst_transform = ref.transform
    dst_crs = ref.crs
    dst_width = ref.width
    dst_height = ref.height

with rasterio.open(sm_flipped_path) as src:
    # 创建内存中的空矩阵，形状完全等同于 PET
    import numpy as np
    destination = np.zeros((dst_height, dst_width), dtype=np.float32)

    # 【核心】重采样：强制将大图的数据“投影”到小图的网格中
    # 这一步会解决你发现的坐标不一致和右下角偏离问题
    reproject(
        source=rasterio.band(src, 1),
        destination=destination,
        src_transform=src.transform,
        src_crs=src.crs,
        dst_transform=dst_transform,
        dst_crs=dst_crs,
        resampling=Resampling.bilinear # 如果是分类数据改用 nearest
    )

    # 更新输出文件的元数据
    kwargs.update({
        'driver': 'GTiff',
        'dtype': 'float32',
        'count': 1,
        'compress': 'lzw'
    })

    # 写入结果
    with rasterio.open(output_path, 'w', **kwargs) as dst:
        dst.write(destination, 1)

print("克隆完成！请检查 SM_FORCED_CLONE.tif 的右下角坐标，现在应该和 PET 完全一致了。")