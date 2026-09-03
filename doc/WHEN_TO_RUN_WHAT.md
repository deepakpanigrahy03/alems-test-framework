# WHEN_TO_RUN_WHAT.md
# Location: alems-test-framework/doc/WHEN_TO_RUN_WHAT.md

---

## When to run what

| When | What to run | Where | How |
|------|------------|-------|-----|
| Before committing any code | Tier B1 hardware checks | Your physical machine | `alems-git b1 --machine <hostname>` |
| Before opening a PR | Tier A logic tests | Your machine | `pytest checks/tier_a/ -v` |
| When PR is opened | Tier A | GitHub Actions (automatic) | Nothing — CI runs it |
| When PR lands in integration | Tier B1 + Tier C | All four machines | `alems-git b1 --machine <hostname>` on each, then `python checks/tier_c/cross_check.py` |
| Daily, on a schedule | Tier D health check | Each machine via cron | Automatic — see `checks/tier_d/cron_template.sh` |

---

## What each tier checks

| Tier | Checks | Needs hardware |
|------|--------|---------------|
| A | Code logic — None paths, column mapping, path resolution | No |
| B1 | Live hardware vs pinned profile — turbostat columns, sysfs paths, RAPL, DCGM | Yes |
| C | Cross-platform consistency — same schema, same non-null columns across all machines | Yes (all four) |
| D | Environment drift — turbostat version, kernel version, sysfs path changes | Yes |

---

## GitHub Actions writes what

Tier A only. Runs automatically on every PR to main. No setup needed.

You write the Tier A tests. CI runs them. You never configure CI manually.

---

## What you write (Stephen's scope)

```
checks/tier_a/          ← Tier A tests (pytest, no hardware)
checks/tier_b1/         ← Tier B1 checks (live hardware)
checks/tier_c/          ← Tier C cross-platform diff
checks/tier_d/          ← Tier D health check
configs/machines/       ← one YAML profile per machine
lib/                    ← shared libraries used by all checks
```

Read WRITING_CHECKS.md for how to write each one.
Read BUILD_PLAN.md for the order to write them.
