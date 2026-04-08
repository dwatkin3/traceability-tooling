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
        res=parse_execution_xlsx(xf, hints.story_column_candidates, hints.testid_column_candidates, patterns.story_patterns, patterns.testid_patterns)
        for r in res.rows:
            exec_rows.append((r.sheet, int(r.row), r.story or '', r.test, r.file))
            exec_test_ids.add(r.test)
            if r.story:
                exec_story_refs.add(r.story)
    smap=StoryMap(plan.story_to_tests)
    result=reconcile(smap.story_to_tests, exec_test_ids, exec_story_refs, settings.red_on_extra)
    release_id=root_dir.name
    out_folder=Path('outputs')/release_id
    out_folder.mkdir(parents=True, exist_ok=True)
    fname=f'Traceability_Reconciliation_{release_id}.xlsx'
    out_f=output_path or (out_folder/fname)
    write_output(out_f, plan.raw_rows, exec_rows, smap.story_to_tests, result, include_audit=settings.enable_audit_sheets, debug_dir=out_folder/'debug')
    return {"output": str(Path(out_f).resolve())}
