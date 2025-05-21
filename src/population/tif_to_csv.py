import os
import rasterio
import numpy as np
import pandas as pd
import csv # Import the csv module for writing

def tif_to_csv(tif_filepath, csv_filepath):
    """
    Converts a TIF image to a CSV file.

    Args:
        tif_filepath (str): The file path to the input TIF image.
        csv_filepath (str): The file path to the output CSV file.
    """
    with rasterio.open(tif_filepath) as src:
        data = src.read(1)  # Read the raster data
        height, width = data.shape
        
        # Create coordinate arrays
        cols, rows = np.meshgrid(np.arange(width), np.arange(height))
        x, y = src.transform * (cols, rows)
        
        # Flatten arrays and create DataFrame
        df = pd.DataFrame({
            'x': x.flatten(),
            'y': y.flatten(),
            'value': data.flatten()
        })
    
    df.to_csv(csv_filepath, index=False)

def tif_to_csv_memory_efficient(tif_filepath, csv_filepath):
    """
    Converts a TIF image to a CSV file.

        tif_filepath (str): The file path to the input TIF image.
        csv_filepath (str): The file path to the output CSV file.
    """
    print(f"Converting {tif_filepath} to {csv_filepath}")
    with rasterio.open(tif_filepath) as src:
        # Print the data type of the first band of the TIF file
        print(f"Data type of {os.path.basename(tif_filepath)}: {src.dtypes[0]}")
        
        # Open the CSV file for writing
        with open(csv_filepath, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            # Write header
            writer.writerow(['x', 'y', 'value'])

            # Iterate over blocks (windows)
            for ji, window in src.block_windows():
                # Read data for the current window, handle nodata with masked=True
                data = src.read(1, window=window, masked=True)

                # Get the transform for the current window
                window_transform = src.window_transform(window)

                # Get the dimensions of the data block
                height, width = data.shape

                # Create coordinate arrays for the window block
                cols, rows = np.meshgrid(np.arange(width), np.arange(height))

                # Apply the window transform to get global coordinates for the block
                x, y = window_transform * (cols, rows)

                # Find valid data points (where data is not masked)
                valid_mask = ~data.mask

                # Prepare and write rows for valid data points in this block
                rows_to_write = zip(x[valid_mask], y[valid_mask], data[valid_mask].data)
                writer.writerows(rows_to_write)

    print(f"Conversion complete for {os.path.basename(tif_filepath)}")

base_dir = os.path.join('.', 'data', 'population')
input_dir = os.path.join(base_dir, 'raw') # Define input directory
file_list = os.listdir(input_dir)
file_list_tif = [file for file in file_list if file.endswith(".tif")]

# print ("file_list_tif:\n{}".format(file_list_tif))

output_dir = os.path.join(base_dir, 'csv') # Define output directory
os.makedirs(output_dir, exist_ok=True) # Create output directory if it doesn't exist

# Example usage:
for input_file_name in file_list_tif:
    tif_file = os.path.join(input_dir, input_file_name)
    output_file_name = os.path.splitext(input_file_name)[0] + '.csv'
    csv_file = os.path.join(output_dir, output_file_name)
    # print("Convert {} => {}".format(tif_file, csv_file))
    # print("Convert {} => {}".format(input_file_name, output_file_name))

    # Use the original function
    # tif_to_csv(tif_file, csv_file)

    # Use the memory-efficient function
    tif_to_csv_memory_efficient(tif_file, csv_file)
