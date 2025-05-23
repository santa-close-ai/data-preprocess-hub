#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import pandas as pd
import numpy as np
import argparse
import glob
import logging
from datetime import datetime
import multiprocessing as mp
from functools import partial

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('process_weather')

def setup_arg_parser():
    """인자 파서를 설정하고 반환합니다."""
    parser = argparse.ArgumentParser(description='날씨 데이터를 그리드 기반 형식으로 처리')
    
    parser.add_argument('--input-dir', type=str, required=True,
                        help='원시 날씨 데이터 파일이 포함된 디렉토리')
    parser.add_argument('--output-file', type=str, required=True,
                        help='처리된 데이터의 출력 파일 경로(CSV 또는 Parquet 형식)')
    parser.add_argument('--start-date', type=str,
                        help='필터링을 위한 시작 날짜(YYYY-MM-DD 형식)')
    parser.add_argument('--end-date', type=str, 
                        help='필터링을 위한 종료 날짜(YYYY-MM-DD 형식)')
    parser.add_argument('--grid-file', type=str,
                        help='그리드 정의가 포함된 파일(필요한 경우)')
    parser.add_argument('--n-processes', type=int, default=1,
                        help='병렬 처리에 사용할 프로세스 수')
    parser.add_argument('--include-wind', action='store_true',
                        help='출력에 바람 데이터 포함')
    
    return parser

def find_weather_files(input_dir):
    """입력 디렉토리에서 모든 날씨 데이터 파일을 찾습니다."""
    logger.info(f"Searching for weather data files in {input_dir}")
    
    # 일반적인 날씨 파일 패턴 정의
    file_patterns = [
        "*.csv",
        "*.nc",
        "*.grib",
        "*.grib2",
        "*.h5",
        "*.hdf"
    ]
    
    all_files = []
    for pattern in file_patterns:
        path_pattern = os.path.join(input_dir, pattern)
        found_files = glob.glob(path_pattern)
        all_files.extend(found_files)
    
    logger.info(f"Found {len(all_files)} weather data files")
    return all_files

def process_weather_file(file_path, start_date=None, end_date=None, include_wind=False):
    """
    단일 날씨 데이터 파일을 처리합니다.
    
    매개변수:
    -----------
    file_path : str
        날씨 데이터 파일 경로
    start_date : str 또는 None
        필터링을 위한 선택적 시작 날짜(YYYY-MM-DD 형식)
    end_date : str 또는 None
        필터링을 위한 선택적 종료 날짜(YYYY-MM-DD 형식)
    include_wind : bool
        바람 데이터 열을 포함할지 여부
        
    반환:
    --------
    pandas.DataFrame
        처리된 날씨 데이터
    """
    logger.info(f"Processing {file_path}")
    
    # 확장자에서 파일 형식 결정
    _, ext = os.path.splitext(file_path)
    ext = ext.lower()
    
    try:
        # 파일 유형에 따라 데이터 로드
        if ext == '.csv':
            df = pd.read_csv(file_path)
        elif ext in ['.nc', '.grib', '.grib2']:
            # NetCDF 또는 GRIB 파일의 경우, 적절한 라이브러리 사용
            # 이것은 단순화된 자리 표시자 - 실제 구현은 xarray 또는 유사한 것을 사용
            raise NotImplementedError(f"Processing of {ext} files is not implemented")
        elif ext in ['.h5', '.hdf']:
            # HDF 파일의 경우
            raise NotImplementedError(f"Processing of {ext} files is not implemented")
        else:
            logger.warning(f"Unsupported file format: {ext}")
            return None
        
        # 날짜 열이 존재하는 경우 datetime으로 변환
        date_columns = [col for col in df.columns if 'date' in col.lower()]
        if date_columns:
            df[date_columns[0]] = pd.to_datetime(df[date_columns[0]])
            
            # 지정된 경우 날짜 필터링 적용
            if start_date:
                start_date = pd.to_datetime(start_date)
                df = df[df[date_columns[0]] >= start_date]
            
            if end_date:
                end_date = pd.to_datetime(end_date)
                df = df[df[date_columns[0]] <= end_date]
        
        # 특정 파일 구조에 따라 처리
        # 이는 입력 데이터 형식에 크게 의존
        # 예제 처리:
        if 'grid_id' not in df.columns and 'latitude' in df.columns and 'longitude' in df.columns:
            # 필요한 경우 위도/경도를 그리드 ID로 변환
            df['grid_id'] = latlon_to_grid_id(df['latitude'], df['longitude'])
        
        # 관련 날씨 변수 추출
        weather_vars = ['temperature', 'relative_humidity', 'precipitation', 'wind_speed', 'wind_direction']
        available_vars = [var for var in weather_vars if any(col.lower().startswith(var.lower()) for col in df.columns)]
        
        # 사용 가능한 변수와 바람 포함 여부에 따라 열 필터링
        if not include_wind:
            available_vars = [var for var in available_vars if not var.startswith('wind')]
        
        # 선택한 열로 새 데이터프레임 생성
        result_columns = date_columns + ['grid_id'] + [col for col in df.columns if any(var.lower() in col.lower() for var in available_vars)]
        result_df = df[result_columns].copy()
        
        logger.info(f"Processed {file_path}, extracted {len(result_df)} rows")
        return result_df
        
    except Exception as e:
        logger.error(f"Error processing {file_path}: {e}")
        return None

def latlon_to_grid_id(lat, lon):
    """
    위도와 경도를 그리드 ID로 변환합니다.
    
    그리드 시스템:
    - 0.1도 전역 그리드
    - 그리드 ID = (latitude_index + 900) * 3600 + (longitude_index + 1800)
    - 위도 인덱스는 -90(남쪽)에서 +90(북쪽)까지 시작
    - 경도 인덱스는 -180(서쪽)에서 +180(동쪽)까지 시작
    
    매개변수:
    -----------
    lat : float 또는 array-like
        위도 값
    lon : float 또는 array-like
        경도 값
        
    반환:
    --------
    int 또는 array-like
        그리드 ID
    """
    # 위도/경도를 그리드 인덱스로 변환
    lat_idx = np.floor(lat * 10).astype(int) + 900
    lon_idx = np.floor(lon * 10).astype(int) + 1800
    
    # 그리드 ID 계산
    grid_id = lat_idx * 3600 + lon_idx
    
    return grid_id

def grid_id_to_latlon(grid_id):
    """
    그리드 ID를 위도와 경도로 변환합니다.
    
    매개변수:
    -----------
    grid_id : int 또는 array-like
        그리드 ID
        
    반환:
    --------
    tuple : (위도, 경도) 튜플
    """
    # 위도 및 경도 인덱스 추출
    lat_idx = np.floor_divide(grid_id, 3600) - 900
    lon_idx = np.remainder(grid_id, 3600) - 1800
    
    # 실제 위도 및 경도로 변환(그리드 셀의 중심)
    lat = lat_idx * 0.1 + 0.05
    lon = lon_idx * 0.1 + 0.05
    
    return lat, lon

def main():
    """날씨 데이터를 처리하는 주요 함수."""
    # 명령줄 인수 구문 분석
    parser = setup_arg_parser()
    args = parser.parse_args()
    
    # 날씨 파일 찾기
    weather_files = find_weather_files(args.input_dir)
    
    if not weather_files:
        logger.error(f"No weather files found in {args.input_dir}")
        return
    
    # 파일 처리(잠재적으로 병렬)
    if args.n_processes > 1:
        logger.info(f"Processing files in parallel with {args.n_processes} processes")
        pool = mp.Pool(processes=args.n_processes)
        process_func = partial(
            process_weather_file,
            start_date=args.start_date,
            end_date=args.end_date,
            include_wind=args.include_wind
        )
        results = pool.map(process_func, weather_files)
        pool.close()
        pool.join()
        
        # None 결과 필터링
        valid_results = [df for df in results if df is not None]
        
        # 결과 결합
        if valid_results:
            combined_df = pd.concat(valid_results, ignore_index=True)
        else:
            logger.error("No valid results after processing")
            return
    else:
        # 순차적으로 처리
        logger.info("Processing files sequentially")
        results = []
        for file in weather_files:
            result = process_weather_file(
                file,
                start_date=args.start_date,
                end_date=args.end_date,
                include_wind=args.include_wind
            )
            if result is not None:
                results.append(result)
        
        # 결과 결합
        if results:
            combined_df = pd.concat(results, ignore_index=True)
        else:
            logger.error("No valid results after processing")
            return
    
    # 중복 제거
    logger.info(f"Combined data has {len(combined_df)} rows")
    combined_df = combined_df.drop_duplicates()
    logger.info(f"After removing duplicates: {len(combined_df)} rows")
    
    # 출력 디렉토리가 없으면 생성
    output_dir = os.path.dirname(args.output_file)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # 파일 확장자에 따라 결과 저장
    _, ext = os.path.splitext(args.output_file)
    ext = ext.lower()
    
    if ext == '.parquet':
        combined_df.to_parquet(args.output_file, index=False)
    else:  # 기본적으로 CSV로 설정
        combined_df.to_csv(args.output_file, index=False)
    
    logger.info(f"Saved processed weather data to {args.output_file}")

if __name__ == '__main__':
    main() 