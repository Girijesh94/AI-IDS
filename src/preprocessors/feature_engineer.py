#!/usr/bin/env python3
"""
Feature Engineering for Hybrid AI-IDS
Creates basic, advanced, and hybrid features.
"""

import pandas as pd

class FeatureEngineer:
    """Engineers features from raw and synchronized log data."""

    def __init__(self):
        pass

    def create_network_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Creates features from network data."""
        print("Creating network features...")
        # Example features:
        # df['flow_duration'] = (df['timestamp_end'] - df['timestamp_start']).dt.total_seconds()
        # df['bytes_per_sec'] = df['total_bytes'] / df['flow_duration']
        return df

    def create_system_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Creates features from system data."""
        print("Creating system features...")
        # Example features:
        # df['command_line_len'] = df['command_line'].str.len()
        # df['is_powershell_encoded'] = df['command_line'].str.contains('-enc', case=False)
        return df

    def create_hybrid_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Creates hybrid features combining network and system data.
        This is a key part of the project's novelty.
        """
        print("Creating hybrid features...")
        # These features require a synchronized DataFrame
        
        # Example 1: Network traffic per process
        # if 'process_name' in df.columns and 'total_fwd_packets' in df.columns:
        #     df['process_network_ratio'] = df.groupby('process_name')['total_fwd_packets'].transform('mean')

        # Example 2: User-based network behavior
        # if 'user_account' in df.columns and 'dst_port' in df.columns:
        #     df['user_unique_ports'] = df.groupby('user_account')['dst_port'].transform('nunique')

        print("Hybrid feature engineering structure is in place.")
        return df

    def engineer_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Main function to orchestrate feature engineering."""
        print("\nStarting feature engineering...")
        df = self.create_network_features(df)
        df = self.create_system_features(df)
        df = self.create_hybrid_features(df)
        print("Feature engineering complete.")
        return df
