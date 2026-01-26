#!/usr/bin/env python3
"""
Network Log Parser for CICIDS-2017 Dataset
"""

import pandas as pd
import numpy as np
from pathlib import Path
import glob

class NetworkLogParser:
    """Parses network logs from the CICIDS-2017 dataset."""

    def __init__(self):
        pass

    def parse(self, data_directory: Path) -> pd.DataFrame:
        """Parses all CICIDS-2017 CSV files in a directory.

        Args:
            data_directory: Path to the directory containing CICIDS-2017 CSV files.

        Returns:
            A pandas DataFrame with the combined and cleaned data.
        """
        print(f"Parsing network logs from: {data_directory}")
        
        csv_files = glob.glob(str(data_directory / "*.csv"))
        if not csv_files:
            raise FileNotFoundError(f"No CSV files found in {data_directory}")

        df_list = []
        for file_path in csv_files:
            print(f"  - Reading {Path(file_path).name}")
            try:
                df = pd.read_csv(file_path)
                df_list.append(df)
            except Exception as e:
                print(f"    Error reading {file_path}: {e}")

        if not df_list:
            raise ValueError("No data could be read from the CSV files.")

        df = pd.concat(df_list, ignore_index=True)

        # Clean column names
        df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_').str.replace('-', '_')

        # Handle infinity and NaN values
        df.replace([np.inf, -np.inf], np.nan, inplace=True)
        df.dropna(inplace=True)

        # Convert timestamp
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])

        print("\nParsing complete.")
        print(f"  - Total samples: {len(df)}")
        print(f"  - Columns: {df.columns.tolist()}")

        return df
