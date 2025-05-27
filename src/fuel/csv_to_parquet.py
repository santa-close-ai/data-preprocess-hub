import argparse
from pathlib import Path
import pandas as pd
import pyarrow.csv as pv
import pyarrow.parquet as pq
import pyarrow as pa

def convert_csv_to_parquet(csv_dir_path: Path):
    """
    Scans a directory for CSV files, sorts them by name,
    and converts each to Parquet format in the same directory.
    """
    csv_files = sorted(list(csv_dir_path.glob('*.csv')))

    if not csv_files:
        print(f"'{csv_dir_path}' 디렉토리에서 CSV 파일을 찾을 수 없습니다.")
        return

    print(f"총 {len(csv_files)}개의 CSV 파일을 찾았습니다. 변환을 시작합니다...")

    for csv_file in csv_files:
        try:
            print(f"'{csv_file.name}' 파일 처리 중...")
            df = pd.read_csv(csv_file, engine='pyarrow')
            
            # Parquet 파일 경로 생성 (원본 파일명 + .parquet 확장자)
            parquet_file = csv_file.with_suffix('.parquet')
            
            # DataFrame을 Parquet 파일로 저장 (인덱스는 저장하지 않음)
            df.to_parquet(parquet_file, index=False)
            print(f"성공: '{csv_file.name}' -> '{parquet_file.name}'")
        except pd.errors.EmptyDataError:
            print(f"경고: '{csv_file.name}' 파일이 비어있어 건너뜁니다.")
        except Exception as e:
            print(f"오류: '{csv_file.name}' 파일 처리 중 오류 발생: {e}")

def combine_csvs_to_single_parquet(csv_dir_path: Path):
    """
    Scans a directory for CSV files, sorts them by name,
    combines them into a single DataFrame, and saves it as a Parquet file
    in the same directory.
    """
    csv_files = sorted(list(csv_dir_path.glob('*.csv')))

    if not csv_files:
        print(f"'{csv_dir_path}' 디렉토리에서 CSV 파일을 찾을 수 없습니다.")
        return

    print(f"총 {len(csv_files)}개의 CSV 파일을 찾았습니다. 병합을 시작합니다...")

    all_dataframes = []
    successfully_read_files = 0

    for csv_file in csv_files:
        try:
            print(f"'{csv_file.name}' 파일 처리 중...")
            df = pd.read_csv(csv_file, engine='pyarrow')
            
            if not df.empty:
                all_dataframes.append(df)
                successfully_read_files += 1
            else:
                print(f"정보: '{csv_file.name}' 파일이 비어있어 병합에서 제외합니다.")
        except pd.errors.EmptyDataError:
            print(f"경고: '{csv_file.name}' 파일이 비어있어 건너뜁니다.")
        except Exception as e:
            print(f"오류: '{csv_file.name}' 파일 처리 중 오류 발생: {e}")

    if not all_dataframes:
        print("병합할 데이터가 있는 CSV 파일을 찾지 못했습니다.")
        return

    print(f"{successfully_read_files}개의 파일에서 데이터를 성공적으로 읽었습니다. 하나의 DataFrame으로 병합합니다...")
    combined_df = pd.concat(all_dataframes, ignore_index=True)

    output_filename = f"{csv_dir_path.name}_combined.parquet"
    output_parquet_path = csv_dir_path / output_filename

    try:
        combined_df.to_parquet(output_parquet_path, index=False)
        print(f"성공: 모든 CSV 파일이 '{output_parquet_path}' 파일로 병합되었습니다.")
    except Exception as e:
        print(f"오류: 병합된 DataFrame을 Parquet 파일로 저장 중 오류 발생: {e}")

def combine_csvs_to_parquet_pyarrow(csv_dir_path: Path):
    """
    Scans a directory for CSV files, sorts them by name, combines them
    into a single Parquet file using PyArrow for memory efficiency.
    The schema is determined by the first valid CSV file.
    """
    csv_files = sorted(list(csv_dir_path.glob('*.csv')))

    if not csv_files:
        print(f"'{csv_dir_path}' 디렉토리에서 CSV 파일을 찾을 수 없습니다.")
        return

    print(f"총 {len(csv_files)}개의 CSV 파일을 찾았습니다. PyArrow를 사용하여 병합을 시작합니다...")

    output_filename = f"{csv_dir_path.name}_combined.parquet"
    output_parquet_path = csv_dir_path / output_filename

    writer = None
    target_schema = None
    files_processed_count = 0
    successful_writes = 0

    try:
        for csv_file in csv_files:
            print(f"'{csv_file.name}' 파일 처리 중...")
            try:
                # CSV 파일을 Arrow Table로 읽기
                # read_options과 parse_options을 통해 더 세밀한 제어 가능
                table = pv.read_csv(csv_file)

                if table.num_rows == 0:
                    print(f"정보: '{csv_file.name}' 파일이 비어있어 건너뜁니다.")
                    continue

                if target_schema is None:  # 첫 번째 유효한 파일로 스키마 설정
                    target_schema = table.schema
                    # ParquetWriter 초기화
                    # 출력 디렉토리가 없을 경우 대비
                    output_parquet_path.parent.mkdir(parents=True, exist_ok=True)
                    writer = pq.ParquetWriter(str(output_parquet_path), target_schema)
                    writer.write_table(table)
                    successful_writes += 1
                    print(f"'{csv_file.name}'의 스키마를 사용하여 '{output_parquet_path}' 파일 초기화 및 첫 데이터 쓰기 완료.")
                else:
                    # 후속 파일들의 스키마를 target_schema에 맞게 변환 시도
                    if not table.schema.equals(target_schema):
                        print(f"경고: '{csv_file.name}' 파일의 스키마가 대상 스키마와 다릅니다. 변환을 시도합니다.")
                        print(f"  현재 파일 스키마: {table.schema}")
                        print(f"  대상 (첫 파일) 스키마: {target_schema}")
                        try:
                            # target_schema로 캐스팅 (컬럼 순서, 타입, 누락/추가 컬럼 처리)
                            table = table.cast(target_schema, safe=False)
                        except pa.ArrowInvalid as e_cast:
                            print(f"오류: '{csv_file.name}'의 스키마를 대상 스키마로 변환하는 데 실패했습니다: {e_cast}")
                            print("  이 파일은 건너뜁니다.")
                            continue
                        except Exception as e_cast_general:
                            print(f"오류: '{csv_file.name}' 스키마 변환 중 예기치 않은 오류: {e_cast_general}")
                            print("  이 파일은 건너뜁니다.")
                            continue
                    writer.write_table(table)
                    successful_writes += 1
                
                files_processed_count +=1 # 성공적으로 읽고 스키마 처리된 파일 수

            except pa.ArrowInvalid as e_read: # CSV 읽기 오류 (예: 빈 파일, 형식 오류)
                print(f"오류: '{csv_file.name}' 파일 읽기 중 PyArrow 오류 발생: {e_read}. 이 파일은 건너뜁니다.")
            except Exception as e:
                print(f"오류: '{csv_file.name}' 파일 처리 중 예기치 않은 오류 발생: {e}. 이 파일은 건너뜁니다.")

    except Exception as e_outer:
        print(f"전체 프로세스 중 오류 발생: {e_outer}")
    finally:
        if writer:
            writer.close()
            print("Parquet writer가 닫혔습니다.")

    if target_schema is None:
        print("데이터를 포함하고 읽을 수 있는 CSV 파일을 찾지 못했습니다. Parquet 파일이 생성되지 않았습니다.")
    elif successful_writes == 0:
        print(f"유효한 데이터가 있는 CSV 파일을 처리하지 못하여 '{output_parquet_path}'에 데이터가 기록되지 않았습니다.")
        if output_parquet_path.exists():
            # 파일이 생성되었지만 비어있을 수 있음 (예: 첫 파일 스키마는 읽었으나 데이터 쓰기 실패)
            print(f"'{output_parquet_path}' 파일이 생성되었지만 내용이 없을 수 있습니다.")
    else: # successful_writes > 0
        print(f"성공: 총 {successful_writes}개의 CSV 파일의 데이터가 '{output_parquet_path}' 파일로 병합되었습니다.")
        print(f"총 {files_processed_count}개의 CSV 파일이 스키마 처리되었습니다.")

def main():
    parser = argparse.ArgumentParser(
        # description="디렉토리 내 CSV 파일들을 파일 이름 순으로 정렬하여 Parquet 형식으로 변환합니다."
        # description="디렉토리 내 CSV 파일들을 파일 이름 순으로 읽어 하나의 Parquet 파일로 통합합니다."
        description="디렉토리 내 CSV 파일들을 파일 이름 순으로 읽어 하나의 Parquet 파일로 통합합니다 (PyArrow 사용)."
    )
    parser.add_argument(
        "csv_directory", 
        type=str, 
        help="CSV 파일들이 포함된 디렉토리 경로"
    )
    args = parser.parse_args()

    csv_dir = Path(args.csv_directory)

    if not csv_dir.is_dir():
        print(f"오류: 디렉토리를 찾을 수 없습니다: '{csv_dir}'")
        return

    # convert_csv_to_parquet(csv_dir)
    # combine_csvs_to_single_parquet(csv_dir)
    combine_csvs_to_parquet_pyarrow(csv_dir)

if __name__ == "__main__":
    main()
