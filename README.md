# IDS/SOC: reproducible monitoring and evaluation

A Windows-first local intrusion-monitoring application with packet replay, bounded bidirectional flow extraction, command rules, SQLite incident storage, and a browser dashboard. The default is **replay mode**. Live machine-learning detection is gated on a compatible, independently evaluated model.

## Current status

- Modular Flask + Socket.IO application served on loopback by Waitress.
- Labels, incoming scores, and severity cannot override inference. No mock models or random score changes in the runtime.
- IPv4/IPv6 flow windows, scan rules, authenticated ingestion, incident review, independent analyst labels, database backup, and retention.
- Separate trained CICIDS2017 and UNSW-NB15 CSV benchmark artifacts and held-out reports.
- Resumable PCAP/label downloads with checksums, canonical extraction, label alignment, and candidate training tools.
- **Not yet qualified for production:** canonical model training awaits complete PCAP acquisition; live collectors require Windows setup; the 72-hour soak and shadow pilot remain outstanding.

See [implementation status](docs/IMPLEMENTATION_STATUS.md), [full rework plan](docs/REWORK_PLAN.md), and [runbook](docs/RUNBOOK.md). Historical project papers describe the older prototype; they are not current validation evidence.

## Setup

The current environment is verified on Windows with Python 3.14.7. Install a compatible Python interpreter, then from the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
.\scripts\start.ps1
```

Open [Dashboard](http://127.0.0.1:5000) or [Operations](http://127.0.0.1:5000/operations). The server binds only to 127.0.0.1. It creates `data/soc.db` and a local write token in `data/local-token.txt`. Keep that token private; enter it in Operations to review incidents and labels. Set `IDS_TOKEN` to override it.

The original `alerts.db`, model files and training CSVs are preserved as legacy material and are not loaded into the new runtime. A source/database checkpoint is under `artifacts/checkpoints/`.

## Reproducible demo

With the server in replay mode:

```powershell
.\.venv\Scripts\python.exe -m scripts.demo
```

This writes an explicitly synthetic PCAP locally and processes it through the real extraction and ingestion path. It does not send scan packets onto the network. The fixture generates 25 flow windows and one grouped scan incident. Repeating the same fixture is idempotent. It verifies plumbing and rules, not learned attack-detection accuracy.

## Real datasets

CSV benchmark commands:

```powershell
.\.venv\Scripts\python.exe -m training.benchmark --dataset cicids2017 --input 'C:\path\to\CIC-CSV' --max-per-file 60000
.\.venv\Scripts\python.exe -m training.benchmark --dataset unsw-nb15 --input 'C:\path\to\UNSW-CSV' --max-per-file 0
```

Reports, complete split manifests, predictions and model checksums are written to `artifacts/benchmarks/<run>/`. CIC sampling is uniform per capture, before labels are used. CIC partitions are Monday-Wednesday training, Thursday validation, Friday test. UNSW uses the supplied filename partitions with fingerprint-group validation. Neither benchmark proves full session independence where source identifiers are missing. Models are explicitly offline-only and rejected by the live loader.

Download missing CIC PCAPs and matching labels:

```powershell
.\.venv\Scripts\python.exe -m training.download
```

The public mirror revision and checksums are recorded in `data/raw/cicids2017/download-manifest.json`. The downloader needs about 53 GB plus working space. It resumes `.part` files. Do not launch a second downloader while one is active. Operations displays progress. The UNSW publisher's PCAP link currently redirects to authentication; its existing CSV benchmark remains usable.

After downloads finish, or while the downloader is active in another process:

```powershell
.\.venv\Scripts\python.exe -m scripts.complete_pipeline
```

This waits for verified captures, extracts the same flow-window schema used live, joins independent labels, checks overlap/alignment, and trains a **candidate**. Progress is in `artifacts/pipeline-status.json`. The current labels have minute-level timing; the join explicitly allows that uncertainty, rejects conflicting labels, and reports match coverage. Failure gates stop training when alignment is poor or extraction drops flows.

Candidate artifacts remain unapproved until the release gates and shadow pilot are reviewed. Existing labels and predictions never automatically retrain the active detector.

## Live collection

Install Npcap using the signed installer under `data/installers/` (or the official Npcap site). Install/configure Sysmon from Microsoft's official package for process events. These are system-level Windows setup steps; downloading the files does not install them. See the runbook.

```powershell
.\scripts\start.ps1 -Mode live -Interface '<Scapy interface name>' -Database 'C:\path\to\live.db'
```

A network sensor sees traffic available at its interface. A workstation cannot monitor an entire switched network without appropriate observation placement. Capture failures are visible in Operations. GNN and legacy command AI remain disabled. Loopback dashboard traffic on TCP port 5000 is excluded from capture.

## Validation

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m scripts.qualify
# Optional browser check, using installed Chrome and requirements-dev.txt:
.\.venv\Scripts\python.exe -m scripts.browser_check
```

The tests cover bidirectional/IPv6 extraction, disjoint windows, malformed data, label isolation, deterministic rules, API access, deduplication, incident review, backup/restore, model compatibility, timestamp precision and split isolation. The bounded qualification is not the 72-hour soak.

## Data and model boundaries

- `backend/`: runtime, common feature contract, deterministic detection, API, persistence, optional endpoint collector.
- `training/`: acquisition, source-specific CSV benchmarks, PCAP extraction/labels, canonical model training.
- `scripts/`: startup, demo, maintenance, qualification, continuation.
- `frontend/`: existing dashboard plus Operations.
- `tests/`: regression and data-integrity tests.
- `data/`, `artifacts/`, `models/`: local generated content excluded from Git.

Older training helpers and UDP senders are historical reference code. Use the commands above for current workflows. No network or endpoint event alone confirms every attack family: evidence and human review remain necessary.

## Sources

- [CICIDS2017 publisher](https://www.unb.ca/cic/datasets/ids-2017.html)
- [CIC public mirror used for acquisition](https://huggingface.co/datasets/bvsam/cic-ids-2017)
- [UNSW-NB15 publisher](https://research.unsw.edu.au/projects/unsw-nb15-dataset)
- [Npcap](https://npcap.com/)
- [Microsoft Sysmon](https://learn.microsoft.com/en-us/sysinternals/downloads/sysmon)
