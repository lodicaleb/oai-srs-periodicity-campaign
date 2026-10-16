# Measurement protocol

## Main experimental design

1. Configure one SRS periodicity in the OAI gNB source (P = 5, 20, 80, or 2560 slots, corresponding to 2.5, 10, 40, 1280 ms).
2. Rebuild `nr-softmodem` and restart the gNB for the period block; ensure the UE is connected.
3. Within that block, measure offered UDP rates 0, 10, 20, 30, 40 Mbps for three repetitions, using a rotated load order.
4. For each period/load/repetition combination, capture 120 s of UE and OAIBOX metrics with a shared Unix start epoch (machines NTP synchronized).
5. Maintain a nominal idle/cooldown interval of 60 s between runs.
6. Save raw run-scoped logs under a unique run name.
7. Compute run means first; treat the 120-second run, not individual per-second samples, as the independent replication unit.

The experiments were **not interleaved across SRS periods**. Block order is a major design limitation: period effects cannot be cleanly separated from drift in radio conditions or other time-varying effects.

## Run naming

Example: `R01_T10_P20_L20` = repetition 01, period 10 ms / 20 slots, offered load 20 Mbps.

Expected primary 60 runs: periods 2.5, 10, 40, 1280 ms × loads 0, 10, 20, 30, 40 Mbps × reps 1, 2, 3.

An additional 160-ms (320-slot) block has corresponding **15 exploratory runs** and is not part of the 60-run manuscript dataset. Keep those separate until their inclusion is explicitly documented.

## Traffic

- `iperf3` UDP from UE toward OAIBOX.
- UDP datagram payload size: 1200 bytes.
- The nominal zero-load condition has no active `iperf3` UDP stream, but ICMP ping continues.
- Measured receiver throughput should be distinguished from target offered load and sender rate.
- Note that the absence of receiver-reported UDP packet loss does not by itself establish the cause of a throughput plateau.

## What is not yet independently verified

- Precise gNB/RRC/SRS effective configuration and active TDD slot/special-slot symbol pattern.
- 10-ms SRS actual reception timing and missed-occasion count.
- The stable environment and binary identity across rebuilt period blocks.
- Cause of high-load throughput limit at ~25–29 Mbps.
- Direct sensing-estimation error or actual age of CSI as consumed by sensing processing.
