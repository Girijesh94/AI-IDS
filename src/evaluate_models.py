#!/usr/bin/env python3
"""
Model Evaluation Pipeline for Hybrid AI-IDS
"""

import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score

# Import models
from models.random_forest_model import RandomForestModel

def main():
    """Main function to run the model evaluation pipeline."""
    print("Starting Hybrid AI-IDS Model Evaluation Pipeline")
    print("="*60)

    # --- 1. Load Data and Models ---
    processed_data_path = Path('../data/processed/processed_cicids2017.parquet')
    models_path = Path('../models/')

    if not processed_data_path.exists():
        print(f"Error: Processed data not found at {processed_data_path}")
        return

    df = pd.read_parquet(processed_data_path)
    X = df.drop(columns=['label'])
    y = df['label']

    # Use the same split as in training
    _, X_test, _, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # --- 2. Evaluate Random Forest Model ---
    rf_model_path = models_path / 'random_forest_model.joblib'
    if rf_model_path.exists():
        print("\n--- Evaluating Random Forest Model ---")
        rf_model = RandomForestModel()
        rf_model.load(str(rf_model_path))

        y_pred = rf_model.predict(X_test)

        # --- 3. Generate Reports ---
        # --- 3. Generate Reports ---
        report = classification_report(y_test, y_pred, output_dict=True)
        report_df = pd.DataFrame(report).transpose()
        
        print("\nClassification Report:")
        print(report_df)
        
        report_path = models_path / 'random_forest_classification_report.csv'
        report_df.to_csv(report_path)
        print(f"\nClassification report saved to {report_path}")

        # Confusion Matrix
        cm = confusion_matrix(y_test, y_pred)
        plt.figure(figsize=(12, 8))
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=report_df.index[:-3], yticklabels=report_df.index[:-3])
        plt.title('Random Forest Confusion Matrix')
        plt.ylabel('Actual')
        plt.xlabel('Predicted')
        cm_path = models_path / 'random_forest_confusion_matrix.png'
        plt.savefig(cm_path)
        print(f"Confusion matrix saved to {cm_path}")

        # Feature Importance
        feature_importances = pd.DataFrame(
            rf_model.model.feature_importances_,
            index = X_test.columns,
            columns=['importance']
        ).sort_values('importance', ascending=False)

        print("\nTop 10 Feature Importances:")
        print(feature_importances.head(10))

        plt.figure(figsize=(10, 8))
        sns.barplot(x=feature_importances.head(20).importance, y=feature_importances.head(20).index)
        plt.title('Top 20 Feature Importances')
        plt.tight_layout()
        fi_path = models_path / 'random_forest_feature_importance.png'
        plt.savefig(fi_path)
        print(f"Feature importance plot saved to {fi_path}")
    else:
        print("Random Forest model not found. Please train it first.")

    print("\n" + "="*60)
    print("Phase 4: Model Development (Evaluation) complete.")

if __name__ == "__main__":
    main()
