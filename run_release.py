#!/usr/bin/env python3
import argparse
import json
import pathlib
import pandas as pd

from src.engine.plan_parser import extract_plan_mappings
from src.engine.exec_parser import extract_exec_mappings
from src.engine.reconcile import reconcile


def main():
    parser = argparse.ArgumentParser(description="Run Traceability Reconciler")
    parser.add_argument("--release", required=True, help="Release ID like 2026.03")
    args = parser.parse_args()

    root = pathlib.Path(__file__).resolve().parent
    rel_dir = root / "releases" / args.release
    manifest_path = rel_dir / "manifest.json"

    if not manifest_path.exists():
        raise SystemExit(f"Manifest not found: {manifest_path}")

    manifest = json.loads(manifest_path.read_text())

    plan_path = rel_dir / manifest["plan_file"]
    exec_paths = [rel_dir / p for p in manifest.get("execution_files", [])]

    print(f"Processing release: {args.release}")
    print(f"PLAN : {plan_path}")
    for p in exec_paths:
        print(f"EXEC : {p}")

    # Extract plan mappings
    plan_map = extract_plan_mappings(str(plan_path))

    # Extract execution mappings (merged across files)
    exec_map = {}
    exec_raw_all = []
    for p in exec_paths:
        m, raw = extract_exec_mappings(str(p))
        for story, tests in m.items():
            exec_map.setdefault(story, set()).update(tests)
        exec_raw_all.extend([{**r, "file": p.name} for r in raw])

    # Reconcile
    df_summary, df_missing, df_extra = reconcile(plan_map, exec_map)

    # TEMP DEBUG: print STRY0086890 status as engine sees it
    row = df_summary.loc[df_summary["story"] == "STRY0086890"]
    print("DEBUG STRY0086890:", row.to_dict(orient="records"))


    # Build plan raw detail sheet
    plan_raw_rows = []
    for s, tests in plan_map.items():
        if tests:
            for t in sorted(tests):
                plan_raw_rows.append({"Story": s, "Test": t})
        else:
            plan_raw_rows.append({"Story": s, "Test": ""})

    df_plan_raw = pd.DataFrame(plan_raw_rows)
    df_exec_raw = pd.DataFrame(exec_raw_all)

    # Output folder
    out_dir = root / "outputs" / args.release
    dbg_dir = out_dir / "debug"
    dbg_dir.mkdir(parents=True, exist_ok=True)

    out_file = out_dir / "Traceability_Reconciliation.xlsx"

    # Write Excel output
    with pd.ExcelWriter(out_file, engine="openpyxl") as writer:
        df_summary.to_excel(writer, index=False, sheet_name="Summary")
        df_plan_raw.to_excel(writer, index=False, sheet_name="Plan_Raw")
        df_exec_raw.to_excel(writer, index=False, sheet_name="Exec_Raw")
        df_missing.to_excel(writer, index=False, sheet_name="Missing")
        df_extra.to_excel(writer, index=False, sheet_name="Extra")

    # Write debug CSVs
    df_plan_raw.to_csv(dbg_dir / "plan_extracted.csv", index=False)
    df_exec_raw.to_csv(dbg_dir / "exec_extracted.csv", index=False)
    df_missing.to_csv(dbg_dir / "missing_tests.csv", index=False)
    df_extra.to_csv(dbg_dir / "extra_tests.csv", index=False)

    print(f"Written outputs to {out_dir}")


if __name__ == "__main__":
    main()