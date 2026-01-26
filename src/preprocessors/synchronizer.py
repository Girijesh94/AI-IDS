#!/usr/bin/env python3
"""
Data Synchronizer for Hybrid AI-IDS
Aligns multiple data sources based on timestamps.
"""

import pandas as pd

class DataSynchronizer:
    """Synchronizes network and system log DataFrames."""

    def __init__(self, time_column='timestamp', tolerance_ms=500):
        """Initializes the synchronizer.

        Args:
            time_column (str): The name of the timestamp column.
            tolerance_ms (int): The time tolerance in milliseconds for merging events.
        """
        self.time_column = time_column
        self.tolerance = pd.Timedelta(milliseconds=tolerance_ms)

    def synchronize(self, network_df: pd.DataFrame, system_df: pd.DataFrame) -> pd.DataFrame:
        """Synchronizes two DataFrames based on their timestamps.

        This uses an as-of merge, which is efficient for time-series data.
        It will match each system event to the nearest preceding network event
        within the specified tolerance.

        Args:
            network_df: DataFrame of network events.
            system_df: DataFrame of system events.

        Returns:
            A merged DataFrame containing synchronized events.
        """
        print("Synchronizing network and system data...")

        if network_df.empty or system_df.empty:
            print("  - One or both DataFrames are empty. Skipping synchronization.")
            return pd.concat([network_df, system_df])

        # Ensure timestamps are sorted
        network_df = network_df.sort_values(by=self.time_column)
        system_df = system_df.sort_values(by=self.time_column)

        # Perform the as-of merge
        hybrid_df = pd.merge_asof(
            left=system_df,
            right=network_df,
            on=self.time_column,
            direction='nearest',
            tolerance=self.tolerance,
            suffixes=('_sys', '_net')
        )

        print(f"  - Synchronization complete. Merged shape: {hybrid_df.shape}")
        return hybrid_df
