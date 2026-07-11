# Semantic Retrieval Smoke

This is an implementation smoke check for the isolated dense-retrieval path. It is not a production-quality or model-selection result.

- Model: `intfloat/multilingual-e5-small`
- Embedding dimensions: `384`
- Index size: `5,000` source-corpus blocks
- Normalization: enabled
- Corpus signature: persisted in `processed/semantic_index/metadata.json`
- Query: `peraturan BI tentang penyedia jasa pembayaran`
- Filter: issuer `BI`, secondary sources included

The query returned `PBI No.23/6/PBI/2021 - Penyedia Jasa Pembayaran` at rank 1 with a semantic score of approximately `0.909`.

This confirms the model, persisted index, CLI path, filtering, and citation metadata work together. The top five results are mostly blocks from the same document, including legal-basis and continuation text; therefore this smoke check does not establish evidence quality, document-level recall, deduplication quality, or superiority over BM25. Those require the planned model matrix and dense/BM25/RRF evaluation.
