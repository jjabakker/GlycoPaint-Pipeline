import os
import shutil
from tkinter import *

import pandas as pd
from PIL import Image

pd.options.mode.copy_on_write = True


def save_as_png(canvas, file_name, size_pixels=(512, 512)):
    canvas.config(width=size_pixels[0], height=size_pixels[1])

    # First save as a postscript file
    canvas.postscript(file=file_name + '.ps', colormode='color')

    # Open the PostScript file with PIL
    img = Image.open(file_name + '.ps')
    img = img.resize(size_pixels)

    # Save as TIFF
    img.save(file_name + '.tiff', 'TIFF')

    # Then let PIL convert to a png file
    img = Image.open(file_name + '.ps')
    img.save(f"{file_name}.png", 'png')


def test_if_square_is_in_rectangle(x0, y0, x1, y1, xr0, yr0, xr1, yr1):
    """
    Test if the square is in the rectangle specified by the user.
    Note these are different unit systems
    The coordinates from the squares are in micrometers
    The coordinates from the rectangle are in pixels
    One or the other needs to be converted before you can compare
    :param x0:
    :param y0:
    :param x1:
    :param y1:
    :param xr0:
    :param yr0:
    :param xr1:
    :param yr1:
    :return:
    """

    # Convert square coordinates from micrometers to pixels
    x0, y0, x1, y1 = [coord / 82.0864 * 512 for coord in [x0, y0, x1, y1]]

    # Determine if the square is within the rectangle
    if xr0 < xr1 and yr0 < yr1:
        return x0 >= xr0 and x1 <= xr1 and y0 >= yr0 and y1 <= yr1
    elif xr0 < xr1 and yr0 > yr1:
        return x0 >= xr0 and x1 <= xr1 and y0 >= yr1 and y1 <= yr0
    elif xr0 > xr1 and yr0 > yr1:
        return x0 >= xr1 and x1 <= xr0 and y0 >= yr1 and y1 <= yr0
    elif xr0 > xr1 and yr0 < yr1:
        return x0 >= xr1 and x1 <= xr0 and y0 >= yr0 and y1 <= yr1

    return False


def only_one_nr_of_squares_in_row(directory):
    df_experiment = pd.read_csv(os.path.join(directory, 'All Recordings.csv'))
    return df_experiment['Nr of Squares in Row'].nunique() == 1


def nr_recordings(directory):
    df_experiment = pd.read_csv(os.path.join(directory, 'All Recordings.csv'))
    return len(df_experiment)


def find_excel_executable():
    """Locate the Microsoft Excel executable on Windows."""
    # First, try to find Excel in the system PATH
    excel_command = shutil.which("Excel.exe")
    if excel_command:
        return excel_command

    # If not found, search common installation directories
    possible_paths = [
        os.path.join(os.environ.get("PROGRAMFILES", "C:\\Program Files"), "Microsoft Office"),
        os.path.join(os.environ.get("PROGRAMFILES(X86)", "C:\\Program Files (x86)"), "Microsoft Office"),
        "C:\\Program Files\\Microsoft Office",
        "C:\\Program Files (x86)\\Microsoft Office"
    ]

    for base_path in possible_paths:
        for root, _, files in os.walk(base_path):
            if "Excel.exe" in files:
                return os.path.join(root, "Excel.exe")

    return None
    # raise FileNotFoundError("Microsoft Excel executable not found. Please check your installation.")
