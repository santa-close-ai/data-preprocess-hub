import os
import xarray as xr
import numpy as np
import pandas as pd
from collections import defaultdict

data_dir = "C:/Users/USER/Downloads/data"
target_vars = ['VOD_ASC', 'VOD_DESC', 'VOD_ASC_DESC']
output_dir = "vod_per_day_csv"
os.makedirs(output_dir, exist_ok=True)

def compute_grid_id(lat_val, lon_val):
    lat_bin = int(np.floor(lat_val / 0.1))
    lon_bin = int(np.floor(lon_val / 0.1))
    return (lat_bin + 900) * 3600 + (lon_bin + 1800)

for file in os.listdir(data_dir):
    if file.endswith(".nc"):
        file_path = os.path.join(data_dir, file)
        print(f"Processing: {file_path}")

        # ✅ 메모리 최적화를 위해 chunking 사용
        ds = xr.open_dataset(file_path, chunks={'lat': 100, 'lon': 100})  

        try:
            lat = ds['lat'].values
            lon = ds['lon'].values
        except Exception as e:
            print(f"❌ 위경도 로딩 실패: {e}")
            continue

        date_str = file.split('_')[3]
        date = pd.to_datetime(date_str, format="%Y%m%d")
        daily_records = []

        for var_name in target_vars:
            if var_name in ds.variables:
                var_data = ds[var_name]

                if 'time' in var_data.dims:
                    data = var_data.isel(time=0).load().values  # lazy → 메모리에 올림
                else:
                    data = var_data.load().values

                dim_order = var_data.dims
                for i in range(data.shape[0]):
                    for j in range(data.shape[1]):
                        if 'lat' in dim_order[0]:
                            lat_val = lat[i]
                            lon_val = lon[j]
                        else:
                            lat_val = lat[j]
                            lon_val = lon[i]
                        val = data[i, j]
                        if not np.isnan(val):
                            grid_id = compute_grid_id(lat_val, lon_val)
                            daily_records.append({
                                'date': date,
                                'lat': lat_val,
                                'lon': lon_val,
                                'grid_id': grid_id,
                                'variable': var_name,
                                'value': val
                            })

        # ✅ 날짜별 CSV 저장
        if daily_records:
            df = pd.DataFrame(daily_records)
            output_path = os.path.join(output_dir, f"vod_{date.strftime('%Y%m%d')}.csv")
            df.to_csv(output_path, index=False)
            print(f"✅ 저장 완료 → {output_path}")

print("\n🎉 모든 날짜별 파일 저장 완료!")
