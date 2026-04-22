# plan_parser.py

from __future__ import annotations
from pathlib import Path
from typing import Dict, List, Set, Tuple
import re
from collections import defaultdict
from docx import Document
from .range_expander import expand_ranges
from .id_normaliser import normalise_id

# -----------------------------
# ID PATTERNS (single source of truth)
# -----------------------------
STORY_PATTERN = r"\bSTRY\d{7}\b"

STORY_RE = re.compile(STORY_PATTERN)
_SPLIT_RE = re.compile(r"[\s,;]+")

class PlanParseResult:
    def __init__(self, story_to_tests: Dict[str, Set[str]], raw_rows: List[Tuple[str,str,str]]):
        self.story_to_tests = story_to_tests
        self.raw_rows = raw_rows  # (stories_csv, row_text, test_cell_text)

def _extract_story_ids(text: str) -> List[str]:
    if not text:
        return []
    return STORY_RE.findall(normalise_id(text))

def _extract_test_tokens(text: str) -> List[str]:
    if not text:
        return []

    # 🔥 NORMALISE DASHES
    text = text.replace("–", "-").replace("—", "-")

    toks = [t for t in _SPLIT_RE.split(text) if t]
    return [normalise_id(t) for t in toks]

def _extract_tests_from_cell(cell_text: str) -> Set[str]:
    if not cell_text:
        return set()

    # --------------------------------------------------
    # NORMALISE DASHES
    # --------------------------------------------------
    text = cell_text.replace("–", "-").replace("—", "-")

    results = set()

    # --------------------------------------------------
    # 1. EXPAND RANGES FIRST (before splitting)
    # --------------------------------------------------
    range_matches = re.findall(r"\b([A-Z]{2,}\d+)\s*-\s*([A-Z]{2,}\d+)\b", text)

    for start, end in range_matches:
        results.update(expand_ranges([f"{start}-{end}"]))

    # Remove ranges from text so we don’t double-count
    text = re.sub(r"\b[A-Z]{2,}\d+\s*-\s*[A-Z]{2,}\d+\b", "", text)

    # --------------------------------------------------
    # 2. EXTRACT INDIVIDUAL TEST IDS
    # --------------------------------------------------
    singles = re.findall(r"\b(?!STRY)[A-Z]{2,}\d+\b", text)

    results.update(normalise_id(t) for t in singles)

    return results


RE_RELEASE = re.compile(r"(RLSE\d{7}\s+.+)", re.IGNORECASE)
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

                # Assume STORY ID is in column 0
                story_cell = cells[0] if len(cells) > 0 else ""
                stories = _extract_story_ids(story_cell)

                if not stories:
                    continue

                test_cell = cells[-1] if cells else ""
                tests = _extract_tests_from_cell(test_cell)

                for story in stories:
                    key = (current_release, story)

                    # 🔥 ALWAYS create the mapping
                    if tests:
                        release_story_to_tests[key].update(tests)
                    else:
                        release_story_to_tests.setdefault(key, set())

                    story_to_release[story] = current_release

                raw_rows.append((
                    ",".join(stories),
                    row_text,
                    test_cell
                ))

    if not release_story_to_tests:
        raise ValueError(
            f"Plan parsing produced zero (release, story) mappings for {path}"
        )

    return release_story_to_tests, story_to_release, raw_rows

