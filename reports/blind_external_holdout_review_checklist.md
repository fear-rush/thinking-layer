# External Holdout Review Checklist

- Run timestamp: `2026-07-11T14:24:37`
- Gold file: `resources/holdout_questions.external.json`
- Quality file: `resources/answer_quality_questions.external.json`

## Pre-Run Integrity

- [x] Questions were written before running this validation.
- [x] Reviewer did not inspect retrieval results while writing expected labels.
- [x] Questions are not copied from `resources/gold_questions.json`, `resources/holdout_questions.internal.json`, or prior failure reports.
- [x] At least one BI-only, OJK-only, cross-regulator, partial, and not-found question is included where relevant.
- [x] Expected documents use title substrings, not exact snippets from retrieved answers.

## Post-Run Triage

- [x] Each failure is classified in `reports/blind_external_holdout_triage.md`.
- [x] No code or label change was made after seeing failures.
- [x] Metrics are reported with exact file paths and date.
- [x] This run will not be reused as a tuning set.

## Results

- Evidence: `18/19`, average `0.945`.
- Answer: `18/19`, average `0.944`.
- Answer quality: `9/10`, average `0.993`.
