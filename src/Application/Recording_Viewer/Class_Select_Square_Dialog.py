import tkinter as tk
from tkinter import ttk


class SelectSquareDialog:

    # --------------------------------------------------------------------------------------------------------
    # Setting up
    # --------------------------------------------------------------------------------------------------------

    def __init__(self, image_viewer, callback_update_select_squares, min_required_density_ratio,
                 max_allowable_variability, min_track_duration, max_track_duration, min_allowable_r_squared,
                 neighbour_mode):
        """
        The callback function that is called is self.update_select_squares
        """

        # Create a new top-level window
        self.image_viewer = image_viewer
        self.callback = callback_update_select_squares  # This is the callback function the UI calls when the sliders are changed

        self.min_required_density_ratio = None
        self.max_allowable_variability = None
        self.min_track_duration = None
        self.max_track_duration = None
        self.min_allowable_r_squared = None
        self.neighbour_mode = None

        # Set window properties
        self.select_square_dialog = tk.Toplevel(self.image_viewer.viewer_dialog)
        self.select_square_dialog.title("Select Squares")
        self.select_square_dialog.attributes("-topmost", True)
        self.select_square_dialog.resizable(False, False)
        self.select_square_dialog.attributes('-topmost', True)
        self.select_square_dialog.protocol("WM_DELETE_WINDOW", self.on_close)

        # Set up the user interface
        self.setup_userinterface()

        # Set dialog focus
        # self.select_square_dialog.grab_set()  # Prevent interaction with the main window
        self.select_square_dialog.focus_force()  # Bring the dialog to focus

        # Initialise the controls
        self.initialise_controls(
            min_required_density_ratio,
            max_allowable_variability,
            min_track_duration,
            max_track_duration,
            min_allowable_r_squared,
            neighbour_mode)

    def setup_userinterface(self):
        # Set up the content frame
        self.content = ttk.Frame(self.select_square_dialog, padding=(5, 5, 5, 5))
        self.content.grid(row=0, column=0, sticky=(tk.N, tk.S, tk.E, tk.W))

        # There are two frames in the content frame, one for the filters and one for the exit buttons
        self.frame_filter = ttk.Frame(self.content, borderwidth=2, relief='groove', padding=(5, 5, 5, 5))

        # Set up the frames
        self.setup_frame_filter()

        # Place the frames in the content frame
        self.frame_filter.grid(row=0, column=0, sticky=(tk.N, tk.S, tk.E, tk.W))

    def setup_frame_filter(self):
        # Create frames for the sliders
        self.frame_min_required_density_ratio = ttk.Frame(self.frame_filter, borderwidth=1, relief='groove',
                                                          padding=(5, 5, 5, 5))
        self.frame_max_allowable_variability = ttk.Frame(self.frame_filter, borderwidth=1, relief='groove',
                                                         padding=(5, 5, 5, 5))
        self.frame_min_duration = ttk.Frame(self.frame_filter, borderwidth=1, relief='groove', padding=(5, 5, 5, 5))
        self.frame_max_duration = ttk.Frame(self.frame_filter, borderwidth=1, relief='groove', padding=(5, 5, 5, 5))
        self.frame_min_allowable_r_squared = ttk.Frame(self.frame_filter, borderwidth=1, relief='groove',
                                                       padding=(5, 5, 5, 5))
        self.frame_neighbours = ttk.Frame(self.frame_filter, borderwidth=1, relief='groove', padding=(5, 5, 5, 5))

        # Set up each filter
        self.setup_frame_minimum_required_density_ratio()
        self.setup_frame_max_allowable_variability()
        self.setup_min_duration()
        self.setup_max_duration()
        self.setup_frame_min_allowable_r_squared()
        self.setup_frame_neighbours()

        # Place all frames in a single row for horizontal alignment
        self.frame_min_required_density_ratio.grid(column=0, row=0, padx=5, pady=5, sticky=(tk.N, tk.S, tk.E, tk.W))
        self.frame_max_allowable_variability.grid(column=1, row=0, padx=5, pady=5, sticky=(tk.N, tk.S, tk.E, tk.W))
        self.frame_min_duration.grid(column=2, row=0, padx=5, pady=5, sticky=(tk.N, tk.S, tk.E, tk.W))
        self.frame_max_duration.grid(column=3, row=0, padx=5, pady=5, sticky=(tk.N, tk.S, tk.E, tk.W))
        self.frame_min_allowable_r_squared.grid(column=4, row=0, padx=5, pady=5, sticky=(tk.N, tk.S, tk.E, tk.W))
        self.frame_neighbours.grid(column=5, row=0, padx=5, pady=5, sticky=(tk.N, tk.S, tk.E, tk.W))

        # Add buttons below the sliders, spanning all columns
        self.frame_buttons = ttk.Frame(self.frame_filter, borderwidth=1, padding=(5, 5, 5, 5))
        self.setup_frame_buttons()
        self.frame_buttons.grid(column=0, row=1, columnspan=5, padx=5, pady=5, sticky=(tk.N, tk.S, tk.E, tk.W))

        # Configure equal column weights to make frames equally wide
        self.frame_filter.columnconfigure(0, weight=1)
        self.frame_filter.columnconfigure(1, weight=1)
        self.frame_filter.columnconfigure(2, weight=1)
        self.frame_filter.columnconfigure(3, weight=1)
        self.frame_filter.columnconfigure(4, weight=1)
        self.frame_filter.columnconfigure(5, weight=1)

    def setup_frame_buttons(self):
        # Create buttons
        bn_set_neighbours_all = tk.Button(self.frame_buttons, text="Set for All", command=self.on_set_for_all, width=12)
        bn_ok = tk.Button(self.frame_buttons, text="OK", command=self.on_close, width=12)

        # Frame layout for buttons
        button_frame = ttk.Frame(self.frame_buttons)
        button_frame.grid(column=0, row=0, padx=5, pady=5, sticky=tk.N)

        # Place buttons side by side with minimal spacing
        bn_set_neighbours_all.grid(column=0, row=0, padx=(0, 5), pady=5)  # Right padding only
        bn_ok.grid(column=1, row=0, padx=(5, 0), pady=5)  # Left padding only

        # Configure button frame to center its contents tightly
        button_frame.columnconfigure(0, weight=0)  # No expansion for button 1
        button_frame.columnconfigure(1, weight=0)  # No expansion for button 2

        # Configure parent frame to center the button_frame
        self.frame_buttons.columnconfigure(0, weight=1)

    def setup_frame_max_allowable_variability(self):
        """
        Create a scale for the variability.
        The moment that the slider button is released, the variability_changed function is called.
        The value of the slider is stored in the variability variable
        """

        self.max_allowable_variability = tk.DoubleVar(value=self.max_allowable_variability)
        self.lbl_max_allowable_variability_text = ttk.Label(self.frame_max_allowable_variability,
                                                            text='Max Allowable\nVariability')
        self.sc_max_allowable_variability = tk.Scale(self.frame_max_allowable_variability, from_=1.5, to=10,
                                                     variable=self.max_allowable_variability,
                                                     orient='vertical', resolution=0.5)
        self.sc_max_allowable_variability.bind("<ButtonRelease-1>",
                                               lambda event: self.on_filter_changed('Max Allowable Variability'))
        self.lbl_max_allowable_variability_text.grid(column=0, row=0, padx=5, pady=5)
        self.sc_max_allowable_variability.grid(column=0, row=1, padx=5, pady=5, sticky=tk.W + tk.E)

    def setup_frame_minimum_required_density_ratio(self):
        """
        Create a scale for the Minimum Required Density Ratio.
        The moment that the slider button is released, the density_ratio_changed function is called.
        The value of the slider is stored in the self.density_ratio variable
        """

        self.min_required_density_ratio = tk.DoubleVar(value=self.min_required_density_ratio)
        self.lbl_min_required_density_ratio_text = ttk.Label(
            self.frame_min_required_density_ratio, text='Min Required\nDensity Ratio', width=10)
        self.sc_min_required_density_ratio = tk.Scale(
            self.frame_min_required_density_ratio, from_=1, to=200, variable=self.min_required_density_ratio,
            orient='vertical', resolution=1)
        self.sc_min_required_density_ratio.bind("<ButtonRelease-1>",
                                                lambda event: self.on_filter_changed('Min Required Density Ratio'))
        self.lbl_min_required_density_ratio_text.grid(column=0, row=0, padx=5, pady=5)
        self.sc_min_required_density_ratio.grid(column=0, row=1, padx=5, pady=5, sticky=tk.W + tk.E)

    def setup_min_duration(self):
        """
        Create a scale for the Minimum Track Duration.
        The moment that the slider button is released, the track_duration_changed function is called.
        The value of the slider is stored in the self.track_min_duration variable
        """

        self.min_track_duration = tk.DoubleVar(value=self.min_track_duration)
        self.lbl_min_track_duration_text = ttk.Label(self.frame_min_duration, text='Min Longest\nTrack Duration',
                                                     width=10)
        self.sc_min_track_duration = tk.Scale(
            self.frame_min_duration, from_=0, to=200, variable=self.min_track_duration, orient='vertical',
            resolution=0.1)
        self.sc_min_track_duration.bind("<ButtonRelease-1>", lambda event: self.on_filter_changed('Min Track Duration'))
        self.lbl_min_track_duration_text.grid(row=0, column=0, padx=5, pady=5, sticky=tk.W + tk.E)
        self.sc_min_track_duration.grid(row=1, column=0, padx=5, pady=5, sticky=tk.W + tk.E)

    def setup_max_duration(self):
        """
        Create a scale for the Maximum Track Duration.
        The moment that the slider button is released, the track_duration_changed function is called.
        The value of the slider is stored in the self.track_max_duration variable
        """

        self.max_track_duration = tk.DoubleVar(value=self.max_track_duration)
        self.lbl_max_track_duration_text = ttk.Label(self.frame_max_duration, text='Max Longest\nTrack Duration',
                                                     width=10)
        self.sc_max_track_duration = tk.Scale(
            self.frame_max_duration, from_=0, to=200, variable=self.max_track_duration, orient='vertical',
            resolution=0.1)
        self.sc_max_track_duration.bind("<ButtonRelease-1>", lambda event: self.on_filter_changed('Max Track Duration'))

        self.lbl_max_track_duration_text.grid(row=0, column=0, padx=5, pady=5, sticky=tk.W + tk.E)
        self.sc_max_track_duration.grid(row=1, column=0, padx=5, pady=5, sticky=tk.W + tk.E)

    def setup_frame_min_allowable_r_squared(self):
        """
        Create a scale for a min r squared slider.

        """
        self.min_allowable_r_squared = tk.DoubleVar(value=0.9)  # Default value
        self.lbl_min_allowable_r_squared_text = ttk.Label(self.frame_min_allowable_r_squared, text='Min\nR Squared',
                                                          width=10)
        self.sc_min_allowable_r_squared = tk.Scale(
            self.frame_min_allowable_r_squared, from_=0, to=1.0, variable=self.min_allowable_r_squared,
            orient='vertical', resolution=0.01)
        self.sc_min_allowable_r_squared.bind("<ButtonRelease-1>",
                                             lambda event: self.on_filter_changed('Min Allowable R Squared'))

        self.lbl_min_allowable_r_squared_text.grid(column=0, row=0, padx=5, pady=5)
        self.sc_min_allowable_r_squared.grid(column=0, row=1, padx=5, pady=5)

    def setup_frame_neighbours(self):
        # Create a label for the neighbour mode
        self.rb_neighbour_label = ttk.Label(self.frame_neighbours, text="Neighbour\nMode", width=10)

        # Create three radio buttons for the neighbour mode
        self.neighbour_mode = tk.StringVar(value="")
        self.rb_neighbour_free = tk.Radiobutton(
            self.frame_neighbours, text="Free", variable=self.neighbour_mode, width=10, value="Free",
            command=lambda: self.on_filter_changed('Neighbour Mode'), anchor=tk.W)
        self.rb_neighbour_strict = tk.Radiobutton(
            self.frame_neighbours, text="Strict", variable=self.neighbour_mode, value="Strict",
            command=lambda: self.on_filter_changed('Neighbour Mode'), anchor=tk.W)
        self.rb_neighbour_relaxed = tk.Radiobutton(
            self.frame_neighbours, text="Relaxed", variable=self.neighbour_mode, value="Relaxed",
            command=lambda: self.on_filter_changed('Neighbour Mode'), anchor=tk.W)

        # Place the radio buttons and button in the grid
        self.rb_neighbour_label.grid(column=0, row=0, padx=5, pady=5, sticky=tk.W)
        self.rb_neighbour_free.grid(column=0, row=1, padx=5, pady=5, sticky=tk.W)
        self.rb_neighbour_relaxed.grid(column=0, row=2, padx=5, pady=5, sticky=tk.W)
        self.rb_neighbour_strict.grid(column=0, row=3, padx=5, pady=5, sticky=tk.W)

    # --------------------------------------------------------------------------------------------------------
    # Event Handlers
    # --------------------------------------------------------------------------------------------------------

    def on_filter_changed(self, changed_slider):
        """
        Notify the main window about the track duration change, using the callback function provided by the
        Image Viewer (update_select_squares)
        """

        self.callback(
            changed_slider,
            self.sc_min_required_density_ratio.get(),
            self.sc_max_allowable_variability.get(),
            self.sc_min_track_duration.get(),
            self.sc_max_track_duration.get(),
            self.sc_min_allowable_r_squared.get(),
            self.neighbour_mode.get())

    def on_set_for_all(self):
        self.callback("Set for All",
                      self.sc_min_required_density_ratio.get(),
                      self.sc_max_allowable_variability.get(),
                      self.sc_min_track_duration.get(),
                      self.sc_max_track_duration.get(),
                      self.min_allowable_r_squared.get(),
                      self.neighbour_mode.get())
        pass

    def on_close(self):
        """
        Set the radio button to an invalid value of -1 and destroy the window
        The callback function (update_select_squares) is called in the ImageViewer dialog
        """

        self.image_viewer.update_select_squares(
            "Exit",
            self.sc_min_required_density_ratio.get(),
            self.sc_max_allowable_variability.get(),
            self.sc_min_track_duration.get(),
            self.sc_max_track_duration.get(),
            self.sc_min_allowable_r_squared.get(),
            self.neighbour_mode.get())
        self.image_viewer.set_dialog_buttons(tk.NORMAL)
        self.select_square_dialog.destroy()

    # --------------------------------------------------------------------------------------------------------
    # Information from the Image Viewer
    # --------------------------------------------------------------------------------------------------------

    def initialise_controls(
            self,
            min_required_density_ratio,
            max_allowable_variability,
            min_track_duration,
            max_track_duration,
            min_allowable_r_squared,
            neighbour_mode):
        # Set the sliders to the initial values
        self.min_required_density_ratio.set(min_required_density_ratio)
        self.max_allowable_variability.set(max_allowable_variability)
        self.min_track_duration.set(min_track_duration)
        self.max_track_duration.set(max_track_duration)
        self.min_allowable_r_squared.set(min_allowable_r_squared)
        self.neighbour_mode.set(neighbour_mode)
