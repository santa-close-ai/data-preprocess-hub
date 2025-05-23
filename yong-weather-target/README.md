# Weather, Target(MODIS af_flag)

## 개요

전처리 워크플로우는 두 가지 주요 데이터 흐름으로 구성됩니다:

1. **타겟 데이터(af_flag)**: MODIS 활성 화재 데이터 처리
2. **날씨 데이터**: 기상 변수(온도, 습도 등) 수집 및 처리

## 데이터 수집 및 전처리 과정

### 1. 타겟 데이터(af_flag) 처리

- **수집**: NASA FIRMS를 통해 MODIS 활성 화재 데이터 다운로드
- **전처리**: `process_af_flag.py`로 데이터 처리
  - 신뢰도 기준 필터링(기본값: 30)
  - 위도/경도를 0.1° 그리드로 변환
  - 날짜-그리드 조합별 화재 발생 여부 집계
- **검증**: `validate_af_flag.py`로 처리 결과 검증

### 2. 날씨 데이터 처리

- **수집**: `collect_weather.py`로 ERA5-Land 데이터 수집
  - 날씨 변수: 기온, 이슬점 온도, 풍속, 강수량
- **전처리**: `process_weather.py`로 날씨 파일 처리
  - 관련 변수 추출 후 0.1° 그리드로 변환
- **결합**: `combine_weather_data.py`로 처리된 날씨 파일 통합

### 3. 데이터 통합

- **결합**: `join_weather_target.py`로 날씨와 타겟 데이터 결합
  - 날짜 및 그리드 ID 기준으로 결합
  - 결과: 각 행은 특정 날짜의 그리드 셀 데이터 포함

## 그리드 시스템

0.1도 전역 그리드 시스템으로 모든 데이터 통합:

- 그리드 ID = (lat_index + 900) \* 3600 + (lon_index + 1800)
- lat_index = floor(latitude \* 10)
- lon_index = floor(longitude \* 10)

## 데이터 시각화

`visualize_af_flag.py`로 화재 분포 시각화:

- 연도별 화재 발생 지도 생성
- 월별 화재 발생 빈도 차트 생성
- af_flag 누락 여부 검증
