import pandas as pd
import os


def tau_for_cell_type_and_adjuvant(df, cell_type, adjuvant):

    # First filter for the specific conditions
    df_filtered = df[(df["Cell Type"] == cell_type) & (df["Adjuvant"] == adjuvant)]

    # Drop NaN values in relevant columns
    df_filtered = df_filtered.dropna(subset=["Probe", "Tau", "Unique Key"])

    # Drop negative Tau values
    df_filtered = df_filtered[df_filtered["Tau"] > 0]

    # Pivot the table to have each Probe's Tau value in separate columns
    try:
        df_pivot_table = df_filtered.pivot(
            index="Unique Key",  # Use Unique Key Combined as the row identifier
            columns="Probe",  # Use Probe as columns
            values="Tau"  # Display Tau values
        )
    except ValueError as e:
        print(f"Error during pivot: {e}")
        exit()

    # Reset index and clean up
    df_pivot_table.reset_index(inplace=True)

    return df_pivot_table


def tau_for_probe_and_adjuvant(df, probe, adjuvant):

    # First filter for the specific conditions
    df_filtered = df[(df["Probe"] == probe) & (df["Adjuvant"] == adjuvant)]

    # Drop NaN values in relevant columns
    df_filtered = df_filtered.dropna(subset=["Cell Type", "Tau", "Unique Key"])

    # Drop negative Tau values
    df_filtered = df_filtered[df_filtered["Tau"] > 0]

    # Pivot the table to have each Probe's Tau value in separate columns
    try:
        df_pivot_table = df_filtered.pivot(
            index="Unique Key",  # Use Unique Key Combined as the row identifier
            columns="Cell Type",  # Use Probe as columns
            values="Tau"  # Display Tau values
        )
    except ValueError as e:
        print(f"Error during pivot: {e}")
        exit()

    # Reset index and clean up
    df_pivot_table.reset_index(inplace=True)

    return df_pivot_table


def main():
    # File path for input and output
    input_file = '/Users/hans/Paint Demo Set/Paint Demo/All Squares.csv'
    output_file = '/Users/Hans/Downloads/graphpad_table_with_keys.xlsx'

    # Load CSV file
    try:
        df = pd.read_csv(input_file)
    except FileNotFoundError:
        print(f"File not found: {input_file}")
        exit()

    df_result1 = tau_for_cell_type_and_adjuvant(df, 'BMDC', 'No')
    df_result2 = tau_for_probe_and_adjuvant(df, '1 Tri', 'No')

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
        df_result1.to_excel(writer, sheet_name="Sheet1", index=False)
        df_result2.to_excel(writer, sheet_name="Sheet2", index=False)

    print(f"Table successfully exported to {output_file}")

if __name__ == "__main__":
    main()