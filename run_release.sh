#!/usr/bin/env bash
set -euo pipefail

# ==========================================================
# run_release.sh
#
# Purpose:
#   Shell entrypoint for executing the traceability pipeline.
#
#   Provides a simple, reproducible way to run a full
#   reconciliation for a given release without requiring
#   manual environment setup.
#
# Behaviour:
#   - Verifies that a project virtual environment exists
#   - Activates the local .venv
#   - Confirms which Python interpreter is being used
#   - Executes the pipeline via module entrypoint:
#       src.engine.run_release
#
# Usage:
#   ./run_release.sh <release-id>
#   e.g.
#     ./run_release.sh 2026.04
#
# Requirements:
#   - .venv must exist (run ./reset_venv.sh first)
#   - manifest.json must exist for the release
#
# Notes:
#   - Uses "python -m" to ensure package-relative imports work
#   - PYTHONPATH is set to repo root for module resolution
#   - Virtual environment activation is local to this script
#
# Example flow:
#   ./reset_venv.sh
#   ./generate_manifest.sh 2026.04
#   ./run_release.sh 2026.04
#
# Output:
#   outputs/<release-id>/Traceability_Reconciliation_<release-id>.xlsx
# ==========================================================

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"

if [ ! -d "$ROOT_DIR/.venv" ]; then
  echo "ERROR: Virtual environment not found. Run ./reset_venv.sh first."
  exit 1
fi

if [ $# -lt 1 ]; then
  echo "Usage: $0 <release-id> (e.g. 2026.04)" >&2
  exit 1
fi

RELEASE="$1"

# Activate the virtual environment
source "$ROOT_DIR/.venv/bin/activate"

echo "Using Python: $(which python)"
echo "Running release: $RELEASE"

PYTHONPATH="$ROOT_DIR" python3 -m src.engine.run_release --release "$RELEASE"