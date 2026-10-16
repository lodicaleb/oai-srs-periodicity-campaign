#!/usr/bin/env python3
"""Read-only audit of the 60 UE-side runs in srs_campaign_v6.

Produces per-run and grouped summaries under analysis_audit_ue.
Never changes source files. Requires only the Python standard library.
"""
import argparse
import csv
import json
import math
import re
import statistics
from pathlib import Path

PERIODS = [('T2p5_P5', '2.5'), ('T10_P20', '10'), ('T40_P80', '40'), ('T1280_P2560', '1280')]
LOADS = [0, 10, 20, 30, 40]
T_95_DF2 = 4.302652729911275

# Values printed in the current manuscript; comparison only, never used as data.
PAPER = {
    (0,'2.5'):(None,19.27), (0,'10'):(None,19.30), (0,'40'):(None,19.23), (0,'1280'):(None,19.24),
    (10,'2.5'):(10.00,11.32), (10,'10'):(10.00,10.40), (10,'40'):(10.00,12.64), (10,'1280'):(10.00,13.63),
    (20,'2.5'):(20.00,10.35), (20,'10'):(20.00,11.14), (20,'40'):(20.00,9.62), (20,'1280'):(20.00,11.07),
    (30,'2.5'):(25.87,55.05), (30,'10'):(28.60,50.13), (30,'40'):(27.50,50.19), (30,'1280'):(28.10,50.15),
    (40,'2.5'):(25.63,54.95), (40,'10'):(28.80,49.79), (40,'40'):(27.50,52.17), (40,'1280'):(28.63,49.97),
}

PING_REPLY = re.compile(r'\btime\s*[=<]\s*([0-9]+(?:\.[0-9]+)?)\s*ms\b', re.I)
PING_SUMMARY = re.compile(r'(?:rtt|round-trip)\s+min/avg/max/(?:mdev|stddev)\s*=\s*[0-9.]+/([0-9.]+)/', re.I)
# iperf3 UDP server output ending in "... Mbits/sec ... 0/340997 (0%) receiver".
SERVER_LOSS = re.compile(r'(?P<lost>\d+)\s*/\s*(?P<total>\d+)\s*\([^)]*\)\s*receiver\s*$', re.I)
SERVER_RATE = re.compile(r'(?P<rate>[0-9]+(?:\.[0-9]+)?)\s*(?P<unit>[KMG])bits/sec', re.I)


def mean_stats(nums):
    if len(nums) != 3:
        return {'n':len(nums), 'mean':None, 'sd':None, 'ci_low':None, 'ci_high':None}
    mean = statistics.mean(nums)
    sd = statistics.stdev(nums)
    margin = T_95_DF2 * sd / math.sqrt(3)
    return {'n':3, 'mean':mean, 'sd':sd, 'ci_low':mean-margin, 'ci_high':mean+margin}


def parse_ping(path):
    if not path.exists():
        return None, 0, 'PING_FILE_MISSING'
    text = path.read_text(encoding='utf-8', errors='replace')
    replies = [float(x) for x in PING_REPLY.findall(text)]
    if replies:
        return statistics.mean(replies), len(replies), 'ping_reply_samples'
    match = PING_SUMMARY.search(text)
    if match:
        return float(match.group(1)), 0, 'ping_summary_avg_only'
    return None, 0, 'PING_NO_RTT_FOUND'


def parse_iperf(path):
    if not path.exists():
        return dict(throughput=None, sender=None, server=None, lost=None, total=None,
                    status='IPERF_FILE_MISSING')
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, ValueError) as exc:
        return dict(throughput=None, sender=None, server=None, lost=None, total=None,
                    status=f'IPERF_JSON_ERROR:{type(exc).__name__}')
    if data.get('error'):
        return dict(throughput=None, sender=None, server=None, lost=None, total=None,
                    status='IPERF_REPORTED_ERROR')
    end = data.get('end') or {}
    # Some iperf3 JSON formats have an exact receiver summary.
    direct = end.get('sum_received')
    if isinstance(direct, dict) and isinstance(direct.get('bits_per_second'), (int,float)):
        rate = direct['bits_per_second'] / 1e6
        return dict(throughput=rate, sender=None, server=rate,
                    lost=direct.get('lost_packets'), total=direct.get('packets'),
                    status='EXACT_RECEIVER_SUMMARY')
    summary = end.get('sum') or {}
    sender_bps = summary.get('bits_per_second')
    sender = (sender_bps / 1e6) if isinstance(sender_bps,(int,float)) else None
    server_text = data.get('server_output_text') or ''
    if not isinstance(server_text, str):
        server_text = ''
    receiver_lines = [line for line in server_text.splitlines() if line.strip().lower().endswith('receiver')]
    if not receiver_lines:
        return dict(throughput=None, sender=sender, server=None, lost=None, total=None,
                    status='SERVER_RECEIVER_SUMMARY_MISSING')
    last = receiver_lines[-1]
    loss_match = SERVER_LOSS.search(last)
    rate_match = SERVER_RATE.search(last)
    if not loss_match or not rate_match:
        return dict(throughput=None, sender=sender, server=None, lost=None, total=None,
                    status='SERVER_SUMMARY_UNPARSEABLE')
    lost, total = int(loss_match.group('lost')), int(loss_match.group('total'))
    unit_scale = {'K':0.001, 'M':1.0, 'G':1000.0}
    server = float(rate_match.group('rate')) * unit_scale[rate_match.group('unit').upper()]
    sender_packets = summary.get('packets')
    if lost == 0 and sender is not None and sender_packets == total:
        # Precision-preserving proxy, not a directly measured exact receiver bitrate.
        throughput = sender
        status = 'SERVER_ZERO_LOSS_PACKET_MATCH_SENDER_RATE_PROXY'
    else:
        # Server text is generally rounded to 0.1 Mbps; retain actual receiver rate.
        throughput = server
        status = 'RECEIVER_ROUNDED_SERVER_TEXT'
    return dict(throughput=throughput, sender=sender, server=server,
                lost=lost, total=total, status=status)


def fmt(x):
    return '' if x is None else f'{x:.6f}'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--base', type=Path, default=Path.home() / 'srs_campaign_v6')
    parser.add_argument('--output', type=Path, default=None)
    args = parser.parse_args()
    base = args.base.expanduser()
    out = (args.output or (base / 'analysis_audit_ue')).expanduser()
    out.mkdir(parents=True, exist_ok=True)

    per_run = []
    for period_key, period in PERIODS:
        for load in LOADS:
            for rep in (1,2,3):
                run = f'R{rep:02d}_{period_key}_L{load}'
                ue = base / run / 'ue'
                ip = parse_iperf(ue / f'iperf3_{run}.json') if load else dict(
                    throughput=None, sender=None, server=None, lost=None, total=None,
                    status='NO_IPERF_EXPECTED_LOAD0')
                rtt, count, rtt_source = parse_ping(ue / f'ping_{run}.log')
                per_run.append(dict(run=run, period_ms=period, load_mbps=load, repetition=rep,
                                    ue_dir_exists=ue.is_dir(), throughput_mbps=ip['throughput'],
                                    sender_mbps=ip['sender'], server_reported_mbps=ip['server'],
                                    server_lost_packets=ip['lost'], server_total_packets=ip['total'],
                                    throughput_evidence=ip['status'], rtt_mean_ms=rtt,
                                    ping_reply_samples=count, rtt_source=rtt_source))

    run_cols = list(per_run[0])
    path = out / 'ue_metrics_per_run.csv'
    with path.open('w', newline='') as file:
        wr = csv.DictWriter(file, fieldnames=run_cols)
        wr.writeheader(); wr.writerows(per_run)

    summaries = []
    for period_key, period in PERIODS:
        for load in LOADS:
            rows = [r for r in per_run if r['period_ms']==period and r['load_mbps']==load]
            throughputs = [r['throughput_mbps'] for r in rows if r['throughput_mbps'] is not None]
            rtts = [r['rtt_mean_ms'] for r in rows if r['rtt_mean_ms'] is not None]
            tp_stat = mean_stats(throughputs) if load else mean_stats([])
            rtt_stat = mean_stats(rtts)
            paper_tp, paper_rtt = PAPER[(load, period)]
            summaries.append(dict(period_ms=period, load_mbps=load,
                    tp_n=tp_stat['n'], throughput_mean=tp_stat['mean'], throughput_sd=tp_stat['sd'],
                    throughput_ci_lo=tp_stat['ci_low'], throughput_ci_hi=tp_stat['ci_high'],
                    rtt_n=rtt_stat['n'], rtt_mean=rtt_stat['mean'], rtt_sd=rtt_stat['sd'],
                    rtt_ci_lo=rtt_stat['ci_low'], rtt_ci_hi=rtt_stat['ci_high'],
                    paper_throughput=paper_tp, paper_rtt=paper_rtt,
                    delta_tp_vs_paper=tp_stat['mean']-paper_tp if paper_tp is not None and tp_stat['mean'] is not None else None,
                    delta_rtt_vs_paper=rtt_stat['mean']-paper_rtt if rtt_stat['mean'] is not None else None))

    summary_path = out / 'ue_metrics_summary.csv'
    with summary_path.open('w', newline='') as file:
        wr = csv.DictWriter(file, fieldnames=list(summaries[0]))
        wr.writeheader(); wr.writerows(summaries)

    print(f'Examined {len(per_run)} runs in {base}')
    print('\nLoad  Period  TP mean±SD [CI] (Mbps)                RTT mean±SD [CI] (ms)            Differences vs paper')
    for r in sorted(summaries, key=lambda x:(x['load_mbps'],float(x['period_ms']))):
        def txt(prefix):
            mean,sd,lo,hi = [r.get(prefix + z) for z in ('mean','sd','ci_lo','ci_hi')]
            return 'INCOMPLETE' if mean is None else f'{mean:6.2f}±{sd:4.2f} [{lo:6.2f},{hi:6.2f}]'
        dt = r['delta_tp_vs_paper']; dr = r['delta_rtt_vs_paper']
        flagged = []
        if r['load_mbps'] and r['tp_n']!=3: flagged.append(f"TP n={r['tp_n']}")
        if r['rtt_n']!=3: flagged.append(f"RTT n={r['rtt_n']}")
        if dt is not None and abs(dt)>=0.015: flagged.append(f'TP delta={dt:+.2f}')
        if dr is not None and abs(dr)>=0.015: flagged.append(f'RTT delta={dr:+.2f}')
        print(f"{r['load_mbps']:>4}  {r['period_ms']:>5}  {txt('throughput_'):<38} {txt('rtt_'):<35} {'; '.join(flagged)}")
    issues = [r for r in per_run if (r['load_mbps'] and r['throughput_evidence'] != 'SERVER_ZERO_LOSS_PACKET_MATCH_SENDER_RATE_PROXY' and r['throughput_evidence'] != 'EXACT_RECEIVER_SUMMARY')
              or r['rtt_mean_ms'] is None]
    print(f'\nRuns requiring inspection: {len(issues)}')
    for row in issues[:25]:
        print(f"  {row['run']}: {row['throughput_evidence']}; {row['rtt_source']}")
    if len(issues)>25: print(f'  ... and {len(issues)-25} more (see CSV)')
    print('\nFiles created:')
    print(' ',path)
    print(' ',summary_path)
    print('\nNOTE: throughput labeled SERVER_ZERO_LOSS_PACKET_MATCH_SENDER_RATE_PROXY')
    print('uses high-precision sender rate only when server confirms equal UDP')
    print('packet counts and zero loss; server textual rate is rounded.')

if __name__ == '__main__':
    main()
