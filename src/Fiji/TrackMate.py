# -*- coding: utf-8 -*-

# --------------------------------------------------------
# Code adapted from
# https://imagej.net/plugins/trackmate/scripting/scripting
# --------------------------------------------------------

import csv
import os
import sys

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
from PaintConfig import get_paint_attribute


def execute_trackmate_in_Fiji(recording_name, threshold, tracks_filename, image_filename, kas_special):
    print("\nProcessing: " + tracks_filename)

    max_frame_gap = get_paint_attribute('Trackmate', 'MAX_FRAME_GAP', 0.5)
    linking_max_distance = get_paint_attribute('Trackmate', 'LINKING_MAX_DISTANCE', 0.5)
    gap_closing_max_distance = get_paint_attribute('Trackmate', 'GAP_CLOSING_MAX_DISTANCE', 0.5)

    alternative_linking_cost_factor = get_paint_attribute('Trackmate', 'ALTERNATIVE_LINKING_COST_FACTOR', 1.05)
    splitting_max_distance = get_paint_attribute('Trackmate', 'SPLITTING_MAX_DISTANCE', 13.0)
    allow_gap_closing = get_paint_attribute('Trackmate', 'ALLOW_GAP_CLOSING', False)
    allow_track_merging = get_paint_attribute('Trackmate', 'ALLOW_TRACK_MERGING', False)
    allow_track_splitting = get_paint_attribute('Trackmate', 'ALLOW_TRACK_SPLITTING', False)
    merging_max_distance = get_paint_attribute('Trackmate', 'MERGING_MAX_DISTANCE', 12.0)

    do_subpixel_localization = get_paint_attribute('Trackmate', 'DO_SUBPIXEL_LOCALIZATION', False)
    radius = get_paint_attribute('Trackmate', 'RADIUS', 0.5)
    target_channel = get_paint_attribute('Trackmate', 'TARGET_CHANNEL', 1)
    do_median_filtering = get_paint_attribute('Trackmate', 'DO_MEDIAN_FILTERING', True)

    min_number_of_spots = get_paint_attribute('Trackmate', 'MIN_NR_SPOTS_IN_TRACK', 3)

    track_colouring = get_paint_attribute('Trackmate', 'TRACK_COLOURING', 'TRACK_DURATION')
    if track_colouring != 'TRACK_DURATION' and track_colouring != 'TRACK_INDEX':
        paint_logger.error('Invalid track colouring option in TrackMate configuration,default to TRACK_DURATION')
        track_colouring = 'TRACK_DURATION'

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
        'DO_SUBPIXEL_LOCALIZATION': do_subpixel_localization,  # False
        'RADIUS': radius,  # 0.5
        'TARGET_CHANNEL': target_channel,  # 1
        'THRESHOLD': threshold,
        'DO_MEDIAN_FILTERING': do_median_filtering,  # False
    }

    # Configure spot filters - Do not filter out any spots
    filter1 = FeatureFilter('QUALITY', 0, True)
    settings.addSpotFilter(filter1)

    # Configure tracker, first set the default, but then override parameters that we know are important
    settings.trackerFactory = SparseLAPTrackerFactory()
    settings.trackerSettings = settings.trackerFactory.getDefaultSettings()

    # These are the important parameters
    settings.trackerSettings['MAX_FRAME_GAP'] = max_frame_gap  # 3
    settings.trackerSettings['LINKING_MAX_DISTANCE'] = linking_max_distance  # 0.6
    settings.trackerSettings['GAP_CLOSING_MAX_DISTANCE'] = gap_closing_max_distance  # 1.2

    # These are default values made explicit
    settings.trackerSettings['ALTERNATIVE_LINKING_COST_FACTOR'] = alternative_linking_cost_factor  # 1.05
    settings.trackerSettings['SPLITTING_MAX_DISTANCE'] = splitting_max_distance  # 15.0
    settings.trackerSettings['ALLOW_GAP_CLOSING'] = allow_gap_closing  # True
    settings.trackerSettings['ALLOW_TRACK_SPLITTING'] = allow_track_splitting  # False
    settings.trackerSettings['ALLOW_TRACK_MERGING'] = allow_track_merging  # False
    settings.trackerSettings['MERGING_MAX_DISTANCE'] = merging_max_distance  # 15 .0
    settings.trackerSettings['CUTOFF_PERCENTILE'] = cutoff_percentile  # 0.9

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

    # Get spots data, iterate through each track to calculate the mean square displacement

    track_ids = model.getTrackModel().trackIDs(True)  # True means only return visible tracks
    diffusion_coefficient_list = []
    for track_id in track_ids:

        # Get the set of spots in this track
        track_spots = model.getTrackModel().trackSpots(track_id)

        first_spot = True
        cum_msd = 0
        # Iterate through the spots in this track, retrieve values for x and y (in micron)
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
    fields = ["Ext Recording Name", "Track Label", "Nr Spots", "Track Duration", 'Track X Location', 'Track Y Location',
              'Track Max Speed', 'Track Median Speed', 'Track Total Distance', 'Diffusion Coefficient']

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
            spots = feature_model.getTrackFeature(track_id, 'NUMBER_SPOTS')
            x = round(feature_model.getTrackFeature(track_id, 'TRACK_X_LOCATION'), 2)
            y = round(feature_model.getTrackFeature(track_id, 'TRACK_Y_LOCATION'), 2)

            max_speed = round(feature_model.getTrackFeature(track_id, 'TRACK_MAX_SPEED'), 2)
            # med_speed = round(feature_model.getTrackFeature(track_id, 'TRACK_MEDIAN_SPEED'), 2)
            # total_distance = round(feature_model.getTrackFeature(track_id, 'TRACK_TOTAL_DISTANCE_TRAVELED'), 2)

            med_speed = 2
            total_distance = 3

            # Write the record for each track
            # csvwriter.writerow([recording_name, label, spots, duration, x, y, diffusion_coefficient_list[track_index]])
            csvwriter.writerow([recording_name, label, spots, duration, x, y, max_speed, med_speed, total_distance,
                                diffusion_coefficient_list[track_index]])
            track_index += 1

    model.getLogger().log('Found ' + str(model.getTrackModel().nTracks(True)) + ' tracks.')

    nr_spots = model.getSpots().getNSpots(True)  # Get visible spots only
    tracks = model.getTrackModel().nTracks(False)  # Get all tracks
    filtered_tracks = model.getTrackModel().nTracks(True)  # Get filtered tracks

    return nr_spots, tracks, filtered_tracks
