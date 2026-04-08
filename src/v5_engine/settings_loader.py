from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Dict
from .config import EngineConfig

def load_settings(path: Path) -> EngineConfig:
    data: Dict[str, Any] = json.loads(Path(path).read_text())
    return EngineConfig.from_settings_dict(data)
