from __future__ import annotations
import re
from typing import Iterable, Set
from .id_normaliser import normalise_id

RANGE_SEP = r"\s*[\-–—]\s*"

def expand_ranges(entries: Iterable[str]) -> Set[str]:
    out: Set[str] = set()
    for raw in entries:
        if not raw:
            continue
        s = normalise_id(str(raw))
        for part in re.split(r"\s*,\s*", s):
            if not part:
                continue
            m = re.match(rf"^([A-Z]+)(\d+){RANGE_SEP}(?:)?(\d+)$", part)
            if m:
                pref, a, b = m.group(1), int(m.group(2)), int(m.group(3))
                width = len(m.group(2))
                step = 1 if a <= b else -1
                for n in range(a, b + step, step):
                    out.add(f"{pref}{n:0{width}d}")
            else:
                out.add(part)
    return out
