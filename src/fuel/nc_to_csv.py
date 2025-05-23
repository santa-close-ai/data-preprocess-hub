import os
import csv
import numpy as np
import netCDF4 as nc

def convert_nc_to_csv(nc_dataset, output_csv_path, data_variable_names):
    """
    NetCDF 데이터셋을 CSV 파일로 변환합니다. latitude와 longitude 대신 grid_id를 저장합니다.

    :param nc_dataset: netCDF4.Dataset 객체
    :param output_csv_path: 출력 CSV 파일 경로
    :param data_variable_names: CSV에 포함할 데이터 변수 이름 목록
    """
    print(f"변환 시작: {nc_dataset.filepath()} -> {output_csv_path}")

    # 차원 변수 추출
    time_var = nc_dataset.variables['time']
    
    # 위도/경도 변수 이름 확인 (일반적으로'lat', 'lon' 또는 'latitude', 'longitude' - grid_id 계산에 필요)
    lat_var_name = None
    if 'lat' in nc_dataset.variables:
        lat_var_name = 'lat'
    elif 'latitude' in nc_dataset.variables:
        lat_var_name = 'latitude'
    else:
        raise ValueError(f"위도 변수('lat' 또는 'latitude')를 찾을 수 없습니다: {nc_dataset.filepath()}")

    lon_var_name = None
    if 'lon' in nc_dataset.variables:
        lon_var_name = 'lon'
    elif 'longitude' in nc_dataset.variables:
        lon_var_name = 'longitude'
    else:
        raise ValueError(f"경도 변수('lon' 또는 'longitude')를 찾을 수 없습니다: {nc_dataset.filepath()}")

    lats = nc_dataset.variables[lat_var_name][:]
    lons = nc_dataset.variables[lon_var_name][:]
    
    # 시간 변수 처리: 숫자형 시간 데이터를 datetime 객체로 변환 후 문자열로 포맷팅
    times_raw = time_var[:]
    processed_times = []
    try:
        time_units = time_var.units
        time_calendar = time_var.calendar if 'calendar' in time_var.ncattrs() else 'standard'
        datetime_objects = nc.num2date(times_raw, units=time_units, calendar=time_calendar)
        processed_times = [dt.strftime('%Y-%m-%d %H:%M:%S') for dt in datetime_objects]
    except Exception as e:
        print(f"경고: {nc_dataset.filepath()}의 시간 변환 중 오류 발생. 원시 시간 값을 사용합니다. 오류: {e}")
        processed_times = [str(t) for t in times_raw]

    # 특정 CSV 파일의 출력 디렉토리가 없으면 생성
    os.makedirs(os.path.dirname(output_csv_path), exist_ok=True)

    with open(output_csv_path, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        
        # 헤더 작성 (latitude, longitude 대신 grid_id 포함)
        header = ['time', 'grid_id'] + data_variable_names
        writer.writerow(header)
        
        # 데이터 작성
        for t_idx, time_str in enumerate(processed_times):
            for lat_idx, lat_val in enumerate(lats):
                current_lat = float(lat_val.item() if isinstance(lat_val, np.generic) else lat_val)
                for lon_idx, lon_val in enumerate(lons):
                    current_lon = float(lon_val.item() if isinstance(lon_val, np.generic) else lon_val)
                    
                    # grid_id 계산
                    lat_bin = int(np.floor(current_lat / 0.1))
                    lon_bin = int(np.floor(current_lon / 0.1))
                    grid_id = int(lat_bin + 900) * 3600 + (lon_bin + 1800)
                    
                    row = [time_str, grid_id] # time과 grid_id로 행 시작
                    for var_name in data_variable_names:
                        data_val = nc_dataset.variables[var_name][t_idx, lat_idx, lon_idx]
                        
                        if isinstance(data_val, np.ma.core.MaskedConstant): # 결측값 처리
                            row.append('') 
                        elif isinstance(data_val, np.generic): # numpy 스칼라 타입 처리 (e.g., np.float32)
                            row.append(data_val.item())
                        else: # 일반 Python 숫자 타입
                            row.append(data_val)
                    # writer.writerow(row)
                    
                    # --- 필터링 로직 시작 ---
                    write_this_row = True
                    
                    # 데이터 열만 추출 (time, grid_id 다음부터)
                    # data_variable_names가 비어있으면 data_values도 비어있게 됨
                    data_values = row[2:] # grid_id가 추가되었으므로 인덱스 조정

                    if data_values: 
                        if any(val == '' for val in data_values):
                            write_this_row = False
                        else:
                            try:
                                if all(float(val) == 0.0 for val in data_values):
                                    write_this_row = False
                            except ValueError:
                                print(f"경고: CSV 행의 데이터 값 중 숫자로 변환할 수 없는 값이 있습니다. 행: {row}, 해당 값들: {data_values}")
                                pass 
                                
                    if write_this_row:
                        writer.writerow(row)
                    # --- 필터링 로직 끝 ---
    
    print(f"성공적으로 변환 완료: {output_csv_path}")

# CSV 파일을 저장할 기본 출력 디렉토리 설정
# 기존 base_dir의 경로 구조를 참고하여 CSV 저장 경로를 설정합니다.
base_dir = r'F:\Study\santa-close-ai\data-preprocess-hub\data\fuel'
origin_dir = os.path.join(base_dir, 'raw')

# 기본 CSV 출력 디렉토리가 없으면 생성
csv_output_base_dir = os.path.join(base_dir, 'csv')
os.makedirs(csv_output_base_dir, exist_ok=True)

dfmc_dir = 'DFMC'
fuel_dir = 'FUEL'
lfmc_dir = 'LFMC'

# --- 처리할 데이터셋 정보 정의 ---
datasets_info = [
    {
        "subdir_name": dfmc_dir,
        "variables_to_extract": ['DFMC_Foliage', 'DFMC_Wood']
    },
    {
        "subdir_name": fuel_dir,
        "variables_to_extract": ['Live_Leaf', 'Live_Wood', 'Dead_Foliage', 'Dead_Wood']
    },
    {
        "subdir_name": lfmc_dir,
        "variables_to_extract": ['LFMC', 'LFMC_low', 'LFMC_high']
    }
]

# --- 각 데이터셋을 순회하며 CSV로 변환 ---
for info in datasets_info:   
    # 출력 CSV 경로 구성
    # 예: F:\Study\santa-close-ai\data-preprocess-hub\data\fuel\csv\DFMC
    subdir_name = info["subdir_name"]
    csv_specific_subdir = os.path.join(csv_output_base_dir, subdir_name)

    # CSV 파일을 저장할 특정 하위 디렉토리 생성 (이미 있으면 무시)
    os.makedirs(csv_specific_subdir, exist_ok=True)

    # 원본 파일명에서 확장자 변경하여 CSV 파일명 생성
    file_path = os.path.join(origin_dir, subdir_name)
    file_list = os.listdir(file_path)
    file_list_nc = [file for file in file_list if file.endswith(".nc")]
    # file_list_nc = [file for file in file_list if '2021_12' in file and file.endswith(".nc")] # .nc 확장자 명시적 확인 추가
    file_list_nc.reverse()
    # print(*file_list_nc, sep='\n')

    for file_name in file_list_nc:
        csv_filename = os.path.splitext(file_name)[0] + '.csv'
        # print(csv_filename)
        
        # 최종 CSV 파일 전체 경로
        output_csv_full_path = os.path.join(csv_specific_subdir, csv_filename)
        # print(output_csv_full_path)
        
        origin_filename = os.path.join(origin_dir, subdir_name, file_name)
        # print(origin_filename)
        
        try: # nc.Dataset 로딩 중 발생할 수 있는 오류 처리
            with nc.Dataset(origin_filename) as nc_ds: # with 문을 사용하여 자동 close 보장
                convert_nc_to_csv(
                    nc_dataset=nc_ds,
                    output_csv_path=output_csv_full_path,
                    data_variable_names=info["variables_to_extract"]
                )
        except FileNotFoundError:
            print(f"오류: NetCDF 파일을 찾을 수 없습니다 - {origin_filename}")
        except Exception as e:
            print(f"오류: {origin_filename} 처리 중 예외 발생 - {e}")


print("\n모든 NetCDF 파일의 CSV 변환 작업이 완료되었습니다.")
