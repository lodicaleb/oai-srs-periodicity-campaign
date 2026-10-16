#!/usr/bin/env bash
set -Eeuo pipefail

CONTAINER=${TELEMETRY_CONTAINER:-oaibox-telemetry-repository}
DB=${TELEMETRY_DB:-oaibox}
COLLECTION=${TELEMETRY_COLLECTION:-gnb_logs}

sudo -v
echo "gNB processes:"
pgrep -a nr-softmodem
echo
echo "Required programs:"
command -v pidstat sar python3 docker
echo
echo "Telemetry collection and newest documents:"
sudo docker exec "$CONTAINER" mongosh "$DB" --quiet --eval \
  "print('count='+db.getCollection('$COLLECTION').countDocuments()); db.getCollection('$COLLECTION').find().sort({_id:-1}).limit(3).forEach(x=>print(EJSON.stringify(x)))"

