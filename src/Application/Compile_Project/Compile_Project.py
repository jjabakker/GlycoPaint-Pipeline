"""
This function takes as input the directory under which the various experiments are held.
It will create an Output directory with three files: All Squares, All Images, and Images Summary.
"""
import os
import sys
import pandas as pd
from tkinter import *
from tkinter import ttk, filedialog, messagebox

from src.Application.Support.General_Support_Functions import (
    correct_all_recordings_column_types,
    classify_directory,
    concat_csv_files,
    concat_squares_files,
    ToolTip)
from src.Fiji.LoggerConfig import (
    paint_logger,
    paint_logger_change_file_handler_name,
    paint_logger_file_name_assigned)
from src.Fiji.NewPaintConfig import (
    update_paint_attribute,
    get_paint_attribute_with_default)

if not paint_logger_file_name_assigned:
    paint_logger_change_file_handler_name('Compile Output.log')


# -----------------------------------------------------------------------------------------------------------------------
# -----------------------------------------------------------------------------------------------------------------------
# The routine that does the work
# -----------------------------------------------------------------------------------------------------------------------
# -----------------------------------------------------------------------------------------------------------------------

def compile_project_output(
        project_dir: str,
        verbose: bool = True):
    paint_logger.info("")
    paint_logger.info(f"Compiling 'All Recordings' and 'All Squares' for {project_dir}")

    experiment_dirs = os.listdir(project_dir)
    experiment_dirs.sort()

    all_recordings = []
    all_tracks = []
    all_squares = []
    experiments = []

    nr_processed = 0
    nr_skipped = 0
    nr_error = 0

    # Collect the files to be appended
    for experiment_name in experiment_dirs:
        # Reset the error flag
        error = False

        # Ignore files that are marked with a '-' in the beginning
        if experiment_name.startswith('-'):
            nr_skipped += 1
            continue

        # Ignore Output directory
        if experiment_name == 'Output':
            continue

        experiment_dir_path = os.path.join(project_dir, experiment_name)
        if not os.path.isdir(experiment_dir_path):
            continue

        tracks_file = os.path.join(experiment_dir_path, 'All Tracks.csv')
        if not os.path.exists(tracks_file):
            paint_logger.info(f"Tracks file does not exist in {os.path.basename(experiment_dir_path)}. You may need to (re)run TrackMate.")
            error =True
        else:
            squares_file = os.path.join(experiment_dir_path, 'All Squares.csv')
            if not os.path.exists(squares_file):
                paint_logger.info(f"Squares file does not exist in : {os.path.basename(experiment_dir_path)}. You need to (re)run Generate Squares.")
                error = True

        recordings_file = os.path.join(experiment_dir_path, 'All Recordings.csv')
        if not os.path.exists(recordings_file):
            paint_logger.error(f"Recordings file does not exist: {recordings_file}. You need to (re)run TrackMate.")
            error= True

        if not error:
            experiments.append(experiment_name)
            all_tracks.append(tracks_file)
            all_squares.append(squares_file)
            all_recordings.append(recordings_file)
            nr_processed += 1
        else:
            nr_error += 1

    # Report on experiments skipped
    paint_logger.info(f"Processing {nr_processed} experiments, skipping {nr_skipped} experiments.")
    if nr_error > 0:
        paint_logger.info(f"Warnings occurred for {nr_error} experiments.")

    # Report on experiments processed
    if verbose:
        for experiment in experiments:
            paint_logger.info(f"Processed experiment: {experiment}")

    # Concatenate all the files
    concat_csv_files(os.path.join(project_dir, 'All Recordings.csv'), all_recordings)
    concat_squares_files(os.path.join(project_dir, 'All Squares.csv'), all_squares)
    concat_csv_files(os.path.join(project_dir, 'All Tracks.csv'), all_tracks)

    # Check for duplicates in the All Recordings file
    df_experiment = pd.read_csv(os.path.join(project_dir, 'All Recordings.csv'),
                                dtype={'Max Allowable Variability': float,
                                       'Min Required Density Ratio': float})
    if len(df_experiment)  != len(df_experiment['Recording Name'].unique()):
        paint_logger.error("Duplicate entries found in All Recordings file.")
        duplicate_names = set(df_experiment[df_experiment.duplicated(subset='Ext Recording Name', keep=False)]['Ext Recording Name'])
        duplicate_list = sorted(duplicate_names)
        paint_logger.error(f"Duplicate Recording Names: {duplicate_list}")
        sys.exit(0)


    correct_all_recordings_column_types(os.path.join(project_dir, 'All Recordings.csv'))
    paint_logger.info(f"Processed {nr_processed} experiments, skipped {nr_skipped} experiments.")



class CompileDialog:

    def __init__(self, _root):
        self.root = _root

        self.root.title('Compile Project')
        self.project_directory = get_paint_attribute_with_default('User Directories', 'Project Directory', '')

        content = ttk.Frame(self.root)
        frame_buttons = ttk.Frame(content, borderwidth=5, relief='ridge')
        frame_directory = ttk.Frame(content, borderwidth=5, relief='ridge')

        #  Do the lay-out
        content.grid(column=0, row=0)
        frame_directory.grid(column=0, row=1, padx=5, pady=5)
        frame_buttons.grid(column=0, row=2, padx=5, pady=5)

        # Fill the button frame
        btn_compile = ttk.Button(frame_buttons, text='Compile', command=self.on_compile_pressed)
        btn_exit = ttk.Button(frame_buttons, text='Exit', command=self.on_exit_pressed)
        btn_compile.grid(column=0, row=1)
        btn_exit.grid(column=0, row=2)

        # Fill the directory frame
        btn_project_dir = ttk.Button(frame_directory, text='Project Directory', width=15, command=self.change_root_dir)
        self.lbl_project_dir = ttk.Label(frame_directory, text=self.project_directory, width=80)

        tooltip = "Specify a Project directory here, i.e. a directory that holds Experiment directories."
        ToolTip(btn_project_dir, tooltip, wraplength=400)

        btn_project_dir.grid(column=0, row=0, padx=10, pady=5)
        self.lbl_project_dir.grid(column=1, row=0, padx=20, pady=5)

    def change_root_dir(self) -> None:
        self.project_directory = filedialog.askdirectory(initialdir=self.project_directory)
        if len(self.project_directory) != 0:
            self.lbl_project_dir.config(text=self.project_directory)
        dir_type, _ = classify_directory(self.project_directory)
        if dir_type == 'Project':
            update_paint_attribute('User Directories', 'Project Directory', self.project_directory)
        else:
            messagebox.showwarning(
                title='Warning',
                message='The selected directory does not seem to be a project directory.')

    def on_compile_pressed(self) -> None:

        # Check if the directory exists and has not been deleted since it lst was chosen
        if not os.path.exists(self.project_directory):
            messagebox.showwarning(title='Warning', message='The selected directory does not exist.')
            return

        # Determine if it indeed is a project directory
        dir_type, _ = classify_directory(self.project_directory)
        if dir_type == 'Project':  # Project directory, so proceed
            compile_project_output(project_dir=self.project_directory, verbose=True)
            self.root.destroy()
        elif dir_type == 'Experiment':  # Experiment directory, so warn
            msg = "The selected directory does not seem to be a project directory, but an experiment directory."
            paint_logger.error(msg)
            messagebox.showwarning(title='Warning', message=msg)
        else:  # Just any directory, so warn
            msg = "The selected directory does not seem to be a project directory, nor an experiment directory."
            paint_logger.error(msg)
            messagebox.showwarning(title='Warning', message=msg)

    def on_exit_pressed(self) -> None:
        self.root.destroy()


if __name__ == "__main__":
    root = Tk()
    root.eval('tk::PlaceWindow . center')
    CompileDialog(root)
    root.mainloop()
