import rasterio
import numpy as np

# 文件路径
pet_path = r'D:\临时文件夹\hlh\PET_Mean_2010-2019.tif'
sm_flipped_path = r'D:\临时文件夹\hlh\SM_1980_1989_mean_Flipped.tif'
output_path = r'D:\临时文件夹\hlh\SM_FORCED_ALIGNED.tif'

with rasterio.open(pet_path) as ref_ds:
    # 1. 提取 PET 的所有“外壳”信息
    ref_meta = ref_ds.meta.copy()
    ref_height = ref_ds.height
    ref_width = ref_ds.width
    
    # 2. 读取翻转后的 SM 数据
    with rasterio.open(sm_flipped_path) as src_ds:
        # 读取矩阵，并强行重塑（Resize）或切片到与 PET 相同的形状
        # 注意：这里我们只读取大图中对应中国区域的那块像素
        # 如果你之前没有裁剪，直接读全图会因为形状不一致报错
        # 所以我们使用 read 的 out_shape 功能进行实时重采样
        sm_data = src_ds.read(
            1, 
            out_shape=(ref_height, ref_width),
            resampling=rasterio.enums.Resampling.bilinear
        )

    # 3. 强行更新元数据
    # 确保数据类型一致，这里强制改为 float32
    ref_meta.update({
        "dtype": 'float32',
        "count": 1,
        "compress": 'lzw'
    })

    # 4. 写入新文件
    with rasterio.open(output_path, 'w', **ref_meta) as dst:
        dst.write(sm_data.astype(np.float32), 1)

print("移花接木完成！现在的 SM 文件在属性上与 PET 完全一致。")