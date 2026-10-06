> Historical prototype document. Its architecture and performance claims are not current validation evidence. See [current implementation status](docs/IMPLEMENTATION_STATUS.md) and [README](README.md).

# AI-IDS/SOC Project Overview

## Table of Contents
1. [Project Goal](#project-goal)
2. [System Architecture](#system-architecture)
3. [How It Works](#how-it-works)
4. [Tools and Technologies](#tools-and-technologies)
5. [Key Components](#key-components)
6. [Data Flow](#data-flow)
7. [Model Training and Evaluation](#model-training-and-evaluation)
8. [Frontend Dashboard](#frontend-dashboard)
9. [Installation and Setup](#installation-and-setup)
10. [Usage](#usage)
11. [Troubleshooting](#troubleshooting)

---

## Project Goal

The AI-IDS/SOC project is a comprehensive **Intrusion Detection System (IDS)** and **Security Operations Center (SOC)** platform that combines multiple detection techniques to identify network attacks and malicious command activities in real-time. The system aims to:

- **Detect network-based attacks** using machine learning models (Isolation Forest, Random Forest, and Graph Neural Networks)
- **Monitor command-line activities** for malicious patterns using both regex-based rules and AI models
- **Provide real-time alerts** through a web-based dashboard
- **Enable model retraining** using labeled data from actual network traffic
- **Offer comprehensive metrics** and model comparison capabilities

The primary objective is to create a production-ready security monitoring solution that can be deployed in enterprise environments to detect and alert on potential security threats.

---

## System Architecture

The system follows a **modular, microservices-inspired architecture** with the following main components:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Network       │    │   Command       │    │   System        │
│   Traffic       │───▶│   Monitoring    │───▶│   Monitoring    │
│   Capture       │    │   (CMD)         │    │   (Logs)        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Backend Server                              │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │   Flow          │  │   Command       │  │   Alert         │ │
│  │   Models        │  │   Detector      │  │   Management    │ │
│  │   (ML/GNN)      │  │   (Regex/AI)    │  │   System        │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │   Database      │  │   API           │  │   WebSocket     │ │
│  │   (SQLite)      │  │   Endpoints     │  │   (Real-time)   │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Frontend Dashboard                           │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │   Network       │  │   Command       │  │   System        │ │
│  │   Alerts        │  │   Alerts        │  │   Logs          │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │   Model         │  │   Metrics       │  │   Heatmap       │ │
│  │   Comparison    │  │   KPIs          │  │   Visualization │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

---

## How It Works

### 1. Network Traffic Analysis

**Flow Capture:**
- The system uses **Scapy** to capture network packets from network interfaces
- Packets are aggregated into **network flows** (5-tuple: src_ip, dst_ip, src_port, dst_port, protocol)
- Each flow is characterized by features: duration, packet count, byte count, packet sizes, etc.

**Feature Extraction:**
```python
features = {
    'duration': flow_duration,
    'pkt_count': total_packets,
    'byte_count': total_bytes,
    'src2dst_pkts': packets_src_to_dst,
    'dst2src_pkts': packets_dst_to_src,
    'mean_pkt_size': average_packet_size
}
```

**ML Model Scoring:**
- **Isolation Forest**: Unsupervised anomaly detection
- **Random Forest**: Supervised classification with probability outputs
- **Graph Neural Network**: Flow relationship analysis using k-NN graphs

### 2. Command Monitoring

**Hybrid Detection:**
- **Regex-based patterns**: 47 predefined malicious command patterns
- **AI-based detection**: Transformer model trained on malicious vs benign commands
- **Real-time monitoring**: System command execution tracking

### 3. Alert Generation

**Severity Classification:**
- Scores are normalized to 0-1 range
- Severity levels: LOW, MEDIUM, HIGH, CRITICAL
- Threshold-based alerting with configurable sensitivity

**Alert Storage:**
- All alerts stored in SQLite database
- Includes raw flow data, model scores, and metadata
- Supports historical analysis and model retraining

---

## Tools and Technologies

### Core Technologies

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Backend Framework** | Flask + Flask-SocketIO | Web server and real-time communication |
| **Database** | SQLite | Alert storage and model comparisons |
| **Machine Learning** | scikit-learn, PyTorch, PyTorch Geometric | ML model implementation |
| **Network Capture** | Scapy | Packet capture and flow creation |
| **Frontend** | HTML5, CSS3, JavaScript | Dashboard interface |
| **Real-time Updates** | Socket.IO | Live alert streaming |

### Machine Learning Stack

| Library | Usage |
|---------|-------|
| **scikit-learn** | Isolation Forest, Random Forest, StandardScaler |
| **PyTorch** | Neural network foundations |
| **PyTorch Geometric** | Graph Neural Network implementation |
| **NumPy** | Numerical computations |
| **pandas** | Data manipulation (training) |

### Security Monitoring Tools

| Tool | Function |
|------|----------|
| **Regex Engine** | Pattern matching for malicious commands |
| **System Monitor** | Command execution tracking |
| **Port Scan Detection** | Network reconnaissance detection |
| **Flow Aggregation** | Network session analysis |

---

## Key Components

### 1. Backend Server (`detector_server.py`)

**Main Responsibilities:**
- UDP listener for flow data
- ML model scoring orchestration
- Alert severity classification
- REST API endpoints
- WebSocket real-time updates
- Database operations

**Key Functions:**
```python
# Core detection pipeline
def udp_listener():
    # Receive flow features via UDP
    # Apply ML models
    # Classify severity
    # Store alerts

# API endpoints
@app.route('/api/alerts')
@app.route('/api/model-metrics')
@app.route('/api/model-comparisons')
@app.route('/api/cmd-detections')
```

### 2. Flow Model Ensemble (`flow_model_ensemble.py`)

**Model Orchestration:**
- Coordinates three ML models
- Handles feature scaling
- Implements ensemble logic
- Provides per-model explanations

**Scoring Pipeline:**
```python
def score_flow(features):
    # 1. Vectorize and scale features
    # 2. Score with Isolation Forest
    # 3. Score with Random Forest
    # 4. Score with GNN (if available)
    # 5. Aggregate ensemble decision
    # 6. Return scores and explanations
```

### 3. GNN Flow Model (`gnn_flow_model.py`)

**Graph Construction:**
- Builds k-NN graphs from flow features
- Uses Graph Convolutional Networks
- Maintains sliding window for temporal context

**Architecture:**
```python
class FlowGCN(torch.nn.Module):
    def __init__(self, input_dim, hidden_dim=32):
        self.conv1 = GCNConv(input_dim, hidden_dim)
        self.conv2 = GCNConv(hidden_dim, 1)
```

### 4. Command Detector (`cmd_detector_hybrid.py`)

**Dual Approach:**
- **Regex Engine**: Fast pattern matching
- **AI Model**: Contextual understanding
- **Hybrid Logic**: Combines both for high accuracy

### 5. Frontend Dashboard (`frontend/index.html`)

**Real-time Interface:**
- Live alert streaming via WebSocket
- Interactive tables and visualizations
- Model performance metrics
- System status monitoring

---

## Data Flow

### 1. Network Flow Processing

```
Network Packets → Scapy Capture → Flow Aggregation → Feature Extraction → UDP Send → Backend ML Scoring → Alert Generation → Dashboard Display
```

### 2. Command Monitoring

```
System Commands → Command Monitor → Regex/AI Analysis → Threat Classification → Alert Storage → Real-time Notification
```

### 3. Model Training Pipeline

```
Labeled Data → Feature Extraction → Model Training → Threshold Optimization → Model Artifact Storage → Backend Reload → Updated Detection
```

---

## Model Training and Evaluation

### Training Data Sources

1. **Synthetic Training Data** (`training_data/`)
   - `benign_flows.csv`: Normal network traffic patterns
   - `attack_flows.csv`: Various attack scenarios
   - `normal_flows.csv`: Additional benign patterns

2. **Live Labeled Data** (`alerts.db`)
   - Ground truth labels from `send_real_attacks.py`
   - Continuous learning capability
   - Real-world traffic patterns

### Model Retraining Process

```bash
# Retrain models with latest labeled data
python backend/retrain_flow_models_from_db.py --db alerts.db --sources payload

# Retrain GNN (if needed)
python backend/gnn_flow_model.py train
```

### Performance Metrics

| Metric | Formula | Interpretation |
|--------|---------|----------------|
| **TPR (True Positive Rate)** | TP / (TP + FN) | Attack detection rate |
| **FPR (False Positive Rate)** | FP / (FP + TN) | False alarm rate |
| **Confidence** | Avg(score when flagged) | Model certainty |
| **Consistency** | 1 - stddev(scores) | Score stability |
| **Unique Rate** | Unique catches / Total attacks | Model contribution |

---

## Frontend Dashboard

### Main Views

1. **Network Traffic View**
   - Real-time flow table
   - Alert severity filtering
   - Detailed flow information

2. **Command Monitoring View**
   - Malicious command detection
   - Confidence scores
   - Pattern matching details

3. **Model Comparison View**
   - Per-model performance metrics
   - TPR/FPR comparisons
   - Confidence and consistency analysis

### Real-time Features

- **WebSocket Integration**: Live updates without page refresh
- **Auto-refresh**: Configurable polling intervals
- **Interactive Filtering**: Severity and type-based filtering
- **Detailed Drill-downs**: Click-to-expand information

---

## Installation and Setup

### Prerequisites

```bash
# Python 3.8+ required
pip install -r requirements.txt

# Optional: GNN support
pip install torch torch-geometric
```

### Database Initialization

The system automatically creates and initializes the SQLite database on first run:
- `alerts.db`: Main storage for alerts and model comparisons
- Tables: `alerts`, `network_flows`, `cmd_detections`, `model_comparisons`

### Configuration Files

| File | Purpose |
|------|---------|
| `flow_model_config.json` | ISO/RF model thresholds and features |
| `gnn_flow_config.json` | GNN model parameters and threshold |
| `cmd_patterns.json` | Regex patterns for command detection |

---

## Usage

### Starting the System

```bash
# Activate virtual environment
source .venv/bin/activate  # Linux/Mac
# or
.venv\Scripts\activate     # Windows

# Start the backend server
python backend/detector_server.py

# In another terminal, start flow capture
python backend/flow_extractor.py

# Access the dashboard
# Open http://localhost:5000 in browser
```

### Sending Test Attacks

```bash
# Send simulated attacks with ground truth labels
python send_real_attacks.py

# Send fileless malware simulations
python backend/simulate_/simulate_fileless.py
```

### Model Retraining

```bash
# Retrain with latest labeled data
python backend/retrain_flow_models_from_db.py --db alerts.db --sources payload

# Restart backend to load new models
# Metrics will update on next dashboard refresh
```

---

## Troubleshooting

### Common Issues

1. **GNN FPR = 100%**
   - **Cause**: Threshold too low for score distribution
   - **Fix**: Run calibration script to set appropriate threshold

2. **TPR = 0% for all models**
   - **Cause**: Feature mismatch between training and live data
   - **Fix**: Retrain models with DB-labeled flows

3. **Continuous CRITICAL alerts**
   - **Cause**: Alert thresholds too sensitive
   - **Fix**: Adjust ensemble scoring and alert gating

4. **Models not loading**
   - **Cause**: Missing model artifacts or config files
   - **Fix**: Train models first or check file paths

### Debug Commands

```bash
# Check model metrics
curl http://localhost:5000/api/model-metrics?window=200

# Verify database contents
sqlite3 alerts.db "SELECT COUNT(*) FROM model_comparisons WHERE ground_truth IS NOT NULL;"

# Test flow extraction
python backend/flow_extractor.py --test-mode
```

### Performance Optimization

1. **Database Size**: Periodic cleanup of old alerts
2. **Memory Usage**: Adjust sliding window sizes
3. **CPU Usage**: Limit model retraining frequency
4. **Network Load**: Filter interfaces for packet capture

---

## Future Enhancements

### Planned Features

1. **Advanced ML Models**
   - LSTM for temporal pattern analysis
   - Autoencoder for anomaly detection
   - Ensemble stacking techniques

2. **Threat Intelligence Integration**
   - IOC matching
   - Reputation scoring
   - Geolocation analysis

3. **Scalability Improvements**
   - PostgreSQL support
   - Distributed processing
   - Microservices architecture

4. **Advanced Visualizations**
   - Attack timeline view
   - Network topology mapping
   - Threat hunting interface

---

## Conclusion

The AI-IDS/SOC project represents a comprehensive approach to modern threat detection, combining traditional security monitoring with advanced machine learning techniques. Its modular architecture allows for continuous improvement and adaptation to emerging threats, while the real-time dashboard provides security analysts with the tools needed for effective threat detection and response.

The system is designed to be:
- **Production-ready**: Robust error handling and logging
- **Scalable**: Modular components and efficient data structures
- **Maintainable**: Clear code organization and documentation
- **Extensible**: Plugin architecture for new detection methods
- **User-friendly**: Intuitive dashboard with real-time updates

For questions, issues, or contributions, please refer to the project documentation and code comments throughout the codebase.
