# Vegetation Type 전처리

**SafeForest**를 위한 **식생 유형 vegetation type** 전처리 작업
ESA CCI에서 제공하는 GeoTIFF 기반의 식생 분류 데이터를 불러옴 -> 격자 기반 `.csv`로 가공

---

## 폴더 구조

```bash
jian/
└── vegetation_type/
    ├── vegetation_process.ipynb
    ├── vegetation_type_2022.csv
    └── README.md



---

## 전처리 개요

- 데이터 출처: ESA CCI Land Cover Map v2.1.1 (2022)
- 공간 해상도: 300m
- 사용 변수: lccs_class (식생 유형 분류)
- 대상 지역: 대한민국 영역 (위도 33~39 / 경도 124~132)

---

## 주요 처리 과정

| 순서 | 설명 |
|------|------|
| 1 | `.nc` (NetCDF) 파일을 `xarray`로 불러옴 |
| 2 | `lccs_class` 변수(식생 유형)를 추출 |
| 3 | 위도/경도를 기준으로 `grid_id`를 생성 |
| 4 | 결측치를 제외하고 모든 셀에 대해 `date`, `grid_id`, `vegetation_type`을 구성 |
| 5 | 최종 결과를 `vegetation_type_2022.csv` 파일로 저장 |

---

## 컬럼 설명

| 컬럼명          | 설명 |
|----------------|------|
| date           | 기준 날짜 (2022-01-01로 고정) |
| grid_id        | 위도/경도에 기반한 격자 ID (900 x 3600 기준) |
| lead           | 리드 타임 (기본값: 0) |
| vegetation_type | ESA CCI 기준 식생 유형 값 (정수형 클래스) |

주의: 클래스 ID는 ESA CCI 문서의 범례에 따라 의미가 부여됨됨

---

## 담당

- 작성: jianppark
```
