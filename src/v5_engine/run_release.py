#!/usr/bin/env python3
import argparse
import json
import pathlib
import pandas as pd
from pathlib import Path


from .spec_reader import extract_story_test_map
from .plan_parser import parse_plan_docx
from .exec_parser import parse_execution_xlsx
from .reconcile import reconcile

def load_planned_tests(manifest: dict, root_dir: pathlib.Path) -> dict[str, set[str]]:
    """
    Always returns:
        { story_id -> set(test_ids) }
    """


    # --- Prefer Test Specification ---
    spec_file = manifest.get("spec_file")
    if spec_file:
        spec_path = root_dir / spec_file
        if spec_path.exists():
            print(f"INFO: Using Test Specification: {spec_path}")
            return extract_story_test_map(spec_path)
        else:
            print(f"WARNING: Spec file not found at {spec_path}")

    # --- Fallback to Test Plan ---
    print("WARNING: Attempting to use PLAN and NOT SPEC")
    plan_file = manifest.get("plan_file")
    if plan_file:
        plan_path = root_dir / plan_file
        if plan_path.exists():
            print(f"INFO: Using Test Plan: {plan_path}")
            result = parse_plan_docx(plan_path)
            return result.story_to_tests
        else:
            print(f"WARNING: Plan file not found at {plan_path}")

    # --- Hard fail (important) ---
    raise FileNotFoundError(
        "No valid spec_file or plan_file found in manifest"
)

def run_release(
    root_dir,
    manifest_path,
    settings_path=None,
    patterns_path=None,
    hints_path=None,
):

    root = root_dir.parent  # project root

    manifest = json.loads(manifest_path.read_text())

    plan_path = root_dir / manifest["plan_file"]
    exec_paths = [root_dir / p for p in manifest.get("execution_files", [])]

    print(f"Processing release: {root_dir.name}")
    print(f"PLAN : {plan_path}")
    for p in exec_paths:
        print(f"EXEC : {p}")

    # Load config
    from .column_hints_loader import load_column_hints
    from .patterns_loader import load_patterns

    hints = load_column_hints(hints_path)
    patterns = load_patterns(patterns_path)

    # Planned tests
    print("✅ ABOUT TO LOAD PLANNED TESTS")
    plan_map = load_planned_tests(manifest, root_dir)

    # Execution parsing
    exec_test_ids = set()
    exec_story_refs = set()
    exec_raw_all = []

    print("✅ ABOUT TO LOAD SPREADSHEETS")
    for p in exec_paths:
        result = parse_execution_xlsx(
            p,
            hints.story_column_candidates,
            hints.testid_column_candidates,
            patterns.story_patterns,
            patterns.testid_patterns
        )

        for r in result.rows:
            exec_test_ids.add(r.test)
            if r.story:
                exec_story_refs.add(r.story)

            exec_raw_all.append((r.sheet, r.row, r.story, r.test, r.file))

    # Reconcile
    print("✅ ABOUT TO RECONCILE")
    result = reconcile(plan_map, exec_test_ids, exec_story_refs)

    # Plan raw
    plan_raw_rows = []
    for s, tests in plan_map.items():
        if tests:
            for t in sorted(tests):
                plan_raw_rows.append((s, "", t))  # ← 3 columns
        else:
            plan_raw_rows.append((s, "", ""))   # ← still 3 columns
    
    # Output
    from .audit_writer import write_output

    root = root_dir.parent.parent
    out_dir = root / "outputs" / root_dir.name
    dbg_dir = out_dir / "debug"
    dbg_dir.mkdir(parents=True, exist_ok=True)

    out_file = out_dir / "Traceability_Reconciliation.xlsx"

    write_output(
        out_file,
        plan_raw_rows,
        exec_raw_all,
        plan_map,
        result,
        include_audit=True,
        debug_dir=dbg_dir
    )

    return {
        "output": str(out_file)
    }

def main():
    parser = argparse.ArgumentParser(description="Run Traceability Reconciler")
    parser.add_argument("--release", required=True)
    args = parser.parse_args()

    root = pathlib.Path(__file__).resolve().parent
    rel_dir = root / "releases" / args.release

    result = run_release(
        root_dir=rel_dir,
        manifest_path=rel_dir / "manifest.json",
        patterns_path=root / "config" / "knowledge" / "patterns.json",
        hints_path=root / "config" / "knowledge" / "column_hints.json",
    )

    print("ABS OUTPUT:", result["output"])