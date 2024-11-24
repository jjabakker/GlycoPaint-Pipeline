import os
import time
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from src.Application.Generate_Squares.Generate_Squares import (
    process_project,
    process_experiment)
from src.Application.Generate_Squares.Generate_Squares_Support_Functions import (
    pack_select_parameters)
from src.Application.Utilities.General_Support_Functions import (
    format_time_nicely,
    classify_directory
)
from src.Application.Utilities.ToolTips import ToolTip
from src.Fiji.LoggerConfig import (
    paint_logger,
    paint_logger_change_file_handler_name,
    paint_logger_file_name_assigned)
from src.Fiji.PaintConfig import (
    get_paint_attribute,
    update_paint_attribute)

if not paint_logger_file_name_assigned:
    paint_logger_change_file_handler_name('Generate Squares.log')


class GenerateSquaresDialog:

    def __init__(self, _root):
        self.root = _root
        self.load_saved_parameters()  # Initialize saved parameters and directories
        self.create_ui(_root)
        _root.title('Generate Squares')

    def load_saved_parameters(self):
        """Load parameters from disk or use default values if unavailable."""
        nr_of_squares_in_row = get_paint_attribute('Generate Squares', 'Nr of Squares in Row')
        min_tracks_to_calculate_tau = get_paint_attribute('Generate Squares', 'Min Tracks to Calculate Tau')
        min_allowable_r_squared = get_paint_attribute('Generate Squares', 'Min Allowable R Squared')
        min_required_density_ratio = get_paint_attribute('Generate Squares', 'Min Required Density Ratio')
        max_allowable_variability = get_paint_attribute('Generate Squares', 'Max Allowable Variability')

        self.project_directory = get_paint_attribute('User Directories', 'Project Directory')
        self.experiment_directory = get_paint_attribute('User Directories', 'Experiment Directory')
        self.images_directory = get_paint_attribute('User Directories', 'Images Directory')
        self.level = get_paint_attribute('User Directories', 'Level')

        if self.level == 'Project':
            self.paint_directory = self.project_directory
        elif self.level == 'Experiment':
            self.paint_directory = self.experiment_directory
        else:
            self.paint_directory = self.project_directory

        self.nr_of_squares_in_row = tk.IntVar(value=nr_of_squares_in_row)
        self.min_tracks_for_tau = tk.IntVar(value=min_tracks_to_calculate_tau)
        self.min_allowable_r_squared = tk.DoubleVar(value=min_allowable_r_squared)
        self.min_required_density_ratio = tk.DoubleVar(value=min_required_density_ratio)
        self.max_allowable_variability = tk.DoubleVar(value=max_allowable_variability)

    def create_ui(self, _root):
        """Create and layout the UI components."""
        content = ttk.Frame(_root)

        # Define frames
        frame_parameters = self.create_frame(content)
        frame_directory = self.create_frame(content)
        frame_buttons = self.create_frame(content)

        # Create controls in frames
        self.create_parameter_controls(frame_parameters)
        self.create_directory_controls(frame_directory)
        self.create_button_controls(frame_buttons)

        # Grid configuration for proper layout
        content.grid(column=0, row=0, sticky="nsew")

        # Add weight to center the frames within the grid
        _root.grid_rowconfigure(0, weight=1)  # Center vertically
        _root.grid_columnconfigure(0, weight=1)  # Center horizontally

        # Layout the frames
        frame_parameters.grid(column=0, row=0, columnspan=2, padx=5, pady=5, sticky="nsew")
        frame_directory.grid(column=0, row=1, columnspan=2, padx=5, pady=5, sticky="nsew")
        frame_buttons.grid(column=0, row=2, columnspan=2, padx=5, pady=5, sticky="nsew")
        _root.grid_rowconfigure(2, weight=1)
        _root.grid_columnconfigure(0, weight=1)

    def create_frame(self, parent, padding=5):
        """Helper method to create a standard frame."""
        return ttk.Frame(parent, borderwidth=5, relief='ridge', padding=(padding, padding, padding, padding))

    def create_parameter_controls(self, frame):
        """Create parameter controls for the UI."""
        msg_nr_of_squares = "The number of squares in a row for the grid. The total number of squares will be this value squared."
        msg_min_tracks = "The minimum number of tracks required to calculate Tau. With too few tracks, curvefitting is unreliable."
        msg_min_allowable_r_squared = "The minimum allowable R-squared value for the tracks. Tau values with lower R-squared values are discarded."
        msg_min_required_density_ratio = "The minimum required density ratio for the tracks. Used to distinguish 'cell' squares from background"
        msg_max_allowable_variability = "The maximum allowable variability for the tracks. Used to filter out squares with high variability."

        params = [
            ("Nr of Squares in Row", self.nr_of_squares_in_row, 1, msg_nr_of_squares),
            ("Minimum tracks to calculate Tau", self.min_tracks_for_tau, 2, msg_min_tracks),
            ("Min allowable R-squared", self.min_allowable_r_squared, 3, msg_min_allowable_r_squared),
            ("Min Required Density Ratio", self.min_required_density_ratio, 4, msg_min_required_density_ratio),
            ("Max Allowable Variability", self.max_allowable_variability, 5, msg_max_allowable_variability),
        ]

        for label_text, var, row, tooltip in params:
            self.create_labeled_entry(frame, label_text, var, row, tooltip)

    def create_labeled_entry(self, frame, label_text, var, row, tooltip):
        """Helper method to create a label and corresponding entry."""
        label = ttk.Label(frame, text=label_text, width=30, anchor=tk.W)
        label.grid(column=0, row=row, padx=5, pady=5)
        entry = ttk.Entry(frame, textvariable=var, width=10)
        entry.grid(column=1, row=row)
        if tooltip:
            ToolTip(label, tooltip, wraplength=400)

    def create_processing_controls(self, frame):
        """Create the processing checkboxes."""

        msg_square_tau = "If checked, the program will calculate a Tau for each square individually."
        msg_recording_tau = "If checked, the program will calculate one Tau for all visible squares combined."

    def create_directory_controls(self, frame):
        """Create controls for directory management."""
        btn_change_dir = ttk.Button(frame, text='Change Directory', width=15, command=self.on_change_dir)
        self.lbl_directory = ttk.Label(frame, text=self.paint_directory, width=60)
        btn_change_dir.grid(column=0, row=0, padx=10, pady=5)
        self.lbl_directory.grid(column=1, row=0, padx=20, pady=5)

        tooltip = "Specify a Project or an Experiment directory here."
        ToolTip(btn_change_dir, tooltip, wraplength=400)

    def create_button_controls(self, frame):
        """Create buttons for the UI."""
        btn_generate = ttk.Button(frame, text='Generate', command=self.on_generate_squares_pressed)
        btn_exit = ttk.Button(frame, text='Exit', command=self.on_exit_pressed)

        # Create two empty columns to balance the buttons in the center
        frame.grid_columnconfigure(0, weight=1)  # Left empty column
        frame.grid_columnconfigure(1, weight=0)  # Buttons column
        frame.grid_columnconfigure(2, weight=1)  # Right empty column

        # Center the buttons by placing them in column 1
        btn_generate.grid(column=1, row=0, padx=10, pady=0, sticky="ew")  # Center Process button
        btn_exit.grid(column=1, row=1, padx=10, pady=0, sticky="ew")  # Center Exit button

    def on_change_dir(self):
        """Change the paint directory through a dialog."""
        paint_directory = filedialog.askdirectory(initialdir=self.paint_directory)
        if classify_directory(paint_directory) == 'Project':
            self.project_directory = paint_directory
        else:
            self.experiment_directory = paint_directory
        if paint_directory:
            self.paint_directory = paint_directory
            self.lbl_directory.config(text=paint_directory)

    def on_exit_pressed(self):
        """Handle the exit button click."""
        self.root.destroy()

    def on_generate_squares_pressed(self):
        """Generate the squares and save the parameters."""
        start_time = time.time()

        if not os.path.isdir(self.paint_directory):
            paint_logger.error("The selected directory does not exist")
            messagebox.showwarning(title='Warning', message="The selected directory does not exist")
            return

        self.level, _ = classify_directory(self.paint_directory)
        if self.level == 'Project':
            generate_function = process_project
            self.project_directory = self.paint_directory
        elif self.level == 'Experiment':
            generate_function = process_experiment
            self.experiment_directory = self.paint_directory
        else:
            msg = "The selected directory does not seem to be a project directory, nor an experiment directory"
            paint_logger.error(msg)
            messagebox.showwarning(self.root, title='Warning', message=msg)
            return

        select_parameters = pack_select_parameters(
            min_required_density_ratio=self.min_required_density_ratio.get(),
            max_allowable_variability=self.max_allowable_variability.get(),
            min_track_duration=get_paint_attribute('Generate Squares', 'Min Track Duration') or 0,
            max_track_duration=get_paint_attribute('Generate Squares', 'Max Track Duration') or 10000,
            min_allowable_r_squared=get_paint_attribute('Generate Squares', 'Min Allowable R Squared') or 0.9,
            neighbour_mode=get_paint_attribute('Generate Squares', 'Neighbour Mode') or 'Free',
        )
        generate_function(
            self.paint_directory,
            select_parameters=select_parameters,
            nr_of_squares_in_row=self.nr_of_squares_in_row.get(),
            min_allowable_r_squared=self.min_allowable_r_squared.get(),
            min_tracks_for_tau=self.min_tracks_for_tau.get(),
            paint_force=True
        )
        run_time = time.time() - start_time
        paint_logger.info(f"Total processing time is {format_time_nicely(run_time)}")
        self.save_parameters()
        self.on_exit_pressed()

    def save_parameters(self):
        update_paint_attribute('Generate Squares', 'Nr of Squares in Row', self.nr_of_squares_in_row.get())
        update_paint_attribute('Generate Squares', 'Min Tracks to Calculate Tau', self.min_tracks_for_tau.get())
        update_paint_attribute('Generate Squares', 'Min Allowable R Squared', self.min_allowable_r_squared.get())
        update_paint_attribute('Generate Squares', 'Min Required Density Ratio', self.min_required_density_ratio.get())
        update_paint_attribute('Generate Squares', 'Max Allowable Variability', self.max_allowable_variability.get())

        update_paint_attribute('User Directories', 'Project Directory', self.project_directory)
        update_paint_attribute('User Directories', 'Experiment Directory', self.experiment_directory)
        update_paint_attribute('User Directories', 'Images Directory', self.images_directory)
        update_paint_attribute('User Directories', 'Level', self.level)


if __name__ == "__main__":
    root = tk.Tk()
    root.eval('tk::PlaceWindow . center')
    GenerateSquaresDialog(root)
    root.mainloop()
