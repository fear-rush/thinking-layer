# Report Index

This directory contains only regenerated current-baseline reports. JSON files are machine-readable companions for the matching Markdown reports.

## Corpus And Extraction

- `corpus_audit.md/json`: source metadata/file audit.
- `extraction_summary.md/json`: LiteParse extraction summary from existing processed outputs.
- `extraction_spot_check.md/json`: focused extraction/citation spot check for high-value BI/OJK regulation areas.
- `ocr_needed.md/json`: files skipped because OCR is needed or extraction failed.
- `parser_comparison_sample.md/json`: small LiteParse vs MinerU/layout-parser comparison gate before parser switching.
- `source_corpus_baseline.md/json`: citation-ready source corpus summary.
- `visual_spot_check.md/json`: rendered page review for QRIS, SNAP, XLSX, and GMRA extraction quality.

## Heuristics And Answer Correctness

- `heuristics_audit.md`: active values loaded from `resources/config/`.
- `answer_noise_audit.md/json`: legal boilerplate/noise classification over the current source corpus.
- `cross_regulator_coverage_audit.md/json`: direct-vs-adjacent topic coverage for BI/OJK comparison queries.
- `regression_audit.md`: comparison of current development evaluations against the frozen regression baseline.

## Development Evaluations

- `retrieval_smoke_test.md/json`: focused retrieval smoke tests.
- `natural_language_eval.md/json`: broader natural-language retrieval tests.
- `evidence_eval.md/json`: evidence-pack evaluation against `resources/gold_questions.json`.
- `answer_eval.md/json`: deterministic answer evaluation against `resources/gold_questions.json`.
- `answer_quality_eval.md/json`: answer presentation/quality checks against `resources/answer_quality_questions.json`.
- `development_issue_triage.md`: separate development investigation and verification for holdout findings.
- `lexicon_review.md`: reviewed generated lexicon candidates, approved failure-driven aliases, and active-runtime verification.
- `query_trace_<slug>.json`: local observability records emitted by `trace-query` when explicitly requested.
- `semantic_retrieval_smoke.md`: bounded SentenceTransformers dense-retrieval implementation smoke check; not a quality benchmark.
- `semantic_retrieval_benchmark.md/json`: bounded model-matrix comparison of BM25, dense retrieval, and RRF; current result does not justify adoption.
- `semantic_retrieval_benchmark_corrected.md/json`: corrected 5,000-block comparison with E5 prefixes; no candidate beats BM25, and GTE is locally incompatible.

## External Validation

- `blind_external_holdout_manifest.json`: reviewer-owned blind validation summary from 2026-07-11.
- `blind_external_holdout_evidence.md/json`: blind evidence results.
- `blind_external_holdout_answer.md/json`: blind answer results.
- `blind_external_holdout_answer_quality.md/json`: blind answer-quality results.
- `blind_external_holdout_triage.md`: classified blind-holdout failures.
