import os
from pathlib import Path


RASTERIO_DIR = Path(__file__).resolve().parents[1] / ".PythonTools" / "Lib" / "site-packages" / "rasterio"
RASTERIO_PROJ_DATA = RASTERIO_DIR / "proj_data"

if RASTERIO_PROJ_DATA.exists():
    os.environ["PROJ_LIB"] = str(RASTERIO_PROJ_DATA)
    os.environ["PROJ_DATA"] = str(RASTERIO_PROJ_DATA)

import numpy as np
import rasterio
from rasterio.enums import Resampling
from rasterio.transform import from_origin
from rasterio.warp import reproject
from rasterio.windows import Window, transform as window_transform


INPUT_TIF = r"D:\临时文件夹\hlh\SM_1980_1989_mean_Flipped.tif"
OUTPUT_TIF = r"D:\临时文件夹\hlh\SM_1980_1989_Standard_Global.tif"

TARGET_CRS = "EPSG:4326"
TARGET_WIDTH = 43200
TARGET_HEIGHT = 21600
TARGET_RESOLUTION = 1.0 / 120.0
TARGET_TRANSFORM = from_origin(-180.0, 90.0, TARGET_RESOLUTION, TARGET_RESOLUTION)
WINDOW_SIZE = 512


def build_profile(src):
    profile = src.profile.copy()
    profile.update(
        driver="GTiff",
        crs=TARGET_CRS,
        transform=TARGET_TRANSFORM,
        width=TARGET_WIDTH,
        height=TARGET_HEIGHT,
        compress="LZW",
        tiled=True,
        blockxsize=WINDOW_SIZE,
        blockysize=WINDOW_SIZE,
        BIGTIFF="IF_SAFER",
    )

    if src.nodata is not None:
        profile["nodata"] = src.nodata
    else:
        profile.pop("nodata", None)

    if np.issubdtype(np.dtype(src.dtypes[0]), np.floating):
        profile["predictor"] = 3

    return profile


def iter_windows(width, height, step):
    for top in range(0, height, step):
        window_height = min(step, height - top)
        for left in range(0, width, step):
            window_width = min(step, width - left)
            yield Window.from_slices(
                (top, top + window_height),
                (left, left + window_width),
            )


def main():
    if not os.path.exists(INPUT_TIF):
        raise FileNotFoundError(f"找不到输入文件: {INPUT_TIF}")

    print(f"输入文件: {INPUT_TIF}")
    print(f"输出文件: {OUTPUT_TIF}")
    print(f"目标网格: {TARGET_WIDTH} x {TARGET_HEIGHT}")
    print(f"目标变换: {TARGET_TRANSFORM}")

    with rasterio.open(INPUT_TIF) as src:
        if src.crs is None:
            raise ValueError("输入栅格缺少 CRS，无法重投影。")

        profile = build_profile(src)
        band_count = src.count
        dst_nodata = src.nodata

        with rasterio.open(OUTPUT_TIF, "w", **profile) as dst:
            for window in iter_windows(TARGET_WIDTH, TARGET_HEIGHT, WINDOW_SIZE):
                dst_window_transform = window_transform(window, TARGET_TRANSFORM)
                window_shape = (int(window.height), int(window.width))

                for band_index in range(1, band_count + 1):
                    destination = np.empty(window_shape, dtype=np.dtype(src.dtypes[band_index - 1]))

                    reproject(
                        source=rasterio.band(src, band_index),
                        destination=destination,
                        src_transform=src.transform,
                        src_crs=src.crs,
                        src_nodata=src.nodata,
                        dst_transform=dst_window_transform,
                        dst_crs=TARGET_CRS,
                        dst_nodata=dst_nodata,
                        resampling=Resampling.bilinear,
                    )

                    dst.write(destination, band_index, window=window)

    print("处理成功")
    print(f"生成文件: {OUTPUT_TIF}")


if __name__ == "__main__":
    main()