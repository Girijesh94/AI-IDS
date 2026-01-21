# Winsurf AI Prompts - Complete List
## Exact Commands to Ask Winsurf to Build Your XDR-IDS Platform

---

## � PHASE 0: Prerequisites & Initial Data Setup

Before building the platform, we need data. This phase covers setting up an initial training dataset and a live data sensor. This is critical for training and validating the AI/ML models.

### Day 0: Initial Dataset and Sensor Setup

#### Prompt 0.1: Download and Prepare Training Data
```
@codebase Create a Python script `scripts/download_dataset.py` to bootstrap our ML models.

The script should:
1.  **Download the CIC-IDS2017 dataset** from a reliable source (e.g., University of New Brunswick website).
    - URL: `https://www.unb.ca/cic/datasets/ids-2017.html`
    - Specifically, download the `MachineLearningCSV.zip` file which contains pre-processed CSVs.
2.  **Unzip the file** into a `data/raw/cic-ids2017` directory.
3.  **Combine all CSV files** from the unzipped folder into a single file: `data/processed/cic-ids2017.csv`.
4.  **Clean the data**:
    - Remove spaces from column names.
    - Drop rows with NaN or infinite values.
    - Ensure the 'Label' column is present and clearly distinguishes benign vs. attack traffic.
5.  **Add logging** to show progress (downloading, unzipping, cleaning).
6.  Include this script in a `.gitignore`d `data/` directory.

Also, add `requests` and `pandas` to `requirements.txt` if they are not there.
```

#### Prompt 0.2: Setup Network Sensor with Packetbeat
```
@codebase To capture live network traffic, let's configure Packetbeat to send data to Kafka. Update the `docker-compose.yml` file:

1.  **Add a new service `packetbeat`**:
    - Use the official image: `docker.elastic.co/beats/packetbeat:8.5.0`
    - Run as `root` user to allow raw socket access (`user: root`).
    - Set `network_mode: host` to allow it to monitor the host's network traffic directly.
    - Add `cap_add: ["NET_RAW", "NET_ADMIN"]` to give it the necessary capabilities.
    - Mount a configuration file: `./config/packetbeat.yml:/usr/share/packetbeat/packetbeat.yml`

2.  **Create the `config/packetbeat.yml` configuration file**:
    - Define the network interface to monitor (e.g., `any`).
    - Configure flows to track network connections.
    - **Set the output to our Kafka service**:
        - `output.kafka.hosts: ["kafka:9092"]`
        - `output.kafka.topic: 'network-events'`
        - `output.kafka.codec.json.pretty: true`
    - Disable the default Elasticsearch output.

This service will act as our primary network sensor, feeding live data into the `network-events` Kafka topic.
```

---

## � PHASE 1: Foundation (Weeks 1-4)

### Day 1-2: Project Setup

#### Prompt 1: Create Complete Project Structure
```
@codebase Create a complete folder structure for an XDR-IDS (Extended Detection and Response + Intrusion Detection System) security platform with these directories:

- config/ (for rules, models, playbooks)
- sensors/ (network, endpoint)
- collectors/ (cloud, logs)
- pipeline/ (normalization, enrichment)
- detection/ (rules-engine, correlation, baseline)
- database/ (postgres, neo4j, redis)
- ml/ (anomaly-detection, inference, training)
- api/ (core, routers, schemas)
- dashboard/ (frontend, backend)
- kubernetes/ (manifests, helm)
- tests/

Also create:
- .gitignore (Python/Docker ignores)
- requirements.txt (empty for now)
- docker-compose.yml (with Kafka, PostgreSQL, Neo4j, Redis)
- README.md

Initialize a Git repository.
```

#### Prompt 2: Generate .gitignore and requirements.txt
```
Generate a comprehensive .gitignore file for a Python/Docker project with:
- Virtual environments (venv, env, .venv)
- Python cache (__pycache__, *.py[cod])
- IDE files (.vscode, .idea)
- Environment files (.env)
- Docker artifacts
- ML models directory
- Logs and data folders

Also create a requirements.txt with these Python packages:
- fastapi, uvicorn, pydantic
- kafka-python, confluent-kafka
- psycopg2-binary, sqlalchemy
- neo4j, redis
- pandas, numpy, scikit-learn
- pytest, pytest-asyncio
- pyyaml, python-dotenv
- prometheus-client
- requests
```

#### Prompt 3: Create Docker-Compose for All Services
```
Create a docker-compose.yml file that spins up 7 services:

1. Zookeeper (for Kafka coordination)
2. Kafka (message streaming, port 9092)
3. PostgreSQL + TimescaleDB (time-series DB, port 5432)
4. Neo4j (graph database, ports 7474, 7687)
5. Redis (cache, port 6379)
6. Prometheus (metrics collection, port 9090)
7. Grafana (dashboards, port 3000)

Include:
- Environment variables for each service
- Volume mounting for persistence
- Health checks
- Proper dependency ordering
- Network configuration
```

---

### Day 3: Kafka & Database Setup

#### Prompt 4: Create Kafka Topic Setup Script
```
Create a bash script (setup_kafka.sh) that creates 4 Kafka topics:

1. network-events (4 partitions, key=dst_ip)
2. endpoint-events (8 partitions, key=hostname)
3. cloud-events (2 partitions, key=service)
4. normalized-events (4 partitions, key=event_type)

Include commands to:
- Create each topic with proper replication factor
- List all topics to verify
- Describe topics to show details
- Add helpful comments explaining each topic's purpose
```

#### Prompt 5: PostgreSQL Schema for XDR-IDS
```
Create a PostgreSQL schema (database/postgres/schema.sql) with these tables:

1. **events** (TimescaleDB hypertable)
   - timestamp (TIMESTAMPTZ)
   - event_id (BIGSERIAL)
   - event_type, severity, source_type
   - username, hostname
   - anomaly_score (FLOAT)
   - data (JSONB)
   - Indexes on: event_type, username, hostname

2. **detection_rules**
   - rule_id, name, severity
   - rule_yaml (TEXT)
   - enabled (BOOLEAN)
   - created_at, updated_at
   - alert_count

3. **incidents**
   - incident_id, created_at
   - severity, status
   - affected_entities (TEXT[])
   - root_cause, analyst_notes

4. **alerts**
   - alert_id (BIGSERIAL)
   - timestamp, incident_id
   - severity, alert_type
   - rule_id, confidence
   - evidence (JSONB)
   - status

5. **event_embeddings** (for ML similarity)
   - event_id, embedding (vector)

Include:
- Constraints and primary keys
- Indexes for performance
- Hypertable conversion for events
- Retention policies (90 days)
- Comments explaining each table
```

---

### Day 4-5: Normalization Service

#### Prompt 6: Create FastAPI Normalization Service
```
Create a FastAPI application (pipeline/normalization/main.py) that:

1. **Connects to Kafka**:
   - Consumes from: network-events, endpoint-events, cloud-events
   - Produces to: normalized-events

2. **Implements OCSFNormalizer class** with methods for:
   - normalize_network_event() → OCSF typeuid 4001
   - normalize_process_event() → OCSF typeuid 1001
   - normalize_auth_event() → OCSF typeuid 3002

3. **Standardizes fields**:
   - Converts all timestamps to ISO format
   - Adds severity levels
   - Extracts src/dst endpoints
   - Normalizes user/hostname/process names

4. **Endpoints**:
   - GET /health → returns service status
   - POST /normalize → manual normalization endpoint
   - GET /metrics → Prometheus metrics

5. **Error handling**:
   - Log all errors with context
   - Skip malformed events
   - Track normalization statistics

6. **Runs on localhost:8000**
```

#### Prompt 7: Create Dockerfile for Normalization Service
```
Create Dockerfile (pipeline/normalization/Dockerfile) that:
- Uses Python 3.11 slim base image
- Sets working directory to /app
- Installs requirements from requirements.txt
- Exposes port 8000
- Sets CMD to run the FastAPI service
- Includes health check

Keep it minimal and efficient.
```

---

### Day 6-7: Rule Engine

#### Prompt 8: Create Rule DSL Detection Engine
```
Create a RuleEngine class (detection/rules-engine/rule_engine.py) that:

1. **Loads YAML rules** from config/rules/detection_rules.yaml

2. **RuleEngine class** with methods:
   - __init__(rules_path) → loads rules
   - load_rules() → parses YAML
   - process_event(event) → returns list of matching alerts
   - matches_rule(event, rule) → boolean match check
   - create_alert(rule, events) → generates alert JSON

3. **Rule matching logic**:
   - Check event fields against rule conditions
   - Support exact match, list match, threshold match
   - Handle windowed rules (aggregate events over time)

4. **Alert structure**:
   - alert_id, timestamp, type
   - severity, rule_id, confidence
   - affected_events count
   - evidence array
   - status

5. **Windowed rules**:
   - Maintain state dict for aggregating events
   - Check thresholds (count, time_window)
   - Reset state after triggering alert

Example rule structure to support:
```yaml
rule_id: 1001
name: "Suspicious Process from Service Host"
severity: critical
match:
  typename: "Process Activity"
  process_name: svchost.exe
  resource_process_name: [cmd.exe, powershell.exe]
is_windowed: false
```
```

#### Prompt 9: Create Sample Detection Rules
```
Create detection_rules.yaml (config/rules/detection_rules.yaml) with 10 production-ready detection rules:

1. Suspicious Process from Service Host
   - svchost.exe spawning cmd.exe or powershell.exe
   - Severity: CRITICAL

2. Brute Force RDP Attempt
   - 20+ failed auth in 5 minutes
   - Severity: HIGH

3. Unusual Data Transfer
   - >500MB in single connection
   - Severity: HIGH

4. DNS Beaconing
   - 100+ DNS queries in 1 minute
   - Severity: MEDIUM

5. C2 Communication
   - Known C2 IP connection
   - Severity: CRITICAL

6. Suspicious File Creation
   - .exe or .ps1 in temp folder
   - Severity: HIGH

7. Lateral Movement
   - Multiple failed RDP attempts
   - Severity: HIGH

8. Registry Modification (Windows)
   - Modification of Run keys
   - Severity: MEDIUM

9. Web Shell Upload
   - .aspx, .php files in web directories
   - Severity: CRITICAL

10. Ransomware Behavior
    - Multiple file extensions in short time
    - Severity: CRITICAL

Format each with:
- rule_id, name, severity
- match conditions
- is_windowed and thresholds if applicable
- actions (alert, block, etc.)
```

---

### Day 8-9: Baseline Service

#### Prompt 10: Create Behavioral Baseline Service
```
Create BaselineService class (detection/baseline/baseline_service.py) that:

1. **Connects to Redis** for storage

2. **Calculates baselines**:
   - calculate_user_baseline(username, events) → stores baseline
   - calculate_host_baseline(hostname, events) → stores baseline

3. **User baseline includes**:
   - typical_hours (login hours)
   - typical_locations (geographic IPs)
   - avg_daily_logins
   - typical login protocols

4. **Host baseline includes**:
   - typical_ports (destination ports)
   - avg_bytes_per_connection
   - avg_connection_duration
   - typical_process_parents
   - total_daily_connections

5. **Storage**:
   - Use Redis with keys like "baseline:user:john.doe"
   - 30-day retention policy
   - Use JSON serialization

6. **Anomaly scoring**:
   - calculate_anomaly_score(event, baseline) → 0.0-1.0
   - Compare event against baseline
   - Return higher score for more deviation
   - Consider: ports, hours, data volume, duration

7. **Methods**:
   - All with proper error handling
   - Logging for debugging
   - Type hints
```

---

### Day 10: Dashboard Frontend

#### Prompt 11: Create React Dashboard HTML
```
Create dashboard/frontend/public/index.html with:

1. **Header section**:
   - Title: "🛡️ XDR-IDS Security Operations Center"
   - Status bar showing:
     - Live Incidents count
     - Critical incidents count
     - High severity incidents count

2. **Main layout** (two columns):
   - Left: Active Incidents list
   - Right: Alert Details panel

3. **Incident cards** showing:
   - Severity badge (color-coded: red=critical, orange=high)
   - Incident type/alert name
   - Affected entity (host/user)
   - Timestamp
   - Clickable to show details

4. **Alert details panel** showing:
   - Full incident information
   - Confidence score
   - Evidence points
   - Status
   - Analyst notes field

5. **Styling**:
   - Dark theme (GitHub dark style)
   - Responsive layout
   - Color-coded severity levels
   - Professional security dashboard feel

6. **JavaScript integration**:
   - Auto-refresh every 5 seconds
   - Click incidents to show details
   - Real-time updates
```

#### Prompt 12: Create Dashboard JavaScript & CSS
```
Create two files:

1. **dashboard/frontend/public/app.js**:
   - const API_BASE = 'http://localhost:8000'
   - fetchIncidents() → GET /api/incidents
   - renderIncidents(incidents) → update DOM
   - showDetails(incidentId) → GET /api/incidents/{id}
   - renderDetails(incident) → update details panel
   - setInterval(fetchIncidents, 5000) → auto-refresh

2. **dashboard/frontend/public/styles.css**:
   - Dark theme background
   - Color-coded severity badges
   - Card styling for incidents
   - Responsive grid layout
   - Hover effects
   - Professional SOC dashboard aesthetic
   - Include CSS for all elements from HTML
```

---

## 🔍 PHASE 2: Detection (Weeks 5-8)

### Prompt 13: Create Multi-Layer Alert Pipeline
```
Create api/core/detection_pipeline.py that:

1. **Integrates all detection layers**:
   - Layer 1: Rule matching (RuleEngine)
   - Layer 2: Baseline anomaly (BaselineService)
   - Layer 3: ML anomaly (placeholder for now)
   - Layer 4: LLM analysis (placeholder for now)
   - Layer 5: Predictive risk (placeholder for now)

2. **DetectionPipeline class**:
   - __init__() → initialize all engines
   - process_event(event) → runs through all layers
   - calculate_final_score(scores) → weighted average
   - generate_alert(event, scores) → create final alert

3. **Output alert structure**:
   - alert_id, timestamp, severity
   - type, affected_entity
   - detection_scores (layer1, layer2, etc.)
   - final_threat_score
   - evidence array
   - confidence (0.0-1.0)

4. **Logging**:
   - Log processing time per layer
   - Alert creation with context
```

### Prompt 14: Create FastAPI Backend for Incidents
```
Create api/routers/incidents.py with FastAPI endpoints:

1. **GET /api/incidents**
   - Returns list of all active incidents
   - Query params: skip, limit, severity, status
   - Response: list of incident objects

2. **GET /api/incidents/{incident_id}**
   - Returns full incident details
   - Include: timeline, evidence, affected entities
   - Include: recommended actions, analyst notes

3. **GET /api/alerts**
   - Returns recent alerts
   - Params: skip, limit, type, severity
   - Response: alert list

4. **POST /api/incidents/{incident_id}/notes**
   - Add analyst notes to incident
   - Body: {notes: "text"}

5. **PATCH /api/incidents/{incident_id}/status**
   - Update incident status
   - Body: {status: "OPEN|INVESTIGATING|CONTAINED|RESOLVED"}

6. **POST /api/incidents/{incident_id}/approve_action**
   - Approve Tier-3 response action
   - Body: {action_id: "...", approved: true}

All endpoints should:
- Connect to PostgreSQL
- Return proper HTTP status codes
- Include error handling
- Have proper request/response schemas
- Include logging
```

---

## 🤖 PHASE 3: ML & Entity Graph (Weeks 9-12)

### Prompt 15: Create Isolation Forest ML Model
```
Create ml/anomaly-detection/isolation_forest.py with:

1. **NetworkAnomalyDetector class**:
   - __init__() → create Isolation Forest model
   - train(X_train) → train on clean network flow data
   - predict(X_test) → returns anomaly scores 0.0-1.0
   - save_model(path) → save trained model
   - load_model(path) → load saved model

2. **Features to use**:
   - bytes_ratio (bytes/duration)
   - packet_rate (packets/duration)
   - payload_entropy (how random is the data)
   - port_diversity (how many unique ports)
   - tls_suspicion (is TLS cert suspicious)

3. **Training**:
   - Contamination=0.05 (5% outliers)
   - n_estimators=100

4. **Usage example in code comments**

5. **Inference** returns 0.0-1.0 anomaly score
```

### Prompt 16: Create Neo4j Entity Graph
```
Create database/neo4j/entity_graph.py with:

1. **EntityGraph class**:
   - __init__(uri, user, password) → connect to Neo4j
   - create_user_node(username) → CREATE (u:User {id})
   - create_host_node(hostname) → CREATE (h:Host {id})
   - create_ip_node(ip) → CREATE (i:IP {id})
   - create_relationship(from_entity, to_entity, rel_type) → creates relationship
   
2. **Relationships to support**:
   - User -LOGSINTO-> Host
   - Host -CONNECTSTO-> IP
   - Process -SPAWNS-> Process
   - IP -IS_KNOWN_C2-> ThreatIntel

3. **Query methods**:
   - find_attack_chain(start_entity) → returns path of related entities
   - get_entity_risk(entity_id) → returns risk score
   - find_similar_patterns(pattern) → finds matching attack patterns

4. **Risk scoring**:
   - Update entity risk based on incidents
   - Propagate risk through relationships

5. **Error handling** for Neo4j connection issues
```

---

## 🧠 PHASE 4: AI & Response (Weeks 13-16)

### Prompt 17: Create LLM Integration Service
```
Create api/integrations/llm_service.py with:

1. **IncidentAnalyzer class**:
   - __init__(api_key, model) → connect to Claude/Mistral
   - analyze_incident(incident_data) → calls LLM
   - Returns: threat_assessment, confidence, risk_level, recommendations

2. **Prompt engineering**:
   - System prompt: "You are a security analyst..."
   - Include: event type, severity, evidence, baseline score
   - Request: What happened? Confidence? What to do?
   - Return: JSON with assessment

3. **PlaybookGenerator class**:
   - generate_playbook(incident) → calls LLM
   - Returns: YAML playbook with steps
   - Each step: tier (1/2/3), action, auto/manual, duration

4. **ThreatHunter class**:
   - hunt(incident, threat_intel) → searches for similar patterns
   - Returns: related incidents, risk updates

5. **Error handling**:
   - Fallback if LLM unavailable
   - Token limit handling
   - Cost tracking

6. **Logging** for all LLM calls
```

### Prompt 18: Create Response Playbook Executor
```
Create api/routers/response.py with:

1. **PlaybookExecutor class**:
   - execute_playbook(playbook, incident_id) → runs approval-gated execution
   - execute_tier1_actions(actions) → run without approval
   - execute_tier2_actions(actions) → await 30s review then run
   - execute_tier3_actions(actions) → wait for analyst approval

2. **Actions to support**:
   - **Tier 1 (auto)**:
     - Send alert to Slack
     - Create ticket
     - Send email
   - **Tier 2 (30s review)**:
     - Block IP at firewall
     - Isolate host to VLAN
     - Kill process
     - Disable account (temp)
   - **Tier 3 (manual)**:
     - Revoke credentials
     - Delete user account
     - Full system wipe

3. **Endpoints**:
   - POST /api/playbooks/{id}/execute
   - POST /api/actions/{id}/approve
   - POST /api/actions/{id}/deny
   - GET /api/playbooks/history

4. **Audit logging** for all actions
```

---

## ☸️ PHASE 5: Kubernetes Deployment

### Prompt 19: Create Kubernetes Manifests
```
Create kubernetes/manifests/xdr-deployment.yaml with:

1. **Namespace**: xdr-platform

2. **StatefulSets** for databases:
   - PostgreSQL (1 replica)
   - Neo4j (1 replica)
   - Redis (1 replica)
   - Kafka (3 replicas)

3. **Deployments** for services:
   - normalization (3 replicas)
   - detection-engine (3 replicas)
   - api-backend (3 replicas)
   - dashboard-frontend (2 replicas)

4. **Each deployment should have**:
   - Resource requests (CPU, memory)
   - Resource limits
   - Health checks (liveness, readiness probes)
   - Environment variables from ConfigMap
   - Image pull policy
   - Container ports
   - Volume mounts for persistent data

5. **Services**:
   - ClusterIP for internal services
   - LoadBalancer for API and dashboard

6. **ConfigMaps**:
   - Database connection strings
   - Kafka brokers
   - Feature flags

7. **Secrets**:
   - Database passwords
   - API keys
   - LLM tokens
```

### Prompt 20: Create Helm Chart
```
Create helm/xdr-platform-chart/ with:

1. **Chart.yaml**:
   - name: xdr-platform
   - version: 1.0.0
   - description: AI-Native XDR-IDS Platform

2. **values.yaml** with:
   - Image versions for all services
   - Resource requests/limits
   - Replica counts
   - Environment configuration
   - Feature toggles

3. **Templates**:
   - deployment.yaml
   - service.yaml
   - configmap.yaml
   - secret.yaml
   - ingress.yaml (for external access)

4. **Installation instructions in README**:
   - helm install xdr-platform ./xdr-platform-chart
   - Configuration options
   - Post-install setup steps
```

---

## 📈 PHASE 6: MLOps & Model Management

To build a reliable AI-powered system, we need to manage the lifecycle of our machine learning models. This phase introduces MLOps (Machine Learning Operations) practices using MLflow for experiment tracking, model versioning, and reproducibility.

### Prompt 20.1: Integrate MLflow for Experiment Tracking
```
@codebase Update the `docker-compose.yml` file to include MLflow for MLOps:

1.  **Add a new `mlflow` service**:
    - Image: `ghcr.io/mlflow/mlflow:v2.9.2`
    - Command: `mlflow server --host 0.0.0.0 --port 5000 --backend-store-uri postgresql://user:password@postgres/mlflow_db --default-artifact-root /mlflow/artifacts`
    - Expose port `5000`.
    - Create a volume for artifacts: `mlflow_artifacts:/mlflow/artifacts`.
    - Depends on `postgres`.

2.  **Update the `postgres` service**:
    - You will need to create a new database for MLflow. You can do this by executing a command in the running postgres container: `createdb -U user mlflow_db`

3.  **Add `mlflow` to `requirements.txt`**.

This sets up the MLflow Tracking Server, which will store experiment data in PostgreSQL and model artifacts in a Docker volume.
```

### Prompt 20.2: Update ML Model Training with MLflow
```
@codebase Refactor the `ml/anomaly-detection/isolation_forest.py` script to integrate with MLflow:

1.  **Import `mlflow`** and set the tracking URI: `mlflow.set_tracking_uri("http://localhost:5000")`.

2.  **Wrap the training logic in an MLflow run**:
    - Use a `with mlflow.start_run():` block.
    - **Log parameters**: Log model parameters like `n_estimators` and `contamination` using `mlflow.log_param()`.
    - **Log metrics**: After training, log evaluation metrics like precision, recall, and F1-score using `mlflow.log_metric()`.
    - **Log the model**: Save the trained model to the MLflow registry using `mlflow.sklearn.log_model()`.
        - Give the model a registered name like `isolation-forest-cicids2017`.
        - This will allow for versioning and easy retrieval.

3.  **Update the `load_model` method**:
    - Modify it to load a specific model version from the MLflow Model Registry (e.g., `models:/isolation-forest-cicids2017/production`).

This ensures that every training run is tracked, versioned, and reproducible.
```

---

## �️ PHASE 7: Security & Production Hardening

A production system must be secure. This phase addresses critical security gaps, starting with secrets management to avoid exposing database passwords, API keys, and other sensitive credentials in code or environment variables.

### Prompt 20.3: Implement Secrets Management with Doppler
```
@codebase To manage secrets securely, we'll use Doppler. First, sign up at Doppler.com and create a project.

1.  **Install the Doppler CLI** on your local machine.
2.  **Authenticate the CLI** by running `doppler login`.
3.  **Setup the project** by running `doppler setup` in the repository root. This will link your local project to a project in the Doppler dashboard.
4.  **Add secrets** like `POSTGRES_USER`, `POSTGRES_PASSWORD`, and `NEO4J_AUTH` to the Doppler project via the UI.
5.  **Update `.gitignore`** to include the `.doppler` directory and any `.env` files.

Now, instead of using a plaintext `.env` file, you can run your application with secrets injected directly by Doppler.
```

### Prompt 20.4: Update Docker Compose for Secure Secret Injection
```
@codebase Modify the `docker-compose.yml` and application code to consume secrets from Doppler.

1.  **Update the `docker-compose.yml` file**:
    - For each service that needs secrets (e.g., `postgres`, `api`, `normalization`), remove the plaintext `environment` variables.
    - Instead, use the `env_file` property to point to a file that Doppler will create:
      ```yaml
      services:
        api:
          env_file:
            - /tmp/doppler.env
      ```

2.  **Run Docker Compose with Doppler**:
    - To start your services, you will now use the Doppler CLI to inject the secrets at runtime:
      `doppler run -- docker-compose up`
    - The `doppler run` command creates a temporary `.env` file, makes it available to the specified command, and then cleans it up.

3.  **Update Python Code**:
    - Ensure all services that consume secrets (e.g., database connections, API keys) use `python-dotenv` to load variables from the environment, which Doppler now populates securely.

This approach ensures no secrets are ever stored on disk in plaintext, significantly improving the security posture of the application.
```

---

## � Testing Prompts

### Prompt 21: Create Unit Tests
```
Create tests/test_normalization.py with pytest tests for:

1. test_normalize_network_event() → verify OCSF output
2. test_normalize_process_event() → verify fields mapped
3. test_normalize_auth_event() → verify all auth fields
4. test_invalid_event_handling() → test error cases
5. test_timestamp_format() → ensure ISO 8601

Create tests/test_rule_engine.py:
1. test_load_rules() → rules load from YAML
2. test_rule_matching() → event matches rule
3. test_alert_generation() → alert created correctly
4. test_windowed_rules() → aggregation works
5. test_multiple_rule_matching() → multiple alerts

Create tests/test_detection_pipeline.py:
1. test_multi_layer_scoring() → all layers contribute
2. test_final_threat_score() → weighted average correct
3. test_end_to_end_alert() → raw event to alert

Run all with: pytest tests/ -v --cov=. --cov-report=html
```

### Prompt 21.1: Create Integration Tests
```
@codebase Create `tests/test_integration.py` to test the interactions between services:

1.  **`test_database_connection`**:
    - A test that connects to the PostgreSQL database using credentials from the environment, creates a test table, inserts data, and then drops the table.
    - This verifies that the application can successfully communicate with the database.

2.  **`test_kafka_connectivity`**:
    - A test that uses the `kafka-python` library to create a producer and a consumer.
    - The producer sends a test message to the `normalized-events` topic.
    - The consumer reads from the topic and asserts that the message was received correctly.
    - This validates that the Kafka service is reachable and topics are configured.

3.  **`test_api_health_check`**:
    - A test that makes an HTTP request to the `/health` endpoint of the API service and asserts a `200 OK` status code.

These tests should be run after the services are started via `docker-compose up`.
```

### Prompt 21.2: Create End-to-End (E2E) Test
```
@codebase Create `tests/test_e2e.py` to test the full data pipeline:

**`test_full_pipeline_alert_generation`**:

1.  **Setup**: Connect a Kafka producer and a PostgreSQL client.

2.  **Act**: Craft a sample JSON event that is known to trigger a specific detection rule (e.g., the "Suspicious Process from Service Host" rule).
    - Send this event to the `endpoint-events` Kafka topic.

3.  **Wait & Poll**: Wait for a few seconds to allow the event to be processed by the normalization service, detection engine, and API.

4.  **Assert**: Query the PostgreSQL `alerts` table.
    - Assert that a new alert has been created.
    - Assert that the `rule_id` in the alert matches the rule you intended to trigger.
    - Assert that the alert's `severity` and `evidence` are correct.

This test provides confidence that the entire system is working together as expected, from data ingestion to final alert storage.
```

---

## � PHASE 8: CI/CD & Automation

To ensure code quality and reliability, we need to automate our testing and build processes. This phase introduces a Continuous Integration (CI) pipeline using GitHub Actions.

### Prompt 21.3: Create a CI Pipeline with GitHub Actions
```
@codebase Create a GitHub Actions workflow file at `.github/workflows/ci.yml`.

The workflow should:
1.  **Trigger** on every `push` to the `main` branch and on any `pull_request`.

2.  **Define a `lint-and-test` job** that runs on `ubuntu-latest`.

3.  **Steps for the job**:
    - **Checkout Code**: Use `actions/checkout@v3`.
    - **Setup Python**: Use `actions/setup-python@v4` with Python 3.11.
    - **Install Dependencies**: `pip install -r requirements.txt`.
    - **Run Linter**: Run a linter like `flake8` or `black --check` across the codebase.
    - **Run Tests**: Start the services in the background (`docker-compose up -d`) and then run the full test suite (`pytest tests/`).

4.  **Define a `build-images` job** that depends on the `lint-and-test` job.
    - **Steps for the job**:
        - **Checkout Code**.
        - **Login to Docker Hub** (using secrets for credentials).
        - **Build and Push Docker Images**: Build the Docker images for the `api`, `normalization`, and `detection` services and push them to a container registry.

This CI pipeline will automatically validate every change, preventing bugs and ensuring that your Docker images are always ready for deployment.
```

---

## � Integration & Debugging Prompts

### Prompt 22: Create Docker Compose Override for Development
```
Create docker-compose.override.yml for local development that:

1. Mounts source code directories as volumes for hot-reload:
   - pipeline/normalization -> /app
   - detection -> /app
   - api -> /app

2. Sets environment variables:
   - LOG_LEVEL=DEBUG
   - ENVIRONMENT=development

3. Exposes additional ports for debugging

4. Mounts Python cache volumes

5. Includes comments explaining each override
```

### Prompt 23: Create Logging Configuration
```
Create config/logging.yaml with structured logging:

1. **Loggers**:
   - root (DEBUG level)
   - kafka (INFO level)
   - database (INFO level)
   - detection (DEBUG level)
   - api (INFO level)

2. **Handlers**:
   - Console handler (JSON format)
   - File handler (logs/ directory)
   - Rotating file handler (max 10MB)

3. **Formatters**:
   - JSON format with timestamp, level, logger, message
   - Include context (event_id, rule_id, etc.)

4. **Usage example** in Python code
```

---

## 📈 Monitoring & Observability

### Prompt 24: Create Prometheus Metrics Configuration
```
Create config/prometheus.yml with:

1. **Scrape configs** for:
   - localhost:8000 (API metrics)
   - localhost:9090 (Prometheus itself)
   - kafka:9092 (Kafka metrics - if exposed)

2. **Global settings**:
   - scrape_interval: 15s
   - evaluation_interval: 15s

3. **Alert rules** in prometheus/rules.yml:
   - Service down (no metrics in 1 min)
   - High error rate (>5%)
   - Processing latency >500ms
   - Kafka lag >10k messages
```

### Prompt 25: Create Grafana Dashboard
```
Create grafana/dashboards/xdr-overview.json with panels for:

1. **System Health**:
   - All services up/down status
   - CPU, Memory usage
   - Disk space

2. **Processing Metrics**:
   - Events/sec throughput
   - Processing latency (p50, p95, p99)
   - Alert generation rate

3. **Detection**:
   - Rules matched/sec
   - Baseline anomalies/sec
   - Incidents created/day
   - False positive rate

4. **Database**:
   - Queries/sec
   - Query latency
   - Disk usage growth

5. **API**:
   - Requests/sec
   - Response time by endpoint
   - Error rates
   - Top endpoints

Include descriptions for each metric.
```

---

## 🎓 Documentation Prompts

### Prompt 26: Generate API Documentation
```
Generate OpenAPI/Swagger documentation for all API endpoints:

GET /api/incidents
GET /api/incidents/{id}
GET /api/alerts
POST /api/incidents/{id}/notes
PATCH /api/incidents/{id}/status
POST /api/incidents/{id}/approve_action

Include for each:
- Description
- Parameters
- Request body (if any)
- Response schema
- Status codes
- Example request/response
```

### Prompt 27: Create Architecture Documentation
```
Create docs/ARCHITECTURE.md explaining:

1. **System Overview**:
   - What the system does
   - Key differentiators
   - Business value

2. **Data Flow**:
   - Raw events to alerts (step-by-step)
   - Timeline of one alert
   - Confidence scoring

3. **Component Details**:
   - Network Sensor (what it captures)
   - Normalization (OCSF schema)
   - Detection layers (rules, ML, LLM)
   - Response execution
   - Database schema

4. **Scalability**:
   - Throughput targets
   - Latency targets
   - Storage requirements

5. **Security**:
   - Data isolation
   - Authentication/authorization
   - API security
```

---

## 💻 Maintenance & Operations Prompts

### Prompt 28: Create Troubleshooting Guide
```
Create docs/TROUBLESHOOTING.md with common issues:

1. "Kafka connection refused"
   - Symptoms
   - Solutions
   - Debug commands

2. "PostgreSQL permission denied"
   - Check password
   - Check user permissions
   - Connection commands

3. "Neo4j failing to load graph"
   - Check disk space
   - Memory settings
   - Query timeout settings

4. "High latency in detection"
   - Check system resources
   - Analyze slow rules
   - Review ML inference time

5. "Dashboard not updating"
   - Check API connectivity
   - Check Kafka topics
   - Browser console errors

6. "Failed LLM calls"
   - Check API key
   - Check rate limiting
   - Check token count

Include debug commands for each.
```

### Prompt 29: Create Deployment Runbook
```
Create docs/DEPLOYMENT.md with:

1. **Prerequisites**:
   - Docker/Docker Desktop
   - kubectl
   - Helm
   - AWS/GCP/Azure account (if cloud)

2. **Local Development Setup**:
   - Clone repo
   - docker-compose up
   - Run setup_kafka.sh
   - python pipeline/normalization/main.py
   - python api/core/main.py

3. **Staging Deployment**:
   - Build Docker images
   - Push to registry
   - helm install on staging cluster

4. **Production Deployment**:
   - Security checklist
   - Data migration
   - Rollback procedures
   - Monitoring setup

5. **Post-Deployment**:
   - Verification steps
   - Performance testing
   - Backup configuration
```

---

## 🚀 QUICK REFERENCE: Top 12 Prompts for a MVP

To get a Minimum Viable Product (MVP) running, execute these 12 prompts in order:

1.  **Download and Prepare Data** (Prompt 0.1)
2.  **Setup Network Sensor** (Prompt 0.2)
3.  **Create Project Structure** (Prompt 1)
4.  **Generate .gitignore & requirements.txt** (Prompt 2)
5.  **Create Docker-Compose** (Prompt 3)
6.  **Create Kafka Topics** (Prompt 4)
7.  **Create PostgreSQL Schema** (Prompt 5)
8.  **Create Normalization Service** (Prompt 6)
9.  **Create Rule Engine** (Prompt 8)
10. **Create Dashboard** (Prompts 11 & 12)
11. **Create Detection Pipeline** (Prompt 13)
12. **Create FastAPI Backend** (Prompt 14)

---

## 💡 How to Use These Prompts in Winsurf

### Method 1: Direct Chat
```
Open Winsurf chat and paste any prompt above.
Example:
"@codebase Create a complete folder structure for an XDR-IDS..."
```

### Method 2: Command Palette
```
Ctrl+Shift+P → "Cursor: Ask"
Paste your prompt
Press Enter
```

### Method 3: Code Generation
```
Right-click in file → "Ask Cursor"
Or: Ctrl+K (on selected code)
Ask to explain or improve the code
```

### Method 4: File Creation
```
Ctrl+Shift+P → "Create New File"
Name it
Then ask Cursor to generate contents:
"Generate FastAPI application code for: [use case]"
```

---

## 🔑 Tips for Best Results with Winsurf

1. **Be specific**: "Create a FastAPI endpoint..." beats "Make an API"

2. **Provide context**: "@codebase Create [thing] that integrates with the existing normalization service"

3. **Show examples**: "Create a rule like this: [YAML example]"

4. **Ask incrementally**: 
   - First: Basic structure
   - Then: Add error handling
   - Then: Add logging
   - Finally: Add tests

5. **Use @codebase**: Helps Winsurf understand your existing code

6. **Iterate**: Ask to improve, refactor, add features

7. **Request explanations**: "Explain what this function does" or "Why is this approach used?"

---

## 📋 Prompt Template for Your Own Questions

When you have a specific need, use this template:

```
@codebase Create a [component type] that:

GOAL:
[What should it do?]

FUNCTIONALITY:
1. [Feature 1]
2. [Feature 2]
3. [Feature 3]

INPUTS:
[What does it receive?]

OUTPUTS:
[What does it return?]

TECHNOLOGIES:
[What tech to use?]

INTEGRATION:
[How does it connect to other parts?]

CONSTRAINTS:
[Any limits or requirements?]
```

---

## 🎯 Progressive Development Path

### Week 1: Foundation & Data Ingestion
- Ask Winsurf prompts: 0.1, 0.2, 1, 2, 3, 4, 5

### Week 2: Core Logic
- Ask Winsurf prompts: 6, 7, 8, 9, 10

### Week 3: API & Dashboard
- Ask Winsurf prompts: 11, 12, 13, 14

### Week 4: ML & Entity Graph
- Ask Winsurf prompts: 15, 16

### Weeks 5-6: AI & Response Automation
- Ask Winsurf prompts: 17, 18

### Weeks 7-8: Deployment & MLOps
- Ask Winsurf prompts: 19, 20, 20.1, 20.2

### Weeks 9-10: Security & Testing
- Ask Winsurf prompts: 20.3, 20.4, 21, 21.1, 21.2

### Weeks 11-12: Automation & Documentation
- Ask Winsurf prompts: 21.3, 22, 23, 24, 25, 26, 27, 28, 29

---

## ✅ Verification After Each Component

After asking Winsurf to create something, verify it:

```bash
# Check file created
ls -la [file_path]

# Test Python syntax
python -m py_compile [file.py]

# Test Docker config
docker-compose config

# Run tests
pytest [test_file.py] -v

# Check for errors
git diff [file]
```

---

**You now have 29 expertly-crafted prompts to guide Winsurf through building your entire XDR-IDS platform! Start with Prompt 1 and work through them systematically.** 🚀
