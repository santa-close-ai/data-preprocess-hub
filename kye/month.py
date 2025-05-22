import os
import pandas as pd
from collections import defaultdict

# 날짜별 CSV가 저장된 폴더 경로
input_dir = "vod_per_day_csv"
output_dir = "vod_per_month_csv"
os.makedirs(output_dir, exist_ok=True)

# 월별 데이터 저장용 딕셔너리
monthly_records = defaultdict(list)

# 폴더 내 모든 파일 순회
for file in os.listdir(input_dir):
    if file.endswith(".csv"):
        # 파일명에서 날짜(예: vod_20110223.csv → 20110223) 추출
        date_str = file.replace("vod_", "").replace(".csv", "")
        month_key = date_str[:6]  # 'YYYYMM' 형식

        file_path = os.path.join(input_dir, file)
        df = pd.read_csv(file_path)
        monthly_records[month_key].append(df)

# 월별로 하나의 CSV로 병합 저장
for month, dfs in monthly_records.items():
    combined_df = pd.concat(dfs, ignore_index=True)
    output_path = os.path.join(output_dir, f"vod_{month}.csv")
    combined_df.to_csv(output_path, index=False)
    print(f"✅ 월별 저장 완료 → {output_path}")

print("\n🎉 모든 월별 CSV 파일 저장 완료!")
