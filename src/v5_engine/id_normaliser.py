from __future__ import annotations
import re

def normalise_id(value: str) -> str:
    if value is None:
        return ''
    return re.sub(r"\s+", "", str(value)).upper()
