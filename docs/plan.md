# Hybrid AI-IDS Project Plan

## Dataset Recommendations

### For System Logs:
- **SEC-Reps**: Contains Windows system logs with various attack scenarios
- **UNSW-NB15**: Includes both network and system features
- **ADFA-LD**: Linux dataset for host-based intrusion detection
- **CTU-13**: Contains botnet traffic with system-level indicators

### For Hybrid Detection:
- **DARPA-1998/1999**: Classic dataset with both network and host data
- **ISCX-2012**: Includes network packets and system logs
- **Custom Lab Environment**: Generate your own hybrid dataset

## System Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Network Logs  │    │   System Logs  │    │   Threat Intel  │
│   (CICIDS-2017) │    │   (SEC-Reps)   │    │   Feeds         │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          ▼                      ▼                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Data Preprocessing Layer                     │
│  • Normalization  • Feature Engineering  • Synchronization     │
└─────────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Feature Fusion Engine                        │
│  • Temporal Alignment  • Correlation Analysis  • Enrichment    │
└─────────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────┐
│                 Hybrid AI Detection Models                       │
│  • Ensemble Learning  • Deep Learning  • Graph Neural Networks │
└─────────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Alert & Response System                       │
│  • Correlation  • Prioritization  • Automated Response          │
└─────────────────────────────────────────────────────────────────┘
```

## Project Phases

### Phase 1: Foundation (Weeks 1-2)
- **Environment Setup**: Docker containers for isolated testing
- **Data Collection**: Download and prepare CICIDS-2017 + system log datasets
- **Baseline Research**: Literature review of hybrid IDS approaches
- **Tool Selection**: Python, TensorFlow/PyTorch, ELK Stack

### Phase 2: Data Engineering (Weeks 3-4)
- **Log Parsers**: Build parsers for network packets, Windows/Linux logs
- **Data Synchronization**: Timestamp alignment across sources
- **Feature Engineering**: Extract meaningful features from both log types
- **Data Quality**: Handle missing values, normalization, balancing

### Phase 3: Attack Simulation (Weeks 5-6)
- **Test Environment**: Virtual machines with vulnerable services
- **Attack Scenarios**:
  - **Fileless Malware**: PowerShell-based attacks
  - **Ransomware**: Simulated encryption processes
  - **MITM**: ARP spoofing, SSL stripping
  - **DNS Attacks**: DNS tunneling, cache poisoning
  - **Payload Injection**: SQL injection, code injection
- **Data Generation**: Capture both network and system logs during attacks

### Phase 4: Model Development (Weeks 7-8)
- **Feature Fusion**: Combine network and system features
- **Model Selection**: 
  - Random Forest for baseline
  - LSTM for temporal patterns
  - Graph Neural Networks for correlation analysis
- **Training Pipeline**: Cross-validation, hyperparameter tuning

### Phase 5: Evaluation & Optimization (Weeks 9-10)
- **Metrics**: Accuracy, precision, recall, F1-score, ROC-AUC
- **Real-time Testing**: Stream processing capabilities
- **Performance**: Latency, throughput, resource usage
- **Comparison**: Against network-only and system-only baselines

### Phase 6: Deployment & Documentation (Weeks 11-12)
- **Production Setup**: Containerized deployment
- **API Development**: RESTful interface for alerts
- **Real-time Monitoring**: Implement network sniffing (pyshark/scapy) and system log watching.
- **Dashboard**: Real-time visualization (Grafana/Kibana)
- **Documentation**: Technical paper, user manual

## Attack Simulation Matrix

| Attack Type | Network Indicators | System Indicators | Detection Approach |
|-------------|-------------------|-------------------|-------------------|
| Fileless Malware | C2 traffic, DNS queries | PowerShell logs, process creation | Behavioral analysis |
| Ransomware | Network scanning, file transfer | File system changes, process execution | Anomaly detection |
| MITM | ARP packets, SSL handshake | Network interface changes | Pattern matching |
| DNS Attack | DNS queries, responses | DNS cache modifications | Protocol analysis |
| Payload Injection | HTTP requests, SQL queries | Application logs, process memory | Signature + anomaly |

## Key Novelty Contributions

1. **Multi-source Correlation**: Real-time correlation between network packets and system events
2. **Temporal Feature Fusion**: Time-synchronized feature extraction from heterogeneous sources
3. **Attack Chain Detection**: End-to-end attack visibility across network and host boundaries
4. **Adaptive Learning**: Models that learn from both network patterns and system behaviors