import os
import csv
from pathlib import Path
import re
import shutil
import pandas as pd
from PIL import Image, ImageTk

from src.Fiji.LoggerConfig import paint_logger

pd.options.mode.copy_on_write = True


def save_experiment_to_file(df_experiment, experiment_file_path):
    df_experiment.to_csv(experiment_file_path, index=False)


def save_squares_to_file(df_squares, square_file_path):
    df_squares.to_csv(square_file_path, index=False)


def read_experiment_file(experiment_file_path: str, only_records_to_process: bool = True) -> pd.DataFrame:
    """
    Create the process table by looking for records that were marked for processing
    :return:
    """

    try:
        df_experiment = pd.read_csv(experiment_file_path, header=0, skiprows=[])
    except IOError:
        return None

    if only_records_to_process:
        df_experiment = df_experiment[df_experiment['Process'].str.lower().isin(['yes', 'y'])]

    df_experiment.set_index('Ext Recording Name', inplace=True, drop=False)
    df_experiment['Experiment Date'] = df_experiment['Experiment Date'].astype(str)

    return df_experiment


def read_experiment_tm_file(experiment_file_path, only_records_to_process=True):
    df_experiment = read_experiment_file(os.path.join(experiment_file_path, 'All Recordings.csv'),
                                         only_records_to_process=only_records_to_process)
    return df_experiment


def correct_all_recordings_column_types(file_path):
    """
    Set the column types for the experiment file
    """

    try:
        df_experiment = pd.read_csv(file_path, header=0, skiprows=[])
        df_experiment['Recording Sequence Nr'] = df_experiment['Recording Sequence Nr'].astype(int)
        df_experiment['Condition Nr'] = df_experiment['Condition Nr'].astype(int)
        df_experiment['Replicate Nr'] = df_experiment['Replicate Nr'].astype(int)
        df_experiment['Experiment Date'] = df_experiment['Experiment Date'].astype(str)
        df_experiment['Threshold'] = df_experiment['Threshold'].astype(int)
        df_experiment['Min Tracks for Tau'] = df_experiment['Min Tracks for Tau'].astype(int)
        df_experiment['Min Allowable R Squared'] = df_experiment['Min Allowable R Squared'].astype(float)
        df_experiment['Nr of Squares in Row'] = df_experiment['Nr of Squares in Row'].astype(int)
        df_experiment.to_csv(file_path, index=False)
    except (ValueError, TypeError):
        return False
    return True


def read_squares_from_file(squares_file_path):
    try:
        df_squares = pd.read_csv(squares_file_path, header=0, skiprows=[])
    except IOError:
        paint_logger.error(f'Read_squares from_file: file {squares_file_path} could not be opened.')
        exit(-1)

    df_squares['Experiment Date'] = df_squares['Experiment Date'].astype(str)

    df_squares.set_index('Unique Key', inplace=True, drop=False)
    return df_squares


def format_time_nicely(seconds):
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    hours = int(hours)
    minutes = int(minutes)
    seconds = int(seconds)

    if hours == 0 and minutes == 0 and seconds == 0:
        return "0 seconds"
    parts = []
    if hours:
        parts.append(f"{hours} hour{'s' if hours > 1 else ''}")
    if minutes:
        parts.append(f"{minutes} minute{'s' if minutes > 1 else ''}")
    if seconds:
        parts.append(f"{seconds} second{'s' if seconds > 1 else ''}")

    return ' and '.join(parts)


def split_probe_valency(row):
    regexp = re.compile(r'(?P<valency>\d) +(?P<structure>[A-Za-z]+)')
    match = regexp.match(row['Probe'])
    if match is not None:
        valency = match.group('valency')
        return int(valency)
    else:
        return 0


def split_probe_structure(row):
    regexp = re.compile(r'(?P<valency>\d) +(?P<structure>[A-Za-z]+)')
    match = regexp.match(row['Probe'])
    if match is not None:
        structure = match.group('structure')
        return structure
    else:
        return ""


def copy_directory(src, dest):
    try:
        shutil.rmtree(dest, ignore_errors=True)
        paint_logger.debug(f"Removed {dest}")
    except FileNotFoundError as e:
        paint_logger.error(f"FileNotFoundError: {e}")
    except PermissionError as e:
        paint_logger.error(f"PermissionError: {e}")
    except OSError as e:
        paint_logger.error(f"OSError: {e}")
    except RecursionError as e:
        paint_logger.error(f"RecursionError: {e}")
    except Exception as e:
        paint_logger.error(f"An unexpected error occurred: {e}")

    try:
        shutil.copytree(src, dest)
        paint_logger.debug(f"Copied {src} to {dest}")
    except FileNotFoundError as e:
        paint_logger.error(f"FileNotFoundError: {e}")
    except FileExistsError as e:
        paint_logger.error(f"FileExistsError: {e}")
    except PermissionError as e:
        paint_logger.error(f"PermissionError: {e}")
    except OSError as e:
        paint_logger.error(f"OSError: {e}")
    except RecursionError as e:
        paint_logger.error(f"RecursionError: {e}")
    except Exception as e:
        paint_logger.error(f"An unexpected error occurred: {e}")


# ToDo there may be an Output dirctory but that should be ignored
# def classify_directory(directory_path):
#     # Define required files and subdirectories for an experiment directory
#     experiment_files = {'All Recordings.csv', 'All Tracks.csv'}
#     experiment_subdirs = {'Brightfield Images', 'TrackMate Images'}
#     mature_experiment_file = 'All Squares.csv'
#
#     # Define required files for a project directory
#     project_files = {'All Recordings.csv', 'All Tracks.csv'}
#     mature_project_file = 'All Squares.csv'
#
#     observations = []
#
#     # Initialize classification variables
#     directory_type = None
#     maturity = 'Immature'
#
#     try:
#         # Check if the directory exists
#         if not os.path.exists(directory_path):
#             paint_logger.error(f"Directory '{directory_path}' does not exist.")
#             return directory_type, maturity
#
#         # Check if the path is a directory
#         if not os.path.isdir(directory_path):
#             paint_logger.error(f"Path '{directory_path}' is not a directory.")
#             return directory_type, maturity
#
#         # Get directory contents
#         contents = set(os.listdir(directory_path))
#
#         # Check if it is an experiment directory
#         if experiment_files.issubset(contents):
#             missing_subdirs = experiment_subdirs - contents
#             if missing_subdirs:
#                 observations.append(
#                     f"Experiment directory '{directory_path}' is missing required subdirectories: {', '.join(missing_subdirs)}")
#             else:
#                 directory_type = 'Experiment'
#                 # Check for maturity
#                 if mature_experiment_file in contents:
#                     maturity = 'Mature'
#                 else:
#                     observations.append(
#                         f"Nor a mature Project: directory '{directory_path}' is missing the file '{mature_experiment_file}' required for maturity.")
#         else:
#             missing_files = experiment_files - contents
#             observations.append(
#                 f"Not an Experiment: directory '{directory_path}' is missing required files: {', '.join(missing_files)}")
#
#         # Check if it is a project directory
#         if directory_type is None:
#             experiment_dirs = [
#                 d for d in os.listdir(directory_path)
#                 if os.path.isdir(os.path.join(directory_path, d))
#             ]
#             experiment_dir_count = 0
#             for sub_dir in experiment_dirs:
#                 sub_dir_path = os.path.join(directory_path, sub_dir)
#                 sub_contents = set(os.listdir(sub_dir_path))
#                 if experiment_files.issubset(sub_contents) and experiment_subdirs.issubset(sub_contents):
#                     experiment_dir_count += 1
#                 else:
#                     observations.append(
#                         f"Not an Experiment: Subdirectory '{sub_dir}' is missing required files or subdirectories")
#
#             if experiment_dir_count > 0:
#                 directory_type = 'Project'
#                 if project_files.issubset(contents) and mature_project_file in contents:
#                     maturity = 'Mature'
#                 else:
#                     observations.append(
#                         f"Not a Project: directory '{directory_path}' is missing files required for project maturity: {', '.join(project_files - contents) or mature_project_file}")
#             else:
#                 observations.append(
#                     f"Not a Project: directory '{directory_path}' does not contain any valid experiment subdirectories.")
#
#     except Exception as e:
#         paint_logger.error(f"An error occurred while classifying the directory: {e}")
#         return directory_type, maturity
#
#     # Return type and maturity
#     if observations:
#         for observation in observations:
#             paint_logger.error(observation)
#
#     return directory_type, maturity





def classify_directory_work(directory_path):
    """
    Classifies a directory as either an experiment or project directory,
    and determines its maturity. Provides feedback if classification fails.

    Args:
        directory_path (str): The path to the directory to classify.

    Returns:
        dict: A dictionary with keys 'type', 'maturity', and 'feedback'.
              Possible 'type' values: 'experiment', 'project', or 'unknown'.
              Possible 'maturity' values: 'mature', 'immature'.
              'feedback' provides information on why classification failed.
    """
    directory = Path(directory_path)

    # Ignore files like .DS_Store
    contents = [item for item in directory.iterdir() if item.name != ".DS_Store"]

    # Initialize feedback
    feedback = []

    # Check for experiment directory
    experiment_files = {"Experiment Info.csv", "All Recordings.csv", "All Tracks.csv"}
    required_dirs = {"Brightfield Images", "TrackMate Images"}
    optional_file = "All Squares.csv"
    output_dir = directory / "Output"

    has_experiment_files = all((directory / file).is_file() for file in experiment_files)
    has_required_dirs = all((directory / dir_name).is_dir() for dir_name in required_dirs)

    if has_experiment_files and has_required_dirs:
        additional_contents = [item for item in contents \
                               if item.name not in experiment_files and \
                                  item.name not in required_dirs and \
                                  item.name != optional_file and \
                                  item != output_dir]
        if additional_contents:
            feedback.append(f"Not an Experiment: directory contains unexpected files or directories: {additional_contents}.")
        if not additional_contents and (not output_dir.exists() or output_dir.is_dir()):
            maturity = "Mature" if (directory / optional_file).is_file() else "Immature"
            return {"type": "Experiment", "maturity": maturity, "feedback": None}
        else:
            feedback.append("Experiment directory contains unexpected files or directories.")
    else:
        if not has_experiment_files:
            file_names = [Path(path).name for path in contents if Path(path).is_file()]
            missing_files = set(experiment_files) - set(file_names)
            feedback.append(f"Not an Experiment: Missing required experiment files: {missing_files}")
        if not has_required_dirs:
            dir_names = [Path(path).name for path in contents if Path(path).is_dir()]
            missing_dirs = set(required_dirs) - set(dir_names)
            feedback.append(f"Not an Experiment: Missing required directories for an experiment: {missing_dirs}")

    # Check for project directory
    experiment_dirs = [item for item in contents if item.is_dir() and classify_directory_work(item)["type"] == "Experiment"]
    project_files = {"All Recordings.csv", "All Tracks.csv", "All Squares.csv"}

    has_project_files = all((directory / file).is_file() for file in project_files)

    if experiment_dirs:
        additional_dirs = [item for item in contents if item.is_dir() and item != output_dir and item not in experiment_dirs]
        additional_files = [item for item in contents if item.is_file() and item.name not in project_files]

        if not additional_dirs and not additional_files and (not output_dir.exists() or output_dir.is_dir()):
            maturity = "Mature" if has_project_files else "Immature"
            return {"type": "Project", "maturity": maturity, "feedback": None}
        else:
            dir_names = [Path(path).name for path in additional_dirs if Path(path).is_dir()]
            feedback.append(f"Not a Project: unexpected files {additional_files} or directories {dir_names}.")
    else:
        feedback.append("Not a Project: No valid experiment directories found for a project.")

    if not has_project_files:
        feedback.append("Not a Project: Missing required project files.")

    # Classify as unknown if criteria are not met
    feedback_message = "; ".join(feedback)
    return {"type": "unknown", "maturity": "immature", "feedback": feedback_message}


def classify_directory(directory_path):
    result = classify_directory_work(directory_path)
    if result['type'] == "unknown":
        if result["feedback"]:
            for line in result["feedback"].split(";"):
                paint_logger.error(line)
        return 'Unknown', ''
    else:
        return result['type'], result['maturity']


def set_application_icon(root):

    icon_file = "../images/paint1.png"
    # For macOS Load the icon using Pillow
    try:
        img = Image.open(icon_file)
        icon = ImageTk.PhotoImage(img)
        root.iconphoto(True, icon)
    except Exception as e:
        print(f"Error loading image: {e}")
        photo = None

    # For Windows
    root.iconbitmap(icon_file)

    return root


def concat_csv_files(output_file, csv_files):
    """
    Concatenate a list of CSV files into a single output file.
    """
    # Open the output file in write mode
    with open(output_file, 'w') as outfile:
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


def set_directory_tree_timestamp(dir_to_change, timestamp=None):
    """
    Set the access and modification timestamps of a directory.

    :param dir_to_change: Path to the directory.
    :param timestamp: Unix timestamp (seconds since epoch) to set for access and modification times.
                      If None, the current time will be used.
    """
    # Check if the provided path is a valid directory
    if not os.path.isdir(dir_to_change):
        paint_logger.error(f"Error: '{dir_to_change}' is not a valid directory.")
        return

    # If no timestamp is provided, use the current time
    if timestamp is None:
        timestamp = time.time()

    try:
        for dir_path, dir_names, filenames in os.walk(dir_to_change):

            # Set timestamp for each file in the directory
            os.utime(dir_to_change, (timestamp, timestamp))
            for dirname in dir_names:
                filepath = os.path.join(dir_path, dirname)
                os.utime(filepath, (timestamp, timestamp))
            for filename in filenames:
                filepath = os.path.join(dir_path, filename)
                os.utime(filepath, (timestamp, timestamp))
        paint_logger.debug(f"Updated timestamps for directory '{dir_to_change}' successfully.")

    except (PermissionError, OSError, FileNotFoundError):
        paint_logger.error(f"Failed to update timestamps for directory '{dir_to_change}'.")
    except PermissionError:
        paint_logger.error(f"Error: Permission denied while setting timestamps for '{dir_to_change}'.")
    except FileNotFoundError:
        paint_logger.error(f"Error: Directory '{dir_to_change}' not found.")
    except Exception as e:
        paint_logger.error(f"An unexpected error occurred: {e}")


# Example Usage: Set timestamps to a specific date
def get_timestamp_from_string(date_str, format_str='%Y-%m-%d %H:%M:%S'):
    """
    Convert a date string into a Unix timestamp.

    :param date_str: The date in string format (e.g., '2023-01-01 12:00:00').
    :param format_str: Format of the input date string (default: '%Y-%m-%d %H:%M:%S').
    :return: Unix timestamp (seconds since epoch).
    """
    try:
        return time.mktime(time.strptime(date_str, format_str))
    except ValueError as e:
        print(f"Error: Invalid date format. {e}")
        return None


class ToolTip:
    def __init__(self, widget, text, wraplength=200):
        self.widget = widget
        self.text = text
        self.wraplength = wraplength  # Set wrap length for the tooltip text
        self.tooltip_window = None

        # Bind the hover events
        self.widget.bind("<Enter>", self.show_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)

    def show_tooltip(self, event=None):
        # Create a small window for the tooltip
        if self.tooltip_window or not self.text:
            return

        x = self.widget.winfo_rootx() + 20  # Tooltip position offset
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 10

        # Create the tooltip window
        self.tooltip_window = tk.Toplevel(self.widget)
        self.tooltip_window.wm_overrideredirect(True)  # Remove window borders
        self.tooltip_window.wm_geometry(f"+{x}+{y}")

        # Add a label with the tooltip text, set the wrap length for text wrapping
        label = tk.Label(
            self.tooltip_window, text=self.text, background="#f0e68c",  # Softer yellow (Khaki)
            relief="solid", borderwidth=1, font=("Arial", 10), wraplength=self.wraplength,
            anchor="w", justify="left"  # Left-align the text
        )
        label.pack(ipadx=5, ipady=2)

    def hide_tooltip(self, event=None):
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None

    def hide_tooltip(self, event=None):
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None
