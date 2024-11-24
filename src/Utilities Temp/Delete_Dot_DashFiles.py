import os


def delete_dot_dash_files(directory):
    # Traverse the directory tree
    deleted = 0
    for root, dirs, files in os.walk(directory):
        # Set to keep track of filenames without the leading dot_dash
        non_dot_dash_files = set()

        # First pass: record all non-dot_dash files
        for file in files:
            if not file.startswith('._'):
                # Store the name of the non-dot_dash file
                non_dot_dash_files.add(file)

        # Second pass: delete dot_dash-files if corresponding non-dot_dash file exists
        i = 0
        for file in files:
            if file.startswith('._'):
                # The corresponding non dot_dash filename
                corresponding_file = file[2:]  # Remove the leading dot_dash

                if corresponding_file in non_dot_dash_files:
                    # Full path of the dot_dash file to be deleted
                    dot_dash_file_path = os.path.join(root, file)

                    try:
                        os.remove(dot_dash_file_path)
                        deleted += 1
                        print(".", end="")
                        i += 1
                        if i > 40:
                            print('')
                            i = 0
                    except OSError as e:
                        print(f"Error deleting {dot_dash_file_path}: {e}")
    print(f"Deleted {deleted}: files.")


# Specify the directory you want to process
directory_path = '/Volumes/Extreme Pro/Paint Data'
# Call the function
delete_dot_dash_files(directory_path)
