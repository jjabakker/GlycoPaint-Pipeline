import os

import pandas as pd


def update_csv_columns(directory):
    # Traverse the directory tree
    for root, dirs, files in os.walk(directory):
        for file in files:
            # Check if the file is a CSV file
            if 'All Squares' in file and file.endswith('.csv'):
                file_path = os.path.join(root, file)

                try:
                    # Read the CSV file
                    df = pd.read_csv(file_path, low_memory=False)

                    # Check if the column ''Visible' exists
                    if 'Visible' in df.columns:
                        print(f"Updating column in file: {file_path}")

                        # Rename the column
                        df.rename(columns={'Visible': 'Selected'}, inplace=True)

                        # Save the updated DataFrame back to the same CSV file
                        df.to_csv(file_path, index=False)
                        print(f"File saved: {file_path}")
                    else:
                        pass
                        print(f"No changes required for file: {file_path}")

                except Exception as e:
                    print(f"Error processing file {file_path}: {e}")


# Usage: Replace 'your_directory_path' with the path of the directory you want to traverse
directory = '/Users/hans/Paint Data - v18'

update_csv_columns(directory)
