from __future__ import annotations
import re
from typing import Iterable, Set
from .id_normaliser import normalise_id


def expand_ranges(tokens: List[str]) -> Set[str]:
    """
    Expands tokens like:
        ME03-ME12 → ME03, ME04, ..., ME12

    Also preserves non-range tokens.
    """

    results = set()

    for tok in tokens:
        tok = tok.strip().upper()

        # --------------------------------------------------
        # MATCH RANGE (e.g. ME03-ME12)
        # --------------------------------------------------
        m = re.match(r"^([A-Z]+)(\d+)-([A-Z]+)?(\d+)$", tok)

        if m:
            prefix1, start_num, prefix2, end_num = m.groups()

            # If second prefix missing, assume same
            prefix2 = prefix2 or prefix1

            # Only expand if prefixes match
            if prefix1 == prefix2:
                start = int(start_num)
                end = int(end_num)

                width = len(start_num)  # preserve leading zeros

                for i in range(start, end + 1):
                    results.add(f"{prefix1}{str(i).zfill(width)}")

                continue  # skip normal add

        # --------------------------------------------------
        # NOT A RANGE → keep as-is
        # --------------------------------------------------
        results.add(tok)

    return results
