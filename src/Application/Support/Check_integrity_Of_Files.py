import pandas as pd

from src.Fiji.LoggerConfig import (
    paint_logger)


def check_files_integrity_failed(df_all_recordings, df_experiment_info, df_all_squares):

    failed = False

    # # Check if DataFrames are empty
    # if df_all_recordings.empty:
    #     paint_logger.error  (f"No records found in All recordings")
    #     failed = True
    # if df_all_recordings.empty:
    #     paint_logger.error  (f"No recordings found in All Experiments")
    #     failed = True


    if not df_all_recordings is None:

        # Find any experiment names different from experiment date
        normalized_name = df_all_recordings['Experiment Name'].astype(str).str.strip()
        normalized_date = df_all_recordings['Experiment Date'].astype(str).str.strip()
        mismatched_rows = df_all_recordings[normalized_name != normalized_date]
        if not mismatched_rows.empty:
            failed = True
            paint_logger.error(f"In All Recordings there are recordings found where Experiment Name and Date do not match")
            for name in mismatched_rows['Ext Recording Name']:
                paint_logger.error(name)


        # Find any row with NaN Adjuvant values
        nan_rows = df_all_recordings[df_all_recordings['Adjuvant'].isna()]
        if not nan_rows.empty:
            failed = True
            paint_logger.error(f"In All Recordings there are Adjuvants with NaN values")
            for name in nan_rows['Ext Recording Name']:
                paint_logger.error(name)

        # Find any row with empty Adjuvant values
        empty_rows = df_all_recordings[df_all_recordings['Adjuvant'].astype(str).str.strip() == '']
        if not empty_rows.empty:
            failed = True
            paint_logger.error(f"In All Recordings there are Adjuvant values not specified")
            for name in empty_rows['Ext Recording Name']:
                paint_logger.error(name)

        # Find any row with Threshold not numeric
        non_numeric = df_all_recordings[~pd.to_numeric(df_all_recordings['Threshold'], errors='coerce').notna()]
        if not non_numeric.empty:
            failed = True
            paint_logger.error(f"In All Recordings there are non numeric Threshold values")
            for name in non_numeric['Ext Recording Name']:
                paint_logger.error(name)


        # Find any row with Concentration not numeric
        non_numeric = df_all_recordings[~pd.to_numeric(df_all_recordings['Concentration'], errors='coerce').notna()]
        if not non_numeric.empty:
            failed = True
            paint_logger.error(f"In All Recordings there are non numeric Concentration values")
            for name in non_numeric['Ext Recording Name']:
                paint_logger.error(name)

    if not df_experiment_info is None:

        # Find any row with NaN Adjuvant values
        nan_rows = df_experiment_info[df_experiment_info['Adjuvant'].isna()]
        if not nan_rows.empty:
            failed = True
            paint_logger.error(f"In Experiment Info there are Adjuvants with NaN values")
            for name in nan_rows['Recording Name']:
                paint_logger.error(name)

        # Find any row with empty Adjuvant values
        empty_rows = df_experiment_info[df_experiment_info['Adjuvant'].astype(str).str.strip() == '']
        if not empty_rows.empty:
            failed = True
            paint_logger.error(f"In Experiment Info there are Adjuvant values not specified")
            for name in empty_rows['Recording Name']:
                paint_logger.error(name)

        # Find any row with Threshold not numeric
        non_numeric = df_experiment_info[~pd.to_numeric(df_experiment_info['Threshold'], errors='coerce').notna()]
        if not non_numeric.empty:
            failed = True
            paint_logger.error(f"In Experiment Info there are non numeric Threshold values")
            for name in non_numeric['Recording Name']:
                paint_logger.error(name)

        # Find any row with Concentration not numeric
        non_numeric = df_experiment_info[~pd.to_numeric(df_experiment_info['Concentration'], errors='coerce').notna()]
        if not non_numeric.empty:
            failed = True
            paint_logger.error(f"In Experiment Info there are non numeric Concentration values")
            for name in non_numeric['Recording Name']:
                paint_logger.error(name)

    return failed