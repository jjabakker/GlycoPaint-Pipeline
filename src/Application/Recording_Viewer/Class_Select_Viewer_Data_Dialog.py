import os
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk

from src.Application.Recording_Viewer.Recording_Viewer_Support_Functions import (
    only_one_nr_of_squares_in_row,
    nr_recordings)
from src.Application.Utilities.General_Support_Functions import (
    classify_directory,
)
from src.Application.Utilities.ToolTips import ToolTip
from src.Fiji.LoggerConfig import paint_logger
from src.Fiji.PaintConfig import (
    get_paint_attribute,
    update_paint_attribute)
from src.Application.Compile_Project.Compile_Project import compile_project_output


class SelectViewerDataDialog:

    def __init__(self, parent) -> None:
        # Create a Toplevel window for the dialog
        self.dialog = tk.Toplevel(parent)
        self.parent = parent
        self.proceed = False

        self.dialog.title('Select a Project or Experiment Directory')
        self.experiment_directory = get_paint_attribute('User Directories', 'Experiment Directory')
        self.project_directory = get_paint_attribute('User Directories', 'Project Directory')
        self.level = get_paint_attribute('User Directories', 'Level')

        self.mode = None

        # Main content frame
        content = ttk.Frame(self.dialog)  # Attach to self.dialog
        content.grid(column=0, row=0)

        # Layout
        frame_buttons = ttk.Frame(content, borderwidth=5, relief='ridge')
        frame_directory = ttk.Frame(content, borderwidth=5, relief='ridge')

        self.setup_frame_directory(frame_directory)
        self.setup_frame_buttons(frame_buttons)

        frame_directory.grid(column=0, row=1, padx=5, pady=5)
        frame_buttons.grid(column=0, row=2, padx=5, pady=5)

        # Make the dialog modal
        self.dialog.transient(parent)  # Link it to the main root window
        # self.dialog.grab_set()           # Grab all input focus   # ToDo not sure why this would be needed
        parent.wait_window(self.dialog)  # Wait until the dialog is closed

    def setup_frame_buttons(self, frame_buttons):
        btn_process = ttk.Button(frame_buttons, text='View', command=self.on_view)
        btn_exit = ttk.Button(frame_buttons, text='Exit', command=self.on_exit)

        btn_process.grid(column=0, row=1)
        btn_exit.grid(column=0, row=2)

    def setup_frame_directory(self, frame_directory):
        btn_root_dir = ttk.Button(frame_directory, text='Paint Directory', width=15, command=self.on_change_dir)
        self.lbl_experiment_dir = ttk.Label(frame_directory, text=self.experiment_directory, width=80)

        tooltip = "Select the directory where the Paint project or experiment is located. This can be a Project or Experiment directory."
        ToolTip(btn_root_dir, tooltip, wraplength=400)

        btn_root_dir.grid(column=1, row=0, padx=(5, 5), pady=5)
        self.lbl_experiment_dir.grid(column=2, row=0, padx=5, pady=5)

    def on_change_dir(self) -> None:
        self.directory = filedialog.askdirectory(initialdir=self.experiment_directory)
        if self.directory:
            self.lbl_experiment_dir.config(text=self.directory)
            if classify_directory(self.directory) == 'Project':
                update_paint_attribute('User Directories', 'Level', self.level)
                update_paint_attribute('User Directories', 'Project Directory', self.directory)
            else:
                update_paint_attribute('User Directories', 'Level', self.level)
                update_paint_attribute('User Directories', 'Experiment Directory', self.directory)

    def on_view(self) -> None:
        self.directory = self.lbl_experiment_dir.cget('text')

        if not os.path.isdir(self.directory):
            paint_logger.error("The selected directory does not exist")
            messagebox.showwarning(title='Warning', message="The selected directory does not exist")
            return

        type, maturity = classify_directory(self.directory)
        if type is None:
            paint_logger.error("The selected directory does not seem to be a project or experiment directory")
            messagebox.showwarning(
                title='Warning',
                message="The selected directory does not seem to be a project or experiment directory")
        elif type == 'Experiment':
            if maturity == 'Mature':
                self.mode = type
                self.proceed = True
                self.dialog.destroy()
            else:
                msg = "The selected directory appears to be an Experiment directory but is missing files"
                paint_logger.error(msg)
                messagebox.showwarning(title='Warning', message=msg)
        elif type == 'Project':
            if maturity == 'Mature':
                # If it is a project directory, check if there are no newer experiments, i.e., when you have forgotten to run Compile Project
                if not self.test_project_up_to_date(self.directory):
                    return
                if not only_one_nr_of_squares_in_row(self.directory):
                    messagebox.showwarning(
                        title='Warning',
                        message="Not all recordings have been processed with the same nr_of_square_in_row setting.")
                    return
                # Ok, it all looks good. Check if very many recordings are requested and warn the user
                nr = nr_recordings(self.directory)
                if nr_recordings(self.directory) > 100:
                    msg = f"You are about to view {nr} recordings. This may take a while."
                    paint_logger.info(msg)
                    messagebox.showinfo('Warning', msg)
                self.mode = type
                self.proceed = True
                self.dialog.destroy()
            else:
                paint_logger.error("The selected directory is an immature project directory")
                messagebox.showwarning(
                    title='Warning',
                    message="The selected directory is an immature project directory")

    def on_exit(self):
        self.proceed = False
        self.dialog.destroy()  # Destroy only the Toplevel dialog

    def get_result(self):
        return self.proceed, getattr(self, 'directory', None), getattr(self, 'mode', None)

    def test_project_up_to_date(self, project_directory):
        out_of_date = []
        time_stamp_project = os.path.getmtime(os.path.join(project_directory, 'All Recordings.csv'))

        experiments = os.listdir(project_directory)
        for experiment in experiments:
            if not os.path.isdir(os.path.join(project_directory, experiment)):
                continue
            experiment_directory = os.path.join(project_directory, experiment)
            time_stamp_experiment = os.path.getmtime(os.path.join(experiment_directory, 'All Recordings.csv'))
            if time_stamp_project < time_stamp_experiment:
                out_of_date.append(experiment)
        if out_of_date and len(out_of_date) > 0:
            response = messagebox.askyesnocancel(
                title='Warning',
                message="The following experiments are out of date: " + ", ".join(
                                 out_of_date) + ". Shall I run Compile Project?")
            if response:
                compile_project_output(project_directory)
                out_of_date = []

        return len(out_of_date) == 0
