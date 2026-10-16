# Verification checklist — do not mark complete without evidence

| Check | Status | Required evidence |
| --- | --- | --- |
| Inventory all 60 primary runs | **Included** | `metadata/run_manifest.csv` and CSV consistency validator |
| Preserve 15 exploratory P320 runs separately | **Included** | `paper_inclusion` field in manifest |
| Verify raw log checksums | **Outstanding** | Import raw logs, SHA256 manifest |
| Verify runtime SRS period of 2.5 ms | **Reported** | Timestamp median around 2.498 ms; raw event counts needed |
| Verify runtime SRS period of 10 ms | **Outstanding** | Actual SRS reception timestamps, missed-event stats |
| Verify runtime SRS period of 40 ms | **Reported** | Timestamp median around 39.996 ms; raw event counts needed |
| Verify runtime SRS period of 1280 ms | **Reported** | Timestamp median around 1279.993 ms; raw event counts needed |
| Confirm exact TDD pattern | **Outstanding** | gNB config, RRC settings, UL/DL slot/symbol map |
| Confirm configured SRS antenna ports | **Outstanding** | ASN.1 SRS resource config and UE capability/logs |
| Preserve exact OAI git commit | **Outstanding** | `git rev-parse HEAD` |
| Preserve period patch per build | **Outstanding** | `git diff`, source files, compiler flags |
| Preserve executable hashes | **Outstanding** | SHA256 of each period-specific `nr-softmodem` |
| Investigate high-load throughput cap | **Outstanding** | Link budget, UL symbols, transport blocks, sender/receiver traces |
| Measure SRS-specific CPU | **Outstanding** | perf/timing instrumentation around SRS routines |
| Controlled comparisons across periods | **Outstanding** | Interleaved runs, >=10 reps where practical |
| Measured sensing performance | **Not performed** | Ground-truth channel/doppler/range or detection metric |
| Check whether raw data can be shared publicly | **Outstanding** | Consent, redaction and institution review |
