# Data provenance and status

## Included files

The data files below are copies of analysis artifacts supplied during the research workflow (not synthetic placeholders):

- `data/extracted/cpu_memory_per_run.csv` — 75 runs, including 15 exploratory 160-ms runs.
- `data/extracted/thread_cpu_per_run.csv` — 75 runs, including exploratory runs.
- `data/extracted/udp_per_run.csv` — 60 nonzero-load runs across five periods (12 are exploratory P320; zero-load UDP runs intentionally absent).
- `data/extracted/radio_metrics_per_run.csv` — 75 runs, including exploratory runs.
- `data/summaries/*` — group means/SDs corresponding to those extracted data.

The paper's primary analyzed design consists of **60 runs**: 4 SRS periods × 5 offered loads × 3 repetitions. Some uploaded summary files instead contain **25 conditions**, including an additional P320 = 160-ms block. **Filter to P5, P20, P80, and P2560 to match the paper.**

## Raw logs not included

The raw UE/host logs from `/home/user/srs_campaign_v6` are **not in this repository**. These are required for fully independent verification of the run-level extracts. The scripts `audit_srs_v6_oaibox.py` and `audit_srs_v6_ue.py` may help recompute metrics when originals are obtained.

Typical expected layout:

```text
srs_campaign_v6/
└── R01_T10_P20_L20/
    ├── oaibox/
    │   ├── gnb_process_R01_T10_P20_L20.log
    │   └── gnb_threads_R01_T10_P20_L20.log
    └── ue/
        ├── iperf3_R01_T10_P20_L20.json
        └── ping_R01_T10_P20_L20.log
```

This is an **expected example layout** based on the audit scripts, not an attestation that these exact files have been uploaded. Actual captures may contain more files.

## `iperf3` precision caveat

The supplied UE audit script sometimes reports a high-precision sender-rate **proxy** for receiver throughput when the server text reports zero packet loss and matching total packets, because the receiver textual throughput is rounded. This is **not an independently measured high-precision receiver bitrate**. Retain the script's `throughput_evidence` field, disclose this rule, and investigate if a 1–3 Mbps claim depends on precision.

## Historical collector scripts

The repository stores a `collector_v5/` snapshot from a supplied campaign-collector archive for preservation. It demonstrates the intended run capture workflow and names. Its identity with the actual final **v6** campaign scripts has **not** been established. Do not claim the historical scripts were the exact data-collection software until checked.

## Data screening before public release

Even aggregated data should be reviewed for accidental exposure. Original logs may contain UE or subscriber identifiers, full network addresses, access credentials, or identifiable timestamps. Review and redact before committing any raw material.
