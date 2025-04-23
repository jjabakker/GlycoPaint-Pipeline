import os


def rename_batch_files(root_dir):
    # Walk the directory tree starting from root_dir
    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Iterate over all filenames in the current directory
        for filename in filenames:
            # Check if the file name is 'batch.csv'
            if filename == 'batch.csv':
                old_file = os.path.join(dirpath, filename)  # Full path to the current 'batch.csv' file
                new_file = os.path.join(dirpath, 'Experiment Info.csv')  # Full path for the renamed file

                try:
                    # Rename the file
                    os.rename(old_file, new_file)
                    print(f"Renamed file: {old_file} -> {new_file}")
                except Exception as e:
                    print(f"Error renaming {old_file}: {e}")


# Example usage
root_directory = '/users/Hans/Paint Source New'  # Replace with the path to your root directory
rename_batch_files(root_directory)
