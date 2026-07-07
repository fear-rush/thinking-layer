from __future__ import annotations

from functools import lru_cache
from typing import Any

from ..common.io import read_json
from .paths import CONFIG_DIR, ROOT


@lru_cache(maxsize=None)
def load_heuristic_config(name: str) -> dict[str, Any]:
    path = CONFIG_DIR / f"{name}.json"
    if not path.exists():
        raise SystemExit(f"Missing heuristic config {path.relative_to(ROOT)}")
    data = read_json(path)
    if not isinstance(data, dict):
        raise SystemExit(f"{path.relative_to(ROOT)} must contain a JSON object")
    return data


def heuristic_section(config_name: str, section: str) -> dict[str, Any]:
    config = load_heuristic_config(config_name)
    value = config.get(section)
    if not isinstance(value, dict):
        raise SystemExit(f"resources/config/{config_name}.json missing object section `{section}`")
    return value
