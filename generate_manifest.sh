#!/usr/bin/env bash
set -euo pipefail

if [ $# -lt 1 ]; then
  echo "Usage: $0 <release-id>   (e.g. 2026.02)"
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

# Manifest must store path relative to release dir
PLAN_FILE_REL="plan/$(basename "$PLAN_FILE_ABS")"

# ---- EXECUTION (.xlsx) ----
EXEC_FILES_ABS=()
while IFS= read -r -d '' file; do
  EXEC_FILES_ABS+=("$file")
done < <(find "$EXEC_DIR" -maxdepth 1 -type f -name '*.xlsx' -print0)

if [[ ${#EXEC_FILES_ABS[@]} -eq 0 ]]; then
  echo "ERROR: No .xlsx execution files found in $EXEC_DIR"
  exit 1
fi

# Build JSON array of execution files
EXEC_JSON_LINES=()
for f in "${EXEC_FILES_ABS[@]}"; do
  rel="execution/$(basename "$f")"
  rel_escaped=${rel//"/\"}
  EXEC_JSON_LINES+=("    \"$rel_escaped\"")
done

# Join with commas and newlines
EXEC_JSON_JOINED="$(printf ",\n%s" "${EXEC_JSON_LINES[@]}")"
EXEC_JSON_JOINED="${EXEC_JSON_JOINED:2}"

# ---- Write manifest.json ----
cat > "$MANIFEST" <<EOF
{
  "plan_file": "$(printf %s "$PLAN_FILE_REL" | sed 's/"/\\\"/g')",
  "execution_files": [
$EXEC_JSON_JOINED
  ]
}
EOF

echo "Manifest created at: $MANIFEST"
echo ""
cat "$MANIFEST"
