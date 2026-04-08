from __future__ import annotations
from typing import Dict, Set
from collections import defaultdict

class StoryMap:
    def __init__(self, story_to_tests: Dict[str, Set[str]]):
        self.story_to_tests = {s:set(v) for s,v in story_to_tests.items()}
        self.test_to_stories: Dict[str, Set[str]] = defaultdict(set)
        for s, tests in self.story_to_tests.items():
            for t in tests:
                self.test_to_stories[t].add(s)
