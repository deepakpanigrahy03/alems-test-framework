# Writing Checks — Guidance and Example Shape

This is scaffolding guidance, not a fixed spec. The actual config
format and check contract are Stephen's HLD/LLD to define. This
document exists so there's a concrete example to react to, discuss, or
discard — not to pre-decide the design.

## Existing test tooling in alems-platform

A unit-test kit already exists for developers in alems-platform:
`scripts/test_runs_regression_extended.sh`, `scripts/test_provenance.sh`,
and other `scripts/test_*` scripts. These include working patterns for
per-column pass/fail reporting and numeric range validation.

The full testing strategy — unit, system integration (SIT), regression,
and pre-prod tiers, branch structure, and promotion criteria between
them — will be defined separately and provided as a directed structure
to build within. This is not part of Stephen's HLD scope.

## The shape a check probably needs

Based on the design discussion (2026-09-02), a check likely needs to:

1. Load a pinned expected-capability profile for the current machine
   from `configs/` (see `configs/README.md`).
2. Query the live `alems-platform` database for what is actually
   populated right now, using the platform's own DB path resolution
   (`vendor/alems-platform`'s `scripts/tools/path_loader.py`) — never a
   hardcoded path.
3. Compare live coverage against the pinned expectation.
4. Report a pass/fail per the agreed v1 scope: structural and
   data-quality failures only (schema drift, loss of a previously
   populated signal, unexpected NULL coverage, integrity violations).
   Numerical energy-band checks are out of scope for v1.

## Illustrative example (not a real check yet)

A possible config profile, `configs/amd_ryzen_5_3600.yaml`:

```yaml
platform: amd_ryzen_5_3600
table: cpu_samples
expected:
  c1_residency: required
  c2_residency: required
  package_temp: required
  c3_residency: null_expected   # genuinely absent on this hardware
  c6_residency: null_expected
  c7_residency: null_expected
  gpu_rc6: null_expected
  dram_power: null_expected
```

A possible check reading it, `checks/example_coverage_check.py`:

```python
"""
Illustrative only — NOT a real check. Shows the shape a v1 coverage
check might take: load expectation, query real data, compare, report.
Replace/discard once the real config format and check contract land.
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
VENDOR_PLATFORM = REPO_ROOT / "vendor" / "alems-platform"
sys.path.insert(0, str(VENDOR_PLATFORM))

import yaml
import sqlite3
from scripts.tools.path_loader import get_alems_db_path


def load_expected_profile(config_path):
    with open(config_path) as f:
        return yaml.safe_load(f)


def get_live_coverage(db_path, table, columns):
    """For each column, return whether ANY row has a non-NULL value."""
    conn = sqlite3.connect(db_path)
    coverage = {}
    for col in columns:
        cur = conn.execute(f"SELECT COUNT(*) FROM {table} WHERE {col} IS NOT NULL")
        coverage[col] = cur.fetchone()[0] > 0
    conn.close()
    return coverage


def run_check(config_path):
    profile = load_expected_profile(config_path)
    db_path = get_alems_db_path()
    columns = list(profile["expected"].keys())
    live = get_live_coverage(db_path, profile["table"], columns)

    failures = []
    for col, expectation in profile["expected"].items():
        is_populated = live.get(col, False)
        if expectation == "required" and not is_populated:
            failures.append(f"{col}: expected REQUIRED, found NULL for all rows — REGRESSION")
        # 'null_expected' columns are not flagged either way in v1 —
        # they're documented hardware truth, not something to alert on.

    if failures:
        print(f"FAIL ({len(failures)} issue(s)):")
        for f in failures:
            print(f"  - {f}")
        sys.exit(1)
    print(f"PASS: {profile['platform']} / {profile['table']} matches expected profile.")


if __name__ == "__main__":
    run_check(sys.argv[1] if len(sys.argv) > 1 else "configs/amd_ryzen_5_3600.yaml")
```

## What this example deliberately does NOT decide

- Whether `required`/`null_expected` are the right vocabulary, or
  whether more states are needed (e.g. `sometimes_populated`,
  `required_above_version_X`).
- Whether profiles are one-file-per-platform or one-file-per-table, or
  a single combined file.
- How results get reported (stdout, JSON, a dashboard, GitHub Actions
  annotations).
- How CI decides which machine's profile to load (hostname detection?
  explicit `--platform` flag? reading the live `cpu_vendor` from
  `hw_config.json`, carefully — see the note below).

## One design trap worth flagging explicitly

Do not have the check auto-detect which platform profile to load by
asking `alems-platform`'s own hardware detector "what platform am I."
That reintroduces the exact failure this framework exists to prevent —
if platform detection itself is what's broken, the check would load
the wrong (or a self-consistent-but-wrong) profile and could pass
falsely. Prefer an explicit, external identifier for "which pinned
profile applies here" (hostname mapping maintained outside the
detector, or a manually-set config value) so the check's notion of
"which machine is this" cannot be corrupted by the same detection logic
being tested.

## Running the example

```bash
python3 scripts/verify_setup.py   # confirm setup is healthy first
pip install pyyaml               # if not already installed
python3 checks/example_coverage_check.py configs/amd_ryzen_5_3600.yaml
```

Requires a real `experiments.db` with a `cpu_samples` table to exist at
whatever path `get_alems_db_path()` resolves to on this machine.
