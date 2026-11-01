from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_config() -> dict:
    with (ROOT / "config.json").open(encoding="utf-8") as f:
        return json.load(f)


def project_path(value: str | Path) -> Path:
    return ROOT / value

