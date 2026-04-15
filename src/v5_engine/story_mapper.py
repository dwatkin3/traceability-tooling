from __future__ import annotations
from typing import Dict, Set, Tuple
from collections import defaultdict

class StoryMap:
    def __init__(
        self,
        release_story_to_tests: Dict[Tuple[str, str], Set[str]]
    ):
        """
        Key: (release, story)
        Value: set of test IDs
        """
        self.release_story_to_tests = release_story_to_tests

    def stories(self):
        return {story for (_, story) in self.release_story_to_tests.keys()}

