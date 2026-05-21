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
    text = (
        cell_text
        .replace("–", "-")
        .replace("—", "-")
    )

    results = set()

    # --------------------------------------------------
    # 1. FULL TOKEN RANGE EXPANSION
    # Supports:
    # AU01-AU05
    # TP-OPT-01-TP-OPT-03
    # --------------------------------------------------
    full_range_re = re.compile(
        r"\b([A-Z]+(?:-[A-Z]+)*\d+[A-Z]*)"
        r"\s*-\s*"
        r"([A-Z]+(?:-[A-Z]+)*\d+[A-Z]*)\b"
    )

    for match in full_range_re.finditer(text):

        start = normalise_id(match.group(1))
        end = normalise_id(match.group(2))

        try:
            expanded = expand_ranges([f"{start}-{end}"])
            results.update(expanded)

            # remove matched range so singles do not double-count
            text = text.replace(match.group(0), " ")

        except Exception:
            pass

    # --------------------------------------------------
    # 2. COMPACT RANGE EXPANSION
    # Supports:
    # IS70A-D
    # AU10-C
    # --------------------------------------------------
    compact_range_re = re.compile(
        r"\b([A-Z]{2,}\d+)([A-Z])-([A-Z])\b"
    )

    for match in compact_range_re.finditer(text):

        prefix = match.group(1)
        start_suffix = match.group(2)
        end_suffix = match.group(3)

        expanded = [
            f"{prefix}{chr(c)}"
            for c in range(
                ord(start_suffix),
                ord(end_suffix) + 1
            )
        ]

        results.update(expanded)

        # remove compact range so singles do not double-count
        text = text.replace(match.group(0), " ")

    # --------------------------------------------------
    # 3. INDIVIDUAL TEST IDS
    # Supports:
    # AU12
    # IS01A
    # TP-CREW-01
    # TP-OPT-01
    # --------------------------------------------------
    TEST_ID_RE = re.compile(
        r"\b(?!STRY)"
        r"(?:"
        r"[A-Z]+(?:-[A-Z]+)*-\d+[A-Z]*"
        r"|"
        r"[A-Z]{2,}\d+[A-Z]*"
        r")\b"
    )

    singles = TEST_ID_RE.findall(text)

    results.update(
        normalise_id(t)
        for t in singles
    )

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

				# --------------------------------------------------
				# Preserve cell structure
				# (important for Word table parsing stability)
				# --------------------------------------------------
				cell_texts = [
					normalise_text(cell.text)
					for cell in row.cells
				]

				row_text = " | ".join(
					t for t in cell_texts
					if t
				)

				if not row_text:
					continue

				# --------------------------------------------------
				# Stories can exist anywhere in row
				# --------------------------------------------------
				stories = _extract_story_ids(row_text)

				if not stories:
					continue

				# --------------------------------------------------
				# Extract tests from EACH CELL independently
				# (avoids DOCX merge/newline corruption)
				# --------------------------------------------------
				tests = set()

				for cell_text in cell_texts:

					tests.update(
						_extract_tests_from_cell(cell_text)
					)

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