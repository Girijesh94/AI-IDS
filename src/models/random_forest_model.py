#!/usr/bin/env python3
"""
Random Forest Model for Hybrid AI-IDS
"""

import pandas as pd
import joblib
from sklearn.ensemble import RandomForestClassifier
from .base_model import BaseModel

class RandomForestModel(BaseModel):
    """Random Forest classifier for intrusion detection."""

    def __init__(self, n_estimators=100, random_state=42, **kwargs):
        super().__init__()
        self.model = RandomForestClassifier(
            n_estimators=n_estimators,
            random_state=random_state,
            n_jobs=-1, # Use all available cores
            **kwargs
        )

    def train(self, X_train: pd.DataFrame, y_train: pd.Series):
        """Trains the Random Forest model."""
        print("Training Random Forest model...")
        self.model.fit(X_train, y_train)
        print("Training complete.")

    def predict(self, X_test: pd.DataFrame) -> pd.Series:
        """Makes predictions using the trained model."""
        print("Making predictions with Random Forest model...")
        return self.model.predict(X_test)

    def save(self, file_path: str):
        """Saves the trained model to a file."""
        print(f"Saving model to {file_path}...")
        joblib.dump(self.model, file_path)
        print("Model saved.")

    def load(self, file_path: str):
        """Loads a trained model from a file."""
        print(f"Loading model from {file_path}...")
        self.model = joblib.load(file_path)
        print("Model loaded.")
