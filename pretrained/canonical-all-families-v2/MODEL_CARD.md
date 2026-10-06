# Traffic candidate model card

Version: `canonical-all-families-v2`. **Unapproved; shadow evaluation only.**

## Artifact and intended use

A 200-tree random forest using thirteen `flow-window-v1` numeric features from the shared live/replay state machine. Fit with the pinned dependencies. Compressed joblib artifact: load only a trusted copy with the matching manifest checksum. The package contains no raw traffic or local process data.

## Data and partitioning

Five CICIDS2017 captures and independent flow labels from the pinned public mirror revision recorded in the full report. Capture and label hashes were rechecked. Minute-level uncertainty is reported; ambiguous/unmatched joins are excluded. A deterministic one-in-ten complete-session sample was selected without labels.

All segments with the same bidirectional capture/endpoint tuple are connected. Shared feature vectors also connect their entire sessions. Three stratified folds train the model, one chooses the threshold under a 0.1% validation false-positive budget, and the untouched fifth fold evaluates it. Each connected component belongs to one partition. Captures are shared across partitions: this is an in-dataset test, not independent-network accuracy.

## Held-out results

65,473 windows: precision 99.6318%, attack recall 95.5774%, benign false-positive rate 0.0390%. Threshold 0.96154294. Scores are classifier outputs, not calibrated confidence.

| Family | Test windows | Flagged | Recall / flag rate |
| --- | ---: | ---: | ---: |
| BENIGN | 58,961 | 23 | 0.04% |
| Bot | 42 | 4 | 9.52% |
| DDoS | 685 | 678 | 98.98% |
| DoS GoldenEye | 233 | 172 | 73.82% |
| DoS Hulk | 1,993 | 1,963 | 98.49% |
| DoS Slowhttptest | 26 | 20 | 76.92% |
| DoS slowloris | 40 | 28 | 70.00% |
| FTP-Patator | 136 | 106 | 77.94% |
| Infiltration | 1 | 0 | 0.00% |
| PortScan | 3,183 | 3,117 | 97.93% |
| SSH-Patator | 158 | 131 | 82.91% |
| Web Attack – Brute Force | 13 | 5 | 38.46% |
| Web Attack – XSS | 2 | 0 | 0.00% |

## Limits and release requirements

Five captures from one dated laboratory environment; no modern production generalization claim.
Identical features can have conflicting labels; every connected session is kept in one partition.
All-family model uses Friday labels for training; it cannot reuse the strict Friday holdout as its independent test.
Rare family support and minute-level label uncertainty remain visible in counts.
Threshold selected only on validation at a 0.1% benign false-positive budget; test FPR can differ.

The separate strict Friday candidate detected only 35.4% of attacks. That retained report is a generalization stress result, not an independent test of this all-family model, which trains with Friday labels.

Weak or tiny family samples cannot establish reliable coverage. Production requires independent reviewed live accuracy, supported-family scope, full Windows collectors, a 72-hour soak, recovery evidence and independent approval. The manifest remains deployment_approved=false.

[CICIDS2017 publisher](https://www.unb.ca/cic/datasets/ids-2017.html) · [Mirror](https://huggingface.co/datasets/bvsam/cic-ids-2017) · [Full report](report.json)
