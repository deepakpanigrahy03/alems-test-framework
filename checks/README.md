# checks/

Regression check implementations. Each check reads a config profile
from `configs/`, queries the live alems-platform database (via the
pinned submodule's `path_loader.py`), and reports pass/fail per the
v1 scope agreed 2026-09-02: structural and data-quality failures only
(schema drift, loss of a previously-populated signal, unexpected NULL
coverage, integrity violations). Numerical energy-band checks are
deferred to a later version.

Scaffolding only — implementation is Stephen's HLD/LLD.
