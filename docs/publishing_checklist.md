# Repository publishing checklist

- [ ] Choose GitHub name and owner, initialize private repository first.
- [ ] Review all CSVs and scripts for secrets or sensitive identifiers.
- [ ] Add verified OAI repository URL, exact git commit, configuration, patch and `nr-softmodem` SHA256 per SRS-period build.
- [ ] Add actual run-scoped raw log archive to an approved storage location or a versioned release; do not commit sensitive raw captures by default.
- [ ] Add checksum manifest (`sha256sum`) and describe file-level provenance.
- [ ] Confirm the 10-ms SRS reception event interval and timestamp method.
- [ ] Confirm TDD symbol counts / actual SRS ports and recompute any theoretical overhead if necessary.
- [ ] Verify the `iperf3` throughput-extraction logic and precision caveat.
- [ ] Document exact source of RTT per-run estimates and attach run-level RTT CSV when available.
- [ ] Choose a license after checking institutional and third-party intellectual property requirements (none has been assigned here).
- [ ] Replace draft paper placeholders and cite the repository only when a public URL is available.
- [ ] Tag a release matching the final accepted paper revision and publish a DOI (e.g., Zenodo) if appropriate.
