# -------------------------------------------------------------------------------------------------------------
# There are two ways to run the select squares files, either by calling  select_squares_with_parameters or by calling
# select_squares.
#
# Both functions call select_squares_actual which is the main function that selects squares based on defined conditions
# -------------------------------------------------------------------------------------------------------------

def select_squares_with_parameters(df_squares, select_parameters, nr_of_squares_in_row, only_valid_tau):
    """
    Wrapper function to select squares based on defined conditions for density, variability, and track duration,
    Parameters are passed through a dictionary.
    """

    _select_squares_actual(
        df_squares,
        select_parameters['min_required_density_ratio'],
        select_parameters['max_allowable_variability'],
        select_parameters['min_track_duration'],
        select_parameters['max_track_duration'],
        select_parameters['min_allowable_r_squared'],
        select_parameters['neighbour_mode'],
        nr_of_squares_in_row,
        only_valid_tau=only_valid_tau)


def select_squares(self, only_valid_tau=True):
    """
    Wrapper function to select squares based on defined conditions for density, variability, and track duration,
    No need to pass on individual parameters.
    """

    _select_squares_actual(
        self.df_squares,
        self.min_required_density_ratio,
        self.max_allowable_variability,
        self.min_track_duration,
        self.max_track_duration,
        self.min_allowable_r_squared,
        self.neighbour_mode,
        self.nr_of_squares_in_row,
        only_valid_tau=only_valid_tau)


def _select_squares_actual(
        df_squares,
        min_required_density_ratio,
        max_allowable_variability,
        min_track_duration,
        max_track_duration,
        min_allowable_r_squared,
        neighbour_mode,
        nr_of_squares_in_row,
        only_valid_tau=True):
    """
    Select squares based on defined conditions for density, variability, and track duration,
    and apply visibility rules based on neighborhood states. This is the function that does the actual work
    """

    # Define the conditions for squares to be visible
    df_squares['Selected'] = (
            (df_squares['Density Ratio'] >= min_required_density_ratio) &
            (df_squares['Variability'] <= max_allowable_variability) &
            (df_squares['Max Track Duration'] >= min_track_duration) &
            (df_squares['Max Track Duration'] <= max_track_duration) &
            (df_squares['R Squared'] >= min_allowable_r_squared))

    if only_valid_tau:
        df_squares['Selected'] = (
                (df_squares['Selected']) &
                (df_squares['Tau'] > 0)
        )

    # Eliminate isolated squares based on neighborhood rules
    df_squares.set_index('Square Nr', inplace=True, drop=False)
    if neighbour_mode == 'Free':
        pass
    elif neighbour_mode == 'Strict':
        select_squares_neighbour_strict(df_squares, nr_of_squares_in_row)
    elif neighbour_mode == 'Relaxed':
        select_squares_neighbour_relaxed(df_squares, nr_of_squares_in_row)
    else:
        raise ValueError(f"Neighbour mode '{neighbour_mode}' not recognized.")
    if 'Unique Key' in df_squares.columns:
        df_squares.set_index('Unique Key', inplace=True, drop=False)


def select_squares_neighbour_strict(df_squares, nr_of_squares_in_row):
    """
    Identifies squares with visible neighbors in strict mode and updates their Selected status.
    """
    list_of_squares = []

    for index, square in df_squares.iterrows():
        if not square['Selected']:
            continue

        row, col = square['Row Nr'], square['Col Nr']
        square_nr = square['Square Nr']

        # Define neighboring squares based on position
        neighbours = get_strict_neighbours(row, col, nr_of_squares_in_row)

        # Check if there are visible neighbors
        has_visible_neighbors = False
        for nb in neighbours:
            # Calculate the neighbor index
            neighbor_index = int((nb[0] - 1) * nr_of_squares_in_row + (nb[1] - 1))

            # Check if the neighbor exists and is visible
            if neighbor_index in df_squares.index and df_squares.loc[neighbor_index, 'Selected']:
                has_visible_neighbors = True
                break  # Exit early if any visible neighbor is found

        # Update visibility based on visible neighbors
        df_squares.at[square_nr, 'Selected'] = has_visible_neighbors
        if has_visible_neighbors:
            list_of_squares.append(square_nr)

    return df_squares, list_of_squares


def select_squares_neighbour_relaxed(df_squares, nr_of_squares_in_row):
    """
    Updates visibility of squares based on relaxed neighborhood conditions,
    ensuring isolated border squares are eliminated.
    """
    # Keep track of squares that remain selected
    list_of_squares = []

    for index, square in df_squares.iterrows():
        if not square['Selected']:
            continue  # Skip unselected squares

        row, col = square['Row Nr'], square['Col Nr']
        square_nr = square['Square Nr']

        # Get neighbors
        neighbours = get_relaxed_neighbours(row, col, nr_of_squares_in_row)

        # Check the visibility of neighbors
        has_visible_neighbors = False
        for nb in neighbours:
            # Calculate neighbor index
            neighbor_index = (nb[0] - 1) * nr_of_squares_in_row + (nb[1] - 1)

            # Ensure the neighbor exists in the grid and is selected
            if neighbor_index in df_squares.index and df_squares.loc[neighbor_index, 'Selected']:
                has_visible_neighbors = True
                break  # Exit early if any visible neighbor is found

        # Update 'Selected' status based on neighbors
        if has_visible_neighbors:
            list_of_squares.append(square_nr)
        else:
            df_squares.at[square_nr, 'Selected'] = False  # Mark as not visible

    return df_squares, list_of_squares


def get_strict_neighbours(row, col, nr_of_squares_in_row):
    """
    Returns neighboring positions for strict neighborhood rule.
    """
    left = (row, max(col - 1, 1))
    right = (row, min(col + 1, nr_of_squares_in_row))
    above = (max(row - 1, 1), col)
    below = (min(row + 1, nr_of_squares_in_row), col)

    if row == 1:
        return [right, below] if col == 1 else \
            [left, below] if col == nr_of_squares_in_row else \
                [left, right, below]
    elif row == nr_of_squares_in_row:
        return [right, above] if col == 1 else \
            [left, above] if col == nr_of_squares_in_row else \
                [left, right, above]
    else:
        return [right, below, above] if col == 1 else \
            [left, below, above] if col == nr_of_squares_in_row else \
                [left, right, below, above]


def get_relaxed_neighbours(row, col, nr_of_squares_in_row):
    """
    Returns all eight possible neighboring positions for relaxed neighborhood rule,
    strictly considering grid boundaries.
    """
    neighbours = []
    max_row, max_col = nr_of_squares_in_row, nr_of_squares_in_row

    # Potential neighbor positions
    potential_neighbours = [
        (row, col - 1),  # Left
        (row, col + 1),  # Right
        (row - 1, col),  # Above
        (row + 1, col),  # Below
        (row + 1, col - 1),  # Below Left
        (row + 1, col + 1),  # Below Right
        (row - 1, col - 1),  # Above Left
        (row - 1, col + 1),  # Above Right
    ]

    # Filter valid positions within bounds
    for nb_row, nb_col in potential_neighbours:
        if 1 <= nb_row <= max_row and 1 <= nb_col <= max_col:
            neighbours.append((nb_row, nb_col))

    return neighbours


def label_selected_squares(df_squares):
    """
    Assigns label numbers to selected squares in descending order of 'Nr Tracks'.
    """

    # Sort by 'Nr Tracks' in descending order
    df_squares.sort_values(by=['Nr Tracks'], inplace=True, ascending=False)
    df_squares.set_index('Square Nr', inplace=True, drop=False)

    # Initialize label number
    label_nr = 1

    # Iterate through rows and label selected ones
    for idx, row in df_squares.iterrows():
        if row['Selected']:
            df_squares.at[idx, 'Label Nr'] = label_nr
            label_nr += 1
        else:
            df_squares.at[idx, 'Label Nr'] = None  # Clear label for unselected rows

    # Restore original order
    df_squares.sort_index(inplace=True)


def label_selected_squares_and_tracks(df_squares, df_tracks):
    """
    Assigns label numbers to selected squares in descending order of 'Nr Tracks'
    and propagates labels to the corresponding tracks DataFrame.

    Optimized for performance using vectorized operations.
    """

    # Step 1: Sort by 'Nr Tracks' in descending order             #ToDO Do we handle indices correctly??
    df_squares.set_index('Square Nr', drop=False, inplace=True)
    df_squares = df_squares.sort_values(by='Nr Tracks', ascending=False).copy()

    # Step 2: Generate labels for selected squares
    df_squares['Label Nr'] = None  # Initialize the column
    selected_indices = df_squares.loc[df_squares['Selected']].index
    df_squares.loc[selected_indices, 'Label Nr'] = range(1, len(selected_indices) + 1)

    # Step 3: Restore the original order
    df_squares = df_squares.sort_index()

    # Step 4: Propagate labels to df_tracks
    # Merge the Label Nr column with df_tracks using 'Square Nr' and 'Ext Recording Name' as keys
    df_squares.reset_index(drop=True, inplace=True)
    df_tracks = df_tracks.merge(
        df_squares[['Square Nr', 'Ext Recording Name', 'Label Nr']],
        on=['Square Nr', 'Ext Recording Name'],
        how='left',
        suffixes=('', '_from_squares')  # Avoid '_x' and '_y', rename the merged Label Nr
    )
    df_tracks['Label Nr'] = df_tracks['Label Nr_from_squares']  # Use the merged Label Nr
    df_tracks.drop(columns=['Label Nr_from_squares'], inplace=True)  # Remove the extra column

    # Step 5: Clean up any unselected rows in df_tracks
    # df_tracks['Label Nr'] = df_tracks['Label Nr'].fillna(0).astype(int)

    return df_squares, df_tracks


def relabel_tracks(df_squares, df_tracks):
    """
    Propagates labels from df_squares to df_tracks based on 'Square Nr' and 'Ext Recording Name'.
    Requires tracks and squares of the recording to be selected and labeled.
    """
    # Merge the Label Nr column with df_tracks using 'Square Nr' and 'Ext Recording Name' as keys
    df_squares.reset_index(drop=True, inplace=True)
    df_tracks = df_tracks.merge(
        df_squares[['Square Nr', 'Ext Recording Name', 'Label Nr']],
        on=['Square Nr', 'Ext Recording Name'],
        how='left',
        suffixes=('', '_from_squares')  # Avoid '_x' and '_y', rename the merged Label Nr
    )
    df_tracks['Label Nr'] = df_tracks['Label Nr_from_squares']  # Use the merged Label Nr
    df_tracks.drop(columns=['Label Nr_from_squares'], inplace=True)  # Remove the extra column
    df_tracks.set_index('Unique Key', inplace=True, drop=True)
    return df_squares, df_tracks
