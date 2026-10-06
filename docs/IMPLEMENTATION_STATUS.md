# Implementation status — 29 September 2026

## What works now

The local application supports replay, shared bidirectional flow extraction, deterministic scan and command rules, authenticated ingestion, SQLite storage, incident review, analyst labels, retention and backup. Incoming labels and scores cannot dictate predictions. The dashboard distinguishes replay, live collection, rules and model availability.

The normal entry point is `scripts/start.ps1`; open http://127.0.0.1:5000/operations. A generated local token is required for changes. The synthetic demonstration exercises extraction, ingestion and grouping without transmitting attack traffic.

## Measured evidence

| Check | Recorded result | Limit |
| --- | --- | --- |
| Regression suite | 19 tests passed | Does not establish live detection accuracy |
| Browser checks | Five pages; no captured JavaScript errors; mobile Operations fits 390 px | Fresh headless Chrome, not every browser |
| Bounded persistence measurement | 1,000 events; approximately 149 events/s; persistence p95 15.1 ms | One producer on this machine; not sustained capacity |
| CIC CSV held-out evaluation | Precision 99.70%, recall 45.53%, benign false-positive rate 0.0559% | Friday held out; unseen families and source feature schema |
| UNSW CSV held-out evaluation | Precision 99.39%, recall 44.54%, benign false-positive rate 0.2361% | Supplied filenames have reversed official row counts; not the standard published split |

Reports are in `artifacts/benchmarks/`, `artifacts/qualification.json` and `artifacts/browser-check.json`. CSV classifiers are offline-only. Their high precision does not compensate for missed attacks, and their features do not match the live extractor.

## Work running or pending

1. Download and checksum all five CICIDS2017 packet captures and eight label files. Partial captures resume without discarding saved bytes. The source is a pinned public mirror; mirror hashes establish download integrity, not independent publisher authenticity.
2. The continuation process waits for complete verification, then extracts canonical windows, joins independent labels and quarantines ambiguous matches. It stops on poor alignment or capacity drops.
3. Train a canonical candidate on Monday–Wednesday, select the threshold on Thursday and evaluate Friday. Complete sessions are sampled deterministically without using their labels. The resulting candidate remains unapproved.
4. Install Npcap interactively and configure Sysmon for live collection. The installers have been downloaded; installation is not confirmed. WMI is an explicitly limited fallback and may miss short processes.
5. Run an independent live shadow pilot and 72-hour soak, measure false alerts and missed scenarios, and review the release thresholds before approving deployment.

Live progress is available in Operations and `artifacts/pipeline-status.json`. Download logs are `artifacts/download.stdout.log` and `artifacts/download.stderr.log`. A running process requires this computer to remain awake. After a reboot, resume acquisition and continuation using the commands in the README; recorded PIDs are informational and may become stale.

UNSW packet captures have not been acquired: the publisher's linked storage redirects to authentication. No authenticated content was bypassed. CIC captures provide the first shared-extractor training path; UNSW CSV results remain separate.

## Completion criteria

This is a functioning replay and rules application with an unfinished model qualification process. It is not a perfect detector or a production-qualified deployment. Release requires verified captures, adequate and audited label alignment, a compatible model with acceptable held-out results, working live collectors, a completed shadow pilot and soak, and a tested recovery procedure.

Historical papers and overview documents describe the earlier prototype and are not evidence for this implementation. Original source and the database were checkpointed under `artifacts/checkpoints/`; the new application uses `data/soc.db`.
