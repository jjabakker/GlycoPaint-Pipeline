import os
from tkinter import *
from tkinter import ttk, filedialog

import pandas as pd


def set_density_ratio(paint_directory, min_density_ratio):
    image_dirs = os.listdir(paint_directory)
    image_dirs.sort()
    for image_dir in image_dirs:
        if 'Output' in image_dir:
            continue
        if os.path.isdir(os.path.join(paint_directory, image_dir)):
            df_batch = pd.read_csv(os.path.join(paint_directory, image_dir, 'batch.csv'), index_col=False)
            if {'Min Density Ratio'}.issubset(df_batch.columns):
                print(os.path.join(paint_directory, image_dir, 'batch.csv'))
                df_batch['Min Density Ratio'] = min_density_ratio
                df_batch.to_csv(os.path.join(paint_directory, image_dir, 'batch.csv'), index=False)


class Dialog:

    def __init__(self, root):
        root.title('Set Minimum')

        self.omero_dir = ""

        content = ttk.Frame(root)
        frame_buttons = ttk.Frame(content, width=100, borderwidth=5, relief='ridge')
        frame_directory = ttk.Frame(content, width=100, borderwidth=5, relief='ridge')
        frame_parameters = ttk.Frame(content, width=100, borderwidth=5, relief='ridge')

        #  Do the lay-out
        content.grid(column=0, row=0)
        frame_directory.grid(column=0, row=1, padx=5, pady=5)
        frame_parameters.grid(column=0, row=2, padx=5, pady=5)
        frame_buttons.grid(column=0, row=3, padx=5, pady=5)

        # Fill the button frame
        btn_process = ttk.Button(frame_buttons, text='Process', command=self.process)
        btn_exit = ttk.Button(frame_buttons, text='Exit', command=self.exit_dialog)
        btn_process.grid(column=0, row=1)
        btn_exit.grid(column=0, row=2)

        # Fill the directory frame
        btn_root_dir = ttk.Button(frame_directory, text='Root Directory', width=15, command=self.select_dir)
        self.lbl_root_dir = ttk.Label(frame_directory, text=self.omero_dir, width=70)
        btn_root_dir.grid(column=0, row=0, padx=5, pady=5)
        self.lbl_root_dir.grid(column=0, row=1, padx=5, pady=5)

        # Fill the parameter frame
        lbl_min_density_ratio = ttk.Label(frame_parameters, text='Min Density Ratio', width=30, anchor=W)
        self.min_density_ratio = IntVar(root, 10)
        en_min_density_ratio = ttk.Entry(frame_parameters, textvariable=self.min_density_ratio, width=10)

        lbl_min_density_ratio.grid(column=0, row=0, padx=0, pady=5)
        en_min_density_ratio.grid(column=1, row=0, padx=0, pady=5)

        frame_buttons.pack_propagate(False)
        frame_directory.pack_propagate(False)
        frame_parameters.pack_propagate(False)

    def select_dir(self):
        self.omero_dir = filedialog.askdirectory()
        if len(self.omero_dir) != 0:
            self.lbl_root_dir.config(text=self.omero_dir)

    def process(self):
        set_density_ratio(self.omero_dir, self.min_density_ratio.get())

    def exit_dialog(self):
        root.destroy()


root = Tk()
root.eval('tk::PlaceWindow . center')
Dialog(root)
root.mainloop()
