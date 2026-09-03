# configs/

Pinned expected-capability and coverage profiles, one per hardware
fingerprint (e.g. `amd_ryzen_5_3600.yaml`, `gn100_gb10.yaml`,
`intel_i7_1165g7.yaml`, `apple_m1_pro.yaml`).

Format and exact fields are Stephen's HLD/LLD to define — this folder
is scaffolding only. The core requirement (from design discussion,
2026-09-02): these profiles are written once, deliberately, and are
NOT derived from the platform's own capability detector output. They
represent what a human has confirmed a given machine should be able to
measure. Live detector output and live database coverage are compared
against these files; a mismatch is a reported regression.
