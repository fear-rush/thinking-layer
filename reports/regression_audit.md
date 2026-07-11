# Development Regression Audit

Date: 2026-07-11

## Result

The post-lexicon serial gate passed. Development evaluation acceptance remained green:

| Evaluation | Frozen baseline | Current run | Result |
| --- | --- | --- | --- |
| Retrieval smoke | 10/10, average `0.996` | 10/10, average `0.998` after ranking fix | Recovered; primary-first behavior improved |
| Natural language | 15/15, average `0.999` | 15/15, average `0.989` | Accepted; ranking/Pasal ordering changed, but no question failed |
| Evidence | 30/30, average `0.990` | 30/30, average `0.990` | Accepted after serial rerun |
| Answer | 30/30, average `0.988` | 30/30, average `0.988` | Accepted after serial rerun |
| Answer quality | 12/12, average `1.000` | 12/12, average `1.000` | Accepted; output shape changed |

The unit suite was also rerun with `52/52` tests passing. The two approved aliases (`pelindungan konsumen` and `uji kemampuan dan kepatutan`) did not change any gold natural-language query plan when compared against the pre-alias runtime lexicon. The natural-language score difference is therefore a regenerated ranking/Pasal-ordering difference rather than an alias-induced acceptance regression.

## Findings

### QRIS query

`QRIS pengembangan aktivitas produk kerja sama` initially changed from `1.000` to `0.940`. The query remained accepted, but three newly indexed `operational_requirement` documents occupied the first three results. This lowered the top-five primary-regulation rate from `1.000` to `0.400`.

The planned-result layer did not apply file-role priority, so title hits from operational guidance could outrank primary regulations. A configured role multiplier was added to that layer. The post-fix result is `0.980`, with primary regulations in four of the top five results. This is a ranking-policy correction, not a query-specific shortcut.

### Technology-risk query

`manajemen risiko teknologi informasi bank umum` initially changed from `1.000` to `0.980`. The expected titles and issuer remained present, but a secondary FAQ entered the top five, reducing the primary-regulation rate from `1.000` to `0.800`. After the role-priority fix, the result returned to `1.000` with primary regulations in the full top five.

The latest extraction changes also alter one extracted `Pasal` value from `Pasal 2 ayat (2)` to `Pasal 2 ayat (1)`. This is consistent with the recent non-standard `Pasal`/`Ayat` extraction work, but the affected source page should receive a visual citation spot check.

### Answer-quality output

Answer-quality acceptance remains `12/12` with average score `1.000`. Citation counts and answer lengths changed for several questions, and one confidence score moved from `1.000` to `0.858`, but no deterministic quality gate failed.

## Decision

Do not add query-specific shortcuts. Keep the current behavior accepted, review primary-first ranking for operational guidance and secondary FAQ records, and perform the cited-page spot check before changing extraction or ranking heuristics.
