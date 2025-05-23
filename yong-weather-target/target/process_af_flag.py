#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import pandas as pd
import numpy as np
import argparse
from datetime import datetime
import logging
import glob

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('process_af_flag')

def setup_arg_parser():
    """인자 파서를 설정하고 반환합니다."""
    parser = argparse.ArgumentParser(description='MODIS 활성 화재 데이터를 그리드 기반 형식으로 처리')
    
    parser.add_argument('--input-dir', type=str, required=True,
                        help='원시 MODIS 활성 화재 CSV 파일이 포함된 디렉토리')
    parser.add_argument('--output-file', type=str, required=True,
                        help='처리된 데이터의 출력 파일 경로(CSV 형식)')
    parser.add_argument('--min-confidence', type=int, default=30,
                        help='화재 감지를 위한 최소 신뢰도 수준(기본값: 30)')
    parser.add_argument('--date-col', type=str, default='acq_date',
                        help='입력 파일의 획득 날짜 열 이름(기본값: "acq_date")')
    parser.add_argument('--start-date', type=str,
                        help='필터링을 위한 시작 날짜(YYYY-MM-DD 형식)')
    parser.add_argument('--end-date', type=str, 
                        help='필터링을 위한 종료 날짜(YYYY-MM-DD 형식)')
    
    return parser

def load_af_data(input_dir, date_col='acq_date', start_date=None, end_date=None):
    """
    입력 디렉토리의 CSV 파일에서 MODIS 활성 화재 데이터를 로드합니다.
    
    매개변수:
    -----------
    input_dir : str
        원시 MODIS 활성 화재 CSV 파일이 포함된 디렉토리
    date_col : str
        입력 파일의 획득 날짜 열 이름
    start_date : str 또는 None
        필터링을 위한 선택적 시작 날짜(YYYY-MM-DD 형식)
    end_date : str 또는 None
        필터링을 위한 선택적 종료 날짜(YYYY-MM-DD 형식)
        
    반환:
    --------
    pandas.DataFrame
        모든 활성 화재 데이터의 결합된 데이터프레임
    """
    logger.info(f"Loading active fire data from {input_dir}")
    
    # 입력 디렉토리에서 모든 CSV 파일 찾기
    file_pattern = os.path.join(input_dir, "*.csv")
    csv_files = glob.glob(file_pattern)
    
    if not csv_files:
        logger.error(f"No CSV files found in {input_dir}")
        sys.exit(1)
    
    logger.info(f"Found {len(csv_files)} CSV files")
    
    # 모든 CSV 파일을 데이터프레임 목록으로 로드
    dfs = []
    for file in csv_files:
        logger.debug(f"Loading {file}")
        try:
            df = pd.read_csv(file)
            dfs.append(df)
        except Exception as e:
            logger.error(f"Error loading {file}: {e}")
    
    # 모든 데이터프레임 결합
    combined_df = pd.concat(dfs, ignore_index=True)
    logger.info(f"Combined data has {len(combined_df)} rows")
    
    # 날짜 열을 datetime으로 변환
    combined_df[date_col] = pd.to_datetime(combined_df[date_col])
    
    # 지정된 경우 날짜 필터링 적용
    if start_date:
        start_date = pd.to_datetime(start_date)
        combined_df = combined_df[combined_df[date_col] >= start_date]
        logger.info(f"Filtered data after {start_date}, {len(combined_df)} rows remaining")
    
    if end_date:
        end_date = pd.to_datetime(end_date)
        combined_df = combined_df[combined_df[date_col] <= end_date]
        logger.info(f"Filtered data before {end_date}, {len(combined_df)} rows remaining")
    
    return combined_df

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

def process_af_data(df, min_confidence=30):
    """
    활성 화재 데이터를 그리드 기반 형식으로 처리합니다.
    
    매개변수:
    -----------
    df : pandas.DataFrame
        활성 화재 데이터가 포함된 데이터프레임
    min_confidence : int
        화재 감지를 위한 최소 신뢰도 수준
        
    반환:
    --------
    pandas.DataFrame
        그리드 ID와 af_flag=1이 있는 처리된 데이터프레임
    """
    logger.info(f"Processing active fire data with min_confidence={min_confidence}")
    
    # 신뢰도 수준으로 필터링
    high_conf_df = df[df['confidence'] >= min_confidence].copy()
    logger.info(f"Filtered data with confidence >= {min_confidence}, {len(high_conf_df)} rows remaining")
    
    # 위도/경도를 그리드 ID로 변환
    high_conf_df['grid_id'] = latlon_to_grid_id(high_conf_df['latitude'], high_conf_df['longitude'])
    
    # 고유한 날짜-그리드 조합으로 새 데이터프레임 생성
    # 적어도 하나의 화재가 있는 각 날짜-그리드 조합은 af_flag=1을 얻음
    result_df = high_conf_df.groupby(['acq_date', 'grid_id']).size().reset_index()
    result_df.rename(columns={0: 'fire_count'}, inplace=True)
    
    # af_flag 열 추가(화재가 있는 그리드만 유지하므로 항상 1)
    result_df['af_flag'] = 1
    
    logger.info(f"Final processed data has {len(result_df)} rows")
    
    # 선택 사항: 날짜 및 grid_id로 정렬
    result_df.sort_values(['acq_date', 'grid_id'], inplace=True)
    
    # 필요한 열만 유지
    result_df = result_df[['acq_date', 'grid_id', 'af_flag']]
    
    return result_df

def main():
    """MODIS 활성 화재 데이터를 처리하는 주요 함수."""
    # 명령줄 인수 구문 분석
    parser = setup_arg_parser()
    args = parser.parse_args()
    
    # 활성 화재 데이터 로드
    af_data = load_af_data(
        args.input_dir,
        date_col=args.date_col,
        start_date=args.start_date,
        end_date=args.end_date
    )
    
    # 데이터 처리
    processed_data = process_af_data(af_data, min_confidence=args.min_confidence)
    
    # 처리된 데이터 저장
    output_dir = os.path.dirname(args.output_file)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    processed_data.to_csv(args.output_file, index=False)
    logger.info(f"Saved processed data to {args.output_file}")

if __name__ == '__main__':
    main() 