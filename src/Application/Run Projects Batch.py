import json
import os
import shutil
import sys
import time
from datetime import datetime

from src.Application.Compile_Project.Compile_Project import compile_project_output
from src.Application.Compile_Project.Copy_TM_Data_From_Source import copy_tm_data_from_paint_source_with_images
from src.Application.Generate_Squares.Generate_Squares import process_project
from src.Application.Generate_Squares.Generate_Squares_Support_Functions import pack_select_parameters
from src.Application.Utilities.General_Support_Functions import format_time_nicely
from src.Application.Utilities.Set_Directory_Tree_Timestamp import (
    set_directory_tree_timestamp,
    get_timestamp_from_string)
from src.Fiji.LoggerConfig import (
    paint_logger,
    paint_logger_change_file_handler_name,
    paint_logger_console_handle_set_level,
    get_paint_logger_directory,
    DEBUG as PAINT_DEBUG
)
from src.Fiji.PaintConfig import get_paint_attribute

paint_logger_change_file_handler_name('Process All Projects.log')
paint_logger_console_handle_set_level(PAINT_DEBUG)

PAINT_FORCE = False


def process_json_configuration_block(paint_source_dir,
                                     project_name: str,
                                     project_path: str,
                                     r_dest_dir: str,
                                     select_parameters: dict,
                                     probe: str,
                                     nr_of_squares_in_row: int,
                                     nr_to_process: int,
                                     current_process: int,
                                     min_allowable_r_squared: float,
                                     min_tracks_for_tau: int,
                                     time_string: str,
                                     paint_force: bool) -> bool:
    time_stamp = time.time()
    msg = f"{current_process} of {nr_to_process} - Processing {project_name}"
    paint_logger.info("")
    paint_logger.info("")
    paint_logger.info("-" * 40)
    paint_logger.info(msg)
    paint_logger.info("")
    paint_logger.info(f"Probe Series                : {probe}")
    paint_logger.info(f"Number of squares           : {nr_of_squares_in_row}")
    paint_logger.info(f"Min Required Density Ratio  : {select_parameters['min_required_density_ratio']}")
    paint_logger.info(f"Max Allowable Variability   : {select_parameters['max_allowable_variability']}")
    paint_logger.info(f"Min Track Duration          : {select_parameters['min_track_duration']}")
    paint_logger.info(f"Max Track Duration          : {select_parameters['max_track_duration']}")
    paint_logger.info(f"Neighbour Mode              : {select_parameters['neighbour_mode']}")
    paint_logger.info(f"Min Allowable R squared     : {min_allowable_r_squared}")
    paint_logger.info(f"Min tracks for tau          : {min_tracks_for_tau}")
    paint_logger.info(f"Paint Force                 : {paint_force}")

    paint_logger.info("")
    paint_logger.info("-" * 40)
    paint_logger.info("")

    # Check if the Paint Source directory exists
    if not os.path.exists(paint_source_dir):
        paint_logger.error(f"Paint Source directory {paint_source_dir} does not exist.")
        return False

    # Check if the Paint Data directory exists
    if not os.path.exists(project_path):
        paint_logger.info(f"Paint Data directory {project_path} does not exist, directory created.")
        os.makedirs(project_path)

    # Copy the data from Paint Source to the appropriate directory in Paint Data
    copy_tm_data_from_paint_source_with_images(paint_source_dir, project_path)

    # if not os.path.exists(r_dest_dir):
    #     os.makedirs(r_dest_dir)

    nr_experiments_processed = process_project(
        project_path=project_path,
        select_parameters=select_parameters,
        nr_of_squares_in_row=nr_of_squares_in_row,
        min_allowable_r_squared=min_allowable_r_squared,
        min_tracks_for_tau=min_tracks_for_tau,
        paint_force=paint_force)

    # Compile the All Recordings and All Squares files
    if nr_experiments_processed > 0:
        compile_project_output(project_path, verbose=True)
    else:
        paint_logger.info(f"No experiments processed in {project_path}")
        paint_logger.info(f"No All Recordings, All Squares, All Tracks compiled for {project_path}")

    # Now copy the data from the Paint Data directory to the R space
    if False:
        output_source = project_path
        output_destination = os.path.join(r_dest_dir, 'Output')
        os.makedirs(output_destination, exist_ok=True)
        try:
            shutil.copy(os.path.join(output_source, 'Squares.csv'), output_destination)
            shutil.copy(os.path.join(output_source, 'Tracks.csv'), output_destination)
            shutil.copy(os.path.join(output_source, 'Recordings.csv'), output_destination)
            paint_logger.info(f"Copied output to {output_destination}")
        except Exception:
            paint_logger.error(f"Failed to copy output to {output_destination}")

    # Set the timestamp for the R data destination directory

    if time_string != '':
        specific_time = get_timestamp_from_string(time_string)
        if specific_time is None:
            paint_logger.error(f"Time string '{time_stamp}' is not a valid date string.")
    else:
        specific_time = None
    # set_directory_tree_timestamp(r_dest_dir, specific_time)
    set_directory_tree_timestamp(project_path, specific_time)

    paint_logger.info("")
    paint_logger.info(
        f"Processed block in {format_time_nicely(time.time() - time_stamp)}")
    return True


def main():
    # Load the configuration file

    conf_file = '../Config/Process Project.json'

    try:
        with open(conf_file, 'r') as file:
            process_project_params_list = json.load(file)
    except FileNotFoundError:
        paint_logger.error(f"The configuration file {conf_file} was not found.")
        sys.exit(1)
    except json.JSONDecodeError:
        paint_logger.error(f"Failed to decode JSON from the configuration file {conf_file}.")
        sys.exit(1)

    process_project_params = process_project_params_list[0]

    conf_file = '../Config/Paint Data Generation.json'
    try:
        with open(conf_file, 'r') as file:
            config = json.load(file)
    except FileNotFoundError:
        paint_logger.error(f"The configuration file {conf_file} was not found.")
        config = []
        sys.exit(1)
    except json.JSONDecodeError:
        paint_logger.error(f"Failed to decode JSON from the configuration file {conf_file}.")
        config = []
        sys.exit(1)

    conf_file = process_project_params['Config File']
    paint_data = process_project_params['Paint Data']
    paint_source = process_project_params['Paint Source']
    data_version = process_project_params['Version']
    r_dest = process_project_params['R Destination']
    time_string = process_project_params['Time String']
    paint_force = process_project_params['Force']

    paint_data = paint_data + ' - v' + data_version
    r_dest = r_dest + ' - v' + data_version

    if time_string == '':
        current_time = datetime.now()
        time_string = current_time.strftime("%Y-%m-%d %H:%M:%S")

    # Main loop to process each configuration based on flags

    nr_to_process = sum(1 for entry in config if entry['flag'])
    main_stamp = time.time()

    paint_logger.info("")
    paint_logger.info("")
    paint_logger.info(f"New Run - {'Debug' if PAINT_DEBUG else 'Production'} mode")
    paint_logger.info("")
    paint_logger.info(f"Started the whole process at: {datetime.now()}")
    paint_logger.info(f"The configuration file is               : {conf_file}")
    paint_logger.info(f"The Paint Source directory is           : {paint_source}")
    paint_logger.info(f"The Paint Data directory is             : {paint_data}")
    paint_logger.info(f"The Version is                          : {data_version}")
    paint_logger.info(f"The R Output directory is               : {r_dest}")
    paint_logger.info(f"The number of projectd to process is    : {nr_to_process}")
    paint_logger.info(f"Paint force is                          : {paint_force}")

    nr_to_process = sum(1 for entry in config if entry['flag'])

    current_process_seq_nr = 0
    error_count = 0

    for entry in config:
        if entry['flag']:
            paint_source_dir = os.path.join(paint_source, entry['probe'])
            paint_data_dir = os.path.join(paint_data, entry['probe'], entry['project_name'])
            r_dest_dir = os.path.join(r_dest, entry['project_name'])
            current_process_seq_nr += 1

            select_parameters = pack_select_parameters(
                min_required_density_ratio=entry['min_required_density_ratio'],
                max_allowable_variability=entry['max_allowable_variability'],
                min_track_duration=get_paint_attribute('Generate Squares', 'Min Track Duration'),
                max_track_duration=get_paint_attribute('Generate Squares', 'Max Track Duration'),
                min_allowable_r_squared=get_paint_attribute('Generate Squares', 'Min Allowable R Squared'),
                neighbour_mode=get_paint_attribute('Generate Squares', 'Neighbour Mode'))

            if not process_json_configuration_block(
                    paint_source_dir=paint_source_dir,
                    project_name=entry['project_name'],
                    project_path=paint_data_dir,
                    r_dest_dir=r_dest_dir,
                    probe=entry['probe'],
                    nr_of_squares_in_row=entry['nr_of_squares'],
                    nr_to_process=nr_to_process,
                    current_process=current_process_seq_nr,
                    select_parameters=select_parameters,
                    min_allowable_r_squared=entry['min_allowable_r_squared'],
                    min_tracks_for_tau=entry['min_tracks_for_tau'],
                    time_string=time_string,
                    paint_force=paint_force):
                error_count += 1

    # Report the time it took in hours, minutes, seconds
    run_time = time.time() - main_stamp
    format_time_nicely(run_time)

    paint_logger.info("")
    paint_logger.info(f"Finished the whole process in: {format_time_nicely(run_time)}")
    paint_logger.info("")

    if error_count > 0:
        paint_logger.error('-' * 80)
        paint_logger.error('-' * 80)
        paint_logger.error(f"Errors occurred in {error_count} of {nr_to_process} directories.")
        paint_logger.error('-' * 80)
        paint_logger.error('-' * 80)

    logger_dir = get_paint_logger_directory()
    shutil.copyfile(os.path.join(logger_dir, 'Process All Projects.log'),
                    os.path.join(logger_dir, f'Process All Projects - v{data_version}.log'))


if __name__ == '__main__':
    main()
