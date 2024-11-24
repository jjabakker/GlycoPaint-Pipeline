import warnings

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.optimize import OptimizeWarning
from scipy.optimize import curve_fit

from src.Fiji.LoggerConfig import paint_logger


def mono_exp(x, m, t, b):
    # Define the exponential decay function that will be used for fitting
    try:
        calc = m * np.exp(-t * x) + b
    except OverflowError:
        paint_logger.error(f"Overflow error in monoExp: m = x = {x}, {m}, t = {t}, b = {b}")
        calc = 0
    except (RuntimeWarning, RuntimeError):
        paint_logger.error(f"RuntimeWarning/Error in monoExp: m = x = {x}, {m}, t = {t}, b = {b}")
        calc = 0
    except FloatingPointError:
        paint_logger.error(f"Floating Point Error in monoExp: m = x = {x}, {m}, t = {t}, b = {b}")
        calc = 0
    return calc


def compile_duration(tracks):
    """
    The function produces a frequency distribution of the track durations.
    :param tracks: A dataframe containing the histogram data
    :return: A dataframe with two columns containing the histogram
    """

    # histdata is returned as a Pandas Series, make histdata into a dataframe
    # The index values are the duration, and the first (and only) column is 'Frequency'
    histdata = tracks.groupby('Track Duration')['Track Duration'].size()
    histdata = pd.DataFrame(histdata)
    histdata.columns = ['Frequency']
    histdata['Track Duration'] = histdata.index

    # This is alternative code to the above
    # histdata_1 = tracks['Track Duration'].value_counts().reset_index()
    # histdata_1.columns = ['Track Duration', 'Frequency']
    # histdata_1 = histdata_1.sort_values(by='Track Duration')
    # histdata_1 = histdata_1.set_index('Track Duration', drop=False)

    return histdata


def curve_fit_and_plot(
        plot_data,
        plot_max_x=5,
        plot_title='Duration Histogram',
        file="",
        plot_to_screen=False,
        plot_to_file=False,
        verbose=False):
    """
    The funct ion fits an exponential decay function to the data and plots the result.
    Function = m * np.exp(-t * x) + b
    """

    # The curve_fit function expects x and y Numpy arrays
    x = np.asarray(plot_data["Track Duration"])
    y = np.asarray(plot_data["Frequency"])
    nr_tracks = len(plot_data)

    # Perform the fit
    p0 = [2000, 4, 10]  # this is more what we see
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=RuntimeWarning)
            warnings.simplefilter("ignore", category=OptimizeWarning)
            params, cv = curve_fit(mono_exp, x, y, p0)

        m, t, b = params
    except ValueError:
        if verbose:
            paint_logger.error('CurveFitAndPlot: ydata or xdata contain NaNs, or incompatible options are used')
        return -2, 0
    except RuntimeError:
        if verbose:
            paint_logger.warning('CurveFitAndPlot: The least-squares optimisation fails')
        return -2, 0
    except OptimizeWarning:
        if verbose:
            paint_logger.warning('CurveFitAndPlot: Covariance of the parameters can not be estimated')
        return -2, 0
    except Exception:
        if verbose:
            paint_logger.warning('CurveFitAndPlot: Exception')
        return -2, 0

    tau_per_sec = (1 / t)

    # Determine the quality of the fit
    squared_diffs = np.square(y - mono_exp(x, m, t, b))
    squared_diffs_from_mean = np.square(y - np.mean(y))
    if np.sum(squared_diffs_from_mean) == 0:
        r_squared = 0
    else:
        try:
            r_squared = 1 - np.sum(squared_diffs) / np.sum(squared_diffs_from_mean)
        except (OptimizeWarning, RuntimeError, RuntimeWarning):
            paint_logger.warning('CurveFitAndPlot: OptimizeWarning, RuntimeError, RuntimeWarning')
            r_squared = 0

    if plot_to_file:
        fig, ax = plt.subplots()
        ax.scatter(x, y, linewidth=1.0, label="Data")
        ax.plot(x, mono_exp(x, m, t, b), linewidth=1.0, label="Fitted")

        x_middle = plot_max_x / 2 - plot_max_x * 0.1
        y_middle = y.max() / 2
        plt.text(x_middle, y_middle, f"Tau = {tau_per_sec * 1e3:.0f} ms")
        plt.text(x_middle, 0.8 * y_middle, f"R2 = {r_squared:.4f} ms")
        plt.text(x_middle, 0.6 * y_middle, f"Number or tracks is {nr_tracks}")
        plt.text(x_middle, 0.4 * y_middle, f"Zoomed in from 0 to {plot_max_x:.0f} s")

        plt.xlim([0, plot_max_x])

        ax.set_xlabel('Duration [in s]')
        ax.set_ylabel('Number of tracks')
        ax.set_title(plot_title)
        ax.legend()

        # Plot to screen per default, but don't when it has been overruled
        # Plot to file when a filename has been specified

        if plot_to_screen:
            plt.show()
        if file != "":
            fig.savefig(file)
            if verbose:
                paint_logger.debug("\nWriting plot file: " + file)

    # Inspect the parameters
    if verbose:
        print("")
        print(f'R² = {r_squared:.4f}')
        print(f'Y = {m:.3f} * e^(-{t:.3f} * x) + {b:.3f}')
        print(f'Tau = {tau_per_sec * 1e3:.0f} ms')

    plt.close()

    # Convert to milliseconds
    tau_per_sec *= 1000
    return tau_per_sec, r_squared
