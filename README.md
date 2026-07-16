# thinking-layer

The backend and generated corpus have been deliberately reset. The repository is
now in a source-understanding stage, not a corpus-building stage.

Only two harvested sources are in scope:

- `data/ease-bi/` with its downloaded files under `downloads/ease-bi/`;
- `data/peraturan-ojk/` with its downloaded files under
  `downloads/peraturan-ojk/`.

There is currently no parser, corpus, database, retrieval pipeline, answer service,
or runnable backend API. Old generated output and synthetic corpus tests were
deleted rather than preserved.

Metadata is treated as a source assertion and provenance sidecar. It must never be
mixed into citable document text. Downloaded files are the evidence to inspect and
eventually parse, after their roles and layout families have been reviewed.

The immediate work is direct document study: open real publication bundles, compare
their metadata and files, and write down the roles and recurring structures. OCR,
bulk extraction, parser code, and corpus generation must not delay that work.
When extraction or parsing eventually encounters unreadable files or pages, it will
document them in `reports/ocr_needed.json` and `reports/ocr_needed.md` for later OCR
work without stopping progress on readable documents.

Run `make baseline-check` to confirm that the reset boundaries still hold. The
detailed research and implementation sequence is in `PLAN.md`.
