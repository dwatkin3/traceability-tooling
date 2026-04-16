from __future__ import annotations
from pathlib import Path
from typing import Dict, List, Set, Tuple
import re
from collections import defaultdict
from docx import Document
from .range_expander import expand_ranges
from .id_normaliser import normalise_id


class PlanParseResult:
    def __init__(self, story_to_tests: Dict[str, Set[str]], raw_rows: List[Tuple[str,str,str]]):
        self.story_to_tests = story_to_tests
        self.raw_rows = raw_rows  # (stories_csv, row_text, test_cell_text)

_STORY_RE = re.compile(r"STRY\d{3,}")
_SPLIT_RE = re.compile(r"[\s,;]+")

def _extract_story_ids(text: str) -> List[str]:
    if not text:
        return []
    return _STORY_RE.findall(normalise_id(text))

def _extract_test_tokens(text: str) -> List[str]:
    if not text:
        return []
    toks = [t for t in _SPLIT_RE.split(text) if t]
    return [normalise_id(t) for t in toks]

def _extract_tests_from_cell(cell_text: str) -> Set[str]:
    return expand_ranges(_extract_test_tokens(cell_text))

def parse_plan_docx(path: Path) -> PlanParseResult:
    doc = Document(str(path))
    story_to_tests: Dict[str, Set[str]] = defaultdict(set)
    raw_rows: List[Tuple[str,str,str]] = []

    for tbl in doc.tables:
        headers = [cell.text.strip() for cell in tbl.rows[0].cells] if tbl.rows else []
        col_story = None; col_test = None
        for idx, h in enumerate(headers):
            h_norm = normalise_id(h)
            if col_story is None and ('STORY' in h_norm or h_norm.startswith('STRY')):
                col_story = idx
            if col_test is None and ('TEST' in h_norm or 'SCENARIO' in h_norm or h_norm=='ID'):
                col_test = idx
        for r in tbl.rows[1:]:
            cells = [c.text for c in r.cells]
            story_cell = cells[col_story] if col_story is not None and col_story < len(cells) else ''
            test_cell  = cells[col_test]  if col_test  is not None and col_test  < len(cells) else ''
            row_text = ' '.join(cells)
            stories = _extract_story_ids(story_cell or row_text)
            tests   = _extract_tests_from_cell(test_cell)
            if stories and tests:
                for s in stories:
                    story_to_tests[s].update(tests)
                raw_rows.append((','.join(stories), row_text, test_cell))
    return PlanParseResult(story_to_tests, raw_rows)

# plan_parser.py

RE_RELEASE = re.compile(r"(RLSE\d{7}\s+.+)", re.IGNORECASE)
RE_STORY = re.compile(r"(STRY\d+)")
RE_TEST_ID = re.compile(r"\b(?!STRY)[A-Z]{2,}\d+[A-Z]*\b")

def parse_plan_docx_with_release(path: Path):

    doc = Document(str(path))

    release_story_to_tests = defaultdict(set)
    story_to_release = {}
    raw_rows = []

    current_release = None
    
    tables = iter(doc.tables)

    # Walk document body in order (paragraphs + tables)
    for block in doc.element.body:

        # ---------- PARAGRAPH ----------
        if block.tag.endswith('}p'):
            text = block.text.strip()

            m = RE_RELEASE.search(text)

            if m:
                print("RAW PARAGRAPH TEXT:", repr(text))    
                release_text = m.group(0).strip()
                if release_text != current_release:
                    current_release = release_text
                continue

        # ---------- TABLE ----------
        if block.tag.endswith('}tbl'):
            table = next(tables)

            if not current_release:
                continue  # tables before first RLSE header are ignored

            for row in table.rows:
                cells = [c.text.strip() for c in row.cells]
                row_text = " ".join(cells)

                stories = _extract_story_ids(row_text)
                if not stories:
                    continue

                tests = _extract_tests_from_cell(cells[-1] if cells else "")
                if not tests:
                    continue

                for story in stories:
                    release_story_to_tests[(current_release, story)].update(tests)
                    story_to_release[story] = current_release
                    raw_rows.append((
                        ",".join(stories),
                        row_text,
                        cells[-1] if cells else ""
                    ))

    if not release_story_to_tests:
        raise ValueError(
            f"Plan parsing produced zero (release, story) mappings for {path}"
        )

    return release_story_to_tests, story_to_release, raw_rows

