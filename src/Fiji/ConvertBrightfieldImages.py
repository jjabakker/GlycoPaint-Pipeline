import os
import shutil

from ij import IJ


from LoggerConfig import (
    paint_logger,
    paint_logger_change_file_handler_name)
from PaintConfig import get_paint_attribute

# Set up logging
paint_logger_change_file_handler_name('Convert BF Images.log')


def convert_bf_images(image_source_directory, paint_directory, force=False):
    """
    Convert BF images to JPEG and store them in a specified directory.

    Args:
        image_source_directory (str): Directory containing the  images.
        paint_directory (str): Directory to store the converted JPEGs.
        force (bool): Force overwrite of existing JPEG files, even if up to date.
    """

    img_file_ext = get_paint_attribute('Paint', 'Image File Extension')

    # Create a 'Converted BF Images' directory if it doesn't exist
    bf_jpeg_dir = os.path.join(image_source_directory, "Converted BF Images")
    if not os.path.isdir(bf_jpeg_dir):
        os.mkdir(bf_jpeg_dir)

    paint_logger.info('')  # Start logging new run

    count = found = converted = 0
    all_images = sorted(os.listdir(image_source_directory))  # Sort images for predictable processing order

    for image_name in all_images:
        # Skip hidden files or system files
        if image_name.startswith('._'):
            continue

        # Check if the file is of the expected file format
        if image_name.endswith(img_file_ext):
            count += 1

            # Only process Bright Field (BF) images
            if 'BF' in image_name:
                found += 1
                display_name = image_name.ljust(30, ' ')  # Align name in log for readability
                input_file = os.path.join(image_source_directory, image_name)
                output_file = os.path.join(bf_jpeg_dir, image_name.replace(img_file_ext, '.jpg'))

                # Determine if the image needs to be converted (force flag or file modification check)
                convert = force or not os.path.isfile(output_file) or os.path.getmtime(output_file) < os.path.getmtime(
                    input_file)

                if convert:
                    try:
                        # Open the image using Bio-Formats and save as JPEG
                        nd2_arg = "open=[%s]" % input_file
                        IJ.run("Bio-Formats (Windowless)", nd2_arg)
                        IJ.saveAs("Jpeg", output_file)
                        IJ.getImage().close()  # Close the image after saving
                        paint_logger.info("Image %s was updated.", display_name)
                        converted += 1
                    except Exception as e:
                        paint_logger.error("Error converting %s: %s", display_name, str(e))
                else:
                    paint_logger.info("Image %s does not require updating.", display_name)

    # Log the conversion summary
    paint_logger.info("\nConverted %d BF images, out of %d BF images from %d total images.", converted, found,
                      count)

    # Copy the entire 'Converted BF Images' directory to the paint directory
    dest_dir = os.path.join(paint_directory, "Brightfield Images")
    if os.path.exists(dest_dir):
        # If the destination directory already exists, remove it before copying
        shutil.rmtree(dest_dir)

    try:
        shutil.copytree(bf_jpeg_dir, dest_dir)
        paint_logger.info("Copied the entire 'Brightfield Images' directory to %s", dest_dir)
    except Exception as e:
        paint_logger.error("Error copying the directory %s to %s: %s", bf_jpeg_dir, dest_dir, str(e))
