#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np
import argparse
import os
import logging
from datetime import datetime

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('validate_af_flag')

def setup_arg_parser():
    """인자 파서를 설정하고 반환합니다."""
    parser = argparse.ArgumentParser(description='af_flag 데이터 처리 검증')
    
    parser.add_argument('--original-data', type=str, required=True,
                        help='원본 MODIS 활성 화재 데이터 파일 경로 (CSV 형식)')
    parser.add_argument('--processed-data', type=str, required=True,
                        help='처리된 af_flag 데이터 파일 경로 (CSV 형식)')
    parser.add_argument('--output-dir', type=str, default='outputs/validation',
                        help='검증 결과 출력 디렉토리')
    parser.add_argument('--min-confidence', type=int, default=30,
                        help='화재 감지 최소 신뢰도 수준 (기본값: 30)')
    parser.add_argument('--date-col', type=str, default='acq_date',
                        help='날짜 열 이름 (기본값: acq_date)')
    
    return parser

def latlon_to_grid_id(lat, lon):
    """
    위도와 경도를 그리드 ID로 변환합니다.
    
    그리드 시스템:
    - 0.1도 전역 그리드
    - 그리드 ID = (위도_인덱스 + 900) * 3600 + (경도_인덱스 + 1800)
    - 위도 인덱스는 -90(남) ~ +90(북)에서 시작
    - 경도 인덱스는 -180(서) ~ +180(동)에서 시작
    
    매개변수:
    -----------
    lat : float 또는 array-like
        위도 값
    lon : float 또는 array-like
        경도 값
        
    반환값:
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

def validate_af_flag_processing(original_file, processed_file, min_confidence=30, date_col='acq_date'):
    """
    원본 데이터의 모든 화재 이벤트가 처리된 데이터에 af_flag=1로 
    적절하게 표현되었는지 검증합니다.
    
    매개변수:
    -----------
    original_file : str
        원본 MODIS 활성 화재 데이터 파일 경로
    processed_file : str
        처리된 af_flag 데이터 파일 경로
    min_confidence : int
        화재 감지 최소 신뢰도 수준
    date_col : str
        날짜 열 이름
        
    반환값:
    --------
    dict
        검증 결과
    """
    logger.info(f"af_flag 처리 검증 중")
    logger.info(f"원본 데이터: {original_file}")
    logger.info(f"처리된 데이터: {processed_file}")
    
    # 데이터 로드
    original_df = pd.read_csv(original_file)
    processed_df = pd.read_csv(processed_file)
    
    logger.info(f"원본 데이터 크기: {original_df.shape}")
    logger.info(f"처리된 데이터 크기: {processed_df.shape}")
    
    # 신뢰도 수준으로 원본 데이터 필터링
    high_conf_df = original_df[original_df['confidence'] >= min_confidence].copy()
    logger.info(f"신뢰도 >= {min_confidence}인 원본 데이터: {len(high_conf_df)} 행")
    
    # 원본 데이터에서 위도/경도를 그리드 ID로 변환
    high_conf_df['grid_id'] = latlon_to_grid_id(high_conf_df['latitude'], high_conf_df['longitude'])
    
    # 날짜 열이 datetime 형식인지 확인
    high_conf_df[date_col] = pd.to_datetime(high_conf_df[date_col])
    processed_df[date_col] = pd.to_datetime(processed_df[date_col])
    
    # 원본 데이터에서 고유한 날짜-그리드 조합 계산
    original_date_grid_pairs = high_conf_df.groupby([date_col, 'grid_id']).size().reset_index()
    original_date_grid_pairs.rename(columns={0: 'fire_count'}, inplace=True)
    
    logger.info(f"원본 데이터의 고유 날짜-그리드 쌍: {len(original_date_grid_pairs)}")
    
    # 처리된 데이터 확인
    processed_positive = processed_df[processed_df['af_flag'] == 1]
    logger.info(f"af_flag=1인 처리된 데이터: {len(processed_positive)} 행")
    
    # 쉬운 비교를 위한 날짜-그리드 쌍 집합 생성
    original_pairs = set([
        (row[date_col].strftime('%Y-%m-%d'), row['grid_id']) 
        for _, row in original_date_grid_pairs.iterrows()
    ])
    
    processed_pairs = set([
        (row[date_col].strftime('%Y-%m-%d'), row['grid_id']) 
        for _, row in processed_positive.iterrows()
    ])
    
    # 누락 및 추가 쌍 찾기
    missing_pairs = original_pairs - processed_pairs
    extra_pairs = processed_pairs - original_pairs
    
    # 검증 메트릭 계산
    total_original = len(original_pairs)
    total_processed = len(processed_pairs)
    
    # 원본 및 처리된 쌍이 정확히 일치하는지 확인
    exact_match = (total_original == total_processed) and (len(missing_pairs) == 0) and (len(extra_pairs) == 0)
    
    # 재현율 계산 (보존된 원본 쌍의 비율)
    recall = (total_original - len(missing_pairs)) / total_original if total_original > 0 else 0
    
    # 정밀도 계산 (원본에 있었던 처리된 쌍의 비율)
    precision = (total_processed - len(extra_pairs)) / total_processed if total_processed > 0 else 0
    
    # F1 점수 계산
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    
    # 상세 보고서 작성
    detailed_results = {
        'original_file': original_file,
        'processed_file': processed_file,
        'min_confidence': min_confidence,
        'original_rows': len(original_df),
        'high_conf_rows': len(high_conf_df),
        'processed_rows': len(processed_df),
        'original_date_grid_pairs': total_original,
        'processed_positive_pairs': total_processed,
        'missing_pairs': len(missing_pairs),
        'extra_pairs': len(extra_pairs),
        'exact_match': exact_match,
        'recall': recall,
        'precision': precision,
        'f1_score': f1
    }
    
    # 결과 로깅
    logger.info(f"검증 결과:")
    logger.info(f"  원본 날짜-그리드 쌍: {total_original}")
    logger.info(f"  처리된 af_flag=1 쌍: {total_processed}")
    logger.info(f"  누락된 쌍: {len(missing_pairs)}")
    logger.info(f"  추가된 쌍: {len(extra_pairs)}")
    logger.info(f"  정확한 일치: {exact_match}")
    logger.info(f"  재현율: {recall:.4f}")
    logger.info(f"  정밀도: {precision:.4f}")
    logger.info(f"  F1 점수: {f1:.4f}")
    
    # 누락된 쌍이 있는 경우 일부 예시 로깅
    if missing_pairs:
        sample_missing = list(missing_pairs)[:min(5, len(missing_pairs))]
        logger.warning(f"누락된 날짜-그리드 쌍 예시:")
        for date, grid in sample_missing:
            logger.warning(f"  날짜: {date}, 그리드 ID: {grid}")
    
    return detailed_results

def main():
    """af_flag 처리를 검증하는 메인 함수."""
    # 명령줄 인자 파싱
    parser = setup_arg_parser()
    args = parser.parse_args()
    
    # 출력 디렉토리가 없으면 생성
    if not os.path.exists(args.output_dir):
        os.makedirs(args.output_dir)
    
    # af_flag 처리 검증
    validation_results = validate_af_flag_processing(
        args.original_data,
        args.processed_data,
        min_confidence=args.min_confidence,
        date_col=args.date_col
    )
    
    # 검증 결과를 CSV로 저장
    output_file = os.path.join(args.output_dir, 'af_flag_validation_results.csv')
    pd.DataFrame([validation_results]).to_csv(output_file, index=False)
    logger.info(f"검증 결과를 {output_file}에 저장했습니다")
    
    # 성공 또는 실패 코드 반환
    if validation_results['exact_match']:
        logger.info("검증 통과: 모든 원본 화재 이벤트가 처리된 데이터에 적절하게 표현되었습니다")
        return 0
    else:
        logger.warning("검증 경고: 일부 화재 이벤트가 처리된 데이터에 적절하게 표현되지 않았을 수 있습니다")
        return 1

if __name__ == '__main__':
    main() 