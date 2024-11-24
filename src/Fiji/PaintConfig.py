import json
import os


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
        'Min Allowable R Squared': 0.9,
        "Min Required Density Ratio": 2.0,
        "Max Allowable Variability": 10.0,

        "logging": {
            "level": "INFO",
            "file": "Generate Squares.log"
        }
    },
    "Recording Viewer": {
        "logging": {
            "level": "INFO",
            "file": "Image Viewer.log"
        }
    },
    "Compile Project Output": {
        "logging": {
            "level": "INFO",
            "file": "Compile Project Output.log"
        }
    },
    "TrackMate": {
        "logging": {
            "level": "INFO",
            "file": "Run Trackmate Batch.log"
        },
        "MAX_FRAME_GAP": 3,
        "LINKING_MAX_DISTANCE": 0.6,
        "GAP_CLOSING_MAX_DISTANCE": 1.2,
        "ALTERNATIVE_LINKING_COST_FACTOR": 1.05,
        "SPLITTING_MAX_DISTANCE": 15.0,
        "ALLOW_GAP_CLOSING": True,
        "ALLOW_TRACK_SPLITTING": False,
        "ALLOW_TRACK_MERGING": False,
        "MERGING_MAX_DISTANCE": 15.0,
        "CUTOFF_PERCENTILE": 0.9,
        "MIN_NR_SPOTS_IN_TRACK": 3,
        "DO_SUBPIXEL_LOCALIZATION": False,
        "RADIUS": 0.5,
        "TARGET_CHANNEL": 1,
        "DO_MEDIAN_FILTERING": False,
        "TRACK_COLOURING": "TRACK_DURATION"
    }
}


def load_paint_config(file_path):
    global paint_configuration

    if paint_configuration is not None:
        return paint_configuration

    if file_path is None:
        file_path = os.path.join(os.path.expanduser('~'), 'Paint', 'Defaults', 'paint.json')

    if not os.path.exists(file_path):
        # If not, create the file with default values
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


def get_paint_attribute(application, attribute_name):
    config = load_paint_config(get_paint_defaults_file_path())
    if config is None:
        paint_logger.error("Error: Configuration file {} not found.".format(get_paint_defaults_file_path()))
        return None
    else:
        application = config.get(application)
        value = application.get(attribute_name, None)
        if value is None:
            pass  # ToDo
            paint_logger.error("Error: Attribute {} not found in configuration file {}.".format(attribute_name,
                                                                                                get_paint_defaults_file_path()))
        return value


def update_paint_attribute(application, attribute_name, value):
    try:
        config = load_paint_config(get_paint_defaults_file_path())

        # Update the RADIUS value under TrackMate
        if application in config:
            config[application][attribute_name] = value
        else:
            paint_logger.error("The {} section does not exist in the JSON file.".format(application))

        # Save the updated data back to the JSON file
        file_path = os.path.join(os.path.expanduser('~'), 'Paint', 'Defaults', 'paint.json')
        with open(file_path, "w") as file:
            json.dump(config, file, indent=4)

    except Exception as e:
        paint_logger.error("An unexpected error occurred: {}.format(e)")


if __name__ == '__main__':
    config = load_paint_config(os.path.join(os.path.expanduser('~'), 'Paint', 'Defaults', 'paint.json'))
    trackmate_config = config['TrackMate']
    max_gap1 = trackmate_config['MAX_FRAME_GAP']

    config = load_paint_config(os.path.join(os.path.expanduser('~'), 'Paint', 'Defaults', 'paint.json'))
    trackmate_config = config['TrackMate']
    max_gap = trackmate_config['MAX_FRAME_GAP']

    i = 1
