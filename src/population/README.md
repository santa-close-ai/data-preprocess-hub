# aggregated_population_density_2000_2020.parquet

Original File Download URL

- https://earth.gov/ghgcenter/data-catalog/sedac-popdensity-yeargrid5yr-v4.11
- https://data.ghg.center/browseui/index.html#sedac-popdensity-yeargrid5yr-v4.11/

## Home / sedac-popdensity-yeargrid5yr-v4.11

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

## Data Directory Structure

- base directory : data/population
- original file directory : data/population/raw/\*.tif
- converted file directory : data/population/csv/\*.csv
- filtered file directory : data/population/filtered/\*.csv
- grid file directory : data/population/grid/\*.csv
- aggregated file directory : data/population/aggregated/\*.csv

## Preprocessing

### 1. tif to csv

- Input : original file directory
- Output : converted file directory

Converting each TIF file to a CSV file will generate a CSV file of approximately 9.82 GB.

각 tif 파일을 csv 파일로 변환하면 각각 9.82 GB 정도의 csv 파일이 생성됨.

```bash
python src/population/tif_to_csv.py
```

### 2. filter rows

- Input : converted file directory
- Output : filtered file directory

The resulting CSV files are quite large. However, if you extract the data using the following conditions, which cover South Korea's latitude and longitude, each file will be reduced to roughly 10.4 MB.

생성된 csv 파일들의 사이즈가 커서 한국의 경위도에 해당하는 다음 조건으로 데이터를 추출하면 각 파일이 10.4 MB 파일로 최종 생성됨.

- 33 <= y (latitude, 위도) <= 39
- 124 <= x (longitude, 경도) <= 132

```bash
python src/population/filter_large_csv.py
```

### 3. transform geocode to grid_id

- Input : filtered file directory
- Output : grid file directory

input csv header : x,y,value

output csv header : grid_id,value

**Calculation method**:

1. 위도를 0.1° 단위로 변환: `lat_bin = int(np.floor(lat / 0.1))`
2. 경도를 0.1° 단위로 변환: `lon_bin = int(np.floor(lon / 0.1))`
3. 최종 격자 ID: `grid_id = (lat_bin + 900) * 3600 + (lon_bin + 1800)`

**Example**: 서울 좌표 (37.5°N, 127.0°E)

- `lat_bin = 375`, `lon_bin = 1270`
- `grid_id = (375 + 900) * 3600 + (1270 + 1800) = 4,593,070`

```bash
python src/population/geocode_to_grid.py
```

### 4. aggregate rows on grid_id

- Input : grid file directory
- Output : aggregated file directory

csv header : grid_id,value,date

각 파일에 대해 grid_id 를 기준으로 데이터를 그룹화하고, value 의 평균을 계산해서 data/population/aggregated 디렉토리에 파일들을 저장

```bash
python ./src/population/data_to_mean.py data/population/grid
```
