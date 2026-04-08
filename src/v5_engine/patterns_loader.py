from __future__ import annotations
import json
from pathlib import Path
from typing import List

class Patterns:
    def __init__(self, story_patterns: List[str], testid_patterns: List[str]):
        self.story_patterns = story_patterns
        self.testid_patterns = testid_patterns

def load_patterns(path: Path) -> Patterns:
    data = json.loads(Path(path).read_text())
    return Patterns(list(data.get('story_patterns', [])), list(data.get('testid_patterns', [])))
