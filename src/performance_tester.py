#!/usr/bin/env python3
"""
Performance Testing Pipeline for Hybrid AI-IDS
Measures model latency and throughput.
"""

import pandas as pd
import time
import joblib
from pathlib import Path
from sklearn.model_selection import train_test_split

def main():
    """Main function to run the performance tests."""
    print("Starting Performance Testing Pipeline")
    print("="*60)

    # --- 1. Load Data and Optimized Model ---
    processed_data_path = Path('../data/processed/processed_cicids2017.parquet')
    model_path = Path('../models/random_forest_optimized_model.joblib')

    if not processed_data_path.exists() or not model_path.exists():
        print("Error: Processed data or optimized model not found.")
        print("Please run the preprocessing and optimization scripts first.")
        return

    df = pd.read_parquet(processed_data_path)
    X = df.drop(columns=['label'])
    y = df['label']

    _, X_test, _, _ = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    print(f"Loading optimized model from {model_path}...")
    model = joblib.load(model_path)

    # --- 2. Test Latency ---
    print("\n--- Testing Prediction Latency ---")
    # Test on a single instance
    single_instance = X_test.iloc[[0]]
    start_time = time.perf_counter()
    model.predict(single_instance)
    end_time = time.perf_counter()
    latency = (end_time - start_time) * 1000 # in milliseconds
    print(f"  - Latency for a single prediction: {latency:.4f} ms")

    # Test on a batch of instances
    batch_size = 1000
    batch = X_test.head(batch_size)
    start_time = time.perf_counter()
    model.predict(batch)
    end_time = time.perf_counter()
    batch_latency = (end_time - start_time) * 1000 # in milliseconds
    avg_batch_latency = batch_latency / batch_size
    print(f"  - Average latency for a batch of {batch_size}: {avg_batch_latency:.4f} ms per instance")

    # --- 3. Test Throughput ---
    print("\n--- Testing Prediction Throughput ---")
    test_duration = 10 # seconds
    predictions = 0
    start_time = time.time()

    while (time.time() - start_time) < test_duration:
        # Simulate a stream of data
        sample_indices = range(len(X_test))
        for i in sample_indices:
            if (time.time() - start_time) >= test_duration:
                break
            model.predict(X_test.iloc[[i]])
            predictions += 1
    
    throughput = predictions / test_duration
    print(f"  - Throughput: {throughput:.2f} predictions per second")

    print("\n" + "="*60)
    print("Performance testing complete.")

if __name__ == "__main__":
    main()
