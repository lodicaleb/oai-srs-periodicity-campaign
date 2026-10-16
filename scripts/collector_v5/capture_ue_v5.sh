#!/usr/bin/env bash
set -Eeuo pipefail

# Usage:
# capture_ue_v5.sh RUN PERIOD_SLOTS PERIOD_MS LOAD_MBPS START_EPOCH DURATION BLOCK

if [[ $# -ne 7 ]]; then
  echo "Usage: $0 RUN PERIOD_SLOTS PERIOD_MS LOAD_MBPS START_EPOCH DURATION BLOCK" >&2
  exit 2
fi

RUN=$1
PERIOD_SLOTS=$2
PERIOD_MS=$3
LOAD_MBPS=$4
START_EPOCH=$5
DURATION=$6
BLOCK=$7

ROOT=${ROOT:-"$HOME/srs_campaign_v5"}
SERVER_IP=${SERVER_IP:-172.31.0.1}
SERVER_PORT=${SERVER_PORT:-5201}
UE_IP=${UE_IP:-172.16.0.3}
UE_INTERFACE=${UE_INTERFACE:-wwan0}
OUT="$ROOT/$RUN/ue"
SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)

mkdir -p "$OUT"

ip -br address show "$UE_INTERFACE" > "$OUT/interface_address_before.txt"
ip route get "$SERVER_IP" > "$OUT/route_before.txt"

if ! ping -I "$UE_INTERFACE" -c 1 -W 3 "$SERVER_IP" >/dev/null; then
  echo "ERROR: $SERVER_IP is not reachable through $UE_INTERFACE" >&2
  exit 1
fi

{
  echo "run=$RUN"
  echo "block=$BLOCK"
  echo "period_slots=$PERIOD_SLOTS"
  echo "period_ms=$PERIOD_MS"
  echo "configured_target_rate_mbps=$LOAD_MBPS"
  echo "duration_s=$DURATION"
  echo "scheduled_start_epoch=$START_EPOCH"
  echo "server_ip=$SERVER_IP"
  echo "server_port=$SERVER_PORT"
  echo "ue_ip=$UE_IP"
  echo "ue_interface=$UE_INTERFACE"
  echo "hostname=$(hostname)"
  echo "kernel=$(uname -r)"
} > "$OUT/manifest.txt"

echo "Waiting for epoch $START_EPOCH" | tee "$OUT/capture_control.log"
while (( $(date +%s) < START_EPOCH )); do sleep 0.1; done

date +%s.%N | tee "$OUT/start_epoch.txt" | tee -a "$OUT/capture_control.log"
ip -s -j link show dev "$UE_INTERFACE" > "$OUT/interface_counters_start.json"

ping -I "$UE_INTERFACE" -D -i 0.2 -s 120 -w "$DURATION" "$SERVER_IP" \
  > "$OUT/ping_${RUN}.log" 2> "$OUT/ping_${RUN}.err" &
PING_PID=$!

IPERF_RC=NA
if (( LOAD_MBPS > 0 )); then
  set +e
  iperf3 -c "$SERVER_IP" -p "$SERVER_PORT" -B "$UE_IP" \
    -u -b "${LOAD_MBPS}M" -l 1200 -t "$DURATION" -i 1 \
    -J --get-server-output \
    > "$OUT/iperf3_${RUN}.json" 2> "$OUT/iperf3_${RUN}.err"
  IPERF_RC=$?
  set -e
else
  sleep "$DURATION"
fi

set +e
wait "$PING_PID"; PING_RC=$?
set -e

ip -s -j link show dev "$UE_INTERFACE" > "$OUT/interface_counters_end.json"
date +%s.%N | tee "$OUT/end_epoch.txt" | tee -a "$OUT/capture_control.log"

{
  echo "iperf3_exit_code=$IPERF_RC"
  echo "ping_exit_code=$PING_RC"
} > "$OUT/traffic_exit_codes.txt"

python3 "$SCRIPT_DIR/summarize_ue.py" "$OUT" "$RUN" "$LOAD_MBPS" \
  > "$OUT/ue_summary_${RUN}.txt"

if [[ "$PING_RC" -ne 0 ]]; then
  echo "ERROR: ping failed" >&2
  exit 1
fi
if [[ "$IPERF_RC" != NA && "$IPERF_RC" -ne 0 ]]; then
  echo "ERROR: iperf3 failed" >&2
  exit 1
fi

touch "$OUT/CAPTURE_COMPLETE"
echo "SUCCESS: $RUN UE capture completed" | tee -a "$OUT/capture_control.log"

