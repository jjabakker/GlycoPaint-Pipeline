import os
import time

from src.Fiji.LoggerConfig import paint_logger


def set_directory_tree_timestamp(dir_to_change, timestamp=None):
    """
    Set the access and modification timestamps of a directory.

    :param dir_to_change: Path to the directory.
    :param timestamp: Unix timestamp (seconds since epoch) to set for access and modification times.
                      If None, the current time will be used.
    """
    # Check if the provided path is a valid directory
    if not os.path.isdir(dir_to_change):
        paint_logger.error(f"Error: '{dir_to_change}' is not a valid directory.")
        return

    # If no timestamp is provided, use the current time
    if timestamp is None:
        timestamp = time.time()

    try:
        for dir_path, dir_names, filenames in os.walk(dir_to_change):

            # Set timestamp for each file in the directory
            os.utime(dir_to_change, (timestamp, timestamp))
            for dirname in dir_names:
                filepath = os.path.join(dir_path, dirname)
                os.utime(filepath, (timestamp, timestamp))
            for filename in filenames:
                filepath = os.path.join(dir_path, filename)
                os.utime(filepath, (timestamp, timestamp))
        paint_logger.debug(f"Updated timestamps for directory '{dir_to_change}' successfully.")

    except (PermissionError, OSError, FileNotFoundError):
        paint_logger.error(f"Failed to update timestamps for directory '{dir_to_change}'.")
    except PermissionError:
        paint_logger.error(f"Error: Permission denied while setting timestamps for '{dir_to_change}'.")
    except FileNotFoundError:
        paint_logger.error(f"Error: Directory '{dir_to_change}' not found.")
    except Exception as e:
        paint_logger.error(f"An unexpected error occurred: {e}")


# Example Usage: Set timestamps to a specific date
def get_timestamp_from_string(date_str, format_str='%Y-%m-%d %H:%M:%S'):
    """
    Convert a date string into a Unix timestamp.

    :param date_str: The date in string format (e.g., '2023-01-01 12:00:00').
    :param format_str: Format of the input date string (default: '%Y-%m-%d %H:%M:%S').
    :return: Unix timestamp (seconds since epoch).
    """
    try:
        return time.mktime(time.strptime(date_str, format_str))
    except ValueError as e:
        print(f"Error: Invalid date format. {e}")
        return None


if __name__ == '__main__':

    # directory = '/Users/hans/Documents/LST/Master Results/PAINT Pipeline/Python and R Code/Paint-R/Data'
    directory = '/Users/hans/Downloads/Code'

    # Example of using a specific timestamp
    time_string = '2024-10-11 00:00:00'
    specific_time = get_timestamp_from_string(time_string)
    if specific_time:
        set_directory_tree_timestamp(directory, specific_time)
    else:
        paint_logger.error("Failed to set timestamp due to an error.")
