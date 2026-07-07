import rasterio
from rasterio.warp import calculate_default_transform, reproject, Resampling
import numpy as np

# 1. 路径设置
pet_path = r'D:\临时文件夹\hlh\PET_Mean_2010-2019.tif'
sm_flipped_path = r'D:\临时文件夹\hlh\SM_1980_1989_mean_Flipped.tif'
output_path = r'D:\临时文件夹\hlh\SM_FINAL_ALIGNED.tif'

with rasterio.open(pet_path) as ref:
    # 获取参考图层（小图）的元数据：范围、分辨率、CRS、行列数
    ref_meta = ref.meta.copy()
    ref_transform = ref.transform
    ref_crs = ref.crs
    ref_width = ref.width
    ref_height = ref.height

with rasterio.open(sm_flipped_path) as src:
    # 创建输出矩阵
    destination = np.zeros((ref_height, ref_width), dtype=np.float32)

    # 核心步骤：重投影/重采样
    # 将 src (翻转后的SM) 强行“重绘”到目标坐标系和范围内
    reproject(
        source=rasterio.band(src, 1),
        destination=destination,
        src_transform=src.transform,
        src_crs=src.crs,
        dst_transform=ref_transform,
        dst_crs=ref_crs,
        resampling=Resampling.bilinear # 使用双线性插值
    )

    # 更新元数据以匹配小图
    ref_meta.update({
        "driver": "GTiff",
        "height": ref_height,
        "width": ref_width,
        "transform": ref_transform,
        "crs": ref_crs,
        "nodata": src.nodata,
        "compress": 'lzw'
    })

    # 写入结果
    with rasterio.open(output_path, "w", **ref_meta) as dest:
        dest.write(destination, 1)

print("强制对齐完成！现在 SM_FINAL_ALIGNED 的行列号与 PET 完全一致。")