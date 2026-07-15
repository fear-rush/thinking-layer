# Report Index

This directory contains the current corpus state and retained terminal golden-evaluation evidence. Historical, exploratory, and superseded reports are not kept here; every non-terminal report can be regenerated from its named command.

## Corpus State

- `extraction_summary.json` and `extraction_summary.md`: extraction coverage from the saved outputs. Regenerate with `uv run python -m thinking_layer.cli report`.
- `ocr_needed.json` and `ocr_needed.md`: files excluded because they require OCR. The JSON file is also the mandatory skip list for `rebuild-blocks`.
- `source_corpus_baseline.json` and `source_corpus_baseline.md`: citation-ready source-corpus counts and coverage. Regenerate with `uv run python -m thinking_layer.cli build-source-corpus --include-secondary`.
- `corpus_audit.json`: structural, provenance, citation-admission, and duplicate-suppression gate. Regenerate with `uv run python -m thinking_layer.cli corpus-audit`.
- `primary_duplicate_files.json`: exact-primary duplicate groups and the canonical/suppressed file decisions produced by corpus construction.

## Terminal Golden Evidence

The authoritative source is `resources/golden_questions.json`: 44 exact legal-unit cases spanning BI and OJK documents, cross-regulator retrieval, parser boundaries, structured answer behavior, and refusal cases.

- `golden_preflight_terminal.json`: all 52 exact target variants were present in the index.
- `golden_smoke_terminal.json`: terminal 12-case smoke run; 10 accepted, average score `0.900`.
- `golden_full_terminal.json`: terminal 44-case run; 21 accepted, average score `0.648`.
- `golden_terminal_analysis.md`: concise failure analysis and ranked follow-up work for the terminal run.

Use `thinking_layer/evaluation/README.md` for the authoritative preflight, smoke, full-suite, filtering, and comparison commands. A report score is regression evidence, not a substitute for legal review.
