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

The generated corpus is a v2-only legal-unit contract. `processed/` is gitignored, so Git cannot recover a changed corpus, index, or OCR-enhanced raw extraction.

- Do not run `extract`, `all`, `build`, or `rebuild-blocks` for routine troubleshooting, frontend/API work, ranking work, or a stale index alone. Starting or restarting `uv run python -m thinking_layer.api` is sufficient for ordinary local use.
- Every searchable/citable corpus row must have `chunk_schema_version: 2`, an explicit legal path, node provenance, retrieval text, display text, anchors, and source block IDs. The only admissible v2 evidence units are atomic legal leaves and bounded `enumeration_aggregate` units; never restore sentence-block or inferred-citation compatibility paths.
- Before any accepted extraction replacement or corpus-wide migration, inspect `GET /healthz`, identify the changed input, and create or verify a complete backup of both `processed/` and generated reports. Rebuild only the downstream artifacts whose inputs changed.
- A full v2 legal-unit rebuild uses saved raw LiteParse pages with `rebuild-blocks`, then `report`, `build-source-corpus --include-secondary`, and `build-index`. The SQLite search index is the sole runtime index and citation lookup store. It requires explicit authorization and a verified backup.
- `rebuild-blocks` must skip every file currently listed in `reports/ocr_needed.json`. Do not enable OCR or re-run OCR as part of a legal-unit migration. Report the skipped file IDs/count and validate the resulting corpus coverage.
- For a document correction, use an explicit `extract --file-id ... --replace-existing` run only after a one-page review. Do not replace a document that is currently listed as OCR-needed without separate explicit OCR authorization.
- Use `build-index --incremental` only for compatible append-only source-corpus changes. A legal-unit migration or replacement requires a full SQLite index rebuild.

## React Server State

For the frontend, use TanStack Query for API-backed server state: queries, mutations, pending/error/success states, caching, and invalidation. Do not reintroduce manual request state through `useEffect` chains when a TanStack Query query or mutation is appropriate.

- Follow React's “You Might Not Need an Effect” guidance: calculate derived display data during render and handle user-triggered API calls in event handlers or TanStack Query mutations.
- Use `useEffect` only to synchronize with an external system that cannot be expressed through rendering, an event handler, or TanStack Query. Keep each required Effect narrowly scoped with complete dependencies and cleanup.
- Keep API request functions typed and centralized in the frontend API client. Use stable query keys for reads, and invalidate/update affected query keys after successful mutations when cached data becomes stale.

## Repository retrieval policy

Keep BM25/title retrieval as production default. Test semantic retrieval and reranking behind isolated commands and reports. A candidate must beat the local BM25 baseline without harming issuer/direct-topic coverage, citation quality, refusal boundaries, answer-noise checks, or latency.

For rerankers, start with BM25/title top-50 or top-100. Preserve role, issuer, direct-topic, citation-confidence, and answer-quality gates. Keep model-specific encoding rules in explicit configuration/helpers; never apply one prefix or pooling policy to every model. Do not change the active model or promote a candidate without passing the repository’s evaluation gates.

Research reports should include the exact CLI queries, model/paper links, tradeoffs, local results, and recommendation.
