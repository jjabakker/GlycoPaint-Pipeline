
import os
import pandas as pd
from tkinter import *
from tkinter import ttk, filedialog, messagebox
from src.Application.Support.Check_integrity_Of_Files import check_files_integrity_failed

from src.Application.Support.General_Support_Functions import (
    classify_directory,
    ToolTip)
from src.Fiji.LoggerConfig import (
    paint_logger,
    paint_logger_change_file_handler_name,
    paint_logger_file_name_assigned)
from src.Fiji.NewPaintConfig import (
    get_paint_attribute_with_default)

if not paint_logger_file_name_assigned:
    paint_logger_change_file_handler_name('Compile Output.log')


# -----------------------------------------------------------------------------------------------------------------------
# -----------------------------------------------------------------------------------------------------------------------
# The routine that does the work
# -----------------------------------------------------------------------------------------------------------------------
# -----------------------------------------------------------------------------------------------------------------------

def check_integrity_experiment(
        experiment_dir_path: str,
        verbose: bool = True):

    paint_logger.info("")
    paint_logger.info(f"Checking Integrity for {experiment_dir_path}")

    all_recordings_path = os.path.join(experiment_dir_path, 'All Recordings.csv')
    if not os.path.exists(all_recordings_path):
        df_all_squares = None
    else:
        df_all_recordings = pd.read_csv(all_recordings_path,
                                    dtype={'Max Allowable Variability': float,
                                           'Min Required Density Ratio': float})

    all_squares_path = os.path.join(experiment_dir_path, 'All Squares.csv')
    if not os.path.exists(all_squares_path):
        df_all_squares = None
    else:
        df_all_squares = pd.read_csv(all_squares_path)

    experiment_info_path = os.path.join(experiment_dir_path, 'Experiment Info.csv')
    if not os.path.exists(experiment_info_path):
        df_experiment_info = None
    else:
        df_experiment_info = pd.read_csv(experiment_info_path)

    if not check_files_integrity_failed(df_all_recordings, df_experiment_info, df_all_squares):
        paint_logger.info(f"Experiment {experiment_dir_path} is ok")


def check_integrity_project(
        project_dir: str,
        verbose: bool = True):

    paint_logger.info("")
    paint_logger.info(f"Checking Integrity for {project_dir}")

    experiment_dirs = os.listdir(project_dir)
    experiment_dirs.sort()

    experiments = []

    nr_processed = 0
    nr_skipped = 0
    nr_error = 0

    # Collect the files to be appended
    for experiment_name in experiment_dirs:
        # Reset the error flag
        error = False

        # Ignore files that are marked .' in the beginning
        if experiment_name.startswith('.'):
            continue

        # Ignore files that are marked with a '-' or '.' in the beginning
        if experiment_name.startswith('-') or experiment_name.startswith('.'):
            nr_skipped += 1
            continue

        # Ignore Output directory
        if experiment_name == 'Output':
            continue

        experiment_dir_path = os.path.join(project_dir, experiment_name)
        if not os.path.isdir(experiment_dir_path):
            continue

        all_recordings_path = os.path.join(experiment_dir_path, 'All Recordings.csv')
        if not os.path.exists(all_recordings_path):
            df_all_squares = None
        else:
            df_all_recordings = pd.read_csv(all_recordings_path,
                                        dtype={'Max Allowable Variability': float,
                                               'Min Required Density Ratio': float})

        all_squares_path = os.path.join(experiment_dir_path, 'All Squares.csv')
        if not os.path.exists(all_squares_path):
            df_all_squares = None
        else:
            df_all_squares = pd.read_csv(all_squares_path)

        experiment_info_path = os.path.join(experiment_dir_path, 'Experiment Info.csv')
        if not os.path.exists(experiment_info_path):
            df_experiment_info = None
        else:
            df_experiment_info = pd.read_csv(experiment_info_path)

        nr_processed += 1
        if not check_files_integrity_failed(df_all_recordings, df_experiment_info, df_all_squares):
            paint_logger.info(f"Experiment {experiment_name} is ok")
        else:
            nr_error += 1

    # Report on experiments processed
    if verbose:
        for experiment in experiments:
            paint_logger.info(f"Processed experiment: {experiment}")

        paint_logger.info(f"Processed {nr_processed} experiments, skipped {nr_skipped} experiments.")


class IntegrityDialog:

    def __init__(self, _root):
        self.root = _root

        self.root.title('Check Project or Experiment')
        self.project_directory = get_paint_attribute_with_default('User Directories', 'Project Directory', '')

        content = ttk.Frame(self.root)
        frame_buttons = ttk.Frame(content, borderwidth=5, relief='ridge')
        frame_directory = ttk.Frame(content, borderwidth=5, relief='ridge')

        #  Do the lay-out
        content.grid(column=0, row=0)
        frame_directory.grid(column=0, row=1, padx=5, pady=5)
        frame_buttons.grid(column=0, row=2, padx=5, pady=5)

        # Fill the button frame
        btn_compile = ttk.Button(frame_buttons, text='Check Integrity', command=self.on_check_pressed)
        btn_exit = ttk.Button(frame_buttons, text='Exit', command=self.on_exit_pressed)
        btn_compile.grid(column=0, row=1)
        btn_exit.grid(column=0, row=2)

        # Fill the directory frame
        btn_project_dir = ttk.Button(frame_directory, text='Directory', width=15, command=self.change_root_dir)
        self.lbl_project_dir = ttk.Label(frame_directory, text=self.project_directory, width=80)

        tooltip = "Specify a Project directory here, i.e. a directory that holds Experiment directories."
        ToolTip(btn_project_dir, tooltip, wraplength=400)

        btn_project_dir.grid(column=0, row=0, padx=10, pady=5)
        self.lbl_project_dir.grid(column=1, row=0, padx=20, pady=5)

    def change_root_dir(self) -> None:
        self.project_directory = filedialog.askdirectory(initialdir=self.project_directory)
        if len(self.project_directory) != 0:
            self.lbl_project_dir.config(text=self.project_directory)

    def on_check_pressed(self) -> None:

        # Check if the directory exists and has not been deleted since it lst was chosen
        if not os.path.exists(self.project_directory):
            messagebox.showwarning(title='Warning', message='The selected directory does not exist.')
            return

        # Determine if it indeed is a project directory
        dir_type, _ = classify_directory(self.project_directory)
        if dir_type in ['Project', 'Experiment']:
            paint_logger.info(f"Checking integrity for {dir_type}")
            paint_logger.info(f"Checking for empty Adjuvant column")
            paint_logger.info(f"Checking for non numerical Concentration")
            paint_logger.info(f"Checking for non numerical Threshold")
            paint_logger.info(f"Checking for Inconsistent Experiment Name and Experiment Date")



        if dir_type == 'Project':  # Project directory, so proceed
            check_integrity_project(project_dir=self.project_directory, verbose=True)
            self.root.destroy()
        elif dir_type == 'Experiment':  # Experiment directory, so warn
            check_integrity_experiment(self.project_directory, verbose=True)
            self.root.destroy()
        else:  # Just any directory, so warn
            msg = "The selected directory does not seem to be a project directory, nor an experiment directory."
            paint_logger.error(msg)
            messagebox.showwarning(title='Warning', message=msg)

    def on_exit_pressed(self) -> None:
        self.root.destroy()


if __name__ == "__main__":
    root = Tk()
    root.eval('tk::PlaceWindow . center')
    IntegrityDialog(root)
    root.mainloop()
