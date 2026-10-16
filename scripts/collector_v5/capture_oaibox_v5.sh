#!/usr/bin/env bash
set -Eeuo pipefail

# Usage:
# capture_oaibox_v5.sh RUN PERIOD_SLOTS PERIOD_MS LOAD_MBPS START_EPOCH DURATION BLOCK

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
# The seventh argument is deliberately reserved for the block number.
BLOCK=$7

ROOT=${ROOT:-"$HOME/srs_campaign_v5"}
OAI_ROOT=${OAI_ROOT:-/home/user/openairinterface5g}
GNB_CONFIG=${GNB_CONFIG:-"$OAI_ROOT/targets/PROJECTS/GENERIC-NR-5GC/CONF/oaibox.yaml"}
TELEMETRY_CONTAINER=${TELEMETRY_CONTAINER:-oaibox-telemetry-repository}
TELEMETRY_DB=${TELEMETRY_DB:-oaibox}
TELEMETRY_COLLECTION=${TELEMETRY_COLLECTION:-gnb_logs}
OUT="$ROOT/$RUN/oaibox"
SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)

mkdir -p "$OUT"
sudo -v

mapfile -t PID_ARRAY < <(pgrep -x nr-softmodem)
if [[ ${#PID_ARRAY[@]} -eq 0 ]]; then
  echo "ERROR: nr-softmodem is not running" >&2
  exit 1
fi

MAIN_PID=$(pgrep -o -x nr-softmodem)
GNB_PIDS=$(IFS=,; echo "${PID_ARRAY[*]}")
RUNNING_EXE=$(sudo readlink -f "/proc/$MAIN_PID/exe")
GNB_CWD=$(sudo readlink -f "/proc/$MAIN_PID/cwd")

sudo docker inspect "$TELEMETRY_CONTAINER" >/dev/null

mongo_eval() {
  local code=$1
  sudo docker exec "$TELEMETRY_CONTAINER" \
    mongosh "$TELEMETRY_DB" --quiet --eval "$code"
}

COLLECTION_OK=$(mongo_eval \
  "print(db.getCollectionNames().includes('$TELEMETRY_COLLECTION'))")
if [[ "$COLLECTION_OK" != *true* ]]; then
  echo "ERROR: MongoDB collection $TELEMETRY_DB.$TELEMETRY_COLLECTION not found" >&2
  exit 1
fi

latest_oid() {
  mongo_eval \
    "const x=db.getCollection('$TELEMETRY_COLLECTION').find().sort({_id:-1}).limit(1).toArray()[0]; if(x) print(x._id.toString());" \
    | tail -n1 | tr -d '\r'
}

EXE_HASH=$(sha256sum "$RUNNING_EXE" | awk '{print $1}')
CONFIG_HASH=$(sha256sum "$GNB_CONFIG" | awk '{print $1}')
GIT_COMMIT=$(git -C "$OAI_ROOT" rev-parse HEAD)

{
  echo "run=$RUN"
  echo "block=$BLOCK"
  echo "period_slots=$PERIOD_SLOTS"
  echo "period_ms=$PERIOD_MS"
  echo "configured_target_rate_mbps=$LOAD_MBPS"
  echo "duration_s=$DURATION"
  echo "scheduled_start_epoch=$START_EPOCH"
  echo "main_gnb_pid=$MAIN_PID"
  echo "gnb_pids=$GNB_PIDS"
  echo "gnb_working_directory=$GNB_CWD"
  echo "running_executable=$RUNNING_EXE"
  echo "executable_sha256=$EXE_HASH"
  echo "configuration_sha256=$CONFIG_HASH"
  echo "git_commit=$GIT_COMMIT"
  echo "telemetry_source=$TELEMETRY_DB.$TELEMETRY_COLLECTION"
  echo "hostname=$(hostname)"
  echo "kernel=$(uname -r)"
} > "$OUT/manifest.txt"

cp "$GNB_CONFIG" "$OUT/oaibox.yaml"

echo "Waiting for epoch $START_EPOCH" | tee "$OUT/capture_control.log"
while (( $(date +%s) < START_EPOCH )); do sleep 0.1; done

# Store the last document that existed at the start. All later documents up to
# END_OID belong to this run window.
START_OID=$(latest_oid)
echo "mongo_start_oid=$START_OID" >> "$OUT/manifest.txt"
date +%s.%N | tee "$OUT/start_epoch.txt" | tee -a "$OUT/capture_control.log"

pidstat -H -h -u -r -p "$GNB_PIDS" 1 "$DURATION" \
  > "$OUT/gnb_process_${RUN}.log" &
PROCESS_MONITOR_PID=$!

pidstat -H -h -t -u -r -p "$GNB_PIDS" 1 "$DURATION" \
  > "$OUT/gnb_threads_${RUN}.log" &
THREAD_MONITOR_PID=$!

sar -P ALL -u 1 "$DURATION" \
  > "$OUT/host_cpu_${RUN}.log" &
HOST_CPU_PID=$!

set +e
wait "$PROCESS_MONITOR_PID"; PROCESS_RC=$?
wait "$THREAD_MONITOR_PID"; THREAD_RC=$?
wait "$HOST_CPU_PID"; HOST_CPU_RC=$?
set -e

END_OID=$(latest_oid)
echo "mongo_end_oid=$END_OID" >> "$OUT/manifest.txt"

MONGO_QUERY="db.getCollection('$TELEMETRY_COLLECTION').find({_id:{\$gt:ObjectId('$START_OID'),\$lte:ObjectId('$END_OID')}}).sort({_id:1}).forEach(x=>print(EJSON.stringify(x)))"
mongo_eval "$MONGO_QUERY" > "$OUT/gnb_telemetry_${RUN}.jsonl"

date +%s.%N | tee "$OUT/end_epoch.txt" | tee -a "$OUT/capture_control.log"

{
  echo "process_pidstat_exit_code=$PROCESS_RC"
  echo "thread_pidstat_exit_code=$THREAD_RC"
  echo "host_cpu_exit_code=$HOST_CPU_RC"
} > "$OUT/monitor_exit_codes.txt"

python3 "$SCRIPT_DIR/inspect_telemetry.py" \
  "$OUT/gnb_telemetry_${RUN}.jsonl" \
  "$OUT/telemetry_candidates_${RUN}.csv" \
  "$OUT/telemetry_validation_${RUN}.txt"

if [[ ! -s "$OUT/gnb_telemetry_${RUN}.jsonl" ]]; then
  echo "ERROR: no telemetry documents were captured" >&2
  exit 1
fi

touch "$OUT/CAPTURE_COMPLETE"
echo "SUCCESS: $RUN OAIBOX capture completed" | tee -a "$OUT/capture_control.log"

