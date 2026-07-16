from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
DOWNLOADS_DIR = ROOT / "downloads"

EASE_BI_RECORDS_DIR = DATA_DIR / "ease-bi"
EASE_BI_DOWNLOADS_DIR = DOWNLOADS_DIR / "ease-bi"
PERATURAN_OJK_RECORDS_DIR = DATA_DIR / "peraturan-ojk"
PERATURAN_OJK_DOWNLOADS_DIR = DOWNLOADS_DIR / "peraturan-ojk"

SUPPORTED_SOURCE_NAMES = frozenset({"ease-bi", "peraturan-ojk"})
ARTIFACTS_DIR = ROOT / "artifacts"
