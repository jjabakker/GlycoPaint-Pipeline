import os
import plistlib

import xattr

from src.Fiji.LoggerConfig import paint_logger


def set_finder_tags(path, tags):
    try:
        plist_data = plistlib.dumps(tags)
        xattr.setxattr(path, 'com.apple.metadata:_kMDItemUserTags', plist_data)

    except Exception as e:
        print(f"Failed to set tags for {path}. Error: {e}")


def get_finder_tags(path):
    try:
        attrs = xattr.getxattr(path, 'com.apple.metadata:_kMDItemUserTags')
        tags = plistlib.loads(attrs)
    except (KeyError, Exception):
        tags = ['No tags']

    return tags


def set_directory_tree_tag(dir_to_change, tags=None):
    # Check if the provided path is a valid directory
    if not os.path.isdir(dir_to_change):
        paint_logger.error(f"Error: '{dir_to_change}' is not a valid directory.")
        return

    try:
        for dirpath, dirnames, filenames in os.walk(dir_to_change):

            # Set tags for each file in the directory
            set_finder_tags(dir_to_change, tags)
            for dirname in dirnames:
                set_finder_tags(dir_to_change, tags)
            for filename in filenames:
                set_finder_tags(dir_to_change, tags)
        paint_logger.debug(f"Updated tags for directory '{dir_to_change}' successfully.")

    except (PermissionError, OSError, FileNotFoundError):
        paint_logger.error(f"Failed to update tags for '{dir_to_change}'.")
    except PermissionError:
        paint_logger.error(f"Error: Permission denied while setting tags for '{dir_to_change}'.")
    except FileNotFoundError:
        paint_logger.error(f"Error: Directory '{dir_to_change}' not found.")
    except Exception as e:
        paint_logger.error(f"An unexpected error occurred: {e}")


if __name__ == '__main__':
    directory = '/Users/hans/Downloads/Code'

    set_directory_tree_tag(directory, ['new'])
