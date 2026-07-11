# Semantic Retrieval Benchmark

This is a retrieval-only benchmark. It compares direct BM25, dense retrieval, and BM25+dense Reciprocal Rank Fusion on the development gold questions. It does not change production retrieval or claim answer/evidence quality improvements.

- Corpus blocks: `5000`
- Questions: `30`
- Dense candidate depth: `20`
- RRF constant: `60`
- Cutoffs: `5`, `10`, `20`

## BM25 Baseline

- MRR: `0.869`
- Document recall: `{'5': 0.821, '10': 0.821, '20': 0.8395}`
- Issuer coverage at 10: `0.8833`

## Dense And RRF

### `intfloat/multilingual-e5-small`

- Dimensions: `384`
- Dense MRR: `0.1667`
- Dense document recall: `{'5': 0.179, '10': 0.179, '20': 0.179}`
- Dense issuer coverage at 10: `0.2167`
- RRF MRR: `0.85`
- RRF document recall: `{'5': 0.8025, '10': 0.821, '20': 0.821}`
- RRF issuer coverage at 10: `0.8833`

### `intfloat/multilingual-e5-base`

- Dimensions: `768`
- Dense MRR: `0.1611`
- Dense document recall: `{'5': 0.179, '10': 0.179, '20': 0.179}`
- Dense issuer coverage at 10: `0.2167`
- RRF MRR: `0.85`
- RRF document recall: `{'5': 0.8025, '10': 0.821, '20': 0.821}`
- RRF issuer coverage at 10: `0.8833`

### `Alibaba-NLP/gte-multilingual-base`

- Status: `error`
- Error type: `IndexError`
- Error: `index 4392253568 is out of bounds for dimension 0 with size 451`

### `BAAI/bge-m3`

- Dimensions: `1024`
- Dense MRR: `0.1689`
- Dense document recall: `{'5': 0.1667, '10': 0.1667, '20': 0.179}`
- Dense issuer coverage at 10: `0.2167`
- RRF MRR: `0.85`
- RRF document recall: `{'5': 0.8025, '10': 0.821, '20': 0.821}`
- RRF issuer coverage at 10: `0.8833`

## Interpretation Guardrails

- Not-found questions are included in the query rows but are excluded from document-recall averaging because retrieval alone has no calibrated refusal threshold.
- The bounded corpus slice and development gold set are suitable for implementation comparison, not final model selection.
- A model must improve recall without increasing irrelevant or boilerplate evidence before it can replace or augment BM25 in the evidence and answer evaluations.
