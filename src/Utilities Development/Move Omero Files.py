import os

from tkinter import *
from tkinter import ttk, filedialog


def move_omero_files(omero_dir):
    # Loop through all Fileset directories
    dest_dir = omero_dir
    all_dirs = os.listdir(dest_dir)

    for d in all_dirs:

        # There should really be only directories named 'Fileset*****'
        # If there is something else (for example an image file already copied) ignore it
        if not os.path.isdir(os.path.join(omero_dir, d)):
            continue
        if 'Fileset_' not in d:
            continue
        src_path = os.path.join(dest_dir, d)

        # Now list all the files in a 'Fileset****' directory
        # There should be only one image file

        all_files = os.listdir(src_path)
        if len(all_files) == 0:
            print(f"Directory {d} does not contain a file.")
            continue

        for f in all_files:
            if f.startswith('._'):  # Skip the weird files
                continue
            file_to_move = os.path.join(src_path, f)
            dest_file = os.path.join(dest_dir, f)
            print(f"The file to move is {file_to_move} to {dest_file}")
            os.rename(file_to_move, dest_file)

        # Then delete the 'Fileset****' directory
        del_dir = os.path.join(dest_dir, d)
        print(f"The directory to delete is {del_dir}")
        os.rmdir(del_dir)


class MoveDialog:

    def __init__(self, root):
        root.title('Move Omero files')

        self.omero_dir = ""

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
        btn_root_dir = ttk.Button(frame_directory, text='Omero Directory', width=15, command=self.select_dir)
        self.lbl_root_dir = ttk.Label(frame_directory, text=self.omero_dir, width=50)

        btn_root_dir.grid(column=0, row=0, padx=10, pady=5)
        self.lbl_root_dir.grid(column=1, row=0, padx=20, pady=5)

    def select_dir(self):
        self.omero_dir = filedialog.askdirectory()
        if len(self.omero_dir) != 0:
            self.lbl_root_dir.config(text=self.omero_dir)

    def process(self):
        move_omero_files(self.omero_dir)

    def exit_dialog(self):
        root.destroy()


root = Tk()
root.eval('tk::PlaceWindow . center')
MoveDialog(root)
root.mainloop()
