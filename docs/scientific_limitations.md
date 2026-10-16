# Interpretation and limitations

1. **No direct sensing measurements.** There are no reference-target positions, Doppler errors, AoA errors, range errors, detection rates, or measured sensing age. Ideal `T_SRS/2` is not an empirical sensing metric. This repository must not be described as validating a three-axis sensing–communication–compute Pareto frontier.
2. **Confounded sequential blocks.** SRS period was changed between blocks, not randomized/interleaved within repetitions. Differences in PUSCH SNR/MCS and environmental drift may explain part of the communication variation.
3. **Small sample size.** Three 120-s runs per configuration limit inferential strength. A numeric maximum of a mean (e.g., 10 ms at 40 Mbps) is not proof of statistical superiority or a globally optimal SRS period.
4. **High-load saturation unexplained.** Received throughput at nominal 30/40 Mbps lies near 25–29 Mbps with higher ICMP RTT. Potential limitations include TDD uplink share, MCS scheduling, UE, interface, host processing, or `iperf3` generation. Cause not yet isolated.
5. **SRS CPU attribution.** L1 RX thread includes more than SRS processing; it is inappropriate to call the observed change *direct per-SRS computation time* without profiling.
6. **One static UE and one SRS resource shape.** Radio behavior may differ with mobility, larger UE counts, SRS bandwidth, ports, and actual sensing workload. Constant RI/TPMI only shows no change in recorded feedback, not that SRS was unused.
7. **Nominal overhead assumptions.** A five-slot TDD pattern with 32 UL symbols, and one SRS occasion in each valid period, needs verification in the actual runtime config; SRS ports are not confirmed.
8. **Doppler geometry.** The monostatic expression `lambda/(4*T)` does not generally apply to a direct one-way UE–gNB link. Target sensing geometry must be specified before citing speed limits.
9. **CPU and memory scope.** Process CPU and L1 thread CPU are different metrics; total CPU can exceed 100% on multicore hosts. RSS is not synonymous with physical system-wide memory pressure.
10. **Rebuilds per period.** The compiled binary changed by design (SRS period constant). Preserve source commit, patch, hashes, and build options to rule out additional differences.
