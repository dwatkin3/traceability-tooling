from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass
import pandas as pd
import re


@dataclass
class ExecRow:
    sheet: str
    row: int
    story: Optional[str]
    test: str
    status: str
    file: str


@dataclass
class ExecParseResult:
    rows: List[ExecRow]


def _find_candidate_column(columns: List[str], candidates: List[str]) -> Optional[int]:
    cols_lower = [str(c).strip().lower() for c in columns]

    # Exact match first
    for cand in candidates:
        cand = cand.lower()
        for i, col in enumerate(cols_lower):
            if cand == col:
                return i

    # Fallback: partial match
    for cand in candidates:
        cand = cand.lower()
        for i, col in enumerate(cols_lower):
            if cand in col:
                return i

    return None


def _extract_with_patterns(text: str, patterns: List[str]) -> Optional[str]:
    for p in patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            return m.group(0).upper()
    return None


def parse_execution_xlsx(
    path: Path,
    story_col_candidates: List[str],
    test_col_candidates: List[str],
    story_patterns: List[str],
    testid_patterns: List[str],
    status_col_candidates: List[str],
    ignore_sheets: List[str],
) -> ExecParseResult:

    print("\nFILE BEING READ:", path.resolve())

    all_rows: List[ExecRow] = []

    xls = pd.ExcelFile(path)

    for sheet in xls.sheet_names:

        sheet_lower = str(sheet).lower()
        if any(ig in sheet_lower for ig in ignore_sheets):
            print(f"Skipping sheet '{sheet}' (ignored)")
            continue

        try:
            df = pd.read_excel(
                path,
                sheet_name=sheet,
                engine="openpyxl",
                dtype=str,
                keep_default_na=False
            )

            # Clean all values
            df = df.apply(lambda col: col.astype(str).str.strip())

        except Exception as e:
            print(f"Failed reading sheet {sheet}: {e}")
            continue

        if df.empty:
            continue


        df_cols = list(df.columns)

        idx_test = _find_candidate_column(df_cols, test_col_candidates)
        idx_story = _find_candidate_column(df_cols, story_col_candidates)
        idx_status = _find_candidate_column(df_cols, status_col_candidates)

        for ridx, row in df.iterrows():

            if row.isna().all():
                continue

            # ---------------- STATUS ----------------
            status_val = ""
            if idx_status is not None and idx_status < len(row):
                status_val = str(row.iloc[idx_status] or "").strip()

            # ---------------- TEST ID ----------------
            test_val = None

            if idx_test is not None and idx_test < len(row):

                test_val = str(row.iloc[idx_test] or "").strip()

            # Fallback extraction
            if not test_val:
                combined = " ".join([str(v) for v in row.values if pd.notna(v)])
                test_val = _extract_with_patterns(combined, testid_patterns)

            if not test_val:
                continue

            # ---------------- STORY ----------------
            story_val = None

            if idx_story is not None and idx_story < len(row):
                story_val = str(row.iloc[idx_story] or "").strip()

            if not story_val:
                combined = " ".join([str(v) for v in row.values if pd.notna(v)])
                story_val = _extract_with_patterns(combined, story_patterns)

            story = (story_val or "").strip()
            test_id = (test_val or "").strip()

            if not story or not test_id:
                continue

            if story.lower() == "nan" or test_id.lower() == "nan":
                continue

            stories = re.findall(r"STRY\d+", story)

            if not stories:
                continue

            for s in stories:
                all_rows.append(
                    ExecRow(
                        sheet=sheet,
                        row=int(ridx) + 2,
                        story=s,
                        test=test_id,
                        status=status_val,
                        file=path.name,
                    )
                )

    return ExecParseResult(rows=all_rows)