import tkinter as tk
from tkinter import ttk


class DefineCellDialog:

    # --------------------------------------------------------------
    # Setting up
    # --------------------------------------------------------------

    def __init__(self,
                 image_viewer,
                 callback_to_assign_squares_to_cell,
                 callback_to_reset_cell_definition,
                 callback_to_close_define_cells_dialog):

        # Create a new top-level window for the controls
        self.image_viewer = image_viewer
        self.callback_to_assign_squares_to_cell = callback_to_assign_squares_to_cell
        self.callback_to_reset_cell_definition = callback_to_reset_cell_definition
        self.callback_to_close_define_cells_dialog = callback_to_close_define_cells_dialog

        # Set windows properties
        self.define_cell_dialog = tk.Toplevel(self.image_viewer.viewer_dialog)
        self.define_cell_dialog.resizable(False, False)
        self.define_cell_dialog.title("Define Cells")
        self.define_cell_dialog.attributes("-topmost", True)
        self.define_cell_dialog.geometry("280x350")
        self.define_cell_dialog.resizable(False, False)
        self.define_cell_dialog.protocol("WM_DELETE_WINDOW", self.on_close)

        self.define_cell_dialog.bind('<Key>', self.on_key_pressed)

        # Set dialog focus
        # self.define_cell_dialog.grab_set()  # Prevent interaction with the main window
        # self.define_cell_dialog.focus_force()  # Bring the dialog to focus

        self.setup_userinterface()

    def setup_userinterface(self):
        """
        This function sets up the UI elements for the control window.
        Three frames are created
        """

        # Create a content frame for the control window
        self.content = ttk.Frame(self.define_cell_dialog, padding=(5, 5, 5, 5))
        self.content.grid(row=0, column=0, sticky=(tk.N, tk.S, tk.E, tk.W))

        # Create two frames for the different sections of the control window
        self.frame_cells = ttk.Frame(self.content, borderwidth=2, relief='groove', padding=(5, 5, 5, 5))
        self.frame_controls = ttk.Frame(self.content, borderwidth=2, padding=(5, 5, 5, 5))

        # Set up the UI elements for the two frames
        self.setup_frame_cells()
        self.setup_frame_controls()

        # Place the frames in the content frame
        self.frame_cells.grid(row=0, column=0, padx=5, pady=10)
        self.frame_controls.grid(row=1, column=0, padx=5, pady=10)

    def setup_frame_cells(self):
        self.cell_var = tk.IntVar(value=0)
        self.squares = []  # List to store square widgets for visual feedback

        cell_options = [
            ("Not on cell", "white", 0),
            ("On cell 1", "red", 1),
            ("On cell 2", "yellow", 2),
            ("On cell 3", "green", 3),
            ("On cell 4", "magenta", 4),
            ("On cell 5", "cyan", 5),
            ("On cell 6", "black", 6)
        ]

        for i, (text, color, value) in enumerate(cell_options):
            rb = tk.Radiobutton(self.frame_cells, text=text, variable=self.cell_var, value=value)
            rb.grid(row=i, column=0, padx=10, pady=5, sticky=tk.W)

            color_square = tk.Label(self.frame_cells, bg=color, width=2, height=1, relief="solid", borderwidth=1)
            color_square.grid(row=i, column=1, padx=10, pady=5)
            color_square.bind('<Button-1>', lambda event, val=value: self.on_square_click(val))

            rb.bind('<Button-2>', lambda e: self.on_provide_report_on_cell(e, i))
            color_square.bind('<Button-2>', lambda e, idx=i: self.on_provide_report_on_cell(e, idx))

            self.squares.append((color_square, value))  # Store square and value pair

    def on_square_click(self, value):
        """
        Handles clicks on the colored squares and updates visual feedback.
        """
        self.cell_var.set(value)
        self.update_square_highlight(value)
        self.on_assign()

    def update_square_highlight(self, selected_value):
        """
        Highlights the selected square and resets others.
        """
        for square, value in self.squares:
            if value == selected_value:
                square.config(relief="sunken", borderwidth=2)
            else:
                square.config(relief="solid", borderwidth=1)

    def setup_frame_controls(self):
        """
        Add a close button and a toggle button to the control window.
        """

        close_button = tk.Button(self.frame_controls, text="Close", command=self.on_close)
        assign_button = tk.Button(self.frame_controls, text="Assign", command=self.on_assign)
        reset_button = tk.Button(self.frame_controls, text="Reset", command=self.on_reset)

        close_button.grid(row=0, column=0, padx=5, pady=10)
        assign_button.grid(row=0, column=1, padx=5, pady=10)
        reset_button.grid(row=0, column=2, padx=5, pady=10)

    # --------------------------------------------------------------
    # Event Handlers
    # --------------------------------------------------------------

    def on_close(self):
        """
        When the user closes the control window, the Viewer dialog is notified, and the dialog is destroyed.
        """

        self.image_viewer.set_dialog_buttons(tk.NORMAL)
        self.callback_to_close_define_cells_dialog()
        self.define_cell_dialog.destroy()

    def on_assign(self):
        self.callback_to_assign_squares_to_cell(self.cell_var.get())
        pass

    def on_reset(self):
        self.callback_to_reset_cell_definition()
        pass

    def on_key_pressed(self, event):
        if event.char == 'a':
            self.on_assign()
        elif event.char == 'r':
            self.on_reset()

    def on_provide_report_on_cell(self, event, i):
        print(f"User requested report on cell {i}")
        pass

    # def provide_report_on_cell(self, _, cell_nr):
    #     """
    #     Invoked by right-clicking on a cell radio button. Only when there are actually squares defined for the cell,
    #     information will be shown, including a histogram of the Tau values
    #
    #     :param _:
    #     :param cell_nr:
    #     :return:
    #     """
    #
    #     # See if there are any squares defined for this cell
    #     df_selection = self.df_squares[self.df_squares['Cell Id'] == cell_nr]
    #     df_visible = df_selection[df_selection['Selected']]
    #     if len(df_visible) == 0:
    #         paint_logger.debug(
    #             f'There are {len(df_selection)} squares defined for cell {cell_nr}, but none are visible')
    #     else:
    #         # The labels and tau values for the visible squares of that cell are retrieved
    #         tau_values = list(df_visible['Tau'])
    #         labels = list(df_visible['Label Nr'])
    #
    #         print(f'There are {len(df_visible)} squares visible for cell {cell_nr}: {labels}')
    #         print(f'The tau values for cell {cell_nr} are: {tau_values}')
    #
    #         cell_ids = list(df_visible['Label Nr'])
    #         cell_str_ids = list(map(str, cell_ids))
    #         plt.figure(figsize=(5, 5))
    #         plt.bar(cell_str_ids, tau_values)
    #         plt.ylim(0, 500)
    #
    #         # Plot the numerical values
    #         for i in range(len(tau_values)):
    #             plt.text(cell_str_ids[i],
    #                      tau_values[i] + 10,
    #                      str(tau_values[i]),
    #                      horizontalalignment='center',
    #                      verticalalignment='center')
    #         plt.title(self.image_name + ' - Cell ' + str(cell_nr))
    #         plt.show()
    #     return
