# ==========================================================
# TRACEABILITY RECONCILER - RUN PIPELINE
#
# Flow:
# 1. Load plan → story_to_tests
# 2. Parse execution files → exec_rows
# 3. Reconcile plan vs execution
# 4. Enrich execution (evidence + results)
# 5. Write output workbook
# ==========================================================

from __future__ import annotations
import json
from pathlib import Path
from .settings_loader import load_settings
from .patterns_loader import load_patterns
from .column_hints_loader import load_column_hints
from .exec_parser import parse_execution_xlsx
from .reconcile import reconcile
from .audit_writer import write_output
from .plan_parser import parse_plan_docx_with_release
from collections import defaultdict
import re

def normalise_test_id(t: str) -> str:
    if t is None:
        return ""
    return (
        str(t)
        .upper()
        .strip()
        .replace("\u00A0", "")
        .replace(" ", "")
    )

def derive_test_result(status, has_evidence, pass_values):
    s = (status or "").lower().strip()
    pass_values = [p.lower().strip() for p in pass_values]

    # PASS logic (from config)
    is_pass = any(p == s for p in pass_values)

    # FAIL logic (anything meaningful but not pass)
    is_fail = "fail" in s

    if is_fail:
        return "Fail"

    if is_pass:
        if has_evidence:
            return "Evidenced"
        return "Passed"

    return "N/A"

def run_release(root_dir: Path, manifest_path: Path, settings_path: Path, patterns_path: Path, hints_path: Path, output_path: Path|None=None):
    root_dir=Path(root_dir)
    settings=load_settings(Path(settings_path))
    patterns=load_patterns(Path(patterns_path))
    hints=load_column_hints(Path(hints_path))
    manifest=json.loads(Path(manifest_path).read_text())
    plan_file=root_dir/manifest['plan_file']
    exec_files=[root_dir/p for p in manifest.get('execution_files', [])]
    
    print("RUN_RELEASE STARTED")

    # -----------------------------
    # LOAD TEST PLAN (source of truth)
    # -----------------------------
    # Returns:
    # - release_story_to_tests: (release, story) → tests
    # - story_to_release: story → release mapping (for reporting later)

    release_story_to_tests, story_to_release, plan_raw_rows = parse_plan_docx_with_release(
            plan_file
    )

    # NOTE:
    # release_story_to_tests is keyed as (release, story)
    # We flatten to story-only because reconcile() works at story level
    # and does not distinguish between releases
    story_to_tests = defaultdict(set)
    for (_, story), tests in release_story_to_tests.items():
        story_to_tests[story].update(tests)

    # --------------------------------------------------
    # NORMALISE PLAN TEST IDS
    # Ensures consistency with execution data
    # This is CRITICAL for matching logic later
    # --------------------------------------------------
    for story in story_to_tests:
        story_to_tests[story] = set(
            normalise_test_id(t) for t in story_to_tests[story]
        )
            
    # -----------------------------
    # PARSE EXECUTION FILES
    # -----------------------------
    # Build:
    # - exec_rows: full execution dataset (for reporting)
    # - exec_test_ids: all test IDs found in execution sheets (regardless of status)
    # - exec_story_refs: all stories referenced in execution

    exec_rows=[]
    exec_test_ids=set(); exec_story_refs=set()

    for xf in exec_files:

        res = parse_execution_xlsx(
            xf,
            hints.story_column_candidates,
            hints.testid_column_candidates,
            patterns.story_patterns,
            patterns.testid_patterns,
            hints.status_column_candidates,
            hints.ignore_sheets
        )

        for r in res.rows:

            exec_rows.append((
                r.sheet,
                int(r.row),
                r.story or '',
                r.test,
                r.status,
                r.file
            ))

            # ✅ MUST BE INSIDE LOOP
            exec_test_ids.add(r.test)

            if r.story:
                exec_story_refs.add(r.story)
    
    # -----------------------------
    # RECONCILIATION (PLAN vs EXECUTION)
    # -----------------------------
    # Identifies:
    # - missing tests
    # - extra tests
    # - stories with no execution coverage
    # - unexpected stories in execution
    result = reconcile(
        story_to_tests,
        exec_test_ids,
        exec_story_refs,
        settings.red_on_extra
    )
    # -----------------------------
    # BUILD EXECUTION DATAFRAME
    # -----------------------------
    # Columns:
    # - Story, Test ID, Status (raw from Excel)
    # - Evidence (derived from evidence folder)
    # - Test Result (derived: Passed / Evidenced / Fail / N/A)

    import pandas as pd

    df_exec = pd.DataFrame(exec_rows, columns=[
        "Sheet", "Row", "Story", "Test ID", "Status", "File"
    ])

    # --------------------------------------------------
    # NORMALISE IDS (CRITICAL FOR MATCHING)
    # Ensures consistency between:
    # - Plan (Word)
    # - Execution (Excel)
    # - Evidence (filenames)
    # --------------------------------------------------
    df_exec["Test ID"] = df_exec["Test ID"].apply(normalise_test_id)

    # --------------------------------------------------
    # NORMALISE STORY IDS
    # - Trim whitespace
    # - Uppercase for consistency
    # - Remove obvious junk (e.g. blank, 'nan')
    # NOTE:
    # We DO NOT force-match to plan stories here
    # (we need to detect misalignment later)
    # --------------------------------------------------
    df_exec["Story"] = (
        df_exec["Story"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    # Clean empty / invalid values
    df_exec.loc[df_exec["Story"].isin(["", "NAN", "NONE"]), "Story"] = ""


    # Evidence is determined by filename match:
    # if any file in /evidence contains the Test ID → Evidence = Yes
    evidence_files = []
    evidence_dir = root_dir / "evidence"

    if evidence_dir.exists():
        for p in evidence_dir.rglob("*"):
            evidence_files.append(p.name.lower())
 
    def normalise(s):
        return re.sub(r'[^a-z0-9]', '', s.lower())

    def has_evidence(test_id):
        t = normalise(test_id)
        return any(t in normalise(f) for f in evidence_files)

    # ✅ THIS MUST BE OUTSIDE THE FUNCTION
    df_exec["Evidence"] = df_exec["Test ID"].apply(
        lambda t: "Yes" if has_evidence(t) else "No"
    )

    df_exec["Test Result"] = df_exec.apply(
        lambda r: derive_test_result(
            r["Status"],
            r["Evidence"] == "Yes",
            hints.pass_values
        ),
        axis=1
    )

    release_id=root_dir.name
    out_folder=Path('outputs')/release_id
    out_folder.mkdir(parents=True, exist_ok=True)
    fname=f'Traceability_Reconciliation_{release_id}.xlsx'
    out_f=output_path or (out_folder/fname)

    # -----------------------------
    # WRITE OUTPUT FILE
    # -----------------------------
    # Delegates to audit_writer:
    # - Summary sheet (main reporting view)
    # - Execution raw data
    # - Missing / Extra tests
    # - Debug outputs (optional)
    write_output(
        out_f,
        plan_raw_rows,
        exec_rows,
        release_story_to_tests,
        result,
        story_to_release,
        df_exec=df_exec,
        pass_values=hints.pass_values,
        include_audit=settings.enable_audit_sheets,
        debug_dir=out_folder/'debug'
)
    return {"output": str(Path(out_f).resolve())}
    

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run Traceability Reconciler")
    parser.add_argument("--release", required=True)
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[2]
    rel_dir = root / "releases" / args.release

    print(f"Manifest: {rel_dir / 'manifest.json'}")

    result = run_release(
        root_dir=rel_dir,
        manifest_path=rel_dir / "manifest.json",
        settings_path=root / "config/settings.json",
        patterns_path=root / "config/knowledge/patterns.json",
        hints_path=root / "config/knowledge/column_hints.json",
    )

    print("Output written to:", result["output"])
