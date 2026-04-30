from __future__ import annotations
from dataclasses import dataclass

# Output root (matches your desired structure)
OUTPUT_ROOT = "outputs/releases"
DEFAULT_OUTPUT_NAME = None

@dataclass(frozen=True)
class EngineConfig:
    red_on_extra: bool = True
    enable_audit_sheets: bool = True

    @staticmethod
    def from_settings_dict(d: dict) -> "EngineConfig":
        return EngineConfig(
            red_on_extra=bool(d.get("red_on_extra", True)),
            enable_audit_sheets=bool(d.get("enable_audit_sheets", True)),
        )
