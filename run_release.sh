#!/usr/bin/env bash
set -euo pipefail

if [ ! -d "$(dirname "$0")/.venv" ]; then
  echo "ERROR: Virtual environment not found. Run ./reset_venv.sh first."
  exit 1
fi

if [ $# -lt 1 ]; then
  echo "Usage: $0 <release-id> (e.g. 2026.03)" >&2
  exit 1
fi

# Activate the virtual environment for this project explicitly
source "$(dirname "$0")/.venv/bin/activate"

PYTHONPATH="$(dirname "$0")" python3 src/v5_engine/run_release.py --release "$1"
