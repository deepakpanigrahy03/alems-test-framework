# TESTING_STRATEGY.md
# A-LEMS Test Framework — Testing Strategy
# Repository: alems-test-framework
# Status: ACTIVE — read before writing any check, config, or CI spec.

---

## 1. Scope

This document defines the testing strategy for the A-LEMS platform.
It covers branch discipline, test tier definitions, CI wiring, gating rules,
and the relationship between this framework and the compliance rule set in
`alems-platform/COMPLIANCE.md`.

All contributors to `alems-platform` and `alems-test-framework` are bound by
the process defined here.

---

## 2. Branch model

```
dev/<contributor>
      |
      | PR to integration
      | GATE: Tier A passes (GitHub Actions, automatic)
      | GATE: one reviewer approval (required)
      |
  integration
      |
      | PR to pre-prod
      | GATE: Tier B passes on all target machines (manual, posted as PR comment)
      | GATE: Tier C passes across all machines (manual, posted as PR comment)
      |
  pre-prod   <--- alems-test-framework submodule pinned here
      |
      | Promotion gate: one successful full experiment run per machine,
      | test_exp_integrity.py --latest exits 0 on all machines
      |
    main   <--- paper-citable, permanent record
```

### Constraints

- No contributor pushes directly to `integration`, `pre-prod`, or `main`.
  Branch protection is enforced on GitHub for all three.
- `main` is never tested by this framework.
  It has already passed every gate. It is the output of the process.
- The submodule pin in `alems-test-framework` advances when a new `pre-prod`
  tag is cut, not when `main` advances.
- External contributors (fork-based) open PRs from their fork to
  `alems-test-framework integration`. The same tier gates apply.

### Promotion from pre-prod to main

Promotion is run-based, not time-based.
One successful full experiment run on each target machine, with
`test_exp_integrity.py --latest` passing on all, is the gate.
Calendar soak periods are not used.

---

## 3. Tier definitions

### Tier A — Logic tests

**Purpose**: validate code logic independently of physical hardware and live databases.
Inputs are mocked: turbostat output, sysfs paths, DB query results.

**Execution**: `pytest checks/tier_a/ -v`
Runs on any machine including cloud CI (GitHub Actions).
Fast. No physical hardware required.

**Gate**: PR from `dev/<contributor>` to `integration`.
Must pass before any human reviewer looks at the code.

**Location in this repo**: `checks/tier_a/`

**Fixture convention**: all shared mocks and fixtures live in `checks/tier_a/conftest.py`.
Individual test files import from there; they do not define their own hardware mocks.

**Design rule**: a Tier A test that mocks away the exact hardware interaction it claims
to test is not a test. Mocking is for isolation of the unit under test, not for
avoiding the hard case. If the function under test calls a hardware reader,
mock the reader's output, not the function itself.

**Existing prior art in alems-platform/scripts/**:
`test_sysfs_cpu_reader.py` is Tier A in structure and should be the reference
pattern for new Tier A checks. It requires no DB, no root, no hardware.

**Current gaps**:
- No pytest infrastructure exists yet.
- No None-path tests exist for any function that can return None.
- No column-mapping validation tests exist.
These are the first deliverables for this tier.

---

### Tier B — Live hardware capability tests

**Purpose**: validate that each physical machine's hardware environment matches
its declared capability profile. These checks cannot be mocked. They run on
the physical machine against live hardware.

**Execution**: `python checks/tier_b/<check>.py --machine <machine-id>`
Run on each target machine. Results posted manually as PR comments.

**Gate**: PR from `integration` to `pre-prod`.
All target machines must post a passing result before merge is approved.

**Location in this repo**: `checks/tier_b/` (checks), `configs/machines/` (profiles)

**Profile format**: one YAML file per machine in `configs/machines/`.
Each profile declares what that machine is expected to be capable of:
turbostat column set, RAPL availability, DCGM availability, sysfs paths present.

**Critical design rule**: a Tier B check must never use `alems-platform`'s own
hardware/vendor detector to decide which profile to load.
If the detector is what is broken, the check would silently load the wrong profile
and pass falsely.
Machine identity is always passed explicitly by the operator via `--machine`.
The check never infers it.

**Existing prior art in alems-platform/scripts/**:
`test_provenance.sh`, `test_exp_integrity.py`, `test_runs_regression.sh`, and
`test_runs_regression_extended.sh` are Tier B in nature (require real DB, real runs).
They remain in `alems-platform/scripts/` as developer tools.
Tier B in `alems-test-framework` focuses on capability profile validation,
not statistical regression (that is Tier C).

**Current gaps**:
- No machine capability profiles exist.
- No Tier B checks exist.
Writing all machine profiles is the first Tier B deliverable.
Writing `check_turbostat_columns.py` is the first Tier B check.

---

### Tier C — Cross-platform consistency tests

**Purpose**: after Tier B passes on all machines individually, confirm that the
platform behaves consistently across them at a structural level.
Not identical values. Structural consistency: same schema version, same non-null
coverage on columns that must never be null, same provenance binding count shape.

**Execution**: run after all Tier B results are posted for a given PR.
Results posted manually as PR comments alongside Tier B results.

**Gate**: same PR as Tier B (integration to pre-prod).

**Location in this repo**: `checks/tier_c/`

**Existing prior art**:
`test_runs_regression_extended.sh` implements `check_range()`, `check_gt()`,
and `check_eq()` patterns that are further along than current Tier C scope.
Review that script before designing new Tier C numeric checks.

**Current gaps**: nothing in Tier C exists. This is v2 scope.
Do not begin Tier C work until Tier A and Tier B are committed and verified
on all target machines.

---

### Tier D — Environmental health checks

**Purpose**: catch hardware environment drift that is unrelated to any code change.
Turbostat version change. Kernel update dropping MSR permissions.
DCGM version change. sysfs path restructure.
These are not triggered by PRs. They run on a schedule.

**Execution**: cron job on each physical machine, daily.
`python checks/tier_d/health_check.py --machine <machine-id>`
Output written to `reports/health/<machine-id>/<date>.log`.
Failure writes an error-level log entry. Alerting mechanism is log-based
for now; push notification is a future iteration.

**Gate**: none. Tier D is not a branch gate.
It is an independent monitoring layer that operates continuously.
A Tier D alert means: investigate the machine's environment before the
next integration-to-pre-prod cycle runs Tier B.

**Location in this repo**: `checks/tier_d/`

**Current gaps**: nothing exists. Scaffold `health_check.py` and cron
setup documentation in `doc/TESTING_GUIDE.md` as part of the initial
framework build.

---

## 4. Existing alems-platform scripts — tier placement

| Script | Tier | Keep location | Notes |
|---|---|---|---|
| `test_sysfs_cpu_reader.py` | A | alems-platform/scripts/ | Reference pattern for tier_a/ pytest checks. |
| `test_exp_integrity.py` | B | alems-platform/scripts/ | Post-experiment, requires real DB and real runs. |
| `test_provenance.sh` | B | alems-platform/scripts/ | MPC compliance gate; run after any provenance-touching change. |
| `test_runs_regression.sh` | B/C | alems-platform/scripts/ | Statistical baseline on runs table. |
| `test_runs_regression_extended.sh` | B/C | alems-platform/scripts/ | 110-column numeric band validation. Prior art for Tier C numeric checks. |

These scripts remain in `alems-platform/scripts/`. They are not migrated into
`alems-test-framework`. The test framework adds structure and hardware-profile
validation on top of what these scripts already cover.

---

## 5. GitHub Actions — Tier A wiring

```yaml
# .github/workflows/tier_a.yml
name: Tier A — Logic Tests

on:
  pull_request:
    branches: [integration]

jobs:
  tier-a:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          submodules: true
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install -r requirements.txt
      - run: pytest checks/tier_a/ -v --tb=short
```

This workflow is a required check on the `integration` branch.
PRs cannot merge until it passes. No exceptions.

Tier B and Tier C cannot run in GitHub Actions. They require physical hardware.
Automation of Tier B/C via SSH dispatch is deferred to a future iteration.
The process for now: run manually on each machine, post result as a PR comment.

---

## 6. Relationship to COMPLIANCE.md

`COMPLIANCE.md` in `alems-platform` defines invariants the code must maintain.
This document defines how violations of those invariants are detected.
They are separate, cross-referencing concerns. Neither is a subset of the other.

The following rule family is added to `COMPLIANCE.md`:

**TS-1**: Every new hardware column mapping added to any config file must have
a corresponding Tier B capability profile entry in `configs/machines/` for every
machine that uses that mapping.
A PR to `integration` is blocked until all profile entries are present and
committed to `alems-test-framework`.

**TS-2**: Every function that can legitimately return `None` must have a Tier A
test covering the None-path at every call site.
A PR to `integration` is blocked until the test exists and passes in CI.

**TS-3**: Tier A must pass in GitHub Actions before any PR receives a human review.
Reviewer time is not spent on code that fails automated checks.

**TS-4**: Tier B and Tier C results for all target machines must be posted as PR
comments before any `integration`-to-`pre-prod` merge is approved.
Comment format: machine ID, pass/fail, timestamp, log tail on failure.

**TS-5**: Promotion from `pre-prod` to `main` requires one successful full
experiment run on each target machine, with `test_exp_integrity.py --latest`
returning exit 0 on all.

---

## 7. Build priority for this framework

The following is the sequenced build order. Do not start a later item until
the earlier one is committed and verified.

1. `checks/tier_a/conftest.py` — shared fixtures: mock turbostat output,
   mock sysfs paths, mock DB cursor. Everything else in tier_a/ imports from here.

2. `checks/tier_a/test_none_path.py` — covers every function in alems-platform
   that can return None, at every call site. Parameterized.

3. `checks/tier_a/test_column_mapping.py` — validates that column mapping logic
   raises a named error on an unrecognized column header, rather than silently
   producing NULL output.

4. `configs/machines/<machine-id>.yaml` — one profile per target machine.
   All four machines. Do not write the Tier B check until the profile format is
   decided here, not the other way around.

5. `checks/tier_b/check_turbostat_columns.py` — takes `--machine <id>`,
   reads live turbostat headers, diffs against profile. This is the highest-value
   check not covered anywhere in the current tooling.

6. `.github/workflows/tier_a.yml` — as specified in section 5.

7. `checks/tier_d/health_check.py` — skeleton. Logs machine environment snapshot
   (turbostat version, kernel version, DCGM version, key sysfs paths present).
   Cron setup documented in `doc/TESTING_GUIDE.md`.

Items 1 through 7 are v1 scope.
Tier C, numeric band validation, and CI automation for Tier B/C are v2 scope.

---

## 8. Out of scope for this document

- Config profile YAML schema: decided during item 4 above, documented separately.
- Tier D alerting beyond log files: future iteration.
- Numeric energy band validation in alems-test-framework: deferred to v2.
  `test_runs_regression_extended.sh` covers this for now.
- CI automation for Tier B/C: deferred. Manual PR comment process for now.
- Any work in alems-platform directly: that repository has its own development
  process. This document covers alems-test-framework only.
