# plan_parser.py

from __future__ import annotations
from pathlib import Path
from typing import Dict, List, Set, Tuple
import re
from collections import defaultdict
from docx import Document
from .range_expander import expand_ranges
from .id_normaliser import normalise_id, normalise_text
from docx.document import Document as DocxDocument
from docx.table import Table
from docx.text.paragraph import Paragraph
from docx.oxml.table import CT_Tbl
from docx.oxml.text.paragraph import CT_P


# -----------------------------
# ID PATTERNS (single source of truth)
# -----------------------------
STORY_PATTERN = r"\bSTRY\d+\b"

STORY_RE = re.compile(STORY_PATTERN)
_SPLIT_RE = re.compile(r"[\s,;]+")

class PlanParseResult:
    def __init__(self, story_to_tests: Dict[str, Set[str]], raw_rows: List[Tuple[str,str,str]]):
        self.story_to_tests = story_to_tests
        self.raw_rows = raw_rows  # (stories_csv, row_text, test_cell_text)

def _extract_story_ids(text: str) -> List[str]:
    if not text:
        return []
    return [
	normalise_id(s)
	for s in STORY_RE.findall(text)
	]

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
    range_matches = re.findall(
        r"\b([A-Z]{2,}\d+)\s*-\s*([A-Z]{2,}\d+)\b",
        text
    )

    for start, end in range_matches:
        results.update(expand_ranges([f"{start}-{end}"]))

    # Remove ranges from text so we don’t double-count
    text = re.sub(
        r"\b[A-Z]{2,}\d+\s*-\s*[A-Z]{2,}\d+\b",
        "",
        text
    )

    # --------------------------------------------------
    # 2. EXTRACT INDIVIDUAL TEST IDS
    # Supports:
    # AU12
    # IS01A
    # TP-CREW-01
    # --------------------------------------------------
    singles = re.findall(
        r"\b(?!STRY)[A-Z]+(?:-[A-Z]+)*-\d+[A-Z]*\b|\b(?!STRY)[A-Z]{2,}\d+[A-Z]*\b",
        text
    )

    results.update(normalise_id(t) for t in singles)

    return results


RE_RELEASE = re.compile(r"RLSE\d{7}", re.IGNORECASE)
RE_RELEASE_IDENTIFIER = re.compile(
	r"Release Identifier:\s*(.+)",
	re.IGNORECASE
)
RE_TEST_ID = re.compile(
    r"\b(?!STRY)[A-Z]+(?:-[A-Z]+)*-\d+[A-Z]*\b|\b(?!STRY)[A-Z]{2,}\d+[A-Z]*\b"
)

def iter_block_items(parent):
	"""
	Yield paragraphs and tables in document order.
	"""

	if isinstance(parent, DocxDocument):
		parent_elm = parent.element.body
	else:
		parent_elm = parent._element

	for child in parent_elm.iterchildren():

		if isinstance(child, CT_P):
			yield Paragraph(child, parent)

		elif isinstance(child, CT_Tbl):
			yield Table(child, parent)


def parse_plan_docx_with_release(path: Path):

	doc = Document(str(path))

	release_story_to_tests = defaultdict(set)
	story_to_release = {}
	raw_rows = []

	current_release = None

	for block in iter_block_items(doc):

		# --------------------------------------------------
		# PARAGRAPHS = release context
		# --------------------------------------------------
		if isinstance(block, Paragraph):

			text = normalise_text(block.text)

			if not text:
				continue

			# --------------------------------------------------
			# Legacy RLSE release identifiers
			# --------------------------------------------------
			release_matches = RE_RELEASE.findall(text)

			if release_matches:
				current_release = normalise_id(
					release_matches[0]
				)

			# --------------------------------------------------
			# New descriptive release identifiers
			# --------------------------------------------------
			else:

				release_identifier = (
					RE_RELEASE_IDENTIFIER.search(text)
				)

				if release_identifier:

					current_release = normalise_text(
						release_identifier.group(1)
					)

					print(
						f"Detected release identifier: "
						f"{current_release}"
					)

			if release_matches:
				current_release = normalise_id(release_matches[0])

			continue

		# --------------------------------------------------
		# TABLES = mappings
		# --------------------------------------------------
		if isinstance(block, Table):

			for row in block.rows:

				row_text = " ".join(
					cell.text.strip()
					for cell in row.cells
					if cell.text.strip()
				)

				row_text = normalise_text(row_text)

				if not row_text:
					continue

				stories = _extract_story_ids(row_text)

				if not stories:
					continue

				tests = _extract_tests_from_cell(row_text)

				for story in stories:

					release_value = current_release or "UNKNOWN"

					key = (release_value, story)

					if tests:
						release_story_to_tests[key].update(tests)
					else:
						release_story_to_tests.setdefault(key, set())

					story_to_release[story] = release_value

				raw_rows.append((
					",".join(sorted(stories)),
					row_text,
					row_text
				))

	if not release_story_to_tests:
		raise ValueError(
			f"No STORY mappings found in {path}"
		)

	return (
		dict(release_story_to_tests),
		story_to_release,
		raw_rows
	)

def parse_plan_documents(plan_files):
	"""
	Aggregate multiple specification documents into a single
	release/story/test structure.
	"""

	combined_story_to_tests = defaultdict(set)
	combined_story_to_release = {}
	combined_raw_rows = []

	for plan_file in plan_files:

		path = Path(plan_file)

		(
			story_to_tests,
			story_to_release,
			raw_rows
		) = parse_plan_docx_with_release(path)

		# --------------------------------------------------
		# Merge story -> tests
		# --------------------------------------------------
		for key, tests in story_to_tests.items():
			combined_story_to_tests[key].update(tests)

		# --------------------------------------------------
		# Merge story -> release
		# --------------------------------------------------
		combined_story_to_release.update(
			story_to_release
		)

		# --------------------------------------------------
		# Merge raw rows
		# --------------------------------------------------
		combined_raw_rows.extend(raw_rows)

	return (
		dict(combined_story_to_tests),
		combined_story_to_release,
		combined_raw_rows
	)