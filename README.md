# OAI 5G NR SRS Periodicity Measurement Campaign

Experimental documentation, run-level summaries, and audit utilities for an **over-the-air OpenAirInterface (OAI) 5G NR uplink SRS periodicity study**. This repository is designed to make the measurement campaign traceable and to support independent examination of the reported computation and communication metrics.

> **Study status:** Documentation and extracted summaries are provided; original host/UE measurement logs, the actual OAI source patch, and a verified runtime configuration **have not yet been imported**. The repository does not provide an end-to-end independent reproduction of the over-the-air results, and it **does not contain direct sensing-accuracy measurements**.

## Experimental setup

- **RAN:** OAI standalone NR gNB on an OAIBOX, with 5G core connectivity.
- **Radio:** USRP B210; band n77; carrier around **4.008 GHz**; 20 MHz nominal channel bandwidth; 30 kHz subcarrier spacing; TDD; reported 2x2 RF configuration.
- **UE:** Quectel RM520N-GL; UDP uplink traffic generated from the UE using `iperf3`.
- **SRS periods analyzed in the paper:** 5, 20, 80, and 2560 slots = **2.5, 10, 40, and 1280 ms** (0.5 ms/slot).
- **Traffic:** 0, 10, 20, 30, 40 Mbps offered; UDP datagrams of 1200 bytes; zero-load runs have no active `iperf3` flow.
- **Replications:** 3 runs per SRS period / load pair; **60 paper runs**, 120 s per run and nominal 60 s idle interval between runs.
- **Additional exploratory block:** 320 slots = **160 ms**; **15 additional runs** (3 per load), not included in paper's 60-run analysis.
- **Ordering:** SRS periods were tested in separate sequential blocks, not randomized or interleaved; traffic loads were rotated across repetitions.
- **Synchronization:** UE and OAIBOX used NTP and a common future Unix start epoch.

See [experiment setup](docs/testbed.md), [protocol](docs/protocol.md), and [run inventory](metadata/run_manifest.csv).

## Repository structure

```text
oai-srs-periodicity-campaign/
├── README.md
├── docs/
│   ├── testbed.md
│   ├── protocol.md
│   ├── measurement_definitions.md
│   ├── data_provenance.md
│   ├── scientific_limitations.md
│   ├── verification_checklist.md
│   └── publishing_checklist.md
├── metadata/
│   └── run_manifest.csv         # 75 campaign runs, labels primary/exploratory
├── data/
│   ├── extracted/              # run-level extracted CSVs, including exploratory P320
│   ├── summaries/              # grouped CSVs, including exploratory P320
│   └── raw/                    # raw OAIBOX and UE logs NOT yet provided
├── scripts/
│   ├── validate_campaign.py    # stdlib-only CSV completeness/integrity checks
│   ├── plot_summary.py         # summary plots (requires matplotlib)
│   ├── audit_srs_v6_oaibox.py  # original supplied audit utility
│   ├── audit_srs_v6_ue.py      # original supplied audit utility
│   └── collector_v5/          # historical collector source (NOT verified v6 provenance)
├── configs/README.md          # actual runtime config and OAI version still needed
├── patches/README.md          # actual SRS-period modification patch still needed
└── results/figures/           # generated plots
```

## Quick start

Python 3.9+ is sufficient to validate the CSVs:

```bash
python3 scripts/validate_campaign.py
```

To reproduce illustrative summary plots from the *included extracted summary tables*:

```bash
python3 -m pip install -r requirements-plot.txt
python3 scripts/plot_summary.py
```

Plots based on summary tables are **not** an independent re-analysis of absent raw logs. Figures are written to `results/figures/`.

### Independent audits from original raw logs

The supplied OAI/UE audit utilities can recompute selected results if the raw logs are present on the two original machines or copied locally with the expected directory structure:

```bash
python3 scripts/audit_srs_v6_oaibox.py --base /path/to/srs_campaign_v6 --output /tmp/oai_audit
python3 scripts/audit_srs_v6_ue.py     --base /path/to/srs_campaign_v6 --output /tmp/ue_audit
```

Audit scripts inspect files read-only, but generate CSVs in `--output`. Inspect the scripts and directory layout before running on a different campaign version. The script's expected naming format is `R01_T10_P20_L20`, with `R` = repetition, `T` = millisecond period, `P` = slot period, and `L` = load in Mbps.

## Key observations (descriptive, not causal)

- The **L1 RX thread's mean CPU utilization** at 0 Mbps is approximately **7.00%** for 2.5 ms, versus **2.24%** for 1280 ms.
- At 40 Mbps offered load, the corresponding values are approximately **12.35%** and **7.64%**.
- At 40 Mbps, the 10-ms configuration has the **highest observed mean** received throughput (**28.80 Mbps**) and lowest observed mean ICMP RTT (**49.79 ms**), but its radio conditions were also more favorable and the mean throughput of the 1280-ms group was similar (**28.63 Mbps**). **Do not infer optimality or statistical superiority from these sample means.**
- The SRS period defines **nominal observation rate**, not a measured sensing-accuracy or actual CSI-age outcome.

See [scientific limitations](docs/scientific_limitations.md) and [measurement definitions](docs/measurement_definitions.md).

## Source and provenance

The `data/extracted/` and `data/summaries/` CSV files are copies of previously generated campaign analysis artifacts, **not simulated or invented measurements**. The supplied `audit_srs_v6_*.py` scripts were originally written to audit raw logs. The historic `collector_v5/` scripts are retained as **historical source only**, not asserted to be the exact v6 collectors. Raw data and the OAI source patch must still be added before claiming full experimental reproducibility. See [data provenance](docs/data_provenance.md).

## Sharing and citation

Review `docs/publishing_checklist.md` before changing a GitHub repository from private to public. Do not publish network access credentials, IMSI/ICCID, personal identifiers, internal IPs that are sensitive, private keys, unredacted configuration, or confidential raw traces. Add the actual OAI source revision and a LICENSE only after the owner chooses an appropriate license.
