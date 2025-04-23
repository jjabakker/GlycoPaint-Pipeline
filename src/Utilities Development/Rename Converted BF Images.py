import os

# Define the root directory to start the search
root_dir = '/Users/hans/Paint Source'

# Walk through the directory tree
for dirpath, dirnames, filenames in os.walk(root_dir):
    # Check if 'Converted BF Images' is in the list of directories
    if 'Images' in dirnames:
        # Define the old and new paths
        old_path = os.path.join(dirpath, 'Images')
        new_path = os.path.join(dirpath, 'TrackMate Images')

        # Rename the directory
        os.rename(old_path, new_path)
        print(f"Renamed: {old_path} -> {new_path}")
