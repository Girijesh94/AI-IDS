#!/usr/bin/env python3
"""
Model Optimization Pipeline for Hybrid AI-IDS
Performs hyperparameter tuning to find the best model settings.
"""

import pandas as pd
import joblib
from pathlib import Path
from sklearn.model_selection import GridSearchCV, train_test_split
from sklearn.ensemble import RandomForestClassifier

def main():
    """Main function to run the model optimization pipeline."""
    print("Starting Model Optimization Pipeline")
    print("="*60)

    # --- 1. Load Data ---
    processed_data_path = Path('../data/processed/processed_cicids2017.parquet')
    if not processed_data_path.exists():
        print(f"Error: Processed data not found at {processed_data_path}")
        return

    df = pd.read_parquet(processed_data_path)
    X = df.drop(columns=['label'])
    y = df['label']

    # Use a smaller subset of data for faster grid search if necessary
    # _, X_sample, _, y_sample = train_test_split(X, y, test_size=0.1, random_state=42, stratify=y)

    X_train, _, y_train, _ = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    # --- 2. Define Parameter Grid ---
    # This is a small grid for demonstration. A real search would be more extensive.
    param_grid = {
        'n_estimators': [50, 100],       # Number of trees in the forest
        'max_depth': [10, 20, None],     # Maximum depth of the tree
        'min_samples_leaf': [1, 2, 4],   # Minimum number of samples required at a leaf node
        'max_features': ['sqrt', 'log2'] # Number of features to consider when looking for the best split
    }

    # --- 3. Run Grid Search ---
    print("Starting GridSearchCV for Random Forest...")
    print(f"Parameter grid: {param_grid}")

    rf = RandomForestClassifier(random_state=42, n_jobs=-1)
    grid_search = GridSearchCV(estimator=rf, param_grid=param_grid, cv=3, n_jobs=-1, verbose=2, scoring='f1_weighted')
    
    # Fit the grid search to the data
    grid_search.fit(X_train, y_train)

    # --- 4. Display Results and Save Best Model ---
    print("\nGridSearchCV complete.")
    print(f"Best parameters found: {grid_search.best_params_}")
    print(f"Best F1-score from search: {grid_search.best_score_:.4f}")

    best_model = grid_search.best_estimator_

    # Save the best model
    models_path = Path('../models/')
    optimized_model_path = models_path / 'random_forest_optimized_model.joblib'
    joblib.dump(best_model, optimized_model_path)
    print(f"\nOptimized model saved to {optimized_model_path}")

    print("\n" + "="*60)
    print("Model optimization complete.")

if __name__ == "__main__":
    main()
