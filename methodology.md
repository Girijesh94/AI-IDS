# III. METHODOLOGY

This section introduces the proposed system model for the AI-IDS-SOC (Artificial Intelligence Intrusion Detection System & Security Operations Center). A multi-layered security mechanism has been implemented to address threats at different levels of the infrastructure. In the network layer, a flow-based analysis framework utilizing an ensemble of machine learning models—including a Graph Neural Network (GNN)—has been established to identify traffic anomalies. Similarly, in the host layer, a hybrid command monitoring system combines deterministic signature matching with probabilistic AI detection to identify malicious execution attempts. The distinct layers of the proposed model are shown in Figure 1. The proposed model is primarily divided into two subsections: i) Network Layer Security, and ii) Host Layer Security. The detailed descriptions of each layer have been elaborated in the following subsections.

## A. Network Layer Security

To implement network layer security, a robust ensemble framework combining three distinct machine learning algorithms: Isolation Forest, Random Forest, and Graph Neural Networks (GNN) is implemented. The Isolation Forest is utilized for unsupervised anomaly detection, identifying outliers that deviate from established baselines. The Random Forest classifier acts as a supervised learning component, providing high-confidence classifications for known attack patterns.

To capture the complex, non-Euclidean relationships between network flows, a Graph Neural Network (GNN) based approach is introduced. Unlike conventional deep learning models that treat network flows as independent instances, the GNN framework constructs a specific topology where flows are represented as nodes, and their feature similarities form edges.

### Graph Construction and Architecture
In this scenario, a k-Nearest Neighbor (k-NN) graph is constructed dynamically from a sliding window of network flows. Let $F = \{f_1, f_2, ..., f_n\}$ be the set of flow feature vectors. For each flow $f_i$, edges are created to its $k$ nearest neighbors based on Euclidean distance in the feature space. This graph structure enables the model to learn spatial relationships and propagating attack signatures across related flows.

The internal architecture of the GNN is based on Graph Convolutional Networks (GCN). The input node features are passed through two GCNConv layers. The first layer transforms the input dimension to a hidden dimension (32 units), followed by a Rectified Linear Unit (ReLU) activation function and a Dropout layer ($p=0.2$) to prevent overfitting. The second GCNConv layer maps the hidden features to a scalar output, which is then passed through a Sigmoid activation function to produce a probability score $[0, 1]$ indicating the likelihood of an attack.

## B. Host Layer Security

In the host layer, security is enforced by monitoring command-line interface (CLI) activities. A novel hybrid detection strategy combining Regex-based pattern matching and AI-based anomaly detection has been proposed and implemented, as shown in Algorithm 1. The Regex engine provides fast, deterministic detection of known malicious strings (e.g., encoded PowerShell, reverse shells), while the AI component employs an Isolation Forest model trained on linguistic features of shell commands to identify obfuscated or novel malicious sequences.

### Algorithm 1: Hybrid Hybrid Command Detection Strategy

**Input:** Command String $C$  
**Output:** Classification Verdict $V$ (Malicious/Benign), Contidence $Conf$

1: **Initialize** Regex Engine $R$ with pattern set $P$  
2: **Initialize** AI Model $M$ (Isolation Forest) and Scaler $S$  
3:  
4: /* Step 1: Deterministic Pattern Matching */  
5: $Match \leftarrow$ **RegexSearch**($C$, $P$)  
6: **if** $Match$ is Found **then**  
7: &nbsp;&nbsp;&nbsp;&nbsp;Determine Severity $Sev$ from pattern group (CRITICAL, HIGH, MEDIUM, LOW)  
8: &nbsp;&nbsp;&nbsp;&nbsp;**if** $Sev \in \{CRITICAL, HIGH\}$ **then**  
9: &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**return** (Malicious, High Confidence)  
10: &nbsp;&nbsp;&nbsp;&nbsp;**end if**  
11: **end if**  
12:  
13: /* Step 2: Probabilistic AI Analysis */  
14: $Feat \leftarrow$ **ExtractFeatures**($C$)  
15: $Feat_{scaled} \leftarrow$ **Transform**($Feat$, $S$)  
16: $Score_{anomaly} \leftarrow$ **Predict**($M$, $Feat_{scaled}$)  
17:  
18: /* Step 3: Fusion and Verdict */   
19: **if** $Score_{anomaly}$ indicates Anomaly **and** $Match$ is Found **then**  
20: &nbsp;&nbsp;&nbsp;&nbsp;**return** (Malicious, Very High Confidence) /* Confirmed by both */  
21: **else if** $Score_{anomaly}$ indicates Anomaly **then**  
22: &nbsp;&nbsp;&nbsp;&nbsp;**return** (Malicious, AI Confidence)  
23: **else if** $Match$ is Found **then**  
24: &nbsp;&nbsp;&nbsp;&nbsp;**return** (Malicious, Regex Confidence)  
25: **else**  
26: &nbsp;&nbsp;&nbsp;&nbsp;**return** (Benign, 0.0)  
27: **end if**

The AI component extracts features such as command length, entropy, and the count of special characters to form a feature vector. This vector is processed by the Isolation Forest to determine if the command structure deviates significantly from benign administrative operations.

---

## Suggested Diagrams for Inclusion

To adhere to the academic format and enhance the explanation, the following figures are recommended for inclusion in the "Methodology" section:

1.  **Fig. 1: Proposed System Model**
    *   **Description**: A high-level block diagram showing the two main protection layers.
    *   **Visuals**: Split the diagram into "Network Layer" (left) and "Host Layer" (right).
        *   *Network Layer*: Show "Traffic Capture" -> "Feature Extraction" -> "Ensemble Models (RF, IF, GNN)" -> "Verdict".
        *   *Host Layer*: Show "Command Input" -> "Hybrid Detector (Regex + AI)" -> "Verdict".
        *   Both outputs feeding into a central "Alert Database" and "Dashboard".

2.  **Fig. 2: GNN Architecture for Flow Analysis**
    *   **Description**: specific visual representation of the neural network described in Section A.
    *   **Visuals**:
        *   *Input Nodes*: Representing Flow Vectors ($f_1, f_2...$).
        *   *Edges*: Connecting nodes based on Similarity (k-NN).
        *   *Layers*: Show "GCNConv Layer 1" -> "ReLU/Dropout" -> "GCNConv Layer 2" -> "Sigmoid Output".

3.  **Fig. 3: Hybrid Command Detection Flowchart**
    *   **Description**: A flowchart representation of Algorithm 1.
    *   **Visuals**: Start node "Command $C$" -> Decision Diamond "Regex Match?" -> If Yes (Critical) -> "Alert". If No/Low -> Decision Diamond "AI Anomaly?" -> Fusion Logic block -> Final Verdict.
