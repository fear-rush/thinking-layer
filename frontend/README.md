# Thinking Layer Web UI

Local web client for the Thinking Layer citation-first regulation API.

## Run locally

Start the API from the repository root:

```bash
uv run python -m thinking_layer.api
```

In another terminal, start the frontend:

```bash
bun install
bun run dev
```

The Vite development server proxies `/v1/*` and `/healthz` to the local API at `http://127.0.0.1:8000`.

## Verify

```bash
bun run test
bun run build
```

## UI components

Add reusable UI primitives with shadcn/ui through Bun:

```bash
bunx --bun shadcn@latest add button
```

Routes are file-based and live in `src/routes/`. Regenerate the route tree after adding or removing routes:

```bash
bun run generate-routes
```
