import os
import sys
import time

import pandas as pd

from src.Application.Generate_Squares.Generate_Squares_Support_Functions import (
    get_square_coordinates)
from src.Application.Utilities.General_Support_Functions import (
    format_time_nicely)
from src.Fiji.LoggerConfig import (
    paint_logger_change_file_handler_name,
    paint_logger_file_name_assigned, paint_logger)

if not paint_logger_file_name_assigned:
    paint_logger_change_file_handler_name('Generate Squares.log')


def add_dc_to_squares_file(df_tracks: pd.DataFrame, nr_of_squares_in_row: int, project_directory: str):
    """
    Add the diffusion coefficient to the squares file. The squares file are assumed to be in the project directory tree.
    """

    time_stamp = time.time()

    # Find out which unique Recordings there are
    # recording_names = df_tracks['Recording Name'].unique().tolist()

    recording_names = find_ext_recording_names(project_directory)

    paint_logger.info(
        f"Updating {len(recording_names)} squares file in {project_directory} with calculated Diffusion Coefficient")

    line_count = 0
    image_count = 0
    for recording_name in recording_names:

        # For each recording get the tracks
        df_tracks_in_recording = df_tracks[df_tracks['Recording Name'] == recording_name]

        # Find the squares file associated with this recording
        squares_file_path = find_squares_file(project_directory, recording_name + '-squares.csv')
        if squares_file_path:
            df_squares = pd.read_csv(squares_file_path)
            df_squares['Diffusion Coefficient'] = 0
        else:
            paint_logger.error(
                f"Could not find squares file {recording_name + '-squares.csv'} for recording {recording_name}")
            sys.exit()

        # Now determine for each square which tracks fit in, start
        for index, row in df_squares.iterrows():
            square_nr = row['Square Nr']
            x0, y0, x1, y1 = get_square_coordinates(nr_of_squares_in_row, square_nr)
            df_tracks_in_square = df_tracks_in_recording[
                (df_tracks_in_recording['Track X Location'] >= x0) & (
                        df_tracks_in_recording['Track X Location'] <= x1) &
                (df_tracks_in_recording['Track Y Location'] >= y0) & (df_tracks_in_recording['Track Y Location'] <= y1)]
            if len(df_tracks_in_square) > 0:
                dc_mean = df_tracks_in_square['Diffusion Coefficient'].mean()
            else:
                dc_mean = -1
            df_squares.loc[index, 'Diffusion Coefficient'] = int(dc_mean)
            line_count += 1

        df_squares.to_csv(squares_file_path, index=False)
        paint_logger.debug(
            f"File {squares_file_path} was updated: {line_count} squares with a valid Diffusion Coefficient")
        image_count += 1

    run_time = round(time.time() - time_stamp, 1)
    paint_logger.info(
        f"Updated {line_count:2d} lines in {image_count} images in {project_directory} in {format_time_nicely(run_time)}")
    paint_logger.info("")


def find_squares_file(root_directory, target_filename):
    for dirpath, dirnames, filenames in os.walk(root_directory):
        if target_filename in filenames:
            # Join the directory path with the filename to get the full path
            return os.path.join(dirpath, target_filename)
    return None  # Return None if the file is not found


def find_ext_recording_names(directory):
    ext_recording_names = []

    # Walk through the directory tree
    for root, _, files in os.walk(directory):
        for file in files:
            if file == "experiment_squares.csv":
                file_path = os.path.join(root, file)

                # Read the CSV file
                try:
                    df = pd.read_csv(file_path)

                    # Check if required columns are in the file
                    if 'Ext Recording Name' in df.columns and 'Process' in df.columns:
                        # Filter rows where 'Process' is 'yes' and collect 'Ext Recording Name' values
                        names = df.loc[df['Process'].str.lower() == 'yes', 'Ext Recording Name']
                        ext_recording_names.extend(names.tolist())
                    else:
                        print(f"Warning: Required columns missing in {file_path}")

                except Exception as e:
                    print(f"Error reading {file_path}: {e}")

    return ext_recording_names
