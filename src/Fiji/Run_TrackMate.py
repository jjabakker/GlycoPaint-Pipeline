import csv
import os
import sys
import threading
import time

from ij import IJ
from java.awt import GridLayout, Dimension, FlowLayout
from java.io import File
from javax.swing import JFrame, JPanel, JButton, JTextField, JFileChooser, JOptionPane, BorderFactory

from DirectoriesAndLocations import (
    get_experiment_info_file_path,
    get_experiment_tm_file_path)

from PaintConfig import (
    get_paint_attribute,
    update_paint_attribute
)
from Trackmate import execute_trackmate_in_Fiji

from FijiSupportFunctions import (
    fiji_get_file_open_write_attribute,
    fiji_get_file_open_append_attribute,
    suppress_fiji_output,
    format_time_nicely)

from LoggerConfig import (
    paint_logger,
    paint_logger_change_file_handler_name)

from ConvertBrightfieldImages import convert_bf_images

paint_logger_change_file_handler_name('Grid Process Batch.log')


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
            col_names = csv_reader.fieldnames + ['Nr Spots', 'Nr Tracks', 'Run Time', 'Ext Recording Name',
                                                 'Recording Size', 'Time Stamp']
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
                    paint_logger.info(
                        "Processing file nr " + str(file_count) + " of " + str(nr_to_process) + ": " + row[
                            'Recording Name'])

                    status, row = process_recording(row, recording_source_directory, experiment_directory)
                    if status == 'OK':
                        nr_recording_processed += 1
                    elif status == 'NOT_FOUND':
                        nr_recording_not_found += 1
                    elif status == 'FAILED':
                        nr_recording_not_found += 1

                write_row_to_temp_file(row, experiment_tm_file_path, col_names)

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
            paint_logger.error("Run_Trackmate: Missing expected column in row: {}.format(e)")
            suppress_fiji_output()
            sys.exit(0)

    convert_bf_images(recording_source_directory, experiment_directory, force=True)


def process_recording(row, recording_source_directory, experiment_directory):
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
            ext_recording_name, threshold, tracks_file_path, recording_file_path, False)
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
    browseButton1 = JButton("Images  Directory")
    browseButton1.setPreferredSize(Dimension(180, 20))
    textField1 = JTextField(40)
    textField1.setEditable(False)

    # Action to open JFileChooser for directory 1
    def browse_action1(event):
        chooser = JFileChooser()
        chooser.setFileSelectionMode(JFileChooser.DIRECTORIES_ONLY)
        chooser.setCurrentDirectory(File(images_dir))
        chooser.rescanCurrentDirectory()  # Ensures the directory tree is refreshed
        textField1.setText(images_dir)
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

    # Action to open JFileChooser for directory 2
    def browse_action2(event):
        chooser = JFileChooser()
        chooser.setFileSelectionMode(JFileChooser.DIRECTORIES_ONLY)
        chooser.setCurrentDirectory(File(experiment_dir))
        chooser.rescanCurrentDirectory()  # Ensures the directory tree is refreshed
        textField2.setText(experiment_dir)
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
