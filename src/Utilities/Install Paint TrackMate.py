import os
import shutil
import subprocess
import logging
import platform

from src.Fiji.NewPaintConfig import (
    get_paint_attribute_with_default,
    update_paint_attribute)

if platform.system() == "Windows":
    import winreg
else:
    winreg = None  # Mock the winreg module on non-Windows systems

def setup_logging():
    """Sets up the logging configuration."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def find_app_path_macos(app_name="Fiji.app"):
    """Finds the installation path of a macOS application."""
    common_paths = [os.path.expanduser('~/Applications'), '/Applications', '/System/Applications']
    for directory in common_paths:
        app_path = os.path.join(directory, app_name)
        if os.path.exists(app_path):
            return app_path
    try:
        result = subprocess.run(
            ['mdfind', f'kMDItemFSName == "{app_name}"'],
            stdout=subprocess.PIPE,
            text=True
        )
        paths = result.stdout.strip().split('\n')
        for path in paths:
            if path.endswith(app_name):
                return path
    except Exception as e:
        logging.error(f"Error using Spotlight to locate {app_name}: {e}")
    return None


def find_app_path_windows(app_name="Fiji"):
    """
    Locates the installation path of a Windows application using the Registry and common paths.

    :param app_name: Name of the application to search for (default: "Fiji").
    :return: Path to the application if found, None otherwise.
    """
    if winreg is None:
        raise NotImplementedError("winreg module is unavailable on this platform. Run this code on Windows.")

    reg_paths = [
        r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
        r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall",
    ]

    for reg_path in reg_paths:
        try:
            reg_key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path)
            for i in range(winreg.QueryInfoKey(reg_key)[0]):
                try:
                    sub_key_name = winreg.EnumKey(reg_key, i)
                    sub_key = winreg.OpenKey(reg_key, sub_key_name)
                    display_name, _ = winreg.QueryValueEx(sub_key, "DisplayName")
                    if app_name.lower() in display_name.lower():
                        install_location, _ = winreg.QueryValueEx(sub_key, "InstallLocation")
                        if os.path.exists(install_location):
                            return install_location
                except (FileNotFoundError, OSError):
                    continue
        except (FileNotFoundError, OSError):
            continue

    # Fallback to common paths
    common_paths = [
        "C:\\Program Files\\Fiji.app",
        "C:\\Program Files (x86)\\Fiji.app",
        "D:\\Fiji.app",
        "E:\\Fiji.app",
    ]
    for path in common_paths:
        if os.path.exists(path):
            return path

    return None

def find_fiji_path():
    """
    Locates the Fiji application path based on the platform.
    Calling get_paint_attribute_with_default('Paint', 'Fiji Path') will cause the paint.json file to be created if it does not exist
    already.
    If the default Fiji path is not found, the function will try to find the Fiji path based on the platform.
    If no valid path is found, the function will return None (and the wuser will be invited to edit the paint.json file).
    """

    fiji_path = get_paint_attribute_with_default('Paint', 'Fiji Path', "")
    if fiji_path and os.path.exists(fiji_path):
        # We can assume we have a valid path to Fiji
        pass
    else:
        logging.warning("Fiji path not found in paint.json file. Trying to locate the Fiji application.")
        fiji_path = None
    if fiji_path is None:
        if platform.system() == "Darwin":
            fiji_path = find_app_path_macos()
            if os.path.exists(fiji_path):
                update_paint_attribute('Paint', 'Fiji Path', fiji_path)
        elif platform.system() == "Windows":
            try:
                fiji_path = find_app_path_windows()
                if os.path.exists(fiji_path):
                    update_paint_attribute('Paint', 'Fiji Path', fiji_path)
            except NotImplementedError:
                logging.warning("Windows functionality is not available on this platform.")
        else:
            logging.error("Unsupported platform.")
    return fiji_path


def copy_file(source_dir, dest_dir, filename):
    """Copies a single file from source to destination."""
    source_file = os.path.join(source_dir, filename)
    dest_file = os.path.join(dest_dir, filename)
    try:
        if not os.path.isfile(source_file):
            logging.warning(f"File not found: {source_file}")
        elif not os.path.isdir(dest_dir):
            logging.warning(f"Destination directory missing: {dest_dir}")
        else:
            shutil.copyfile(source_file, dest_file)
            logging.info(f"Copied {filename} to {dest_dir}")
    except Exception as e:
        logging.error(f"Failed to copy {filename}: {e}")


def install():
    """Main installation function for setting up Fiji plugins and scripts."""

    fiji_app = find_fiji_path()
    if not fiji_app:
        logging.critical("Fiji application not found an also not specified properly in the paint.json file.")
        logging.critical("Please make sure that Fiji is installed and specify the path to the Fiji application in the paint.json file.")
        return

    # Clean and create the directory
    dest_root = os.path.join(fiji_app, 'Scripts', 'Glyco-PAINT')
    if os.path.exists(dest_root):
        shutil.rmtree(dest_root)
    dest_root = os.path.join(fiji_app, 'Scripts', 'Glyco-PAINT')
    if os.path.exists(dest_root):
        shutil.rmtree(dest_root)

    os.makedirs(dest_root, exist_ok=True)

    # Remove the __pycache__ directory if it exists
    base_dir = os.path.abspath(os.path.join("..", "..", "src", "Fiji"))
    pycache_dir = os.path.join(base_dir, '__pycache__')

    if os.path.exists(pycache_dir):
        shutil.rmtree(pycache_dir)

    source_root = os.path.dirname(os.getcwd())

    source_directories = {
        "fiji_source": os.path.join(source_root, 'Fiji'),
    }

    dest_directories = {
        "fiji_dest": dest_root
    }

    file_groups = {
        source_directories["fiji_source"]: [
            "Run_TrackMate.py",
            "Run_TrackMate_Batch.py",
            "Run_TrackMate_Sweep.py",
            "Single_Analysis.py",
            "FijiSupportFunctions.py",
            "NewTrackMate.py",
            "ConvertBrightfieldImages.py",
            "LoggerConfig.py",
            "DirectoriesAndLocations.py",
            "NewPaintConfig.py"],
    }

    for src_dir, files in file_groups.items():
        dest_dir = dest_directories["fiji_dest"]
        for file in files:
            copy_file(src_dir, dest_dir, file)


if __name__ == '__main__':
    setup_logging()
    install()