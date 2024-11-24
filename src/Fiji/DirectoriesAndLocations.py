import os
from os import makedirs

# ----------------------------------------------------------------------------------------------------------------------
# Experiment
# ----------------------------------------------------------------------------------------------------------------------
EXPERIMENT_TM = "All Recordings.csv"
EXPERIMENT_INFO = "Experiment Info.csv"


def get_experiment_info_file_path(experiment_directory):
    return os.path.join(experiment_directory, EXPERIMENT_INFO)


def get_experiment_tm_file_path(experiment_directory):
    return os.path.join(experiment_directory, EXPERIMENT_TM)


# ----------------------------------------------------------------------------------------------------------------------
# Tau Plots
# ----------------------------------------------------------------------------------------------------------------------

TAU_PLOTS = "Tau Plots"


def get_tau_plots_dir_path(experiment_directory, image_name):
    return os.path.join(experiment_directory, image_name, TAU_PLOTS)


# ----------------------------------------------------------------------------------------------------------------------
# Miscellanea
# ----------------------------------------------------------------------------------------------------------------------

def create_directories(image_directory, delete_existing=True):
    """
    :param image_directory:
    :param delete_existing:
    :return:
    """

    if not os.path.isdir(image_directory):
        os.makedirs(image_directory)
    else:
        if delete_existing:
            delete_files_in_directory(image_directory)
    return


def _get_paint_configuration_directory(sub_dir):
    conf_dir = os.path.join(os.path.expanduser('~'), 'Paint')
    if not os.path.exists(conf_dir):
        makedirs(os.path.join(conf_dir, sub_dir))
    return conf_dir


def get_paint_logger_directory():
    sub_dir = 'Logger'
    return os.path.join(_get_paint_configuration_directory(sub_dir), sub_dir)


def delete_files_in_directory(directory_path):
    """
    Delete all files in the specified directory.
    Note that only files are deleted, directories are left.

    :param directory_path: The directory to be emptied
    :return:
    """
    try:
        if not os.path.exists(directory_path):
            return
        files = os.listdir(directory_path)
        for file in files:
            file_path = os.path.join(directory_path, file)
            if os.path.isfile(file_path):
                os.remove(file_path)
    except OSError:
        print("Error occurred while deleting files.")  # TODO Add logging


def get_default_image_directory():
    """
    Determine where the root is. We are looking for something like /Users/xxxx/Trackmate Data
    The only thing that can vary is the username.
    If the directory does not exist, just warn and abort
    :return:  the image root directory
    """

    image_directory = os.path.expanduser('~') + os.sep + "Trackmate Data"
    if not os.path.isdir(image_directory):
        makedirs(image_directory)
    else:
        return image_directory
