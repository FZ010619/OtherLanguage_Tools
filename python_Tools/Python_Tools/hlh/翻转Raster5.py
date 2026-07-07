import rasterio
from rasterio.warp import reproject, Resampling
import numpy as np

# 1. 路径设置
pet_path = r'D:\临时文件夹\hlh\PET_Mean_2010-2019.tif'
# 注意：这里使用你最开始那张“倒着”或“刚转正”的 SM 作为参考
sm_ref_path = r'D:\临时文件夹\hlh\SM_1980_1989_mean_Flipped.tif' 
output_path = r'D:\临时文件夹\hlh\PET_MATCHED_TO_OLD_SM.tif'

with rasterio.open(sm_ref_path) as ref:
    # 提取老数据的“骨架”：分辨率 0.0107, 原点 -180, 维度 16800x43200
    kwargs = ref.meta.copy()
    dst_transform = ref.transform
    dst_crs = ref.crs
    dst_width = ref.width
    dst_height = ref.height

with rasterio.open(pet_path) as src:
    # 创建一个和【全图SM】一样大的内存空间
    # 警告：全图 SM 很大（16800x43200），这会占用约 2.7GB 内存
    destination = np.zeros((dst_height, dst_width), dtype=np.float32)

    # 将 PET 的数据投影到 SM 的坐标系中
    reproject(
        source=rasterio.band(src, 1),
        destination=destination,
        src_transform=src.transform,
        src_crs=src.crs,
        dst_transform=dst_transform,
        dst_crs=dst_crs,
        resampling=Resampling.bilinear
    )

    # 写入结果
    kwargs.update({
        'driver': 'GTiff',
        'dtype': 'float32',
        'count': 1,
        'compress': 'lzw'
    })

    with rasterio.open(output_path, 'w', **kwargs) as dst:
        dst.write(destination, 1)

print("反向匹配完成！现在 PET 的属性和老数据 SM 完全一致了。")