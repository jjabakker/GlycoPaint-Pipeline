import tkinter as tk
from tkinter import ttk

import pandas as pd


def disable_button(button):
    """Disable the button and apply the custom disabled style."""
    button.state(["disabled"])

def enable_button(button):
    """Enable the button and restore the normal style."""
    button.state(["!disabled"])

class SelectRecordingDialog():

    def __init__(self, image_viewer, df_experiment, callback, selected_values=None, filter_applied=None):

        self.image_viewer = image_viewer

        # Set windows properties
        self.select_recording_dialog = tk.Toplevel(self.image_viewer.viewer_dialog)
        self.select_recording_dialog.title("Select Recordings")
        self.select_recording_dialog.attributes("-topmost", True)
        self.select_recording_dialog.resizable(False, False)
        self.select_recording_dialog.protocol("WM_DELETE_WINDOW", self.on_cancel)

        # For this dialog, it is not important to have access to the parent window
        self.select_recording_dialog.grab_set()  # Prevent interaction with the main window
        self.select_recording_dialog.focus_force()  # Bring the dialog to focus

        self.df = df_experiment.copy()
        self.callback = callback

        # Only filter on these specific columns
        self.filter_columns = ['Probe Type', 'Probe', 'Cell Type', 'Adjuvant', 'Concentration']

        # Make 'Concentration' a string type
        self.df['Concentration'] = self.df['Concentration'].astype(str)

        # Store original unique values for reset functionality
        self.original_values = {col: sorted(self.df[col].unique()) for col in self.filter_columns}

        # Restore previous selections or initialize with empty selections
        self.selected_values = selected_values if selected_values else {col: [] for col in self.filter_columns}
        self.filter_applied = filter_applied if filter_applied else {col: False for col in self.filter_columns}

        self.df_filtered = self.df.copy()
        for col in self.filter_applied:
            if self.filter_applied[col]:
                self.df_filtered = self.df_filtered[self.df_filtered[col].isin(self.selected_values[col])]

        self.setup_userinterface()



    def setup_userinterface(self):
        # Frame to hold list boxes and buttons
        content = ttk.Frame(self.select_recording_dialog, padding="10")
        content.grid(row=0, column=0, sticky="NSEW")

        self.reset_buttons = {}
        self.listboxes = {}  # Listboxes for each column
        self.filtered_df = self.df.copy()  # DataFrame to store the filtered results

        # Generate a listbox, filter button, and reset button for each column
        for i, col in enumerate(self.filter_columns):
            # Label for the column name
            ttk.Label(content, text=col).grid(row=0, column=i, padx=5, sticky="W")

            # Create a listbox with multiple selection mode
            listbox = tk.Listbox(content, height=6, width=15, selectmode=tk.MULTIPLE)
            listbox.grid(row=1, column=i, padx=5, pady=5)
            self.listboxes[col] = listbox

            # Populate listbox with all unique values from the column
            self.populate_listbox(col)

            # Create a filter button below the listbox
            filter_button = ttk.Button(content, text="Filter", command=lambda c=col: self.apply_filter(c))
            filter_button.grid(row=2, column=i, padx=(5, 2), pady=(5, 2), sticky="EW")

            # Create a reset button below the filter button

            # Create a custom style
            style = ttk.Style()
            style.configure("Custom.TButton",
                            font=("Helvetica", 14),
                            padding=10)
            style.map("Custom.TButton",
                      background=[("disabled", "lightgray")],  # Background when disabled
                      foreground=[("disabled", "gray")])  # Text color when disabled

            reset_button = ttk.Button(content, text="Reset", style="Custom.TButton", command=lambda c=col: self.reset_filter(c))
            reset_button.grid(row=3, column=i, padx=(5, 2), pady=(2, 5), sticky="EW")
            disable_button(reset_button)
            self.reset_buttons[col] = reset_button

        # Buttons to reset all, apply all, and cancel at the bottom center
        button_frame = ttk.Frame(content)  # Frame for the buttons
        button_frame.grid(row=4, column=0, columnspan=len(self.filter_columns), pady=10)

        reset_all_button = ttk.Button(button_frame, text="Reset All", command=self.reset_all_filters)
        reset_all_button.pack(side=tk.LEFT, padx=5)

        confirm_button = ttk.Button(button_frame, text="Apply All Filters", command=self.apply_all_filters)
        confirm_button.pack(side=tk.LEFT, padx=5)

        cancel_button = ttk.Button(button_frame, text="Cancel", command=self.on_cancel)
        cancel_button.pack(side=tk.LEFT, padx=5)

    def reset_filter(self, col):
        """ Clear the selection and restore original values for a specific column. """
        listbox = self.listboxes[col]
        listbox.selection_clear(0, tk.END)  # Clear current selections
        self.populate_listbox(col)  # Restore original values for this column

        self.selected_values[col] = []  # Clear selected values for this column
        self.filter_applied[col] = False

        self.filtered_df = self.df.copy()
        for c, lb in self.listboxes.items():
            selected_values = self.selected_values[c]
            if selected_values:
                # self.filtered_df = self.filtered_df[self.df[c].isin(selected_values)]
                self.filtered_df = self.filtered_df[self.filtered_df[c].isin(selected_values)]

        # Update each listbox with filtered unique values
        for c, lb in self.listboxes.items():
            current_values = sorted(self.filtered_df[c].unique())
            lb.delete(0, tk.END)  # Clear existing values
            for value in current_values:
                lb.insert(tk.END, value)

        disable_button(self.reset_buttons[col])


    def populate_listbox(self, col):
        """ Populate the listbox with original unique values from the column. """
        listbox = self.listboxes[col]
        listbox.delete(0, tk.END)  # Clear existing values
        if self.selected_values[col]:
            for value in self.selected_values[col]:
                listbox.insert(tk.END, value)
        else:
            for value in self.original_values[col]:
                listbox.insert(tk.END, value)

    def reset_all_filters(self):
        """ Clear all selections in all listboxes and restore their content. """
        for col in self.filter_columns:
            self.listboxes[col].selection_clear(0, tk.END)  # Clear selections
            self.selected_values[col] = []  # Clear selected values
            self.populate_listbox(col)  # Restore original values
            self.filter_applied[col] = False

        self.filtered_df = self.df.copy()  # Reset the filtered DataFrame

    def apply_filter(self, col):
        """ Apply filter based on selected values in the specified listbox. """
        listbox = self.listboxes[col]
        selected_values = [listbox.get(i) for i in listbox.curselection()]
        self.selected_values[col] = selected_values
        self.filter_applied[col] = True

        if selected_values:
            # Trigger filtering when the button is pressed
            filtered_df = self.df[self.df[col].isin(selected_values)]

            # Update the filtered DataFrame with the current filter
            self.filtered_df = self.filtered_df[self.filtered_df[col].isin(selected_values)]

            # Update each listbox with filtered unique values
            for c, lb in self.listboxes.items():
                current_values = sorted(self.filtered_df[c].unique())
                lb.delete(0, tk.END)  # Clear existing values
                for value in current_values:
                    lb.insert(tk.END, value)

        enable_button(self.reset_buttons[col])

    def apply_all_filters(self):
        """ Collect selected values for all listboxes and apply filters. """
        selected_filters = {}
        for col, listbox in self.listboxes.items():
            count = listbox.size()
            current_values = [listbox.get(i) for i in range(count)]
            if current_values:
                selected_filters[col] = current_values

        # Pass the selected filters to the main window through the callback
        self.callback(selected_filters, True, self.filter_applied)

        # Close the dialog
        self.select_recording_dialog.destroy()

    def on_cancel(self):
        """ Close the dialog without applying any filters. """
        self.callback(None, False, self.filter_applied)
        self.select_recording_dialog.destroy()


if __name__ == "__main__":
    # Sample DataFrame with example data
    data = {
        'Probe Type': ['Type1', 'Type2', 'Type1', 'Type3', 'Type2'],
        'Probe': ['A', 'B', 'A', 'C', 'B'],
        'Cell Type': ['X', 'Y', 'X', 'Z', 'Y'],
        'Adjuvant': ['Adj1', 'Adj2', 'Adj1', 'Adj3', 'Adj2'],
        'Concentration': [1, 2, 1, 3, 2]
    }
    df = pd.DataFrame(data)


    class MainWindow(tk.Tk):
        def __init__(self):
            super().__init__()
            self.title("Main Window")

            # Button to open filter dialog
            open_dialog_button = ttk.Button(self, text="Open Filter Dialog", command=self.open_filter_dialog)
            open_dialog_button.pack(pady=20)

            # Label to display filter results
            self.result_label = ttk.Label(self, text="Filtered Data: None")
            self.result_label.pack(pady=20)

        def open_filter_dialog(self):
            # Open the filter dialog and pass a callback to receive the data
            SelectRecordingDialog(self, df, self.on_filter_applied)

        def on_filter_applied(self, selected_filters):
            # Display the selected filters
            filter_text = ", ".join(f"{k}: {v}" for k, v in selected_filters.items())
            self.result_label.config(text=f"Filtered Data: {filter_text}")


    main_app = MainWindow()
    main_app.mainloop()
