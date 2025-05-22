# data-preprocess-hub

This repository serves as a centralized location for team members to share and organize algorithms for wildfire prediction data collection and preprocessing.

산불예측용 데이터 수집과 전처리 알고리즘을 팀원 간에 공유 및 정리하기 위한 레포지토리입니다.

## Population

Original File Download URL

- https://earth.gov/ghgcenter/data-catalog/sedac-popdensity-yeargrid5yr-v4.11
- https://data.ghg.center/browseui/index.html#sedac-popdensity-yeargrid5yr-v4.11/

### Home / sedac-popdensity-yeargrid5yr-v4.11

| Name                                                 | File Type | Last Modified             | Size     |
| ---------------------------------------------------- | --------- | ------------------------- | -------- |
| gpw_v4_population_density_rev11_2000_30_sec_2000.tif | tif       | 2024. 7. 30. 오전 3:35:30 | 406.4 MB |
| gpw_v4_population_density_rev11_2005_30_sec_2005.tif | tif       | 2024. 7. 30. 오전 3:35:51 | 406.2 MB |
| gpw_v4_population_density_rev11_2010_30_sec_2010.tif | tif       | 2024. 7. 30. 오전 3:36:13 | 406.4 MB |
| gpw_v4_population_density_rev11_2015_30_sec_2015.tif | tif       | 2024. 7. 30. 오전 3:36:33 | 406.5 MB |
| gpw_v4_population_density_rev11_2020_30_sec_2020.tif | tif       | 2024. 7. 30. 오전 3:36:54 | 406.7 MB |

- Temporal Extent: 2000 - 2020
- Temporal Resolution: Annual, every 5 years
- Spatial Extent: Global
- Spatial Resolution: 30 arc-seconds (~1 km at equator)
- Data Units: Number of persons per square kilometer (persons/km²)
- Data Type: Research
- Data Latency: 5 years

### Data Directory Structure

- base directory : data/population
- original file directory : data/population/raw/\*.tif
- converted file directory : data/population/csv/\*.csv
- filtered file directory : data/population/filtered/\*.csv
- grid file directory : data/population/grid/\*.csv

### Preprocessing

#### 1. tif to csv

- Input : original file directory
- Output : converted file directory

Converting each TIF file to a CSV file will generate a CSV file of approximately 9.82 GB.

각 tif 파일을 csv 파일로 변환하면 각각 9.82 GB 정도의 csv 파일이 생성됨.

```bash
python src/population/tif_to_csv.py
```

#### 2. csv filtering

- Input : converted file directory
- Output : filtered file directory

The resulting CSV files are quite large. However, if you extract the data using the following conditions, which cover South Korea's latitude and longitude, each file will be reduced to roughly 10.4 MB.

생성된 csv 파일들의 사이즈가 커서 한국의 경위도에 해당하는 다음 조건으로 데이터를 추출하면 각 파일이 10.4 MB 파일로 최종 생성됨.

- 33 <= y (latitude, 위도) <= 39
- 124 <= x (longitude, 경도) <= 132

```bash
python src/population/filter_large_csv.py
```

#### 3. transform geocode to grid_id

- Input : filtered file directory
- Output : grid file directory

input csv header : x,y,value

output csv header : grid_id,value

grid_id = (y*10 + 900) * 3600 + (x\*10 + 1800)

```bash
python src/population/geocode_to_grid.py
```
