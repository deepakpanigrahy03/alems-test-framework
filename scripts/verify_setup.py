#!/usr/bin/env python3
"""
verify_setup.py — setup verification and pin/status inspection for
alems-test-framework. Run the full check after cloning, after every
deliberate pin bump, and any time you switch your local submodule
checkout to a different tag or branch (see doc/TESTING_GUIDE.md).

This tool never modifies anything inside vendor/alems-platform/. It
only reads/imports from it.

Usage:
    python3 scripts/verify_setup.py                 # full setup verification
    python3 scripts/verify_setup.py --status         # current pin only
    python3 scripts/verify_setup.py --list-tags      # all available alems-platform tags
    python3 scripts/verify_setup.py --where          # resolved filesystem paths
    python3 scripts/verify_setup.py --help           # this message
"""

import sys
import os
import subprocess
import argparse
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
VENDOR_PLATFORM = REPO_ROOT / "vendor" / "alems-platform"


def _run(args, cwd=VENDOR_PLATFORM):
    """Run a git command in the vendor checkout, return stdout or None."""
    try:
        result = subprocess.run(
            args, cwd=cwd, capture_output=True, text=True, timeout=15,
        )
        return result.stdout.strip() if result.returncode == 0 else None
    except Exception:
        return None


def get_pin_description():
    """
    Returns (ref, kind) describing what vendor/alems-platform is
    currently checked out to: an exact tag, a branch tip (detached),
    or something else — so it's always clear what platform version is
    being tested against.
    """
    if not VENDOR_PLATFORM.exists():
        return None, "MISSING — submodule not checked out"

    exact_tag = _run(["git", "describe", "--tags", "--exact-match"])
    if exact_tag:
        return exact_tag, "tag (exact)"

    commit = _run(["git", "describe", "--tags", "--always"]) or "unknown"
    branch = _run(["git", "rev-parse", "--abbrev-ref", "HEAD"])

    if branch and branch != "HEAD":
        return commit, f"branch tip ({branch}, not pinned to a tag)"
    return commit, "detached, not exactly on a tag (commit-ish checkout)"


def cmd_status():
    """Prints just the current pin info, no import/DB checks."""
    print("=" * 60)
    print("Current alems-platform pin")
    print("=" * 60)
    ref, kind = get_pin_description()
    if ref is None:
        print(f"STATUS: {kind}")
    else:
        print(f"Checked out: {ref}")
        print(f"Kind:        {kind}")
    print("=" * 60)


def cmd_list_tags():
    """Lists every tag available in the alems-platform remote."""
    print("=" * 60)
    print("Available alems-platform tags")
    print("=" * 60)
    if not VENDOR_PLATFORM.exists():
        print("MISSING — submodule not checked out. Run:")
        print("  git submodule update --init --recursive")
        return
    _run(["git", "fetch", "--tags"])
    tags_output = _run(["git", "tag", "-l", "--sort=-creatordate"])
    if not tags_output:
        print("No tags found (or fetch failed — check network access).")
        return
    tags = tags_output.splitlines()
    current_ref, _ = get_pin_description()
    for t in tags:
        marker = "  <-- currently checked out" if t == current_ref else ""
        print(f"  {t}{marker}")
    print("=" * 60)
    print(f"{len(tags)} tag(s). To switch:")
    print("  cd vendor/alems-platform && git checkout <tag> && cd ../..")
    print("  python3 scripts/verify_setup.py   # re-verify after switching")


def cmd_where():
    """Shows resolved filesystem paths — this repo, the submodule, and
    the actual alems-platform database this checkout points to."""
    print("=" * 60)
    print("Resolved paths")
    print("=" * 60)
    print(f"alems-test-framework root:  {REPO_ROOT}")
    print(f"vendor/alems-platform:      {VENDOR_PLATFORM}")
    print(f"  exists:                   {VENDOR_PLATFORM.exists()}")

    if VENDOR_PLATFORM.exists():
        sys.path.insert(0, str(VENDOR_PLATFORM))
        try:
            from scripts.tools.path_loader import get_alems_db_path
            db_path = get_alems_db_path()
            print(f"Resolved DB path:           {db_path}")
            print(f"  exists on this machine:   {Path(db_path).exists()}")
        except Exception as e:
            print(f"Could not resolve DB path via path_loader: {e}")
    print("=" * 60)
    print("NOTE: the DB path above is whatever THIS machine's own")
    print("hw_config/environment resolves to — it is not necessarily")
    print("the same database another machine's checkout would resolve")
    print("to. Each platform (GN100, UBUNTU2505, AMD box, Mac) has its")
    print("own local experiments.db.")


def cmd_full_verify():
    print("=" * 60)
    print("alems-test-framework — setup verification")
    print("=" * 60)

    if not VENDOR_PLATFORM.exists():
        print(f"FAIL: {VENDOR_PLATFORM} does not exist.")
        print("Did you clone with --recurse-submodules, or run:")
        print("  git submodule update --init --recursive")
        sys.exit(1)
    print(f"OK: submodule present at {VENDOR_PLATFORM}")

    ref, kind = get_pin_description()
    print(f"CURRENTLY TESTING AGAINST: {ref}  ({kind})")
    if "not pinned to a tag" in kind or "not exactly on a tag" in kind:
        print("NOTE: not on an exact tag. Fine for local, exploratory")
        print("testing (see doc/TESTING_GUIDE.md section 3), but results")
        print("checked in or reported to others should reference an")
        print("exact tag for reproducibility.")

    sys.path.insert(0, str(VENDOR_PLATFORM))
    try:
        import core  # noqa: F401
        print("OK: 'core' package is importable from the pinned submodule.")
    except ImportError as e:
        print(f"FAIL: could not import 'core' from vendor/alems-platform: {e}")
        sys.exit(1)

    try:
        from scripts.tools.path_loader import get_alems_db_path
        db_path = get_alems_db_path()
        print(f"OK: get_alems_db_path() resolved to: {db_path}")
        if not Path(db_path).exists():
            print(f"NOTE: resolved path does not exist on this machine "
                  f"yet ({db_path}) — expected if no experiments have "
                  f"run here. Not a setup failure.")
    except Exception as e:
        print(f"FAIL: could not resolve DB path via path_loader: {e}")
        sys.exit(1)

    print("=" * 60)
    print("Setup verification passed.")
    print(f"Testing against: {ref}  ({kind})")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description="Setup verification and pin/status inspection for alems-test-framework."
    )
    parser.add_argument("--status", action="store_true", help="Show current pin only.")
    parser.add_argument("--list-tags", action="store_true", help="List all available alems-platform tags.")
    parser.add_argument("--where", action="store_true", help="Show resolved filesystem/DB paths.")
    args = parser.parse_args()

    if args.status:
        cmd_status()
    elif args.list_tags:
        cmd_list_tags()
    elif args.where:
        cmd_where()
    else:
        cmd_full_verify()


if __name__ == "__main__":
    main()
