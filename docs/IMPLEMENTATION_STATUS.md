# Implementation status — 7 October 2026

## Operational application

The application runs locally with real Npcap capture, shared IPv4/IPv6 flow windows, authenticated ingestion, deterministic scan/command rules, SQLite persistence, incident review, independent analyst labels, retention and backup. The Operations page shows real collector health and model availability. Payloads are not retained. Sender labels and scores cannot control predictions.

The current live server listens at http://127.0.0.1:5000/operations, using `data/live.db`, the active Wi-Fi interface and the bundled `canonical-all-families-v2` candidate in shadow mode. Classifier predictions are recorded for review. Rules raise incidents. The model remains unapproved for active model alerts.

Npcap is installed and running. A 15-second capture check observed 606 packets and 28 flow windows with zero queue drops, capacity drops or processing errors. The running server has continued collecting real traffic. This check establishes collection plumbing, not detection accuracy.

The standalone signed Microsoft Sysmon 15.22 installer validated the configuration but failed at event-manifest registration. The supported built-in Windows optional feature was then enabled and its `Sysmon` service installed successfully with the process-event configuration. The service is running. However, Windows channel access currently returns error 4201 (the instance name is not recognized by a WMI provider), including from an elevated diagnostic. The application therefore remains on the explicitly limited WMI fallback, which can miss short-lived processes. No full Sysmon capture pass is claimed. Installation and channel diagnostics remain under `artifacts/sysmon-*`. The Windows event provider state still needs repair; a Windows restart may be necessary.

## Data and completed training

All five CICIDS2017 captures, eight independent label files and the mirror README finished downloading. Every capture and label file was rechecked against the recorded hash before preparation. Mirror hashes prove integrity against that mirror, not independent publisher authenticity.

Preparation completed for all five days with no extractor capacity drops. It uses a fast header decoder and the same state machine as live capture. Tests compare the fast/reference paths for PCAP, PCAPNG, nanosecond timestamps, VLAN, IPv6, fragments and timing. One thousand real Tuesday windows were also compared exactly. Repeated same-time reset packets now receive distinct deterministic session/event IDs.

Labels are matched by bidirectional endpoints/protocol and observation interval. Minute-truncated timing is reported; ambiguous and unmatched labels are quarantined. Coverage is checked over all windows. A deterministic one-in-ten complete-session sample is written without using labels to select sessions. Completed days have output checksums and can be reused after interruption.

Two compatible candidates were trained:

| Evaluation | Windows | Precision | Attack recall | Benign FPR |
| --- | ---: | ---: | ---: | ---: |
| Strict Friday capture holdout | 60,018 | 95.09% | 35.41% | 0.6691% |
| All-family grouped holdout | 65,473 | 99.63% | 95.58% | 0.0390% |

The strict candidate trains on Monday–Wednesday and tunes on Thursday. Its absent-family failures are retained in `docs/FRIDAY_HOLDOUT_REPORT.json`. The bundled all-family candidate trains on three of five grouped folds; validation and test each use a separate fold. All segments of a bidirectional capture/endpoint tuple and sessions connected by identical numeric feature vectors remain together. Captures are shared across its partitions; it is an in-dataset evaluation and cannot claim independent-network generalization. Its artifact, checksum, complete report and model card are in `pretrained/canonical-all-families-v2/`.

Family results remain uneven: Bot recall is 9.5% on 42 test windows, GoldenEye 73.8%, FTP-Patator 77.9%, and infiltration 0% on one window. Heartbleed and SQL injection have no test support; tiny web/infiltration samples cannot establish reliable family performance. Aggregate precision is not evidence that every family is supported.

Existing CIC and UNSW CSV classifiers remain separate offline benchmarks. UNSW PCAP acquisition remains blocked by the publisher's authentication redirect; no synthetic replacement was used.

## Local validation evidence

- 26 regression checks passed, including import/startup, live feature contract, candidate checksum/approval, shadow isolation, persistence, backup/recovery, data grouping and checkpoint integrity.
- Five browser pages passed with no captured JavaScript errors. Operations fits a 390-pixel viewport.
- A bounded 1,000-event synthetic measurement with the candidate enabled stored every event, approximately 71.2 windows/second, scoring/persistence p95 15.1 ms and read API p95 8.7 ms. This measures one producer on this machine, not sustained network capacity.
- The model can load in a fresh process using the pinned dependencies. GitHub Actions is configured to run the regression checks on Windows after pushes.

Published evidence is in `docs/VALIDATION_RESULTS.json`. Generated local reports, screenshots and diagnostics remain under `artifacts/`.

## Running qualification and remaining gates

A 72-hour **network shadow model** soak has started. It measures real collection stability, requires new telemetry and fails on suspension, polling gaps, server restarts, unavailable capture or drops. Status is in `artifacts/shadow-soak.json`; its PID is in `artifacts/soak.pid`. The computer must remain awake. This is running, not passed. It does not establish endpoint completeness or classifier accuracy.

Production qualification still requires:

1. Repair the Windows Sysmon event channel (error 4201) and validate full endpoint collection.
2. An uninterrupted full collector soak (`scripts.shadow_soak --require-sysmon`).
3. Independently reviewed live sessions, false-alert measurement and realistic authorized scenario coverage.
4. Adequate supported-family evidence and review of the documented weak/rare families.
5. An independent deployment review and approved manifest, with a recovery/rollback exercise.

`scripts.release_report` computes evidence from reviewed live events and soak records. It never fabricates labels, marks missing evidence as passed or promotes a model. The current release report fails the production gates. The functioning local application and trained shadow candidate are complete; production qualification remains incomplete.
