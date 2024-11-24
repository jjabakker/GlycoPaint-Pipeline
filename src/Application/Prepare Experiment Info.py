import os
import re
from tkinter import *
from tkinter import messagebox
from tkinter import ttk, filedialog

import pandas as pd

from src.Application.Process_Projects.Convert_BF_from_nd2_to_jpg import convert_bf_images
from src.Application.Utilities.General_Support_Functions import set_application_icon
from src.Fiji.LoggerConfig import (
    paint_logger,
    paint_logger_change_file_handler_name)
from src.Fiji.PaintConfig import get_paint_attribute


def prepare_experiment_info_file(image_source_directory, experiment_directory):
    """
    This function creates a batch file in the image directory
    :return:
    """

    all_recordings = os.listdir(image_source_directory)
    all_recordings.sort()
    format_problem = False
    img_file_ext = get_paint_attribute('Paint', 'Image File Extension')

    # Check if this is a likely correct directory. There should be lots of image files
    count = 0
    count_bf = 0
    for recording_name in all_recordings:
        if recording_name.endswith(img_file_ext):
            if recording_name.find("BF") == -1:
                count += 1
            else:
                count_bf += 1

    # If there are less than 10 files, ask the user
    if count < 10:
        txt = f"There were {count + count_bf} {img_file_ext} files found, of which {count_bf} are brightfield.\n"
        txt += "\nDo you want to continue?"
        proceed = messagebox.askyesno(title=txt, message=txt)
        if not proceed:
            return

    # Prepare the df to receive the date
    df_experiment = pd.DataFrame()

    # Scan the files
    all_recordings = os.listdir(image_source_directory)
    all_recordings.sort()

    seq_nr = 1
    paint_logger.info("")

    for recording_name in all_recordings:

        # Skip files starting with .
        if recording_name.startswith(('._', '.DS')) or not recording_name.endswith(img_file_ext):
            continue

        # Check the filename format of both the film and the BF
        regexp = re.compile(
            r'(?P<exp_date>\d{6})-Exp-(?P<condition_nr>\d{1,2})-[AB][1234]-(?P<replicate_nr>\d{1,2})(-BF[1-2])?$')
        match = regexp.match(os.path.splitext(recording_name)[0])
        if match is None:
            format_problem = True
            paint_logger.info(f"Image name: {recording_name} is not in the expected format")
            condition_nr = ""
            replicate_nr = ""
            exp_date = ""
        else:
            condition_nr = match.group('condition_nr')
            replicate_nr = match.group('replicate_nr')
            exp_date = match.group('exp_date')

        # For further processing, skip the BF file
        if recording_name.find("BF") != -1:
            continue

        paint_logger.info(f'Processing file: {recording_name}')

        recording_name = recording_name.replace(img_file_ext, "")

        row = {'Recording Sequence Nr': seq_nr,
               'Recording Name': recording_name,
               'Experiment Date': exp_date,
               'Experiment Name': exp_date,
               'Condition Nr': condition_nr,
               'Replicate Nr': replicate_nr,
               'Probe': '',
               'Probe Type': '',
               'Cell Type': '',
               'Adjuvant': '',
               'Concentration': '',
               'Threshold': '',
               'Process': 'Yes',
               }
        df_experiment = pd.concat([df_experiment, pd.DataFrame.from_records([row])])
        seq_nr += 1

    # Now write the file, but only if there is data
    if len(df_experiment) == 0:
        paint_logger.info('No images were found. You have probably selected an incorrect directory.')
        paint_logger.info('No batch file was written.')
    else:
        df_experiment.to_csv(os.path.join(experiment_directory, "experiment_info.csv"), index=False)
        if format_problem:
            paint_logger.info('')
            paint_logger.info(
                f"There were filenames not in the expected format (\\d{6})-Exp-\\d{1, 2}-[AB][1234]-(\\d{1, 2})")
            paint_logger.info(
                "Please supply values for Experiment Date, Condition Nr, Replicate Nr yourself.")
        paint_logger.info('')
        paint_logger.info(f"Process finished normally with {seq_nr - 1} images processed.")

    convert_bf_images(image_source_directory, experiment_directory, force=False)

    paint_logger.info('')
    paint_logger.info(
        "Don't forget to edit the experiment file to specify correct values for Probe, Probe type, Cell Type, Adjuvant and concentration.")
    paint_logger.info("Then choose the threshold values and select which images needs processing.")


if __name__ == '__main__':

    class BatchDialog:

        def __init__(self, _root):
            _root.title('Prepare Experiments Info')

            self.image_directory = ""
            self.paint_directory = ""

            content = ttk.Frame(_root)
            frame_buttons = ttk.Frame(content, borderwidth=5, relief='ridge')
            frame_directory = ttk.Frame(content, borderwidth=5, relief='ridge')

            #  Do the lay-out
            content.grid(column=0, row=0)
            frame_directory.grid(column=0, row=1, padx=5, pady=5)
            frame_buttons.grid(column=0, row=2, padx=5, pady=5)

            # Fill the button frame
            btn_prepare = ttk.Button(frame_buttons, text='Prepare', command=self.on_prepare_pressed)
            btn_exit = ttk.Button(frame_buttons, text='Exit', command=self.on_exit_pressed)
            btn_prepare.grid(column=0, row=1)
            btn_exit.grid(column=0, row=2)

            # Fill the directory frame
            btn_image_dir = ttk.Button(frame_directory, text='Image Source Directory', width=20,
                                       command=self.change_image_dir)
            self.lbl_image_dir = ttk.Label(frame_directory, text=self.image_directory, width=50)

            btn_paint_dir = ttk.Button(frame_directory, text='Experiment Directory', width=20,
                                       command=self.change_paint_dir)
            self.lbl_paint_dir = ttk.Label(frame_directory, text=self.paint_directory, width=50)

            btn_image_dir.grid(column=0, row=0, padx=10, pady=5)
            self.lbl_image_dir.grid(column=1, row=0, padx=20, pady=5)

            btn_paint_dir.grid(column=0, row=1, padx=10, pady=5)
            self.lbl_paint_dir.grid(column=1, row=1, padx=20, pady=5)

        def change_image_dir(self):
            self.image_directory = filedialog.askdirectory(initialdir=self.image_directory)
            if len(self.image_directory) != 0:
                self.lbl_image_dir.config(text=self.image_directory)

        def change_paint_dir(self):
            self.paint_directory = filedialog.askdirectory(initialdir=self.paint_directory)
            if len(self.paint_directory) != 0:
                self.lbl_paint_dir.config(text=self.paint_directory)

        def on_prepare_pressed(self):
            if self.image_directory == "" or self.paint_directory == "":
                message = 'The image directory needs to point to where the images are.\n\n'
                message += 'The experiment directory is where the experiment_info.csv will be placed.'
                messagebox.showwarning(title='Warning', message=message)
            else:
                convert_bf_images(self.image_directory, self.paint_directory)
                prepare_experiment_info_file(self.image_directory, self.paint_directory)
                self.on_exit_pressed()

        def on_exit_pressed(self):
            root.destroy()


    paint_logger_change_file_handler_name('Prepare Experiment_Info File.log')

    root = Tk()
    root = set_application_icon(root)
    root.eval('tk::PlaceWindow . center')
    BatchDialog(root)
    root.mainloop()
