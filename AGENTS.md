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

## Corpus Generation

The backend is undergoing a hard migration. Generated blocks, source-corpus rows, catalogs, reports, and indexes may be deleted and rebuilt whenever their schema or producing code changes. No compatibility path, incremental migration, backup, or preservation of obsolete generated artifacts is required.

- OCR is disabled for this migration. Never enable or run OCR.
- Every file listed in `reports/ocr_needed.json` must be excluded from parsing, cataloging, indexing, evaluation targets, and coverage claims until OCR work is explicitly authorized in a future request.
- A rebuild must report the skipped OCR-needed file IDs and count so the API can expose the resulting corpus limitation honestly.

## React Server State

For the frontend, use TanStack Query for API-backed server state: queries, mutations, pending/error/success states, caching, and invalidation. Do not reintroduce manual request state through `useEffect` chains when a TanStack Query query or mutation is appropriate.

- Follow React's “You Might Not Need an Effect” guidance: calculate derived display data during render and handle user-triggered API calls in event handlers or TanStack Query mutations.
- Use `useEffect` only to synchronize with an external system that cannot be expressed through rendering, an event handler, or TanStack Query. Keep each required Effect narrowly scoped with complete dependencies and cleanup.
- Keep API request functions typed and centralized in the frontend API client. Use stable query keys for reads, and invalidate/update affected query keys after successful mutations when cached data becomes stale.
