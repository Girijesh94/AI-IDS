#!/usr/bin/env python3
"""
Main Data Preprocessing Pipeline for Hybrid AI-IDS
Orchestrates parsing, synchronization, feature engineering, and data quality.
"""

import pandas as pd
from pathlib import Path

# Import all our preprocessing modules
from preprocessors.network_parser import NetworkLogParser
from preprocessors.system_parser import SystemLogParser
from preprocessors.synchronizer import DataSynchronizer
from preprocessors.feature_engineer import FeatureEngineer
from preprocessors.data_quality import DataQuality

def main():
    """Main function to run the entire data preprocessing pipeline."""
    print("Starting Hybrid AI-IDS Data Engineering Pipeline (Phase 2)")
    print("="*60)

    # Define paths
    # TODO: Update this path to where your CICIDS-2017 data is located
    network_data_path = Path('../data/cicids-2017/MachineLearningCVE/')
    system_data_path = Path('../data/system_logs/') # Placeholder
    output_path = Path('../data/processed/')
    output_path.mkdir(exist_ok=True)

    # --- 1. Log Parsing ---
    network_parser = NetworkLogParser()
    system_parser = SystemLogParser()

    # For now, we'll just process the network data as a baseline
    try:
        network_df = network_parser.parse(network_data_path)
    except FileNotFoundError as e:
        print(f"\nError: {e}")
        print("Please download the CICIDS-2017 dataset and place the CSVs in the correct directory.")
        print("Expected directory structure: data/cicids-2017/MachineLearningCVE/")
        return

    # System log parsing will be integrated after attack simulation (Phase 3)
    system_df = system_parser.parse(system_data_path)

    # --- 2. Data Synchronization ---
    synchronizer = DataSynchronizer()
    # In the full pipeline, we would synchronize network_df and system_df
    # For now, we'll work with the network data.
    # synchronized_df = synchronizer.synchronize(network_df, system_df)
    current_df = network_df

    # --- 3. Feature Engineering ---
    feature_engineer = FeatureEngineer()
    featured_df = feature_engineer.engineer_features(current_df)

    # --- 4. Data Quality ---
    data_quality_processor = DataQuality(target_column='label')
    processed_df = data_quality_processor.process(featured_df)

    # --- 5. Save Processed Data ---
    output_file = output_path / 'processed_cicids2017.parquet'
    print(f"\nSaving processed data to: {output_file}")
    processed_df.to_parquet(output_file, index=False)
    print("✅ Processed data saved successfully.")

    print("\n" + "="*60)
    print("Phase 2: Data Engineering complete.")
    print("Next step is Phase 3: Attack Simulation.")

if __name__ == "__main__":
    main()
