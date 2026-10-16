#!/usr/bin/env python3
import json
import re
import sys
from pathlib import Path

directory = Path(sys.argv[1])
run = sys.argv[2]
load = int(sys.argv[3])

print(f"configured_target_rate_mbps={load}")

if load > 0:
    path = directory / f"iperf3_{run}.json"
    try:
        data = json.loads(path.read_text())
        end = data.get("end", {})
        sent = end.get("sum_sent", end.get("sum", {}))
        received = end.get("sum_received", end.get("sum", {}))
        print(f"actual_sender_mbps={sent.get('bits_per_second', 0) / 1e6:.9f}")
        print(f"receiver_delivered_mbps={received.get('bits_per_second', 0) / 1e6:.9f}")
        print(f"udp_jitter_ms={received.get('jitter_ms', float('nan'))}")
        print(f"udp_lost_packets={received.get('lost_packets', 'NA')}")
        print(f"udp_total_packets={received.get('packets', 'NA')}")
        print(f"udp_loss_percent={received.get('lost_percent', 'NA')}")
    except Exception as exc:
        print(f"iperf_parse_error={exc}")

ping_text = (directory / f"ping_{run}.log").read_text(errors="replace")
loss = re.search(r"([0-9.]+)% packet loss", ping_text)
rtt = re.search(r"rtt min/avg/max/mdev = ([^/]+)/([^/]+)/([^/]+)/([^ ]+)", ping_text)
print(f"icmp_loss_percent={loss.group(1) if loss else 'NA'}")
if rtt:
    print(f"rtt_min_ms={rtt.group(1)}")
    print(f"rtt_mean_ms={rtt.group(2)}")
    print(f"rtt_max_ms={rtt.group(3)}")
    print(f"rtt_mdev_ms={rtt.group(4)}")
else:
    print("rtt_mean_ms=NA")

