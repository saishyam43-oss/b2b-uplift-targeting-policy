# =========================================
# Script: record_schema.py
# Purpose: Generate technical documentation of the dataset
# =========================================

import pandas as pd
import os
import io
from pathlib import Path

RAW_DIR = Path("data/raw")
RAW_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_FILE = RAW_DIR/"validation/schema_manifest.txt"

files = [
    RAW_DIR/"accounts_raw.csv",
    RAW_DIR/"users_raw.csv",
    RAW_DIR/"user_activity_daily_raw.csv",
    RAW_DIR/"interventions_raw.csv",
    RAW_DIR/"outcomes_raw.csv",
    RAW_DIR/"latent_uplift_groups_hidden.csv"
]

with open(OUTPUT_FILE, "w") as f:
    f.write("PROJECT SCHEMA MANIFEST\n")
    f.write("=======================\n\n")

    for file_path in files:
        file_name = os.path.basename(file_path)
        f.write(f"FILE: {file_name}\n")
        f.write("-" * (len(file_name) + 6) + "\n")

        try:
            # Read only header and first few rows to infer types
            df = pd.read_csv(file_path, nrows=100)

            # Buffer to catch df.info() output
            buf = io.StringIO()
            df.info(buf=buf)

            # Extract relevant lines from info()
            lines = buf.getvalue().split("\n")

            # Write row count estimation
            # (We strictly count lines for speed/accuracy in doc)
            with open(file_path, "rb") as raw_f:
                row_count = sum(1 for _ in raw_f) - 1
            f.write(f"Rows: {row_count:,}\n")
            f.write("Columns:\n")

            # Parse info output for cleaner look
            # Usually strict tabular format is better for docs
            col_info = df.dtypes.reset_index()
            col_info.columns = ["Column Name", "Data Type"]

            # Check for nulls in sample
            nulls = df.isnull().sum()
            col_info["Sample Nulls"] = nulls.values

            # Format as string table
            f.write(col_info.to_string(index=False))
            f.write("\n\n")

        except FileNotFoundError:
            f.write("ERROR: File not found.\n\n")
        except Exception as e:
            f.write(f"ERROR: {str(e)}\n\n")

    f.write("=======================\n")
    f.write("End of Manifest\n")

print(f"Schema manifest generated at: {OUTPUT_FILE}")
