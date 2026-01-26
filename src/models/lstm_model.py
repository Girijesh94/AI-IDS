#!/usr/bin/env python3
"""
LSTM Model for Hybrid AI-IDS
Captures temporal patterns in attack sequences.
"""

import pandas as pd
import numpy as np
from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.layers import LSTM, Dense, Dropout
from .base_model import BaseModel

class LSTMModel(BaseModel):
    """LSTM-based model for intrusion detection."""

    def __init__(self, input_shape, num_classes):
        super().__init__()
        self.input_shape = input_shape
        self.num_classes = num_classes
        self.model = self._build_model()

    def _build_model(self):
        """Builds the Keras LSTM model."""
        model = Sequential([
            LSTM(64, input_shape=self.input_shape, return_sequences=True),
            Dropout(0.2),
            LSTM(32),
            Dropout(0.2),
            Dense(16, activation='relu'),
            Dense(self.num_classes, activation='softmax')
        ])
        model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])
        return model

    def train(self, X_train: np.ndarray, y_train: np.ndarray, epochs=10, batch_size=32, **kwargs):
        """Trains the LSTM model."""
        print("Training LSTM model...")
        # Note: LSTM requires data to be in a 3D shape [samples, timesteps, features]
        # This reshaping needs to be done in the training pipeline.
        self.model.fit(X_train, y_train, epochs=epochs, batch_size=batch_size, **kwargs)
        print("Training complete.")

    def predict(self, X_test: np.ndarray) -> np.ndarray:
        """Makes predictions using the trained LSTM model."""
        print("Making predictions with LSTM model...")
        return np.argmax(self.model.predict(X_test), axis=1)

    def save(self, file_path: str):
        """Saves the trained Keras model."""
        print(f"Saving model to {file_path}...")
        self.model.save(file_path)
        print("Model saved.")

    def load(self, file_path: str):
        """Loads a trained Keras model."""
        print(f"Loading model from {file_path}...")
        self.model = load_model(file_path)
        print("Model loaded.")
