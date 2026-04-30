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
#   ./validate.sh <release-id> [--archive] [--update-baseline]
# ==========================================================

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"

if [ $# -lt 1 ]; then
  echo "Usage: $0 <release-id> [--archive] [--update-baseline]" >&2
  exit 1
fi

RELEASE="$1"

ARCHIVE=false
UPDATE_BASELINE=false

for arg in "${@:2}"; do
  case $arg in
    --archive)
      ARCHIVE=true
      ;;
    --update-baseline)
      UPDATE_BASELINE=true
      ;;
  esac
done

OUTPUT_DIR="$ROOT_DIR/outputs/$RELEASE"
OUTPUT_FILE="Traceability_Reconciliation_${RELEASE}.xlsx"

BASELINE_DIR="$ROOT_DIR/tests/regression/baseline"
BASELINE_FILE="Traceability_Reconciliation_${RELEASE}.xlsx"

echo "========================================"
echo "VALIDATION START"
echo "Release: $RELEASE"
echo "Archive: $ARCHIVE"
echo "Update baseline: $UPDATE_BASELINE"
echo "========================================"

# ----------------------------------------------------------
# Ensure output dir
# ----------------------------------------------------------
mkdir -p "$OUTPUT_DIR"

# ----------------------------------------------------------
# Optional archive
# ----------------------------------------------------------
if [ "$ARCHIVE" = true ] && [ -f "$OUTPUT_DIR/$OUTPUT_FILE" ]; then
  TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
  ARCHIVE_NAME="${OUTPUT_FILE%.xlsx}_$TIMESTAMP.xlsx"

  echo "Archiving existing output..."
  mv "$OUTPUT_DIR/$OUTPUT_FILE" "$OUTPUT_DIR/$ARCHIVE_NAME"
fi

# ----------------------------------------------------------
# Generate manifest
# ----------------------------------------------------------
echo "Generating manifest..."
"$ROOT_DIR/generate_manifest.sh" "$RELEASE"

# ----------------------------------------------------------
# Run engine (ONCE)
# ----------------------------------------------------------
echo "Running release pipeline..."
"$ROOT_DIR/run_release.sh" "$RELEASE"

# ----------------------------------------------------------
# Baseline handling
# ----------------------------------------------------------
mkdir -p "$BASELINE_DIR"

if [ "$UPDATE_BASELINE" = true ]; then
  echo "Updating baseline..."
  cp "$OUTPUT_DIR/$OUTPUT_FILE" \
     "$BASELINE_DIR/$BASELINE_FILE"
fi

# ----------------------------------------------------------
# Run regression (compare only)
# ----------------------------------------------------------
echo "Running regression..."
python -m src.engine.regression

echo "========================================"
echo "VALIDATION COMPLETE ✅"
echo "========================================"