# alems-test-framework

Cross-platform hardware capability and coverage regression test framework
for [alems-platform](https://github.com/deepakpanigrahy03/alems-platform).

## Purpose

alems-platform runs on multiple hardware platforms (Intel, AMD, ARM/Grace
GB10, Apple Silicon). Each platform's ability to measure a given signal
(a CPU sample column, a thermal reading, a C-state residency, etc.)
depends on hardware capability detection that can silently regress —
a kernel update, a turbostat version change, a permissions change, or a
code change can cause a signal that used to be measured to quietly stop
being measured, with no error, just a NULL where real data used to be.

This framework exists to catch that class of regression. It does **not**
trust alems-platform's own capability detector as the authority on what
a machine should be able to measure. Instead, each hardware fingerprint
gets a pinned, version-controlled expected capability and coverage
profile, decided once and updated deliberately. Every test run compares
live detector output and live database coverage against that pinned
profile — not against itself. If a signal that was previously available
disappears, that is reported as a regression, not silently accepted as
a new, lower baseline.

## How alems-platform is referenced

alems-platform is included here as a git submodule, pinned to a specific
tag — **not** tracking `main`. This is deliberate: the framework must be
able to test against a known, fixed version of the platform, and must
never silently follow platform changes. If it auto-updated with every
platform commit, it could never catch a regression — it would simply
keep adjusting its expectations to match whatever the platform currently
does, which defeats the purpose of the framework entirely.

Current pin: `v-testframework-baseline-2026-09-02`

To intentionally advance the pin to a newer alems-platform version:

```bash
cd vendor/alems-platform
git fetch --tags
git checkout <new-tag>
cd ../..
git add vendor/alems-platform
git commit -m "Bump alems-platform pin to <new-tag>"
```

Do this deliberately, as its own reviewed commit — never as a side
effect of another change.

## Setup

```bash
git clone --recurse-submodules https://github.com/deepakpanigrahy03/alems-test-framework.git
cd alems-test-framework
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
export PYTHONPATH="$PYTHONPATH:$(pwd)/vendor/alems-platform"
python3 scripts/verify_setup.py
```

If you cloned without `--recurse-submodules`:

```bash
git submodule update --init --recursive
```

`scripts/verify_setup.py` confirms the pinned alems-platform submodule
resolves correctly and that its `core` modules and database path
resolution (`path_loader.py`) are importable — before any real checks
are written against it.

## Important

**Never edit files inside `vendor/alems-platform/`.** It is a pinned
reference checkout, not a working copy. Changes to the platform itself
belong in alems-platform's own repository and review process. Editing
files here will not be reflected upstream, and will be silently
overwritten (or cause confusing merge state) the next time the pin is
updated.

## Documentation

See [doc/TESTING_GUIDE.md](doc/TESTING_GUIDE.md) for how to check out
specific alems-platform tags/branches, work on your own feature branch,
and how multiple people can test in parallel without interfering with
each other.

## Status

Early scaffolding only. HLD in progress — see project tracker for the
current design (pinned per-machine capability/coverage profiles,
config-driven rule definitions, advisory-first CI integration promoted
to blocking once baselines are proven stable across all four platforms).
