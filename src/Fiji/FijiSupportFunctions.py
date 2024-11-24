import os
import sys
import time

import java.lang
from java.io import PrintStream, ByteArrayOutputStream
from java.lang import System
from javax.swing import JFileChooser


def ask_user_for_file(prompt='Select File'):
    """
    Ask the user to specify the user image directory. Present the last used value as default.
    Save the user choice.
    :param prompt:
    :return:
    """

    file_chooser = JFileChooser('~')
    file_chooser.setFileSelectionMode(JFileChooser.FILES_ONLY)

    # Show the dialog and get the result
    result = file_chooser.showDialog(None, prompt)

    # Check if the user selected a directory
    if result == JFileChooser.APPROVE_OPTION:
        selected_file = file_chooser.getSelectedFile()
        return selected_file.getAbsolutePath()
    else:
        return ""


def fiji_get_file_open_write_attribute():
    """
    Returns an open write attribute that works both on macOS and Windows
    :return: A string containing the open write attribute
    """

    ver = java.lang.System.getProperty("os.name").lower()
    if ver.startswith("mac"):
        open_attribute = "w"
    else:
        open_attribute = "wb"

    return open_attribute


def fiji_get_file_open_append_attribute():
    """
    Returns an open append  attribute that works both on macOS and Windows
    :return: A string containing the open append attribute
    """

    ver = java.lang.System.getProperty("os.name").lower()
    if ver.startswith("mac"):
        open_attribute = "a"
    else:
        open_attribute = "ab"

    return open_attribute


def format_time_nicely(seconds):
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    hours = int(hours)
    minutes = int(minutes)
    seconds = int(seconds)

    parts = []
    if hours:
        parts.append("{0} hour{1}".format(hours, 's' if hours > 1 else ''))
    if minutes:
        parts.append("{0} minute{1}".format(minutes, 's' if minutes > 1 else ''))
    if seconds:
        parts.append("{0} second{1}".format(seconds, 's' if seconds > 1 else ''))

    return ', '.join(parts)


def set_directory_timestamp(dir_path, timestamp=None):
    """
    Set the access and modification timestamps of a directory.

    :param dir_path: Path to the directory.
    :param timestamp: Unix timestamp (seconds since epoch) to set for access and modification times.
                      If None, the current time will be used.
    """
    # Check if the provided path is a valid directory
    if not os.path.isdir(dir_path):
        paint_logger.error("Error: '{0}' is not a valid directory.".format(dir_path))
        return

    # If no timestamp is provided, use the current time
    if timestamp is None:
        timestamp = time.time()
        print("Using current time as timestamp for '{0}'.".format(dir_path))

    # Update the directory's access and modification times
    os.utime(dir_path, (timestamp, timestamp))
    print("Updated timestamps for directory '{0}' to {1} successfully.".format(dir_path, time.ctime(timestamp)))


def suppress_fiji_output():
    # Redirect system output streams
    sys_out_stream = ByteArrayOutputStream()
    sys_err_stream = ByteArrayOutputStream()

    # Set dummy output streams
    System.setOut(PrintStream(sys_out_stream))
    System.setErr(PrintStream(sys_err_stream))


def restore_fiji_output():
    # Restore default system output streams
    System.setOut(System.out)
    System.setErr(System.err)
