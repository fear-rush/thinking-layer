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
hashes, source URLs when harvested, extraction settings, and a reproducibility
manifest. A missing harvested source URL remains `null`; URLs are never inferred from
file names, titles, or paths. Do not replace them with legacy raw extraction.

The restored commands are:

```sh
uv run python -m thinking_layer.cli extract
uv run python -m thinking_layer.cli build
```

The clean build emits a versioned `LegalDocumentV1` JSON AST and its JSON Schema. It
classifies regulations, explanations, attachments, circulars, and FAQs from source
evidence. Legal paths are created only in normative regulation/decision zones.
Markdown blocks are validated against LiteParse geometry; disagreements are
quarantined and reported rather than guessed.

The latest full-corpus build is intentionally unpublished: its durable failure report
is `processed/corpus.failure.json`. It currently reports incomplete legal fragments at
source boundaries and Markdown-presentation leakage findings. These are Phase 2
acceptance-gate failures, not published corpus coverage. The builder preserves the
machine-readable report before removing failed staging output.

No full corpus, database, API, or coverage claim is published until the remaining
normalization, fragment-handling, structural-audit, and clean-build acceptance gates
in `PLAN.md` pass. Phase 3's SQLite build begins only after that publication gate.
