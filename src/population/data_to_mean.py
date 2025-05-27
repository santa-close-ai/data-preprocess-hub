# import glob
# import os
import argparse
from pathlib import Path
import pandas as pd

def process_csv_files_in_directory(input_directory_path: Path, output_directory_path: Path):
    """
    지정된 입력 디렉터리의 모든 CSV 파일을 처리합니다.
    각 파일에 대해 'grid_id'를 기준으로 데이터를 그룹화하고, 'value'의 평균을 계산하며,
    각 그룹의 첫 번째 'date' 값을 유지합니다.
    처리된 데이터는 지정된 출력 디렉터리에 원본 파일명과 동일하게 저장됩니다.
    """
    # OS에 독립적인 경로 생성을 위해 os.path.join 사용
    # 사용자가 'data\population\grid'와 같이 입력해도 올바르게 처리
    # search_pattern = os.path.join(directory_path, '*.csv')
    
    # 출력 디렉터리 생성 (이미 존재하면 무시, 부모 디렉터리도 필요시 생성)
    try:
        output_directory_path.mkdir(parents=True, exist_ok=True)
        print(f"출력 디렉터리 확인/생성: '{output_directory_path}'")
    except OSError as e:
        print(f"오류: 출력 디렉터리 '{output_directory_path}'를 생성할 수 없습니다: {e}")
        return

    # CSV 파일 목록을 가져와 이름순으로 정렬
    # csv_files = sorted(glob.glob(search_pattern))
    csv_files = sorted(list(input_directory_path.glob('*.csv')))

    if not csv_files:
        print(f"알림: '{input_directory_path}' 디렉터리에서 CSV 파일을 찾을 수 없습니다.")
        return

    print(f"총 {len(csv_files)}개의 CSV 파일을 처리합니다.")

    for file_path in csv_files:
        print(f"처리 중인 입력 파일: {file_path}")
        try:
            df = pd.read_csv(file_path)

            if df.empty:
                print(f"알림: '{file_path}' 파일이 비어 있어 건너뜁니다.")
                continue

            # 필수 열(column) 확인 (grid_id, value, date)
            required_columns = ['grid_id', 'value', 'date']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                print(f"경고: '{file_path}' 파일에 다음 필수 열이 없습니다: {', '.join(missing_columns)}. 이 파일을 건너뜁니다.")
                continue
            
            # 'grid_id'로 그룹화하고 'value'의 평균 계산, 'date'는 첫 번째 값 사용
            # as_index=False는 'grid_id'를 인덱스가 아닌 열로 유지
            processed_df = df.groupby('grid_id', as_index=False).agg(
                value=('value', 'mean'),
                date=('date', 'first')  # 각 grid_id 그룹의 첫 번째 'date' 값을 사용
            )

            # 출력 열 순서 지정: grid_id, value, date
            processed_df = processed_df[['grid_id', 'value', 'date']]

            # 처리된 데이터프레임을 출력 디렉터리에 저장
            output_file_path = output_directory_path / file_path.name
            # index=False 옵션으로 pandas 인덱스는 저장하지 않음
            processed_df.to_csv(output_file_path, index=False, encoding='utf-8')
            print(f"성공: '{output_file_path}' 파일로 저장했습니다.")


        except pd.errors.EmptyDataError:
            print(f"알림: '{file_path}' 파일이 비어 있거나 CSV 형식이 아니어서 건너뜁니다.")
        except Exception as e:
            print(f"오류: '{file_path}' 파일 처리 중 오류가 발생했습니다: {e}")

def main():
    parser = argparse.ArgumentParser(
        description="입력 디렉토리 내 CSV 파일들을 처리하여 grid_id 기준으로 value 평균을 계산하고, 결과를 자동으로 생성된 출력 디렉토리에 저장합니다. 출력 디렉토리는 입력 디렉토리의 부모에 'aggregated' 이름으로 생성됩니다."
    )
    parser.add_argument(
        "input_directory",
        type=str, 
        help="CSV 파일들이 포함된 입력 디렉토리 경로 (예: data/population/grid)"
    )
    args = parser.parse_args()

    input_dir = Path(args.input_directory)

    if not input_dir.is_dir():
        print(f"오류: 입력 디렉토리를 찾을 수 없습니다: '{input_dir}'")
        return

    # 출력 디렉토리 경로 생성: 입력 디렉토리의 부모 디렉토리 + "aggregated"
    # 예: input_dir = "data/population/grid" -> output_dir = "data/population/aggregated"
    output_dir = input_dir.parent / "aggregated"
    
    print(f"입력 디렉터리: '{input_dir}'")
    print(f"자동 생성된 출력 디렉터리: '{output_dir}'")

    process_csv_files_in_directory(input_dir, output_dir)

    print("모든 파일 처리가 완료되었습니다.")

if __name__ == "__main__":
    main()
