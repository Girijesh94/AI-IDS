#!/usr/bin/env python3
"""
Main Model Training Pipeline for Hybrid AI-IDS
"""

import pandas as pd
from pathlib import Path
from sklearn.model_selection import train_test_split

# Import models
from models.random_forest_model import RandomForestModel
# from models.lstm_model import LSTMModel
# from models.gnn_model import GNNModel

def main():
    """Main function to run the model training pipeline."""
    print("Starting Hybrid AI-IDS Model Training Pipeline (Phase 4)")
    print("="*60)

    # --- 1. Load Processed Data ---
    processed_data_path = Path('data/processed/processed_cicids2017.parquet')
    if not processed_data_path.exists():
        print(f"Error: Processed data not found at {processed_data_path}")
        print("Please run the main_preprocessor.py script first.")
        return

    print(f"Loading data from {processed_data_path}...")
    df = pd.read_parquet(processed_data_path)

    # --- 2. Train/Test Split ---
    X = df.drop(columns=['label'])
    y = df['label']

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    print("Data split into training and testing sets.")
    print(f"  - Training set shape: {X_train.shape}")
    print(f"  - Testing set shape: {X_test.shape}")

    # --- 3. Train Models ---
    models_path = Path('../models/')
    models_path.mkdir(exist_ok=True)

    # --- Random Forest ---
    rf_model = RandomForestModel()
    rf_model.train(X_train, y_train)
    rf_model.save(str(models_path / 'random_forest_model.joblib'))

    # --- LSTM (Structure) ---
    # print("\nLSTM training would be here.")
    # Note: LSTM requires data reshaping (e.g., into sequences)
    # and one-hot encoding for the target variable.

    # --- GNN (Structure) ---
    # print("\nGNN training would be here.")
    # Note: GNN requires building a graph from the data.

    print("\n" + "="*60)
    print("Phase 4: Model Development (Training) complete.")
    print("Next step is to evaluate the trained models.")

if __name__ == "__main__":
    main()
