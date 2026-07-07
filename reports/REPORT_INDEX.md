# Report Index

This directory contains only regenerated current-baseline reports. JSON files are machine-readable companions for the matching Markdown reports.

## Corpus And Extraction

- `corpus_audit.md/json`: source metadata/file audit.
- `extraction_summary.md/json`: LiteParse extraction summary from existing processed outputs.
- `extraction_spot_check.md/json`: focused extraction/citation spot check for high-value BI/OJK regulation areas.
- `ocr_needed.md/json`: files skipped because OCR is needed or extraction failed.
- `parser_comparison_sample.md/json`: small LiteParse vs MinerU/layout-parser comparison gate before parser switching.
- `source_corpus_baseline.md/json`: citation-ready source corpus summary.

## Heuristics And Answer Correctness

- `heuristics_audit.md`: active values loaded from `resources/config/`.
- `answer_noise_audit.md/json`: legal boilerplate/noise classification over the current source corpus.
- `cross_regulator_coverage_audit.md/json`: direct-vs-adjacent topic coverage for BI/OJK comparison queries.

## Development Evaluations

- `retrieval_smoke_test.md/json`: focused retrieval smoke tests.
- `natural_language_eval.md/json`: broader natural-language retrieval tests.
- `evidence_eval.md/json`: evidence-pack evaluation against `resources/gold_questions.json`.
- `answer_eval.md/json`: deterministic answer evaluation against `resources/gold_questions.json`.
- `answer_quality_eval.md/json`: answer presentation/quality checks against `resources/answer_quality_questions.json`.

## External-Style Validation

- `ai_external_holdout_manifest.json`: summary for the AI-authored external-style run.
- `ai_external_holdout_evidence.md/json`: evidence results for `resources/holdout_questions.external.json`.
- `ai_external_holdout_answer.md/json`: answer results for `resources/holdout_questions.external.json`.
- `ai_external_holdout_answer_quality.md/json`: answer-quality results for `resources/answer_quality_questions.external.json`.
- `ai_external_holdout_review_checklist.md`: checklist reminding that this run is not blind reviewer validation.
