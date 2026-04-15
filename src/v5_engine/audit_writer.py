from __future__ import annotations
from pathlib import Path
from typing import Dict, Iterable, List, Set, Tuple
import pandas as pd
import re
from .status_utils import classify_status

COL_STORY = "Story"
COL_STATUS = "Status"
COL_EVIDENCE = "Evidence"
COL_TEST = "Test ID"

def _df_from_set(name: str, values: Iterable[str]) -> pd.DataFrame:
    return pd.DataFrame({name: sorted(values)})

def _join(values: Iterable[str]) -> str:
    return ",".join(sorted(values)) if values else ""

def _family(t: str) -> str:
    m = re.match(r"^([A-Z]+)", t)
    return m.group(1) if m else ''

def _derive_exec_status(
    total_exec,
    passed,
    failed,
    in_progress,
    not_started,
    passed_with_evidence
):
    """
    Determine STORY-level execution status
    """

    if total_exec == 0:
        return "🔴 No execution tests"

    if failed > 0:
        return "🔴 Failed tests present"

    if passed > 0 and passed_with_evidence < passed and failed == 0:
        return "🔴 Passed but missing evidence"

    if in_progress > 0:
        return "🟠 In progress"

    if total_exec > 0 and passed == 0 and in_progress == 0:
        return "🟠 Not started"

    if passed == total_exec and passed_with_evidence == total_exec:
        return "🟢 Passed with evidence"

    return "🟠 Mixed / Unknown"

def _build_summary(story_to_tests, df_exec, pass_values, story_to_release):
    """
    Build one row per STORY with:
    - Traceability (Plan vs Execution presence)
    - Exec Status (RED / AMBER / GREEN based on rules)
    """

    print("DEBUG: story_to_release keys:", list(story_to_release.keys())[:5])
    print("PASS VALUES:", pass_values)

    import pandas as pd

    # 🔧 Ensure consistent column names
    df_exec = df_exec.copy()
    df_exec.columns = [c.strip() for c in df_exec.columns]

    summary_rows = []
    # -----------------------------
    # PRE-COMPUTE STATUS CLASS ONCE
    # -----------------------------
    df_exec["StatusClass"] = df_exec["Status"].apply(
        lambda s: classify_status(s, pass_values)
)

    for story, planned_tests in sorted(story_to_tests.items()):

        release = story_to_release.get(story, "UNKNOWN")
        print("DEBUG STORY:", story, "→ RELEASE:", release)

        # -----------------------------
        # EXECUTION DATA FOR THIS STORY
        # -----------------------------
        group = df_exec[df_exec[COL_STORY] == story]

        total_exec = len(group)

        # -----------------------------
        # TRACEABILITY
        # -----------------------------
        has_execution_tests = total_exec > 0

        if not has_execution_tests:
            traceability = "🔴 No tests in execution"
        else:
            traceability = "🟢 Tests present"

        status_counts = group["StatusClass"].value_counts()

        passed = status_counts.get("PASS", 0)
        failed = status_counts.get("FAIL", 0)
        in_progress = status_counts.get("IN_PROGRESS", 0)
        not_started = status_counts.get("NOT_STARTED", 0)

        # -----------------------------
        # ISSUE BUILDING
        # -----------------------------
        failed_tests = group[group["StatusClass"] == "FAIL"]["Test ID"].tolist()

        missing_evidence_tests = group[
            (group["StatusClass"] == "PASS") &
            (group["Evidence"] == "No")
        ]["Test ID"].tolist()

        issues = []

        if failed_tests:
            issues.append(f"Failed: {', '.join(sorted(failed_tests))}")

        if missing_evidence_tests:
            issues.append(f"Missing evidence: {', '.join(sorted(missing_evidence_tests))}")

        issue_text = " | ".join(issues) if issues else ""

        # -----------------------------
        # EVIDENCE CHECK
        # -----------------------------
        passed_with_evidence = len(group[
            (group["StatusClass"] == "PASS") &
            (group["Evidence"] == "Yes")
        ])

        # -----------------------------
        # EXEC STATUS (YOUR RULES)
        # -----------------------------
        exec_status = _derive_exec_status(
            total_exec,
            passed,
            failed,
            in_progress,
            not_started,
            passed_with_evidence
)

        # -----------------------------
        # BUILD ROW
        # -----------------------------
        summary_rows.append({
            "Release": release,   # 
            "Story": story,
            "Traceability": traceability,
            "Exec Status": exec_status,
            "Issue": issue_text,  # 
            "Planned Tests": len(planned_tests),
            "Execution Tests": total_exec,
            "Passed": int(passed),
            "Failed": int(failed),
            "In Progress": int(in_progress),
            "Not Started": int(not_started),
            "Passed w/ Evidence": int(passed_with_evidence)
        })

    df = pd.DataFrame(summary_rows)
    return df.sort_values(["Release", "Story"])


def write_output(
    output_path,
    plan_raw_rows,
    exec_rows,
    story_to_tests,
    result,
    story_to_release=None,
    df_exec=None,
    pass_values=None,   
    include_audit=True,
    debug_dir=None
):
    
    if df_exec is None:
        exec_rows_unique = list(dict.fromkeys(exec_rows))
        df_exec = pd.DataFrame(exec_rows_unique, columns=[
                               'Sheet', 'Row', 'Story', 'Test ID', 'Status', 'File'])
    else:
        # Ensure consistent column naming for downstream logic
        df_exec = df_exec.copy()
        df_exec.columns = [c.strip() for c in df_exec.columns]

    df_summary = _build_summary(
        story_to_tests,
        df_exec,
        pass_values,
        story_to_release
    )

    df_missing=_df_from_set('MissingTest', result.missing_tests)
    df_extra=_df_from_set('ExtraTest', result.extra_tests)
    st_rows=[(s,t) for s,tests in sorted(story_to_tests.items()) for t in sorted(tests)]
    
    df_story_map=pd.DataFrame(st_rows, columns=['Story','Test'])
    df_plan_raw=pd.DataFrame(plan_raw_rows, columns=['StoryCell','RowText','TestCell'])
    
    output_path=Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with pd.ExcelWriter(output_path, engine='openpyxl') as xw:
        df_summary.to_excel(xw, sheet_name='Summary', index=False)
        df_missing.to_excel(xw, sheet_name='Missing', index=False)
        df_extra.to_excel(xw, sheet_name='Extra', index=False)
        df_story_map.to_excel(xw, sheet_name='Story_To_Test_Map', index=False)
        df_exec.to_excel(xw, sheet_name='Execution_Attachments', index=False)
       
        if include_audit:
            df_plan_raw.to_excel(xw, sheet_name='Plan_Raw', index=False)
            df_exec.to_excel(xw, sheet_name='Exec_Raw', index=False)
    
    if debug_dir:
        debug_dir=Path(debug_dir); debug_dir.mkdir(parents=True, exist_ok=True)
        df_summary.to_csv(debug_dir/'summary.csv', index=False)
        df_story_map.to_csv(debug_dir/'plan_extracted.csv', index=False)
        df_exec.to_csv(debug_dir/'exec_extracted.csv', index=False)
        df_missing.to_csv(debug_dir/'missing_tests.csv', index=False)
        df_extra.to_csv(debug_dir/'extra_tests.csv', index=False)
