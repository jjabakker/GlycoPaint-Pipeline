import tkinter as tk
from tkinter import ttk

from src.Application.Recording_Viewer.Heatmap_Support import (
    get_colormap_colors,
    get_heatmap_data)


class HeatMapDialog:

    # --------------------------------------------------------------
    # Setting up
    # --------------------------------------------------------------

    def __init__(self, image_viewer, on_close_heatmap_callback):

        # Create a new top-level window for the controls
        self.image_viewer = image_viewer
        self.on_close_heatmap_callback = on_close_heatmap_callback
        self.toggle = False

        # Set windows properties
        self.heatmap_dialog = tk.Toplevel(self.image_viewer.viewer_dialog)
        self.heatmap_dialog.title("Heatmap")
        self.heatmap_dialog.resizable(False, False)
        self.heatmap_dialog.geometry("370x420")
        self.heatmap_dialog.resizable(False, False)
        self.heatmap_dialog.attributes('-topmost', True)
        self.heatmap_dialog.protocol("WM_DELETE_WINDOW", self.on_close)

        self.setup_userinterface()

        # Initialise by pretending a value has been changed
        self.on_heatmap_variable_change()

        # Set dialog focus
        # self.heatmap_dialog.grab_set()  # Prevent interaction with the main window
        self.heatmap_dialog.focus_force()  # Bring the dialog to focus

    def setup_userinterface(self):
        """
        This function sets up the UI elements for the control window.
        Three frames are created.
        """

        # Create a content frame for the control window
        self.content = ttk.Frame(self.heatmap_dialog, padding=(5, 5, 5, 5))
        self.content.grid(row=0, column=0, sticky='nsew')

        # Create three frames for the different sections of the control window
        self.frame_mode_buttons = ttk.Frame(self.content, borderwidth=2, relief='groove', padding=(5, 5, 5, 5))
        self.frame_legend = ttk.Frame(self.content, borderwidth=2, relief='groove', padding=(5, 5, 5, 5))
        self.frame_controls = ttk.Frame(self.content, borderwidth=2, padding=(5, 5, 5, 5))

        # Set up the UI elements for the three frames
        self.setup_heatmap_variable_buttons()
        self.setup_legend()
        self.setup_controls()

        # Place the frames in the content frame
        self.frame_mode_buttons.grid(row=0, column=0, padx=10, pady=(10, 0), sticky='nsew')
        self.frame_legend.grid(row=0, column=1, padx=5, pady=(10, 0), sticky='nsew')
        self.frame_controls.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky='we')

        # Configure rows to ensure control frame can expand horizontally
        self.content.rowconfigure(0, weight=1)  # Top row with frames
        self.content.rowconfigure(1, weight=0)  # Control frame row does not expand

        self.heatmap_dialog.bind('<Key>', self.on_key_pressed)
        self.heatmap_dialog.bind('<Escape>', lambda event: self.on_close())

    def setup_heatmap_variable_buttons(self):
        """
        Add radio buttons for the provided option names, by cycling through the option names
        The variable that is updated is the image_viewer.heatmap_option.
        When a change occurs on_heatmap_variable_change is called.
        """

        # Add a label for radio button group
        lbl_radio = tk.Label(self.frame_mode_buttons, text="Select an Option:", font=("Arial", 12))
        lbl_radio.grid(row=2, column=0, padx=5, pady=5)

        # Add radio buttons for the provided option names
        self.option_names = ["Tau", "Density", "Diffusion Coefficient", "Track Duration", "Cum Track Duration"]
        for idx, name in enumerate(self.option_names, start=1):
            radio_btn = tk.Radiobutton(
                self.frame_mode_buttons, text=name, command=self.on_heatmap_variable_change,
                variable=self.image_viewer.heatmap_option, value=idx)
            radio_btn.grid(row=2 + idx, column=0, padx=5, pady=2, sticky=tk.W)
        self.image_viewer.heatmap_option.set(1)

        lbl_radio.grid(row=1, column=0, padx=5, pady=10)

    def setup_legend(self):
        """
        Add a legend to the control window. The legend shows the color scale of the heatmap.
        There are also two labels that show the min and max values of the heatmap.
        """

        self.canvas = tk.Canvas(self.frame_legend, width=30)

        # Add rectangles with the colors of the heatmap
        colors = get_colormap_colors('Blues', 10)
        for i, color in enumerate(colors):
            self.canvas.create_rectangle(10, 10 + i * 20, 30, 80 + i * 20, fill=color, outline=color)

        # Add labels for the min and max values of the heatmap
        self.lbl_min = tk.Label(self.frame_legend, text="", font=("Arial", 12))
        self.lbl_max = tk.Label(self.frame_legend, text="", font=("Arial", 12))

        # Add a checkbox to toggle between recording or experiment min and max values
        # Note the variable is defined in the image_viewer class
        self.image_viewer.heatmap_global_min_max.set(0)
        self.cb_global_min_max = tk.Checkbutton(
            self.frame_legend, text="Global Min/Max", variable=self.image_viewer.heatmap_global_min_max,
            command=self.on_heatmap_global_local_change)

        self.canvas.grid(row=1, column=0, rowspan=11, padx=5, pady=0)
        self.lbl_min.grid(row=0, column=0, padx=2, pady=5)
        self.lbl_max.grid(row=15, column=0, padx=2, pady=5)
        self.cb_global_min_max.grid(row=16, column=0, padx=5, pady=10)

    def setup_controls(self):
        """
        Add Close and Toggle buttons to the control window, centered within frame_controls with controlled width.
        """

        # Configure frame_controls to center its contents
        self.frame_controls.columnconfigure(0, weight=1)

        # Create a container frame to hold the buttons, which will be centered within frame_controls
        button_container = ttk.Frame(self.frame_controls)
        button_container.grid(row=0, column=0, padx=5, pady=10, sticky="n")

        # Configure two equally weighted columns in the button_container to keep buttons close
        button_container.columnconfigure(0, weight=1)
        button_container.columnconfigure(1, weight=1)

        # Create the Close and Toggle buttons with a fixed width
        close_button = tk.Button(button_container, text="Close", command=self.on_close, width=10)
        toggle_button = tk.Button(button_container, text="Toggle", command=self.on_toggle, width=10)

        # Grid the buttons in the container frame
        toggle_button.grid(row=0, column=0, padx=5, pady=5)
        close_button.grid(row=0, column=1, padx=5, pady=5)

    # --------------------------------------------------------------
    # Event Handlers
    # --------------------------------------------------------------

    def on_close(self):
        """
        When the user closes the control window, the Viewer dialog is notified, and the dialog is destroyed.
        """

        self.on_close_heatmap_callback()
        self.heatmap_dialog.destroy()

    def on_toggle(self):
        """
        If the user presses the toggle button a message is sent to the image viewer
        to toggle between the heatmap and the selected squares
        """

        if not self.toggle:
            self.image_viewer.select_squares_for_display()
            self.image_viewer.display_selected_squares()
        else:
            self.image_viewer.display_heatmap()
        self.toggle = not self.toggle

    def on_heatmap_variable_change(self):
        """
        """

        var = self.image_viewer.heatmap_option.get()
        _, min_val, max_val = get_heatmap_data(
            self.image_viewer.df_squares, self.image_viewer.df_all_squares,
            self.image_viewer.heatmap_option.get(), self.image_viewer.heatmap_global_min_max.get())

        self.lbl_min.config(text=str(min_val))
        self.lbl_max.config(text=str(max_val))
        self.image_viewer.display_heatmap()

    def on_heatmap_global_local_change(self):
        """
        """

        var = self.image_viewer.heatmap_option.get()
        _, min_val, max_val = get_heatmap_data(
            self.image_viewer.df_squares, self.image_viewer.df_all_squares, var,
            self.image_viewer.heatmap_global_min_max.get())

        self.lbl_min.config(text=str(min_val))
        self.lbl_max.config(text=str(max_val))
        self.image_viewer.display_heatmap()

    def on_key_pressed(self, event):
        """
        If the user presses the 't' key the toggle button is pressed
        """

        if event.char == 't':
            self.on_toggle()

        if event.char == 'c':
            self.on_close()
