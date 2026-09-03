# Testing Guide — Checking Out Versions and Working in Parallel

This document explains how to point your local checkout of
`alems-test-framework` at a specific `alems-platform` version, how to
work on your own test-framework feature branch, and how multiple people
can do both of these independently without interfering with each other.

If you haven't run initial setup yet, do that first — see the root
[README.md](../README.md).

---

## 1. The two independent axes

There are two separate things you can check out independently:

1. **Which `alems-platform` version you're testing against** — controlled
   by the submodule pin at `vendor/alems-platform`. This determines what
   platform code and schema the checks run against.
2. **Which `alems-test-framework` branch you're working on** — normal
   git branch, controls which check implementations / config profiles
   you're writing or running.

These are independent. You can be on your own feature branch of
`alems-test-framework` while pinned to the shared baseline platform tag,
or on `main` of `alems-test-framework` while pinned to a newer platform
tag to validate against it, or any other combination.

**Nothing about your local pin or branch affects anyone else** until you
commit and push it. Each person's clone is its own independent working
directory.

---

## 2. Checking out a specific alems-platform tag

To point your local submodule checkout at a specific tag (e.g. to test
against a platform version with a new fix):

```bash
cd vendor/alems-platform
git fetch --tags
git checkout <tag-name>
cd ../..
```

Example — checking out the current shared baseline:

```bash
cd vendor/alems-platform
git checkout v-testframework-baseline-2026-09-02
cd ../..
```

Confirm what you're actually pinned to:

```bash
cd vendor/alems-platform
git describe --tags --always
cd ../..
```

**This checkout is local to your machine** until you `git add
vendor/alems-platform && git commit` from the `alems-test-framework`
repo root. Checking out a different tag to test something does not
change what anyone else sees — the shared pin only changes when someone
commits and pushes that submodule pointer update, deliberately, as its
own reviewed commit (see root README's "How alems-platform is
referenced" section for why this is deliberate and not automatic).

If you just want to look around at what's available:

```bash
cd vendor/alems-platform
git tag -l
git log --oneline -10
cd ../..
```

---

## 3. Checking out a specific alems-platform branch (instead of a tag)

Normally you should pin to a **tag**, not a branch — branches move,
tags don't, and the whole point of pinning is stability (see root
README). But if you specifically need to test against work-in-progress
platform code that hasn't been tagged yet:

```bash
cd vendor/alems-platform
git fetch origin
git checkout origin/<branch-name>
cd ../..
```

This puts you in a detached HEAD pointing at the current tip of that
branch — same non-tracking behavior as a tag checkout, i.e. it won't
auto-follow if that branch gets new commits. Re-run the same command to
pick up newer commits on that branch.

Treat this as a temporary, exploratory state. Before committing any
findings from this checkout, prefer switching back to a real tag once
one exists, so the result is reproducible by others later.

---

## 4. Working on your own alems-test-framework branch

Standard git branch workflow, independent of the platform pin above:

```bash
git checkout -b your-feature-branch
# make changes to checks/, configs/, etc.
git add <files>
git commit -m "..."
git push origin your-feature-branch
```

Open a PR into `main` when ready. If you're working from a fork rather
than a branch in this repo directly, push to your fork and open the PR
from there instead.

---

## 5. Multiple people working in parallel — the actual scenario

Each person clones (or has already cloned) this repo independently.
From that point on, everyone's local checkout — both their
`alems-test-framework` branch and their `vendor/alems-platform` pin —
is completely their own until they push.

**Example: two people, two different needs, at the same time**

- Person A is validating a brand-new platform fix. They check out the
  new (unreleased) platform commit directly in their submodule, run
  checks against it locally, confirm it works, then a maintainer tags
  that commit on `alems-platform` and Person A updates their pin to the
  new tag and commits that pin-bump to `alems-test-framework` as its
  own reviewed change.
- Person B is building a new check type for their HLD. They stay
  pinned to the current shared baseline tag (so their work is being
  developed against a known-stable reference) and work on their own
  feature branch of `alems-test-framework`, unaffected by whatever
  Person A is doing in their own submodule checkout.

Neither person's local state affects the other. The only shared state
is:
- Whatever is committed to `alems-test-framework`'s branches (visible
  to everyone once pushed)
- Whatever tag is currently recorded as the submodule pin in `main`
  (only changes via a deliberate, reviewed pin-bump commit — see
  Section 6)

**In short:** you can freely experiment with different tags/branches of
`alems-platform` locally without any coordination. You only need to
coordinate with others when you're ready to change what `main`'s
recorded pin actually is.

---

## 6. Bumping the shared pin (do this deliberately, rarely)

When the team agrees the shared baseline should move to a newer
`alems-platform` version (e.g. after new fixes have been verified across
all four platforms):

```bash
cd vendor/alems-platform
git fetch --tags
git checkout <new-tag>
cd ../..
git add vendor/alems-platform
git commit -m "Bump alems-platform pin to <new-tag>"
git push
```

This is a real commit others will pull and be affected by — treat it
with the same review care as any other change, and note in the commit
message or PR description what changed on the platform side and why
the bump is happening now (e.g. reference the relevant bug number).

Everyone else picks up the new pin the normal way:

```bash
git pull
git submodule update --init --recursive
```

---

## 7. Quick reference

| I want to...                                    | Command |
|--------------------------------------------------|---------|
| See current pin                                   | `cd vendor/alems-platform && git describe --tags --always` |
| Switch to a different tag locally                 | `cd vendor/alems-platform && git checkout <tag>` |
| List available tags                               | `cd vendor/alems-platform && git tag -l` |
| Test against unreleased platform branch           | `cd vendor/alems-platform && git checkout origin/<branch>` |
| Start my own test-framework feature branch         | `git checkout -b <name>` |
| Confirm my setup still works after switching       | `python3 scripts/verify_setup.py` |
| Make my tag switch the new shared default          | `git add vendor/alems-platform && git commit -m "Bump pin to <tag>"` (then push, with review) |

Always re-run `python3 scripts/verify_setup.py` after switching the
submodule pin, before running any real checks — it confirms the
checkout resolved correctly and the platform's modules and DB path
resolution still import cleanly.
