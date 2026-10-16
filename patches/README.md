# OAI source patch — not yet imported

SRS periodicity was altered in OAI gNB source and the binary rebuilt for each experimental block. A **verified patch** for the exact campaign OAI base revision is required.

On the original OAIBOX, identify the OAI git checkout and run the following commands in that checkout (review output for secrets before publishing):

```bash
cd /home/user/openairinterface5g
git rev-parse HEAD
git status --short
git diff -- openair2/LAYER2/NR_MAC_gNB/nr_radio_config.c > /tmp/oai_srs_period_patch.diff
sha256sum cmake_targets/ran_build/build/nr-softmodem
```

The source constant reportedly lived in `nr_radio_config.c`, but the exact file location and build executable path must be confirmed for the deployed revision. Ideally record **one patch and one executable SHA256 for each period block** to show no unrelated code changes were introduced.
