# Metric definitions and statistical reporting

| Metric | Instrument / source | Notes |
| --- | --- | --- |
| Offered load (Mbps) | `iperf3` UE command | Target; not guaranteed achieved |
| Sender rate (Mbps) | `iperf3` sender output | Generated application traffic |
| Receiver throughput (Mbps) | Receiver summary in `iperf3` output | **Read** `docs/data_provenance.md` about precision-preserving sender-rate proxy in the audit script |
| ICMP RTT (ms) | Ping replies / summary | RTT during concurrent UDP load; includes queueing and scheduling effects |
| gNB CPU (%) | `pidstat` per-process | 100% roughly one fully busy logical CPU; >100% possible for multithreaded process |
| L1 RX CPU (%) | `pidstat` thread samples | **Not** SRS-only processing |
| gNB RSS (MiB) | `pidstat` | May count shared resident pages more than once if multiple processes summed |
| PUSCH SNR (dB) | OAI/Mongo telemetry | Channel covariate; block-associated |
| Mean UL MCS | OAI/Mongo telemetry | Not a throughput-isolated treatment variable |
| HARQ retransmission ratio | `(round1 + round2 + round3)/round0 × 100%` | Run-level counter deltas; not directly equal to OAI's smoothed BLER |
| Reported BLER | OAI link adaptation telemetry | Exponentially smoothed indicator; inspect source for precise formulation |
| Nominal SRS observations/sec | `1000 / T_SRS_ms` | Analytical, not observed reception count |
| Ideal mean age | `T_SRS / 2` | Idealized sampling age, excludes losses and processing |

## Statistical unit

Each 120-second run is a replicate. For each period/load pair, report the mean, **sample** standard deviation (`ddof=1`), and optionally Student-t 95% CI with `n=3`, `df=2`, `t*=4.30265`. Confidence intervals rely on assumptions that cannot be evaluated reliably at n=3 and do not account for time/confounding between separate period blocks.

Overlapping confidence intervals do not, by themselves, prove no statistically meaningful difference. However, data from noninterleaved blocks must not be used to make a causal claim about throughput, CPU, or latency changes induced solely by SRS periodicity.
