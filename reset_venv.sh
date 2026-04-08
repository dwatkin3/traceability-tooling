#!/usr/bin/env bash
set -euo pipefail

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