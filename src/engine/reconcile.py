from __future__ import annotations
from typing import Dict, Set
from dataclasses import dataclass

@dataclass
class ReconcileResult:
    missing_tests: Set[str]
    extra_tests: Set[str]
    missing_execution_for_story: Set[str]
    extra_stories_in_execution: Set[str]

def reconcile(plan_story_to_tests: Dict[str, Set[str]], exec_test_ids: Set[str], exec_story_refs: Set[str], red_on_extra: bool=True) -> ReconcileResult:
    plan_tests: Set[str] = set().union(*plan_story_to_tests.values()) if plan_story_to_tests else set()
    missing_tests = plan_tests - exec_test_ids
    extra_tests = exec_test_ids - plan_tests if red_on_extra else set()
    missing_execution_for_story = {s for s, tests in plan_story_to_tests.items() if not (tests & exec_test_ids)}
    extra_stories_in_execution = exec_story_refs - set(plan_story_to_tests.keys())
    return ReconcileResult(missing_tests, extra_tests, missing_execution_for_story, extra_stories_in_execution)
