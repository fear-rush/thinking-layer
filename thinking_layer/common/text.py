from __future__ import annotations

import re


def slugify(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return re.sub(r"-+", "-", value).strip("-")


def normalize_space(value: str | None) -> str:
    return re.sub(r"\s+", " ", value or "").strip()
