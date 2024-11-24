import os
import shutil


def delete_plot_tau_dirs(start_dir):
    # Walk through the directory tree
    for root, dirs, files in os.walk(start_dir):
        # Iterate over the directories in the current root
        for dir_name in dirs:
            # Check if the directory name is 'Plot Tau'
            if dir_name == 'Plot Tau':
                dir_path = os.path.join(root, dir_name)
                print(f"Deleting directory: {dir_path}")

                # Delete the directory and all its contents
                shutil.rmtree(dir_path)
                print(f"Deleted directory: {dir_path}")


# Set the starting directory here
start_directory = '/Users/Hans/Paint Source New/'

# Call the function to start traversing and deleting
delete_plot_tau_dirs(start_directory)
