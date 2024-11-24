import os
import sys

import numpy as np
import pandas as pd

from src.Application.Generate_Squares.Curvefit_and_Plot import (
    compile_duration,
    curve_fit_and_plot
)
from src.Fiji.LoggerConfig import paint_logger
from src.Fiji.PaintConfig import get_paint_attribute

pd.options.mode.copy_on_write = True


def calculate_density(nr_tracks: int, area: float, time: float, concentration: float, magnification: float) -> float:
    """
    The function implements a simple algorithm to calculate the density of tracks in a square.
    To calculate the density use the actual surface coordinates.
    Assume 2000 frames (100 sec) -  need to check - this is not always the case
    Multiply by 1000 to get an easier number
    Area is calculated with Fiji info:
        Width: 82.0864 microns(512)
        Height: 82.0864 microns(512)
    The area of a square then is (82.0854/nr_of_squares_in_row)^2

    To normalise the concentration we divide by the supplied concentration

    :param nr_tracks:
    :param area:
    :param time: Normally 100 sec (2000 frames)
    :param concentration:
    :param magnification: use 1000 to getr easier numbers
    :return: the density
    """

    density = nr_tracks / area
    density /= time
    density /= concentration
    density *= magnification
    density = round(density, 1)
    return density


def get_square_coordinates(nr_of_squares_in_row, sequence_number):
    """

    :param nr_of_squares_in_row:
    :param sequence_number: The sequence number of the square for which the coordinates are needed
    :return: The coordinates of the upper left (x0, y0) and lower right corner (x1, y1)
    """
    width = 82.0864 / nr_of_squares_in_row
    height = 82.0864 / nr_of_squares_in_row

    i = sequence_number % nr_of_squares_in_row
    j = sequence_number // nr_of_squares_in_row

    x0 = i * width
    x1 = (i + 1) * width
    y0 = j * height
    y1 = (j + 1) * width
    return x0, y0, x1, y1


def calc_variability(df_tracks, square_nr, nr_of_squares_in_row, granularity):
    """
    The variability is calculated by creating a grid of granularity x granularity in the square for
    which tracks_fd specifies the tracks
    :param df_tracks: A dataframe that contains the tracks of the square for which the variability is calculated
    :param square_nr: The sequence number of the square for which the variability is calculated
    :param nr_of_squares_in_row: The number of rows and columns in the image
    :param granularity: Specifies how fine the grid is that is created
    :return:
    """

    # Create the matrix for the variability analysis
    matrix = np.zeros((granularity, granularity), dtype=int)

    # Loop over all the tracks in the square and determine where they sit in the grid
    for index, row in df_tracks.iterrows():
        # Retrieve the x and y values expressed in micrometers
        x = float(row["Track X Location"])
        y = float(row["Track Y Location"])

        # The width of the image is 82.0864 micrometer. The width and height of a square can be calculated
        width = 82.0864 / nr_of_squares_in_row
        height = width

        # Get the grid indices for this track and update the matrix
        xi, yi = get_indices(x, y, width, height, square_nr, nr_of_squares_in_row, 10)
        matrix[yi, xi] += 1

    # Calculate the variability by dividing the standard deviation by the average
    std = np.std(matrix)
    mean = np.mean(matrix)
    if mean != 0:
        variability = std / mean
    else:
        variability = 0
    return variability


def get_indices(x1: float, y1: float, width: float, height: float, square_seq_nr: int, nr_of_squares_in_row: int,
                granularity: int) -> tuple[int, int]:
    """
    Given coordinates (x1, y1) of the track, calculate the indices of the grid

    :param x1: The x coordinate of the track
    :param y1: The y coordinate of the track
    :param width: The width of a grid in the square
    :param height: The height of a grid in the square
    :param square_seq_nr: The number of the square for which the variability is calculated
    :param nr_of_squares_in_row: The numbers of rows and columns in the full image
    :param granularity: Specifies how fine the grid is that is overlaid on the square
    :return: The indices (xi, yi) of the grid
    """

    # Calculate the top-left corner (x0, y0) of the square
    x0 = (square_seq_nr % nr_of_squares_in_row) * width
    y0 = (square_seq_nr // nr_of_squares_in_row) * height

    # Calculate the grid indices (xi, yi) for the track
    xi = int(((x1 - x0) / width) * granularity)
    yi = int(((y1 - y0) / height) * granularity)

    return xi, yi


def check_experiment_integrity(df_experiment):
    """
    Check if the experiment file has the expected columns and makes sure that the types are correct
    :param df_experiment:
    :return:
    """
    expected_columns = {
        'Recording Sequence Nr',
        'Recording Name',
        'Experiment Date',
        'Experiment Name',
        'Condition Nr',
        'Replicate Nr',
        'Probe',
        'Probe Type',
        'Cell Type',
        'Adjuvant',
        'Concentration',
        'Threshold',
        'Process',
        'Ext Recording Name',
        'Nr Spots',
        'Recording Size',
        'Run Time',
        'Time Stamp'}.issubset(df_experiment.columns)

    if expected_columns:
        # Make sure that there is a meaningful index           # TODO: Check if this is not causing problems
        df_experiment.set_index('Recording Sequence Nr', inplace=True, drop=False)
        return True
    else:
        return False


def calc_average_track_count_in_background_squares(df_squares, nr_of_average_count_squares):
    """
    The function calculates the average track count of the lowest average_count_squares squares with a track count > 0.
    The df_squares df is already sorted on track number.
    All we have to do is access backwards, ignore 0 values and only then start counting.

    :param df_squares:
    :param nr_of_average_count_squares:
    :return:
    """

    count_values = list(df_squares['Nr Tracks'])
    count_values.sort(reverse=True)

    total = 0
    n = 0
    for i in range(len(count_values) - 1, -1, -1):
        if count_values[i] > 0:
            total += count_values[i]
            n += 1
            if n >= nr_of_average_count_squares:
                break
    if n == 0:
        average = 0
    else:
        average = total / n
    return average


def calc_area_of_square(nr_of_squares_in_row):
    micrometer_per_pixel = 0.1602804  # Referenced from Fiji
    pixel_per_image = 512  # Referenced from Fiji
    micrometer_per_image = micrometer_per_pixel * pixel_per_image
    micrometer_per_square = micrometer_per_image / nr_of_squares_in_row
    area = micrometer_per_square * micrometer_per_square
    return area


def create_unique_key_for_squares(df):
    df['String Square Nr'] = df['Square Nr'].astype(str)
    df['Unique Key'] = df['Ext Recording Name'] + ' - ' + df['String Square Nr']
    df.set_index('Unique Key', inplace=True, drop=False)
    df.drop('String Square Nr', axis=1, inplace=True)

    # Reorder the columns
    cols = list(df.columns)
    cols.insert(0, cols.pop(cols.index('Unique Key')))
    df = df[cols]
    return df


def extra_constraints_on_tracks_for_tau_calculation(df_tracks_in_square):
    limit_dc = get_paint_attribute('Generate Squares', 'Exclude zero DC tracks from Tau Calculation') or False
    if limit_dc:
        df_tracks_in_square = df_tracks_in_square[df_tracks_in_square['Diffusion Coefficient'] > 0]
    return df_tracks_in_square


def create_unique_key_for_tracks(df):
    df['Unique Key'] = df['Ext Recording Name'] + ' - ' + df['Track Label'].str.split('_').str[1]
    df.set_index('Unique Key', inplace=True, drop=False)

    # Reorder the columns
    cols = list(df.columns)
    cols.insert(0, cols.pop(cols.index('Unique Key')))
    df = df[cols]
    return df


def add_columns_to_experiment(
        df_experiment: pd.DataFrame,
        nr_of_squares_in_row: int,
        min_tracks_for_tau: int,
        min_allowable_r_squared: float,
        min_required_density_ratio: float,
        max_allowable_variability: float):
    """
    This function adds columns to the experiment file that are needed for the grid processing.
    Only images for which the 'Process' column is set to 'Yes' are processed.
    """

    mask = ((df_experiment['Process'] == 'Yes') |
            (df_experiment['Process'] == 'yes') |
            (df_experiment['Process'] == 'Y') |
            (df_experiment['Process'] == 'y'))

    # User specified parameters
    df_experiment.loc[mask, 'Min Tracks for Tau'] = int(min_tracks_for_tau)
    df_experiment.loc[mask, 'Min Allowable R Squared'] = round(min_allowable_r_squared, 2)
    df_experiment.loc[mask, 'Nr of Squares in Row'] = int(nr_of_squares_in_row)
    df_experiment.loc[mask, 'Max Allowable Variability'] = round(max_allowable_variability, 1)
    df_experiment.loc[mask, 'Min Required Density Ratio'] = round(min_required_density_ratio, 1)

    # Default values
    df_experiment.loc[mask, 'Exclude'] = False
    df_experiment.loc[mask, 'Neighbour Mode'] = 'Free'

    # Recording specific values
    df_experiment.loc[mask, 'Tau'] = 0
    df_experiment.loc[mask, 'Density'] = 0
    df_experiment.loc[mask, 'R Squared'] = 0.0

    return df_experiment


def pack_select_parameters(
        min_required_density_ratio: float,
        max_allowable_variability: float,
        min_track_duration: int,
        max_track_duration: int,
        min_allowable_r_squared: float,
        neighbour_mode: str):
    select_parameters = {
        'min_required_density_ratio': min_required_density_ratio,
        'max_allowable_variability': max_allowable_variability,
        'min_track_duration': min_track_duration,
        'max_track_duration': max_track_duration,
        'min_allowable_r_squared': min_allowable_r_squared,
        'neighbour_mode': neighbour_mode
    }
    return select_parameters


def calculate_tau(
        df_tracks_for_tau: pd.DataFrame,
        min_tracks_for_tau: int,
        min_allowable_r_squared: float
) -> tuple:
    """
    Calculate the Tau for the square if requested. Use error codes:
       -1: too few points to try to fit
       -2: curve fitting tries, but failed
       -3: curve fitting succeeded, but R2 is too low
    """

    if len(df_tracks_for_tau) < min_tracks_for_tau:  # Too few points to curve fit
        tau = -1
        r_squared = 0
    else:
        duration_data = compile_duration(df_tracks_for_tau)
        tau, r_squared = curve_fit_and_plot(plot_data=duration_data)
        if tau == -2:  # Tau calculation failed
            r_squared = 0
        if r_squared < min_allowable_r_squared:  # Tau was calculated, but not reliable
            tau = -3
            tau = int(tau)

    return tau, r_squared


def calculate_average_long_track(df_tracks):
    """
    Calculate the average of the long tracks for the square
    The long tracks are defined as the longest 10% of the tracks
    """
    nr_of_tracks = len(df_tracks)
    if nr_of_tracks == 0:
        average_long_track = 0
    else:
        df_tracks.sort_values(by=['Track Duration'], inplace=True)
        fraction = get_paint_attribute('Generate Squares',
                                       'Fraction of Squares to Determine Background') or 0.1
        nr_tracks_to_average = max(round(fraction * nr_of_tracks),  1)
        average_long_track = df_tracks.tail(nr_tracks_to_average)['Track Duration'].mean()
    return average_long_track


def read_tracks_of_experiment(experiment_path: str) -> pd.DataFrame:
    """
    Read the All Tracks file for an Experiment
    """

    df_tracks_of_experiment = pd.read_csv(os.path.join(experiment_path, 'All Tracks.csv'))
    if df_tracks_of_experiment is None:
        paint_logger.error(f"Could not read the 'All Tracks.csv' file in {experiment_path}")
        sys.exit(1)
    df_tracks_of_experiment = create_unique_key_for_tracks(df_tracks_of_experiment)
    if df_tracks_of_experiment is None:
        paint_logger.error(f"Could not read the 'All Tracks.csv' file in {experiment_path}")
        sys.exit(1)
    df_tracks_of_experiment['Square Nr'] = None
    df_tracks_of_experiment['Label Nr'] = None
    return df_tracks_of_experiment


def read_recordings_of_experiment(experiment_path: str) -> pd.DataFrame:
    """
    Read the All Recordings file for an Experiment
    """
    df_recordings_of_experiment = pd.read_csv(os.path.join(experiment_path, 'All Recordings.csv'))
    if df_recordings_of_experiment is None:
        paint_logger.error(
            f"Function 'process_experiment' failed: Likely, {experiment_path} is not a valid  \
                directory containing cell image information.")
        sys.exit(1)
    if len(df_recordings_of_experiment) == 0:
        paint_logger.error(
            f"Function 'process_experiment' failed: 'All Recordings.csv' in {experiment_path} \
                is empty")
        sys.exit(1)

    # Confirm the experiment is in the correct format
    if not check_experiment_integrity(df_recordings_of_experiment):
        paint_logger.error(
            f"Function 'process_experiment' failed: The experiment file in {experiment_path} is not in the valid format.")
        sys.exit(1)

    return df_recordings_of_experiment


def get_row_and_column(square_seq_nr: int, nr_of_squares_in_row: int) -> tuple:
    col_nr = square_seq_nr % nr_of_squares_in_row
    row_nr = square_seq_nr // nr_of_squares_in_row
    return row_nr, col_nr
