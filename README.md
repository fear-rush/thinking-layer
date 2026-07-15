# thinking-layer

The backend is in a destructive hard-cutover migration. Phases 0 and 1 are complete;
Phase 2—the source-backed corpus truth layer—is in progress. The legacy retrieval,
answering, API, and evaluation contracts remain removed and are not runnable.

The prior LiteParse output was discarded and replaced with a fresh, pinned,
OCR-disabled extraction from downloaded source documents. The current fresh-run
manifest inventories 3,816 PDFs: 3,767 were extracted, 48 OCR-required files were
skipped, and one parse failure was recorded. OCR remains disabled; every file named
by `reports/ocr_needed.json` is excluded before LiteParse is invoked and reported as
an explicit coverage limitation.

The generated raw records live under `processed/raw/liteparse/` and are intentionally
ignored by Git. They contain Markdown, text, text-item geometry, word boxes, source
hashes, extraction settings, and a reproducibility manifest. Do not replace them with
legacy raw extraction.

The restored commands are:

```sh
uv run python -m thinking_layer.cli extract
uv run python -m thinking_layer.cli build
```

The clean build currently classifies regulations, explanations, attachments,
circulars, and FAQs from source evidence. Legal paths are created only in normative
regulation/decision zones. Markdown blocks are validated against LiteParse geometry;
disagreements are quarantined and reported in the corpus manifest rather than guessed.

No full corpus, database, API, or coverage claim is published until the remaining
normalization, structural-audit, and clean-build acceptance gates in `PLAN.md` pass.
