import os
from tkinter import *
from tkinter import ttk, filedialog

import pandas as pd


def remove_min_density(root_directory):
    # Traverse the root directory and all its subdirectories
    for dirpath, dirnames, filenames in os.walk(root_directory):
        # Skip directories that contain 'Output' in their names
        if 'Output' in dirpath:
            continue

        # Define the two files you're looking for
        target_files = ['experiment_squares.csv', 'Experiment TM.csv']

        # Check each target file if it exists in the current directory
        for target_file in target_files:
            if target_file in filenames:  # Look for the exact file
                # Construct the full path to the file
                csv_path = os.path.join(dirpath, target_file)

                # Read the CSV file into a pandas DataFrame
                df_batch = pd.read_csv(csv_path, index_col=False)

                # Check if 'Min Density Ratio' column exists and remove it
                if 'Min Density Ratio' in df_batch.columns:
                    df_batch.drop(['Min Density Ratio'], axis=1, inplace=True)

                    # Save the modified DataFrame back to the CSV file or a new file
                    output_path = os.path.join(dirpath, target_file)
                    df_batch.to_csv(output_path, index=False)

                    # Print the path where the file was modified
                    print(f"Deleted column in file: {output_path}")

    print('Exited normally')


class Dialog:

    def __init__(self, root):
        root.title('Remove Min Density Ratio')

        self.root_dir = ""

        content = ttk.Frame(root)
        frame_buttons = ttk.Frame(content, borderwidth=5, relief='ridge')
        frame_directory = ttk.Frame(content, borderwidth=5, relief='ridge')

        #  Do the lay-out
        content.grid(column=0, row=0)
        frame_directory.grid(column=0, row=1, padx=5, pady=5)
        frame_buttons.grid(column=0, row=2, padx=5, pady=5)

        # Fill the button frame
        btn_process = ttk.Button(frame_buttons, text='Process', command=self.process)
        btn_exit = ttk.Button(frame_buttons, text='Exit', command=self.exit_dialog)
        btn_process.grid(column=0, row=1)
        btn_exit.grid(column=0, row=2)

        # Fill the directory frame
        btn_root_dir = ttk.Button(frame_directory, text='Root Directory', width=15, command=self.select_dir)
        self.lbl_root_dir = ttk.Label(frame_directory, text=self.root_dir, width=50)

        btn_root_dir.grid(column=0, row=0, padx=10, pady=5)
        self.lbl_root_dir.grid(column=1, row=0, padx=20, pady=5)

    def select_dir(self):
        self.root_dir = filedialog.askdirectory()
        if len(self.root_dir) != 0:
            self.lbl_root_dir.config(text=self.root_dir)

    def process(self):
        remove_min_density(self.root_dir)

    def exit_dialog(self):
        root.destroy()


root = Tk()
root.eval('tk::PlaceWindow . center')
Dialog(root)
root.mainloop()
