#!/usr/bin/env bash
set -euo pipefail

# ==========================================================
# bootstrap.sh
#
# Full clean bootstrap + validation
#
# Usage:
#   ./bootstrap.sh <release-id> [--archive]
# ==========================================================

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"

if [ $# -lt 1 ]; then
  echo "Usage: $0 <release-id> [--archive]" >&2
  exit 1
fi

RELEASE="$1"
shift

echo "========================================"
echo "BOOTSTRAP START"
echo "Release: $RELEASE"
echo "========================================"

# ----------------------------------------------------------
# Rebuild environment
# ----------------------------------------------------------
echo "Rebuilding virtual environment..."
"$ROOT_DIR/reset_venv.sh"

# Activate it for downstream steps
source "$ROOT_DIR/.venv/bin/activate"

# ----------------------------------------------------------
# Delegate to validation
# ----------------------------------------------------------
"$ROOT_DIR/validate.sh" "$RELEASE" "$@"

echo "========================================"
echo "BOOTSTRAP + VALIDATION COMPLETE ✅"
echo "========================================"