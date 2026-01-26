#!/usr/bin/env python3
"""
Base Model for Hybrid AI-IDS
Defines the common interface for all detection models.
"""

from abc import ABC, abstractmethod
import pandas as pd

class BaseModel(ABC):
    """Abstract base class for detection models."""

    def __init__(self):
        self.model = None

    @abstractmethod
    def train(self, X_train: pd.DataFrame, y_train: pd.Series):
        """Trains the model."""
        pass

    @abstractmethod
    def predict(self, X_test: pd.DataFrame) -> pd.Series:
        """Makes predictions on new data."""
        pass

    @abstractmethod
    def save(self, file_path: str):
        """Saves the trained model to a file."""
        pass

    @abstractmethod
    def load(self, file_path: str):
        """Loads a trained model from a file."""
        pass
