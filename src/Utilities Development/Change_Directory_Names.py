import os


def rename_plt_directories(root_dir):
    # Walk the directory tree starting from root_dir
    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Iterate over all directory names
        for dirname in dirnames:
            # Check if the directory name is 'plt'
            if dirname == 'plt':
                old_dir = os.path.join(dirpath, dirname)  # Full path to the current 'plt' directory
                new_dir = os.path.join(dirpath, 'Tau Plot')  # Full path for the renamed directory
                try:
                    os.rename(old_dir, new_dir)
                    print(f"Renamed directory: {old_dir} -> {new_dir}")
                except Exception as e:
                    print(f"Error renaming {old_dir}: {e}")

            if dirname == 'img':
                old_dir = os.path.join(dirpath, dirname)  # Full path to the current 'plt' directory
                new_dir = os.path.join(dirpath, 'TrackMate Images')  # Full path for the renamed directory
                try:
                    os.rename(old_dir, new_dir)
                    print(f"Renamed directory: {old_dir} -> {new_dir}")
                except Exception as e:
                    print(f"Error renaming {old_dir}: {e}")

            if dirname == 'grid':
                old_dir = os.path.join(dirpath, dirname)  # Full path to the current 'plt' directory
                new_dir = os.path.join(dirpath, 'Squares')  # Full path for the renamed directory
                try:
                    os.rename(old_dir, new_dir)
                    print(f"Renamed directory: {old_dir} -> {new_dir}")
                except Exception as e:
                    print(f"Error renaming {old_dir}: {e}")

            if dirname == 'tracks':
                old_dir = os.path.join(dirpath, dirname)  # Full path to the current 'plt' directory
                new_dir = os.path.join(dirpath, 'TrackMate Tracks')  # Full path for the renamed directory
                try:
                    os.rename(old_dir, new_dir)
                    print(f"Renamed directory: {old_dir} -> {new_dir}")
                except Exception as e:
                    print(f"Error renaming {old_dir}: {e}")


# Example usage
root_directory = '/Users/hans/Paint Source New/'  # Replace with the path to your root directory
rename_plt_directories(root_directory)
