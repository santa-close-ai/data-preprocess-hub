import os
import csv

def extract_and_save_large_csv(input_csv_path, output_csv_path, x_min, x_max, y_min, y_max):
    """
    대용량 CSV 파일에서 특정 x, y 범위에 해당하는 행을 추출하여 새로운 CSV 파일로 저장합니다.
    파일을 한 줄씩 읽어 처리하여 메모리 사용량을 최소화합니다.

    Args:
        input_csv_path (str): 입력 CSV 파일 경로.
        output_csv_path (str): 추출된 행을 저장할 출력 CSV 파일 경로.
        x_min (float): x 값의 최소 범위 (포함).
        x_max (float): x 값의 최대 범위 (포함).
        y_min (float): y 값의 최소 범위 (포함).
        y_max (float): y 값의 최대 범위 (포함).
    """
    processed_rows_count = 0
    filtered_rows_count = 0

    try:
        # 입력 파일 열기
        with open(input_csv_path, 'r', newline='', encoding='utf-8') as infile:
            reader = csv.reader(infile)

            # 헤더 읽기
            header = next(reader)
            # x, y 컬럼의 인덱스 찾기
            try:
                x_idx = header.index('x')
                y_idx = header.index('y')
            except ValueError:
                print(f"오류: CSV 헤더에 'x' 또는 'y' 컬럼이 없습니다. 헤더: {header}")
                return

            # 출력 파일 열기
            with open(output_csv_path, 'w', newline='', encoding='utf-8') as outfile:
                writer = csv.writer(outfile)

                # 출력 파일에 헤더 쓰기
                writer.writerow(header)

                # 데이터 행 처리
                for row in reader:
                    processed_rows_count += 1
                    if len(row) > max(x_idx, y_idx): # 행의 길이가 충분한지 확인
                        try:
                            # x, y 값을 float으로 변환
                            x = float(row[x_idx])
                            y = float(row[y_idx])

                            # 조건 확인
                            if (x_min <= x <= x_max) and (y_min <= y <= y_max):
                                writer.writerow(row)
                                filtered_rows_count += 1
                        except ValueError:
                            # x나 y가 숫자로 변환할 수 없는 경우 (데이터 오류)
                            # print(f"경고: 숫자 변환 오류 발생. 행 건너뛰기: {row}")
                            pass # 오류가 있는 행은 건너뜁니다.
                        except IndexError:
                            # 행의 길이가 예상보다 짧은 경우 (데이터 오류)
                            # print(f"경고: 행의 길이가 부족합니다. 행 건너뛰기: {row}")
                            pass
                    # 진행 상황 표시 (선택 사항)
                    if processed_rows_count % 100000 == 0:
                        print(f"\r{processed_rows_count}개 행 처리 중...", end='', flush=True)

        print(f"\n총 {processed_rows_count}개 행 중, {filtered_rows_count}개 행이 '{output_csv_path}'에 저장되었습니다.")

    except FileNotFoundError:
        print(f"오류: '{input_csv_path}' 파일을 찾을 수 없습니다.")
    except Exception as e:
        print(f"처리 중 오류가 발생했습니다: {e}")

base_dir = os.path.join('.', 'data', 'population')
input_dir = os.path.join(base_dir, 'csv')
file_list = os.listdir(input_dir)
file_list_csv = [file for file in file_list if file.endswith(".csv")]

# print ("file_list_csv:\n{}".format(file_list_csv))

output_dir = os.path.join(base_dir, 'filtered') # Define output directory
os.makedirs(output_dir, exist_ok=True) # Create output directory if it doesn't exist

# Example usage:
for input_file_name in file_list_csv:
    org_file = os.path.join(input_dir, input_file_name)
    out_file = os.path.join(output_dir, input_file_name)
    # print("Filter {} => {}".format(org_file, out_file))

    extract_and_save_large_csv(org_file, out_file, 124, 132, 33, 39)
