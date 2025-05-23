#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import pandas as pd
import numpy as np
import argparse
import logging
from datetime import datetime

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('join_weather_target')

def setup_arg_parser():
    """인자 파서를 설정하고 반환합니다."""
    parser = argparse.ArgumentParser(description='날씨 데이터와 타겟(af_flag) 데이터 결합')
    
    parser.add_argument('--weather-file', type=str, required=True,
                        help='처리된 날씨 데이터 파일 경로(CSV 또는 Parquet)')
    parser.add_argument('--target-file', type=str, required=True,
                        help='처리된 타겟 데이터 파일 경로(CSV 또는 Parquet)')
    parser.add_argument('--output-file', type=str, required=True,
                        help='결합된 데이터의 출력 파일 경로(CSV 또는 Parquet 형식)')
    parser.add_argument('--date-col', type=str, default='acq_date',
                        help='날짜 열 이름(기본값: acq_date)')
    parser.add_argument('--interpolate-missing', action='store_true',
                        help='누락된 날씨 데이터를 보간')
    parser.add_argument('--fill-zeros', action='store_true',
                        help='누락된 af_flag 값을 0으로 채우기')
    
    return parser

def load_data(file_path):
    """
    CSV 또는 Parquet 파일에서 데이터를 로드합니다.
    
    매개변수:
    -----------
    file_path : str
        데이터 파일 경로
        
    반환:
    --------
    pandas.DataFrame
        로드된 데이터
    """
    logger.info(f"Loading data from {file_path}")
    
    # 확장자에서 파일 형식 결정
    _, ext = os.path.splitext(file_path)
    ext = ext.lower()
    
    if ext == '.parquet':
        df = pd.read_parquet(file_path)
    else:  # 기본적으로 CSV로 설정
        df = pd.read_csv(file_path)
    
    logger.info(f"Loaded {len(df)} rows from {file_path}")
    return df

def join_data(weather_df, target_df, date_col='acq_date', fill_zeros=False):
    """
    날짜와 grid_id를 기준으로 날씨 데이터와 타겟 데이터를 결합합니다.
    
    매개변수:
    -----------
    weather_df : pandas.DataFrame
        처리된 날씨 데이터
    target_df : pandas.DataFrame
        처리된 타겟 데이터(af_flag)
    date_col : str
        날짜 열 이름
    fill_zeros : bool
        누락된 af_flag 값을 0으로 채울지 여부
        
    반환:
    --------
    pandas.DataFrame
        결합된 데이터
    """
    logger.info("Joining weather and target data")
    
    # 날짜 열이 datetime인지 확인
    weather_df[date_col] = pd.to_datetime(weather_df[date_col])
    target_df[date_col] = pd.to_datetime(target_df[date_col])
    
    # 두 데이터셋에서 고유한 날짜와 grid_id 가져오기
    unique_dates = pd.concat([weather_df[date_col], target_df[date_col]]).unique()
    unique_grids = pd.concat([weather_df['grid_id'], target_df['grid_id']]).unique()
    
    logger.info(f"Found {len(unique_dates)} unique dates and {len(unique_grids)} unique grid IDs")
    
    # 옵션 1: 날짜와 grid_id로 병합
    merged_df = pd.merge(
        weather_df,
        target_df[['acq_date', 'grid_id', 'af_flag']],
        how='left',
        on=['acq_date', 'grid_id']
    )
    
    # 지정된 경우 누락된 af_flag 값을 0으로 채우기
    if fill_zeros:
        merged_df['af_flag'] = merged_df['af_flag'].fillna(0).astype(int)
        logger.info("Filled missing af_flag values with 0")
    
    logger.info(f"Joined data has {len(merged_df)} rows")
    
    # 통계 계산
    af_positive = (merged_df['af_flag'] == 1).sum()
    af_missing = merged_df['af_flag'].isna().sum()
    
    logger.info(f"af_flag=1 count: {af_positive}")
    logger.info(f"af_flag=missing count: {af_missing}")
    
    return merged_df

def interpolate_weather_data(df, date_col='acq_date'):
    """
    누락된 날씨 데이터를 보간합니다.
    
    매개변수:
    -----------
    df : pandas.DataFrame
        잠재적으로 누락된 날씨 값이 있는 데이터
    date_col : str
        날짜 열 이름
        
    반환:
    --------
    pandas.DataFrame
        보간된 날씨 값이 있는 데이터
    """
    logger.info("Interpolating missing weather data")
    
    # grid_id로 그룹화하고 날짜별로 정렬
    grouped = df.groupby('grid_id')
    interpolated_dfs = []
    
    # 날씨 열(날짜, grid_id 또는 af_flag가 아닌)
    weather_cols = [col for col in df.columns if col not in [date_col, 'grid_id', 'af_flag']]
    
    # 각 그룹 보간
    for grid_id, group in grouped:
        group_sorted = group.sort_values(date_col)
        group_sorted[weather_cols] = group_sorted[weather_cols].interpolate(method='linear')
        interpolated_dfs.append(group_sorted)
    
    # 보간된 데이터 결합
    result = pd.concat(interpolated_dfs)
    
    # 통계 계산
    before_missing = df[weather_cols].isna().sum().sum()
    after_missing = result[weather_cols].isna().sum().sum()
    
    logger.info(f"Interpolated {before_missing - after_missing} missing weather values")
    
    return result

def main():
    """날씨와 타겟 데이터를 결합하는 주요 함수."""
    # 명령줄 인수 구문 분석
    parser = setup_arg_parser()
    args = parser.parse_args()
    
    # 데이터 로드
    weather_df = load_data(args.weather_file)
    target_df = load_data(args.target_file)
    
    # 데이터 결합
    joined_data = join_data(
        weather_df,
        target_df,
        date_col=args.date_col,
        fill_zeros=args.fill_zeros
    )
    
    # 지정된 경우 누락된 날씨 데이터 보간
    if args.interpolate_missing:
        joined_data = interpolate_weather_data(joined_data, date_col=args.date_col)
    
    # 출력 디렉토리가 없으면 생성
    output_dir = os.path.dirname(args.output_file)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # 아직 없는 경우 출력 파일 이름에 날짜 범위 추가
    output_file = args.output_file
    min_date = joined_data[args.date_col].min().strftime('%Y%m')
    max_date = joined_data[args.date_col].max().strftime('%Y%m')
    
    # 파일 이름에 이미 날짜가 포함되어 있는지 확인
    base_name, ext = os.path.splitext(output_file)
    if not (min_date in base_name and max_date in base_name):
        date_range = f"{min_date}-{max_date}"
        new_base_name = f"{base_name}_{date_range}"
        output_file = f"{new_base_name}{ext}"
        logger.info(f"Added date range to output filename: {output_file}")
    
    # 파일 확장자에서 출력 형식 결정
    _, ext = os.path.splitext(output_file)
    ext = ext.lower()
    
    # 결합된 데이터 저장
    if ext == '.parquet':
        joined_data.to_parquet(output_file, index=False)
    else:  # 기본적으로 CSV로 설정
        joined_data.to_csv(output_file, index=False)
    
    logger.info(f"Saved joined data to {output_file}")
    
    # 최종 통계 출력
    total_rows = len(joined_data)
    active_fires = (joined_data['af_flag'] == 1).sum()
    active_fire_percentage = (active_fires / total_rows) * 100
    
    logger.info(f"Final dataset has {total_rows} total rows")
    logger.info(f"Active fires (af_flag=1): {active_fires} ({active_fire_percentage:.6f}%)")

if __name__ == '__main__':
    main() 