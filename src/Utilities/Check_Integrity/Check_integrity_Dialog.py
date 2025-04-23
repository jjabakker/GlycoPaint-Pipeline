import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from src.Application.Check_Integrity.Check_Integrity import (
    check_integrity_experiment,
    check_integrity_project
)
from src.Fiji.LoggerConfig import (
    paint_logger,
    paint_logger_change_file_handler_name,
    paint_logger_file_name_assigned)
from src.Fiji.NewPaintConfig import (
    get_paint_attribute_with_default)
from src.Application.Support.General_Support_Functions import (
    ToolTip,
    classify_directory)

if not paint_logger_file_name_assigned:
    paint_logger_change_file_handler_name('Generate Squares.log')

class CheckIntegrityDialog:

    def __init__(self, _root):
        self.root = _root
        self.load_saved_parameters()  # Initialize saved parameters and directories
        self.create_ui(_root)
        _root.title('Check Integrity')

    def load_saved_parameters(self):
        """Load parameters from disk or use default values if unavailable."""
        self.project_directory = get_paint_attribute_with_default('User Directories', 'Project Directory','')
        self.experiment_directory = get_paint_attribute_with_default('User Directories', 'Experiment Directory','')
        self.images_directory = get_paint_attribute_with_default('User Directories', 'Images Directory','')
        self.level = get_paint_attribute_with_default('User Directories', 'Level','')

        if self.level == 'Project':
            self.paint_directory = self.project_directory
        elif self.level == 'Experiment':
            self.paint_directory = self.experiment_directory
        else:
            self.paint_directory = self.project_directory


    def create_ui(self, _root):
        """Create and layout the UI components."""
        content = ttk.Frame(_root)

        # Define frames
        frame_directory = self.create_frame(content)
        frame_buttons = self.create_frame(content)

        # Create controls in frames
        self.create_directory_controls(frame_directory)
        self.create_button_controls(frame_buttons)

        # Grid configuration for proper layout
        content.grid(column=0, row=0, sticky="nsew")

        # Add weight to center the frames within the grid
        _root.grid_rowconfigure(0, weight=1)  # Center vertically
        _root.grid_columnconfigure(0, weight=1)  # Center horizontally

        # Layout the frames
        frame_directory.grid(column=0, row=1, columnspan=2, padx=5, pady=5, sticky="nsew")
        frame_buttons.grid(column=0, row=2, columnspan=2, padx=5, pady=5, sticky="nsew")
        _root.grid_rowconfigure(2, weight=1)
        _root.grid_columnconfigure(0, weight=1)

    def create_frame(self, parent, padding=5):
        """Helper method to create a standard frame."""
        return ttk.Frame(parent, borderwidth=5, relief='ridge', padding=(padding, padding, padding, padding))

    def create_labeled_entry(self, frame, label_text, var, row, tooltip):
        """Helper method to create a label and corresponding entry."""
        label = ttk.Label(frame, text=label_text, width=30, anchor=tk.W)
        label.grid(column=0, row=row, padx=5, pady=5)
        entry = ttk.Entry(frame, textvariable=var, width=10)
        entry.grid(column=1, row=row)
        if tooltip:
            ToolTip(label, tooltip, wraplength=400)

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
        btn_generate = ttk.Button(frame, text='Check', command=self.on_check_integrity_pressed)
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

    def on_check_integrity_pressed(self):
        """Generate the squares and save the parameters."""
        if not os.path.isdir(self.paint_directory):
            paint_logger.error("The selected directory does not exist")
            messagebox.showwarning(title='Warning', message="The selected directory does not exist")
            return

        self.level, _ = classify_directory(self.paint_directory)
        if self.level == 'Project':
            check_integrity_project(self.paint_directory)
        elif self.level == 'Experiment':
            check_integrity_experiment(self.paint_directory)
        else:
            msg = "The selected directory does not seem to be a project directory, nor an experiment directory"
            paint_logger.error(msg)
            messagebox.showwarning(self.root, title='Warning', message=msg)
            return
        self.on_exit_pressed()


