#!/usr/bin/env python3
"""Replot selected published metrics from available extracted CSV summaries.

These plots are derived from grouped CSVs; the original raw captures are absent.
"""
import csv
from pathlib import Path
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/figures'
OUT.mkdir(parents=True,exist_ok=True)
PERIODS=['P5','P20','P80','P2560']
LABELS=['2.5 ms','10 ms','40 ms','1280 ms']

def rows(file):
    with (ROOT/'data/summaries'/file).open(newline='') as f:return list(csv.DictReader(f))

def plot_series(source,mean,sd,ylabel,output,loads,reference=False):
    dataset=rows(source)
    fig,ax=plt.subplots(figsize=(7,4.6))
    for period,label in zip(PERIODS,LABELS):
        group=[r for r in dataset if r['period']==period and int(r['load_mbps']) in loads]
        group.sort(key=lambda r:int(r['load_mbps']))
        x=[int(r['load_mbps']) for r in group]
        ax.errorbar(x,[float(r[mean]) for r in group],yerr=[float(r[sd]) for r in group],label=label,marker='o',capsize=2)
    if reference:ax.plot(loads,loads,linestyle='--',label='Offered rate',alpha=.6)
    ax.set(xlabel='Offered UDP load (Mbps)',ylabel=ylabel)
    ax.set_xticks(loads)
    ax.grid(alpha=.25)
    ax.legend()
    fig.tight_layout()
    fig.savefig(OUT/output,dpi=180)
    plt.close(fig)
    print('wrote',OUT/output)

plot_series('thread_cpu_summary.csv','l1_rx_cpu_pct_mean','l1_rx_cpu_pct_sd','L1 RX CPU utilization (% of one core)','l1_rx_cpu_summary.png',[0,10,20,30,40])
plot_series('udp_summary.csv','receiver_mbps_mean','receiver_mbps_sd','Received UDP throughput (Mbps)','udp_throughput_summary.png',[10,20,30,40],reference=True)
