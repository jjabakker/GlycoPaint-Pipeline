import os
import shutil

def clean_directory(root_dir):
    target_csvs = {'All Recordings.csv', 'All Squares.csv', 'All Tracks.csv'}
    target_dirs = {'Brightfield Images', 'TrackMate Images'}

    for dirpath, dirnames, filenames in os.walk(root_dir, topdown=True):
        # Delete matching CSV files
        for filename in filenames:
            if filename in target_csvs:
                full_path = os.path.join(dirpath, filename)
                try:
                    os.remove(full_path)
                    print(f"Deleted file: {full_path}")
                except Exception as e:
                    print(f"Failed to delete file {full_path}: {e}")

        # Delete matching directories
        for dirname in list(dirnames):  # copy to avoid modifying list during iteration
            if dirname in target_dirs:
                full_dir_path = os.path.join(dirpath, dirname)
                try:
                    shutil.rmtree(full_dir_path)
                    print(f"Deleted directory: {full_dir_path}")
                    dirnames.remove(dirname)  # prevent os.walk from descending into deleted dir
                except Exception as e:
                    print(f"Failed to delete directory {full_dir_path}: {e}")

# Example usage
clean_directory('/Users/hans/Paint Sweep Multiple Experiments/Cases')