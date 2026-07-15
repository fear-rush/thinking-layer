# thinking-layer

Local-first retrieval and citation pipeline for Indonesian financial regulations.

The system audits local BI and OJK sources, extracts citation-aware legal text, builds a BM25 index, retrieves evidence, and serves deterministic answers through a CLI, FastAPI service, and local web UI. It must refuse unsupported conclusions and must never invent a document, page, Pasal, Ayat, or Huruf.

## Current State

The working baseline includes:

- canonical BI and OJK metadata;
- v2-only hierarchical legal units with deterministic IDs, page spans, legal paths, retrieval text, and citation display text;
- persisted lexical retrieval with a sole SQLite BM25 index;
- query planning, evidence confidence, and citation-quality gates;
- deterministic answer composition with `answerable`, `partial`, and `not_found` outcomes;
- a local FastAPI service and browser UI;
- unit, evaluation, and browser/API test suites.

Canonical searchable regulations come from `data/peraturan-ojk` and `data/ease-bi`. `data/sikepo-ojk` is used for audit and enrichment research, but is not merged into the canonical searchable OJK documents.

## Pipeline

```text
local BI/OJK files
  -> raw page extraction
  -> legal-unit blocks with provenance
  -> citation-ready source corpus
  -> BM25 retrieval and query planning
  -> evidence selection and confidence gates
  -> structured findings
  -> CLI / FastAPI / web UI
```

SQLite is the sole persisted production BM25 index and exact citation lookup store. Search and cited-document routes remain degraded until that index is current.

## Repository Layout

- `thinking_layer/corpus/`: metadata, extraction, legal blocks, citations, and source-corpus construction.
- `thinking_layer/indexing/`: lexical, SQLite, title, and isolated semantic indexes.
- `thinking_layer/retrieval/`: query planning, search, evidence packing, and topic coverage.
- `thinking_layer/answer/`: deterministic answer selection, composition, and quality checks.
- `thinking_layer/api/`: FastAPI schemas, routes, services, and local feedback storage.
- `thinking_layer/evaluation/`: the v2 exact-target golden evaluation runner and workflow.
- `frontend/`: Bun, Vite, React, TanStack Router/Query, shadcn/ui, Vitest, and Playwright.
- `resources/config/`: explicit extraction, ranking, confidence, and answer heuristics.
- `resources/`: the active query lexicon, reviewed lexicon provenance, stopwords, configuration, and the v2 golden suite.
- `reports/`: current corpus reports and retained terminal v2 evaluation evidence.
- `processed/`: expensive generated corpus and indexes; intentionally ignored by Git.

Use the current CLI as the command reference:

```bash
uv run python -m thinking_layer.cli --help
uv run python -m thinking_layer.cli COMMAND --help
```

## Run Locally

The ordinary local workflow does not require extraction or an index rebuild.

Start the API from the repository root:

```bash
uv run python -m thinking_layer.api
```

Confirm the active source-corpus, index, and citation-lookup state:

```bash
curl http://127.0.0.1:8000/healthz
```

Start the frontend in another terminal:

```bash
cd frontend
bun install
bun run dev
```

Open `http://localhost:3000`. Vite proxies `/v1/*` and `/healthz` to the API at `http://127.0.0.1:8000`.

Inspect the same answer path from the CLI:

```bash
uv run python -m thinking_layer.cli plan-query "Apa ketentuan BI tentang penyedia jasa pembayaran?"
uv run python -m thinking_layer.cli evidence "Apa ketentuan BI tentang penyedia jasa pembayaran?" --write-report
uv run python -m thinking_layer.cli answer "Apa ketentuan BI tentang penyedia jasa pembayaran?" --write-report
uv run python -m thinking_layer.cli trace-query "Apa ketentuan BI tentang penyedia jasa pembayaran?" --write-report
```

Reports requested with `--write-report` are written under `reports/`.

## Local API

The API listens on `127.0.0.1:8000`. Interactive OpenAPI documentation is available at `http://127.0.0.1:8000/docs`.

| Endpoint | Purpose |
| --- | --- |
| `GET /healthz` | Report source-corpus, SQLite, lexical-index, and citation-lookup readiness. |
| `POST /v1/queries` | Run the deterministic query, evidence, and answer path. |
| `GET /v1/documents/{file_id}` | Return metadata for a cited document. |
| `GET /v1/documents/{file_id}/blocks/{block_id}` | Return an exact cited block and its legal metadata. |
| `POST /v1/feedback` | Store local helpful/not-helpful feedback. |

Example:

```bash
curl -X POST http://127.0.0.1:8000/v1/queries \
  -H 'content-type: application/json' \
  -d '{"question":"Apa ketentuan BI tentang penyedia jasa pembayaran?"}'
```

The API is read-only for corpus and index data. Query traces remain internal, and raw questions or evidence snippets must not be sent to hosted observability services without an explicit privacy and redaction decision.

## Generated Corpus Safety

Files under `processed/` are expensive local artifacts. The searchable corpus is v2-only: each row carries an explicit legal-unit path, deterministic node provenance, page anchors, source spans, retrieval text, and display text. Atomic legal leaves are indexed alongside bounded enumeration aggregates that keep a governing list readable.

Do not run `extract`, `all`, `build`, or `rebuild-blocks` as routine troubleshooting, for frontend/API work, or because an index appears stale. Check `GET /healthz`, identify the changed input, and use the narrowest operation.

| Change | Safe action |
| --- | --- |
| API, frontend, query planning, ranking, or answer presentation | Restart the API and run focused tests. Do not rebuild corpus artifacts. |
| Legal-unit parser or citation-contract change | Use unit fixtures and saved raw-page samples first. Do not rewrite `processed/blocks.ndjson` until the new boundaries are accepted. |
| One incorrect document | Test one page, then use `extract --file-id ... --replace-existing`. |
| Accepted extraction replacement | Refresh the report and source corpus, then rebuild the SQLite index. |
| Accepted corpus-wide chunking change | Back up `processed/`, rebuild blocks from saved raw extraction, inspect the diff/report, then rebuild downstream artifacts. |
| Append-only source-corpus update | Use `build-index --incremental` only when the existing index is compatible. |

### Targeted Document Repair

Test one page before replacing a complete file:

```bash
uv run python -m thinking_layer.cli extract \
  --file-id FILE_ID \
  --target-pages 1 \
  --max-pages 1 \
  --replace-existing \
  --progress-every 1 \
  --verbose
```

For an OCR-needed file, add `--enable-ocr` and the configured OCR server options only after the one-page output has been reviewed. OCR remains off for normal extraction.

After an accepted file replacement:

```bash
uv run python -m thinking_layer.cli report
uv run python -m thinking_layer.cli build-source-corpus --include-secondary
uv run python -m thinking_layer.cli build-index
```

### Accepted Corpus-Wide Legal-Unit Migration

`rebuild-blocks` rewrites the v2 legal-unit corpus from saved raw LiteParse JSON. Run it only after fixture-level and representative-document review, explicit approval, and a verified backup of `processed/` and generated reports. It automatically skips every file listed in `reports/ocr_needed.json`; do not enable OCR as part of this migration.

```bash
uv run python -m thinking_layer.cli rebuild-blocks
uv run python -m thinking_layer.cli report
uv run python -m thinking_layer.cli build-source-corpus --include-secondary
uv run python -m thinking_layer.cli build-index
```

## Verification

Backend tests:

```bash
uv run python -m unittest discover -s tests -v
```

Frontend checks:

```bash
cd frontend
bun run test
bun run typecheck
bun run lint
bun run format:check
bun run build
bun run test:e2e
```

Install the Playwright Chromium runtime once if needed:

```bash
cd frontend
bunx playwright install chromium
```

The browser suite uses an isolated API fixture and does not read or rebuild generated corpus artifacts.

Validate the exact citation targets before evaluating answers:

```bash
uv run python -m thinking_layer.evaluation.golden \
  --tier smoke \
  --preflight-only
```

Run the 12-case smoke tier during routine backend work, then the complete 44-case suite only when the index under test is ready:

```bash
uv run python -m thinking_layer.evaluation.golden \
  --tier smoke \
  --jobs 1 \
  --output reports/golden_v2_smoke_current.json

uv run python -m thinking_layer.evaluation.golden \
  --tier full \
  --jobs 1 \
  --output reports/golden_v2_full_current.json
```

The runner checks exact legal-unit retrieval, v2 citation provenance, answer boundaries, issuer coverage, and refusal behavior. See `thinking_layer/evaluation/README.md` for filtering and baseline-comparison commands. Evaluation scores are regression signals, not proof of legal accuracy.

## Retrieval and Answer Invariants

- Prefer primary regulations over summaries, FAQs, and operational guidance.
- Preserve issuer and direct-topic coverage for BI/OJK comparison questions.
- Treat adjacent evidence as context, not direct evidence for the requested topic.
- Preserve exact file, page, Pasal, Ayat, and Huruf provenance when available.
- Never infer missing citation fields.
- Refuse when evidence is weak, conflicting, or absent.
- Exclude legal boilerplate unless the question explicitly asks for it.
- Keep semantic retrieval and reranking isolated until they beat BM25 without harming citations, refusal boundaries, coverage, or latency.

## Deferred Work

Semantic/hybrid retrieval, reranking, query expansion, graph retrieval, and LLM answer generation remain experiments. Revisit them only after coherent legal units and structured answers are stable and a candidate demonstrates a measured improvement over the BM25 baseline. Authentication and permissions remain unnecessary while the corpus and history are local and non-restricted.

## Reports

Use `reports/REPORT_INDEX.md` as the map of the deliberately small retained report set. The current acceptance evidence is:

- `reports/v2_corpus_audit.json`
- `reports/golden_v2_preflight_terminal.json`
- `reports/golden_v2_smoke_terminal.json`
- `reports/golden_v2_full_terminal.json`
- `reports/golden_v2_post_rebuild_analysis.md`

Regenerate reports into explicit `*_current` or task-specific paths while iterating. Promote a result to a terminal baseline only after the v2 preflight passes and the selected case IDs match the comparison baseline.
