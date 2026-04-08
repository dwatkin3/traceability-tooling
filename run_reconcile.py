#!/usr/bin/env python3

"""
Unified entry point for traceability reconciliation.

Usage:
    python run_reconcile.py YYYY.MM
    python run_reconcile.py 2026.02
"""

import os
import sys
import re
import warnings
from pathlib import Path


# ------------------------------------------------------------
# Environment setup
# ------------------------------------------------------------

def setup_environment():
    repo_root = Path(__file__).resolve().parent
    src_path = repo_root / "src"

    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))

    # Suppress harmless openpyxl warnings
    warnings.filterwarnings(
        "ignore",
        category=UserWarning,
        module="openpyxl"
    )


# ------------------------------------------------------------
# Argument handling
# ------------------------------------------------------------

def parse_release_arg():
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python run_reconcile.py YYYY.MM (e.g. 2026.02)")

    release = sys.argv[1]

    if not re.fullmatch(r"\d{4}\.\d{2}", release):
        raise SystemExit(f"Invalid release format: {release} (expected YYYY.MM)")

    return release


# ------------------------------------------------------------
# Main
# ------------------------------------------------------------

def main():
    setup_environment()
    release = parse_release_arg()

    from v5_engine.run_release import run_release

    root = Path(__file__).resolve().parent
    release_dir = root / "releases" / release

    result = run_release(
        root_dir=release_dir,
        manifest_path=release_dir / "manifest.json",
        settings_path=root / "config" / "settings.json",
        patterns_path=root / "config" / "knowledge" / "patterns.json",
        hints_path=root / "config" / "knowledge" / "column_hints.json",
    )

    print(f"{release} reconciliation complete.")
    print("ABS OUTPUT:", result["output"])


if __name__ == "__main__":
    main()