# thinking-layer

The backend is in a destructive hard-cutover migration. The legacy corpus, retrieval,
answering, API, evaluation, and test contracts have been removed and are not runnable.

Saved non-OCR LiteParse pages under processed/raw/liteparse/ remain migration input.
Documents named by reports/ocr_needed.json are excluded from all future corpus and
coverage claims; OCR remains disabled.

The implementation order and acceptance gates are defined in PLAN.md.
The first restored runtime surface will be the clean corpus build, followed by the
SQLite database, two-stage retrieval, API, and real-index evaluation.

Build the corpus from saved raw non-OCR pages with:

    uv run python -m thinking_layer.cli build
