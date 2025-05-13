# Saving information to All Tracks, All Recordings and All Squares

In the Recording Viewer, the user can make changes that require the data files to be updated.
Possible changes include:

- Changing filter parameters, which causes the selection of visible squares to change (function `update_select_squares`)
- Excluding an image from the analysis (function `on_exinclude`)
- Assigning squares to cells (function `callback_to_assign_squares_to_cell_id`)
- Manually deselecting squares (function `deselect_square`)
- Selecting all squares after previously deselecting squares (function `reset_deselected_squares`).

When changes have been made, they need to be saved when the user changes to a different image or exits the Viewer.


### Changing filter parameters

When the user changes the filter parameters, the selection of visible squares changes.
This requires the following changes to be recorded:

- `All Recordings`
  - The changed filter parameters for the recording are updated.
  - The recording Tau and Density values are updated.
- `All Squares`
  - The `Selected` flag is updated for each square to indicate if the square is selected or not.
  - The `Label Nr` is updated for each square and sorted so that the lowest `Label Nr` has the highest number of tracks
- `All Tracks`
  -  The `Label Nr` of each track contained in the selected squares is updated.

### Excluding an image from the analysis

When the user excludes an image, the following changes need to be recorded:

- All Recordings
  - The `Excluded` flag is set to `True` for the recording.

- All Squares
  - The `Image Excluded` flag is set to `True` for each square in the recording.

### Assigning squares to cells

When the user changes the assignment of squares to cells, the following changes need to be recorded:

- All Squares
  - The `Cell Id` field is updated for each square to indicate the cell it belongs to.

### Manually (de)selecting squares

When the user manually selects or deselects squares, the following changes need to be recorded:

- All Squares
  - The `Square Manually Excluded` flag is set to `True` for each excluded square in the recording.


## The mechanism

When the user makes changes to the data, the `recording_changed` flag is set in the software to indicate that data needs to be saved.
The value of this flag is inspected when the user either selects a new recording or exists the Viewer.
If saving actually takes place, depends on the state of the `Save` flag: `Always Save`
(to be certain that no changes get lost), `Never Save` (if the user just wants to inspect data), `Ask to Save` (default).

### Saving when changing recording

When the `recording_changed` flag is set, the `All Squares` and `All Tracks` data is updated:
- The `All Squares` dataframe (df_all_squares) is updated with the square information contained in df_squares.
- The `All Tracks` dataframe (df_all_tracks) is updated to ensure that the label information is correct.
The `save_on_exit` flag is set to `True`,
to ensure that the `All Recordings`, `All Squares` and `All Tracks` data is saved when the Viewer exits.

### Saving when exciting the Viewer

If the `save_on_exit` is set, and if the `save_mode` is set, `All Recordings`, `All Squares` and `All Tracks` data is saved.
