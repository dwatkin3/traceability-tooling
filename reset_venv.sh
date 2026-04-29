#!/usr/bin/env bash
set -euo pipefail

# ==========================================================
# reset_venv.sh
#
# Purpose:
#   Rebuild the project’s Python virtual environment from scratch.
#
#   This ensures a clean, reproducible environment for running
#   the traceability pipeline, avoiding issues caused by:
#     - stale dependencies
#     - conflicting packages
#     - local environment drift
#
# Behaviour:
#   - Deletes existing .venv (if present)
#   - Creates a fresh virtual environment
#   - Activates it for the duration of the script
#   - Upgrades core packaging tools (pip, setuptools, wheel)
#   - Installs dependencies from requirements.txt
#
# Usage:
#   ./reset_venv.sh
#
# After running:
#   source .venv/bin/activate
#
# Notes:
#   - Safe to run multiple times (idempotent)
#   - Intended for initial setup and troubleshooting
#   - Used in clean-environment validation workflows
#
# Typical workflow:
#   ./reset_venv.sh
#   source .venv/bin/activate
#   ./generate_manifest.sh 2026.04
#   ./run_release.sh 2026.04
# ==========================================================

echo "Removing old venv (if exists)..."
rm -rf .venv

echo "Creating new venv..."
python3 -m venv .venv

echo "Activating venv..."
source .venv/bin/activate

echo "Upgrading core tooling..."
pip install --upgrade pip setuptools wheel

echo "Installing requirements..."
pip install -r requirements.txt

echo ""
echo "VENV READY."
echo "To activate manually later: source .venv/bin/activate"