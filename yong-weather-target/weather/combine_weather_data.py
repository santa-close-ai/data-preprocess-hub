#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import pandas as pd
import numpy as np
import argparse
import glob
import logging
from datetime import datetime

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('combine_weather_data')

def setup_arg_parser():
    """인자 파서를 설정하고 반환합니다."""
    parser = argparse.ArgumentParser(description='처리된 날씨 데이터 파일 결합')
    
    parser.add_argument('--input-dir', type=str, required=True,
                        help='처리된 날씨 데이터 파일이 있는 디렉토리')
    parser.add_argument('--output-file', type=str, required=True,
                        help='결합된 데이터 출력 파일 경로 (CSV 또는 Parquet 형식)')
    parser.add_argument('--start-date', type=str,
                        help='필터링 시작 날짜 (YYYY-MM-DD 형식)')
    parser.add_argument('--end-date', type=str, 
                        help='필터링 종료 날짜 (YYYY-MM-DD 형식)')
    
    return parser

def combine_weather_files(input_dir, start_date=None, end_date=None):
    """
    입력 디렉토리의 모든 처리된 날씨 데이터 파일을 결합합니다.
    
    매개변수:
    -----------
    input_dir : str
        처리된 날씨 데이터 파일이 있는 디렉토리
    start_date : str 또는 None
        필터링 시작 날짜 (YYYY-MM-DD 형식, 선택적)
    end_date : str 또는 None
        필터링 종료 날짜 (YYYY-MM-DD 형식, 선택적)
        
    반환값:
    --------
    pandas.DataFrame
        결합된 날씨 데이터
    """
    logger.info(f"{input_dir}에서 날씨 데이터 파일 결합 중")
    
    # 모든 날씨 데이터 파일 찾기
    file_pattern = os.path.join(input_dir, "*.csv")
    csv_files = glob.glob(file_pattern)
    
    file_pattern = os.path.join(input_dir, "*.parquet")
    parquet_files = glob.glob(file_pattern)
    
    all_files = csv_files + parquet_files
    
    if not all_files:
        logger.error(f"{input_dir}에서 날씨 데이터 파일을 찾을 수 없습니다")
        return None
    
    logger.info(f"{len(all_files)}개의 날씨 데이터 파일을 찾았습니다")
    
    # 모든 파일 로드 및 결합
    dfs = []
    for file in all_files:
        logger.info(f"{file} 처리 중")
        try:
            # 확장자에 따라 파일 로드
            if file.endswith('.csv'):
                df = pd.read_csv(file)
            elif file.endswith('.parquet'):
                df = pd.read_parquet(file)
            else:
                logger.warning(f"지원되지 않는 파일 형식: {file}")
                continue
                
            # 날짜 열 식별
            date_columns = [col for col in df.columns if 'date' in col.lower()]
            if not date_columns:
                logger.warning(f"{file}에서 날짜 열을 찾을 수 없습니다, 건너뜁니다")
                continue
                
            date_col = date_columns[0]
            
            # 날짜 열을 datetime으로 변환
            df[date_col] = pd.to_datetime(df[date_col])
            
            # 지정된 경우 날짜 필터링 적용
            if start_date:
                start_date_obj = pd.to_datetime(start_date)
                df = df[df[date_col] >= start_date_obj]
                
            if end_date:
                end_date_obj = pd.to_datetime(end_date)
                df = df[df[date_col] <= end_date_obj]
                
            dfs.append(df)
            
        except Exception as e:
            logger.error(f"{file} 처리 중 오류 발생: {e}")
    
    if not dfs:
        logger.error("처리된 유효한 데이터 파일이 없습니다")
        return None
        
    # 모든 데이터프레임 결합
    combined_df = pd.concat(dfs, ignore_index=True)
    
    # 중복 제거
    n_before = len(combined_df)
    combined_df = combined_df.drop_duplicates()
    n_after = len(combined_df)
    
    if n_before > n_after:
        logger.info(f"{n_before - n_after}개의 중복 행을 제거했습니다")
    
    logger.info(f"결합된 데이터에는 {len(combined_df)}개의 행이 있습니다")
    
    return combined_df

def main():
    """날씨 데이터 파일을 결합하는 메인 함수."""
    # 명령줄 인자 파싱
    parser = setup_arg_parser()
    args = parser.parse_args()
    
    # 날씨 파일 결합
    combined_data = combine_weather_files(
        args.input_dir,
        start_date=args.start_date,
        end_date=args.end_date
    )
    
    if combined_data is None:
        return
    
    # 출력 디렉토리가 없으면 생성
    output_dir = os.path.dirname(args.output_file)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # 파일 확장자에서 출력 형식 결정
    _, ext = os.path.splitext(args.output_file)
    ext = ext.lower()
    
    # 결합된 데이터 저장
    if ext == '.parquet':
        combined_data.to_parquet(args.output_file, index=False)
    else:  # 기본적으로 CSV
        combined_data.to_csv(args.output_file, index=False)
    
    logger.info(f"결합된 날씨 데이터를 {args.output_file}에 저장했습니다")

if __name__ == '__main__':
    main() 