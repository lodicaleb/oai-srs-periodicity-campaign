#!/usr/bin/env bash
set -Eeuo pipefail

# Run the balanced 15-run load sequence for one already-attached UE.
# Usage: run_load_sequence_ue_v5.sh LABEL PERIOD_SLOTS PERIOD_MS FIRST_START_EPOCH [DURATION] [COOLDOWN]

if (( $# < 4 || $# > 6 )); then
  echo "Usage: $0 LABEL PERIOD_SLOTS PERIOD_MS FIRST_START_EPOCH [DURATION=120] [COOLDOWN=60]" >&2
  exit 2
fi

LABEL=$1
PERIOD_SLOTS=$2
PERIOD_MS=$3
FIRST_START_EPOCH=$4
DURATION=${5:-120}
COOLDOWN=${6:-60}

ROOT=${ROOT:-"$HOME/srs_campaign_v5"}
CAPTURE_SCRIPT="$ROOT/capture_ue_v5.sh"
RUN_SPACING=$((DURATION + COOLDOWN + 2))

# R01: 0,10,20,30,40; R02: 20,30,40,0,10; R03: 40,0,10,20,30.
LOADS=(0 10 20 30 40 20 30 40 0 10 40 0 10 20 30)
REPETITIONS=(1 1 1 1 1 2 2 2 2 2 3 3 3 3 3)
TOTAL_RUNS=${#LOADS[@]}

[[ -x "$CAPTURE_SCRIPT" ]] || {
  echo "ERROR: missing executable $CAPTURE_SCRIPT" >&2
  exit 1
}

if (( FIRST_START_EPOCH < $(date +%s) + 20 )); then
  echo "ERROR: FIRST_START_EPOCH must be at least 20 seconds in the future" >&2
  exit 1
fi

PLAN="$ROOT/sequence_${LABEL}_ue.csv"
printf 'sequence_index,run,repetition,load_mbps,start_epoch,duration_s,cooldown_s\n' > "$PLAN"

for index in "${!LOADS[@]}"; do
  repetition=${REPETITIONS[$index]}
  load=${LOADS[$index]}
  printf -v repetition_text '%02d' "$repetition"
  run="R${repetition_text}_${LABEL}_L${load}"
  start_epoch=$((FIRST_START_EPOCH + index * RUN_SPACING))

  if [[ -e "$ROOT/$run/ue/CAPTURE_COMPLETE" ]]; then
    echo "ERROR: completed UE output already exists for $run" >&2
    exit 1
  fi

  printf '%d,%s,%d,%d,%d,%d,%d\n' \
    "$((index + 1))" "$run" "$repetition" "$load" \
    "$start_epoch" "$DURATION" "$COOLDOWN" >> "$PLAN"
done

echo "UE sequence plan:"
column -s, -t "$PLAN" 2>/dev/null || cat "$PLAN"

for index in "${!LOADS[@]}"; do
  repetition=${REPETITIONS[$index]}
  load=${LOADS[$index]}
  printf -v repetition_text '%02d' "$repetition"
  run="R${repetition_text}_${LABEL}_L${load}"
  start_epoch=$((FIRST_START_EPOCH + index * RUN_SPACING))

  echo "[$((index + 1))/$TOTAL_RUNS] UE $run scheduled for $start_epoch"
  "$CAPTURE_SCRIPT" \
    "$run" "$PERIOD_SLOTS" "$PERIOD_MS" "$load" \
    "$start_epoch" "$DURATION" "$repetition"
done

touch "$ROOT/SEQUENCE_${LABEL}_UE_COMPLETE"
echo "SUCCESS: UE $TOTAL_RUNS-run sequence completed for $LABEL"
