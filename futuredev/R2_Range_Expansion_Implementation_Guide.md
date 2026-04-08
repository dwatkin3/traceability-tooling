
# R2 Range Expansion — Developer Implementation Guide

**Release context:** V5 Traceability Reconciler  
**Decisions locked:** R2 + S1 + F1 + E3 + A + D2 + Q20

---

## 0) Summary of Agreed Rules

- **R2 (Range Expansion):** Expand numeric spans and family tokens; support unions (commas, `&`, `AND`) and dash variants (`–`, `—`, `-`).
- **S1 (Span semantics):** Spans represent **real planned test sets** for the story. Missing any expanded test ⇒ **RED**; all covered + extras ⇒ **AMBER**; exact match ⇒ **GREEN**. **RED overrides AMBER.**
- **F1 (Universe):** Expand **only** using test IDs present in the execution workbook for the release.
- **E3 (Summary display):** Summary shows **original spans** (not expanded lists); expansion is internal.
- **A (ALL token):** `ALL` = all families present in execution (for the current release).
- **D2 (Audit):** Add **Expanded_Plan** sheet to the output workbook.
- **Q20 (Prefix rule):** Family prefix = **leading A–Z** characters before the first digit (e.g., `CEMO05` → prefix `CEMO`, number `05`).

---

## 1) Module Responsibilities

### 1.1 `src/v5_engine/range_expander.py` (NEW)
**Purpose:** Expand plan tokens into concrete test IDs using execution-derived universe.

**Public function:**
```
from typing import List, Dict, Set

def expand_plan_items(
    raw_items: List[str],
    exec_ids: Set[str],
    exec_families: Dict[str, List[str]]
) -> Set[str]:
    """Expand plan tokens (spans, families, ALL, unions) into concrete test IDs.
    - raw_items: tokens like "KP01–KP91", "BA13–BA16", "CEMO", "ALL", etc.
    - exec_ids: all test IDs that appear in execution (F1)
    - exec_families: mapping {family -> [ids]} discovered from execution
    Returns a set of concrete, deduplicated test IDs.
    """
    ...
```

**Responsibilities:**
- Normalize tokens: trim, unify dash to `-`, split by `,`, `&`, `AND`.
- Expand **numeric ranges** (e.g., `KP01-KP91`) preserving zero-pad width; include only IDs present in `exec_ids` (F1).
- Expand **families** (e.g., `CEMO`) via `exec_families`.
- Expand **ALL** = union of all `exec_families.values()`.
- Ignore non-meaningful tokens (`"&"`, `"-"`, blank).
- Deduplicate and sort using `(prefix, numeric)` ordering.

---

### 1.2 `src/v5_engine/plan_parser.py`
**Purpose change:**
- Keep extracting raw plan tokens **as-is** (for Summary/E3).
- **Also** call `expand_plan_items()` to compute **expanded** sets for reconciliation (S1).

**Data to produce:**
- `story_to_original_spans: Dict[str, List[str]]`
- `story_to_expanded_tests: Dict[str, Set[str]]`

Pass `story_to_expanded_tests` forward into the reconciliation pathway (either by wrapping into the StoryMap or returning alongside existing structures).

---

### 1.3 `src/v5_engine/audit_writer.py`
**Purpose change:**
- Status logic (GREEN/AMBER/RED) must use the **expanded** planned sets.
- Summary’s `planned_list` column must show the **original spans**.
- Add a new **Expanded_Plan** sheet:
  - Columns: `Story`, `ExpandedTest`
  - One row per expanded test ID (sorted)

---

### 1.4 `src/v5_engine/reconcile.py`
No interface change. Ensure reconciliation uses **expanded** planned sets.

---

## 2) Range Expansion Algorithms

### 2.1 Normalization
- Replace unicode dashes: `token = token.replace('–', '-').replace('—', '-')`.
- Split tokens with regex: `re.split(r"[,&]|\bAND\b", token, flags=re.IGNORECASE)`.
- Strip whitespace around pieces.

### 2.2 Prefix/number extraction (Q20)
```
import re
m = re.match(r"^([A-Z]+)([0-9]+)$", test_id)
# prefix = m.group(1), num = m.group(2)
```

### 2.3 Numeric range expansion
- Pattern: `^([A-Z]+)([0-9]+)-([A-Z]+)?([0-9]+)$`.
- If second prefix missing → use first.
- `width = len(first_numeric)`; generate `prefix + str(n).zfill(width)` for `n in range(start, end + step)`; step=+1 if start<=end else -1.
- **F1:** include only if generated ID is in `exec_ids`.

### 2.4 Family expansion
- If piece is alphabetic only (e.g., `CEMO`, `KP`, `BA`, `ET`, `TT`, `KO`, `BC`, `BB`):
  - expanded |= `set(exec_families.get(piece, []))`.

### 2.5 `ALL` expansion (Q18=A)
- expanded |= union of all `exec_families.values()`.

### 2.6 Ignore noise
- Skip `"&"`, `"-"`, empty pieces.

### 2.7 Deduplicate & sort
- After all expansions, output a sorted list using key `(prefix(x), int(number(x)))` with the same regex as §2.2.

---

## 3) Data Flow

1. `run_release.py` builds execution universe:
   - `exec_ids: Set[str]` from Exec_Attachments
   - `exec_families: Dict[str, List[str]]` by grouping `exec_ids` by prefix
2. `plan_parser.parse_plan_docx()`
   - Extract **raw tokens** per story (unchanged), store for Summary.
   - Call `expand_plan_items(raw_tokens, exec_ids, exec_families)` to get **expanded** set.
3. Reconcile/Writer
   - Use **expanded** sets for coverage/missing/extra/status.
   - Show **raw spans** in Summary `planned_list` (E3).
   - Write **Expanded_Plan** sheet (D2).

---

## 4) Status Logic (unchanged)

For each story:
- **RED** if any expanded planned test is missing.
- **AMBER** if all expanded planned tests are covered but there are extras for this story.
- **GREEN** if covered exactly (no extras).
- **RED overrides AMBER**.

---

## 5) Expanded_Plan Sheet

- Sheet name: `Expanded_Plan`
- Columns: `Story`, `ExpandedTest`
- One row per test ID; sort by family prefix then numeric.

---

## 6) Test Cases

1. Numeric: `KP01–KP03` with KP01..KP03 in exec → expanded matches.
2. Family: `CEMO` with CEMO01..CEMO23 in exec → 23 items.
3. Union: `CEMO & CEMOVAR` → combined.
4. ALL: with families across exec → union of all.
5. Summary view: shows spans only (E3).
6. RED: expanded items exist but none tied to story → RED.
7. GREEN: exactly covered; no extras → GREEN.
8. AMBER: covered but extras tied to story → AMBER.

---

## 7) Execution Universe Builder (F1)

Example logic (in `run_release.py` or a helper):
```
exec_ids = {row.test for row in all_exec_rows}
exec_families: Dict[str, List[str]] = {}
for t in exec_ids:
    m = re.match(r"^([A-Z]+)([0-9]+)$", t)
    if not m:
        continue
    fam = m.group(1)
    exec_families.setdefault(fam, []).append(t)
for fam in exec_families:
    exec_families[fam].sort(key=lambda x: (re.match(r"^([A-Z]+)([0-9]+)$", x).group(1), int(re.match(r"^([A-Z]+)([0-9]+)$", x).group(2))))
```

---

## 8) Integration Sequence

1) **plan_parser** → produce raw spans + expanded sets.  
2) **reconcile** → use expanded sets.  
3) **audit_writer** → Summary shows spans; status uses expanded sets; write Expanded_Plan.  
4) **debug** → also export `plan_expanded.csv` for audit if useful.

---

## 9) Edge Cases & Notes

- If a numeric range expands to *zero* IDs (none exist in this release’s exec), the planned set for that piece is effectively empty; treat accordingly (story may then not be RED purely for that span if no IDs exist this month).
- If a family token maps to zero IDs in this release (e.g., `KO` present in plan but not executed this release), expansion returns empty; same handling as above.
- Mixed directions (`KP10-KP08`) must still expand with step -1, respecting zero-padding.
- Deduplicate across multiple spans/unions in a single story.
- Keep Summary clean (spans only) per E3.

---

## 10) Deployment Checklist

- Implement `range_expander.py` fully.
- Wire `plan_parser.py` to call `expand_plan_items`.
- Ensure `audit_writer.py` uses **expanded** sets for status logic and writes `Expanded_Plan`.
- Verify folder structure stays: `outputs/<release>/Traceability_Reconciliation_<release>.xlsx`.
- Re-run March and February and compare against expectations.

