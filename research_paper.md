> Historical prototype document. Its architecture and performance claims are not current validation evidence. See [current implementation status](docs/IMPLEMENTATION_STATUS.md) and [README](README.md).

# Developing a Hybrid AI-Based Intrusion Detection System and Security Operations Center (SOC) Platform

**Date:** October 26, 2023
**Project:** AI-IDS/SOC
**Subject:** Research Paper

---

## Abstract

As cyber threats become increasingly sophisticated, traditional signature-based Intrusion Detection Systems (IDS) often fail to detect novel or complex attacks. This paper presents the development of a comprehensive AI-powered IDS and Security Operations Center (SOC) platform designed to detect network anomalies and malicious command activities in real-time. The proposed system employs a hybrid ensemble of machine learning models—specifically Isolation Forest, Random Forest, and Graph Neural Networks (GNN)—to analyze network traffic flows. Additionally, it integrates a dual-method command monitor utilizing both regex patterns and AI models for host-based intrusion detection. Signal processing and alert generation are managed via a Flask-based backend with real-time WebSocket communication to an interactive frontend dashboard. Evaluation on a labeled dataset of 200 samples demonstrates the system's efficacy, with the Random Forest model achieving a **97.3% True Positive Rate (TPR)** and **0.0% False Positive Rate (FPR)**, highlighting its potential as a robust production-ready security solution.

---

## 1. Introduction

The rapid expansion of digital infrastructure has widened the attack surface for malicious actors, necessitating advanced security monitoring solutions. Traditional IDS solutions typically rely on predefined signatures, making them effective against known threats but vulnerable to zero-day attacks and polymorphic malware. To address these limitations, machine learning (ML) and artificial intelligence (AI) have emerged as critical technologies for identifying anomalous behavior indicative of intrusion.

This project aims to bridge the gap between academic ML research and practical security application by building a modular, real-time AI-IDS/SOC platform. The system is designed not only to detect network-based attacks (such as Denial of Service and port scanning) but also to monitor host-based activities like malicious command execution. By providing a unified dashboard for visualization and alerting, the platform offers security analysts actionable intelligence to mitigate threats promptly.

## 2. System Architecture

The AI-IDS/SOC platform follows a modular, microservices-inspired architecture comprising three main layers: Data Collection, Analysis/Detection, and Visualization/Alerting.

### 2.1 Core Components

1.  **Data Collection Layer**:
    *   **Network Capture**: Utilizes **Scapy** to capture raw packets from network interfaces. Packets are aggregated into 5-tuple network flows (Source IP, Destination IP, Source Port, Destination Port, Protocol).
    *   **System Monitoring**: Tracks system logs and command-line execution for host-based monitoring.

2.  **Analysis & Detection Layer (Backend)**:
    *   **Backend Server**: Built with **Flask**, this component acts as the central orchestrator. It listens for UDP flow data, manages the ML pipeline, and handles database operations via **SQLite**.
    *   **ML Engine**: Orchestrates the ensemble of models (Isolation Forest, Random Forest, GNN) to score network flows.
    *   **Command Detector**: A hybrid module combining regex pattern matching with an AI transformer model to classify command severity.

3.  **Visualization Layer (Frontend)**:
    *   **Dashboard**: A real-time web interface built with HTML5 and JavaScript. It connects to the backend via **Socket.IO** to display streaming alerts, flow metrics, and system status without requiring page refreshes.

## 3. Methodology

### 3.1 Feature Engineering

Raw network packets are processed into statistical features suitable for machine learning algorithms. The following six key features are extracted for each flow:
*   **Duration**: The time span of the flow.
*   **Packet Count**: Total number of packets transferred.
*   **Byte Count**: Total volume of data transferred.
*   **Source-to-Dest Packets**: Number of packets sent by the initiator.
*   **Dest-to-Source Packets**: Number of packets sent in response.
*   **Mean Packet Size**: Average size of packets in the flow.

### 3.2 Machine Learning Models

The system employs a multi-model ensemble approach to maximize detection capabilities:

1.  **Isolation Forest (Unsupervised)**: Used for anomaly detection. It isolates observations by randomly selecting a feature and a split value. It is effective at identifying outliers (potential zero-day attacks) that deviate significantly from normal traffic patterns.
2.  **Random Forest (Supervised)**: A robust classification algorithm trained on labeled datasets of benign and malicious traffic. It provides high accuracy and interpretability.
3.  **Graph Neural Network (GNN)**: Implemented using **PyTorch Geometric**, this model analyzes the relationships between flows by constructing k-Nearest Neighbor (k-NN) graphs. This allows the system to detect complex, distributed attack patterns that single-flow analysis might miss.

### 3.3 Hybrid Command Detection

To protect the host system, a specialized command monitor is implemented:
*   **Regex Engine**: Matches commands against a database of 47 known malicious patterns (e.g., reverse shells, data exfiltration commands).
*   **AI Model**: Uses natural language processing techniques to evaluate the context and intent of commands that do not match specific signatures.

## 4. Implementation Details

The technological stack was chosen for performance and ease of deployment:
*   **Language**: Python 3.8+
*   **Libraries**: Scikit-learn (ML), PyTorch (DL), Scapy (Network), Flask (Web).
*   **Database**: SQLite for lightweight, file-based persistence of alerts and metrics.

The `detector_server.py` script serves as the entry point, initializing the database, loading pre-trained models, and starting the UDP listener for flow data. It exposes REST endpoints for historical data retrieval and manages the WebSocket namespace for real-time alerts.

## 5. Results and Evaluation

The system was evaluated using a dataset of **200 labeled real-world samples**, consisting of **110 attack flows** and **90 benign flows**.

### 5.1 Performance Metrics

| Model | Detection Rate (TPR) | False Positive Rate (FPR) | Confidence |
| :--- | :--- | :--- | :--- |
| **Random Forest** | **97.3%** | **0.0%** | 98.8% |
| **Isolation Forest** | 65.5% | 0.0% | 76.4% |
| **GNN** | 58.2% | 0.0% | 68.1% |

### 5.2 Analysis

*   **Random Forest**: Demonstrated superior performance, detecting nearly all attacks (107/110) with zero false alarms. This makes it the primary driver for high-confidence alerts in the system.
*   **Isolation Forest**: Served as a reliable backup, detecting a majority of anomalies (65.5%). Its value lies in identifying deviations without requiring labeled attack data.
*   **GNN**: The Graph Neural Network showed promising results (58.2% TPR) considering it is an experimental feature for this architecture. It successfully identified attacks that had complex structural patterns, though it requires further tuning for standalone reliability.

## 6. Conclusion and Future Work

This project successfully demonstrates the feasibility of a production-ready, AI-driven IDS/SOC platform. By combining the precision of supervised learning (Random Forest) with the anomaly detection capabilities of unsupervised learning (Isolation Forest), the system provides a balanced defense against both known and unknown threats. The inclusion of a real-time dashboard and host-based command monitoring creates a holistic security tool suitable for small to medium-sized enterprise networks.

**Future Work**:
*   **GNN Optimization**: Improving the GNN architecture to better capture temporal dependencies in network flows.
*   **Scalability**: Migrating from SQLite to PostgreSQL to support larger historical datasets.
*   **Advanced Models**: Integrating LSTM (Long Short-Term Memory) networks for better time-series anomaly detection.
*   **Threat Intelligence**: Incorporating external feeds (IOCs) to enrich alert data.
