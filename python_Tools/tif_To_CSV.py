"""
================================================================================
脚本名称: InSAR 形变结果栅格转 CSV 导出工具
适用场景: 
    1. 将时序 InSAR（PS/SBAS）处理后的单波段地理编码栅格图（TIF/DAT）导出为
       包含 [经度, 纬度, 形变量] 的 CSV 表格。
    2. 用于向非 GIS 专业人员提交监测点位数据或进行后续统计分析。
    
核心功能:
    - 环境自检：自动清理常见的 PROJ/GDAL 环境变量冲突（针对安装了 PostgreSQL/ArcGIS 的环境）。
    - 坐标转换：如果输入 TIF 为投影坐标系（如 UTM），脚本会自动将其重采样并转换为 WGS84 经纬度。
    - 空值处理：自动识别并过滤 NoData 像元，确保 CSV 文件的纯净和紧凑。
    - 图形化操作：内置 Tkinter 界面，无需修改代码路径，直接“点选”即可完成转换。

依赖库: rasterio, numpy, pandas, tkinter
作者: Fan Zhen
最后修改日期: 2026-04-09
================================================================================
"""
import os


def _sanitize_geospatial_env():
    # 避免系统安装的 PostgreSQL/PostGIS 覆盖 Python 环境自带的 PROJ/GDAL 数据
    for key in ("PROJ_LIB", "PROJ_DATA", "GDAL_DATA"):
        value = os.environ.get(key, "")
        lower_value = value.lower()
        if "postgresql" in lower_value or "postgis" in lower_value:
            os.environ.pop(key, None)


_sanitize_geospatial_env()

import rasterio
import numpy as np
import pandas as pd
from rasterio.warp import transform as rio_transform
from rasterio.transform import xy as rio_xy
import tkinter as tk
from tkinter import filedialog, messagebox
from pathlib import Path

def export_tif_to_csv(input_tif, output_csv):
    with rasterio.open(input_tif) as src:
        if src.count != 1:
            raise ValueError(f"仅支持单波段 TIFF，当前波段数: {src.count}")

        print(f"正在读取数据: {input_tif}")
        band_data = src.read(1)

        rows, cols = np.indices((src.height, src.width))
        flat_rows = rows.ravel()
        flat_cols = cols.ravel()
        flat_values = band_data.ravel()

        xs, ys = rio_xy(src.transform, flat_rows, flat_cols)
        xs = np.array(xs)
        ys = np.array(ys)

        nodata = src.nodata
        if nodata is None:
            mask = ~np.isnan(flat_values)
        else:
            mask = (flat_values != nodata) & (~np.isnan(flat_values))

        valid_x = xs[mask]
        valid_y = ys[mask]
        valid_values = flat_values[mask]

        if src.crs is not None and src.crs.to_epsg() != 4326:
            try:
                transformed = rio_transform(src.crs, "EPSG:4326", valid_x.tolist(), valid_y.tolist())
                valid_lons, valid_lats = transformed[0], transformed[1]
                valid_lons = np.array(valid_lons)
                valid_lats = np.array(valid_lats)
            except Exception as exc:
                raise RuntimeError(
                    "坐标转换失败：检测到 PROJ 环境冲突或坐标系不可识别。"
                    "请关闭外部 GIS/数据库环境后重试，或在命令行先清空 PROJ_LIB/GDAL_DATA。"
                ) from exc
        else:
            valid_lons = valid_x
            valid_lats = valid_y

        print(f"提取完成，有效像元数量: {len(valid_values)}")

        df = pd.DataFrame(
            {
                "Longitude": valid_lons,
                "Latitude": valid_lats,
                "BandValue": valid_values,
            }
        )
        df.to_csv(output_csv, index=False, encoding="utf-8-sig")
        print(f"成功导出到: {output_csv}")


def run_gui():
    root = tk.Tk()
    root.title("单波段TIF转CSV")
    root.geometry("560x240")
    root.resizable(False, False)

    tif_var = tk.StringVar()
    out_dir_var = tk.StringVar()

    def choose_tif():
        selected = filedialog.askopenfilename(
            title="选择单波段TIF文件",
            filetypes=[("TIFF 文件", "*.tif *.tiff"), ("全部文件", "*.*")],
        )
        if selected:
            tif_var.set(selected)

    def choose_output_dir():
        selected = filedialog.askdirectory(title="选择CSV输出目录")
        if selected:
            out_dir_var.set(selected)

    def export_csv():
        input_tif = tif_var.get().strip()
        output_dir = out_dir_var.get().strip()

        if not input_tif:
            messagebox.showwarning("提示", "请先选择一个单波段TIF文件。")
            return

        if not output_dir:
            messagebox.showwarning("提示", "请先选择输出目录。")
            return

        output_csv = str(Path(output_dir) / f"{Path(input_tif).stem}_lonlat_value.csv")

        try:
            export_tif_to_csv(input_tif, output_csv)
            messagebox.showinfo("完成", f"导出成功:\n{output_csv}")
        except Exception as exc:
            messagebox.showerror("导出失败", str(exc))

    tk.Label(root, text="1) 选择单波段 TIF 文件", anchor="w").place(x=20, y=20, width=220)
    tk.Button(root, text="选择文件", command=choose_tif).place(x=250, y=16, width=100)
    tk.Entry(root, textvariable=tif_var).place(x=20, y=50, width=520, height=26)

    tk.Label(root, text="2) 选择 CSV 输出目录", anchor="w").place(x=20, y=95, width=220)
    tk.Button(root, text="选择目录", command=choose_output_dir).place(x=250, y=91, width=100)
    tk.Entry(root, textvariable=out_dir_var).place(x=20, y=125, width=520, height=26)

    tk.Button(root, text="3) 开始导出 CSV", command=export_csv).place(x=210, y=175, width=140, height=34)

    root.mainloop()


if __name__ == "__main__":
    run_gui()