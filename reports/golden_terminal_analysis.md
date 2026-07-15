# Golden Terminal Analysis

## Acceptance Gate

- Corpus audit: all nine structural and source-hygiene checks passed.
- Extracted legal-unit blocks: 375,489 from 2,475 documents.
- Searchable source/index rows: 357,784.
- Exact-target preflight: 52/52 target variants found.
- OCR-needed skip list: empty; no OCR ran during the rebuild.

| Tier | Accepted | Average score | p50 | p95 | Maximum |
| --- | ---: | ---: | ---: | ---: | ---: |
| Smoke | 10/12 (83.3%) | 0.900 | 1.067 s | 18.339 s | 20.055 s |
| Full | 21/44 (47.7%) | 0.648 | 1.641 s | 16.491 s | 19.901 s |

The full run has 23 exact-target failures, 22 citation-precision failures, 15 answer-term failures, 11 status failures, 7 citation-count failures, 7 issuer-coverage failures, and 7 provenance failures. All required units passed preflight, so these are retrieval, planning, or answer-selection defects rather than missing corpus targets.

The highest-value next work is to recover strict `not_found` cases whose exact targets are already indexed, then fix off-target citation selection for partial/answerable cases. Cross-document and ambiguity handling should follow. Exact targets and refusal boundaries must not be relaxed to raise the score.

Retained machine-readable evidence:

- `golden_preflight_terminal.json`
- `golden_smoke_terminal.json`
- `golden_full_terminal.json`
