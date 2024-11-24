import sys

import matplotlib.pyplot as plt

from src.Fiji.LoggerConfig import paint_logger

heatmap_modes = {
    1: 'Tau',
    2: 'Density',
    3: 'Diffusion Coefficient',
    4: 'Max Track Duration',
    5: 'Total Track Duration'
}


# Function to convert RGB to HEX format
def _rgb_to_hex(rgb):
    return '#{:02x}{:02x}{:02x}'.format(int(rgb[0] * 255), int(rgb[1] * 255), int(rgb[2] * 255))


# Generate colors from a colormap
def get_colormap_colors(cmap_name, num_colors):
    cmap = plt.get_cmap(cmap_name)
    return [_rgb_to_hex(cmap(i / num_colors)) for i in range(num_colors)]


def get_color_index(value, var_max, var_min, nr_levels):
    var = max(value, 0)
    if var_max == var_min:
        return 0

    # Normalize the value to an index in the range of the color index (0-19)
    index = int((value - var_min) / (var_max - var_min) * (nr_levels - 1))

    return index


def get_heatmap_data(df_squares, df_all_squares, heatmap_mode, experiment_min_max=True):
    global heatmap_modes

    if df_all_squares.empty or df_squares.empty:
        paint_logger.error("Function 'display_heatmap' failed - No data available")
        sys.exit()

    if heatmap_mode in heatmap_modes:
        column_name = heatmap_modes[heatmap_mode]

        if not column_name in df_squares.columns:
            paint_logger.error(f"No data vailable for {column_name} - possibly Generate All tracks was not run")
            min_val = 0
            max_val = 0
            df_heatmap_data = None
            return df_heatmap_data, min_val, max_val

        if experiment_min_max:
            min_val = df_all_squares[column_name].min()
            max_val = df_all_squares[column_name].max()
        else:
            min_val = df_squares[column_name].min()
            max_val = df_squares[column_name].max()
        min_val = max(min_val, 0)

        df_heatmap_data = df_squares[[column_name]]

        # Change the name of the first colums to something independent of the actual parameter
        df_heatmap_data.columns = ['Value'] + df_heatmap_data.columns[1:].tolist()

        # There can be Nan values in the data, so we need to replace them
        df_heatmap_data = df_heatmap_data.fillna(0)

    else:
        paint_logger.error("Function 'get_heatmap_data' failed - Unknown heatmap mode")
        sys.exit()

    return df_heatmap_data, min_val, max_val
