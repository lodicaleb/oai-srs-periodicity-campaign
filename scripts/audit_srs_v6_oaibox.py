#!/usr/bin/env python3
"""Independently recompute CPU and RSS from all 60 OAIBOX raw pidstat logs.

Uses only Python standard library; read-only for raw experiment files.
Creates 2 CSVs in the optional output directory.
"""
from pathlib import Path
import argparse
import csv
import math
import re
import statistics

PERIODS = (('T2p5_P5', 2.5), ('T10_P20', 10), ('T40_P80', 40), ('T1280_P2560', 1280))
LOADS = (0, 10, 20, 30, 40)
T95_2 = 4.302652729911275


def read_pidstat(path, thread=False):
    """Read pidstat -r -u or -t -r -u logs, tolerant of repeated headers."""
    if not path.exists():
        return [], 'MISSING'
    rows = []
    header = None
    for line in path.read_text(errors='replace').splitlines():
        line = line.strip()
        if line.startswith('# Time ') or line.startswith('#\tTime\t'):
            header = line.lstrip('#').strip().split()
            continue
        if not line or not line[0].isdigit() or header is None:
            continue
        parts = line.split(maxsplit=len(header) - 1)
        if len(parts) != len(header):
            continue
        record = dict(zip(header, parts))
        try:
            ts = int(record['Time'])
            cpu = float(record['%CPU'])
            rss_kib = float(record['RSS'])
        except (ValueError, KeyError):
            continue
        if ts < 1_000_000_000:
            continue  # reject HH:MM:SS log variants
        record['_time'] = ts
        record['_cpu'] = cpu
        record['_rss_kib'] = rss_kib
        rows.append(record)
    return rows, ('OK' if rows else 'NO_NUMERIC_ROWS')


def mean_sd_ci(vals):
    if len(vals) != 3:
        return {'n': len(vals), 'mean': None, 'sd': None, 'ci_lo': None, 'ci_hi': None}
    m = statistics.mean(vals)
    sd = statistics.stdev(vals)
    e = T95_2 * sd / math.sqrt(3)
    return {'n': 3, 'mean': m, 'sd': sd, 'ci_lo': m-e, 'ci_hi': m+e}


def grouping(rows, name, kind):
    groups = {}
    for r in rows:
        if kind == 'process':
            if not r.get('PID', '').isdigit() or r.get('Command', '') != 'nr-softmodem':
                continue
            key = (r['_time'], r['PID'])
        else:
            if not r.get('TID', '').isdigit():
                continue  # ignore TGID summary to avoid double-counting
            cmd = r.get('Command', '').lower().lstrip('|_').strip()
            if not re.search(r'l1[_\s-]*rx|l1[_\s-]*receive|rx[_\s-]*l1', cmd):
                continue
            key = (r['_time'], r['TID'])
        # Last instance wins if pidstat repeats a timestamp/PID pair.
        groups[key] = r
    by_sec = {}
    for (ts, _), row in groups.items():
        by_sec.setdefault(ts, []).append(row)
    return by_sec


def get_existing(path):
    if not path.exists():
        return {}
    with path.open(newline='') as f:
        return {r['run']: r for r in csv.DictReader(f)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--base', type=Path, default=Path.home() / 'srs_campaign_v6')
    ap.add_argument('--output', type=Path)
    args = ap.parse_args()
    base = args.base.expanduser()
    out = (args.output or (base / 'analysis_audit_oaibox')).expanduser()
    out.mkdir(parents=True, exist_ok=True)
    old_proc = get_existing(base / 'analysis_final' / 'cpu_memory_per_run.csv')
    old_thread = get_existing(base / 'analysis_final' / 'thread_cpu_per_run.csv')
    metrics = []
    for period_key, period in PERIODS:
        for load in LOADS:
            for rep in (1, 2, 3):
                run = f'R{rep:02d}_{period_key}_L{load}'
                root = base / run / 'oaibox'
                proc, proc_status = read_pidstat(root / f'gnb_process_{run}.log')
                threads, thread_status = read_pidstat(root / f'gnb_threads_{run}.log', thread=True)
                p_secs = grouping(proc, run, 'process')
                t_secs = grouping(threads, run, 'thread')
                cpu = [sum(r['_cpu'] for r in p_secs[t]) for t in sorted(p_secs)]
                # RSS is summed per separate process; NOT de-duplicated physical memory.
                rss = [sum(r['_rss_kib'] for r in p_secs[t])/1024 for t in sorted(p_secs)]
                l1 = [sum(r['_cpu'] for r in t_secs[t]) for t in sorted(t_secs)]
                pold, told = old_proc.get(run, {}), old_thread.get(run, {})
                def cmp(value, old, key):
                    try:
                        return value - float(old[key]) if value is not None else None
                    except (ValueError, KeyError, TypeError):
                        return None
                m_cpu = statistics.mean(cpu) if cpu else None
                m_rss = statistics.mean(rss) if rss else None
                m_l1 = statistics.mean(l1) if l1 else None
                metrics.append(dict(run=run, period_ms=period, load_mbps=load, repetition=rep,
                    process_log_status=proc_status, thread_log_status=thread_status,
                    process_samples=len(cpu), l1_rx_samples=len(l1),
                    gnb_cpu_mean_pct=m_cpu, gnb_cpu_peak_pct=max(cpu) if cpu else None,
                    gnb_rss_mean_mib=m_rss, gnb_rss_peak_mib=max(rss) if rss else None,
                    l1_rx_cpu_mean_pct=m_l1,
                    old_gnb_cpu_mean=pold.get('gnb_cpu_mean_pct'),
                    old_gnb_rss_mean=pold.get('gnb_rss_mean_mib'),
                    old_l1_rx_cpu_mean=told.get('l1_rx_cpu_pct'),
                    delta_gnb_cpu=cmp(m_cpu,pold,'gnb_cpu_mean_pct'),
                    delta_rss=cmp(m_rss,pold,'gnb_rss_mean_mib'),
                    delta_l1=cmp(m_l1,told,'l1_rx_cpu_pct')))
    with (out/'oaibox_metrics_per_run.csv').open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(metrics[0])); w.writeheader(); w.writerows(metrics)
    sums = []
    for pk, period in PERIODS:
        for load in LOADS:
            group = [r for r in metrics if r['period_ms']==period and r['load_mbps']==load]
            summary = dict(period_ms=period, load_mbps=load)
            for key,prefix in [('gnb_cpu_mean_pct','gnb_cpu_'),('gnb_rss_mean_mib','gnb_rss_'),('l1_rx_cpu_mean_pct','l1_rx_')]:
                results = mean_sd_ci([r[key] for r in group if r[key] is not None])
                summary.update({prefix+k:v for k,v in results.items()})
            sums.append(summary)
    with (out/'oaibox_metrics_summary.csv').open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(sums[0])); w.writeheader(); w.writerows(sums)
    print('Run audit: 60 expected OAIBOX runs')
    warnings = 0
    for r in metrics:
        flags = []
        if r['process_samples'] != 120: flags.append(f"PROCESS_SAMPLES={r['process_samples']}")
        if r['l1_rx_samples'] != 120: flags.append(f"L1_RX_SAMPLES={r['l1_rx_samples']}")
        for col in ('delta_gnb_cpu','delta_rss','delta_l1'):
            v = r[col]
            if v is not None and abs(v)>0.02: flags.append(f'{col}={v:+.4f}')
        if flags:
            warnings+=1
            print('CHECK', r['run'], '; '.join(flags))
    print('\n  load period  gNB CPU: mean ± SD [95% CI]     L1 RX CPU: mean ± SD [95% CI]')
    for r in sorted(sums, key=lambda s:(s['load_mbps'],s['period_ms'])):
        def desc(p):
            return ('INCOMPLETE' if r[p+'mean'] is None else
                   f"{r[p+'mean']:.2f}±{r[p+'sd']:.2f} [{r[p+'ci_lo']:.2f},{r[p+'ci_hi']:.2f}]")
        print(f"  {r['load_mbps']:>4} {r['period_ms']:>6g}  {desc('gnb_cpu_'):<33} {desc('l1_rx_')}")
    print('\nRuns with warnings:', warnings)
    print('Created:', out/'oaibox_metrics_per_run.csv')
    print('Created:', out/'oaibox_metrics_summary.csv')
    print('RSS is sum of per-process resident sets; may double count shared pages.')
    print('pidstat %CPU=100 corresponds approximately to one logical core, NOT all 32 CPUs.')

if __name__ == '__main__':
    main()
