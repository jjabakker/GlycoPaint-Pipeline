import pandas as pd


def csv_file_identical(file1, file2, columns=None):
    try:
        # Load the CSV files into DataFrames
        df1 = pd.read_csv(file1, low_memory=False)
        df2 = pd.read_csv(file2, low_memory=False)

        # If columns are not specified, compare all columns
        if columns is None:
            columns = df1.columns.intersection(df2.columns)

        # Check if the shapes of selected columns are identical
        if df1[columns].shape != df2[columns].shape:
            print("The selected columns do not have the same shape.")
            return False

        # Select specified columns for comparison
        selected_df1 = df1[columns].copy()
        selected_df2 = df2[columns].copy()

        # Ensure data types are consistent
        selected_df2 = selected_df2.astype(selected_df1.dtypes.to_dict())

        # Strip whitespace from string columns
        for col in columns:
            if selected_df1[col].dtype == 'object':  # 'object' dtype in pandas often means strings
                selected_df1[col] = selected_df1[col].str.strip()
                selected_df2[col] = selected_df2[col].str.strip()

        # Reset index to ensure a row-by-row comparison
        selected_df1.reset_index(drop=True, inplace=True)
        selected_df2.reset_index(drop=True, inplace=True)

        # Check if the columns in both DataFrames are identical
        comparison = selected_df1.equals(selected_df2)

        if comparison:
            print("The selected columns are identical.")
            return True
        else:
            print("The selected columns are NOT identical.")
            differences = selected_df1.compare(selected_df2, keep_shape=True, keep_equal=False)
            print("Differences:\n", differences)
            return False

    except Exception as e:
        print(f"An error occurred: {e}")
        return False


if __name__ == '__main__':
    version_old = 'v19'
    version_new = 'v20'

    print("\nComparing All Squares files...")
    file1a = f'/Users/hans/Paint Data - {version_old}/New Probes/Paint New Probes - 20 Squares/240812/All Squares.csv'
    file1b = f'/Users/hans/Paint Data - {version_new}/New Probes/Paint New Probes - 20 Squares/240812/All Squares.csv'
    csv_file_identical(file1a, file1b, columns=['Tau', 'Density', 'Diffusion Coefficient', 'Label Nr'])

    print("\nComparing All Recordings files...")
    file1a = f'/Users/hans/Paint Data - {version_old}/New Probes/Paint New Probes - 20 Squares/240812/All Recordings.csv'
    file1b = f'/Users/hans/Paint Data - {version_new}/New Probes/Paint New Probes - 20 Squares/240812/All Recordings.csv'
    csv_file_identical(file1a, file1b, columns=['Tau', 'Density', 'Nr Tracks'])

    print("\nComparing All Tracks files...")
    file1a = f'/Users/hans/Paint Data - {version_old}/New Probes/Paint New Probes - 20 Squares/240812/All Tracks.csv'
    file1b = f'/Users/hans/Paint Data - {version_new}/New Probes/Paint New Probes - 20 Squares/240812/All Tracks.csv'
    csv_file_identical(file1a, file1b, columns=['Label Nr', 'Square Nr'])
