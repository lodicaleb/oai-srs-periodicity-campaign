# Testbed architecture and radio settings

## System

- OAI 5G NR standalone gNB and 5G core running on OAIBOX.
- USRP B210 RF front end.
- Quectel RM520N-GL physical 5G UE.
- Uplink application data generated from UE with `iperf3`; OAIBOX-side `iperf3` server.
- ICMP ping and CPU/process/thread/host telemetry collected during the campaign.

| Parameter | Reported value | Evidence / status |
| --- | --- | --- |
| NR band | n77 | Paper's experimental configuration |
| Carrier frequency | 4.008 GHz | Paper's experimental configuration |
| Nominal channel bandwidth | 20 MHz | Paper's experimental configuration |
| UL BWP | 51 PRBs | OAI config-derived, paper |
| Subcarrier spacing | 30 kHz | Paper |
| Slot duration | 0.5 ms | From SCS |
| Duplex | TDD | Paper |
| RF setup | 2x2 | Does **not** establish SRS antenna port count |
| SRS resource | 48 PRBs, comb 2, one OFDM symbol | Derived from inspected OAI config/source; recheck on actual build |
| SRS slot symbol | Second-to-last | Derived from inspected OAI source; runtime validation pending |
| SRS hopping | Disabled | Derived from inspected OAI source; runtime validation pending |
| Actual SRS ports | **Not verified** | Check RRC SRS config and logs |
| UL/DL TDD pattern | **Not independently verified** | Must inspect active gNB config/RRC |
| OAIBOX OAI commit and hashes | **Not provided** | Record commit and binary hash |

## Signal path

```
Quectel UE  -- NR uplink -->  USRP B210  -- I/Q -->  OAI gNB  -->  5G Core / UPF  -->  iperf3 receiver
    |                                             |
    +---- UDP sender + ICMP RTT -----------------+---- CPU / RSS / telemetry / SRS timestamps
```

The UE-to-gNB radio link is **not** a monostatic sensing experiment. An unambiguous velocity-aliasing bound requires the sensing geometry and estimated Doppler model to be specified; this campaign does not directly validate moving-target speed or sensing accuracy.
