#!/usr/bin/env python3
"""
verify_setup.py — confirms the pinned alems-platform submodule resolves
correctly before any real capability/coverage checks are written against
it. Run this once after cloning and after every deliberate pin bump.

This does NOT modify anything inside vendor/alems-platform/. It only
imports from it and reads its resolved database path.
"""

import sys
import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
VENDOR_PLATFORM = REPO_ROOT / "vendor" / "alems-platform"

def main():
    print("=" * 60)
    print("alems-test-framework — setup verification")
    print("=" * 60)

    # 1. Confirm the pinned submodule checkout actually exists
    if not VENDOR_PLATFORM.exists():
        print(f"FAIL: {VENDOR_PLATFORM} does not exist.")
        print("Did you clone with --recurse-submodules, or run:")
        print("  git submodule update --init --recursive")
        sys.exit(1)
    print(f"OK: submodule present at {VENDOR_PLATFORM}")

    # 2. Report which commit/tag it's actually pinned to right now
    git_head = VENDOR_PLATFORM / ".git"
    if git_head.exists():
        os.system(f"cd {VENDOR_PLATFORM} && git describe --tags --always")
    else:
        print("WARNING: vendor/alems-platform/.git not found — "
              "submodule may not be initialized correctly.")

    # 3. Confirm the platform's core modules are importable
    sys.path.insert(0, str(VENDOR_PLATFORM))
    try:
        import core  # noqa: F401
        print("OK: 'core' package is importable from the pinned submodule.")
    except ImportError as e:
        print(f"FAIL: could not import 'core' from vendor/alems-platform: {e}")
        sys.exit(1)

    # 4. Confirm the DB path resolution mechanism works — this is the
    # single shared source of truth path_loader.py already provides,
    # and this framework must reuse it rather than hardcoding DB paths.
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
    print("=" * 60)


if __name__ == "__main__":
    main()
