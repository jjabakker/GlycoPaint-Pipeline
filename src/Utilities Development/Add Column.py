import pandas as pd

file = '/Users/hans/Paint/Paint Source Squares Sweep/Results/5/All Squares.csv'
# Load the CSV
df = pd.read_csv(file)

# Add the new column with a fixed value
df['Nr Of Squares'] = 5

# Save back to CSV (overwrite or to a new file)
df.to_csv(file, index=False)