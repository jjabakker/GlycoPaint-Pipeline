import os
import sys
from tkinter import *

from PIL import Image, ImageTk

from src.Fiji.LoggerConfig import paint_logger


def get_images(self, initial=False):
    """
    Retrieve the images to be displayed (for the left and right frame) from disk.
    A list with all necessary attributes for each image is created.
    """

    list_images = []
    error_count = 0

    for index, experiment_row in self.df_experiment.iterrows():
        ext_recording_name = experiment_row['Ext Recording Name']
        recording_name = experiment_row['Recording Name']
        experiment = str(experiment_row['Experiment Name'])

        try:
            left_image_dir = os.path.join(
                self.user_specified_directory,
                'TrackMate Images' if self.user_specified_mode == 'Experiment' else os.path.join(experiment,
                                                                                                 'TrackMate Images')
            )
            left_img = ImageTk.PhotoImage(Image.open(os.path.join(left_image_dir, ext_recording_name + '.jpg')))
            valid = True
        except:
            valid = False
            left_img = Image.new('RGB', (512, 512), "rgb(235,235,235)")
            left_img = ImageTk.PhotoImage(left_img)
            error_count += 1

        # Retrieve Tau from the experiments_squares file, defaults to 0
        tau = experiment_row['Tau'] if 'Tau' in experiment_row else 0

        # Find the corresponding BF
        bf_image_dir = os.path.join(
            self.user_specified_directory,
            'Brightfield Images' if self.user_specified_mode == 'Experiment' else os.path.join(experiment,
                                                                                               'Brightfield Images')
        )
        right_valid, right_img = get_corresponding_bf(bf_image_dir, ext_recording_name, recording_name)

        record = {
            "Left Image Name": experiment_row['Ext Recording Name'],
            "Left Image": left_img,
            "Left Valid": valid,

            "Right Image Name": ext_recording_name,
            "Right Image": right_img,
            "Right Valid": right_valid,

            "Cell Type": experiment_row['Cell Type'],
            "Adjuvant": experiment_row['Adjuvant'],
            "Probe": experiment_row['Probe'],
            "Probe Type": experiment_row['Probe Type'],
            "Concentration": experiment_row['Concentration'],

            "Threshold": experiment_row['Threshold'],
            "Nr Spots": int(experiment_row['Nr Spots']),
            "Min Required Density Ratio": experiment_row['Min Required Density Ratio'],
            "Max Allowable Variability": experiment_row['Max Allowable Variability'],
            "Min Allowable R Squared": experiment_row['Min Allowable R Squared'],
            "Neighbour Mode": experiment_row['Neighbour Mode'],

            "Tau": tau
        }

        list_images.append(record)

    print("\n\n")

    if error_count > 0:
        paint_logger.error(
            f"There were {error_count} out of {len(self.df_experiment)} images for which no picture was available")

    if initial:
        self.saved_list_images = list_images

    return list_images


def get_corresponding_bf(bf_dir, ext_recording_name, recording_name):
    """
    Retrieve the corresponding BF image for the given image name
    """

    if not os.path.exists(bf_dir):
        paint_logger.error(
            "Function 'get_corresponding_bf' failed - The directory for jpg versions of BF images does not exist. Run 'Convert BF Images' first")
        sys.exit()

    # List of possible BF image names
    bf_images = [f"{recording_name}-BF.jpg", f"{recording_name}-BF1.jpg", f"{recording_name}-BF2.jpg"]

    # Iterate through the list and check if the file exists
    recording_name = None
    for img in bf_images:
        if os.path.isfile(os.path.join(bf_dir, img)):
            recording_name = img
            break

    if recording_name:
        img = ImageTk.PhotoImage(Image.open(os.path.join(bf_dir, recording_name)))
        valid = True
    else:
        img = ImageTk.PhotoImage(Image.new('RGB', (512, 512), (235, 235, 235)))
        valid = False

    return valid, img
