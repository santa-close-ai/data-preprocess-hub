#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as colors
from matplotlib.colors import LinearSegmentedColormap
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import argparse
import os
from datetime import datetime

def grid_id_to_latlon(grid_id):
    """
    그리드 ID를 위도와 경도로 변환합니다.
    
    매개변수:
    -----------
    grid_id : int 또는 array-like
        변환할 그리드 ID
    
    반환:
    --------
    tuple : (위도, 경도) 튜플
    """
    # Row index = int(grid_id / 3600) - 900
    # Col index = grid_id % 3600 - 1800
    lat_idx = np.floor_divide(grid_id, 3600) - 900
    lon_idx = np.remainder(grid_id, 3600) - 1800
    
    # 0.1도 그리드 중심점 계산(0.05도 오프셋 추가)
    lat = lat_idx * 0.1 + 0.05
    lon = lon_idx * 0.1 + 0.05
    
    return lat, lon

def visualize_af_flag_by_year(af_flag_file, output_dir, start_year=None, end_year=None):
    """
    연도별로 한국 지도에 af_flag=1인 그리드를 시각화합니다.
    
    매개변수:
    -----------
    af_flag_file : str
        전처리된 af_flag 데이터 파일 경로
    output_dir : str
        출력 디렉토리 경로
    start_year : int, 선택사항
        시작 연도(기본값: 데이터의 최소 연도)
    end_year : int, 선택사항
        종료 연도(기본값: 데이터의 최대 연도)
    """
    print(f"\n=== af_flag Data Visualization ===")
    print(f"af_flag data: {af_flag_file}")
    print(f"Output directory: {output_dir}")
    
    # 출력 디렉토리 생성
    os.makedirs(output_dir, exist_ok=True)
    
    # 데이터 로드
    print("\n[1/4] Loading data...")
    df = pd.read_csv(af_flag_file)
    print(f"Data size: {df.shape}")
    
    # af_flag 값 개수
    af_flag_counts = df['af_flag'].value_counts()
    print("\naf_flag value counts:")
    print(af_flag_counts)
    
    if 1 not in af_flag_counts:
        print("\nERROR: No af_flag=1 records found in the data!")
        print("Please check if the data file contains fire events.")
        return
    
    # 날짜 변환
    df['acq_date'] = pd.to_datetime(df['acq_date'])
    
    # 연도 추출
    df['year'] = df['acq_date'].dt.year
    
    # 연도 범위 설정
    all_years = sorted(df['year'].unique())
    if start_year is None:
        start_year = min(all_years)
    if end_year is None:
        end_year = max(all_years)
    
    years_to_process = [y for y in all_years if start_year <= y <= end_year]
    print(f"Years to process: {years_to_process}")
    
    # af_flag=1인 데이터만 필터링
    positive_df = df[df['af_flag'] == 1].copy()
    print(f"Number of af_flag=1 records: {len(positive_df)}")
    
    if len(positive_df) == 0:
        print("ERROR: No af_flag=1 records in the specified year range!")
        return
    
    # 그리드 ID를 위도/경도로 변환
    print("\n[2/4] Converting grid IDs to lat/lon...")
    lats, lons = grid_id_to_latlon(positive_df['grid_id'].values)
    positive_df['latitude'] = lats
    positive_df['longitude'] = lons
    
    # 연도별 시각화
    print("\n[3/4] Visualizing by year...")
    for year in years_to_process:
        print(f"Processing year {year}...")
        
        # 해당 연도의 데이터 필터링
        year_df = positive_df[positive_df['year'] == year]
        if len(year_df) == 0:
            print(f"  No af_flag=1 data for year {year}.")
            continue
        
        # 월별 빈도 계산
        monthly_counts = year_df.groupby(year_df['acq_date'].dt.month).size()
        
        # 지도 시각화
        fig = plt.figure(figsize=(15, 10))
        
        # 지도 설정
        ax = plt.axes(projection=ccrs.PlateCarree())
        ax.set_extent([124, 132, 33, 39])  # South Korea region
        
        # 지도 레이어 추가
        ax.add_feature(cfeature.LAND)
        ax.add_feature(cfeature.OCEAN)
        ax.add_feature(cfeature.COASTLINE)
        ax.add_feature(cfeature.BORDERS, linestyle=':')
        
        # 그리드 포인트 표시(단순 산점도)
        ax.scatter(
            year_df['longitude'], 
            year_df['latitude'], 
            c='red', 
            s=10,  # 점 크기를 조금 키움
            alpha=0.7,  # 투명도 조정
            transform=ccrs.PlateCarree(),
            label=f'Fire events ({len(year_df)} points)'
        )
        
        # 정보 추가
        plt.title(f"Fire Locations in {year}")
        plt.legend(loc='upper right')
        
        # 월별 빈도 차트 추가
        ax_inset = fig.add_axes([0.15, 0.15, 0.2, 0.2])
        months = range(1, 13)
        monthly_data = [monthly_counts.get(m, 0) for m in months]
        ax_inset.bar(months, monthly_data, color='darkred')
        ax_inset.set_title('Monthly Fire Occurrences')
        ax_inset.set_xlabel('Month')
        ax_inset.set_ylabel('Count')
        ax_inset.set_xticks(months)
        
        # 파일 저장
        output_file = os.path.join(output_dir, f"af_flag_map_{year}.png")
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"  Map saved: {output_file}")
    
    # 통합 연도 지도 생성
    print("\n[4/4] Creating combined year map with all years...")
    
    # 지도 시각화
    fig = plt.figure(figsize=(15, 10))
    
    # 지도 설정
    ax = plt.axes(projection=ccrs.PlateCarree())
    ax.set_extent([124, 132, 33, 39])  # South Korea region
    
    # 지도 레이어 추가
    ax.add_feature(cfeature.LAND)
    ax.add_feature(cfeature.OCEAN)
    ax.add_feature(cfeature.COASTLINE)
    ax.add_feature(cfeature.BORDERS, linestyle=':')
    
    # 모든 연도 데이터 표시를 위한 색상 설정
    # 모든 연도에 대해 다른 색상 사용 (일관된 색상 맵 사용)
    num_years = len(years_to_process)
    
    # 연도별 색상을 효과적으로 구분하기 위해 더 적합한 컬러맵 선택
    if num_years <= 10:
        cmap = plt.cm.tab10
    elif num_years <= 20:
        cmap = plt.cm.tab20
    else:
        # 많은 연도를 다룰 때는 hsv 컬러맵 사용
        cmap = plt.cm.hsv
    
    colors = cmap(np.linspace(0, 1, num_years))
    
    # 각 연도에 대한 포인트 표시
    for i, year in enumerate(years_to_process):
        year_df = positive_df[positive_df['year'] == year]
        if len(year_df) > 0:
            ax.scatter(
                year_df['longitude'], 
                year_df['latitude'], 
                c=[colors[i]], 
                s=15, 
                alpha=0.7,
                label=f'{year} ({len(year_df)} points)',
                transform=ccrs.PlateCarree()
            )
    
    # 정보 추가
    title = f"Fire Locations {years_to_process[0]}-{years_to_process[-1]}"
    plt.title(title)
    
    # 범례 최적화 (연도가 많을 경우 범례를 조정)
    if num_years > 15:
        # 범례를 2열 또는 3열로 표시
        ncol = 3 if num_years > 25 else 2
        plt.legend(loc='upper right', fontsize='small', ncol=ncol)
    else:
        plt.legend(loc='upper right')
    
    # 파일 저장
    output_file = os.path.join(output_dir, f"af_flag_map_combined_all_years.png")
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Combined map with all years saved: {output_file}")
    
    # 연도별 통계 출력
    yearly_stats = positive_df.groupby('year').size().sort_index()
    print("\nYearly af_flag=1 counts:")
    for year, count in yearly_stats.items():
        print(f"{year}: {count} points")
    
    print("\n=== af_flag data visualization complete ===")

def main():
    parser = argparse.ArgumentParser(description='af_flag data visualization')
    parser.add_argument('--input', type=str, required=True,
                        help='Path to preprocessed af_flag data file')
    parser.add_argument('--output-dir', type=str, default='outputs/visualizations',
                        help='Output directory path (default: outputs/visualizations)')
    parser.add_argument('--start-year', type=int,
                        help='Start year')
    parser.add_argument('--end-year', type=int,
                        help='End year')
    
    args = parser.parse_args()
    
    visualize_af_flag_by_year(
        args.input,
        args.output_dir,
        start_year=args.start_year,
        end_year=args.end_year
    )

if __name__ == '__main__':
    main() 