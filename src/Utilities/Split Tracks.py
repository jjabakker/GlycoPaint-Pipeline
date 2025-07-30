import pandas as pd
import os

from src.Fiji.LoggerConfig import paint_logger

def split_tracks_by_cell_type(directory):

    paint_logger.info("Splitting tracks by cell type")
    paint_logger.info("")

    paint_logger.info("reading All Recordings ")
    df_recordings = pd.read_csv(f"{directory}/All Recordings.csv")

    paint_logger.info("Reading All Tracks")
    df_all_tracks = pd.read_csv(f"{directory}/All Tracks.csv")

    paint_logger.info("")

    unique_cell_types = df_recordings['Cell Type'].dropna().unique().tolist()
    for cell_type in unique_cell_types:
        paint_logger.info(f"Splitting tracks for {cell_type}...")
        safe_cell_type = cell_type.replace('/', '').replace('\\', '').replace(' ', ' ')
        recording_names_list = df_recordings[df_recordings['Cell Type'] == cell_type]['Ext Recording Name'].dropna().unique().tolist()
        df_all_tracks_for_cell_type = df_all_tracks[df_all_tracks['Ext Recording Name'].isin(recording_names_list)]
        if not df_all_tracks_for_cell_type.empty:
            df_all_tracks_for_cell_type = df_all_tracks_for_cell_type.reset_index(drop=True)
            df_all_tracks_for_cell_type.to_csv(os.path.join(directory, f"All Tracks - {safe_cell_type}.csv"), index=False)
            paint_logger.info(f"Tracks for cell type '{cell_type}' saved to {safe_cell_type}_Tracks.csv")
        else:
            paint_logger.info(f"No tracks found for cell type '{cell_type}'")

    paint_logger.info("")
    paint_logger.info("Splitting tracks by cell type completed.")


if __name__ == "__main__":
    split_tracks_by_cell_type('/Users/hans/Paint/Paint Data - v38/Regular Probes/Paint Regular Probes - 20 Squares')

