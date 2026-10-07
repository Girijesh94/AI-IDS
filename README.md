# AI IDS / SOC

A local Windows intrusion-monitoring application with real packet capture, packet replay, shared bidirectional flow extraction, trained traffic models, command rules, SQLite incident storage and a browser dashboard.

## Current state — 7 October 2026

The application works locally. Npcap capture has been verified, canonical training has finished, and a compatible trained candidate is included in `pretrained/canonical-all-families-v2/`. Default startup scores that candidate in **shadow mode**: predictions are recorded for review, while deterministic rules raise incidents. Default collection mode is replay; select live mode explicitly.

**Production qualification is incomplete.** The live 72-hour network soak is running on the development machine. Independent live labels are still needed. Built-in Windows Sysmon is installed and its service runs, but the Windows event channel currently returns error 4201; endpoint collection therefore uses an explicitly limited WMI fallback. Rare attacks have insufficient support or weak recall. See [implementation status](docs/IMPLEMENTATION_STATUS.md).

## Start

Verified locally with Windows and Python 3.14.7:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
.\scripts\start.ps1
```

Open [Operations](http://127.0.0.1:5000/operations). No PCAP download is needed to load the bundled candidate. The server binds to localhost. `data/local-token.txt` contains the write token; enter it in Operations to review incidents and label events. The token is never embedded in the page.

The browser interface includes an interactive 3D sensor, X-ray inspection, liquid metal emblem, ripple background and pointer effects. It adapts to mobile screens and reduced motion. The built frontend is included; rebuilding it requires Node. See [frontend implementation and build instructions](docs/FRONTEND.md).

For live collection after installing [Npcap](https://npcap.com/):

```powershell
.\scripts\start.ps1 -Mode live -Database "$PWD\data\live.db"
```

Scapy uses the default network interface unless `-Interface` is supplied. Operations shows the selected interface, collector state, packet counts, drops, model mode and endpoint limitations. Collection sees traffic available at that interface.

Select another locally trusted candidate explicitly:

```powershell
.\scripts\start.ps1 -Mode live -Database "$PWD\data\live.db" -Model "$PWD\models\another-candidate" -Shadow
```

An unapproved candidate is rejected for active model alerts. Approved artifacts can be selected with `-Model` without `-Shadow` after the release evidence and independent review are complete. Joblib uses pickle: load only trusted local artifacts.

## Measured model results

| Evaluation | Test windows | Precision | Attack recall | Benign false-positive rate |
| --- | ---: | ---: | ---: | ---: |
| All-family candidate: grouped session/feature holdout | 65,473 | 99.63% | 95.58% | 0.0390% |
| Separate strict Friday capture holdout | 60,018 | 95.09% | 35.41% | 0.6691% |

The first evaluation trains on all available labeled families. All segments of the same captured connection, whole sessions and identical feature vectors form connected components, and each component belongs to one partition. Captures are shared across partitions; this is an evaluation within CICIDS2017, **not accuracy on an independent network**. Threshold selection uses validation only.

The strict Friday test trains on Monday–Wednesday and tunes on Thursday. Its poor Bot/PortScan performance exposes limits when attack families are absent from training. The all-family candidate uses Friday labels, so that strict test cannot be reused to claim its generalization. Family counts and misses remain visible in Operations and the [model card](pretrained/canonical-all-families-v2/MODEL_CARD.md).

CIC and UNSW CSV benchmark models remain separate from live inference because their feature schemas differ. Their locally generated reports appear under Offline evaluations. The CSV models and reports are not needed for startup and are not bundled.

## Reproduce acquisition and training

```powershell
.\.venv\Scripts\python.exe -m training.download
.\.venv\Scripts\python.exe -m scripts.complete_pipeline
.\.venv\Scripts\python.exe -m training.train_grouped
# Package a new candidate to a new destination:
.\.venv\Scripts\python.exe -m training.package_model --input models/canonical-all-families-v2 --output pretrained/my-candidate
```

The five CIC captures and eight label files are downloaded from a pinned public mirror. Download manifests record hashes and provenance. Approximately 53 GB of captures plus working space are required. All five captures were rechecked against recorded hashes during preparation on this machine.

Preparation uses the same flow state machine as live capture. It checks label alignment across all extracted windows, quarantines ambiguous/unmatched labels, then writes a deterministic sample of complete sessions (one in ten). Three day workers run concurrently. Completed days have checksum-verified checkpoints; interrupted days restart. Cross-partition feature duplicates are removed for the strict capture evaluation. The grouped trainer instead connects all segments of the same captured connection and shared feature vectors to keep them in one fold.

`complete_pipeline` resumes preparation and creates or verifies `models/canonical-v3/`, the strict capture candidate. `train_grouped` creates the all-family candidate in a new directory. Use its `--output` option for another run. Candidate creation never grants deployment approval. The repository includes a compressed copy of the all-family estimator, its checksum and report.

UNSW PCAP acquisition remains unavailable through the publisher's authentication redirect. Existing UNSW CSVs support an offline benchmark; they are not converted into invented live features.

## Checks and live qualification

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m scripts.qualify --model pretrained/canonical-all-families-v2 --shadow --output artifacts/qualification-model.json
.\.venv\Scripts\python.exe -m scripts.browser_check
```

Browser checks require `requirements-dev.txt` and installed Chrome. GitHub Actions runs the regression checks on Windows. Published local evidence is in [validation results](docs/VALIDATION_RESULTS.json).

With the server in live shadow mode:

```powershell
.\.venv\Scripts\python.exe -m scripts.shadow_soak
.\.venv\Scripts\python.exe -m scripts.release_report
```

The default soak covers network capture and model availability. It requires 72 uninterrupted hours and new telemetry. Suspension, server restart, collector failure or drops invalidate that run. Logs are under `artifacts/shadow-soak.*`. Once Sysmon works, use `--require-sysmon` for full collector qualification. The release report requires that full scope, independent reviewed live sessions, acceptable false alerts/recall and adequate family support. It never approves a model automatically.

See [runbook](docs/RUNBOOK.md) for Windows setup, backup, restore, incident review and collector limits. Historical papers describe the older prototype and are not current validation evidence.

## Repository boundaries

- `backend/`: application, feature contract, collection, rules, inference and storage.
- `training/`: downloads, CSV benchmarks, canonical labeling and training.
- `pretrained/`: one documented candidate with checksum and measured limitations.
- `scripts/`: startup, maintenance, qualification and continuation.
- `frontend/`: monitoring and incident review.
- `tests/`: regression and data-integrity checks.
- `data/`, `artifacts/`, `models/`: local datasets, logs, databases and experimental artifacts excluded from Git.

## Data and collector sources

[CICIDS2017 publisher](https://www.unb.ca/cic/datasets/ids-2017.html), [CIC mirror](https://huggingface.co/datasets/bvsam/cic-ids-2017), [UNSW-NB15 publisher](https://research.unsw.edu.au/projects/unsw-nb15-dataset), [Npcap](https://npcap.com/), [Microsoft Sysmon](https://learn.microsoft.com/en-us/sysinternals/downloads/sysmon).
