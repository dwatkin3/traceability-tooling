from docx import Document
import re

TEST_ID_RANGE_RE = re.compile(r"(Test|KP|ME)\s?(\d+)\s?[–-]\s?(?:Test|KP|ME)\s?(\d+)")
TEST_ID_SINGLE_RE = re.compile(r"\b(CEMO[A-Z]+\d+|KP\d+[A-Z]?|IS\d+[A-Z]?|ME\d+)\b")

def expand_ranges(text: str):
    results = set()
    for m in TEST_ID_RANGE_RE.finditer(text):
        prefix, start, end = m.groups()
        for i in range(int(start), int(end) + 1):
            results.add(f"{prefix}{i}")
    return results

def extract_test_ids(cell_text: str):
    ids = set(TEST_ID_SINGLE_RE.findall(cell_text))
    ids |= expand_ranges(cell_text)
    return ids

def extract_story_test_map(spec_path: str) -> dict[str, set[str]]:
    """
    Returns:
      {
        "STRY0084121": {"CEMOAC01", "CEMOAC02", ...},
        ...
      }
    """
    doc = Document(spec_path)
    story_map: dict[str, set[str]] = {}

    for table in doc.tables:
        headers = [c.text.strip().upper() for c in table.rows[0].cells]

        if "STORY" not in headers or "TEST ID" not in "".join(headers):
            continue

        story_col = headers.index("STORY")
        test_col = next(
            i for i, h in enumerate(headers)
            if "TEST ID" in h
        )

        for row in table.rows[1:]:
            story = row.cells[story_col].text.strip()
            tests = extract_test_ids(row.cells[test_col].text)

            if story and tests:
                story_map.setdefault(story, set()).update(tests)

    return story_map
