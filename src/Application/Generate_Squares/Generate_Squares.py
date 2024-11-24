import os
import time

import numpy as np
import pandas as pd

from src.Application.Recording_Viewer.Select_Squares import (
    select_squares_with_parameters,
    label_selected_squares_and_tracks)
from src.Fiji.LoggerConfig import (
    paint_logger,
    paint_logger_change_file_handler_name,
    paint_logger_file_name_assigned)

if not paint_logger_file_name_assigned:
    paint_logger_change_file_handler_name('Generate Squares.log')

from src.Application.Generate_Squares.Generate_Squares_Support_Functions import (
    get_square_coordinates,
    calc_variability,
    calculate_density,
    calc_area_of_square,
    calc_average_track_count_in_background_squares,
    create_unique_key_for_squares,
    extra_constraints_on_tracks_for_tau_calculation,
    add_columns_to_experiment,
    read_recordings_of_experiment,
    read_tracks_of_experiment,
    get_row_and_column,
    calculate_tau,
    calculate_average_long_track
)

from src.Application.Utilities.General_Support_Functions import (
    format_time_nicely)

from src.Fiji.DirectoriesAndLocations import (
    delete_files_in_directory)

from src.Fiji.PaintConfig import (
    get_paint_attribute)

if not paint_logger_file_name_assigned:
    paint_logger_change_file_handler_name('Generate Squares.log')


# ----------------------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------------------
#                                       Process Project
# ----------------------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------------------

def process_project(
        project_path: str,
        select_parameters: dict,
        nr_of_squares_in_row: int,
        min_allowable_r_squared: float,
        min_tracks_for_tau: int,
        paint_force: bool = False) -> None:
    """
    This function processes all Recordings in a Project.
    It calls the function 'process_experiment' for each Experiment in the Project.
    """

    paint_logger.info(f"Starting generating squares for all recordings in {project_path}")
    paint_logger.info('')
    experiment_dirs = os.listdir(project_path)
    experiment_dirs.sort()

    nr_experiments_processed = 0
    for experiment_dir in experiment_dirs:

        # Skip if not a directory or if it is the Output directory
        if not os.path.isdir(os.path.join(project_path, experiment_dir)):
            continue
        if 'Output' in experiment_dir:
            continue

        # Look at the time tags and decide if reprocessing is needed. Always process when the paint_force flag is set
        if (os.path.exists(os.path.join(project_path, experiment_dir)) and
                os.path.exists(os.path.join(project_path, experiment_dir, 'All Squares.csv')) and
                os.path.exists(os.path.join(project_path, experiment_dir, 'All Recordings.csv')) and
                os.path.exists(os.path.join(project_path, experiment_dir, 'All Tracks.csv')) and
                not paint_force):
            paint_logger.info('')
            paint_logger.info(f"Experiment output exists and skipped: {experiment_dir}")
            paint_logger.info('')
            continue

        # Process the experiment
        process_experiment(
            os.path.join(project_path, experiment_dir),
            select_parameters=select_parameters,
            nr_of_squares_in_row=nr_of_squares_in_row,
            min_allowable_r_squared=min_allowable_r_squared,
            min_tracks_for_tau=min_tracks_for_tau)
        nr_experiments_processed += 1

    return nr_experiments_processed


# ----------------------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------------------
#                                    Process Experiment
# ----------------------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------------------


def process_experiment(
        experiment_path: str,
        select_parameters: dict,
        nr_of_squares_in_row: int,
        min_allowable_r_squared: float,
        min_tracks_for_tau: int,
        paint_force: bool = False) -> None:
    """
    This function processes all Recordings in an Experiment.
    It reads the All Recordings file to find out which Recordings need processing
    """

    # Preparations
    plot_to_file = get_paint_attribute('Generate Squares', 'Plot to File') or ""
    plot_max = get_paint_attribute('Generate Squares', 'Plot Max') or 5
    time_stamp = time.time()
    df_squares_of_experiment = pd.DataFrame()
    df_tracks_of_experiment_with_labels = pd.DataFrame()

    # Read the Tracks file and add (or reinitialise two columns for the square and label numbers)
    df_tracks_of_experiment = read_tracks_of_experiment(experiment_path)

    # Read the Recordings file, check the integrity and add some columns
    df_recordings_of_experiment = read_recordings_of_experiment(experiment_path)

    # Add some parameters that the user just specified to the experiment
    df_recordings_of_experiment = add_columns_to_experiment(
        df_recordings_of_experiment,
        nr_of_squares_in_row,
        min_tracks_for_tau,
        min_allowable_r_squared,
        select_parameters['min_required_density_ratio'],
        select_parameters['max_allowable_variability'])

    # Determine how many names there are from Recordings and Tracks anc compare
    nr_files_tracks = df_tracks_of_experiment['Ext Recording Name'].nunique()
    nr_files_recordings = len(df_recordings_of_experiment)
    if nr_files_recordings != nr_files_tracks:
        paint_logger.info("All Squares file is not consistent with All Recordings")
    nr_files = nr_files_tracks
    if nr_files <= 0:
        paint_logger.info("No files selected for processing")
        return

    # --------------------------------------------------------------------------------------------
    # Loop though selected recordings
    # --------------------------------------------------------------------------------------------

    current_image_nr = 1
    processed = 0

    nr_of_recordings_to_process = len(
        df_recordings_of_experiment[df_recordings_of_experiment['Process'].isin(['Yes', 'y', 'Y'])])
    paint_logger.info(f"Processing {nr_of_recordings_to_process:2d} images in {experiment_path}")

    for index, recording_data in df_recordings_of_experiment.iterrows():

        recording_name = recording_data['Ext Recording Name']

        # Process the Recording
        paint_logger.debug(f"Processing file {current_image_nr} of {nr_of_recordings_to_process}: {recording_name}")

        df_tracks_of_recording = df_tracks_of_experiment[
            df_tracks_of_experiment['Ext Recording Name'] == recording_name]
        df_squares_of_recording, df_tracks_of_recording, recording_tau, recording_r_squared, recording_density = process_recording(
            df_tracks_of_recording,
            select_parameters,
            recording_data,
            experiment_path,
            recording_name,
            nr_of_squares_in_row,
            min_allowable_r_squared,
            min_tracks_for_tau,
            plot_to_file)
        if df_squares_of_recording is None:
            paint_logger.error("Aborted with error")
            return None

        # Update the Experiment with the results
        df_recordings_of_experiment.at[index, 'Ext Recording Name'] = recording_name
        df_recordings_of_experiment.at[index, 'Tau'] = recording_tau
        df_recordings_of_experiment.at[index, 'Density'] = recording_density
        df_recordings_of_experiment.at[index, 'R Squared'] = round(recording_r_squared, 3)

        current_image_nr += 1
        processed += 1
        df_squares_of_experiment = pd.concat([df_squares_of_experiment, df_squares_of_recording], ignore_index=True)
        df_tracks_of_experiment_with_labels = pd.concat([df_tracks_of_experiment_with_labels, df_tracks_of_recording],
                                                        ignore_index=True)

    # Save the updated tracks to the All Tracks file (the square and label columns have been updated)
    df_tracks_of_experiment_with_labels.to_csv(os.path.join(experiment_path, 'All Tracks.csv'), index=False)

    # Save df_squares_of_experiment into the All Recordings file
    df_recordings_of_experiment.to_csv(os.path.join(experiment_path, "All Recordings.csv"), index=False)

    # Make a unique index and then save df_squares_of_experiment into the All Squares file
    df_squares_of_experiment = create_unique_key_for_squares(df_squares_of_experiment)
    df_squares_of_experiment.to_csv(os.path.join(experiment_path, "All Squares.csv"), index=False)

    run_time = round(time.time() - time_stamp, 1)
    paint_logger.info(f"Processed  {nr_files:2d} images in {experiment_path} in {format_time_nicely(run_time)}")


# ----------------------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------------------
#                                   Process Recording
# ----------------------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------------------


def process_recording(
        df_tracks_of_recording: pd.DataFrame,
        select_parameters: dict,
        recording_data: pd.Series,
        experiment_path: str,
        recording_name: str,
        nr_of_squares_in_row: int,
        min_allowable_r_squared: float,
        min_tracks_for_tau: int,
        plot_to_file: False) -> tuple:
    """
    This function processes a single Recording in an Experiment. It creates a grid of squares.
    For each square, the Tau and Density ratio is calculated. The squares are then filtered on visibility.
    """

    # Create the Plot directory if needed
    if plot_to_file:
        plot_dir = os.path.join(experiment_path, 'Plot')
        if not os.path.exists(plot_dir):
            os.makedirs(plot_dir)
        else:
            delete_files_in_directory(plot_dir)

    # -----------------------------------------------------------------------------------------------------
    # A df_squares_of_recording dataframe is generated and, if the process_square_tau flag is set, for every square the
    # Tau and Density are calculated. The results are stored in 'All Squares'.
    # -----------------------------------------------------------------------------------------------------

    # Create the tau_matrix
    tau_matrix = np.zeros((nr_of_squares_in_row, nr_of_squares_in_row), dtype=int)

    # Create an empty squares dataframe, that will contain the data for each square
    df_squares_of_recording = pd.DataFrame()
    nr_total_squares = int(nr_of_squares_in_row * nr_of_squares_in_row)
    square_area = calc_area_of_square(nr_of_squares_in_row)

    # --------------------------------------------------------------------------------------------
    # Generate the data for a square in a row and append it to the squares dataframe
    # --------------------------------------------------------------------------------------------

    for square_seq_nr in range(nr_total_squares):
        # Calculate the square_data and column number from the sequence number (all are 0-based)
        row_nr, col_nr = get_row_and_column(square_seq_nr, nr_of_squares_in_row)
        concentration = float(recording_data['Concentration'])

        square_data = process_square(
            df_tracks_of_recording,
            df_tracks_of_recording,
            recording_data,
            nr_of_squares_in_row,
            concentration,
            min_allowable_r_squared,
            min_tracks_for_tau,
            square_area,
            square_seq_nr,
            row_nr,
            col_nr)

        # And add it to the squares dataframe and the recorisng_tau to the tau_matrix
        df_squares_of_recording = pd.concat([df_squares_of_recording, pd.DataFrame.from_records([square_data])])
        tau_matrix[row_nr, col_nr] = int(square_data['Tau'])

    nr_tracks_in_background = calc_average_track_count_in_background_squares(df_squares_of_recording,
                                                                             int(0.1 * nr_total_squares))
    if nr_tracks_in_background == 0:
        df_squares_of_recording['Density Ratio'] = 999.9  # Special code
    else:
        df_squares_of_recording['Density Ratio'] = round(df_squares_of_recording['Nr Tracks'] / nr_tracks_in_background,
                                                         1)

    # Assign labels in All Squares, so that selected tracks are assigned to squares.
    select_squares_with_parameters(
        df_squares=df_squares_of_recording,
        select_parameters=select_parameters,
        nr_of_squares_in_row=nr_of_squares_in_row,
        only_valid_tau=True)
    df_squares_of_recording, df_tracks_of_recording = label_selected_squares_and_tracks(df_squares_of_recording,
                                                                                        df_tracks_of_recording)

    # ----------------------------------------------------------------------------------------------------
    # Now do the single mode processing: determine a single Tau and Density per image, i.e., for all squares
    # and return those values
    # ----------------------------------------------------------------------------------------------------

    # Refresh df_tracks_of_recording now to pick up Label and Square Nrs
    df_tracks_of_recording = df_tracks_of_recording[df_tracks_of_recording['Ext Recording Name'] == recording_name]

    recording_tau, recording_r_squared, recording_density = calculate_tau_and_density_for_recording(
        df_squares_of_recording,
        df_tracks_of_recording,
        min_tracks_for_tau,
        min_allowable_r_squared,
        nr_of_squares_in_row,
        float(recording_data['Concentration']),
        select_parameters)

    return df_squares_of_recording, df_tracks_of_recording, recording_tau, recording_r_squared, recording_density


# ----------------------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------------------
#                                    Process Square
# ----------------------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------------------

def process_square(
        df_tracks_of_experiment: pd.DataFrame,
        df_tracks_of_recording: pd.DataFrame,
        recording_data: pd.Series,
        nr_of_squares_in_row: int,
        concentration: float,
        min_allowable_r_squared: float,
        min_tracks_for_tau: int,
        square_area: float,
        square_seq_nr: int,
        row_nr: int,
        col_nr: int) -> pd.Series:
    # Determine which tracks fall within the square defined by boundaries x0, y0, x1, y1
    x0, y0, x1, y1 = get_square_coordinates(nr_of_squares_in_row, square_seq_nr)
    mask = ((df_tracks_of_recording['Track X Location'] >= x0) &
            (df_tracks_of_recording['Track X Location'] < x1) &
            (df_tracks_of_recording['Track Y Location'] >= y0) &
            (df_tracks_of_recording['Track Y Location'] < y1))
    df_tracks_of_square = df_tracks_of_recording[mask]
    df_tracks_of_experiment.loc[df_tracks_of_square['Unique Key'], 'Square Nr'] = int(square_seq_nr)

    # Provide reasonable values for squares not containing any tracks
    nr_of_tracks_in_square = len(df_tracks_of_square)
    if nr_of_tracks_in_square == 0:
        total_track_duration = 0
        average_long_track = 0
        max_track_duration = 0
        r_squared = 0
        tau = -1
        density = 0
        variability = 0
        dc_mean = 0

    else:

        # Calculate the sum of track durations for the square
        total_track_duration = sum(df_tracks_of_square['Track Duration'])

        # Calculate the average of the long tracks for the square
        average_long_track = calculate_average_long_track(df_tracks_of_square)

        # Calculate the maximum track duration
        max_track_duration = df_tracks_of_square['Track Duration'].max()

        # Calculate the Tau and R squared for the square
        tau = 0
        r_squared = 0
        df_tracks_for_tau = extra_constraints_on_tracks_for_tau_calculation(df_tracks_of_square)
        tau, r_squared = calculate_tau(
            df_tracks_for_tau,
            min_tracks_for_tau,
            min_allowable_r_squared)

        # Calculate the density for the square-
        density = calculate_density(
            nr_tracks=nr_of_tracks_in_square, area=square_area, time=100, concentration=concentration,
            magnification=1000)

        # Calculate the variability for the square
        variability = calc_variability(df_tracks_of_square, square_seq_nr, nr_of_squares_in_row, 10)

        # Calculate the diffusion coefficient for the square
        dc_mean = df_tracks_of_square['Diffusion Coefficient'].mean()

    # Create the new squares record to add all the data for this square
    square_data = {
        'Recording Sequence Nr': recording_data['Recording Sequence Nr'],
        'Ext Recording Name': recording_data['Ext Recording Name'],
        'Experiment Name': recording_data['Experiment Name'],
        'Experiment Date': recording_data['Experiment Date'],
        'Condition Nr': recording_data['Condition Nr'],
        'Replicate Nr': recording_data['Replicate Nr'],
        'Square Nr': int(square_seq_nr),
        'Probe': recording_data['Probe'],
        'Probe Type': recording_data['Probe Type'],
        'Cell Type': recording_data['Cell Type'],
        'Adjuvant': recording_data['Adjuvant'],
        'Concentration': recording_data['Concentration'],
        'Threshold': recording_data['Threshold'],
        'Row Nr': int(row_nr + 1),
        'Col Nr': int(col_nr + 1),
        'Label Nr': 0,
        'Cell Id': 0,
        'Nr Spots': recording_data['Nr Spots'],
        'Nr Tracks': int(nr_of_tracks_in_square),
        'X0': round(x0, 2),
        'Y0': round(y0, 2),
        'X1': round(x1, 2),
        'Y1': round(y1, 2),
        'Selected': True,
        'Variability': round(variability, 2),
        'Density': round(density, 1),
        'Density Ratio': 0.0,
        'Tau': round(tau, 0),
        'R Squared': round(r_squared, 2),
        'Diffusion Coefficient': round(dc_mean, 0),
        'Average Long Track Duration': round(average_long_track, 1),
        'Max Track Duration': round(max_track_duration, 1),
        'Total Track Duration': round(total_track_duration, 1),
    }

    return square_data


# ----------------------------------------------------------------------------------------------------
#                        calculate_tau_and_density_for_recording
# ----------------------------------------------------------------------------------------------------

def calculate_tau_and_density_for_recording(
        df_squares: pd.DataFrame,
        df_recording_tracks: pd.DataFrame,
        min_tracks_for_tau: int,
        min_allowable_r_squared: float,
        nr_of_squares_in_row: int,
        concentration: float,
        select_parameters: dict
) -> tuple:
    """
    This function calculates a single Tau and Density for a Recording. It does this by considering all the tracks
    in the image that meet the selection criteria.
    Note that also squares are included for which no square Tau could be calculated (provided they meet the selection
    criteria). The Tau and Density are calculated for the entire image, not for individual squares.
    """

    # Within that recording use all the selected squares. Note: no need to filter out squares with Ta < 0
    select_squares_with_parameters(
        df_squares=df_squares,
        select_parameters=select_parameters,
        nr_of_squares_in_row=nr_of_squares_in_row,
        only_valid_tau=False)
    df_squares_for_single_tau = df_squares[df_squares['Selected']]

    # Select only the tracks that fall within these squares.
    # The following code filters df_tracks to include rows where Square Nr values match those
    # in df_squares_for_single_tau

    df_tracks_for_tau = df_recording_tracks[
        df_recording_tracks['Square Nr'].isin(df_squares_for_single_tau['Square Nr'])]
    nr_of_tracks_for_single_tau = len(df_tracks_for_tau)

    df_tracks_for_tau = extra_constraints_on_tracks_for_tau_calculation(df_tracks_for_tau)
    tau, r_squared = calculate_tau(
        df_tracks_for_tau,
        min_tracks_for_tau,
        min_allowable_r_squared)

    # Calculate the Density
    area = calc_area_of_square(nr_of_squares_in_row)
    density = calculate_density(
        nr_tracks=nr_of_tracks_for_single_tau, area=area, time=100, concentration=concentration, magnification=1000)

    return tau, r_squared, density
