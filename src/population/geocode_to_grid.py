import os
import csv

def transform_geocode_to_grid_id(input_csv_path, output_csv_path):
    """
    Transforms geocodes (x, y coordinates) from an input CSV file to grid IDs
    and writes them to an output CSV file.

    The input CSV must have columns 'x', 'y', and 'value'.
    The output CSV will have columns 'grid_id' and 'value'.
    The grid_id is calculated as: (y*10 + 900) * 3600 + (x*10 + 1800)
    """
    try:
        with open(input_csv_path, mode='r', newline='', encoding='utf-8') as infile, \
            open(output_csv_path, mode='w', newline='', encoding='utf-8') as outfile:

            reader = csv.reader(infile)
            writer = csv.writer(outfile)

            # Read header from input
            try:
                header = next(reader)
            except StopIteration:
                print(f"Warning: Input CSV {input_csv_path} is empty or has no header.")
                writer.writerow(['grid_id', 'value']) # Write header to output even if input is empty
                return

            try:
                x_idx = header.index('x')
                y_idx = header.index('y')
                value_idx = header.index('value')
            except ValueError:
                print(f"Error: Input CSV {input_csv_path} is missing required headers 'x', 'y', or 'value'. Found: {header}")
                return

            # Write new header to output
            writer.writerow(['grid_id', 'value'])

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
                    writer.writerow([grid_id, value])
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
file_list = os.listdir(input_dir)
file_list_csv = [file for file in file_list if file.endswith(".csv")]

# print ("file_list_csv:\n{}".format(file_list_csv))

output_dir = os.path.join(base_dir, 'grid') # Define output directory
os.makedirs(output_dir, exist_ok=True) # Create output directory if it doesn't exist

# Example usage:
for input_file_name in file_list_csv:
    org_file = os.path.join(input_dir, input_file_name)
    out_file = os.path.join(output_dir, input_file_name)
    print("Transform {} => {}".format(org_file, out_file))

    transform_geocode_to_grid_id(org_file, out_file)
