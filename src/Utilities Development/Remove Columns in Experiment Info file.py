import csv
import os


def clean_experiment_info_csv(file_path):
    try:
        # Open the CSV file for reading
        with open(file_path, 'r') as f:
            reader = csv.reader(f)
            rows = list(reader)  # Read all rows into memory

        # Find the index of the 'Process' column
        header = rows[0]  # First row is the header
        if 'Process' in header:
            process_index = header.index('Process')
        else:
            print(f"'Process' column not found in {file_path}. Skipping file.")
            return

        # Iterate over the rows and remove comments or data after 'Process' column
        cleaned_rows = []
        for row in rows:
            # Keep only the data up to the 'Process' column, discard anything after
            cleaned_rows.append(row[:process_index + 1])

        # Write the cleaned rows back to the CSV file
        with open(file_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerows(cleaned_rows)
        print(f"Cleaned file: {file_path}")

    except Exception as e:
        print(f"Error processing {file_path}: {e}")


def traverse_and_clean(root_dir):
    # Walk the directory tree starting from root_dir
    for dirpath, dirnames, filenames in os.walk(root_dir):
        for filename in filenames:
            if filename == 'Experiment Info.csv':
                file_path = os.path.join(dirpath, filename)
                clean_experiment_info_csv(file_path)


# Example usage
root_directory = '/Users/Hans/Paint Source New'
traverse_and_clean(root_directory)
