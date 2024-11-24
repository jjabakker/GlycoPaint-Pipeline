import os
import shutil


def copy_tm_data_from_paint_source(source_dir, destination_dir):
    # Ensure the destination directory exists
    os.makedirs(destination_dir, exist_ok=True)

    # Loop through only the first level of subdirectories in source_dir
    for subdir in os.listdir(source_dir):
        subdir_path = os.path.join(source_dir, subdir)

        # Check if it's a directory (to ignore files in the root)
        if os.path.isdir(subdir_path):
            # Create the corresponding directory in the destination
            dest_path = os.path.join(destination_dir, subdir)
            os.makedirs(dest_path, exist_ok=True)

            # Copy only the specified files if they exist
            for file in ['All Tracks.csv', 'All Recordings.csv']:
                src_file_path = os.path.join(subdir_path, file)
                if os.path.exists(src_file_path):
                    dest_file_path = os.path.join(dest_path, file)
                    shutil.copy(src_file_path, dest_file_path)  # copy2 preserves metadata


def copy_with_overwrite(src, dst):
    # If the destination is a directory and exists, remove it
    if os.path.isdir(dst):
        shutil.rmtree(dst)
    # Copy the source to destination
    shutil.copytree(src, dst)


def copy_tm_data_from_paint_source_with_images(source_dir, destination_dir):
    # Ensure the destination directory exists
    os.makedirs(destination_dir, exist_ok=True)

    # Loop through only the first level of subdirectories in source_dir
    for subdir in os.listdir(source_dir):
        subdir_path = os.path.join(source_dir, subdir)

        # Check if it's a directory (to ignore files in the root)
        if os.path.isdir(subdir_path):
            # Create the corresponding directory in the destination
            dest_path = os.path.join(destination_dir, subdir)
            os.makedirs(dest_path, exist_ok=True)

            # Copy only the specified files if they exist
            for file in ['All Tracks.csv', 'All Recordings.csv', 'Experiment Info.csv']:
                src_file_path = os.path.join(subdir_path, file)
                dest_file_path = os.path.join(dest_path, file)
                if os.path.exists(src_file_path):
                    shutil.copy(src_file_path, dest_file_path)  # Overwrite if exists
                    # print(f"Copied {src_file_path} to {dest_file_path}")

            # Copy 'Brightfield Images' and 'TrackMate Images' directories if they exist
            for folder in ['Brightfield Images', 'TrackMate Images']:
                src_folder_path = os.path.join(subdir_path, folder)
                dest_folder_path = os.path.join(dest_path, folder)
                if os.path.exists(src_folder_path):
                    copy_with_overwrite(src_folder_path, dest_folder_path)
