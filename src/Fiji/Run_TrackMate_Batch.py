import csv
import os
import sys
import time

from javax.swing import JOptionPane

from LoggerConfig import (
    paint_logger,
    paint_logger_change_file_handler_name)

from FijiSupportFunctions import (
    ask_user_for_file,
    format_time_nicely)

from Run_TrackMate import run_trackmate

# Set an appropriate name for the log file
paint_logger_change_file_handler_name('Run TrackMate Batch.log')

if __name__ == "__main__":

    batch_file_name = ask_user_for_file("Specify the batch file")
    if not batch_file_name:
        paint_logger.info("User aborted the batch processing.")
        sys.exit(1)

    if not os.path.exists(batch_file_name):
        msg = "Error: The file '{}' does not exist.".format(batch_file_name)
        paint_logger.error(msg)
        JOptionPane.showMessageDialog(None, msg, "Warning", JOptionPane.WARNING_MESSAGE)
    else:

        message = "Processing Trackmate batchfile: '{}'".format(batch_file_name)
        paint_logger.info("")
        paint_logger.info("")
        paint_logger.info("-" * len(message))
        paint_logger.info("-" * len(message))
        paint_logger.info("")
        paint_logger.info(message)
        paint_logger.info("")
        paint_logger.info("-" * len(message))
        paint_logger.info("-" * len(message))
        paint_logger.info("")
        paint_logger.info("")

        try:
            # Use `with` to open the file and ensure it is closed after reading
            with open(batch_file_name, mode='r') as file:
                # Create a DictReader object
                csv_reader = csv.DictReader(file)

                # Check if the required columns are present
                required_columns = ['Source', 'Destination', 'Process']
                if not all(col in csv_reader.fieldnames for col in required_columns):
                    paint_logger.error("Error: Missing one or more required columns: {}".format(required_columns))
                    sys.exit()

                # Read and print each row
                time_stamp = time.time()
                error = False
                for row in csv_reader:
                    if 'y' in row['Process'].lower():

                        source = os.path.join(row['Source'], row['Image'])
                        if not os.path.exists(source):
                            paint_logger.error("Error: The source '{}' does not exist.".format(source))
                            error = True
                            continue

                        destination = os.path.join(row['Destination'], row['Image'])
                        if not os.path.exists(destination):
                            paint_logger.error("Error: The destination '{}' does not exist.".format(destination))
                            error = True
                            continue

                        message = "Processing image '{}'".format(row['Image'])
                        paint_logger.info("")
                        paint_logger.info("-" * len(message))
                        paint_logger.info(message)
                        paint_logger.info("-" * len(message))
                        run_trackmate(experiment_directory=os.path.join(row['Source'], row['Image']),
                                      recording_source_directory=os.path.join(row['Destination'], row['Image']))
                        paint_logger.info("")
                        paint_logger.info("")
                run_time = round(time.time() - time_stamp, 1)

                if error:
                    msg = "Errors occurred during processing. Refer to the log file for more information."
                    JOptionPane.showMessageDialog(None, msg, "Warning", JOptionPane.WARNING_MESSAGE)
                else:
                    paint_logger.info("Processing completed in {} seconds".format(format_time_nicely(run_time)))

        except csv.Error as e:
            paint_logger.error("run_trackmate_batch: Error reading CSV file: {}".format(e))
        except Exception as e:
            paint_logger.error("run_trackmate_batch: An unexpected error occurred: {}".format(e))
