# 대한민국 월별 잎 면적 지수(LAI) 데이터

## 개요

이 저장소에는 Copernicus LAI v2 데이터를 바탕으로 대한민국(경도 124°E\~132°E, 위도 33°N\~39°N) 구역을 0.1° × 0.1° 해상도로 재처리한 저층(`lai_low`) 및 고층(`lai_high`) 잎 면적 지수(Leaf Area Index) 월별 평균값이 포함되어 있습니다.

- **LAI (Leaf Area Index)**: 단위 지면 면적당 식물 잎 면적의 비율(m²/m²)로, 식생량·연료량 및 광합성 활동의 지표로 활용됩니다.
- **저층 식생(`lai_low`)**: 초지, 관목 등 하층 식생을 대표
- **고층 식생(`lai_high`)**: 숲 상층부 수목을 대표

## 원본 데이터

- **원본 데이터셋**: ed48f79bc88a221192613d5f105743ed.nc (Copernicus LAI v2 (월별 합성, 300 m 해상도))
- **공간 범위**: 경도 124°E\~132°E, 위도 33°N\~39°N
- **시간 범위**: 2000-01-01 \~ 2025-04-01 (월별_YYYY-MM-01)
- **라이선스**: Copernicus Data License Agreement (공개)

## 전처리 데이터

1. **결측지 대체**: lai_lv, lai_hv 변수에서 NaN → 0.0 
2. **그리드 ID 계산**: 위도·경도 → 0.1° 그리드 중심에 대응시키는 단일 정수값`grid_id` 부여
3. **월별·그리드별 평균**: 각 (grid_id, date) 조합에서 픽셀별 LAI 값을 평균
6. **전처리 파일목록**:
   - Parquet(`lai_low_high_monthly.parquet`)
   - CSV(`lai_low_high_monthly.csv`)

  - **컬럼**:
    - `date` : 월별 기준일 (YYYY-MM-01)
    - `grid_id` : 0.1° 그리드 셀 ID (아래 \[그리드 인덱싱] 참조)
    - `lai_low` : 저층 식생 LAI (m²/m²)
    - `lai_high` : 고층 식생 LAI (m²/m²)

## 시각화 히트맵 예시

- **LAI 저층 (2020-04)**

  ![LAI Low Vegetation – 2020-04](lai_low.png)

- **LAI 고층 (2020-04)**

  ![LAI High Vegetation – 2020-04](lai_high.png)

---

_생성일: 2025-05-22_
