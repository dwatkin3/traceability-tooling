from __future__ import annotations
import json
from dataclasses import dataclass
from pathlib import Path
from typing import List

@dataclass
@dataclass
class ColumnHints:
    story_column_candidates: List[str]
    testid_column_candidates: List[str]
    status_column_candidates: List[str]
    pass_values: List[str]
    ignore_sheets: List[str]

def load_column_hints(path: Path) -> ColumnHints:
    data = json.loads(path.read_text())

    return ColumnHints(
        story_column_candidates=data.get("story_column_candidates", []),
        testid_column_candidates=data.get("testid_column_candidates", []),
        status_column_candidates=data.get("status_column_candidates", []),
        pass_values=data.get("pass_values", []),
        ignore_sheets=data.get("ignore_sheets", [])
    )