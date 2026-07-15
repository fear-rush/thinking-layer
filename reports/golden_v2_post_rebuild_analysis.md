# Golden v2 Terminal Analysis

## Acceptance Gate

- V2 corpus audit: passed all nine structural and source-hygiene checks.
- Extracted legal-unit blocks: 417,673.
- Searchable source/index/catalog rows: 398,930.
- Exact-target preflight: 52/52 target variants found in the current v2 index.
- Health at evaluation time: SQLite index current, lexical search ready, document catalog ready.

| Tier | Accepted | Average score | p50 | p95 | Maximum |
| --- | ---: | ---: | ---: | ---: | ---: |
| Smoke | 11/12 (91.7%) | 0.950 | 1.529 s | 19.481 s | 19.489 s |
| Full | 22/44 (50.0%) | 0.664 | 1.679 s | 18.655 s | 20.129 s |

The terminal full run has 21 exact-target failures, 21 citation-precision failures, 15 answer-term failures, 10 status failures, 8 citation-count failures, 8 issuer-coverage failures, and 8 v2-provenance failures.

Category acceptance is 7/18 direct exact, 4/9 enumeration exact, 1/2 amendment exact, 4/5 parser boundary, and 1/1 cross-page exact. Lifecycle, table-refusal, unsupported-issuer, and no-answer cases all pass. Governance, cross-document, and ambiguity cases remain unaccepted.

The retained machine-readable evidence is:

- `golden_v2_preflight_terminal.json`
- `golden_v2_smoke_terminal.json`
- `golden_v2_full_terminal.json`

## Highest-Priority Remaining Failures

Every required unit below passed exact-target preflight. The corpus contains the evidence; these are retrieval, constraint-planning, or answer-selection defects rather than missing-target or parser failures.

| Case | Category | Required exact target | Terminal result | Classification |
| --- | --- | --- | --- | --- |
| `bi_qris_processor_approval` | direct | Pasal 11(1): prior BI approval | `not_found`, no citations | Retrieval ranking |
| `bi_pjp_activity_regression_control` | enumeration | Pasal 2(1): complete four-activity aggregate | `not_found`, no citations | Retrieval ranking |
| `bi_transfer_rejection_notice` | direct | Pasal 9(3): next-business-day rejection reason | `not_found`, no citations | Retrieval ranking |
| `ojk_lpbbti_consumer_rate_2025` | amendment | SEOJK 19/2025 p.19 huruf b: 0.3%/0.2% tiers | `not_found`, no citations | Retrieval constraints |
| `ojk_sharia_bank_minimum_capital` | direct | Pasal 2(1): risk-profile minimum capital | `not_found`, no citations | Retrieval ranking |
| `ojk_pawnshop_paid_up_capital_by_region` | enumeration | Pasal 6(1): paid-up-capital tiers by region | `not_found`, no citations | Retrieval ranking |
| `ojk_bmpk_liquidity_placement_limit` | direct | Pasal 29(3): 30% of BPR/BPRS capital | `not_found`, no citations | Retrieval ranking |
| `ojk_bpr_governance_conflict_disclosure` | governance | Pasal 70(2): conflict disclosure for every decision | `not_found`, no citations | Retrieval ranking |
| `bi_consumer_data_consent` | direct | Pasal 35(2): written consent or statutory exception | Answerable with one off-target citation | Retrieval/composer |
| `ojk_insurance_marketing_information` | direct | Pasal 55(1)(a): accurate, clear, honest, non-misleading information | Two off-target citations; terms absent | Retrieval/composer |
| `bi_written_complaint_required_information` | enumeration | Pasal 29 huruf c: complete required-information list | Partial with one off-target citation | Retrieval/composer |
| `ojk_exoneration_clauses_prohibited` | parser boundary | Pasal 30(4) prohibition and complete Pasal 30(5) enumeration | Only the prohibition target returned | Retrieval/composer |
| `cross_regulator_consumer_data` | cross-document | BI Pasal 35(2) and OJK Pasal 11(1) | Exact OJK target only | Retrieval/topic coverage |
| `ambiguous_institution_data_rule` | ambiguity | BI Pasal 35(2) and OJK Pasal 11(1) | Partial with no exact targets | Retrieval/composer |
| `ambiguous_bank_capital_type` | ambiguity | One explicit OJK bank-capital rule | Partial with one off-target citation | Retrieval/composer |

The next accuracy work should begin with the strict `not_found` rows whose targets already exist, then address off-target citation selection, and finally improve cross-document and ambiguity handling. Do not relax exact targets to raise the score.
