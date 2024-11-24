import logging
import os
from tkinter import *
from tkinter import ttk, filedialog, messagebox

import pandas as pd

from src.Application.Utilities.General_Support_Functions import (
    read_experiment_file,
    classify_directory
)
from src.Fiji.PaintConfig import (
    get_paint_attribute,
    update_paint_attribute)

# -------------------------------------------------------------------------------------
# Configure logging
# -------------------------------------------------------------------------------------
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def inspect_experiment_squares_files(root_dir):
    """
    Inspects experiments files in the given root directory and generates an output summary.

    :param root_dir: Directory containing experiment subdirectories
    """
    df_all_images = pd.DataFrame()  # Create an empty DataFrame to store results

    # Check if the root directory exists
    if not os.path.isdir(root_dir):
        logging.error(f"Root directory '{root_dir}' does not exist.")
        return

    # Get the list of experiment directories
    experiment_dir_names = sorted(os.listdir(root_dir))

    for experiment_dir_name in experiment_dir_names:
        paint_dir_path = os.path.join(root_dir, experiment_dir_name)

        if not os.path.isdir(paint_dir_path):  # If it's not a directory, skip it
            continue
        if 'Output' in experiment_dir_name:  # Skip the output directory
            continue
        if experiment_dir_name.startswith('-'):  # Skip directories marked with '-'
            continue

        logging.info(f'Inspecting directory: {paint_dir_path}')

        # Read the experiments file in the directory
        experiment_file_name = os.path.join(paint_dir_path, 'All Recordings.csv')

        df_experiment = read_experiment_file(experiment_file_name, only_records_to_process=False)

        if df_experiment is None:
            logging.error(f"Experiment file '{experiment_file_name}' does not exist. Skipping directory.")
            continue

        # Concatenate the experiments DataFrame with the main DataFrame
        df_all_images = pd.concat([df_all_images, df_experiment])

    # ------------------------------------
    # Save the output file
    # ------------------------------------

    # Save the concatenated DataFrame to Excel
    output_file = os.path.join(root_dir, 'Images to Process.csv')
    try:
        df_all_images.to_csv(output_file, index=False)
        logging.info(f"Output file saved at: {output_file}")
    except Exception as e:
        logging.error(f"Failed to save output file '{output_file}': {e}")


class InspectDialog:
    """
    A class for handling the user interface to inspect experiment files.
    """

    def __init__(self, _root):
        self.root = _root
        self.root.title('Inspect Experiments Files')
        self.project_directory = get_paint_attribute('User Directories', 'Project Directory')

        # Set up the UI layout
        self.root.geometry("800x140")
        content = ttk.Frame(self.root)

        # Configure content frame to take full width
        content.grid(column=0, row=0, sticky="nsew")
        self.root.grid_columnconfigure(0, weight=1)

        frame_buttons = ttk.Frame(content, borderwidth=5, relief='ridge')
        frame_directory = ttk.Frame(content, borderwidth=5, relief='ridge')

        # Layout configuration
        frame_directory.grid(column=0, row=1, padx=5, pady=5, sticky="ew")
        frame_buttons.grid(column=0, row=2, padx=5, pady=5)

        # Configure the column inside frame_directory to expand
        frame_directory.grid_columnconfigure(1, weight=1)

        # Fill the button frame
        btn_process = ttk.Button(frame_buttons, text='Process', command=self.process)
        btn_exit = ttk.Button(frame_buttons, text='Exit', command=self.exit_dialog)
        btn_process.grid(column=0, row=1)
        btn_exit.grid(column=0, row=2)

        # Fill the directory frame
        btn_root_dir = ttk.Button(frame_directory, text='Project Directory', width=15, command=self.change_root_dir)
        self.lbl_root_dir = ttk.Label(frame_directory, text=self.project_directory, width=60)

        btn_root_dir.grid(column=0, row=0, padx=10, pady=5)
        self.lbl_root_dir.grid(column=1, row=0, padx=20, pady=5, sticky="ew")

    def change_root_dir(self):
        """
        Allows the user to select a new root directory.
        """
        self.project_directory = filedialog.askdirectory(initialdir=self.project_directory)
        if self.project_directory:
            update_paint_attribute('User Directories', 'Project Directory', self.project_directory)
            self.lbl_root_dir.config(text=self.project_directory)

    def process(self):
        """
        Starts the Experiments file inspection process.
        """

        dir_type, _ = classify_directory(self.project_directory)
        if dir_type == 'Project':
            inspect_experiment_squares_files(root_dir=self.project_directory)
            root.destroy()
        elif dir_type == 'Experiment':
            msg = "The selected directory does not seem to be a project directory, but an experiment directory"
            messagebox.showwarning(title='Warning', message=msg)
        else:
            msg = "The selected directory does not seem to be a project directory, nor an experiment directory"
            messagebox.showwarning(title='Warning', message=msg)

    def exit_dialog(self):
        """
        Closes the application.
        """
        root.destroy()


if __name__ == '__main__':
    root = Tk()
    root.eval('tk::PlaceWindow . center')
    InspectDialog(root)
    root.mainloop()
