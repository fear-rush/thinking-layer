# thinking-layer

Local-first retrieval and citation system for Indonesian financial regulations.

The project processes local BI and OJK documents into structured legal units, builds a searchable SQLite index, retrieves relevant regulations and provisions, and serves source-backed answers through a CLI, FastAPI service, and web interface.

See [PLAN.md](PLAN.md) for the backend roadmap and implementation specification.

## Core Principles

- Keep document and provision retrieval separate.
- Preserve exact document, page, Pasal, Ayat, Huruf, and source-span provenance.
- Return readable legal context without inventing source text.
- Resolve every citation against the local database.
- State limitations when evidence, lifecycle information, or corpus coverage is incomplete.
- Keep data and query processing local by default.

## Architecture

```text
BI/OJK documents
  -> legal structure parser
  -> regulation catalog and lifecycle metadata
  -> legal units with citation provenance
  -> SQLite lexical index
  -> document and provision retrieval
  -> evidence validation
  -> structured answer and citations
  -> CLI / FastAPI / web UI
```

## Repository Layout

- `thinking_layer/corpus/`: document parsing, legal structure, catalog, lifecycle, and corpus generation.
- `thinking_layer/indexing/`: SQLite storage and lexical retrieval.
- `thinking_layer/retrieval/`: query interpretation, document search, provision search, and evidence validation.
- `thinking_layer/answer/`: structured answer composition.
- `thinking_layer/api/`: FastAPI routes, schemas, and services.
- `thinking_layer/evaluation/`: retrieval and answer evaluation.
- `frontend/`: Bun, React, Vite, TanStack Router/Query, and shadcn/ui application.
- `resources/`: configuration and reviewed evaluation resources.
- `reports/`: corpus and evaluation reports.
- `processed/`: generated corpus and indexes; ignored by Git.

## Run Locally

Start the backend from the repository root:

```bash
uv run python -m thinking_layer.api
```

Check backend health:

```bash
curl http://127.0.0.1:8000/healthz
```

Start the frontend in another terminal:

```bash
cd frontend
bun install
bun run dev
```

Open `http://localhost:3000`. The frontend proxies API requests to `http://127.0.0.1:8000`.

## API

Interactive API documentation is available at `http://127.0.0.1:8000/docs`.

| Endpoint | Purpose |
| --- | --- |
| `GET /healthz` | Report corpus, index, and citation lookup readiness. |
| `POST /queries` | Search regulations and return structured evidence. |
| `GET /documents/{file_id}` | Return cited document metadata. |
| `GET /documents/{file_id}/blocks/{block_id}` | Return an exact cited legal block. |
| `POST /feedback` | Store local answer feedback. |

Example query:

```bash
curl -X POST http://127.0.0.1:8000/queries \
  -H 'content-type: application/json' \
  -d '{"question":"Apa aturan periklanan bagi penyedia jasa pembayaran?"}'
```

## CLI

List available commands:

```bash
uv run python -m thinking_layer.cli --help
uv run python -m thinking_layer.cli COMMAND --help
```

## Corpus Coverage

OCR is currently disabled. Documents listed in `reports/ocr_needed.json` are excluded until OCR processing is explicitly enabled in future work.

Canonical source documents are stored under `data/peraturan-ojk` and `data/ease-bi`.
