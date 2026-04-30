#!/usr/bin/env bash
set -euo pipefail

# ==========================================================
# validate.sh
#
# Run release + regression validation
#
# MODES:
#   Default:
#     - Run engine
#     - Compare output against baseline
#
#   --update-baseline:
#     - Run engine
#     - Update baseline from output
#     - Then run comparison
#
# Usage:
#   ./validate.sh <release-id> [--update-baseline]
# ==========================================================

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"

if [ $# -lt 1 ]; then
  echo "Usage: $0 <release-id> [--update-baseline]" >&2
  exit 1
fi

RELEASE="$1"
UPDATE_BASELINE=false

if [ "${2:-}" = "--update-baseline" ]; then
  UPDATE_BASELINE=true
fi

OUTPUT_DIR="$ROOT_DIR/outputs/$RELEASE"
OUTPUT_FILE="Traceability_Reconciliation_${RELEASE}.xlsx"

BASELINE_DIR="$ROOT_DIR/tests/regression/baseline"
BASELINE_FILE="Traceability_Reconciliation_${RELEASE}.xlsx"

echo "========================================"
echo "VALIDATION START"
echo "Release: $RELEASE"
echo "Update baseline: $UPDATE_BASELINE"
echo "========================================"

mkdir -p "$OUTPUT_DIR"

echo "Generating manifest..."
"$ROOT_DIR/generate_manifest.sh" "$RELEASE"

echo "Running release pipeline..."
"$ROOT_DIR/run_release.sh" "$RELEASE"

mkdir -p "$BASELINE_DIR"

if [ "$UPDATE_BASELINE" = true ]; then
  echo "Updating baseline..."
  cp "$OUTPUT_DIR/$OUTPUT_FILE" \
     "$BASELINE_DIR/$BASELINE_FILE"
fi

echo "Running regression..."
python "$ROOT_DIR/src/engine/regression.py"

echo "========================================"
echo "VALIDATION COMPLETE ✅"
echo "========================================"