# Agent Instructions

## Documentation

Use Context7 MCP for current documentation whenever a task involves a library, framework, SDK, API, CLI tool, or cloud service. Prefer Context7 over general web search. Do not use it for refactoring, business-logic debugging, code review, or general programming concepts.

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
