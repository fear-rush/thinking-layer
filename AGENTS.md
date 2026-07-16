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

## Source Research

The backend and generated corpus have been reset. Work must follow `PLAN.md` and focus on understanding the two supported source systems before designing a parser or corpus.

- The only supported inputs are `data/ease-bi/` with `downloads/ease-bi/`, and `data/peraturan-ojk/` with `downloads/peraturan-ojk/`.
- Treat metadata as harvested assertions and provenance. Never merge metadata text into downloaded document text or present it as citable legal wording.
- Treat downloaded bytes as the evidence for wording and layout. Preserve every source occurrence and hash before deduplication.
- OCR remains disabled, but OCR triage is not a milestone. Mark unreadable files as deferred and continue studying readable documents. When extraction or parsing is eventually run, record every file and affected page that appears to need OCR in `reports/ocr_needed.json` and `reports/ocr_needed.md` without running OCR.
- Unknown, conflicting, unsupported, and unreadable files must remain explicit. Never default an unknown file to a primary regulation.
- Do not add a corpus builder, legal AST, database, retrieval system, answer renderer, or query API before the corresponding source-understanding gates in `PLAN.md` pass.
- Do not use mocks, fabricated source records, injected parser output, or runtime-generated expected values as evidence of source understanding or legal correctness.
- Generated research artifacts belong under `artifacts/` and may be deleted and rebuilt without compatibility or migration support.

## React Server State

For the frontend, use TanStack Query for API-backed server state: queries, mutations, pending/error/success states, caching, and invalidation. Do not reintroduce manual request state through `useEffect` chains when a TanStack Query query or mutation is appropriate.

- Follow React's “You Might Not Need an Effect” guidance: calculate derived display data during render and handle user-triggered API calls in event handlers or TanStack Query mutations.
- Use `useEffect` only to synchronize with an external system that cannot be expressed through rendering, an event handler, or TanStack Query. Keep each required Effect narrowly scoped with complete dependencies and cleanup.
- Keep API request functions typed and centralized in the frontend API client. Use stable query keys for reads, and invalidate/update affected query keys after successful mutations when cached data becomes stale.
