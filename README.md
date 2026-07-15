# thinking-layer

The backend is in a destructive hard-cutover migration. The legacy corpus, retrieval,
answering, API, evaluation, and test contracts have been removed and are not runnable.

The prior LiteParse output has been discarded. The next corpus build is blocked on
a fresh, pinned, OCR-disabled extraction from downloaded source documents. Documents
named by reports/ocr_needed.json must be skipped before extraction and reported as
an explicit coverage limitation; OCR remains disabled.

The implementation order and acceptance gates are defined in PLAN.md.
The first restored runtime surface will be the clean corpus build, followed by the
SQLite database, two-stage retrieval, API, and real-index evaluation.

The fresh source-inventory and extraction command will be restored before the corpus
build command. Do not populate `processed/raw/liteparse/` from a legacy extraction.
