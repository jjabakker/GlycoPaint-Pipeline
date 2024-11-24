import csv
import os
import time

from src.Application.Utilities.General_Support_Functions import (
    format_time_nicely)
from src.Fiji.LoggerConfig import (
    paint_logger,
    paint_logger_change_file_handler_name,
    paint_logger_file_name_assigned)

if not paint_logger_file_name_assigned:
    paint_logger_change_file_handler_name('Create All Tracks.log')


def compile_all_tracks(project_directory):
    """
    Read all tracks files in the directory tree and concatenate them into a single DataFrame.
    The file is then saved as 'All Tracks.csv' in the root directory.
    """

    time_stamp = time.time()

    csv_files = []

    # Traverse the directory tree, to find all the files
    for root, dirs, files in os.walk(project_directory):

        for file in files:
            if file == 'All Tracks.csv' and root != project_directory:
                csv_files.append(os.path.join(root, file))
                # paint_logger.debug(f"Read Tracks file: {os.path.join(root, file)}")
    paint_logger.info(f"Compiling 'All Tracks' from {len(csv_files)} tracks files in {project_directory}")

    csv_files.sort()

    # Read and concatenate all CSV files found

    # Define the list of CSV files and the output file path
    all_tracks_file_path = os.path.join(project_directory, "All Tracks.csv")

    # Open the output file in write mode
    with open(all_tracks_file_path, 'w') as outfile:
        writer = None  # Initialize writer as None

        for i, file in enumerate(csv_files):
            with open(file, 'r') as infile:
                reader = csv.reader(infile)
                # Write the header only for the first file
                if i == 0:
                    writer = csv.writer(outfile)
                    writer.writerow(next(reader))  # Write the header
                else:
                    next(reader)  # Skip the header in subsequent files

                # Write the rows
                for row in reader:
                    writer.writerow(row)

    run_time = time.time() - time_stamp
    paint_logger.info(
        f"Compiled  'All Tracks' from {len(csv_files)} tracks files in {project_directory} in {format_time_nicely(run_time)}.")
    paint_logger.info("")


if __name__ == '__main__':
    compile_all_tracks('/Users/hans/Paint Data - v12/Regular Probes/Paint Regular Probes - 30 Squares')
