#!/usr/bin/env python3
"""
Data Quality Pipeline for Hybrid AI-IDS
Handles normalization, encoding, and class balancing.
"""

import pandas as pd
from sklearn.preprocessing import MinMaxScaler, LabelEncoder
from imblearn.over_sampling import SMOTE

class DataQuality:
    """Applies data quality and preprocessing steps to the dataset."""

    def __init__(self, target_column='label'):
        """Initializes the data quality processor.

        Args:
            target_column (str): The name of the target/label column.
        """
        self.target_column = target_column
        self.scaler = MinMaxScaler()
        self.encoder = LabelEncoder()

    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Performs initial data cleaning."""
        # Drop columns with too many missing values (if any remain)
        # Convert data types
        # ... more cleaning steps
        return df

    def scale_and_encode(self, df: pd.DataFrame) -> pd.DataFrame:
        """Applies scaling to numerical features and encoding to categorical ones."""
        print("Scaling and encoding data...")
        
        # Separate features and target
        X = df.drop(columns=[self.target_column])
        y = df[self.target_column]

        # Identify numerical and categorical columns
        numerical_cols = X.select_dtypes(include=['number']).columns
        categorical_cols = X.select_dtypes(include=['object', 'category']).columns

        # Scale numerical features
        if not numerical_cols.empty:
            X[numerical_cols] = self.scaler.fit_transform(X[numerical_cols])
            print(f"  - Scaled {len(numerical_cols)} numerical columns.")

        # Encode categorical features
        for col in categorical_cols:
            X[col] = self.encoder.fit_transform(X[col])
        if not categorical_cols.empty:
            print(f"  - Encoded {len(categorical_cols)} categorical columns.")

        # Encode target variable
        y_encoded = self.encoder.fit_transform(y)

        # Combine back into a single DataFrame
        processed_df = X
        processed_df[self.target_column] = y_encoded

        return processed_df

    def balance_classes(self, df: pd.DataFrame) -> pd.DataFrame:
        """Balances the dataset using SMOTE for the minority classes."""
        print("Balancing classes using SMOTE...")
        
        X = df.drop(columns=[self.target_column])
        y = df[self.target_column]

        # Apply SMOTE
        smote = SMOTE()
        X_resampled, y_resampled = smote.fit_resample(X, y)

        print(f"  - Original dataset shape: {X.shape}")
        print(f"  - Resampled dataset shape: {X_resampled.shape}")

        balanced_df = pd.DataFrame(X_resampled, columns=X.columns)
        balanced_df[self.target_column] = y_resampled

        return balanced_df

    def process(self, df: pd.DataFrame) -> pd.DataFrame:
        """Runs the full data quality pipeline."""
        print("\nStarting data quality processing...")
        df = self.clean_data(df)
        df = self.scale_and_encode(df)
        # Balancing should typically be done only on the training set
        # df = self.balance_classes(df)
        print("Data quality processing complete.")
        return df
