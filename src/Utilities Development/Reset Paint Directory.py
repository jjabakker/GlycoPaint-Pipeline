import os
import shutil
from tkinter import *
from tkinter import ttk, filedialog, messagebox

from src.Application.Utilities.ToolTips import ToolTip


def reset_root(root_dir):
    files_to_remove = ['All Recordings.csv', 'All Squares.csv', 'All Tracks.csv',
                       'Experiment TM.csv']  # Add file names you want to remove
    directories_to_remove = ['Brightfield Images', 'TrackMate Images']  # Add directory names you want to remove

    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Remove specified files
        for file in filenames:
            if file in files_to_remove:
                file_path = os.path.join(dirpath, file)
                try:
                    os.remove(file_path)
                    print(f"Deleted file {file_path}")
                except Exception as e:
                    print(f"Failed to delete file {file_path}: {e}")

        # Remove specified directories
        for directory in dirnames[:]:  # Copy list to avoid modifying during iteration
            if directory in directories_to_remove:
                dir_path = os.path.join(dirpath, directory)
                try:
                    shutil.rmtree(dir_path)
                    print(f"Deleted directory {dir_path}")
                except Exception as e:
                    print(f"Failed to delete directory {dir_path}: {e}")


class Dialog:

    def __init__(self, _root):
        _root.title('Reset Root Directory')
        self.root_dir = ""

        content = ttk.Frame(_root)
        frame_buttons = ttk.Frame(content, borderwidth=5, relief='ridge')
        frame_directory = ttk.Frame(content, borderwidth=5, relief='ridge')

        # Layout
        content.grid(column=0, row=0, padx=10, pady=10)
        frame_directory.grid(column=0, row=1, padx=5, pady=5)
        frame_buttons.grid(column=0, row=2, padx=5, pady=5)

        # Fill button frame
        self.btn_process = ttk.Button(frame_buttons, text='Reset', command=self.process, state='disabled')
        btn_exit = ttk.Button(frame_buttons, text='Exit', command=self.exit_dialog)
        self.btn_process.grid(column=0, row=1)
        btn_exit.grid(column=0, row=2)

        tooltip = "This will delete specified files and directories in the selected directory tree."
        ToolTip(self.btn_process, tooltip, wraplength=400)

        # Fill directory frame
        btn_root_dir = ttk.Button(frame_directory, text='Root Directory', width=15, command=self.select_dir)
        self.lbl_root_dir = ttk.Label(frame_directory, text=self.root_dir, width=50)

        btn_root_dir.grid(column=0, row=0, padx=10, pady=5)
        self.lbl_root_dir.grid(column=1, row=0, padx=20, pady=5)

    def select_dir(self):
        self.root_dir = filedialog.askdirectory()
        if self.root_dir:
            self.lbl_root_dir.config(text=self.root_dir)
            self.btn_process.config(state='normal')  # Enable Reset button

    def process(self):
        confirm = messagebox.askyesno(
            "Confirm Reset",
            "Are you sure you want to delete specified files and directories in the selected directory tree?"
        )
        if confirm:
            reset_root(self.root_dir)

    def exit_dialog(self):
        root.destroy()


root = Tk()
root.eval('tk::PlaceWindow . center')
Dialog(root)
root.mainloop()
