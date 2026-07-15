# V2 Golden Evaluation

`resources/golden_questions.v2.json` is the sole active backend evaluation contract. Its 44 cases evaluate exact legal-unit targets, citation provenance, answer boundaries, issuer coverage, parser-boundary behavior, and conservative refusal. The smoke tier contains 12 representative cases for routine iteration.

Every selected exact citation target is checked against the active v2 SQLite index before answer generation. A failed preflight means the corpus or index is incomplete or stale; it is not an answer-ranking failure and must not be hidden with `--skip-preflight` in integration or release evaluation.

Required `targets` determine answer recall. Narrowly reviewed `allowed_targets` may count toward citation precision, but they never substitute for a missing required target.

## Routine Workflow

Validate smoke targets without generating answers:

```bash
uv run python -m thinking_layer.evaluation.golden \
  --tier smoke \
  --preflight-only
```

Run the smoke tier and save a disposable current report:

```bash
uv run python -m thinking_layer.evaluation.golden \
  --tier smoke \
  --jobs 1 \
  --output reports/golden_v2_smoke_current.json
```

Run the complete 44-case gate only after the corpus and index under test are ready:

```bash
uv run python -m thinking_layer.evaluation.golden \
  --tier full \
  --jobs 1 \
  --output reports/golden_v2_full_current.json
```

## Focused Diagnosis

Select exact cases or one category without creating a second fixture:

```bash
uv run python -m thinking_layer.evaluation.golden \
  --tier full \
  --case-id bi_qris_mandatory \
  --case-id ojk_personal_data_prohibition

uv run python -m thinking_layer.evaluation.golden \
  --tier full \
  --category parser_boundary \
  --output reports/golden_v2_parser_boundary_current.json
```

Repeated and comma-separated filters are accepted. Case-ID and category filters intersect, output order follows fixture order, and `--limit` applies after filtering.

## Baseline Comparison

Compare a smoke run with the retained terminal baseline:

```bash
uv run python -m thinking_layer.evaluation.golden \
  --tier smoke \
  --output reports/golden_v2_smoke_current.json \
  --compare-to reports/golden_v2_smoke_terminal.json
```

For a full-suite candidate, compare against `reports/golden_v2_full_terminal.json`. Accept a comparison only when `same_case_ids` is true. The summary reports acceptance, average score, hard failures, per-category results, and p50/p95/maximum/total latency.

The retained terminal evidence is indexed in `reports/REPORT_INDEX.md`. Current report files are working artifacts; do not accumulate numbered, `final`, or intermediate copies in `reports/`.
