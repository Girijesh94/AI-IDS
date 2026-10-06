# IDS/SOC rework plan

Prepared 2026-09-29 from the current working tree. Status: proposed work, not implemented.

## 1. Objective and boundaries

Build a reproducible Windows-first IDS/SOC prototype with trustworthy telemetry, real model inference, defensible evaluation, and useful incident handling. Initial deployment is one workstation or a small authorized lab. Retain Flask, Socket.IO, and SQLite until measured load justifies replacements. Keep monitoring passive; automatic blocking is outside the first release.

No IDS can guarantee perfect detection. The release contract below defines what must work and what must be measured. Models may identify suspicious behavior; six flow statistics cannot establish that ransomware, fileless execution, or SQL injection occurred. Those claims require appropriate endpoint or application evidence.

A workstation capture sees traffic available at its interface, not every device on a switched network. Network-wide deployment requires a sensor at an appropriate mirror/TAP or gateway observation point. Document visibility in the UI and evaluation report.

## 2. Findings in the current repository

The CSV audit used PowerShell Import-Csv; it did not execute training or unpickle models.

| File | Rows | Labels | Rows failing packet-total consistency |
|---|---:|---|---:|
| training_data/benign_flows.csv | 1,000 | benign | 999 |
| training_data/attack_flows.csv | 600 | fileless_malware, mitm_dns, payload_injection, ransomware: 150 each | 600 |
| training_data/normal_flows.csv | 5,000 | normal | 4,999 |

Under the project's intended feature definitions, packet count should equal forward plus reverse packet counts. In all 6,600 rows, mean packet size also differs from byte count divided by packet count by more than 0.02 bytes. The supplied generator independently samples quantities that should be related. The precise generator/provenance for the 17-column benign/attack files is not established; their contents are unsuitable as validated packet-derived training data.

The default flow ensemble trainer uses benign_flows.csv and attack_flows.csv: 1,600 rows and six features (duration, packet count, byte count, directional packet counts, mean size). It discards attack-family distinctions and ignores endpoint-like columns such as registry modifications. The older ml_training.py uses normal_flows.csv and eight features. A separate trainer reads labeled database rows. The saved model artifacts have no complete run manifest linking them to exact input data and code, so their actual training source cannot be verified from filenames alone.

The command trainer contains 107 handwritten examples and uses nine string statistics. Its declared text vectorizers are not used by extract_all_features. It is not the transformer described in project documentation. The saved backend/model_metrics.json contains 85 training samples, 22 test samples, and recall 1/9 (11.1%). This is a small command-model evaluation, not the network Random Forest's measured recall.

Critical implementation findings:

- detector_server.py:1631-1680 changes inference based on whether ground_truth is present and forces the final decision from that label. Incoming score/severity/is_anomaly can also override inference. Random jitter modifies scores later in the listener.
- flow_model_ensemble.py defines a random heuristic MockGNNScorer and substitutes it when the native import fails, reporting readiness. This must not be presented as learned GNN inference.
- flow_model_ensemble.py and retrain_flow_models_from_db.py fit preprocessing before splitting; Isolation Forest sees all benign samples. The database trainer selects thresholds on its test subset. Existing evaluation is not a clean held-out estimate.
- gnn_flow_model.py builds the graph and scaler before its random split; held-out nodes participate in the full graph during training. This does not validate future-only streaming behavior.
- flow_extractor.py uses directional keys, so return packets create another flow and dst2src_pkts stays zero in the normal packet callback. It repeatedly emits unchanged cumulative flows, has no maximum lifetime for continuously active flows, and retains every packet size. IPv6 is in the capture filter but not supported by make_key.
- The listener disables port-scan detection; other logic suppresses small unlabeled flows. The backend and ensemble also apply different voting policies.
- system_monitor.py drops events from browser and svchost parents and deduplicates whole command strings; both can hide meaningful activity.
- Relative model/database paths, duplicate database files, unpinned requirements, and platform-specific imports complicate startup. The earlier Python launch attempt failed with access denied; that establishes an execution limitation, not a diagnosed broken Python installation.

The existing simulation scripts submit synthetic feature JSON. They do not establish capture correctness or demonstrate real attack recognition. Retain them as explicitly marked ingestion fixtures only.

## 3. Data strategy

### Recommended sources and roles

1. **CICIDS2017 PCAPs and published attack metadata:** initial reproducible network benchmark. The publisher supplies packet captures, labeled CSVs, and attack schedules. Process a manageable subset first, then expand across sessions and families. The complete PCAP collection is tens of GB; estimate storage/download needs before acquisition. [Publisher](https://www.unb.ca/cic/datasets/ids-2017.html).
2. **Representative local benign traffic:** essential for calibrating false alarms. Capture 7-14 days initially, including browsing, video calls, downloads, updates, developer tools, VPN usage, and idle periods. Preserve a later time period as an untouched test set. A time window is not automatically benign: use known clean lab systems, document activity, review suspicious periods, and retain uncertain labels as unknown.
3. **Labeled authorized lab scenarios:** collect actual packet/process telemetry with a separate scenario log containing start/end times, hosts, actions, and expected observations. Include realistic benign lookalikes. Use offline PCAP replay and benign emulation for routine demonstrations; stronger scenarios belong in isolated, authorized lab environments.
4. **UNSW-NB15:** secondary external evaluation after a compatible extractor and label mapping are validated. Its publisher provides PCAPs, feature data, and ground-truth records from a controlled cyber range. Keep this source separate for a transfer evaluation; do not silently combine unlike CSV schemas. [Publisher](https://research.unsw.edu.au/projects/unsw-nb15-dataset).
5. **Command/process data:** collect reviewed endpoint events separately from network flows. Include legitimate administration, installers, scheduled tasks, scripts, and suspicious variants with parent/user context. Handwritten examples are fixtures; they are insufficient evidence of generalization.

Public benchmarks are controlled, historical datasets. Their scores are benchmark results, not proof of present-day deployment effectiveness. Dataset acquisition must preserve source URLs, versions, checksums, citation/license requirements, label definitions, and known ambiguities.

### One feature contract

Use one repaired extraction library for both PCAP processing and live capture. Do not train on vendor CSV features merely renamed to resemble our features. If a CSV mapping is used for exploration, document semantics and keep its model out of live deployment until parity is demonstrated.

Define schema version, time units, byte accounting layer, flow orientation, TCP/UDP/ICMP treatment, IPv4/IPv6 behavior, idle/active timeouts, truncation, and partial-window rules. Start with a bounded 5-second observation window, 10-second idle closure, and 60-second active segmentation; validate these initial choices against latency and attack coverage. Use non-overlapping windows for scoring, a stable session ID across windows, and separate final session summaries. Train on the same windows used online.

Initial feature groups: directional packets/bytes, duration, size statistics, inter-arrival statistics, TCP flag counts, protocol, and carefully selected connection state. Add causal host-window features such as distinct destinations/ports and connection rates for scanning and repeated connection activity. Compute these using only prior/current observations. Raw addresses and absolute capture timestamps are metadata, not default model features.

Maintain online aggregates instead of per-packet lists. Define zero-duration/empty-direction handling explicitly. Validate finite values, nonnegative counts, packet/byte identities, units, unique event IDs, and unsupported packets. Do not silently substitute zero for required missing features. Unknown and malformed observations must remain visible as data quality issues.

### Labels and splits

Store labels in a separate dataset/evaluation channel. Scoring takes telemetry only. Join labels after predictions using immutable event/session IDs. Only reviewed analyst labels or verified benchmark/lab labels qualify for supervised training. Predictions, severity, and arbitrary sender labels are not ground truth.

Split sessions/scenarios/captures before preprocessing and window construction where necessary. Keep all windows and near duplicates from a session or scenario together. Use train, validation/calibration, and locked test partitions, targeting roughly 60/20/20 where independent groups permit. Prefer chronological partitions and report family coverage; never force a percentage by leaking a capture across partitions. Reserve explicit unseen-scenario/family evaluations and report these separately from known-family detection.

Fit transformations only on training data, tune models and thresholds only on validation data, and evaluate the locked test once per release decision. A failed release followed by development requires a fresh independent confirmation set; do not repeatedly optimize against the same test. Class weighting/resampling applies only to training. Keep evaluation prevalence visible and report per-source results so dataset identity cannot masquerade as attack detection.

## 4. Target implementation

```text
PCAP replay / live capture -> common flow extractor -> validated bounded queue
Windows process events ----------------------------> endpoint normalizer
                                                     |
                                                     v
                                            rules + real model inference
                                                     |
                                                     v
                                           incident correlation / dedup
                                                     |
                                                     v
                                            SQLite -> API -> dashboard

Reviewed labels -> offline dataset builder -> training -> independent evaluation
                                                -> versioned approved artifact
```

Separate collection from the API's lifecycle and privileges. Bind local services to loopback by default. Use a bounded in-process queue for a single-process flow path or acknowledged authenticated local ingestion between processes, with sequence numbers, durable retry where needed, and explicit drop counters. Remove public unauthenticated UDP ingestion from the default runtime.

Suggested modules: backend/app.py, config.py, schemas.py, collectors/, features/, detection/, storage/, api/; training/ for preparation/splits/training/calibration; evaluation/ for replay and release reports; models/<task>/<version>/ for manifests and trusted artifacts. This is a modular application; distributed services are unnecessary for the first release.

Retain existing dashboards and API concepts while migrating behind them. Add migrations and a single configured database path. Store immutable telemetry and predictions separately from analyst labels, incidents, and evaluation runs. Include event ID, sensor ID, model version, feature version, rule version, timestamp, raw score, threshold, prediction, and reasons. Do not reinterpret historical predictions using the current threshold.

## 5. Ordered delivery work

### Phase 0 — Reproduce and preserve (1-2 engineering days)

- Inventory existing changes; create a recoverable checkpoint without restoring/deleting the user's work. Back up SQLite with a consistent backup method including active WAL state.
- Diagnose the interpreter permission/runtime issue. Choose a supported Python version after confirming package compatibility, lock dependencies, and separate core, Windows collector, and optional research dependencies.
- Add a documented launch/configuration path, absolute application-relative artifact paths, explicit startup diagnostics, graceful shutdown, and real readiness checks.
- Preserve current data/models as legacy artifacts; remove their unverified evaluation claims from active status displays.

Exit: a clean setup can start the API and replay mode with a fresh database, and missing optional collectors/models report unavailable accurately.

### Phase 1 — Make detection honest (2-3 days)

- Remove label-driven decisions, input-score overrides, display jitter, and mock learned-model fallbacks from inference.
- Consolidate voting/calibration into one versioned policy; show raw anomaly scores as scores unless probability calibration has been validated.
- Mark replay/live provenance and prohibit synthetic fixtures from entering operational metrics or supervised datasets by default.
- Decouple label writes from public ingestion. Preserve unknown labels, and distinguish no evidence from benign.

Exit: identical telemetry with identical ordered context produces the same predictions regardless of added, removed, or changed evaluation labels. Unavailable models never report online. Injected score/severity fields cannot control results.

### Phase 2 — Repair collection and storage (4-6 days)

- Implement the common bidirectional flow/window contract, reverse-direction accounting, IPv6 handling, bounded memory, expiration, and dropped-packet/error instrumentation.
- Exclude the system's own collection transport from capture; avoid duplicate collector instances.
- Re-enable scan detection as a causal multi-connection rule with tested grouping and cooldowns, replacing broad suppression of small flows.
- Implement schema validation, event IDs, acknowledgment/retry semantics, batched persistence, retention, migrations, and resumable replay.
- Add a Windows event collector using Sysmon process creation records where available; preserve WMI as an explicitly limited fallback. Sysmon supplies process command line and correlation information. [Microsoft documentation](https://learn.microsoft.com/en-us/sysinternals/downloads/sysmon).
- Replace blanket browser/service-parent exclusions and permanent command-string deduplication with contextual filtering and counted incident grouping.

Exit: known PCAP fixtures produce expected directional features and matching offline/live-parser outputs. Repeated events are idempotent, resource limits work, capture failure is visible, and shutdown/restart preserves recorded events.

### Phase 3 — Build defensible datasets (3-5 days plus collection time)

- Create download/import manifests, immutable raw storage, label adapters, schema validation, provenance reports, and group-aware split manifests.
- Re-extract public PCAPs with the production feature library. Align labels with time/tuple/session information; quarantine ambiguous joins and report exclusions.
- Begin local background capture early and gather multiple independent sessions for each supported attack scenario and benign lookalike.
- Keep the inconsistent CSVs in legacy/demo storage. Do not repair invented data by adjusting totals and then call it real telemetry.

Exit: every accepted row is traceable to a capture/session/label source; train/test group overlap is zero; feature invariants pass; independent family support and remaining gaps are reported.

### Phase 4 — Train and select useful models (3-5 days)

- Establish rules-only and simple supervised baselines; train Random Forest for binary suspicious-flow scoring. Compare a boosting candidate only after the baseline evaluation works.
- Train Isolation Forest on training-only reviewed benign traffic. Treat it as an anomaly signal and measure incremental value at the same false-alert budget before enabling it for incidents.
- Calibrate decision thresholds on validation data under an explicit false-alert budget. Evaluate models and the complete rules/correlation pipeline separately.
- Keep command rules as the initial endpoint baseline. Compare a supervised character n-gram classifier plus process context after collecting adequate labeled data; hold out command templates/scripts, not random cosmetic variants.
- Save the complete transformation/model pipeline with feature order, task type, training hashes, commit, dependency versions, seeds, splits, thresholds, and metrics. Separate network and command artifact namespaces. Reject incompatible artifacts at startup.
- Keep GNN disabled in release one. Reintroduce it only as a measured experiment with causal graphs, independent capture splits, realistic streaming warm-up, and an ablation proving additional value for its cost.

Exit: a reproducible candidate report shows performance, uncertainty, operational cost, and comparison to rules-only. No candidate is promoted merely because it is newer or more complex.

### Phase 5 — Make the SOC usable (3-4 days; can overlap after API contract stabilizes)

- Show live/replay mode, capture interface and scope, collector heartbeat, queue/drop counts, database status, and real model readiness.
- Replace universal healthy responses with component readiness and actionable errors. Use same-origin API/socket URLs.
- Display evidence, first/last seen, event counts, detection reasons, model/rule versions, and incident states: new, investigating, resolved, false positive.
- Persist analyst decisions with provenance; keep them separate from automatic predictions. Use safe text rendering for commands and untrusted event fields.
- Show live volume separately from labeled offline evaluation. Report sample support and unknown labels; show unavailable rather than invented or zero accuracy.
- Default to local access. Before shared deployment, add authentication, authorization, restricted origins, protected write operations, request limits, and encrypted remote transport.

Exit: an analyst can investigate and label an incident, reconnect without missing persisted data, and distinguish capture failure, quiet traffic, unknown labels, and unavailable inference.

### Phase 6 — Qualify the complete release (3-5 days plus soak time)

- Run an end-to-end PCAP replay through ingestion, extraction, inference, persistence, and dashboard; compare event IDs and counts at each stage.
- Test malformed/oversized payloads, missing/corrupt models, mismatched features, unavailable capture drivers, collector crashes, queue overload, database contention/disk limits, websocket reconnects, and restart recovery.
- Run a 72-hour soak followed by a 7-day local shadow pilot with reviewed alert outcomes. Record hardware and offered packet/flow/event rates.
- Exercise backup/restore and atomic model promotion/rollback. Retain the previous artifact and prohibit automatic retraining on unreviewed detections.
- Rewrite setup instructions and the paper/results from versioned reports. Provide a reproducible demo using held-out data with labels inaccessible to inference.

Exit: release gates below pass or the release report explicitly limits scope and documents unresolved failures.

## 6. Proposed release gates

These are initial acceptance targets for the stated small-lab deployment, not measured results or promises. Revise them before testing if actual hardware/workload requires different bounds, then freeze them for that release.

| Area | Gate |
|---|---|
| Inference integrity | Zero paths from evaluation labels to predictions; no random score decoration or fake readiness |
| Feature integrity | All accepted rows pass schema/invariant checks; offline and live extraction agree within documented numerical tolerance |
| Split integrity | Zero overlap of session/scenario/duplicate groups; all learned preprocessing and tuning isolated from locked test |
| Known-scenario detection | Initial target >=90% incident recall on declared supported scenarios and >=90% precision at the pilot prevalence; report family-level counts and confidence intervals |
| False-alert burden | Initial target <=1 reviewed false incident per monitored host-day; also report flow-level FPR and total false incidents for the whole sensor |
| Evidence volume | Aim for >=30 independent held-out instances per supported family and >=14 monitored benign host-days; these are minimum planning targets, not proof of statistical adequacy |
| Latency | At a declared initial load of 100 completed windows/events per second, p95 scoring-to-persistence <=100 ms and API p95 <=500 ms; measure observation-window delay separately |
| Reliability | 72-hour soak without uncaught crashes or sustained unbounded memory growth; explicit loss/drop accounting; idempotent persistence under retry |
| Recoverability | Documented restart, database restore, and model rollback demonstrated |

Report precision, recall, PR-AUC, confusion matrices, per-family/per-source support, event-level versus incident-level results, confidence intervals over independent sessions, unknown-label coverage, and false incidents per host-day. Do not imply that raw score magnitude is calibrated confidence. Example of why accuracy is insufficient: a 0.1% flow false-positive rate across 100,000 benign flows means about 100 flagged flows before incident grouping.

Unknown attack-family detection must have its own evaluation and limitations; it is not covered by a known-scenario recall target. Small sample support warrants a provisional result, not a rounded claim of perfection.

## 7. Maintenance and effort

Expected initial effort: about 4-6 focused engineering weeks, with data collection beginning early and continuing in parallel. A broader enterprise deployment, comprehensive attack coverage, or a research-grade GNN would require additional work. Estimates depend on data availability, capture permissions, hardware, and quality of labels.

After release, track collection health, feature drift, alert burden, and reviewed misses. Create retraining candidates from curated versioned data on demonstrated drift or coverage gaps; evaluate, approve, deploy atomically, and retain rollback. Recheck thresholds against current benign activity without reusing the locked benchmark as a tuning set. Review retention, access to command/packet data, and database growth regularly.

The first implementation milestone is an honest, reproducible replay pipeline with repaired flow extraction. New training follows that milestone; otherwise a larger dataset will train against incorrect features and misleading measurements.
