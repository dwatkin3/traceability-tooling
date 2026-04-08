from __future__ import annotations
import json
from dataclasses import dataclass
from pathlib import Path
from typing import List

@dataclass
class ColumnHints:
    story_column_candidates: List[str]
    testid_column_candidates: List[str]

def load_column_hints(path: Path) -> ColumnHints:
    data = json.loads(Path(path).read_text())
    return ColumnHints(
        story_column_candidates=[c.strip() for c in data.get('story_column_candidates', [])],
        testid_column_candidates=[c.strip() for c in data.get('testid_column_candidates', [])],
    )
