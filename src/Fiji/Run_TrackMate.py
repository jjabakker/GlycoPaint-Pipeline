import csv
import os
import sys
import threading
import time

from java.awt import GridLayout, Dimension, FlowLayout
from java.io import File
from javax.swing import JFrame, JPanel, JButton, JTextField, JFileChooser, JOptionPane, BorderFactory

import fiji.plugin.trackmate.features.FeatureFilter as FeatureFilter
import fiji.plugin.trackmate.visualization.hyperstack.HyperStackDisplayer as HyperStackDisplayer

from fiji.plugin.trackmate.action import CaptureOverlayAction
from fiji.plugin.trackmate.detection import LogDetectorFactory
from fiji.plugin.trackmate.gui.displaysettings import DisplaySettingsIO
from fiji.plugin.trackmate.gui.displaysettings.DisplaySettings import TrackMateObject
from fiji.plugin.trackmate.tracking.jaqaman import SparseLAPTrackerFactory
from fiji.plugin.trackmate.util import LogRecorder
from fiji.plugin.trackmate import (
    Logger,
    Model,
    SelectionModel,
    Settings,
    TrackMate)

from ij import WindowManager
from ij.io import FileSaver
from ij.plugin.frame import RoiManager
from ij import IJ

from PaintConfig import (
    load_paint_config,
    get_paint_defaults_file_path)

from DirectoriesAndLocations import (
    get_experiment_info_file_path,
    get_experiment_tm_file_path)

from PaintConfig import (
    get_paint_attribute,
    update_paint_attribute
)

from FijiSupportFunctions import (
    fiji_get_file_open_write_attribute,
    fiji_get_file_open_append_attribute,
    suppress_fiji_output,
    format_time_nicely)

from LoggerConfig import (
    paint_logger,
    paint_logger_change_file_handler_name)

from ConvertBrightfieldImages import convert_bf_images

paint_logger_change_file_handler_name('Run Trackmate.log')


# --------------------------------------------------------
# --------------------------------------------------------
# --------------------------------------------------------
# Start of Code originally kept in TrackMate.py
# --------------------------------------------------------
# --------------------------------------------------------
# --------------------------------------------------------
# --------------------------------------------------------


# --------------------------------------------------------
# Code adapted from
# https://imagej.net/plugins/trackmate/scripting/scripting
# --------------------------------------------------------


def execute_trackmate_in_Fiji(recording_name, threshold, tracks_filename, image_filename, first, kas_special ):

    paint_config = load_paint_config(get_paint_defaults_file_path())
    trackmate_config = paint_config['TrackMate']

    max_frame_gap = trackmate_config['MAX_FRAME_GAP'] or 0.5
    linking_max_distance = trackmate_config['LINKING_MAX_DISTANCE'] or 0.5
    gap_closing_max_distance = trackmate_config['GAP_CLOSING_MAX_DISTANCE'] or 0.5

    alternative_linking_cost_factor = trackmate_config['ALTERNATIVE_LINKING_COST_FACTOR'] or 1.05
    splitting_max_distance = trackmate_config['SPLITTING_MAX_DISTANCE'] or 13.0
    allow_gap_closing = trackmate_config['ALLOW_GAP_CLOSING'] or True
    allow_track_merging = trackmate_config['ALLOW_TRACK_MERGING'] or False
    allow_track_splitting = trackmate_config['ALLOW_TRACK_SPLITTING'] or False
    merging_max_distance = trackmate_config['MERGING_MAX_DISTANCE'] or 12.0

    do_subpixel_localization = trackmate_config['DO_SUBPIXEL_LOCALIZATION'] or False
    radius = trackmate_config['RADIUS'] or 0.5
    target_channel = trackmate_config['TARGET_CHANNEL'] or 1
    do_median_filtering = trackmate_config['DO_MEDIAN_FILTERING'] or True

    min_number_of_spots = trackmate_config['MIN_NR_SPOTS_IN_TRACK'] or 3

    track_colouring = trackmate_config['TRACK_COLOURING'] or 'TRACK_DURATION'
    if track_colouring != 'TRACK_DURATION' and track_colouring != 'TRACK_INDEX':
        paint_logger.error('Invalid track colouring option in TrackMate configuration,default to TRACK_DURATION')
        track_colouring = 'TRACK_DURATION'

    if first:
        paint_logger.info('TrackMate Parameters')
        paint_logger.info("")
        paint_logger.info('TARGET_CHANNEL:                  ' + str(target_channel))
        paint_logger.info('RADIUS:                          ' + str(radius))
        paint_logger.info('DO_SUBPIXEL_LOCALIZATION:        ' + str(do_subpixel_localization))
        paint_logger.info('DO_MEDIAN_FILTERING:             ' + str(do_median_filtering))
        paint_logger.info("")
        paint_logger.info('LINKING_MAX_DISTANCE:            ' + str(linking_max_distance))
        paint_logger.info('ALTERNATIVE_LINKING_COST_FACTOR: ' + str(alternative_linking_cost_factor))
        paint_logger.info("")
        paint_logger.info('ALLOW_GAP_CLOSING:               ' + str(allow_gap_closing))
        paint_logger.info('GAP_CLOSING_MAX_DISTANCE:        ' + str(gap_closing_max_distance))
        paint_logger.info('MAX_FRAME_GAP:                   ' + str(max_frame_gap))
        paint_logger.info("")
        paint_logger.info('ALLOW_TRACK_SPLITTING:           ' + str(allow_track_splitting))
        paint_logger.info('SPLITTING_MAX_DISTANCE:          ' + str(splitting_max_distance))
        paint_logger.info("")
        paint_logger.info('ALLOW_TRACK_MERGING:             ' + str(allow_track_merging))
        paint_logger.info('MERGING_MAX_DISTANCE:            ' + str(merging_max_distance))
        paint_logger.info("")
        paint_logger.info('MIN_NR_SPOTS_IN_TRACK:           ' + str(min_number_of_spots))
        paint_logger.info('TRACK_COLOURING:                 ' + str(track_colouring))
        paint_logger.info("")
        paint_logger.info("")

    # We have to do the following to avoid errors with UTF8 chars generated in
    # TrackMate that will mess with our Fiji Jython.
    reload(sys)
    sys.setdefaultencoding('utf-8')

    # ----------------------------
    # Create the model object now
    # ----------------------------

    # Some of the parameters we configure below need to have
    # a reference to the model at creation. So we create an
    # empty model now.

    model = Model()
    model.setLogger(Logger.IJ_LOGGER)

    # Get currently selected image
    imp = WindowManager.getCurrentImage()

    # Prepare settings object
    settings = Settings(imp)

    # Configure detector - all important parameters
    settings.detectorFactory = LogDetectorFactory()
    settings.detectorSettings = {
        'TARGET_CHANNEL': target_channel,
        'RADIUS': radius,
        'DO_SUBPIXEL_LOCALIZATION': do_subpixel_localization,  # False
        'THRESHOLD': threshold,
        'DO_MEDIAN_FILTERING': do_median_filtering
    }

    # Configure spot filters - Do not filter out any nr_spots
    filter1 = FeatureFilter('QUALITY', 0, True)
    settings.addSpotFilter(filter1)

    # Configure tracker, first set the default, but then override parameters that we know are important
    settings.trackerFactory = SparseLAPTrackerFactory()
    settings.trackerSettings = settings.trackerFactory.getDefaultSettings()

    # These are the important parameters

    settings.trackerSettings['LINKING_MAX_DISTANCE'] = linking_max_distance  # 0.6
    settings.trackerSettings['ALTERNATIVE_LINKING_COST_FACTOR'] = alternative_linking_cost_factor  # 1.05

    settings.trackerSettings['ALLOW_GAP_CLOSING'] = allow_gap_closing
    settings.trackerSettings['GAP_CLOSING_MAX_DISTANCE'] = gap_closing_max_distance  # 1.2
    settings.trackerSettings['MAX_FRAME_GAP'] = max_frame_gap

    settings.trackerSettings['ALLOW_TRACK_SPLITTING'] = allow_track_splitting
    settings.trackerSettings['SPLITTING_MAX_DISTANCE'] = splitting_max_distance

    settings.trackerSettings['ALLOW_TRACK_MERGING'] = allow_track_merging
    settings.trackerSettings['MERGING_MAX_DISTANCE'] = merging_max_distance

    # Add ALL the feature analyzers known to TrackMate.
    # They will yield numerical features for the results, such as speed, mean intensity etc.
    settings.addAllAnalyzers()

    # Configure track filters - Only consider tracks of 3 and longer.
    filter2 = FeatureFilter('NUMBER_SPOTS', min_number_of_spots, True)
    settings.addTrackFilter(filter2)

    # Instantiate plugin
    trackmate = TrackMate(model, settings)

    # Process
    ok = trackmate.checkInput()
    if not ok:
        paint_logger.error('Routine paint_trackmate - checkInput failed')
        return -1, -1, -1

    ok = trackmate.process()
    if not ok:
        paint_logger.error('Routine paint_trackmate - process failed')
        return -1, -1, -1

    # Get nr_spots data, iterate through each track to calculate the mean square displacement

    track_ids = model.getTrackModel().trackIDs(True)  # True means only return visible tracks
    diffusion_coefficient_list = []
    for track_id in track_ids:

        # Get the set of nr_spots in this track
        track_spots = model.getTrackModel().trackSpots(track_id)

        first_spot = True
        cum_msd = 0
        # Iterate through the nr_spots in this track, retrieve values for x and y (in micron)
        for spot in track_spots:
            if first_spot:
                x0 = spot.getFeature('POSITION_X')
                y0 = spot.getFeature('POSITION_Y')
                first_spot = False
            else:
                x = spot.getFeature('POSITION_X')
                y = spot.getFeature('POSITION_Y')
                cum_msd += (x - x0) ** 2 + (y - y0) ** 2
        msd = cum_msd / (len(track_spots) - 1)
        diffusion_coefficient = msd / (2 * 2 * 0.05)

        nice_diffusion_coefficient = round(diffusion_coefficient, 4)
        diffusion_coefficient_list.append(nice_diffusion_coefficient)

    # ----------------
    # Display results
    # ----------------

    if kas_special:
        rm = RoiManager.getInstance()
        rm.runCommand("Open", os.path.expanduser("~/paint.roi"))
        rm.runCommand("Show All")

    # A selection.
    selection_model = SelectionModel(model)

    # Read the default display settings.
    ds = DisplaySettingsIO.readUserDefault()
    ds.setSpotVisible(False)
    ds.setTrackColorBy(TrackMateObject.TRACKS, track_colouring)

    displayer = HyperStackDisplayer(model, selection_model, imp, ds)
    displayer.render()
    displayer.refresh()

    # ---------------------------------------------------
    # Save the image file with image with overlay as tiff
    # ---------------------------------------------------

    image = trackmate.getSettings().imp
    tm_logger = LogRecorder(Logger.VOID_LOGGER)
    capture = CaptureOverlayAction.capture(image, -1, 1, tm_logger)
    FileSaver(capture).saveAsTiff(image_filename)

    # The feature model, that stores edge and track features.
    feature_model = model.getFeatureModel()

    # ----------------
    # Write the Tracks file
    # ----------------

    fields = ["Ext Recording Name", "Track Label", "Nr Spots", "Track Duration", 'Track X Location', 'Track Y Location',
              'Diffusion Coefficient']
    fields = ["Ext Recording Name", "Track Label", "Nr Spots", "Nr Gaps", "Longest Gap",
              "Track Duration",
              'Track X Location', 'Track Y Location', 'Track Displacement', 'Track Total Distance',
              'Track Max Speed', 'Track Median Speed', 'Track Mean Speed',
              'Diffusion Coefficient']

    # Determine write attributes
    open_attribute = fiji_get_file_open_write_attribute()

    # Iterate over all the tracks that are visible.
    with open(tracks_filename, open_attribute) as csvfile:

        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(fields)

        track_index = 0
        for track_id in model.getTrackModel().trackIDs(True):
            # Fetch the track feature from the feature model.
            label = 'Track_' + str(track_id)
            duration = round(feature_model.getTrackFeature(track_id, 'TRACK_DURATION'), 3)
            nr_spots = feature_model.getTrackFeature(track_id, 'NUMBER_SPOTS')
            x = round(feature_model.getTrackFeature(track_id, 'TRACK_X_LOCATION'), 2)
            y = round(feature_model.getTrackFeature(track_id, 'TRACK_Y_LOCATION'), 2)

            med_speed = 2
            total_distance = 3

            max_speed = feature_model.getTrackFeature(track_id, 'TRACK_MAX_SPEED')
            if max_speed is None:
                max_speed = -1
            else:
                max_speed = round(max_speed, 2)

            med_speed = feature_model.getTrackFeature(track_id, 'TRACK_MEDIAN_SPEED')
            if med_speed is None:
                med_speed = -1
            else:
                med_speed = round(med_speed, 2)

            mean_speed = feature_model.getTrackFeature(track_id, 'TRACK_MEAN_SPEED')
            if mean_speed is None:
                mean_speed = -1
            else:
                mean_speed = round(mean_speed, 2)

            total_distance = feature_model.getTrackFeature(track_id, 'TRACK_TOTAL_DISTANCE_TRAVELED')
            if total_distance is None:
                total_distance = -2
            else:
                total_distance = round(total_distance, 2)

            nr_gaps = feature_model.getTrackFeature(track_id, 'NUMBER_GAPS')
            if nr_gaps is None:
                nr_gaps = -1

            longest_gap = feature_model.getTrackFeature(track_id, 'LONGEST_GAP')
            if longest_gap is None:
                longest_gap = -1

            displacement = feature_model.getTrackFeature(track_id, 'TRACK_DISPLACEMENT')
            if  displacement is None:
                displacement = -1
            else:
                displacement = round(displacement, 2)

            # Write the record for each track
            # csvwriter.writerow([recording_name, label, nr_spots, duration, x, y, diffusion_coefficient_list[track_index]])
            csvwriter.writerow([recording_name, label, nr_spots, nr_gaps, longest_gap,
                                duration,
                                x, y, displacement, total_distance,
                                max_speed, med_speed, mean_speed,
                                diffusion_coefficient_list[track_index]])
            track_index += 1

    model.getLogger().log('Found ' + str(model.getTrackModel().nTracks(True)) + ' tracks.')

    nr_spots = model.getSpots().getNSpots(True)  # Get visible nr_spots only
    tracks = model.getTrackModel().nTracks(False)  # Get all tracks
    filtered_tracks = model.getTrackModel().nTracks(True)  # Get filtered tracks

    return nr_spots, tracks, filtered_tracks

# --------------------------------------------------------
# --------------------------------------------------------
# --------------------------------------------------------
# End of Code originally kept in TrackMate.py
# --------------------------------------------------------
# --------------------------------------------------------
# --------------------------------------------------------
# --------------------------------------------------------




# -----------------------------------------------------------------------------------------------------------
# -----------------------------------------------------------------------------------------------------------
# -----------------------------------------------------------------------------------------------------------
# This is the start of the actual Run_TrackMate code
# -----------------------------------------------------------------------------------------------------------\
# -----------------------------------------------------------------------------------------------------------
# -----------------------------------------------------------------------------------------------------------



def run_trackmate(experiment_directory, recording_source_directory):
    # Open the experiment file to determine the columns (which should be in the paint directory)

    experiment_info_path = get_experiment_info_file_path(experiment_directory)

    if not os.path.exists(experiment_info_path):
        msg = "Warning: The file '{}' does not exist.".format(experiment_info_path)
        paint_logger.error(msg)
        JOptionPane.showMessageDialog(None, msg, "Warning", JOptionPane.WARNING_MESSAGE)
        suppress_fiji_output
        sys.exit()

    image_dir = os.path.join(experiment_directory, 'TrackMate Images')
    if not os.path.exists(image_dir):
        os.mkdir(image_dir)
    else:
        for filename in os.listdir(image_dir):
            file_path = os.path.join(image_dir, filename)
            if os.path.isfile(file_path):
                os.remove(file_path)  # Delete the file

    with open(experiment_info_path, mode='r') as experiment_info_file:
        csv_reader = csv.DictReader(experiment_info_file)
        if not {'Recording Sequence Nr', 'Recording Name', 'Experiment Date', 'Experiment Name', 'Condition Nr',
                'Replicate Nr', 'Probe', 'Probe Type', 'Cell Type', 'Adjuvant', 'Concentration', 'Threshold',
                'Process'} <= set(csv_reader.fieldnames):
            paint_logger.error("Error: Missing expected column headers ")
            suppress_fiji_output()
            sys.exit()

        try:
            # Count how many recordings need to be processed
            count = 0
            nr_to_process = 0
            for row in csv_reader:
                if 'y' in row['Process'].lower():
                    nr_to_process += 1
                count += 1
            if nr_to_process == 0:
                paint_logger.warning("No recordings selected for processing")
                return -1

            message = "Processing " + str(nr_to_process) + " recordings in directory " + recording_source_directory
            paint_logger.info(message)

            # Initialise the All Recordings file with the column headers
            col_names = csv_reader.fieldnames
            new_columns = ['Nr Spots', 'Nr Tracks', 'Run Time', 'Ext Recording Name', 'Recording Size', 'Time Stamp']
            col_names += [col for col in new_columns if col not in col_names]

            # And create the header row
            experiment_tm_file_path = initialise_experiment_tm_file(experiment_directory, col_names)

            # And now cycle through the experiment file
            nr_recording_processed = 0
            nr_recording_failed = 0
            nr_recording_not_found = 0

            experiment_info_file.seek(0)
            csv_reader = csv.DictReader(experiment_info_file)

            file_count = 0
            for row in csv_reader:  # Here we are reading the experiment file
                if 'y' in row['Process'].lower():
                    file_count += 1


                    status, row = process_recording_trackmate(row, recording_source_directory, experiment_directory, file_count==1)
                    paint_logger.info(
                        "Processed file nr " + str(file_count) + " of " + str(nr_to_process) + ": " + row[
                            'Recording Name'])
                    if status == 'OK':
                        nr_recording_processed += 1
                    elif status == 'NOT_FOUND':
                        nr_recording_not_found += 1
                    elif status == 'FAILED':
                        nr_recording_not_found += 1

                write_row_to_temp_file(row, experiment_tm_file_path, col_names)

            paint_logger.info("")
            paint_logger.info("Number of recordings processed successfully:      " + str(nr_recording_processed))
            paint_logger.info("Number of recordings not found:                   " + str(nr_recording_not_found))
            paint_logger.info("Number of recordings not  successfully processed: " + str(nr_recording_failed))

            if nr_recording_processed == 0:
                msg = "No recordings processed successfully. Refer to Paint log for details."
                paint_logger.warning(msg)
                JOptionPane.showMessageDialog(None, msg, "Warning", JOptionPane.WARNING_MESSAGE)
            elif nr_recording_not_found:
                msg = "Some recordings were not found. Refer to Paint log for details."
                paint_logger.warning(msg)
                JOptionPane.showMessageDialog(None, msg, "Warning", JOptionPane.WARNING_MESSAGE)

            # -----------------------------------------------------------------------------
            # Concatenate the Tracks file with the existing one
            # -----------------------------------------------------------------------------

            # Define the directory to search in
            keywords = ["threshold", "tracks"]
            matching_files = []

            # Loop through each file in the directory
            for filename in os.listdir(experiment_directory):
                # Check if it's a CSV file and if all keywords are in the filename
                if filename.endswith('.csv') and all(keyword in filename.lower() for keyword in ["threshold", "track"]):
                    matching_files.append(os.path.join(experiment_directory, filename))
            matching_files.sort()

            # Define the output file
            output_file = os.path.join(experiment_directory, "All Tracks.csv")

            # Open the output file in write mode
            with open(output_file, 'w') as outfile:
                writer = None

                # Loop through each CSV file
                for filename in matching_files:
                    with open(filename, 'r') as infile:
                        reader = csv.reader(infile)
                        header = next(reader)  # Read the header row

                        # Write the header only once, when the writer is None
                        if writer is None:
                            writer = csv.writer(outfile)
                            writer.writerow(header)

                        # Write the rest of the rows
                        for row in reader:
                            writer.writerow(row)

            for filename in matching_files:
                os.remove(filename)

        except KeyError as e:
            paint_logger.error("Run_TrackMate: Missing expected column in row: {}.format(e)")
            suppress_fiji_output()
            sys.exit(0)

    convert_bf_images(recording_source_directory, experiment_directory, force=True)


def process_recording_trackmate(row, recording_source_directory, experiment_directory, first):
    status = 'OK'
    recording_name = row['Recording Name']
    threshold = float(row['Threshold'])

    if row['Adjuvant'] == 'None':
        row['Adjuvant'] = 'No'

    img_file_ext = get_paint_attribute('Paint', 'Image File Extension')
    recording_file_name = os.path.join(recording_source_directory, recording_name + img_file_ext)

    if not os.path.exists(recording_file_name):
        paint_logger.warning("Processing: Failed to open recording: " + recording_file_name)
        row['Recording Size'] = 0
        status = 'NOT_FOUND'
    else:
        row['Recording Size'] = os.path.getsize(recording_file_name)
        imp = IJ.openImage(recording_file_name)

        imp.show()
        IJ.run("Enhance Contrast", "saturated=0.35")
        IJ.run("Grays")

        # Set the scale
        # IJ.run("Set Scale...", "distance=6.2373 known=1 unit=micron")
        # IJ.run("Scale Bar...", "width=10 height=5 thickness=3 bold overlay")

        ext_recording_name = recording_name + "-threshold-" + str(int(threshold))

        time_stamp = time.time()
        tracks_file_path = os.path.join(experiment_directory, ext_recording_name + '-tracks.csv')
        recording_file_path = os.path.join(experiment_directory, 'TrackMate Images', ext_recording_name + '.jpg')

        # suppress_fiji_output()
        nr_spots, total_tracks, long_tracks = execute_trackmate_in_Fiji(
            ext_recording_name, threshold, tracks_file_path, recording_file_path, first, False, )
        # restore_fiji_output()

        # IJ.run("Set Scale...", "distance=6.2373 known=1 unit=micron")
        # IJ.run("Scale Bar...", "width=10 height=5 thickness=3 bold overlay")

        if nr_spots == -1:
            paint_logger.error("\n'Process single recording' did not manage to run 'paint_trackmate'")
            status = 'FAILED'
        else:
            time.sleep(3)  # Display the recording for 3 seconds
        run_time = round(time.time() - time_stamp, 1)

        paint_logger.debug('Nr of spots: ' + str(nr_spots) + " processed in " + str(run_time) + " seconds")
        imp.close()

        # Update the row
        row['Nr Spots'] = nr_spots
        row['Nr Tracks'] = long_tracks
        row['Run Time'] = run_time
        row['Ext Recording Name'] = ext_recording_name
        row['Time Stamp'] = time.asctime(time.localtime(time.time()))

    return status, row


def initialise_experiment_tm_file(experiment_directory, column_names):
    temp_file_path = get_experiment_tm_file_path(experiment_directory)
    try:
        temp_file = open(temp_file_path, fiji_get_file_open_write_attribute())
        temp_writer = csv.DictWriter(temp_file, column_names)
        temp_writer.writeheader()
        temp_file.close()
        return temp_file_path
    except IOError:
        paint_logger.error("Could not open results file:" + temp_file_path)
        suppress_fiji_output()
        sys.exit(-1)


def write_row_to_temp_file(row, temp_file_path, column_names):
    try:
        temp_file = open(temp_file_path, fiji_get_file_open_append_attribute())
        temp_writer = csv.DictWriter(temp_file, column_names)
        temp_writer.writerow(row)
        temp_file.close()
    except IOError:
        paint_logger.error("Could not write results file:" + temp_file_path)
        suppress_fiji_output()
        sys.exit()


# Function to process directories after the window is closed
def run_trackmate_with_supplied_directories(recordings_directory, experiment_directory):
    def run_fiji_code():
        time_stamp = time.time()
        run_trackmate(experiment_directory, recordings_directory)
        run_time = time.time() - time_stamp
        run_time = round(run_time, 1)
        paint_logger.info("\nProcessing completed in {}.".format(format_time_nicely(run_time)))

    # Run Fiji code on a new thread to avoid conflicts with the Swing EDT
    fiji_thread = threading.Thread(target=run_fiji_code)
    fiji_thread.start()


# Function to create the GUI
def create_gui():
    root_dir = None
    level = None

    # Set up the frame
    frame = JFrame("Run TrackMate")
    frame.setSize(700, 200)
    frame.setDefaultCloseOperation(JFrame.DISPOSE_ON_CLOSE)
    frame.setLayout(GridLayout(3, 1))

    # Get the default drectories
    experiment_dir = get_paint_attribute('User Directories', 'Experiment Directory')
    images_dir = get_paint_attribute('User Directories', 'Images Directory')

    # Add padding around the frame content
    frame.getRootPane().setBorder(BorderFactory.createEmptyBorder(20, 20, 20, 20))

    # Panel for directory 1
    panel1 = JPanel(FlowLayout(FlowLayout.LEFT))
    browseButton1 = JButton("Images Directory")
    browseButton1.setPreferredSize(Dimension(180, 20))
    textField1 = JTextField(40)
    textField1.setEditable(False)
    textField1.setText(images_dir)  # Set the default directory text immediately

    # Action to open JFileChooser for directory 1
    def browse_action1(event):
        chooser = JFileChooser()
        chooser.setFileSelectionMode(JFileChooser.DIRECTORIES_ONLY)
        chooser.setCurrentDirectory(File(images_dir))
        chooser.rescanCurrentDirectory()  # Ensures the directory tree is refreshed
        result = chooser.showOpenDialog(frame)
        if result == JFileChooser.APPROVE_OPTION:
            selected_dir = chooser.getSelectedFile().getAbsolutePath()
            textField1.setText(selected_dir)

    browseButton1.addActionListener(browse_action1)
    panel1.add(browseButton1)
    panel1.add(textField1)

    # Panel for directory 2
    panel2 = JPanel(FlowLayout(FlowLayout.LEFT))
    browseButton2 = JButton("Experiment Directory")
    browseButton2.setPreferredSize(Dimension(180, 20))
    textField2 = JTextField(40)
    textField2.setEditable(False)
    textField2.setText(experiment_dir)  # Set the default directory text immediately

    # Action to open JFileChooser for directory 2
    def browse_action2(event):
        chooser = JFileChooser()
        chooser.setFileSelectionMode(JFileChooser.DIRECTORIES_ONLY)
        chooser.setCurrentDirectory(File(experiment_dir))
        chooser.rescanCurrentDirectory()  # Ensures the directory tree is refreshed
        result = chooser.showOpenDialog(frame)
        if result == JFileChooser.APPROVE_OPTION:
            selected_dir = chooser.getSelectedFile().getAbsolutePath()
            textField2.setText(selected_dir)

    browseButton2.addActionListener(browse_action2)
    panel2.add(browseButton2)
    panel2.add(textField2)

    # Panel for OK and Cancel buttons
    buttonPanel = JPanel()
    okButton = JButton("OK")
    cancelButton = JButton("Cancel")

    # Define actions for the OK and Cancel buttons
    def ok_action(event):

        recordings_directory = textField1.getText()
        experiment_directory = textField2.getText()

        # save_default_locations(root_dir, experiment_directory, recordings_directory, level)
        update_paint_attribute('User Directories', 'Experiment Directory', experiment_directory)
        update_paint_attribute('User Directories', 'Images Directory', recordings_directory)

        frame.dispose()

        # Process directories
        run_trackmate_with_supplied_directories(recordings_directory, experiment_directory)

    def cancel_action(event):
        print("Operation cancelled.")

        frame.dispose()  # Close the window

    # Assign actions to buttons
    okButton.addActionListener(ok_action)
    cancelButton.addActionListener(cancel_action)

    # Add components to the frame
    buttonPanel.add(okButton)
    buttonPanel.add(cancelButton)
    frame.add(panel1)
    frame.add(panel2)
    frame.add(buttonPanel)

    # Show the frame
    frame.setVisible(True)


if __name__ == "__main__":
    # Call the function to create the GUI

    create_gui()
