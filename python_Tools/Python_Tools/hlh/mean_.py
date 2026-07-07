import os
import glob
import xarray as xr
import rioxarray
import numpy as np

# ===================== 路径 =====================
BASE_DIR = r"E:\原始数据备份\1980-1990和2000_2020_SM_666"
OUT_DIR = r"D:\zhuomian\Data_20260421\1980s_2000s_2010s_SM"
os.makedirs(OUT_DIR, exist_ok=True)

period_dict = {
    "1980_1989": range(1980, 1990),
    "2000_2009": range(2000, 2010),
    "2010_2019": range(2010, 2020)
}

# 【关键】全球 1km 高精度经纬度坐标
LON = np.arange(-180 + 0.0041666665, 180, 0.008333333)
LAT = np.arange(90 - 0.005357143, -90, -0.010714286)


# ===================== 读取函数 =====================
def load_year_nc(year):
    nc_files = sorted(glob.glob(os.path.join(BASE_DIR, str(year), "*.nc")))
    if not nc_files:
        print(f"⚠️ {year} 年无文件")
        return None

    das = []
    for f in nc_files:
        try:
            ds = xr.open_dataset(f, engine="h5netcdf", chunks="auto")
            da = ds["SoilMoist_S_tavg"]
            da = da.where(da > -9998)
            das.append(da)
            ds.close()
        except Exception as e:
            print(f"❌ 读取失败：{f}")

    print(f"✅ {year} 年 加载完成：{len(nc_files)} 个文件")
    return xr.concat(das, dim="time") if das else None


# ===================== 主程序 =====================
if __name__ == "__main__":
    for period_name, years in period_dict.items():
        print(f"\n===== 计算 {period_name} 均值 =====")
        year_das = []
        for y in years:
            da = load_year_nc(y)
            if da is not None:
                year_das.append(da)

        # 计算均值
        all_data = xr.concat(year_das, dim="time")
        mean_da = all_data.mean(dim="time", skipna=True)

        # ===================== 【核心：强制赋予正确坐标】 =====================
        # 自动识别维度并重命名
        dims = list(mean_da.dims)
        y_dim = [d for d in dims if mean_da.shape[dims.index(d)] == 16800][0]
        x_dim = [d for d in dims if mean_da.shape[dims.index(d)] == 43200][0]

        mean_da = mean_da.rename({x_dim: "lon", y_dim: "lat"})
        mean_da = mean_da.assign_coords(lon=LON, lat=LAT)
        mean_da = mean_da.rio.set_spatial_dims(x_dim="lon", y_dim="lat")
        mean_da = mean_da.rio.write_crs("EPSG:4326")
        # ======================================================================

        # 导出TIFF
        out_tif = os.path.join(OUT_DIR, f"SM_{period_name}_mean.tif")
        mean_da.rio.to_raster(out_tif, compress="DEFLATE", dtype="float32")
        print(f"🎉 导出成功：{out_tif}")

    print("\n✅ 全部三个时期处理完成！")