from __future__ import annotations
from pathlib import Path
from typing import Iterable
import pandas as pd
import re
from .status_utils import classify_status
from .id_normaliser import normalise_id

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

def _build_execution_detail(df_exec, story_to_tests, story_to_release):
    rows = []

    # Debug (optional – remove later)
    print("STORY KEY SAMPLE:", list(story_to_tests.keys())[:3])

    # --------------------------------------------------
    # Pre-group execution by Test ID
    # --------------------------------------------------
    exec_by_test = df_exec.groupby("Test ID")

    for story_key, planned_tests in story_to_tests.items():

        # --------------------------------------------------
        # 🔑 FIX: unpack tuple (release, story)
        # --------------------------------------------------
        if isinstance(story_key, (tuple, list)):
            release = str(story_key[0])
            story = str(story_key[1])
        else:
            story = str(story_key)
            release_val = story_to_release.get(story, "")
            if isinstance(release_val, (tuple, list)):
                release = str(release_val[0])
            else:
                release = str(release_val)

        story_clean = story.strip()

        for test_id in sorted(planned_tests):

            test_clean = str(test_id).strip()

            if test_clean in exec_by_test.groups:
                exec_rows = df_exec.loc[exec_by_test.groups[test_clean]]

                for _, r in exec_rows.iterrows():

                    exec_story = str(r["Story"]).strip()

                    # --------------------------------------------------
                    # ✅ CORRECT ALIGNMENT LOGIC
                    # --------------------------------------------------
                    aligned = "YES" if exec_story == story_clean else "NO"

                    rows.append({
                        "Release": release,
                        "Story": story_clean,
                        "Test ID": test_clean,
                        "Exec File": r["File"],
                        "Sheet": r["Sheet"],
                        "Status": r.get("Test Result", r.get("Status", "")),
                        "Aligned": aligned,
                        "Execution Location": exec_story,
                    })

            else:
                # --------------------------------------------------
                # Test never executed anywhere
                # --------------------------------------------------
                rows.append({
                    "Release": release,
                    "Story": story_clean,
                    "Test ID": test_clean,
                    "Exec File": "",
                    "Sheet": "",
                    "Status": "NOT EXECUTED",
                    "Aligned": "NO",
                    "Execution Location": "",
                })

    return pd.DataFrame(rows)

def _build_summary(story_to_tests, df_exec, pass_values, story_to_release):

    df_exec = df_exec.copy()

    df_exec.columns = [c.strip() for c in df_exec.columns]
    df_exec["Evidence"] = df_exec["Evidence"].astype(str).str.strip().str.lower()

    df_exec["StatusClass"] = df_exec["Status"].apply(
        lambda s: classify_status(s, pass_values)
    )

    # --------------------------------------------------
    # GLOBAL execution set
    # --------------------------------------------------
    all_executed = set(
        df_exec["Test ID"]
        .dropna()
        .astype(str)
        .str.strip()
    )

    summary_rows = []

    for story, planned_tests in sorted(story_to_tests.items()):

        group = df_exec[df_exec["Story"] == story]

        planned = set(planned_tests)

        executed_in_story = set(
            group["Test ID"]
            .dropna()
            .astype(str)
            .str.strip()
        )

        # --------------------------------------------------
        # TRACEABILITY (CORRECT)
        # --------------------------------------------------
        genuine_missing = planned - all_executed
        misaligned = (planned - executed_in_story) & all_executed

        if genuine_missing:
            traceability = "🔴 Tests missing"
        elif misaligned:
            traceability = "🟡 Tests present (not linked)"
        else:
            traceability = "🟢 Tests present"

        # --------------------------------------------------
        # EXECUTION COUNT (ACTUAL)
        # --------------------------------------------------
        total_exec = len(executed_in_story)

        # --------------------------------------------------
        # STATUS COUNTS (story-local)
        # --------------------------------------------------
        status_counts = group["StatusClass"].value_counts()

        passed = status_counts.get("PASS", 0)
        failed = status_counts.get("FAIL", 0)
        in_progress = status_counts.get("IN_PROGRESS", 0)
        not_started = status_counts.get("NOT_STARTED", 0)

        # --------------------------------------------------
        # EVIDENCE
        # --------------------------------------------------
        passed_with_evidence = len(group[
            (group["StatusClass"] == "PASS") &
            (group["Evidence"] == "yes")
        ])

        # --------------------------------------------------
        # EXEC STATUS
        # --------------------------------------------------
        exec_status = _derive_exec_status(
            total_exec,
            passed,
            failed,
            in_progress,
            not_started,
            passed_with_evidence
        )

        # --------------------------------------------------
        # ISSUE BUILDING (CLEAN)
        # --------------------------------------------------
        issues = []

        if genuine_missing:
            issues.append(f"Missing: {', '.join(sorted(genuine_missing))}")

        if misaligned:
            issues.append(f"Misaligned: {', '.join(sorted(misaligned))}")

        extra = executed_in_story - planned
        if extra:
            issues.append(f"Extra: {', '.join(sorted(extra))}")

        failed_tests = group[group["StatusClass"] == "FAIL"]["Test ID"].tolist()
        if failed_tests:
            issues.append(f"Failed: {', '.join(sorted(set(failed_tests)))}")

        missing_evidence_tests = group[
            (group["StatusClass"] == "PASS") &
            (group["Evidence"] == "no")
        ]["Test ID"].tolist()

        if missing_evidence_tests:
            issues.append(f"Missing evidence: {', '.join(sorted(set(missing_evidence_tests)))}")

        issue_text = " | ".join(issues) if issues else ""

        # --------------------------------------------------
        # RELEASE
        # --------------------------------------------------
        release = story_to_release.get(story, "UNKNOWN")

        # --------------------------------------------------
        # APPEND
        # --------------------------------------------------
        summary_rows.append({
            "Release": release,
            "Story": story,
            "Traceability": traceability,
            "Exec Status": exec_status,
            "Issue": issue_text,
            "Planned Tests": len(planned),
            "Execution Tests": total_exec,
            "Passed": int(passed),
            "Failed": int(failed),
            "In Progress": int(in_progress),
            "Not Started": int(not_started),
            "Passed w/ Evidence": int(passed_with_evidence)
        })

    return pd.DataFrame(summary_rows).sort_values(["Release", "Story"])

def _build_traceability_gaps(df_exec, story_to_tests, story_to_release):
    rows = []

    # --------------------------------------------------
    # ALL executed tests across ALL stories
    # --------------------------------------------------
    all_exec_tests = set(
        df_exec["Test ID"]
        .dropna()
        .astype(str)
    )

    for story, planned_tests in sorted(story_to_tests.items()):

        group = df_exec[df_exec["Story"] == story]

        exec_tests = set(group["Test ID"].dropna().astype(str))
        planned_tests = set(planned_tests)

        # --------------------------------------------------
        # MISALIGNED (executed, but not under this story)
        # --------------------------------------------------
        misaligned = (planned_tests - exec_tests) & all_exec_tests

        # --------------------------------------------------
        # TRUE MISSING (not executed anywhere)
        # --------------------------------------------------
        genuine_missing = planned_tests - all_exec_tests

        # --------------------------------------------------
        # STORY MISSING (includes misaligned)
        # --------------------------------------------------
        story_missing = genuine_missing.union(misaligned)

        # --------------------------------------------------
        # EXTRA (executed under story but not planned)
        # --------------------------------------------------
        extra = exec_tests - planned_tests

        # --------------------------------------------------
        # EXECUTION (aligned + misaligned)
        # --------------------------------------------------
        # --- DISPLAY (what actually ran here)
        execution_tests_display = exec_tests

        # --- COVERAGE (used for counts)
        execution_tests_coverage = (planned_tests & exec_tests) | misaligned

        # Try to get source info
        if not group.empty:
            source_file = group["File"].iloc[0]
            source_sheet = group["Sheet"].iloc[0]
        else:
            source_file = ""
            source_sheet = ""

        rows.append({
            "Release": story_to_release.get(story, ""),
            "Story": story,
            "Source File": source_file,
            "Sheet": source_sheet,
            "Planned Tests": ", ".join(sorted(planned_tests)),
            "Execution Tests": ", ".join(sorted(execution_tests_display)),
            "Missing Tests": ", ".join(sorted(story_missing)),
            "Misaligned Tests": ", ".join(sorted(misaligned)),
            "Extra Tests": ", ".join(sorted(extra)),
            "Planned Count": len(planned_tests),
            "Execution Count": len(execution_tests_coverage),
            "Missing Count": len(story_missing),
            "Extra Count": len(extra),
            "Has Gap": any([
                len(story_missing) > 0,
                len(extra) > 0,
                len(misaligned) > 0
            ]),
        })

    return pd.DataFrame(rows)

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

        
    # Convert (release, story) → story_to_tests
    story_to_tests_flat = {}

    for (release, story), tests in story_to_tests.items():
        story_to_tests_flat.setdefault(story, set()).update(tests)

    df_summary = _build_summary(
        story_to_tests_flat,
        df_exec,
        pass_values,
        story_to_release   
    )

    df_gaps = _build_traceability_gaps(
        df_exec,
        story_to_tests_flat,
        story_to_release   #
    )

    df_missing=_df_from_set('MissingTest', result.missing_tests)
    df_extra=_df_from_set('ExtraTest', result.extra_tests)

    st_rows = [
    (s, t)
    for s, tests in sorted(story_to_tests_flat.items())
    for t in sorted(tests)
    ]
    
    df_story_map=pd.DataFrame(st_rows, columns=['Story','Test'])
    df_plan_raw=pd.DataFrame(plan_raw_rows, columns=['StoryCell','RowText','TestCell'])
    
    output_path=Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with pd.ExcelWriter(output_path, engine='openpyxl') as xw:
        df_summary.to_excel(xw, sheet_name='Summary', index=False)
        df_gaps.to_excel(xw, sheet_name="Traceability Gaps", index=False)
        df_missing.to_excel(xw, sheet_name='Missing', index=False)
        df_extra.to_excel(xw, sheet_name='Extra', index=False)
        df_story_map.to_excel(xw, sheet_name='Story_To_Test_Map', index=False)
        df_exec.to_excel(xw, sheet_name='Execution_Attachments', index=False)
       
        df_detail = _build_execution_detail(df_exec, story_to_tests, story_to_release)
        df_detail.to_excel(xw, sheet_name="Execution_Detail", index=False)
        
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
