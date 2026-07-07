from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
DOWNLOADS_DIR = ROOT / "downloads"
REPORTS_DIR = ROOT / "reports"
PROCESSED_DIR = ROOT / "processed"
RESOURCES_DIR = ROOT / "resources"
CONFIG_DIR = RESOURCES_DIR / "config"
RAW_LITEPARSE_DIR = PROCESSED_DIR / "raw" / "liteparse"
SEARCH_INDEX_DIR = PROCESSED_DIR / "search_index"
SEARCH_INDEX_DB = SEARCH_INDEX_DIR / "search.sqlite"
STOPWORDS_PATH = RESOURCES_DIR / "indonesian-stopwords-complete.txt"
QUERY_LEXICON_PATH = RESOURCES_DIR / "query_lexicon.json"
GOLD_QUESTIONS_PATH = RESOURCES_DIR / "gold_questions.json"
ANSWER_QUALITY_QUESTIONS_PATH = RESOURCES_DIR / "answer_quality_questions.json"
LEXICON_DIR = PROCESSED_DIR / "lexicon"
LEXICON_CANDIDATES_PATH = LEXICON_DIR / "candidates.json"
GENERATED_LEXICON_PATH = RESOURCES_DIR / "query_lexicon.generated.json"
REVIEWED_LEXICON_PATH = RESOURCES_DIR / "query_lexicon.reviewed.json"
SOURCE_CORPUS_PATH = PROCESSED_DIR / "source_corpus.ndjson"

SOURCE_DIRS = {
    "ease-bi": DATA_DIR / "ease-bi",
    "peraturan-ojk": DATA_DIR / "peraturan-ojk",
    "sikepo-ojk": DATA_DIR / "sikepo-ojk",
}
