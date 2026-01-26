# Hybrid AI-IDS: Intrusion Detection System

This project is a comprehensive, AI-powered Intrusion Detection System (IDS) that leverages a novel hybrid approach by analyzing both **network logs** and **system logs** to detect a wide range of cyber attacks.

## Features

- **Hybrid Detection**: Correlates network traffic with system-level events for higher accuracy.
- **Machine Learning Core**: Utilizes a suite of models (Random Forest, LSTM, GNN) for robust detection.
- **Real-time Monitoring**: Includes components to sniff live network traffic and monitor system logs.
- **REST API**: A Flask-based API to serve the trained model for real-time predictions.
- **Containerized**: Dockerfile for easy deployment and scalability.
- **Dashboard**: A Streamlit-based dashboard for visualizing live alerts.

## System Architecture

The system is designed in a modular way:
1.  **Data Preprocessing**: Scripts to parse, clean, synchronize, and engineer features from raw logs.
2.  **Model Training**: Pipelines to train and evaluate multiple AI models.
3.  **Real-time Deployment**: A containerized API that serves the best model.
4.  **Live Monitoring**: Scripts that capture live data and send it to the API.
5.  **Visualization**: A dashboard to display the results.

## Project Structure

```
ids-system/
├── data/                # Raw and processed datasets
├── docs/                # Project documentation (plan.md)
├── models/              # Saved model artifacts
├── notebooks/           # Jupyter notebooks for exploration
├── scripts/             # Helper scripts (e.g., download_datasets.py)
├── src/                 # Main source code
│   ├── api/             # Flask API for model serving
│   ├── models/          # Model implementations
│   ├── monitors/        # Real-time data collectors
│   ├── preprocessors/   # Data processing modules
│   ├── __init__.py
│   ├── comparative_analysis.py
│   ├── dashboard.py
│   ├── evaluate_models.py
│   ├── main_preprocessor.py
│   ├── optimize_model.py
│   └── train_models.py
├── Dockerfile           # For containerization
└── requirements.txt     # Project dependencies
```

## Setup and Installation

1.  **Clone the repository**:
    ```bash
    git clone <repository-url>
    cd ids-system
    ```

2.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Download Datasets**:
    -   Download the CICIDS-2017 dataset and place the CSVs in `data/cicids-2017/MachineLearningCVE/`.
    -   Run the script to download other datasets if needed:
        ```bash
        python scripts/download_datasets.py
        ```

## Usage Guide

### 1. Data Preprocessing
Run the main preprocessing pipeline to prepare the data for training.
```bash
python src/main_preprocessor.py
```

### 2. Model Training
Train the AI models on the processed data.
```bash
python src/train_models.py
```

### 3. Model Evaluation
Evaluate the performance of the trained models.
```bash
python src/evaluate_models.py
```

### 4. Run the API
Start the Flask API to serve the best model.
```bash
python src/api/app.py
```

### 5. Start Real-time Monitoring
In separate terminals, run the monitoring scripts.
```bash
# Terminal 1: Network Sniffer
python src/monitors/network_sniffer.py

# Terminal 2: System Monitor
python src/monitors/system_monitor.py
```

### 6. View the Dashboard
Launch the Streamlit dashboard to see live alerts.
```bash
streamlit run src/dashboard.py
```

## Future Work

- **Phase 3: Attack Simulation**: The project can be extended by building a dedicated simulation environment to generate custom, synchronized network and system log data for the specified attack scenarios. This would further enhance the model's accuracy and real-world applicability.
- **Advanced Models**: Fully implement and tune the LSTM and GNN models for potentially higher accuracy on complex and sequential attacks.
