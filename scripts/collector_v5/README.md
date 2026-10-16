# SRS synchronized campaign collector v5

This package captures the selected paper metrics without requiring
`nrMAC-stats.log`. OAIBOX dashboard telemetry is preserved as run-scoped JSONL
from MongoDB, while CPU is sampled independently with `pidstat`.

## Metrics

- UE: configured target rate, actual sender rate, delivered throughput, UDP
  loss/jitter, timestamped ICMP RTT and interface counters.
- OAIBOX: whole-process gNB CPU/RSS, per-thread gNB CPU/RSS, host per-core CPU,
  executable/configuration hashes, and raw dashboard telemetry.
- Telemetry target fields: UL MCS, UL BLER, NPRB, HARQ rounds/errors and PUSCH
  SNR.

## Install

Copy the directory to both machines. Then run:

```bash
chmod +x *.sh *.py
```

Run `preflight_oaibox.sh` on OAIBOX before the first pilot. Confirm that the
newest MongoDB documents correspond to the dashboard data.

## Start one synchronized run

Choose a future epoch on either machine:

```bash
START_EPOCH=$(( $(date +%s) + 30 ))
```

For block 1, period 2.5 ms, target 30 Mbps, duration 120 seconds:

OAIBOX:

```bash
./capture_oaibox_v5.sh B01_T2p5_L30 5 2.5 30 "$START_EPOCH" 120 1
```

UE:

```bash
./capture_ue_v5.sh B01_T2p5_L30 5 2.5 30 "$START_EPOCH" 120 1
```

Use the same run name, period, load, epoch, duration and block on both hosts.

## Automated load sequence for one periodicity

After manually installing/restarting the desired gNB binary and attaching the
UE, generate one start epoch at least 90 seconds in the future. Run the OAIBOX
and UE supervisors with the same arguments. They execute the balanced order
R01: 0,10,20,30,40; R02: 20,30,40,0,10; R03: 40,0,10,20,30, using
120-second runs and at least 60 seconds of idle time between runs. A zero-load
run sends no iperf3 traffic; timestamped ICMP probes continue for RTT and
connectivity monitoring.

For the 2.5-ms configuration, for example:

```bash
./run_load_sequence_oaibox_v5.sh T2p5 5 2.5 FIRST_EPOCH 120 60
./run_load_sequence_ue_v5.sh     T2p5 5 2.5 FIRST_EPOCH 120 60
```

Other supported configurations at 30 kHz SCS: `T10 20 10`, `T40 80 40`, `T160 320 160`, and `T1280 2560 1280` (fifth period subject to confirmation). Period changes and UE attachment remain manual.

## Important limitations

This package does not capture complex SRS I/Q/channel estimates. It records MongoDB telemetry, iperf3/ping and CPU measurements. The rotated order is deterministic/counterbalanced, not randomized. MongoDB document IDs are used to bound each run; validate the timestamp semantics and data completeness before relying on run attribution.

## Mandatory pilot validation

After one short run, inspect on OAIBOX:

```bash
RUN=B01_T2p5_L30
DIR="$HOME/srs_campaign_v5/$RUN/oaibox"
cat "$DIR/telemetry_validation_${RUN}.txt"
head -n 20 "$DIR/telemetry_candidates_${RUN}.csv"
```

Do not start the full campaign until every required telemetry field has a
nonzero match count. If a field is zero, the dashboard uses a different
collection/schema or OAI is not exporting it; adjust the collector after
inspecting the three preflight documents.

## Experimental discipline

- If requiring a gNB restart and UE reattachment before every run, perform it externally; the supplied automated sequence scripts do not do this.
- Use prebuilt, hashed binaries; do not rebuild between runs.
- Use identical stabilization and cooldown intervals.
- Keep the complete 120-second run as the replication unit.
- Evaluate 0, 10, 20, 30, and 40 Mbps; do not assume which load is saturated until measurements confirm it.

