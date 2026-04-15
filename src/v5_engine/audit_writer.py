from __future__ import annotations
from pathlib import Path
from typing import Dict, Iterable, List, Set, Tuple
import pandas as pd
import re

def _df_from_set(name: str, values: Iterable[str]) -> pd.DataFrame:
    return pd.DataFrame({name: sorted(values)})

def _join(values: Iterable[str]) -> str:
    return ",".join(sorted(values)) if values else ""

def _family(t: str) -> str:
    m = re.match(r"^([A-Z]+)", t)
    return m.group(1) if m else ''

def _build_summary(story_to_tests, df_exec, pass_values):

    def _classify_status(s, pass_values):
        s_clean = str(s).strip().lower()

        pass_values_clean = [p.lower() for p in pass_values]

        if any(p in s_clean for p in pass_values_clean):
            return "PASS"

        if "fail" in s_clean:
            return "FAIL"

        if "progress" in s_clean:
            return "IN_PROGRESS"

        if "start" in s_clean:
            return "NOT_STARTED"

        return "OTHER"


    def _derive_exec_status(group):
        total = len(group)

        status_counts = group["StatusClass"].value_counts()

        passed = status_counts.get("PASS", 0)
        failed = status_counts.get("FAIL", 0)
        in_progress = status_counts.get("IN_PROGRESS", 0)
        not_started = status_counts.get("NOT_STARTED", 0)

        passed_with_evidence = len(group[
            (group["StatusClass"] == "PASS") &
            (group["Evidence"] == "Yes")
        ])

        # ---- LOGIC ----
        if total == 0:
            return "🔴 No Tests"

        if failed > 0:
            return "🔴 Failed"

        if passed > 0 and passed_with_evidence < passed:
            return "🔴 Passed but NO evidence"

        if passed == 0 and in_progress == 0:
            return "🔴 Not Started"

        if in_progress > 0:
            return "🟠 In Progress"

        if passed == total and passed_with_evidence == passed:
            return "🟢 Passed with Evidence"

        return "🟠 Mixed"

    df_exec = df_exec.copy()

    # Ensure expected column names
    df_exec.rename(columns={
        'story': 'Story',
        'test': 'Test ID'
    }, inplace=True)

    df_exec["StatusClass"] = df_exec["Status"].apply(
        lambda s: _classify_status(s, pass_values)
    )

    summary_rows = []

    # 🔑 iterate ALL stories from PLAN (important for missing case)
    for story, group in df_exec.groupby("Story"):

        total = len(group)

        status_counts = group["StatusClass"].value_counts()

        passed = status_counts.get("PASS", 0)
        failed = status_counts.get("FAIL", 0)
        in_progress = status_counts.get("IN_PROGRESS", 0)
        not_started = status_counts.get("NOT_STARTED", 0)

        passed_with_evidence = len(group[
            (group["StatusClass"] == "PASS") &
            (group["Evidence"] == "Yes")
        ])

        # ✅ TRACEABILITY
        traceability = "🟢 Covered" if total > 0 else "🔴 No Tests"

        # ✅ EXEC STATUS
        exec_status = _derive_exec_status(group)

        summary_rows.append({
            "Story": story,
            "Traceability": traceability,
            "Exec Status": exec_status,
            "Total Tests": total,
            "Passed": passed,
            "Failed": failed,
            "In Progress": in_progress,
            "Not Started": not_started,
            "Passed w/ Evidence": passed_with_evidence
        })

    return pd.DataFrame(summary_rows)

def write_output(output_path: Path, plan_raw_rows, exec_rows, 
                 story_to_tests, result, df_exec=None, df_summary=None,
                 include_audit=True, debug_dir=None, 
                 pass_values=None):
    
    if df_exec is None:
        exec_rows_unique = list(dict.fromkeys(exec_rows))
        df_exec = pd.DataFrame(exec_rows_unique, columns=[
                               'Sheet', 'Row', 'Story', 'Test ID', 'Status', 'File'])
    else:
        # Ensure consistent column naming for downstream logic
        df_exec = df_exec.copy()
        df_exec.columns = [c.strip() for c in df_exec.columns]

    # 🔧 NORMALISE COLUMN NAMES FOR SUMMARY LOGIC
    df_exec.rename(columns={
        'Story': 'story',
        'Test ID': 'test'
    }, inplace=True)

    df_summary = _build_summary(story_to_tests, df_exec, pass_values)
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
