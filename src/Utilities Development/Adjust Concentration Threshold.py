import os
import pandas as pd


def process_experiment_info(file_path):
    df = pd.read_csv(file_path)

    # Ensure required columns exist
    required_columns = {"Cell Type", "Probe Type", "Adjuvant", "Concentration", "Threshold", "Process", "Probe"}
    if not required_columns.issubset(df.columns):
        print(f"Skipping {file_path}: Missing required columns.")
        return

    # First, set all Process flags to 'No'
    df["Process"] = "No"

    # Define conditions and corresponding actions
    conditions = [
        (("BMDC", "Epitope", "CytD"), 10, 5),
        (("CHO-MR", "Epitope", "CytD"), 5, 10),
        (("BMDC", "Epitope", 'No'), 10, 5),
        (("BMDC", "Simple", 'No'), 10, 5),
        (("CHO-MR", "Epitope", 'No'), 5, 5),
        (("CHO-MR", "Simple", 'No'), 1, 5)
    ]

    valid_probes = {"1 Mono", "2 Mono", "6 Mono", "1 Tri", "2 Tri", "6 Tri", "Control"}

    for (cell_type, probe_type, adjuvant), conc_value, threshold in conditions:
        mask = (df["Cell Type"] == cell_type) & (df["Probe Type"] == probe_type) & (
                df["Adjuvant"] == adjuvant)

        df.loc[mask & (df["Concentration"] == conc_value), "Threshold"] = threshold
        df.loc[mask & (df["Concentration"] == conc_value) & df["Probe"].isin(valid_probes), "Process"] = "Yes"

    # Save changes back to the file
    df.to_csv(file_path, index=False)
    print(f"Updated: {file_path}")


def traverse_and_edit(root_dir):
    for subdir in next(os.walk(root_dir))[1]:  # Get immediate subdirectories
        file_path = os.path.join(root_dir, subdir, "Experiment info.csv")
        if os.path.isfile(file_path):
            process_experiment_info(file_path)


if __name__ == "__main__":
    root_directory = '/Users/hans/Paint Source - New Processing/Regular Probes'
    traverse_and_edit(root_directory)