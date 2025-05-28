# README

## 개요

`korea_grids_with_jibun.parquet` 파일은 대한민국 영토(위도 33.0°\~38.6°, 경도 124.6°\~131.9°)를 0.1° 격자 단위로 분할하여 생성한 총 4,275개의 그리드에 대해, 각 격자의 고유 ID와 중심 좌표, 지번 주소를 담고 있습니다.

## 파일 정보

- **파일명**: `korea_grids_with_jibun.parquet`
- **행(row)**: 4,275개 (격자 개수)
- **열(column)**:

  - `grid_id` (int64): 위도·경도 격자에 대응하는 고유 식별자
  - `lat` (float64): 격자 중심점 위도 (소수점 첫째 자리 0.1° 단위 + 0.05)
  - `lon` (float64): 격자 중심점 경도 (소수점 첫째 자리 0.1° 단위 + 0.05)
  - `jibun` (string): 해당 격자 중심 위치의 지번 주소 (빈 문자열이면 매칭 실패)

## 생성 과정

1. **격자 생성**

   - 대한민국 범위 안에서 위도와 경도를 각각 0.1° 단위로 분할
   - 각 분할에 대해 `grid_id = (lat_bin + 900)*3600 + (lon_bin + 1800)` 계산
   - 중심 좌도: `lat = lat_bin*0.1 + 0.05`, 경도: `lon = lon_bin*0.1 + 0.05`

2. **지번 역지오코딩**

   - VWorld `coord2jibun.do` API 호출
   - 반환된 JSON 최상위 `ADDR` 값을 `jibun` 열에 저장
   - 호출 속도 제한(초당 약 5건) 준수

3. **파일 저장**

   - 결과를 Parquet 포맷으로 저장 (`pyarrow` 엔진 사용)

## API 출처

- **지번 주소**: VWorld Open API `coord2jibun.do` 엔드포인트
- **문서**: [https://www.vworld.kr/dev/v4dv_geocoding.jsp](https://www.vworld.kr/dev/v4dv_geocoding.jsp)

## 데이터 예시

다음은 `korea_grids_with_jibun.parquet` 파일에 포함된 데이터 예시입니다.

| grid_id | lat   | lon    | jibun                                    |
| ------- | ----- | ------ | ---------------------------------------- |
| 4571479 | 36.95 | 127.95 | 충청북도 충주시 직동 산 2                |
| 4575078 | 37.05 | 127.85 | 충청북도 충주시 중앙탑면 하구암리 산 102 |
| 4578679 | 37.15 | 127.95 | 충청북도 충주시 엄정면 가춘리 산 16-1    |
| 4578677 | 37.15 | 127.75 | 충청북도 충주시 앙성면 목미리 산 35      |
| 4578678 | 37.15 | 127.85 | 충청북도 충주시 소태면 주치리 653-6      |

## 사용 예시

```python
import pandas as pd

df = pd.read_parquet("korea_grids_with_jibun.parquet", engine="pyarrow")
print(df.head())
```

**지번 주소가 존재하는 격자만 확인**

```python
valid = df[df['jibun'].astype(bool)]
print(f"매칭된 격자 수: {len(valid)}")
```

**산점도 시각화**

```python
import matplotlib.pyplot as plt

plt.scatter(valid['lon'], valid['lat'], s=10, alpha=0.6)
plt.xlabel('Longitude')
plt.ylabel('Latitude')
plt.title('Grids with Jibun Address')
plt.show()
```

## 요구사항

- Python 3.7 이상
- `numpy`, `pandas`, `requests`, `pyarrow` 패키지 설치 필요

## 문의

- 데이터 생성 및 사용 관련 문의: vworld API Key 소유자에게 문의 바랍니다.
