from __future__ import annotations
from pathlib import Path
from typing import List
import re
import pandas as pd
from .id_normaliser import normalise_id

class ExecRow:
    __slots__ = ('sheet','row','story','test','file')
    def __init__(self, sheet: str, row: int, story: str, test: str, file: str):
        self.sheet = sheet
        self.row = row
        self.story = story
        self.test = test
        self.file = file

class ExecParseResult:
    def __init__(self, rows: List[ExecRow]):
        self.rows = rows

def _find_candidate_column(columns: List[str], candidates: List[str]) -> int | None:
    cols_norm = [normalise_id(c) for c in columns]
    cands = [normalise_id(c) for c in candidates]
    for i, cn in enumerate(cols_norm):
        for cand in cands:
            if cand and cand in cn:
                return i
    return None

def parse_execution_xlsx(path: Path, story_col_candidates: List[str], test_col_candidates: List[str], story_patterns: List[str], testid_patterns: List[str]) -> ExecParseResult:
    xl = pd.ExcelFile(path)
    rows: List[ExecRow] = []

    SKIP_SHEETS = { 'SUMMARY','DASHBOARD','OVERALL DASHBOARD','PHASE 6 DASHBOARD','PHASE 7 DASHBOARD','ACQUISITIVE CRIME DASHBOARD','VALIDATION','DEFECTS','SHEET1','SHEET2'}

    for sheet in xl.sheet_names:
        if sheet.strip().upper() in SKIP_SHEETS:
            continue
        try:
            df = xl.parse(sheet)
        except Exception:
            continue
        if df.empty:
            continue
        df_cols = list(map(str, df.columns))
        idx_test = _find_candidate_column(df_cols, test_col_candidates)
        idx_story = _find_candidate_column(df_cols, story_col_candidates)
        for ridx, row in df.iterrows():
            if row.isna().all():
                continue
            # test
            test = ''
            if idx_test is not None and idx_test < len(row):
                test = normalise_id(str(row.iloc[idx_test] or ''))
            if not test:
                text = ' '.join(map(lambda v: '' if v is None else str(v), row.values))
                if any(ch.isalnum() for ch in text):
                    for pat in testid_patterns:
                        m = re.search(pat, text, flags=re.IGNORECASE)
                        if m:
                            test = normalise_id(m.group(0)); break
            if not test:
                continue
            # story (optional)
            story = ''
            if idx_story is not None and idx_story < len(row):
                sval = normalise_id(str(row.iloc[idx_story] or ''))
                ms = re.findall(r"STRY\d{3,}", sval)
                if ms: story = ms[0]
            rows.append(ExecRow(sheet=sheet, row=int(ridx), story=story, test=test, file=Path(path).name))
    return ExecParseResult(rows)
