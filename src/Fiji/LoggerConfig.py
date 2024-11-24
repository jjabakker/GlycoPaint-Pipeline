import logging
import os
from os import path

DEBUG = logging.DEBUG
INFO = logging.INFO
WARNING = logging.WARNING
ERROR = logging.ERROR
CRITICAL = logging.CRITICAL

paint_logger_file_name_assigned = False

# ----------------------------------------------------------
# Set up the logging
# ----------------------------------------------------------

paint_logger = logging.getLogger('paint')
paint_logger.setLevel(logging.DEBUG)  # Logs everything from DEBUG level and above
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%H:%M:%S')

# ----------------------------------------------------------
# Set up the console handler
# ----------------------------------------------------------

console_handler = logging.StreamHandler()  # Logs to the console (standard output)
console_handler.setLevel(logging.DEBUG)  # All logs at DEBUG level or higher go to the console
console_handler.setFormatter(formatter)

# ----------------------------------------------------------
# Set up the file handler
# ----------------------------------------------------------

# file_handler = logging.FileHandler(os.path.join(get_paint_logger_directory(), 'paint.log'), mode='w')  # Logs to a file
file_handler = logging.FileHandler(os.path.join(os.path.expanduser('~'), 'Paint', 'Logger', 'paint.log'),
                                   mode='w')  # Logs to a file   #ToDo
file_handler.setLevel(logging.INFO)  # All logs at INFO level or higher go to the console
file_handler.setFormatter(formatter)

# ----------------------------------------------------------
# Add the handlers to the logger
# ----------------------------------------------------------

paint_logger.addHandler(console_handler)
paint_logger.addHandler(file_handler)


# ----------------------------------------------------------
# Functions that can be called from the application
# ----------------------------------------------------------

# Get the directory where the log files will be stored
def get_paint_logger_directory():
    sub_dir = 'Logger'
    conf_dir = os.path.join(os.path.expanduser('~'), 'Paint')
    if not os.path.exists(os.path.join(conf_dir, sub_dir)):
        os.makedirs(os.path.join(conf_dir, sub_dir))
    return os.path.join(conf_dir, sub_dir)


# Change the log level of the file logger
def paint_logger_file_handle_set_level(level):
    global file_handler

    if level not in (logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR, logging.CRITICAL):
        raise ValueError("Invalid level: {}".format(level))
    else:
        file_handler.setLevel(level)


# Change the log level of the console logger
def paint_logger_console_handle_set_level(level):
    global console_handler

    if level not in (logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR, logging.CRITICAL):
        raise ValueError("Invalid level: {}.format(level)")
    else:
        console_handler.setLevel(level)


# Change the file name of the file logger
def paint_logger_change_file_handler_name(file_name):
    global file_handler
    global paint_logger_file_name_assigned

    paint_logger.removeHandler(file_handler)

    file_handler = logging.FileHandler(path.join(get_paint_logger_directory(), file_name), mode='w')  # Logs to a file
    file_handler.setLevel(logging.INFO)  # All logs at INFO level or higher go to the console
    file_handler.setFormatter(formatter)

    paint_logger.addHandler(file_handler)
    paint_logger_file_name_assigned = True
