#!/usr/bin/env bash
set -euo pipefail

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
    EXEC_JSON="$EXEC_JSON
    \"$rel\""
  fi
done

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
