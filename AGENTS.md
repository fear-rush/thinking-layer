# Agent Instructions

## Documentation

Use Context7 MCP for current documentation whenever a task involves a library, framework, SDK, API, CLI tool, or cloud service. Prefer Context7 over general web search. Do not use it for refactoring, business-logic debugging, code review, or general programming concepts.

## Frontend

The `frontend/` directory contains the web application that consumes this project's API. Use the following stack and conventions for all frontend work:

- Use Bun as the runtime and package manager. Run frontend scripts and add dependencies with `bun`; do not introduce npm, pnpm, or Yarn lockfiles or workflows.
- Use Vite with Rolldown as the bundler. Keep Vite build configuration compatible with Rolldown; do not add Rollup-specific build configuration.
- Use TanStack Router and **always use its file-based routing**. Define routes as route files in the router's routes directory and keep generated route-tree files in sync. Do not introduce code-defined/manual route registration as an alternative routing system.
- Use Oxlint for linting and Oxfmt for formatting (the Oxc toolchain). Do not add ESLint or Prettier.
- Use Vitest for frontend unit and component tests. Do not introduce another JavaScript test runner unless explicitly requested.
- Build UI with shadcn/ui components first. Before creating a custom primitive or component, check whether shadcn/ui provides a suitable component and compose or extend it when it does. Create custom UI only when shadcn/ui cannot meet the need.

## Generated Corpus Safety

The extracted corpus and indexes are expensive generated assets. `processed/` is gitignored, so a plain extraction can overwrite OCR-enhanced output without Git being able to restore it.

- Do not run `uv run python -m thinking_layer.cli extract`, `all`, or `build` as a generic troubleshooting step, for frontend/API work, or merely because an index is stale.
- Treat an unscoped `extract` as a full corpus rewrite. Run it only for an explicitly requested full re-extraction and only after making or confirming a backup of the current generated artifacts.
- For OCR, parsing, or document corrections, use explicit `--file-id ... --replace-existing` runs. Test one page before replacing a full file; never start full-corpus OCR by default.
- Rebuild downstream artifacts only after their inputs changed: run `report`, `build-source-corpus --include-secondary`, `build-index`, and `build-document-catalog` after an accepted extraction replacement. Do not rebuild them for UI-only, API-only, query-planning, ranking, or answer-presentation changes.
- Before suggesting or executing a rebuild, inspect `GET /healthz`, identify exactly which input changed, and choose the narrowest command. Use `build-index --incremental` only for compatible append-only source-corpus changes.
- Starting or restarting `uv run python -m thinking_layer.api` is sufficient for ordinary local use; it does not require extraction, corpus, index, or catalog rebuilds.

## Hugging Face research

Use the Hugging Face Hub CLI (`hf`) for current model, embedding, reranker, quantization, compatibility, and local-inference research. If `hf` is not on `PATH`, use `$HOME/.local/bin/hf`. Do not choose models from memory, download counts, or leaderboard rank alone.

```bash
hf models list --search "multilingual embedding retrieval" --limit 20 --sort downloads --format json
hf models info MODEL_ID --expand=downloads,likes,tags,config,cardData,safetensors,transformersInfo --format json
hf models card MODEL_ID --text
hf papers search "legal multilingual retrieval reranking" --limit 10 --format json
hf papers read PAPER_ID
```

For each serious candidate, check and record:

- exact model ID/revision, task and architecture;
- Indonesian/language coverage and linked paper;
- license and commercial restrictions;
- parameters, dimensions, context length, memory, and latency;
- pooling, normalization, query/document prefixes or instructions;
- `trust_remote_code`, custom code, quantization, device, and SentenceTransformers/Transformers support.

## Repository retrieval policy

Keep BM25/title retrieval as production default. Test semantic retrieval and reranking behind isolated commands and reports. A candidate must beat the local BM25 baseline without harming issuer/direct-topic coverage, citation quality, refusal boundaries, answer-noise checks, or latency.

For rerankers, start with BM25/title top-50 or top-100. Preserve role, issuer, direct-topic, citation-confidence, and answer-quality gates. Keep model-specific encoding rules in explicit configuration/helpers; never apply one prefix or pooling policy to every model. Do not change the active model or promote a candidate without passing the repository’s evaluation gates.

Research reports should include the exact CLI queries, model/paper links, tradeoffs, local results, and recommendation.
