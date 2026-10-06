# Local operations runbook

## Startup and modes

Run `scripts/start.ps1` from PowerShell. Default mode is replay and the listener is loopback-only. Use a separate `-Database` for live and replay runs when maintaining independent operational history. No collector starts merely by importing the application.

The server uses Waitress and Socket.IO HTTP polling. It is a single-host application; remote deployment and multi-user identity are not configured. A local bearer token protects write operations. Startup creates `data/local-token.txt` unless `IDS_TOKEN` is supplied. The browser does not persist this token. Enter it in Operations when making changes.

Stop a foreground server with Ctrl+C; the runtime stops capture and attempts to drain its queue. Investigate nonzero processing errors or drop counters before trusting collection completeness. Queue depth, capture state, interface, packet counters and endpoint state are available at `/api/network-status`.

## Windows collection setup

1. Run the signed `data/installers/npcap-1.89.exe` installer. The free edition is interactive. This installs a Windows driver and may require administrator approval.
2. For Sysmon, extract the official `data/installers/Sysmon.zip` and verify the Microsoft executable signature. A minimal process-create configuration is in `scripts/sysmon-processes.xml`. An administrator can install with `Sysmon64.exe -i <absolute configuration path>`. Review its EULA and configuration. Review any existing Sysmon configuration before changing it.
3. List interfaces with `.venv\Scripts\python.exe -c "from scapy.all import get_if_list; print(get_if_list())"`.
4. Start `scripts/start.ps1 -Mode live -Interface '<interface>' -Database '<absolute live database path>'`.
5. Verify packet counts and heartbeats change with ordinary authorized traffic. Missing drivers must show an error. Endpoint collection uses Sysmon where accessible; the limited WMI fallback may miss short-lived processes and is shown as degraded.

Only traffic visible at the selected interface is observed. IPv4/IPv6 fragments and unsupported protocols are counted; reassembly is outside this version. Flow state is bounded to 20,000 active entries. Bytes count IP packets including headers. Five-second windows are disjoint, with ten-second idle expiry and sixty-second segmentation. Live capture retains no payloads. Dashboard traffic on TCP 5000 is excluded.

## Data acquisition and continuation

Acquisition uses a pinned public mirror revision because the CIC publisher form failed during this run. Hashes verify bytes against mirror metadata; they are not independent publisher signatures. Keep the downloaded README and manifest for attribution/provenance.

`python -m training.download` resumes incomplete captures. Do not run duplicate downloader instances. `python -m scripts.complete_pipeline` waits for verification, prepares canonical data, joins labels, then trains a candidate. Progress is in `artifacts/pipeline-status.json`; the current background job logs to `artifacts/pipeline.stdout.log` and `artifacts/pipeline.stderr.log`. Its process ID is in `artifacts/pipeline.pid`. Preparation now resumes checksum-verified day checkpoints under `data/prepared/canonical-v3/`. Interrupted days restart. The strict candidate is reused only when model and input checksums match. Run `python -m training.train_grouped` afterward for a new all-family candidate; use a fresh `--output` directory if it already exists. Reboot interrupts these jobs; restart acquisition and then continuation to resume.

The five captures total approximately 53 GB. Extraction needs additional working space and CPU time. All five captures and eight label files have been downloaded and verified on the development machine. Three workers prepare days independently. The label join uses bidirectional endpoint tuple, protocol and observation interval, infers timestamp precision, and excludes conflicting/unmatched labels. Minute-truncated labels have up to sixty seconds of timing uncertainty, recorded in the extraction report. Training stops if alignment is below 80% or capacity drops occur. Preparation samples one in ten complete sessions using a stable hash independent of labels, after measuring alignment over all windows. The trainer does not sample those selected sessions again. Use `--session-sample-modulus 1` with `training.label_pcaps` and a new output directory for all sessions on sufficiently large hardware.

The UNSW publisher's PCAP link redirects to sign-in. Its downloaded CSVs support an independent offline benchmark; inaccessible captures are not replaced by synthetic data.

## Models and promotion

CSV artifacts are dataset-specific and cannot be loaded for live flow inference. A canonical model requires `schema_version=flow-window-v1`, exact feature order, checksum, version, threshold and explicit approval. Only trusted local artifacts may be loaded: joblib uses pickle and is unsafe for untrusted interchange.

Candidate creation does not approve deployment. Complete independent review, false-alert measurement, supported-family recall, the 72-hour soak and shadow pilot first. Retain the previous approved directory. Select an approved artifact with `IDS_MODEL` or `start.ps1 -Model`, then restart. Invalid models report unavailable while rules continue. Roll back by selecting the previous directory. There is no automatic retraining on detections.

## Incident review

Operations groups related alerts within a five-minute arrival window, preserving first/last seen, counts, mode, reasons and last evidence ID. States are new, investigating, resolved and false positive. Labels require an analyst name and evidence note. Reviews are audited separately and never alter stored predictions.

The demo is explicitly synthetic and verifies the scan rule and pipeline. It does not demonstrate model accuracy. CSV precision/recall appears in offline evaluation. Live performance is unavailable without independent reviewed labels; unknown does not mean benign.

## Backup and recovery

Run `.venv\Scripts\python.exe -m scripts.maintenance backup --database data/soc.db --destination data/backups/<new-file>.db`. SQLite's backup API captures committed WAL state. The destination must not exist. Check the backup opens successfully.

To restore: stop the application, preserve the database and WAL/SHM sidecars, copy the backup to a new path, then start with `-Database <restored-path>`. A new path avoids stale WAL files mixing with restored data. Retain the original for investigation.

Maintenance removes unreviewed/unreferenced events and logs older than 30 days by receipt time. Reviewed labels, audits and incident evidence are retained. Plan separate archival if these grow large.

## Qualification

Run the regression suite after changing scoring, extraction or persistence. `scripts.qualify` records a bounded single-producer 1,000-event measurement. `scripts.browser_check` uses a fresh headless Chrome instance and saves desktop/mobile screenshots without using the user's profile.

These checks do not replace multi-day live evaluation, driver validation, independent attack scenarios, uncertainty estimates over sessions or enterprise access controls. Remaining gates are tracked in `docs/IMPLEMENTATION_STATUS.md`.


## Bundled candidate and shadow collection

Startup includes `pretrained/canonical-all-families-v2` in shadow mode by default. It is a compatible estimator with a checksum and grouped evaluation report; it is not deployment-approved. Shadow model flags are stored inside `model_results` and do not create incidents. Scan/command rules continue to create incidents. Select another trusted candidate with `start.ps1 -Model <directory> -Shadow`.

The live development server uses `data/live.db` separately from replay. Run `python -m scripts.shadow_soak` for a 72-hour network-only measurement. Add `--require-sysmon` for full collector qualification. A restart or suspension invalidates that run; the next run starts a new uninterrupted interval. Read `artifacts/shadow-soak.json` for the measured scope and status. Do not launch duplicate monitors writing the same output.

Review real live sessions independently through Operations, including non-alerted events from Traffic. `python -m scripts.release_report` reads live shadow predictions and analyst labels without changing either. Every observed window in a session must be reviewed before that session enters its live metrics. Its minimum support/accuracy thresholds and family checks are explicit; coverage and review selection still require human audit. It never changes `deployment_approved`.

On this machine, standalone Sysmon registration failed. The built-in Windows optional feature subsequently installed successfully and its service runs, but channel access still fails with Windows error 4201. Npcap is working; WMI remains limited. `scripts/install_sysmon.ps1` validates the signature, checks for existing services and saves installer diagnostics. It requires an administrator PowerShell window and refuses to replace an existing Sysmon setup. It prefers the supported built-in Windows feature and never restarts Windows automatically. For older systems, the standalone fallback requires the official package extracted under `data/installers/Sysmon-latest/`. Built-in and standalone installations must not coexist. Repair the Windows event channel before full collector qualification. Built-in setup follows https://learn.microsoft.com/en-us/windows/security/operating-system-security/sysmon/how-to-enable-sysmon. Microsoft documents the installer and manifest options at https://learn.microsoft.com/en-us/sysinternals/downloads/sysmon.
