#!/usr/bin/env bash
set -euo pipefail

# ==========================================================
# validate.sh
#
# Run release + regression (no environment rebuild)
#
# Usage:
#   ./validate.sh <release-id> [--archive]
# ==========================================================

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"

if [ $# -lt 1 ]; then
  echo "Usage: $0 <release-id> [--archive]" >&2
  exit 1
fi

RELEASE="$1"
ARCHIVE=false

if [ "${2:-}" = "--archive" ]; then
  ARCHIVE=true
fi

OUTPUT_DIR="$ROOT_DIR/outputs/$RELEASE"
OUTPUT_FILE="Traceability_Reconciliation_${RELEASE}.xlsx"
REGRESSION_DIR="$ROOT_DIR/tests/regression/output"
BASELINE_FILE="Traceability_Reconciliation_${RELEASE}.xlsx"

echo "========================================"
echo "VALIDATION START"
echo "Release: $RELEASE"
echo "Archive: $ARCHIVE"
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
# Generate manifest (safe to always run)
# ----------------------------------------------------------
echo "Generating manifest..."
"$ROOT_DIR/generate_manifest.sh" "$RELEASE"

# ----------------------------------------------------------
# Run release
# ----------------------------------------------------------
echo "Running release pipeline..."
"$ROOT_DIR/run_release.sh" "$RELEASE"

# ----------------------------------------------------------
# Prepare regression baseline
# ----------------------------------------------------------
echo "Preparing regression baseline..."
mkdir -p "$REGRESSION_DIR"

cp "$OUTPUT_DIR/$OUTPUT_FILE" \
   "$REGRESSION_DIR/$BASELINE_FILE"

# ----------------------------------------------------------
# Run regression
# ----------------------------------------------------------
echo "Running regression..."
python "$ROOT_DIR/tests/regression/run_regression.py"

echo "========================================"
echo "VALIDATION COMPLETE ✅"
echo "========================================"