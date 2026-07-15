from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
DOWNLOADS_DIR = ROOT / "downloads"
SOURCE_RECORDS_DIR = DATA_DIR
PROCESSED_DIR = ROOT / "processed"
RAW_LITEPARSE_DIR = PROCESSED_DIR / "raw" / "liteparse"
RAW_LITEPARSE_DOCUMENTS_DIR = RAW_LITEPARSE_DIR / "documents"
CORPUS_DIR = PROCESSED_DIR / "corpus"
DATABASE_DIR = PROCESSED_DIR / "database"
REPORTS_DIR = ROOT / "reports"
RESOURCES_DIR = ROOT / "resources"
OCR_NEEDED_PATH = REPORTS_DIR / "ocr_needed.json"
