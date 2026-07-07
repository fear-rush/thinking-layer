# External Holdout Review Checklist

- Run timestamp: `2026-07-05T15:19:53`
- Gold file: `resources/holdout_questions.external.json`
- Quality file: `resources/answer_quality_questions.external.json`

## Pre-Run Integrity

- [ ] Questions were written before running this validation.
- [ ] Reviewer did not inspect retrieval results while writing expected labels.
- [ ] Questions are not copied from `resources/gold_questions.json`, `resources/holdout_questions.internal.json`, or prior failure reports.
- [ ] At least one BI-only, OJK-only, cross-regulator, partial, and not-found question is included where relevant.
- [ ] Expected documents use title substrings, not exact snippets from retrieved answers.

## Post-Run Triage

- [ ] Each failure is classified as retrieval, citation extraction, answer composer, answer quality, or gold-label issue.
- [ ] Any code or label change after seeing failures is logged with rationale.
- [ ] Metrics are reported with exact file paths and dates.
- [ ] This run is not called blind again after code/label tuning against it.

## Results

- Evidence: `30/30`, average `0.982`.
- Answer: `30/30`, average `0.979`.
- Answer quality: `12/12`, average `1.0`.

