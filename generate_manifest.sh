#!/usr/bin/env bash
set -euo pipefail

# ==========================================================
# generate_manifest.sh
#
# Purpose:
#   Generates a manifest.json file for a given release folder.
#
#   The manifest defines the inputs required by the reconciliation
#   pipeline:
#     - The latest test plan document (.docx)
#     - All execution files (.xlsx)
#
# Behaviour:
#   - Identifies the most recently modified .docx file in /plan
#   - Collects all .xlsx files in /execution
#   - Writes a clean, deterministic manifest.json
#
# Output:
#   releases/<release-id>/manifest.json
#
# Usage:
#   ./generate_manifest.sh <release-id>
#   e.g.
#     ./generate_manifest.sh 2026.04
#
# Notes:
#   - The release ID is supplied via CLI (not stored in manifest)
#   - Output paths are relative to the release folder
#   - Designed to work on macOS and Linux (no GNU-specific flags)
#
# Example output:
# {
#   "plan_file": "plan/Some Plan.docx",
#   "execution_files": [
#     "execution/File1.xlsx",
#     "execution/File2.xlsx"
#   ]
# }
# ==========================================================

# Usage check
if [ $# -lt 1 ]; then
  echo "Usage: $0 <release-id>   (e.g. 2026.04)"
  exit 1
fi

RELEASE="$1"
ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
RELEASE_DIR="$ROOT_DIR/releases/$RELEASE"
PLAN_DIR="$RELEASE_DIR/plan"
EXEC_DIR="$RELEASE_DIR/execution"
MANIFEST="$RELEASE_DIR/manifest.json"

# Validate folder structure
[[ -d "$RELEASE_DIR" ]] || { echo "ERROR: Missing $RELEASE_DIR"; exit 1; }
[[ -d "$PLAN_DIR"   ]] || { echo "ERROR: Missing $PLAN_DIR";   exit 1; }
[[ -d "$EXEC_DIR"   ]] || { echo "ERROR: Missing $EXEC_DIR";   exit 1; }

# ---- PLAN (.docx) ----
PLAN_FILE_ABS="$(ls -t "$PLAN_DIR"/*.docx 2>/dev/null | head -n 1)"

if [[ -z "${PLAN_FILE_ABS:-}" ]]; then
  echo "ERROR: No .docx plan file found in $PLAN_DIR"
  exit 1
fi

PLAN_FILE_REL="plan/$(basename "$PLAN_FILE_ABS")"

# ---- EXECUTION (.xlsx) ----
EXEC_JSON=""

for f in "$EXEC_DIR"/*.xlsx; do
  [ -e "$f" ] || continue
  rel="execution/$(basename "$f")"

  if [ -z "$EXEC_JSON" ]; then
    EXEC_JSON="    \"$rel\""
  else
    EXEC_JSON="${EXEC_JSON},\n    \"$rel\""
  fi
done

# Convert literal \n into real newlines
EXEC_JSON=$(printf "%b" "$EXEC_JSON")

if [ -z "$EXEC_JSON" ]; then
  echo "ERROR: No .xlsx execution files found in $EXEC_DIR"
  exit 1
fi

# ---- Write manifest.json ----
cat > "$MANIFEST" <<EOF
{
  "plan_file": "$PLAN_FILE_REL",
  "execution_files": [
$EXEC_JSON
  ]
}
EOF

echo "Manifest created at: $MANIFEST"
echo ""
cat "$MANIFEST"
