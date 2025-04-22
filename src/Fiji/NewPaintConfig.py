import json
import os
import sys

def get_paint_defaults_file_path():  # ToDo
    return os.path.join(os.path.expanduser('~'), 'Paint', 'Defaults', 'Paint.json')

# This is unusual code. One import will work in Jython, the other in Python. The other will fail, but the error will
# be caught.

# Import for Jython
try:
    from LoggerConfig import paint_logger
except:
    pass

# Import for Python
try:
    from src.Fiji.LoggerConfig import paint_logger
except:
    pass

paint_configuration = None

# Default JSON structure
default_data = {
    "Paint": {
        "Version": "1.0",
        "Image File Extension": ".nd2",
        "Fiji Path": "/Applications/Fiji.app"
    },
    "User Directories": {
        "Project Directory": "~",
        "Experiment Directory": "~",
        "Images Directory": "~",
        "Level": "Experiment"
    },
    "Generate Squares": {
        "Plot to File": False,
        "Plot Max": 5,
        "Fraction of Squares to Determine Background": 0.1,
        "Exclude zero DC tracks from Tau Calculation": False,
        "Neighbour Mode": "Free",
        "Min Track Duration": 0,
        "Max Track Duration": 1000000,
        "Nr of Squares in Row": 20,
        "Min Tracks to Calculate Tau": 20,
        'Min Required R Squared': 0.9,
        "Min Required Density Ratio": 2.0,
        "Max Allowable Variability": 10.0,

        "logging": {
            "level": "INFO",
            "file": "Generate Squares.log"
        }
    },
    "TrackMate": {
        "logging": {
            "level": "INFO",
            "file": "Run TrackMate Batch.log"
        },

        "TARGET_CHANNEL": 1,  # Old value: 1
        "RADIUS": 0.5,  # Old value: 0.5
        "DO_SUBPIXEL_LOCALIZATION": False,  # Old value: False
        "DO_MEDIAN_FILTERING": False,  # Old value: False

        "LINKING_MAX_DISTANCE": 0.6,  # Old value: 0.6
        "ALTERNATIVE_LINKING_COST_FACTOR": 1.05,  # Old value: 1.05

        "ALLOW_GAP_CLOSING": True,  # Old value: True
        "GAP_CLOSING_MAX_DISTANCE": 1.2,  # Old value: 1.2
        "MAX_FRAME_GAP": 3,  # Old value: 3, this causes the longest gap to be 2 (and not 1 as you would expect)

        "ALLOW_TRACK_SPLITTING": False,  # Old value: False
        "SPLITTING_MAX_DISTANCE": 15.0,  # Old value: 15.0

        "ALLOW_TRACK_MERGING": False,  # Old value: False
        "MERGING_MAX_DISTANCE": 15.0,  # Old value: 15.0

        "MIN_NR_SPOTS_IN_TRACK": 3,  # Old value: 3
        "TRACK_COLOURING": "TRACK_DURATION",  # Old value: "TRACK_DURATION"

        "MAX_NR_SPOTS_IN_IMAGE": 2000000
    }
}


def load_paint_config(file_path):
    global paint_configuration

    if paint_configuration is not None:
        return paint_configuration

    if file_path is None:
        file_path = os.path.join(os.path.expanduser('~'), 'Paint', 'Defaults', 'paint.json')

    if not os.path.exists(file_path):

        # Make sure the directory exists
        if not os.path.exists(os.path.join(os.path.expanduser('~'), 'Paint', 'Defaults')):
            os.mkdir(os.path.join(os.path.expanduser('~'), 'Paint', 'Defaults'))
        # Then create the file with default values
        with open(file_path, "w") as file:
            json.dump(default_data, file, indent=4)
        paint_logger.info("File '{}' created with default values.".format(file_path))

    try:
        with open(file_path, 'r') as config_file:
            paint_configuration = json.load(config_file)
        return paint_configuration
    except IOError:
        paint_logger.error("Error: Configuration file {} not found.".format(file_path))
        return None
    except ValueError:
        paint_logger.error("Failed to parse JSON from {}.".format(file_path))
        return None
    except:
        paint_logger.error("Error: Problem with configuration file {}.".format(file_path))
        return None


def get_paint_attribute_with_default(application, attribute_name, default_value):
    config = load_paint_config(get_paint_defaults_file_path())
    if config is None:
        paint_logger.error("Error: Configuration file {} not found.".format(get_paint_defaults_file_path()))
        return None
    else:
        application = config.get(application)
        value = application.get(attribute_name, None)
        if value is None:
            paint_logger.error("Info: Attribute {} not found in configuration file {}.".format(attribute_name,
                                                                                                get_paint_defaults_file_path()))
            if default_value is not None:
                paint_logger.error(
                    "Info: Default value {} applied for Attribute {}.".format(default_value, attribute_name))
                value = default_value
                update_paint_attribute(application, attribute_name, value)
            else:
                paint_logger.error(
                    "Error: Attribute {} not found in configuration file {} and application {} and no default value.".format(
                        attribute_name, application, get_paint_defaults_file_path()))
                sys.exit()
        return value


def update_paint_attribute(application, attribute_name, value):
    try:
        # Load the current configuration
        config = load_paint_config(get_paint_defaults_file_path())  # Ensure these functions are defined
        if application in config:
            # Check if the attribute exists, if not, create it
            config[application][attribute_name] = value
        else:
            paint_logger.error("The '{}' section does not exist in the config file.".format(application))
            return

        # Save the updated configuration back to the file
        with open(get_paint_defaults_file_path(), "w") as file:
            json.dump(config, file, indent=4)

    except Exception as e:
        paint_logger.error("An unexpected error occurred while saving the config file: {}".format(str(e)))

if __name__ == '__main__':
    config = load_paint_config(os.path.join(os.path.expanduser('~'), 'Paint', 'Defaults', 'paint.json'))
    trackmate_config = config['TrackMate']
    max_gap1 = trackmate_config['MAX_FRAME_GAP']

    config = load_paint_config(os.path.join(os.path.expanduser('~'), 'Paint', 'Defaults', 'paint.json'))
    trackmate_config = config['TrackMate']
    max_gap = trackmate_config['MAX_FRAME_GAP']

    i = 1
