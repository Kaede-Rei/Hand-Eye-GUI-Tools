from __future__ import annotations

import json
from pathlib import Path
from typing import Any


try:
    import yaml
except Exception:  # pragma: no cover
    yaml = None


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def read_data(path: Path) -> Any:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".json" or yaml is None:
        return json.loads(text)
    return yaml.safe_load(text)


def write_data(path: Path, payload: Any) -> None:
    ensure_dir(path.parent)
    if path.suffix.lower() == ".json" or yaml is None:
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    else:
        path.write_text(yaml.safe_dump(payload, allow_unicode=True, sort_keys=False), encoding="utf-8")
