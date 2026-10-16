#!/usr/bin/env python3
"""Validate inventory and aggregated campaign CSV data; standard library only.

This checks schema, cardinality, and numeric agreement between per-run values and
summary mean/SD within tolerance. It cannot validate unavailable raw logs.
"""
import csv
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXTRACTED = ROOT / 'data' / 'extracted'
SUMMARIES = ROOT / 'data' / 'summaries'
PERIODS = {'P5':2.5,'P20':10,'P80':40,'P320':160,'P2560':1280}
LOADS = {0,10,20,30,40}

def read(path):
    with open(path, newline='', encoding='utf8') as f:
        return list(csv.DictReader(f))

def run():
    errors=[]
    inventory=read(ROOT/'metadata/run_manifest.csv')
    manifest={r['run_id']:r for r in inventory}
    if len(inventory)!=75 or len(manifest)!=75:errors.append(f'manifest: expected 75 unique rows, got {len(inventory)}/{len(manifest)}')
    if sum(r['paper_inclusion']=='primary' for r in inventory)!=60:errors.append('expected exactly 60 primary runs')
    if sum(r['paper_inclusion']=='exploratory' for r in inventory)!=15:errors.append('expected exactly 15 exploratory runs')

    datasets={}
    for fn,expected in [('cpu_memory_per_run.csv',75),('thread_cpu_per_run.csv',75),('radio_metrics_per_run.csv',75),('udp_per_run.csv',60)]:
        rows=read(EXTRACTED/fn);datasets[fn]=rows
        ids=[r['run'] for r in rows]
        if len(rows)!=expected or len(set(ids))!=expected:errors.append(f'{fn}: expected {expected} unique runs; got {len(rows)}, unique={len(set(ids))}')
        for r in rows:
            if r['run'] not in manifest:errors.append(f'{fn}: unexpected run {r["run"]}')
            if r['period'] not in PERIODS or int(r['load_mbps']) not in LOADS or int(r['repetition']) not in (1,2,3):
                errors.append(f'{fn}: bad period/load/rep for {r["run"]}')
            if fn=='udp_per_run.csv' and int(r['load_mbps'])==0:errors.append('UDP extract unexpectedly has zero-load stream')
    for fn in ['cpu_memory_summary.csv','thread_cpu_summary.csv','radio_metrics_summary.csv','udp_summary.csv']:
        rows=read(SUMMARIES/fn)
        expected=20 if fn=='udp_summary.csv' else 25
        if len(rows)!=expected:errors.append(f'{fn}: expected {expected} groups, got {len(rows)}')
        for r in rows:
            if int(r['runs'])!=3:errors.append(f'{fn}: expected n=3 in {r}')
    # Recompute mean/sd on named matched columns (checks actual numeric consistency).
    pairs=[('thread_cpu_per_run.csv','thread_cpu_summary.csv','l1_rx_cpu_pct','l1_rx_cpu_pct_mean','l1_rx_cpu_pct_sd'),
           ('cpu_memory_per_run.csv','cpu_memory_summary.csv','gnb_cpu_mean_pct','gnb_cpu_mean_pct_mean','gnb_cpu_mean_pct_sd'),
           ('udp_per_run.csv','udp_summary.csv','receiver_mbps','receiver_mbps_mean','receiver_mbps_sd'),
           ('radio_metrics_per_run.csv','radio_metrics_summary.csv','snr_mean_db','snr_mean_db_mean','snr_mean_db_sd')]
    for source,summary,value,mean_col,sd_col in pairs:
        run_rows=datasets[source]
        summaries=read(SUMMARIES/summary)
        for s in summaries:
            vals=[float(r[value]) for r in run_rows if r['period']==s['period'] and r['load_mbps']==s['load_mbps'] and r[value]!='']
            if len(vals)!=3:errors.append(f'{source}: group {s["period"]}/{s["load_mbps"]} n={len(vals)}');continue
            m=statistics.mean(vals);sd=statistics.stdev(vals)
            if abs(m-float(s[mean_col]))>1e-6 or abs(sd-float(s[sd_col]))>1e-6:
                errors.append(f'{summary}: inconsistent {mean_col}/{sd_col}: {s["period"]}/{s["load_mbps"]}')
    for msg in errors[:30]:print('ERROR',msg)
    if len(errors)>30:print(f'... {len(errors)-30} more errors')
    if errors:raise SystemExit(f'FAIL: {len(errors)} issues')
    print('PASS: 75 unique runs in inventory: 60 primary, 15 exploratory')
    print('PASS: expected run-level tables and summary group counts')
    print('PASS: selected reported means/SDs match available per-run extracts')
    print('LIMITATION: raw OAI/UE logs and exact runtime patches not present; this is NOT a raw-data audit')

if __name__=='__main__':run()
