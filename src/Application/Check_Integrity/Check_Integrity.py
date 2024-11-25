import os
from logging import error

import pandas as pd
from fontTools.misc.roundTools import otRound
from matplotlib.projections import projection_registry

from src.Fiji.LoggerConfig import paint_logger

def check_integrity_project(project_path):

    expected_files = {'All Recordings.csv', 'All Tracks.csv', 'All Squares.csv'}

    # Check directories
    dirs = [entry for entry in os.listdir(project_path) if os.path.isdir(os.path.join(project_path, entry))]
    files = [
        entry for entry in os.listdir(project_path)
        if os.path.isfile(os.path.join(project_path, entry)) and not entry.startswith('.')
    ]

    paint_logger.info("")
    paint_logger.info("-" * 80)
    paint_logger.info(f"Checking integrity of project level files")
    paint_logger.info("-" * 80)

    # Check files
    error = False
    if set(expected_files) - set(files):
        paint_logger.error(
            f"Project directory '{project_path}' is missing files: {set(expected_files) - set(files)}")
        error = True

    if set(files) - set(expected_files):
        paint_logger.error(
            f"Experiment directory '{project_path}' has excess files: {set(files) - set(expected_files)}")
        error = True

    if 'All Recordings.csv' in files:
        error = error or check_all_recordings_file(os.path.join(project_path, 'All Recordings.csv'))

    if 'All Tracks.csv' in files:
        error = error or check_all_tracks_file(os.path.join(project_path, 'All Tracks.csv'))

    if 'All Squares.csv' in files:
        error = error or check_all_squares_file(os.path.join(project_path, 'All Squares.csv'))

    if not error:
        paint_logger.info("")
        paint_logger.info("Project level files are complete and consistent.")

    for dir in dirs:
        paint_logger.info("")
        paint_logger.info("-" * 80)
        paint_logger.info(f"Checking integrity of experiment '{dir}'")
        paint_logger.info("-" * 80)
        check_integrity_experiment(os.path.join(project_path, dir))
        paint_logger.info("")


def check_integrity_experiment(experiment_path):

    expected_dirs = {'Brightfield Images', 'TrackMate Images'}
    expected_files = {'Experiment Info.csv', 'All Recordings.csv', 'All Tracks.csv', 'All Squares.csv'}
    error = False

    if not (os.path.isdir(experiment_path)):
        paint_logger.error(f"Experiment directory '{experiment_path}' does not exist.")
        return False

    # Check directories
    dirs = [entry for entry in os.listdir(experiment_path) if os.path.isdir(os.path.join(experiment_path, entry))]
    files = [
        entry for entry in os.listdir(experiment_path)
        if os.path.isfile(os.path.join(experiment_path, entry)) and not entry.startswith('.')
    ]

    if set(expected_dirs) - set(dirs):
        paint_logger.error(
            f"Experiment directory '{experiment_path}' is missing directories: {set(expected_dirs) - set(dirs)}")
        error = True

    if set(dirs) - set(expected_dirs):
        paint_logger.error(
            f"Experiment directory '{experiment_path}' has extra directories: {set(dirs) - expected_dirs}")
        error = True

    # Check files
    if set(expected_files) - set(files):
        paint_logger.error(
            f"Experiment directory '{experiment_path}' is missing files: {set(expected_files) - set(files)}")
        error = True

    if set(files) - set(expected_files):
        paint_logger.error(
            f"Experiment directory '{experiment_path}' has extra files: {set(files) - set(expected_files)}")
        error = True

    paint_logger.info("")

    if 'Experiment Info.csv' in files:
        error = error or check_experiment_info_file(os.path.join(experiment_path, 'Experiment Info.csv'))

    if 'All Recordings.csv' in files:
        error = error or check_all_recordings_file(os.path.join(experiment_path, 'All Recordings.csv'))

    if 'All Tracks.csv' in files:
        error = error or check_all_tracks_file(os.path.join(experiment_path, 'All Tracks.csv'))

    if 'All Squares.csv' in files:
        error = error or check_all_squares_file(os.path.join(experiment_path, 'All Squares.csv'))

    if not error:
        paint_logger.info("Experiment level files are complete and consistent.")


def check_experiment_info_file(exp_info_file):

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
        }

    df = pd.read_csv(exp_info_file)
    error = False

    actual_columns = df.columns

    if set(expected_columns) - set(actual_columns):
        paint_logger.error(
            f"Experiment Info file '{exp_info_file}' is missing columns: {set(expected_columns) - set(actual_columns)}")
        error = True

    if set(actual_columns) - set(expected_columns):
        paint_logger.error(
            f"Experiment Info file '{exp_info_file}' has unexpected columns: {set(actual_columns) - set(expected_columns)}")
        error = True

    return error


def check_all_recordings_file(file):
    expected_columns_1 = [
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
        'Nr Tracks',
        'Run Time',
        'Ext Recording Name',
        'Recording Size',
        'Time Stamp'
    ]

    expected_columns_2 = [
        'Min Tracks for Tau',
        'Min Allowable R Squared',
        'Nr of Squares in Row',
        'Max Allowable Variability',
        'Min Required Density Ratio',
        'Exclude',
        'Neighbour Mode',
        'Tau',
        'Density',
        'R Squared'
    ]

    df = pd.read_csv(file)
    error = False

    actual_columns = df.columns

    phase_1_incomplete = set(expected_columns_1) - set(actual_columns)
    if phase_1_incomplete:
        paint_logger.error(f"All Recordings file '{file}' is missing columns for Phase 1: {phase_1_incomplete}")
        error = True

    phase_2_incomplete = set(expected_columns_1 + expected_columns_2) - set(actual_columns)
    if phase_2_incomplete:
        paint_logger.error(f"All Recordings file '{file}' is missing columns for Phase 2: {phase_2_incomplete}")
        paint_logger.error(f"Consider (re)running Generate Squares.")
        error = True

    excess_columns = set(actual_columns) - set(expected_columns_1) - set(expected_columns_2)
    if excess_columns :
        paint_logger.error(f"All Recordings file '{file}' has excess columns: {excess_columns}")
        error = True

    return error

def check_all_squares_file(file):
    expected_columns = {
        'Unique Key',
        'Recording Sequence Nr',
        'Ext Recording Name',
        'Experiment Name',
        'Experiment Date',
        'Condition Nr',
        'Replicate Nr',
        'Square Nr',
        'Probe',
        'Probe Type',
        'Cell Type',
        'Adjuvant',
        'Concentration',
        'Threshold',
        'Row Nr',
        'Col Nr',
        'Label Nr',
        'Cell Id',
        'Nr Spots',
        'Nr Tracks',
        'X0',
        'Y0',
        'X1',
        'Y1',
        'Selected',
        'Variability',
        'Density',
        'Density Ratio',
        'Tau',
        'R Squared',
        'Diffusion Coefficient',
        'Average Long Track Duration',
        'Max Track Duration',
        'Total Track Duration'
    }

    df = pd.read_csv(file)
    error = False

    actual_columns = df.columns

    if set(expected_columns) - set(actual_columns):
        paint_logger.error(
            f"All Squares file '{file}' is missing columns: {set(expected_columns) - set(actual_columns)}")
        error = True

    if set(actual_columns) - set(expected_columns):
        paint_logger.error(
            f"All Squares file '{file}' has excess columns: {set(actual_columns) - set(expected_columns)}")
        error = True

    return error

def check_all_tracks_file(file):
    expected_columns_1 = {
        'Unique Key',
        'Ext Recording Name',
        'Track Label',
        'Nr Spots',
        'Track Duration',
        'Track X Location',
        'Track Y Location',
        'Diffusion Coefficient'
    }

    expected_columns_2 = {
        'Square Nr',
        'Label Nr'
    }

    df = pd.read_csv(file)
    error = False

    actual_columns = df.columns

    if set(expected_columns_1) - set(actual_columns):
        paint_logger.error(
            f"All Tracks file '{file}' is missing columns: {set(expected_columns_1) - set(actual_columns)}")
        error = True

    if set(actual_columns) - set(expected_columns_1)  != set(expected_columns_2):
        paint_logger.error(
            f"All Tracks file '{file}' has excess columns: {set(actual_columns) - set(expected_columns_1)}")
        error = True

    return error


if __name__ == '__main__':
    # experiment_path = '/Users/hans/Paint Demo Set/Paint Demo/240104'
    # check_integrity_experiment(experiment_path)
    #
    # experiment_path = '/Users/hans/Paint Demo Set/Paint Demo/240116'
    # check_integrity_experiment(experiment_path)

    # experiment_path = '/Users/hans/Paint Data - v24/New Probes/Paint New Probes - 20 Squares/240812'
    # check_integrity_experiment(experiment_path)

    project_path = '/Users/hans/Paint Demo Set/Paint Demo'
    check_integrity_project(project_path)