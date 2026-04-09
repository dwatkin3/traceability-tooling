from __future__ import annotations
import json
from pathlib import Path
from .settings_loader import load_settings
from .patterns_loader import load_patterns
from .column_hints_loader import load_column_hints
from .plan_parser import parse_plan_docx
from .exec_parser import parse_execution_xlsx
from .story_mapper import StoryMap
from .reconcile import reconcile
from .audit_writer import write_output

def derive_test_result(status, has_evidence, pass_values):
    s = (status or "").lower().strip()
    pass_values = [p.lower().strip() for p in pass_values]

    # PASS logic (from config)
    is_pass = any(p == s for p in pass_values)

    # FAIL logic (anything meaningful but not pass)
    is_fail = s and not is_pass

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
    plan=parse_plan_docx(plan_file)
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
            print(f"DEBUG ROW → story={r.story} test={r.test}")

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
    

    # ✅ FINAL DEBUG (only once)
    print(f"\nFINAL DEBUG: collected {len(exec_rows)} execution rows")
    print("Sample:", exec_rows[:5])


    smap = StoryMap(plan.story_to_tests)

    result = reconcile(
        smap.story_to_tests,
        exec_test_ids,
        exec_story_refs,
        settings.red_on_extra
)
    # -----------------------------
    # Build enriched execution data
    # -----------------------------
    import pandas as pd

    df_exec = pd.DataFrame(exec_rows, columns=[
        "Sheet", "Row", "Story", "Test ID", "Status", "File"
    ])

    # --- Simple evidence check (filename contains Test ID) ---
    evidence_files = []
    evidence_dir = root_dir / "evidence"

    if evidence_dir.exists():
        for p in evidence_dir.rglob("*"):
            evidence_files.append(p.name.lower())

    def has_evidence(test_id):
        t = str(test_id).lower()
        return any(t in f for f in evidence_files)

    df_exec["Evidence"] = df_exec["Test ID"].apply(
        lambda t: "Yes" if has_evidence(t) else "No"
    )

    # --- Apply your new function ---
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

    print("DF_EXEC COLUMNS:", df_exec.columns.tolist())
    write_output(
    out_f,
    plan.raw_rows,
    exec_rows,
    smap.story_to_tests,
    result,
    df_exec=df_exec, 
    include_audit=settings.enable_audit_sheets,
    debug_dir=out_folder/'debug'
)
    return {"output": str(Path(out_f).resolve())}
