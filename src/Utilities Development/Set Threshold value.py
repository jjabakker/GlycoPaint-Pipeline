import os
import pandas as pd

def update_thresholds_in_csv(root_dir, target_filename='Experiment Info.csv', column_name='Threshold', new_value=8):
    for dirpath, dirnames, filenames in os.walk(root_dir):
        if target_filename in filenames:
            full_path = os.path.join(dirpath, target_filename)
            try:
                df = pd.read_csv(full_path)
                if column_name in df.columns:
                    df[column_name] = new_value
                    df.to_csv(full_path, index=False)
                    print(f"Updated: {full_path}")
                else:
                    print(f"Skipped (no '{column_name}' column): {full_path}")
            except Exception as e:
                print(f"Error processing {full_path}: {e}")

# Example usage
update_thresholds_in_csv('/Users/hans/Paint Source - Treshold 8')