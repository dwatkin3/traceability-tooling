from pathlib import Path
import pandas as pd
import subprocess
import sys

BASELINE = Path("tests/regression/baseline/Traceability_Reconciliation_2026.04.xlsx")
OUTPUT = Path("tests/regression/output/Traceability_Reconciliation_test.xlsx")

RELEASE = "2026.04"


def run_engine():
    print("Running reconciliation...")
    result = subprocess.run(
        ["python", "run_reconcile.py", RELEASE],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print(result.stdout)
        print(result.stderr)
        raise RuntimeError("Engine run failed")


def load_sheet(path, sheet):
    return pd.read_excel(path, sheet_name=sheet).fillna("")


def compare_sheets(sheet):
    print(f"Comparing sheet: {sheet}")

    df_base = load_sheet(BASELINE, sheet)
    df_new = load_sheet(OUTPUT, sheet)

    # --------------------------------------------------
    # Align columns (CRITICAL FIX)
    # --------------------------------------------------
    common_cols = sorted(set(df_base.columns) & set(df_new.columns))

    df_base = df_base[common_cols]
    df_new = df_new[common_cols]

    # --------------------------------------------------
    # Sort rows to remove ordering noise
    # --------------------------------------------------
    df_base = df_base.sort_values(common_cols).reset_index(drop=True)
    df_new = df_new.sort_values(common_cols).reset_index(drop=True)

    # --------------------------------------------------
    # Compare
    # --------------------------------------------------
    if not df_base.equals(df_new):
        print(f"\n❌ MISMATCH in {sheet}")

        diff = df_base.compare(df_new)
        print(diff.head(20))

        print("\nColumns baseline:", list(df_base.columns))
        print("Columns new:", list(df_new.columns))

        return False

    print(f"✅ {sheet} matches")
    return True

def main():
    run_engine()

    # Move output file to known location
    latest = sorted(Path("outputs").rglob("Traceability_Reconciliation_*.xlsx"))[-1]
    latest.rename(OUTPUT)

    sheets = [
        "Summary",
        "Traceability Gaps",
        "Execution_Detail"
    ]

    results = [compare_sheets(s) for s in sheets]

    if not all(results):
        print("\n❌ REGRESSION FAILED")
        sys.exit(1)

    print("\n✅ REGRESSION PASSED")


if __name__ == "__main__":
    main()