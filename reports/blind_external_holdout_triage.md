# Blind External Holdout Triage

Date: 2026-07-11

The holdout questions were written before validation and were not used to tune code or labels during the run. Results:

- Evidence: `18/19`, average `0.945`
- Answer: `18/19`, average `0.944`
- Answer quality: `9/10`, average `0.993`

## Failure Classification

### `blind_not_found_staff_uniform`

- Query: `apa ketentuan BI mengenai warna seragam petugas pemasaran bank?`
- Evidence result: `strong`, but no expected document or direct topic evidence.
- Answer result: `answerable` with six generic BI citations.
- Classification: retrieval/refusal-boundary failure.
- Reason: generic issuer and bank-related matches were sufficient to avoid refusal even though the retrieved documents did not establish a direct rule about staff uniform color.
- Action: do not tune against this holdout run. Review generic-topic refusal and direct-topic coverage behavior in a separately logged development investigation.

### `blind_quality_cross_consumer`

- Query: `apa perbedaan ruang lingkup pelindungan konsumen menurut BI dan OJK?`
- Evidence result: accepted with `strong` confidence and both issuers represented.
- Answer result: `answerable`, while the gold label expected `partial`.
- Classification: gold-label/evaluation-rubric issue pending manual review.
- Reason: the current evidence pack found direct topic-bearing evidence for both BI and OJK, so `partial` is not supported by the observed evidence contract.
- Action: do not retag or tune the system from this run. A reviewer should decide whether the expected behavior is actually `answerable` before any future holdout reset.

## Decision

The holdout is now consumed for blind validation and must not be used as a tuning set without recording that it is no longer blind. Keep the implementation unchanged and address the two findings in a separate development cycle with new regression cases.
