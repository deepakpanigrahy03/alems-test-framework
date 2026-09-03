#!/usr/bin/env bash
# collect.sh — Copy B1 reports from all machines into reports/collected/
# Edit MACHINES list to match your network before running.
set -euo pipefail
REPORT_DIR="$(git rev-parse --show-toplevel)/reports/collected"
mkdir -p "$REPORT_DIR"
MACHINES=(
    "dpani@gn100-2b96:~/mydrive/alems-test-framework/reports/b1/gn100-2b96"
    # "user@ubuntu2505:~/mydrive/alems-test-framework/reports/b1/ubuntu2505"
    # "user@amd-host:~/mydrive/alems-test-framework/reports/b1/amd"
    # "user@mac-host:~/mydrive/alems-test-framework/reports/b1/mac"
)
for src in "${MACHINES[@]}"; do
    echo "Collecting from $src ..."
    scp -r "$src" "$REPORT_DIR/" || echo "WARNING: could not reach $src"
done
echo "Done. Reports in $REPORT_DIR"
ls "$REPORT_DIR"
