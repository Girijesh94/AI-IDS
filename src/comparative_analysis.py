#!/usr/bin/env python3
"""
Comparative Analysis Pipeline for Hybrid AI-IDS
Compares Hybrid vs. Network-Only vs. System-Only models.
"""

import pandas as pd
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from models.random_forest_model import RandomForestModel

def define_feature_sets(columns):
    """Defines network and system feature sets based on column names."""
    # This is an approximation based on common feature names from the datasets.
    # In a real scenario, this would be more rigorously defined.
    network_features = [col for col in columns if 'flow' in col or 'packet' in col or 'fwd' in col or 'bwd' in col]
    network_features += ['dst_port', 'protocol', 'timestamp']
    
    # All other features are considered 'system' features for this analysis
    system_features = [col for col in columns if col not in network_features and col != 'label']
    
    # Remove duplicates
    network_features = list(set(network_features) & set(columns))
    system_features = list(set(system_features) & set(columns))

    return network_features, system_features

def train_and_evaluate(model, X_train, y_train, X_test, y_test):
    """Helper function to train a model and return its performance metrics."""
    model.train(X_train, y_train)
    y_pred = model.predict(X_test)
    
    return {
        'accuracy': accuracy_score(y_test, y_pred),
        'precision': precision_score(y_test, y_pred, average='weighted'),
        'recall': recall_score(y_test, y_pred, average='weighted'),
        'f1_score': f1_score(y_test, y_pred, average='weighted')
    }

def main():
    """Main function to run the comparative analysis."""
    print("Starting Comparative Analysis Pipeline")
    print("="*60)

    # --- 1. Load Data ---
    processed_data_path = Path('../data/processed/processed_cicids2017.parquet')
    if not processed_data_path.exists():
        print(f"Error: Processed data not found at {processed_data_path}")
        return

    df = pd.read_parquet(processed_data_path)
    X = df.drop(columns=['label'])
    y = df['label']

    # --- 2. Define Feature Sets ---
    network_features, system_features = define_feature_sets(X.columns)
    print(f"Defined {len(network_features)} network features and {len(system_features)} system features.")

    feature_sets = {
        'Hybrid': X.columns.tolist(),
        'Network-Only': network_features,
        'System-Only': system_features
    }

    results = {}

    # --- 3. Run Analysis for each Feature Set ---
    for name, features in feature_sets.items():
        print(f"\n--- Training and Evaluating {name} Model ---")
        if not features:
            print(f"Skipping {name} model as no features were defined.")
            continue

        X_subset = X[features]
        X_train, X_test, y_train, y_test = train_test_split(
            X_subset, y, test_size=0.2, random_state=42, stratify=y
        )

        model = RandomForestModel()
        performance = train_and_evaluate(model, X_train, y_train, X_test, y_test)
        results[name] = performance
        print(f"{name} Model Performance: {performance}")

    # --- 4. Display Final Comparison ---
    results_df = pd.DataFrame(results).T
    print("\n" + "="*60)
    print("Final Performance Comparison:")
    print(results_df)

    # Save results
    output_path = Path('../models/')
    results_df.to_csv(output_path / 'comparative_analysis_results.csv')
    print(f"\nComparative analysis results saved to {output_path}")

if __name__ == "__main__":
    main()
