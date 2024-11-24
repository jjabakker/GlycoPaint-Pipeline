import math
import os
import platform
import shutil
import statistics
import subprocess
import sys
import tempfile
import time
import tkinter as tk
from datetime import datetime
from tkinter import *
from tkinter import messagebox
from tkinter import ttk

import pandas as pd
from PIL import Image

from src.Application.Generate_Squares.Generate_Squares_Support_Functions import (
    calculate_tau,
    extra_constraints_on_tracks_for_tau_calculation,
    calc_area_of_square,
    calculate_density)
from src.Application.Recording_Viewer.Class_Define_Cell_Dialog import DefineCellDialog
from src.Application.Recording_Viewer.Class_Heatmap_Dialog import HeatMapDialog
from src.Application.Recording_Viewer.Class_Select_Recording_Dialog import SelectRecordingDialog
from src.Application.Recording_Viewer.Class_Select_Square_Dialog import SelectSquareDialog
from src.Application.Recording_Viewer.Class_Select_Viewer_Data_Dialog import SelectViewerDataDialog
from src.Application.Recording_Viewer.Display_Selected_Squares import (
    display_selected_squares)
from src.Application.Recording_Viewer.Get_Images import get_images
from src.Application.Recording_Viewer.Heatmap_Support import (
    get_colormap_colors, get_color_index,
    get_heatmap_data)
from src.Application.Recording_Viewer.Recording_Viewer_Support_Functions import (
    test_if_square_is_in_rectangle,
    save_as_png,
    find_excel_executable)
from src.Application.Recording_Viewer.Select_Squares import (
    relabel_tracks,
    select_squares)
from src.Application.Utilities.General_Support_Functions import (
    read_squares_from_file,
    set_application_icon)
from src.Fiji.LoggerConfig import (
    paint_logger,
    paint_logger_change_file_handler_name)

# Log to an appropriately named file
paint_logger_change_file_handler_name('Recording Viewer.log')


# ----------------------------------------------------------------------------------------
# RecordingViewer Class
# ----------------------------------------------------------------------------------------

class RecordingViewer:

    def __init__(self, parent, user_specified_directory, user_specified_mode):

        super().__init__()
        self.viewer_dialog = tk.Toplevel(parent)
        self.viewer_dialog.title(f'Recording Viewer - {user_specified_directory}')
        self.viewer_dialog.resizable(False, False)
        self.viewer_dialog.protocol("WM_DELETE_WINDOW", self.on_exit_viewer)
        self.viewer_dialog.grab_set()  # Prevent interaction with the main window
        self.viewer_dialog.focus_force()  # Bring the dialog to focus

        # Save the parameters
        self.user_specified_directory = user_specified_directory
        self.user_specified_mode = user_specified_mode

        self.initialize_variables()

        self.setup_ui()
        self.load_images_and_config()
        self.setup_exclude_button()
        self.setup_heatmap()
        self.setup_key_bindings()

        # Set the custom icon for the main window
        root.iconbitmap('../Images/Paint1.png')

    def setup_heatmap(self):

        self.heatmap_option = tk.IntVar()
        self.heatmap_option.set(1)  # Default selection is the first option

        self.heatmap_global_min_max = tk.IntVar()
        self.heatmap_global_min_max.set(1)  # Default selection is the first option

        # The heatmap_type_selection_changed function is called by the UI when a radio button is clicked
        self.heatmap_option.trace_add("write", self.heatmap_type_selection_changed)

        self.checkbox_value = tk.BooleanVar()
        self.checkbox_value.set(False)  # Default is unchecked

    def initialize_variables(self):

        self.img_no = 0
        self.image_directory = None

        # The main data structures
        self.df_all_squares = None
        self.df_squares = None
        self.df_all_tracks = None
        self.df_experiment = None

        # UI state variables
        self.start_x = None
        self.start_y = None
        self.rect = None

        # Variables to keep track if the user changed something
        self.recording_changed = False
        self.save_on_exit = False

        # Variables indicating whether to show squares and square numbers in the left pane
        self.show_squares_numbers = True
        self.show_squares = True

        # Variables to hold the information on the current image
        self.max_allowable_variability = None
        self.min_required_density_ratio = None
        self.min_track_duration = None
        self.max_track_duration = None
        self.min_allowable_r_squared = None
        self.neighbour_mode = None

        # Variables to hold references to the Dialogs, initially all empty
        self.select_square_dialog = None
        self.heatmap_control_dialog = None
        self.define_cells_dialog = None
        self.square_info_popup = None
        self.select_recording_dialog = None

        self.squares_in_rectangle = []
        self.saved_list_images = []
        self.only_valid_tau = True

        self.selected_values = []
        self.filter_applied = []

    def setup_ui(self):
        """
        Sets up the UI by defining the top level frames
        For each frame a setup function is called
        """

        self.content = ttk.Frame(self.viewer_dialog, borderwidth=2, relief='groove', padding=(5, 5, 5, 5))

        self.frame_images = ttk.Frame(self.content, borderwidth=2, relief='groove', padding=(5, 5, 5, 5))
        self.frame_navigation_buttons = ttk.Frame(self.content, borderwidth=2, relief='groove', padding=(5, 5, 5, 5))
        self.frame_controls = ttk.Frame(self.content, borderwidth=2, relief='groove', padding=(5, 5, 5, 5))

        self.frame_images.grid(column=0, row=0, rowspan=2, padx=5, pady=5, sticky=tk.N)
        self.frame_navigation_buttons.grid(column=0, row=2, padx=5, pady=5, sticky=tk.N)
        self.frame_controls.grid(column=1, row=0, rowspan=2, padx=5, pady=5, sticky=N)

        self.setup_frame_images()
        self.setup_frame_navigation_buttons()
        self.setup_frame_controls()

        self.content.grid(column=0, row=0)

    # ----------------------------------------------------------------------------------------
    # Setup functions for the frame_images content
    # ----------------------------------------------------------------------------------------

    def setup_frame_images(self):

        frame_width = 530
        frame_height = 690

        self.left_image_frame = ttk.Frame(
            self.frame_images,
            borderwidth=2,
            relief='groove',
            width=frame_width,
            height=frame_height)
        self.right_image_frame = ttk.Frame(
            self.frame_images,
            borderwidth=2,
            relief='groove',
            width=frame_width,
            height=frame_height)

        self.left_image_frame.grid(column=0, row=0, padx=5, pady=5, sticky=N)
        self.right_image_frame.grid(column=1, row=0, padx=5, pady=5, sticky=N)

        # Prevent the frames from resizing
        self.left_image_frame.grid_propagate(False)
        self.right_image_frame.grid_propagate(False)

        # Define the canvas widgets for the images
        self.left_image_canvas = tk.Canvas(self.left_image_frame, width=512, height=512)
        self.right_image_canvas = tk.Canvas(self.right_image_frame, width=512, height=512)

        self.left_image_canvas.grid(column=0, row=0, padx=5, pady=5)
        self.right_image_canvas.grid(column=0, row=0, padx=5, pady=5)

        # Define the labels and combobox widgets for the images
        self.list_images = []
        self.list_of_image_names = []
        self.cb_image_names = ttk.Combobox(
            self.left_image_frame, values=self.list_of_image_names, state='readonly', width=30)

        # Label for the right image name
        self.lbl_image_bf_name = StringVar(self.viewer_dialog, "")
        lbl_image_bf_name = ttk.Label(self.right_image_frame, textvariable=self.lbl_image_bf_name)

        # Labels for image info
        self.text_for_info1 = StringVar(self.viewer_dialog, "")
        self.lbl_info1 = ttk.Label(self.left_image_frame, textvariable=self.text_for_info1)

        self.text_for_info2 = StringVar(self.viewer_dialog, "")
        self.lbl_info2 = ttk.Label(self.left_image_frame, textvariable=self.text_for_info2)

        self.text_for_info3 = StringVar(self.viewer_dialog, "")
        self.lbl_info3 = ttk.Label(self.left_image_frame, textvariable=self.text_for_info3)

        self.text_for_info4 = StringVar(self.viewer_dialog, "")
        self.lbl_info4 = ttk.Label(self.left_image_frame, textvariable=self.text_for_info4)

        # Create a ttk style object
        self.style = ttk.Style()
        self.style.configure("Red.Label", foreground="red")
        self.style.configure("Black.Label", foreground="red")

        # Bind combobox selection
        self.cb_image_names.bind("<<ComboboxSelected>>", self.image_selected)

        # Layout labels and combobox
        self.cb_image_names.grid(column=0, row=1, padx=5, pady=5)
        self.lbl_info1.grid(column=0, row=2, padx=5, pady=5)
        self.lbl_info2.grid(column=0, row=3, padx=5, pady=5)
        self.lbl_info3.grid(column=0, row=4, padx=5, pady=5)
        self.lbl_info4.grid(column=0, row=5, padx=5, pady=5)
        lbl_image_bf_name.grid(column=0, row=1, padx=0, pady=0)

    def setup_frame_navigation_buttons(self):
        # This frame is part of the content frame and contains the following buttons: bn_forward, bn_exclude, bn_backward, bn_exit

        self.bn_end = ttk.Button(
            self.frame_navigation_buttons, text='>>', command=lambda: self.on_forward_backward('END'))
        self.bn_forward = ttk.Button(
            self.frame_navigation_buttons, text='>', command=lambda: self.on_forward_backward('FORWARD'))
        self.bn_exclude = ttk.Button(self.frame_navigation_buttons, text='Reject', command=lambda: self.on_exinclude())
        self.bn_backward = ttk.Button(
            self.frame_navigation_buttons, text='<', command=lambda: self.on_forward_backward('BACKWARD'))
        self.bn_start = ttk.Button(
            self.frame_navigation_buttons, text='<<', command=lambda: self.on_forward_backward('START'))
        self.bn_exit = ttk.Button(self.frame_navigation_buttons, text='Exit', command=lambda: self.on_exit_viewer())

        # Layout the buttons
        self.bn_start.grid(column=0, row=0, padx=5, pady=5)
        self.bn_backward.grid(column=1, row=0, padx=5, pady=5)
        self.bn_exclude.grid(column=2, row=0, padx=5, pady=5)
        self.bn_forward.grid(column=3, row=0, padx=5, pady=5)
        self.bn_end.grid(column=4, row=0, padx=5, pady=5)
        self.bn_exit.grid(column=5, row=0, padx=30, pady=5)

        # Initially disable the back button
        self.bn_backward.configure(state=tk.DISABLED)

    def setup_frame_controls(self):
        # This frame is part of the content frame and contains the following frames: frame_commands

        self.frame_commands = ttk.Frame(self.frame_controls, borderwidth=2, relief='groove', padding=(5, 5, 5, 5))
        self.frame_save_commands = ttk.Frame(self.frame_controls, borderwidth=2, relief='groove', padding=(5, 5, 5, 5))
        self.setup_frame_commands()
        self.setup_frame_save_commands()
        self.frame_commands.grid(column=0, row=3, padx=5, pady=5)
        self.frame_save_commands.grid(column=0, row=6, padx=5, pady=5)

    def setup_frame_commands(self):
        # This frame is part of frame_controls and contains the following buttons: bn_output, bn_reset, bn_excel, bn_histogram

        button_width = 13

        self.bn_select_recording = ttk.Button(
            self.frame_commands, text='Select Recordings', command=lambda: self.on_select_recording(),
            width=button_width)
        self.bn_heatmap = ttk.Button(
            self.frame_commands, text='Heatmap', command=lambda: self.on_heatmap(), width=button_width)
        self.bn_select_squares = ttk.Button(
            self.frame_commands, text='Select Squares', command=lambda: self.on_select_squares(),
            width=button_width)
        self.bn_define_cells = ttk.Button(
            self.frame_commands, text='Define Cells', command=lambda: self.on_define_cells(), width=button_width)
        self.bn_square_data = ttk.Button(
            self.frame_commands, text='Squares Data', command=lambda: self.on_squares_data(), width=button_width)

        self.bn_select_recording.grid(column=0, row=0, padx=5, pady=5)
        self.bn_select_squares.grid(column=0, row=1, padx=5, pady=5)
        self.bn_heatmap.grid(column=0, row=2, padx=5, pady=5)
        self.bn_define_cells.grid(column=0, row=3, padx=5, pady=5)
        self.bn_square_data.grid(column=0, row=6, padx=5, pady=5)

    def setup_frame_save_commands(self):
        # Create a StringVar for save state
        self.save_state_var = tk.StringVar(value="Ask")

        # Define options for the radio buttons
        options = [("Always Save", "Always"), ("Never Save", "Never"), ("Ask to Save", "Ask")]

        # Create and place each radio button using a loop
        for i, (text, value) in enumerate(options):
            rb = tk.Radiobutton(
                self.frame_save_commands, text=text, variable=self.save_state_var,
                width=12, value=value, anchor=tk.W
            )
            rb.grid(column=0, row=i, padx=5, pady=5, sticky=tk.W)

    # ----------------------------------------------------------------------------------------
    # Load images and data
    # ----------------------------------------------------------------------------------------

    def load_images_and_config(self):

        # Read the 'All Squares' file
        self.df_all_squares = read_squares_from_file(
            os.path.join(self.user_specified_directory, 'All Squares.csv'))
        if self.df_all_squares is None:
            self.show_error_and_exit("No 'All Squares.csv.csv' file, Did you select an image directory?")

        # Read the 'All Experiments' file
        self.df_experiment = pd.read_csv(os.path.join(self.user_specified_directory, 'All Recordings.csv'),
                                         dtype={'Max Allowable Variability': float,
                                                'Min Required Density Ratio': float})
        if self.df_experiment is None:
            self.show_error_and_exit("No 'All Recordings' file, Did you select an image directory?")
        self.df_experiment.set_index('Ext Recording Name', drop=False, inplace=True)

        # Check that the two files align
        if set(self.df_all_squares['Ext Recording Name']) != set(self.df_experiment['Ext Recording Name']):
            self.show_error_and_exit(
                "The recordings in the 'All Squares' file do not align with the 'All Experiments' file")

        # Read the 'All Tracks' file
        self.df_all_tracks = pd.read_csv(os.path.join(self.user_specified_directory, 'All Tracks.csv'))
        if self.df_all_tracks is None:
            self.show_error_and_exit("No 'All Tracks' file, Did you select an image directory?")
        if 'Unique Key' not in self.df_all_tracks.columns:
            self.show_error("No 'Unique Key' in the All Tracks file. Did you run Generate Squares?")
        self.df_all_tracks.set_index('Unique Key', inplace=True, drop=False)

        self.nr_of_squares_in_row = int(self.df_experiment.iloc[0]['Nr of Squares in Row'])

        # Load the images
        self.list_images = get_images(self, initial=True)
        if not self.list_images:
            self.show_error_and_exit(f"No images were found in directory {self.user_specified_directory}.")

        # Load the combobox with the image names
        self.list_of_image_names = [image['Left Image Name'] for image in self.list_images]
        self.cb_image_names['values'] = self.list_of_image_names

        self.initialise_image_display()
        self.img_no = -1
        self.on_forward_backward('FORWARD')

    def setup_exclude_button(self):
        # Find the index of the row matching the image name
        row_index = self.df_experiment.index[self.df_experiment['Ext Recording Name'] == self.image_name].tolist()[0]

        # Check the 'Exclude' status and set properties accordingly
        is_excluded = self.df_experiment.loc[row_index, 'Exclude']
        self.bn_exclude.config(text='Include' if is_excluded else 'Exclude')
        self.text_for_info4.set('Excluded' if is_excluded else '')
        self.lbl_info4.config(style="Red.Label" if is_excluded else "Black.Label")

    # ----------------------------------------------------------------------------------------
    # Event Handlers for buttons
    # ----------------------------------------------------------------------------------------

    def on_select_recording(self):
        if self.is_dialog_active():
            return
        else:
            self.select_recording_dialog = SelectRecordingDialog(
                self,
                self.df_experiment,
                self.on_recording_selection,
                self.selected_values,
                self.filter_applied)

    def on_heatmap(self):
        # If the heatmap is not already active, then we need to run the heatmap dialog

        if self.is_dialog_active():
            return
        else:
            # HeatMap expects square numbers as index
            self.df_squares.set_index('Square Nr', inplace=True, drop=False)

            self.set_dialog_buttons(tk.DISABLED)
            self.heatmap_control_dialog = HeatMapDialog(self, self.on_heatmap_close_callback)
            self.img_no -= 1
            self.on_forward_backward('FORWARD')

    def on_select_squares(self):
        # If the select square dialog is not already active, then we need to run the select square dialog

        if self.is_dialog_active():
            return

        self.viewer_dialog.grab_release()
        self.set_dialog_buttons(tk.DISABLED)
        self.min_required_density_ratio = self.list_images[self.img_no]['Min Required Density Ratio']
        self.max_allowable_variability = self.list_images[self.img_no]['Max Allowable Variability']
        self.min_allowable_r_squared = self.list_images[self.img_no]['Min Allowable R Squared']
        self.neighbour_mode = self.list_images[self.img_no]['Neighbour Mode']

        self.min_track_duration = 1  # ToDo thi does not look ok
        self.max_track_duration = 199

        if self.select_square_dialog is None:
            self.select_square_dialog = SelectSquareDialog(
                self,
                self.update_select_squares,
                self.min_required_density_ratio,
                self.max_allowable_variability,
                self.min_track_duration,
                self.max_track_duration,
                self.min_allowable_r_squared,
                self.neighbour_mode)

    def on_define_cells(self):
        if self.is_dialog_active():
            return

        self.set_dialog_buttons(tk.DISABLED)
        self.viewer_dialog.grab_release()
        self.define_cells_dialog = DefineCellDialog(
            self,
            self.callback_to_assign_squares_to_cell_id,
            self.callback_to_reset_cell_definition,
            self.callback_to_close_define_cells_dialog
        )

    def on_squares_data(self):
        """Exports square data to a temporary CSV file and opens it in Excel."""

        # Ensure the DataFrame exists and is valid
        if self.df_squares.empty:
            return

        # Determine the command for opening Excel
        if platform.system() == 'Darwin':
            excel_command = 'open'
            excel_args = ['-a', '/Applications/Microsoft Excel.app']
        elif platform.system() == 'Windows':
            excel_command = find_excel_executable()
            excel_args = [excel_command]
        else:
            raise OSError("Unsupported operating system.")

        # Create a temporary file
        temp_dir = tempfile.mkdtemp()
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        temp_file = os.path.join(temp_dir, f'Temporary_All_Squares_{timestamp}.csv')

        # Save the Squares data to a temporary file
        self.df_squares.to_csv(temp_file, index=False)
        if not os.path.exists(temp_file):
            raise FileNotFoundError(f"Failed to create temporary file: {temp_file}")

        # Open the file in Excel
        try:
            if platform.system() == 'Darwin':
                subprocess.run([excel_command] + excel_args + [temp_file], check=True)
            elif platform.system() == 'Windows':
                subprocess.run(excel_args + [temp_file], shell=True, check=True)
        except subprocess.CalledProcessError as e:
            msg = "Failed to open Excel, cannot display squares data."
            messagebox.showerror("Error", msg)
            paint_logger.error(msg)
            # Clean up the temporary directory
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
            return

        # Allow some time for Excel to process the file
        time.sleep(2)

        # Clean up the temporary directory
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

        # Process square data statistics
        nr_total_squares = len(self.df_squares)
        tau_values = self.df_squares[self.df_squares['Selected']]['Tau'].tolist()
        nr_visible_squares = len(tau_values)

        # Initialize Tau statistics
        tau_min = tau_max = tau_mean = tau_median = tau_std = '-'

        if nr_visible_squares > 0:
            tau_min = min(tau_values)
            tau_max = max(tau_values)
            tau_mean = round(statistics.mean(tau_values), 0)
            tau_median = round(statistics.median(tau_values), 0)
            tau_std = round(statistics.stdev(tau_values), 1)

        # Display statistics   #ToDo print statements are not good
        print('\n\n')
        print(f'The total number of squares:   {nr_total_squares}')
        print(f'The visible number of squares: {nr_visible_squares}')
        print(f'The maximum Tau value:         {tau_max}')
        print(f'The minimum Tau value:         {tau_min}')
        print(f'The mean Tau value:            {tau_mean}')
        print(f'The median Tau value:          {tau_median}')
        print(f'The Tau standard deviation:    {tau_std}')

    # --------------------------------------------------------------------------------------------
    # Key Bindings and associated functions
    # --------------------------------------------------------------------------------------------

    def setup_key_bindings(self):
        # Key binding dictionary
        self.key_bindings = {
            '<Right>': lambda e: self.conditional_navigation(e),
            '<Left>': lambda e: self.conditional_navigation(e),
            's': lambda e: self.toggle_show_squares(),
            'n': lambda e: self.toggle_show_square_numbers(),
            't': lambda e: self.toggle_selected_squares(),
            'v': lambda e: self.on_toggle_valid_square(),
            'o': lambda e: self.output_picture(),
            'p': lambda e: self.output_pictures_to_pdf(),
            '<Escape>': lambda e: self.on_escape()
        }

        for key, action in self.key_bindings.items():
            self.viewer_dialog.bind(key, action)

    def conditional_navigation(self, event):
        # Navigate to 'START' or 'END' based on a modifier (Shift key), otherwise go 'FORWARD' or 'BACKWARD'.
        if event.keysym == 'Right':
            direction = 'END' if event.state & 0x0001 else 'FORWARD'  # Shift modifier check
        elif event.keysym == 'Left':
            direction = 'START' if event.state & 0x0001 else 'BACKWARD'
        else:
            return
        self.on_forward_backward(direction)

    def toggle_show_squares(self):
        self.show_squares = not self.show_squares
        self.display_selected_squares()

    def toggle_show_square_numbers(self):
        self.show_squares_numbers = not self.show_squares_numbers
        self.show_numbers = self.show_squares  # Set show_numbers based on show_squares
        self.display_selected_squares()

    def toggle_selected_squares(self):
        self.show_squares = not self.show_squares
        self.display_selected_squares()

    def on_toggle_valid_square(self):
        self.only_valid_tau = not self.only_valid_tau
        select_squares(self, only_valid_tau=self.only_valid_tau)
        self.display_selected_squares()

    def output_pictures_to_pdf(self):
        # Create the squares directory if it does not exist
        squares_dir = os.path.join(self.user_specified_directory, 'Output', 'Squares')
        os.makedirs(squares_dir, exist_ok=True)

        # Cycle through all images
        self.img_no = -1
        for img_no in range(len(self.list_images)):
            self.on_forward_backward('FORWARD')

            image_name = self.list_images[self.img_no]['Left Image Name']
            paint_logger.debug(f"Writing {image_name} to pdf file {os.path.join(squares_dir, image_name)}")

            # Delete the squares and write the canvas with just the tracks
            self.left_image_canvas.delete("all")
            self.left_image_canvas.create_image(0, 0, anchor=NW, image=self.list_images[self.img_no]['Left Image'])
            save_as_png(self.left_image_canvas, os.path.join(squares_dir, image_name))

            # Add the squares and write the canvas complete with squares
            self.select_squares_for_display()
            self.display_selected_squares()
            image_name = image_name + '-squares'
            save_as_png(self.left_image_canvas, os.path.join(squares_dir, image_name))

        # Find all the png files and sort them
        png_files = []
        files = os.listdir(squares_dir)
        for file in files:
            if file.endswith(".png"):
                png_files.append(os.path.join(squares_dir, file))
        png_files = sorted(png_files)

        # Create Image objects of all png files
        png_images = []
        for png_file in png_files:
            png_images.append(Image.open(png_file))
        pdf_path = os.path.join(squares_dir, 'images.pdf')

        # Create a PDF with a first image and add all the other images to it
        if platform.system() == "Darwin":
            png_images[0].save(pdf_path, "PDF", resolution=200.0, save_all=True, append_images=png_images[1:])

        # Go back to the image where we were
        self.img_no -= 1
        self.on_forward_backward('FORWARD')

    def output_picture(self):
        # Create the squares directory if it does not exist
        squares_dir = os.path.join(self.user_specified_directory, 'Output', 'Squares')
        os.makedirs(squares_dir, exist_ok=True)

        image_name = self.list_images[self.img_no]['Left Image Name']
        paint_logger.debug(f"Writing {image_name} to pdf file {os.path.join(squares_dir, image_name)}")

        # Delete the squares and write the canvas with just the tracks
        self.left_image_canvas.delete("all")
        self.left_image_canvas.create_image(0, 0, anchor=NW, image=self.list_images[self.img_no]['Left Image'])
        save_as_png(self.left_image_canvas, os.path.join(squares_dir, image_name))

        # Add the squares and write the canvas complete with squares
        self.select_squares_for_display()
        self.display_selected_squares()
        image_name = image_name + '-squares'
        save_as_png(self.left_image_canvas, os.path.join(squares_dir, image_name))

        # Find all the png files and sort them
        png_files = []
        files = os.listdir(squares_dir)
        for file in files:
            if file.endswith(".png"):
                png_files.append(os.path.join(squares_dir, file))
        png_files = sorted(png_files)

        # Create Image objects of all png files
        png_images = []
        for png_file in png_files:
            png_images.append(Image.open(png_file))
        pdf_path = os.path.join(squares_dir, 'images.pdf')

        # Create a PDF with a first image and add all the other images to it
        if platform.system() == "Darwin":
            png_images[0].save(pdf_path, "PDF", resolution=200.0, save_all=True, append_images=png_images[1:])

        # Go back to the image where we were
        self.img_no -= 1
        self.on_forward_backward('FORWARD')

    def on_escape(self):

        if self.square_info_popup:
            self.square_info_popup.destroy()
            self.square_info_popup = None

    # ----------------------------------------------------------------------------------------
    #
    # ----------------------------------------------------------------------------------------

    def callback_to_close_define_cells_dialog(self):
        # Now update All Squares
        if self.recording_changed:
            self.df_all_squares.update(self.df_squares)
            self.save_on_exit = True
        self.define_cells_dialog = None

    def callback_to_reset_square_selection(self):
        """
        This function is called by the DefineCellsDialog
        It will empty the list of squares that are currently selected and update the display
        """

        self.squares_in_rectangle = []
        self.display_selected_squares()

    def callback_to_assign_squares_to_cell_id(self, cell_id):
        """
        This function is called by the DefineCellsDialog when a cell id has been selected to is assigned to a square
        See if there are any squares selected and if so update the cell id, then update the display
        """

        # Update 'Cell Id' for all squares in the rectangle
        self.df_squares.set_index('Square Nr', inplace=True, drop=False)
        if len(self.squares_in_rectangle) > 0:
            self.df_squares.loc[self.squares_in_rectangle, 'Cell Id'] = int(cell_id)

        # Set the flag and clear the list
        self.recording_changed = True
        self.squares_in_rectangle = []
        self.display_selected_squares()

    def callback_to_reset_cell_definition(self):
        """
        This function is called by DefineCellsDialog
        It will clear all the cell selection and update the display
        """

        self.df_squares['Cell Id'] = 0
        self.display_selected_squares()
        self.recording_changed = True

    def initialise_image_display(self):
        # Get current image data
        current_image = self.list_images[self.img_no]

        # Update the image display based on the current image number
        self.left_image_canvas.create_image(0, 0, anchor=tk.NW, image=current_image['Left Image'])
        self.right_image_canvas.create_image(0, 0, anchor=tk.NW, image=current_image['Right Image'])

        # Update labels for image information
        self.lbl_image_bf_name.set(current_image['Right Image Name'])

        # Construct cell information text
        cell_info = (
            f"({current_image['Cell Type']}) - "
            f"({current_image['Adjuvant']}) - "
            f"({current_image['Probe Type']}) - "
            f"({current_image['Probe']})"
        )
        self.text_for_info1.set(cell_info)
        info2 = f"Spots: {self.list_images[self.img_no]['Nr Spots']:,} - Threshold: {self.list_images[self.img_no]['Threshold']}"
        self.text_for_info2.set(info2)
        info3 = f"Min Required Density Ratio: {self.list_images[self.img_no]['Min Required Density Ratio']:,} - Max Allowable Variability: {self.list_images[self.img_no]['Max Allowable Variability']}"
        self.text_for_info3.set(info3)

        self.image_name = current_image['Left Image Name']
        self.df_squares = self.df_all_squares[self.df_all_squares['Ext Recording Name'] == self.image_name]

    def on_exinclude(self):
        """
        Toggle the state of the recording. Change the button text and the info text
        :return:
        """

        # row_index = self.df_experiment.index[self.df_experiment['Ext Recording Name'] == self.image_name].tolist()[0]
        # This was complex code, but the index is already the image name

        row_index = self.image_name
        is_excluded = self.df_experiment.loc[row_index, 'Exclude'] = not self.df_experiment.loc[row_index, 'Exclude']

        self.bn_exclude.config(text='Include' if is_excluded else 'Exclude')
        self.text_for_info4.set('Excluded' if is_excluded else '')
        self.lbl_info4.config(style="Red.Label" if is_excluded else "Black.Label")
        self.lbl_info4.configure(foreground='red' if is_excluded else 'black')

        self.recording_changed = True  # ToDo

    def on_exit_viewer(self):
        if self.save_on_exit or self.recording_changed:  # You need to test both!
            status = self.save_changes_on_exit()
            if status is None:
                return
            else:
                root.quit()
        else:
            root.quit()

    def image_selected(self, _):
        image_name = self.cb_image_names.get()
        paint_logger.debug(image_name)
        index = self.list_of_image_names.index(image_name)
        self.img_no = index - 1
        self.on_forward_backward('FORWARD')

    def update_select_squares(
            self,
            setting_type: str,
            min_required_density_ratio: float,
            max_allowable_variability: float,
            min_duration: float,
            max_duration: float,
            min_allowable_r_squared: float,
            neighbour_mode: str,
    ) -> None:
        """
        This function is called from the SelectSquareDialog when a control has changed or when the control exists. This
        gives an opportunity to update the settings for the current image
        """
        self.recording_changed = True
        self.save_on_exit = True
        if setting_type == "Min Required Density Ratio":
            self.min_required_density_ratio = min_required_density_ratio
            self.list_images[self.img_no]['Min Required Density Ratio'] = min_required_density_ratio
            self.df_experiment.loc[self.image_name, 'Min Required Density Ratio'] = min_required_density_ratio
        elif setting_type == "Max Allowable Variability":
            self.max_allowable_variability = max_allowable_variability
            self.list_images[self.img_no]['Max Allowable Variability'] = max_allowable_variability
            self.df_experiment.loc[self.image_name, 'Max Allowable Variability'] = max_allowable_variability
        elif setting_type == "Min Track Duration":
            self.min_track_duration = min_duration
        elif setting_type == "Max Track Duration":  # ToDo
            self.max_track_duration = max_duration
        elif setting_type == "Min Allowable R Squared":
            self.min_allowable_r_squared = min_allowable_r_squared
            self.list_images[self.img_no]['Min Allowable R Squared'] = min_allowable_r_squared
            self.df_experiment.loc[self.image_name, 'Min Allowable R Squared'] = min_allowable_r_squared
        elif setting_type == "Neighbour Mode":
            self.neighbour_mode = neighbour_mode
            self.list_images[self.img_no]['Neighbour Mode'] = neighbour_mode
            self.df_experiment.loc[self.image_name, 'Neighbour Mode'] = neighbour_mode
        elif setting_type == "Set for All":
            # Set the same settings for all recordings
            self.min_required_density_ratio = min_required_density_ratio
            self.max_allowable_variability = max_allowable_variability
            self.min_allowable_r_squared = min_allowable_r_squared
            self.neighbour_mode = neighbour_mode

            self.min_track_duration = min_duration
            self.max_track_duration = max_duration

            for index, row in self.df_experiment.iterrows():
                self.df_experiment.loc[index, 'Min Required Density Ratio'] = min_required_density_ratio
                self.df_experiment.loc[index, 'Max Allowable Variability'] = max_allowable_variability
                self.df_experiment.loc[index, 'Min Allowable R Squared'] = min_allowable_r_squared
                self.df_experiment.loc[index, 'Neighbour Mode'] = neighbour_mode

            self.df_experiment.loc[self.image_name, 'Min Required Density Ratio'] = min_required_density_ratio
            self.df_experiment.loc[self.image_name, 'Max Allowable Variability'] = max_allowable_variability
            self.df_experiment.loc[self.image_name, 'Min Allowable R Squared'] = min_allowable_r_squared
            self.df_experiment.loc[self.image_name, 'Neighbour Mode'] = neighbour_mode

            for image in self.list_images:
                image['Min Required Density Ratio'] = min_required_density_ratio
                image['Max Allowable Variability'] = max_allowable_variability
                image['Neighbour Mode'] = neighbour_mode
                image['Min Allowable R Squared'] = min_allowable_r_squared
        elif setting_type == "Exit":
            self.select_square_dialog = None
        else:
            paint_logger.error(f"Unknown setting type: {setting_type}")

        self.select_squares_for_display()
        self.display_selected_squares()

        # Update the Density Ratio and Variability information in the Viewer
        info3 = f"Min Required Density Ratio: {min_required_density_ratio:,} - Max Allowable Variability: {max_allowable_variability}"
        self.text_for_info3.set(info3)

        recalc_recording_tau_and_density(self)

    def select_squares_for_display(self):
        select_squares(self, only_valid_tau=self.only_valid_tau)  # The function is in the file 'Select_Squares.py'

    def display_selected_squares(self):
        display_selected_squares(self)

    def square_assigned_to_cell(self, square_nr):
        if square_nr in self.squares_in_rectangle:
            self.squares_in_rectangle.remove(square_nr)
        else:
            self.squares_in_rectangle.append(int(square_nr))
        self.display_selected_squares()

    def provide_information_on_square(self, event, label_nr, square_nr):
        """
        Display a popup with information about a square on right-click.
        """
        # Ensure the canvas has focus
        self.left_image_canvas.focus_set()

        # Destroy the existing popup if it exists
        if self.square_info_popup:
            self.square_info_popup.destroy()
            self.square_info_popup = None

        # Define the popup
        self.square_info_popup = Toplevel(self.viewer_dialog)
        self.square_info_popup.transient(self.viewer_dialog)
        self.square_info_popup.resizable(False, False)
        self.square_info_popup.attributes('-topmost', True)
        self.square_info_popup.title("Square Info")

        # Calculate popup position based on the mouse click
        x = self.viewer_dialog.winfo_rootx() + event.x + 40
        y = self.viewer_dialog.winfo_rooty() + event.y + 40
        self.square_info_popup.geometry(f"+{x}+{y}")

        # Get the data to display from the dataframe
        self.df_squares.set_index('Square Nr', inplace=True, drop=False)
        squares_row = self.df_squares.loc[square_nr]
        self.df_squares.set_index('Unique Key', inplace=True, drop=False)

        # Define the fields to display
        if math.isnan(label_nr) or label_nr is None:
            label_nr = "-"
        else:
            label_nr = str(int(label_nr))
        fields = [
            ("Label Nr", label_nr),
            ("Square Nr", squares_row['Square Nr']),
            ("Tau", squares_row['Tau']),
            ("R Squared", squares_row['R Squared']),
            ("Density", squares_row['Density']),
            ("Number of Tracks", squares_row['Nr Tracks']),
            ("Density Ratio", squares_row['Density Ratio']),
            ("Variability", squares_row['Variability']),
            ("Max Track Duration", squares_row['Max Track Duration']),
            ("Mean Diffusion Coefficient", int(squares_row['Diffusion Coefficient']))
        ]

        # Fill the popup with labels using a loop

        for idx, (label, value) in enumerate(fields, start=1):
            ttk.Label(self.square_info_popup, text=label, anchor=W, width=20).grid(row=idx, column=1, padx=10, pady=2)
            ttk.Label(self.square_info_popup, text=str(value), anchor=W).grid(row=idx, column=2, padx=10, pady=2)

        # Bring the focus back to the root window so the canvas can detect more clicks
        self.viewer_dialog.focus_force()

    # --------------------------------------------------------------------------------------
    # User square selection rectangle functions
    # --------------------------------------------------------------------------------------

    def start_rectangle(self, event):
        self.start_x = event.x
        self.start_y = event.y
        self.rect = self.left_image_canvas.create_rectangle(
            self.start_x, self.start_y, self.start_x + 1, self.start_y + 1, fill="", outline='white')

    def expand_rectangle_size(self, event):
        # Expand rectangle as you drag the mouse
        self.left_image_canvas.coords(self.rect, self.start_x, self.start_y, event.x, event.y)

    def close_rectangle(self, event):
        # Remove the rectangle
        self.left_image_canvas.delete(self.rect)

        if self.define_cells_dialog is None:
            pass  # ToDo Maybe open the dialog here

        for i in range(len(self.df_squares)):
            square = self.df_squares.iloc[i]
            if square['Selected']:
                if test_if_square_is_in_rectangle(
                        square['X0'], square['Y0'], square['X1'], square['Y1'], self.start_x, self.start_y,
                        event.x, event.y):
                    self.squares_in_rectangle.append(int(square['Square Nr']))
        self.display_selected_squares()

    def mark_selected_squares(self):
        self.display_selected_squares()

    # --------------------------------------------------------------------------------------
    # Navigation
    # --------------------------------------------------------------------------------------

    def on_forward_backward(self, direction):
        """
        The function is called when we switch image
        """

        # ----------------------------------------------------------------------------
        # Determine what the next image is, depending on the direction
        # Be sure not move beyond the boundaries (could happen when the left and right keys are used)
        # Disable the forward and backward buttons when the boundaries are reached
        # ----------------------------------------------------------------------------

        # Determine the next image number
        if direction == 'START':
            self.img_no = 0
        elif direction == 'END':
            self.img_no = len(self.list_images) - 1
        elif direction == 'FORWARD':
            if self.img_no != len(self.list_images) - 1:
                self.img_no += 1
        elif direction == 'BACKWARD':
            if self.img_no != 0:
                self.img_no -= 1

        # Set the name of the new image
        self.image_name = self.list_images[self.img_no]['Left Image Name']

        # Save and update the Squares info
        if self.recording_changed:
            self.save_changes_on_recording_change(self)
            self.save_on_exit = True
            self.recording_changed = False
        self.df_squares = self.df_all_squares[self.df_all_squares['Ext Recording Name'] == self.image_name]

        # Set the correct state of Forward and back buttons
        if self.img_no == len(self.list_images) - 1:
            self.set_forward_backward_buttons('block_forward')
        elif self.img_no == 0:
            self.set_forward_backward_buttons('block_backward')
        else:
            self.set_forward_backward_buttons('allow_both')

        # image_name = self.list_images[self.img_no]['Left Image Name']
        self.cb_image_names.set(self.image_name)

        # ----------------------------------------------------------------------------
        # Irrespective up heatmap or normal image update the BF image, the bright field
        # and the labels can be updated
        # ----------------------------------------------------------------------------

        # Place new image_bf
        self.right_image_canvas.create_image(0, 0, anchor=NW, image=self.list_images[self.img_no]['Right Image'])
        self.lbl_image_bf_name.set(str(self.img_no + 1) + ":  " + self.list_images[self.img_no]['Right Image Name'])

        # The information labels are updated
        if self.list_images[self.img_no]['Adjuvant'] is None:
            adj_label = 'No'
        else:
            adj_label = self.list_images[self.img_no]['Adjuvant']
        cell_info = f"({self.list_images[self.img_no]['Cell Type']}) - ({adj_label}) - ({self.list_images[self.img_no]['Probe Type']}) - ({self.list_images[self.img_no]['Probe']})"
        self.text_for_info1.set(cell_info)

        info2 = f"Spots: {self.list_images[self.img_no]['Nr Spots']:,} - Threshold: {self.list_images[self.img_no]['Threshold']}"
        if self.list_images[self.img_no]['Tau'] != 0:
            info2 = f"{info2} - Tau: {int(self.list_images[self.img_no]['Tau'])}"
        self.text_for_info2.set(info2)
        # TODO: If saved, the Tau value should be displayed
        info3 = f"Min Required Density Ratio: {self.list_images[self.img_no]['Min Required Density Ratio']:,} - Max Allowable Variability: {self.list_images[self.img_no]['Max Allowable Variability']}"
        self.text_for_info3.set(info3)

        # Set the correct label for Exclude/Include button
        if self.heatmap_control_dialog is None:
            row_index = self.df_experiment.index[self.df_experiment['Ext Recording Name'] == self.image_name].tolist()[
                0]
            if self.df_experiment.loc[row_index, 'Exclude']:
                self.bn_exclude.config(text='Include')
                self.text_for_info4.set("Excluded")
            else:
                self.bn_exclude.config(text='Exclude')
                self.text_for_info4.set("")

        # If the heatmap control dialog is up display the heatmap
        if self.heatmap_control_dialog:
            self.display_heatmap()
            # And Send the heatmap control dialog a sign that min max values have changed
            self.heatmap_control_dialog.on_heatmap_global_local_change()
            return

        else:  # update the regular image

            self.left_image_canvas.create_image(0, 0, anchor=NW, image=self.list_images[self.img_no]['Left Image'])

            # Set the filter parameters with values retrieved from the experiment file
            self.min_track_duration = 0  # self.df_experiment.loc[self.image_name]['Min Duration']   # ToDo this does not look ok
            self.max_track_duration = 200  # self.df_experiment.loc[self.image_name]['Max Duration']

            self.min_required_density_ratio = self.list_images[self.img_no]['Min Required Density Ratio']
            self.max_allowable_variability = self.list_images[self.img_no]['Max Allowable Variability']
            self.min_allowable_r_squared = self.list_images[self.img_no]['Min Allowable R Squared']
            self.neighbour_mode = self.list_images[self.img_no]['Neighbour Mode']

            if self.select_square_dialog:
                self.select_square_dialog.initialise_controls(
                    self.min_required_density_ratio,
                    self.max_allowable_variability,
                    self.min_track_duration,
                    self.max_track_duration,
                    self.min_allowable_r_squared,
                    self.neighbour_mode)

        # Then display
        self.select_squares_for_display()
        if self.heatmap_control_dialog:
            self.display_heatmap()
        else:
            self.display_selected_squares()

        # Make sure that there is no user square selection left
        self.squares_in_rectangle = []
        self.mark_selected_squares()

    def save_changes_on_recording_change(self, save_experiment=True, save_squares=True):

        # Save the changes in All Squares
        self.df_squares.set_index('Unique Key', inplace=True, drop=False)
        self.df_all_squares.update(self.df_squares)

        # Update the labels in All Tracks
        df_recording_squares = self.df_squares
        df_recording_tracks = self.df_all_tracks[self.df_all_tracks['Ext Recording Name'] == self.image_name]
        dfs, dft = relabel_tracks(df_recording_squares, df_recording_tracks)
        self.df_all_tracks.update(dft)

    def save_changes_on_exit(self, save_experiment=True, save_squares=True):

        # See if there is anything to save
        if not self.save_on_exit and not self.recording_changed:
            return False

        # There is something to save, but the Never option is selected
        if self.save_state_var.get() == 'Never':
            paint_logger.debug("Changes were not saved, because the 'Never' option was selected.")
            return False

        if self.save_state_var.get() == 'Ask':
            save = self.user_confirms_save('Experiment')
        else:  # Then must be 'Always'
            save = True
        if save:
            # Save the Squares  data
            self.df_all_squares.to_csv(os.path.join(self.user_specified_directory, 'All Squares.csv'), index=False)
            self.df_all_tracks.to_csv(os.path.join(self.user_specified_directory, 'All Tracks.csv'), index=False)
            self.df_experiment.to_csv(os.path.join(self.user_specified_directory, 'All Recordings.csv'), index=False)

        return save

    def user_confirms_save(self, mode):
        """
        Ask the user if they want to save the changes
        :return: True if the user wants to save, False if not
        """
        answer = messagebox.askyesnocancel("Save Changes", f"Do you want to save the {mode} changes?")
        return answer

    # ---------------------------------------------------------------------------------------
    # Heatmap Dialog Interaction
    # ---------------------------------------------------------------------------------------

    def heatmap_type_selection_changed(self, *args):

        self.img_no -= 1
        self.on_forward_backward('FORWARD')

    def display_heatmap(self):

        # Clear the screen and reshow the picture
        self.left_image_canvas.delete("all")

        self.df_squares.set_index('Square Nr', inplace=True, drop=False)

        colors = get_colormap_colors('Blues', 20)
        heatmap_mode = self.heatmap_option.get()
        heatmap_global_min_max = self.heatmap_global_min_max.get()

        df_heatmap_data, min_val, max_val = get_heatmap_data(self.df_squares, self.df_all_squares, heatmap_mode,
                                                             heatmap_global_min_max)
        if df_heatmap_data is None:
            messagebox.showwarning("No data for heatmap", "There is no data for the heatmap")
            return

        for index, row in df_heatmap_data.iterrows():
            draw_heatmap_square(self.left_image_canvas, index, self.nr_of_squares_in_row, row['Value'],
                                min_val, max_val, colors)

    def on_heatmap_close_callback(self):

        self.df_squares.set_index('Square Nr', inplace=True, drop=False)

        self.heatmap_control_dialog = None
        self.set_dialog_buttons(tk.NORMAL)

        self.select_squares_for_display()
        self.display_selected_squares()

    # ---------------------------------------------------------------------------------------
    # Recording Selection Dialog Interaction
    # ---------------------------------------------------------------------------------------

    def on_recording_selection(self, selection, selected, filter_applied):
        # Clear the dialog reference
        self.select_recording_dialog = None

        # Return early if nothing was selected
        if not selected or not selection:
            return
        self.selected_values = selection
        self.filter_applied = filter_applied

        # Filter the list of images based on the selection criteria
        self.list_images = [
            image for image in self.saved_list_images
            if all(str(image[key]) in value for key, value in selection.items())
        ]

        # Update the combobox with the new list of image names
        self.list_of_image_names = [image['Left Image Name'] for image in self.list_images]
        self.cb_image_names['values'] = self.list_of_image_names

        if self.list_of_image_names:
            self.cb_image_names.set(self.list_of_image_names[0])  # Set to the first item if available

        # Start at the first image
        self.on_forward_backward('START')

    # ---------------------------------------------------------------------------------------
    # Utility functions
    # ---------------------------------------------------------------------------------------
    def set_forward_backward_buttons(self, mode):
        self.bn_backward.configure(state=tk.NORMAL)
        self.bn_start.configure(state=tk.NORMAL)
        self.bn_forward.configure(state=tk.NORMAL)
        self.bn_end.configure(state=tk.NORMAL)
        if mode == 'block_backward':
            self.bn_backward.configure(state=tk.DISABLED)
            self.bn_start.configure(state=tk.DISABLED)
        if mode == 'block_forward':
            self.bn_forward.configure(state=tk.DISABLED)
            self.bn_end.configure(state=tk.DISABLED)

    def set_dialog_buttons(self, state):
        self.bn_heatmap.configure(state=state)
        self.bn_define_cells.configure(state=state)
        self.bn_select_squares.configure(state=state)
        self.bn_select_recording.configure(state=state)

    def is_dialog_active(self):
        return any(dialog is not None for dialog in
                   [self.select_square_dialog,
                    self.define_cells_dialog,
                    self.heatmap_control_dialog,
                    self.select_recording_dialog])

    def show_error_and_exit(self, message):
        paint_logger.error(message)
        sys.exit()


def draw_heatmap_square(
        canvas_to_draw_on,
        square_nr,
        nr_of_squares_in_row,
        value,
        min_value,
        max_value,
        colors):
    # Calculate column, row, and square dimensions
    col_nr = square_nr % nr_of_squares_in_row
    row_nr = square_nr // nr_of_squares_in_row
    square_size = 512 / nr_of_squares_in_row

    # Determine the color index based on the value
    color_index = get_color_index(value, max_value, min_value, 20)
    color = colors[color_index]

    # Define coordinates for the rectangle
    x1 = col_nr * square_size
    y1 = row_nr * square_size
    x2 = x1 + square_size
    y2 = y1 + square_size

    # Draw the square with the selected color
    canvas_to_draw_on.create_rectangle(x1, y1, x2, y2, fill=color, outline=color)


def recalc_recording_tau_and_density(self):
    """
    Recalculate the Tau and Density values for the current recording
    """

    df_squares_for_single_tau = self.df_squares[self.df_squares['Selected']]
    df_tracks_for_reecording = self.df_all_tracks[self.df_all_tracks['Ext Recording Name'] == self.image_name]

    df_tracks_for_tau = df_tracks_for_reecording[
        df_tracks_for_reecording['Square Nr'].isin(df_squares_for_single_tau['Square Nr'])]
    df_tracks_for_tau = extra_constraints_on_tracks_for_tau_calculation(df_tracks_for_tau)

    tau, r_squared = calculate_tau(
        df_tracks_for_tau,
        # self.min_tracks_for_tau,
        10,
        self.min_allowable_r_squared)

    # Calculate the Density values
    area = calc_area_of_square(self.nr_of_squares_in_row)
    density = calculate_density(
        nr_tracks=len(df_tracks_for_tau),
        area=area,
        time=100,
        # concentration=self.concentration,   # ToDO
        concentration=10,
        magnification=1000)

    # Update the Tau and Density values in the Viewer
    self.list_images[self.img_no]['Tau'] = tau
    self.list_images[self.img_no]['Density'] = density

    self.df_experiment.loc[self.image_name, 'Tau'] = tau
    self.df_experiment.loc[self.image_name, 'Density'] = density
    self.df_experiment.loc[self.image_name, 'R Squared'] = r_squared

    # Update the Tau information in the Viewer
    info2 = f"Spots: {self.list_images[self.img_no]['Nr Spots']:,} - Threshold: {self.list_images[self.img_no]['Threshold']} - Tau: {int(tau)}"
    self.text_for_info2.set(info2)


# ---------------------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------------------


if __name__ == '__main__':
    root = tk.Tk()
    root.geometry("1x1")  # Ensure root is visible

    root = set_application_icon(root)
    root.deiconify()
    dialog = SelectViewerDataDialog(root)
    proceed, directory, mode = dialog.get_result()

    if proceed:
        # Initialize RecordingViewer without withdrawing `root`
        root.deiconify()  # Show the root window for RecordingViewer
        paint_logger.debug(f'Mode: {mode}')
        paint_logger.info(f'Mode is: {mode} - Directory: {directory}')

        # Initialize RecordingViewer, ensuring it does not create a new Tk instance
        image_viewer = RecordingViewer(root, directory, mode)
    else:
        # Hide root if not proceeding
        root.withdraw()

    root.mainloop()
