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

def _build_summary(story_to_tests: Dict[str, Set[str]], df_exec: pd.DataFrame) -> pd.DataFrame:
    rows=[]
    for story, planned_set in sorted(story_to_tests.items()):
        planned=set(planned_set)
        # only THIS story's execution rows
        exec_rows=set(df_exec.loc[df_exec['story']==story,'test'].dropna().astype(str))

        executed = set(
                        df_exec[
                         (df_exec['story'] == story) &
                          (df_exec['Status'].str.lower().isin(['passed', 'pass', 'complete']))
                                ]['test'].dropna().astype(str)
)
        covered=planned & executed
        missing=planned - executed
        extra_tests=executed - planned
        planned_fams={_family(t) for t in planned}
        extra_same={t for t in extra_tests if _family(t) in planned_fams}
        extra_diff={t for t in extra_tests if _family(t) not in planned_fams}
        extra_fams={_family(t) for t in extra_tests}
        if missing:
            status='RED'; reason='MISSING_PLANNED'
        elif extra_diff:
            status='AMBER'; reason='CROSS_FAMILY_EXTRA_TESTS'
        elif extra_same:
            status='AMBER'; reason='SAME_FAMILY_EXTRA_TESTS'
        else:
            status='GREEN'; reason='ALL_PLANNED_EXECUTED'
        rows.append({
            'story':story,
            'status':status,
            'planned':len(planned),
            'executed':len(executed),
            'covered':len(covered),
            'missing':len(missing),
            'planned_list':_join(planned),
            'executed_list':_join(executed),
            'missing_list':_join(missing),
            'extra_list':_join(extra_tests),
            'extra_same_family_list':_join(extra_same),
            'extra_diff_family_list':_join(extra_diff),
            'extra_families':_join(extra_fams),
            'status_reason':reason
        })
    return pd.DataFrame(rows)

def write_output(output_path: Path, plan_raw_rows, exec_rows, 
                 story_to_tests, result, df_exec=None, 
                 include_audit=True, debug_dir=None):
    
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

    df_summary=_build_summary(story_to_tests, df_exec)
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
