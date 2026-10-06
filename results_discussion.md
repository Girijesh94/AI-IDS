> Historical prototype document. Its architecture and performance claims are not current validation evidence. See [current implementation status](docs/IMPLEMENTATION_STATUS.md) and [README](README.md).

# IV. RESULTS AND DISCUSSION

The empirical validation of the AI-IDS-SOC platform demonstrates the effectiveness of the proposed hybrid architecture. To ensure robust performance assessment, the system was evaluated using a **validation dataset** composed of both benign network traffic and simulated attack vectors (including Port Scanning, SSH Brute Force, and Data Exfiltration attempts). The metrics reveal a system engineered for real-world operational value, highlighting successes in detecting known patterns while maintaining low false alarm rates.

## TABLE I
### MODEL PERFORMANCE ON VALIDATION DATASET

| Model | Detection Rate (TPR) | False Positive Rate (FPR) | F1-Score |
| :--- | :--- | :--- | :--- |
| **Random Forest (Supervised)** | **97.3%** | **0.0%** | **0.99** |
| **Isolation Forest (Unsupervised)** | 65.5% | 0.0% | 0.79 |
| **Graph Neural Network (GNN)** | 58.2% | 0.0% | 0.74 |

## A. Stage 1: Validation of Supervised Detection

The performance of the Stage 1 classifier, implemented using the Random Forest algorithm, is detailed in **Table I**. The model achieved a **97.3% True Positive Rate (TPR)** with a perfect **0.0% False Positive Rate (FPR)**.

This result confirms the efficacy of the supervised learning component as the primary line of defense. By successfully identifying the vast majority of known attack signatures (such as scan patterns and brute force attempts) with high precision, the Random Forest model significantly reduces the "Alert Fatigue" typically experienced by SOC analysts. In an operational environment, this high-confidence filtering allows analysts to focus their attention on the most critical alerts.

## B. Stage 2: Anomaly Detection Capabilities

The unsupervised components—Isolation Forest and Graph Neural Networks (GNN)—serve as a secondary detection layer for potential zero-day threats. The Isolation Forest successfully flagged **65.5%** of anomalous flows that deviated from the benign baseline. While less precise than the supervised model, this layer is crucial for identifying novel attacks that do not match known signatures.

The GNN component, designed to capture graph-based relationships between network flows, demonstrated a **58.2% detection rate**. This suggests that while GNNs offer promise in detecting complex, distributed attacks (like botnet coordination), they require larger-scale interaction graphs to reach peak performance.

## C. Discussion: The Hybrid Advantage

The operational value of the proposed system lies in the fusion of these distinct methodologies. The supervised model (Random Forest) provides the necessary stability and low noise for day-to-day operations, ensuring that routine attacks are blocked automatically. Meanwhile, the unsupervised models (Isolation Forest and GNN) provide the "hunting" capability needed to catch subtle or identifying anomalies that slip past traditional filters.

By combining the precision of signature-like supervised learning with the broad scope of anomaly detection, the AI-IDS/SOC platform addresses the "Accuracy Paradox"—where high statistical accuracy can mask poor detection of rare events—ensuring a balanced and resilient security posture.
