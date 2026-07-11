# Development Issue Triage

Date: 2026-07-11

This report records the separate development investigation following the consumed blind holdout. The blind holdout files and reports were not modified.

## Staff-Uniform Refusal Boundary

### Finding

The query `apa ketentuan BI mengenai warna seragam petugas pemasaran bank?` was incorrectly expanded into the `advertising_marketing` topic because `pemasaran` matched a broad topic pattern. That caused unrelated BI regulations to be treated as strong evidence.

### Fix

Added config-driven negative context for `seragam`, `pakaian`, and `uniform`. When one of those terms is present, the advertising topic is not matched, so the generic bank query does not broaden into unrelated regulations.

### Verification

- Fresh planning regression test passes.
- End-to-end answer status is `not_found`.
- Evidence confidence is `weak` with score `0.775`.
- Citation count is `0`.

## Consumer-Protection Comparison Label

### Finding

The consumed blind query expected `partial` but produced `answerable` with direct BI and OJK evidence. A fresh variant, `bandingkan cakupan pelindungan konsumen BI dengan OJK`, produces `partial` with score `0.71` and explicitly limits claims to retrieved evidence.

### Decision

Do not change the answer-status contract or retag the consumed blind case from a single run. Keep the exact blind case as a manual gold-label review item. The behavior is query-sensitive and the fresh variant supports the existing conservative partial path.

## Verification

- Unit tests: `46/46` passed.
- No post-run tuning was applied to the consumed blind holdout.
