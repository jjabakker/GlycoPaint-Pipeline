# -*- coding: utf-8 -*-

# --------------------------------------------------------
# Code adapted from
# https://imagej.net/plugins/trackmate/scripting/scripting
# --------------------------------------------------------

import csv
import math
import os
import sys

from java.lang.System import getProperty

paint_dir = os.path.join(getProperty('fiji.dir'), "Scripts", "GlycoPaint")
sys.path.append(paint_dir)

import fiji.plugin.trackmate.features.FeatureFilter as FeatureFilter
import fiji.plugin.trackmate.visualization.hyperstack.HyperStackDisplayer as HyperStackDisplayer
from fiji.plugin.trackmate import (
    Logger,
    Model,
    SelectionModel,
    Settings,
    TrackMate)
from fiji.plugin.trackmate.action import CaptureOverlayAction
from fiji.plugin.trackmate.detection import LogDetectorFactory
from fiji.plugin.trackmate.gui.displaysettings import DisplaySettingsIO
from fiji.plugin.trackmate.gui.displaysettings.DisplaySettings import TrackMateObject
from fiji.plugin.trackmate.tracking.jaqaman import SparseLAPTrackerFactory
from fiji.plugin.trackmate.util import LogRecorder
from ij import WindowManager
from ij.io import FileSaver
from ij.plugin.frame import RoiManager

from FijiSupportFunctions import fiji_get_file_open_write_attribute
from LoggerConfig import paint_logger
from NewPaintConfig import get_paint_attribute_with_default


def own_median(data):
    """Return the median of a list of numbers."""
    sorted_data = sorted(data)
    n = len(sorted_data)
    if n == 0:
        raise ValueError("median() arg is an empty list")
    mid = n // 2
    if n % 2 == 1:
        return sorted_data[mid]
    else:
        return (sorted_data[mid - 1] + sorted_data[mid]) / 2.0  # ensure float division


def get_track_attributes(track_model, track_id):
    spots = list(track_model.trackSpots(track_id))
    if len(spots) < 2:
        return 0.0  # Not enough spots to calculate distance, but this cannot happen

    # Sort by frame to get the correct order
    spots.sort(key=lambda s: s.getFeature('FRAME'))

    total_distance = 0.0
    cum_msd = 0.0
    cum_msd_ext = 0.0
    speed_list = []

    for i in range(1, len(spots)):
        x1 = spots[i - 1].getFeature('POSITION_X')
        y1 = spots[i - 1].getFeature('POSITION_Y')

        x2 = spots[i].getFeature('POSITION_X')
        y2 = spots[i].getFeature('POSITION_Y')

        # Keep a reference to the first point
        if i == 1:
            x0 = x1
            y0 = y1

        dist = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
        total_distance += dist

        cum_msd += (x2 - x0) ** 2 + (y2 - y0) ** 2
        cum_msd_ext += (x2 - x1) ** 2 + (y2 - y1) ** 2

        speed = dist / 0.05  # Assuming time between frames is 0.05 seconds
        speed_list.append(speed)

    max_speed = round(max(speed_list), 2)
    median_speed = round(own_median(speed_list), 2)
    mean_speed = round(sum(speed_list) / len(speed_list), 2)
    total_distance = round(total_distance, 2)

    msd = cum_msd / (len(spots) - 1)
    diffusion_coefficient = round(msd / (2 * 2 * 0.05), 2)

    msd_ext = cum_msd_ext / (len(spots) - 1)
    diffusion_coefficient_ext = round(msd_ext / (2 * 2 * 0.05), 2)

    return total_distance, max_speed, median_speed, mean_speed, diffusion_coefficient, diffusion_coefficient_ext


def execute_trackmate_in_Fiji(
        recording_name,
        threshold,
        tracks_filename,
        image_filename,
        first,
        kas_special):
    max_frame_gap = get_paint_attribute_with_default('TrackMate', 'MAX_FRAME_GAP', 0.5)
    linking_max_distance = get_paint_attribute_with_default('TrackMate', 'LINKING_MAX_DISTANCE', 0.5)
    gap_closing_max_distance = get_paint_attribute_with_default('TrackMate', 'GAP_CLOSING_MAX_DISTANCE', 0.5)

    alternative_linking_cost_factor = get_paint_attribute_with_default('TrackMate', 'ALTERNATIVE_LINKING_COST_FACTOR',
                                                                       1.05)
    splitting_max_distance = get_paint_attribute_with_default('TrackMate', 'SPLITTING_MAX_DISTANCE', 13.0)
    allow_gap_closing = get_paint_attribute_with_default('TrackMate', 'ALLOW_GAP_CLOSING', False)
    allow_track_merging = get_paint_attribute_with_default('TrackMate', 'ALLOW_TRACK_MERGING', False)
    allow_track_splitting = get_paint_attribute_with_default('TrackMate', 'ALLOW_TRACK_SPLITTING', False)
    merging_max_distance = get_paint_attribute_with_default('TrackMate', 'MERGING_MAX_DISTANCE', 12.0)

    do_subpixel_localization = get_paint_attribute_with_default('TrackMate', 'DO_SUBPIXEL_LOCALIZATION', False)
    radius = get_paint_attribute_with_default('TrackMate', 'RADIUS', 0.5)
    target_channel = get_paint_attribute_with_default('TrackMate', 'TARGET_CHANNEL', 1)
    do_median_filtering = get_paint_attribute_with_default('TrackMate', 'DO_MEDIAN_FILTERING', True)

    min_number_of_spots = get_paint_attribute_with_default('TrackMate', 'MIN_NR_SPOTS_IN_TRACK', 3)

    max_nr_of_spots_in_image = get_paint_attribute_with_default('TrackMate', 'MAX_NR_SPOTS_IN_IMAGE', 2000000)

    track_colouring = get_paint_attribute_with_default('TrackMate', 'TRACK_COLOURING', 'TRACK_DURATION')
    if track_colouring != 'TRACK_DURATION' and track_colouring != 'TRACK_INDEX':
        paint_logger.error('Invalid track colouring option in TrackMate configuration,default to TRACK_DURATION')
        track_colouring = 'TRACK_DURATION'

    if first:
        paint_logger.info('')
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
        paint_logger.info('MAX_NR_SPOTS_IN_IMAGE:           ' + str(max_nr_of_spots_in_image))
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

    # Get the currently selected image
    imp = WindowManager.getCurrentImage()

    # Prepare the Settings object
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

    # Configure the tracker, first set the default, but then override parameters that we know are important
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
    # They will yield numerical features for the results, such as speed, mean intensity, etc.
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
        return -1, -1, -1, -1, -1, -1, -1, -1, -1

    # Run the spot detection step first
    ok = trackmate.execDetection()
    if not ok:
        paint_logger.error('Routine paint_trackmate - execDetection failed')
        return -1, -1, -1, -1, -1, -1, -1, -1, -1

    nr_spots = model.getSpots().getNSpots(False)
    if nr_spots > max_nr_of_spots_in_image:
        paint_logger.error('Too many spots detected ({}). Limit is {}.'.format(nr_spots, max_nr_of_spots_in_image))
        return nr_spots, -1, -1, -1, -1, -1, -1, -1 , -1 # Return early, skipping further processing

    # Continue with full TrackMate processing - nr_spots is within limits
    if not trackmate.process():
        paint_logger.error('Routine paint_trackmate - process failed')
        return -1, -1, -1, -1, -1, -1, -1, -1, -1

    # Get nr_spots data, iterate through each track to calculate the mean square displacement

    track_model = model.getTrackModel()
    feature_model = model.getFeatureModel()

    # ----------------
    # Display results
    # ----------------

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

    # ----------------
    # Write the Tracks file
    # ----------------

    fields = ['Ext Recording Name', 'Track Id', 'Track Label', 'Nr Spots', 'Nr Gaps', 'Longest Gap',
              'Track Duration',
              'Track X Location', 'Track Y Location', 'Track Displacement',
              'Track Max Speed', 'Track Median Speed', 'Track Mean Speed',
              'Track Max Speed Calc', 'Track Median Speed Calc', 'Track Mean Speed Calc',
              'Diffusion Coefficient', 'Diffusion Coefficient Ext',
              'Total Distance', 'Confinement Ratio']

    # Determine write attributes
    open_attribute = fiji_get_file_open_write_attribute()

    nr_spots_in_all_tracks = 0

    # Iterate over all the tracks that are visible.
    with open(tracks_filename, open_attribute) as csvfile:

        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(fields)

        for track_id in track_model.trackIDs(True):

            total_distance_c, max_speed_c, median_speed_c, mean_speed_c, diffusion_coefficient_c, diffusion_coefficient_ext_c = get_track_attributes(track_model, track_id)

            nr_spots_in_all_tracks += len(track_model.trackSpots(track_id))

            track_label = track_model.name(track_id)
            if track_label is None:
                track_label = 'Track-' + str(track_id)

            duration = feature_model.getTrackFeature(track_id, 'TRACK_DURATION')
            if duration is None:
                duration = -1
            else:
                duration = round(duration, 3)

            nr_spots = feature_model.getTrackFeature(track_id, 'NUMBER_SPOTS')
            if nr_spots is None:
                nr_spots = -1
            else:
                nr_spots = round(nr_spots, 0)

            x = feature_model.getTrackFeature(track_id, 'TRACK_X_LOCATION')
            if x is None:
                x = -1
            else:
                x = round(x, 2)

            y = feature_model.getTrackFeature(track_id, 'TRACK_Y_LOCATION')
            if y is None:
                y = -1
            else:
                y = round(y, 2)

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

            nr_gaps = feature_model.getTrackFeature(track_id, 'NUMBER_GAPS')
            if nr_gaps is None:
                nr_gaps = -1

            longest_gap = feature_model.getTrackFeature(track_id, 'LONGEST_GAP')
            if longest_gap is None:
                longest_gap = -1

            displacement = feature_model.getTrackFeature(track_id, 'TRACK_DISPLACEMENT')
            if displacement is None:
                displacement = -1
            else:
                displacement = round(displacement, 2)

            if total_distance_c != 0:
                confinement_ratio = round(displacement / total_distance_c, 2)
            else:
                confinement_ratio = None

            # Write the record for each track
            csvwriter.writerow([recording_name, track_id, track_label, nr_spots, nr_gaps, longest_gap, duration,
                                x, y, displacement,
                                max_speed, med_speed, mean_speed,
                                max_speed_c, median_speed_c, mean_speed_c,
                                diffusion_coefficient_c, diffusion_coefficient_ext_c,
                                total_distance_c, confinement_ratio])

    model.getLogger().log('Found ' + str(model.getTrackModel().nTracks(True)) + ' tracks.')

    nr_spots = model.getSpots().getNSpots(True)  # Get visible nr_spots only
    tracks = track_model.nTracks(False)  # Get all tracks
    filtered_tracks = track_model.nTracks(True)  # Get filtered tracks

    return (nr_spots, tracks, filtered_tracks, max_frame_gap, linking_max_distance, gap_closing_max_distance,
            nr_spots_in_all_tracks, do_median_filtering, min_number_of_spots)
