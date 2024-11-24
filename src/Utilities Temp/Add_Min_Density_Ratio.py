import os

import pandas as pd

paint_directory = '/Users/hans/Paint/Paint Regular Projects 30 squares'
image_dirs = os.listdir(paint_directory)
image_dirs.sort()
for image_dir in image_dirs:
    if 'Output' in image_dir:
        continue
    if os.path.isdir(os.path.join(paint_directory, image_dir)):
        df_batch = pd.read_csv(os.path.join(paint_directory, image_dir, 'batch.csv'), index_col=False)
        if {'Min Density Ratio'}.issubset(df_batch.columns):
            continue
        colnr = df_batch.columns.get_loc('Threshold')
        df_batch.insert(loc=colnr + 1, column='Min Density Ratio', value='30')
        df_batch.to_csv(os.path.join(paint_directory, image_dir, 'batch.csv'), index=False)
