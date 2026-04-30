from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass
import pandas as pd
import re
from .id_normaliser import normalise_text, normalise_id


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
    """
    Find the index of a column whose name matches one of the candidate names.

    Matching strategy:
    1. Exact match (case-insensitive, trimmed)
    2. Partial match (candidate contained within column name)

    Returns:
        Index of matching column, or None if no match found.
    """

    # --------------------------------------------------
    # Normalise columns ONCE (lowercase + trimmed)
    # --------------------------------------------------
    cols_norm = [str(c).strip().lower() for c in columns]

    # Normalise candidates once (avoids repeated work)
    candidates_norm = [str(c).strip().lower() for c in candidates]

    # --------------------------------------------------
    # 1. Exact match (preferred)
    # --------------------------------------------------
    for cand in candidates_norm:
        for idx, col in enumerate(cols_norm):
            if col == cand:
                return idx

    # --------------------------------------------------
    # 2. Partial match (fallback)
    # --------------------------------------------------
    for cand in candidates_norm:
        for idx, col in enumerate(cols_norm):
            if cand in col:
                return idx

    return None

def _extract_with_patterns(text: str, patterns: List[str]) -> Optional[str]:
    """
    Attempt to extract a value from text using a list of regex patterns.

    Returns the first match found, normalised as an ID.
    """

    # --------------------------------------------------
    # Guard against None / empty input
    # --------------------------------------------------
    if not text:
        return None

    text = str(text)

    # --------------------------------------------------
    # Try each pattern in order
    # --------------------------------------------------
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            # --------------------------------------------------
            # Normalise using shared ID normaliser
            # (removes whitespace + uppercases consistently)
            # --------------------------------------------------
            return normalise_id(match.group(0))

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

        # --------------------------------------------------
        # Skip ignored sheets (normalised text comparison)
        # --------------------------------------------------
        sheet_lower = normalise_text(sheet).lower()
        if any(ig in sheet_lower for ig in ignore_sheets):
            print(f"Skipping sheet '{sheet}' (ignored)")
            continue

        try:
            df = pd.read_excel(
                path,
                sheet_name=sheet,
                engine="openpyxl",
                dtype=str,
                keep_default_na=False,
            )

            if df.empty:
                continue

            # --------------------------------------------------
            # Normalise columns + all cell text ONCE
            # --------------------------------------------------
            df.columns = [normalise_text(c) for c in df.columns]

            for col in df.columns:
                df[col] = df[col].map(normalise_text)

        except Exception as e:
            print(f"Failed reading sheet {sheet}: {e}")
            continue

        df_cols = list(df.columns)

        idx_test = _find_candidate_column(df_cols, test_col_candidates)
        idx_story = _find_candidate_column(df_cols, story_col_candidates)
        idx_status = _find_candidate_column(df_cols, status_col_candidates)

        for ridx, row in df.iterrows():

            # --------------------------------------------------
            # Skip completely empty rows
            # --------------------------------------------------
            if not any(row):
                continue

            # --------------------------------------------------
            # STATUS (text field → normalise_text)
            # --------------------------------------------------
            status_val = ""
            if idx_status is not None and idx_status < len(row):
                status_val = normalise_text(row.iloc[idx_status])

            # --------------------------------------------------
            # TEST ID (identifier → normalise_id)
            # --------------------------------------------------
            test_val = None

            if idx_test is not None and idx_test < len(row):
                test_val = normalise_id(row.iloc[idx_test])

            # Fallback extraction from entire row
            if not test_val:
                combined = " ".join([normalise_text(v) for v in row.values if v])
                test_val = _extract_with_patterns(combined, testid_patterns)

            if not test_val:
                continue

            # --------------------------------------------------
            # STORY (identifier → normalise_id)
            # --------------------------------------------------
            story_val = None

            if idx_story is not None and idx_story < len(row):
                story_val = normalise_id(row.iloc[idx_story])

            # Fallback extraction
            if not story_val:
                combined = " ".join([normalise_text(v) for v in row.values if v])
                story_val = _extract_with_patterns(combined, story_patterns)

            if not story_val:
                continue

            story = story_val
            test_id = test_val

            # --------------------------------------------------
            # STORY EXTRACTION (handles multiple STRY IDs)
            # --------------------------------------------------
            stories = re.findall(r"STRY\d+", story)

            if stories:
                # Standard case: one or more valid story IDs
                for s in stories:
                    all_rows.append(
                        ExecRow(
                            sheet=normalise_text(sheet),
                            row=int(ridx) + 2,
                            story=normalise_id(s),
                            test=test_id,
                            status=status_val,
                            file=path.name,
                        )
                    )
            else:
                # Non-standard story (e.g. NEGATIVE, N/A)
                # Keep but normalise as ID for consistency
                all_rows.append(
                    ExecRow(
                        sheet=normalise_text(sheet),
                        row=int(ridx) + 2,
                        story=normalise_id(story),
                        test=test_id,
                        status=status_val,
                        file=path.name,
                    )
                )

    return ExecParseResult(rows=all_rows)