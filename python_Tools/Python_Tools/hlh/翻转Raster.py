import rasterio
import numpy as np

# 文件路径，请修改为你自己的路径
input_path = r'D:\临时文件夹\hlh\SM_1980_1989_mean.tif'
output_path = r'D:\临时文件夹\hlh\SM_1980_1989_mean_Flipped.tif'

with rasterio.open(input_path) as src:
    # 1. 读取原始数据
    data = src.read(1)
    
    # 2. 核心操作：上下翻转矩阵
    # src.read() 读出来是 (row, col)，flipud 会反转 row 的顺序
    flipped_data = np.flipud(data)
    
    # 3. 准备新的元数据
    # 我们需要保持分辨率和坐标系，但要确保原点（Origin）在北纬90度
    new_meta = src.meta.copy()
    
    # 获取原始的 Affine 参数
    # 原始参数可能导致读取起点在南半球，我们强行修正它
    from rasterio.transform import from_origin
    # 参数：左上角经度, 左上角纬度, 像素宽度, 像素高度(必须为负)
    new_transform = from_origin(-180.0, 90.0, 0.008333333, 0.010714286)
    
    new_meta.update({
        "driver": "GTiff",
        "height": flipped_data.shape[0],
        "width": flipped_data.shape[1],
        "transform": new_transform,
        "compress": 'deflate'
    })

    # 4. 写入新文件
    with rasterio.open(output_path, "w", **new_meta) as dest:
        dest.write(flipped_data, 1)

print("翻转完成！请在 QGIS 中查看新生成的图层。")