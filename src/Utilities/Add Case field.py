import os
import pandas as pd

# Path to the root directory
root_dir = '/Users/hans/Paint Sweep New/Cases'

# Loop through all subdirectories
for subdir in os.listdir(root_dir):
    subdir_path = os.path.join(root_dir, subdir)

    if os.path.isdir(subdir_path):
        squares_file = os.path.join(subdir_path, "All Squares.csv")

        if os.path.exists(squares_file):
            try:
                df = pd.read_csv(squares_file)
                df['Case'] = subdir  # Add a new column 'case' with the subdirectory name

                # Overwrite the original file
                df.to_csv(squares_file, index=False)
                print(f"Updated: {squares_file}")
            except Exception as e:
                print(f"Error processing {squares_file}: {e}")