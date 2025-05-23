import os
import csv
import numpy as np
import re # 정규 표현식 모듈 추가

def transform_geocode_to_grid_id(input_csv_path, output_csv_path):
    """
    Transforms geocodes (x, y coordinates) from an input CSV file to grid IDs
    and writes them to an output CSV file.

    The input CSV must have columns 'x', 'y', and 'value'.
    If the input_csv_path ends with '_YYYY.csv' (where YYYY is a year),
    the output CSV will have columns 'grid_id', 'value', and 'date'
    (with 'YYYY-01-01' as value).
    Otherwise, the output CSV will have columns 'grid_id' and 'value'.
    The grid_id is calculated as: floor(y/0.1) + 900) * 3600 + (floor(x/0.1) + 1800)
    """
    try:
        input_filename = os.path.basename(input_csv_path)
        add_date_column = False
        date_value_to_add = None

        # 파일 이름에서 연도 추출 (예: _2020.csv -> 2020)
        year_match = re.search(r'_(\d{4})\.csv$', input_filename)
        if year_match:
            year = year_match.group(1)
            add_date_column = True
            date_value_to_add = f"{year}-01-01"

        with open(input_csv_path, mode='r', newline='', encoding='utf-8') as infile, \
            open(output_csv_path, mode='w', newline='', encoding='utf-8') as outfile:

            reader = csv.reader(infile)
            writer = csv.writer(outfile)

            # Prepare output header
            output_header = ['grid_id', 'value']
            if add_date_column:
                output_header.append('date')

            # Read header from input
            try:
                header = next(reader)
            except StopIteration:
                print(f"Warning: Input CSV {input_csv_path} is empty or has no header.")
                writer.writerow(output_header) # Write configured header to output even if input is empty
                return

            try:
                x_idx = header.index('x')
                y_idx = header.index('y')
                value_idx = header.index('value')
            except ValueError:
                print(f"Error: Input CSV {input_csv_path} is missing required headers 'x', 'y', or 'value'. Found: {header}")
                return

            # Write new header to output
            writer.writerow(output_header)

            # Process data rows
            for row_num, row in enumerate(reader, 1):
                try:
                    x_val = float(row[x_idx])
                    y_val = float(row[y_idx])
                    value = row[value_idx]

                    lat_bin = int(np.floor(y_val / 0.1))
                    lon_bin = int(np.floor(x_val / 0.1))
                    grid_id = int(lat_bin + 900) * 3600 + (lon_bin + 1800)
                    # grid_id = int((y_val * 10 + 900) * 3600 + (x_val * 10 + 1800))
                    # writer.writerow([grid_id, value])
                    output_row_data = [grid_id, value]
                    if add_date_column:
                        output_row_data.append(date_value_to_add)
                    
                    writer.writerow(output_row_data)
                except (ValueError, TypeError) as e:
                    print(f"Warning: Skipping row {row_num} in {input_csv_path} due to data conversion error: {row} - {e}")
                except IndexError:
                    print(f"Warning: Skipping row {row_num} in {input_csv_path} due to missing columns: {row}")

    except FileNotFoundError:
        print(f"Error: Input file not found at {input_csv_path}")
    except Exception as e:
        print(f"An unexpected error occurred while processing {input_csv_path}: {e}")

base_dir = os.path.join('.', 'data', 'population')
input_dir = os.path.join(base_dir, 'filtered') # Define input directory
if not os.path.isdir(input_dir):
    print(f"Error: Input directory not found at {input_dir}")
    file_list_csv = [] # 빈 리스트로 초기화하여 이후 로직에서 오류 방지
else:
    file_list = os.listdir(input_dir)
    file_list_csv = [file for file in file_list if file.endswith(".csv")]

# print ("file_list_csv:\n{}".format(file_list_csv))

output_dir = os.path.join(base_dir, 'grid') # Define output directory
os.makedirs(output_dir, exist_ok=True) # Create output directory if it doesn't exist

# Example usage:
if not file_list_csv:
    print(f"No CSV files found in {input_dir} to process.")
else:
    for input_file_name in file_list_csv:
        org_file = os.path.join(input_dir, input_file_name)
        out_file = os.path.join(output_dir, input_file_name)
        print("Transform {} => {}".format(org_file, out_file))

        transform_geocode_to_grid_id(org_file, out_file)
