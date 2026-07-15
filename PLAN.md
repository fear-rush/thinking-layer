# Backend Hard-Cutover Plan

Status: approved for destructive implementation, not yet implemented

Scope: backend, generated corpus, catalog, index, API contract, evaluation, tests, resources, and reports

Compatibility policy: none

OCR policy: disabled; every document in `reports/ocr_needed.json` is skipped

## Directive

This is a hard replacement, not an incremental refactor. The current query planner, retrieval orchestration, answer heuristics, confidence model, golden evaluator, and backend test suite will be deleted. There will be one backend architecture, one corpus contract, one index schema, one API response contract, and one test strategy.

The migration will not provide:

- compatibility wrappers;
- old and new execution paths;
- schema adapters for obsolete generated artifacts;
- fallback to the existing planner, search, confidence, composer, or evaluator;
- deprecated API fields;
- preservation of tests merely because they currently pass;
- preservation of generated indexes or reports;
- prompt-specific exceptions for known questions.

Breaking imports, CLI commands, generated artifacts, fixtures, API payloads, and frontend integration during the backend cutover is acceptable. All consumers must move to the new contract together.

## Why the current backend is being replaced

The current runtime does not learn. It maps prompts through regexes, a manually expanded lexicon, issuer assumptions, hand-tuned boosts, query-specific branches, and a confidence mixture that can reward provenance while the cited clause is irrelevant. That is pattern memorization, not legal understanding.

The existing parser has useful ideas, especially legal paths and source spans, but useful code is not a reason to preserve its interface. Any algorithm reused during the rewrite must satisfy the new contract and new tests. Nothing survives solely for backward compatibility.

The demonstrated failures are architectural:

- a document-discovery question is forced through a provision-answer path;
- document-title relevance leaks into claim relevance;
- fragments are rendered without their governing lead-in;
- issuer and topic mappings behave as hidden hard filters;
- lifecycle state is unknown but answers can look authoritative;
- confidence is not calibrated;
- visible goldens encourage tuning to known prompts;
- mocks can pass while the real API and index fail;
- stale reports are presented too close to current evidence;
- the test suite asserts implementation details instead of user-visible legal behavior.

## Non-negotiable target

The completed backend must:

1. parse source-backed legal structure into complete, readable, citable units;
2. build canonical instrument identities without collisions;
3. record source-backed amendment, revocation, supersession, partial-revocation, and unknown lifecycle state;
4. distinguish document discovery, exact lookup, rule, definition, value, procedure, comparison, and lifecycle questions;
5. retrieve documents first and provisions only inside selected document scope;
6. calculate passage relevance from claim text rather than title or generated search text;
7. return complete source-backed context while citing the exact underlying units;
8. expose independent evidence diagnostics rather than a probability-like confidence score;
9. resolve every citation against the active database;
10. pass real-index paraphrase, negative, lifecycle, readability, refusal, latency, and citation tests;
11. expose skipped OCR-needed coverage as an explicit limitation;
12. provide a deterministic evidence contract suitable for a later constrained LLM.

## Destructive migration rules

- Delete obsolete code before implementing its replacement. A temporarily broken branch is acceptable during the cutover.
- Do not create compatibility modules under old import paths.
- Do not preserve old JSON shapes, SQLite tables, CLI flags, test fixtures, or report formats.
- Delete and recreate generated legal blocks, source-corpus rows, catalog tables, and indexes when the producing contract changes.
- Do not use an incremental index migration. Build the new database from an empty target.
- Do not copy the old golden suite into the new release gate.
- Do not tune against the sealed evaluation set.
- Do not add a query string, known answer phrase, regulation name, or issuer-specific exception merely to pass one question.
- OCR remains disabled. Exclude every file in `reports/ocr_needed.json` from all generated datasets and report the exclusion.

## Target architecture

```text
source documents and saved non-OCR raw pages
  -> document eligibility filter
       exclude reports/ocr_needed.json
  -> legal structure parser
       source nodes + hierarchy + spans + contextual units
  -> regulation catalog and lifecycle graph
  -> clean SQLite database
       regulations
       source_documents
       lifecycle_relations
       legal_nodes
       contextual_units
       lexical index
  -> typed QuerySpec
  -> document retrieval
  -> provision retrieval within selected documents
  -> evidence gates
  -> mode-specific response renderer
  -> database-resolved citations
  -> API
  -> real-index acceptance evaluation
```

No title text, query expansion, or issuer prior may satisfy provision-level claim relevance.

## File destruction manifest

The following files will be deleted rather than adapted.

### Runtime modules to delete

- `thinking_layer/answer/alignment.py`
- `thinking_layer/answer/composer.py`
- `thinking_layer/answer/noise.py`
- `thinking_layer/answer/quality.py`
- `thinking_layer/retrieval/evidence.py`
- `thinking_layer/retrieval/planning.py`
- `thinking_layer/retrieval/query_tools.py`
- `thinking_layer/retrieval/search.py`
- `thinking_layer/retrieval/topic_coverage.py`
- `thinking_layer/indexing/scoring.py`
- `thinking_layer/indexing/semantic.py`
- `thinking_layer/indexing/title.py`
- `thinking_layer/config/heuristic_audit.py`
- `thinking_layer/config/heuristics.py`
- `thinking_layer/lexicon/candidates.py`
- `thinking_layer/lexicon/merge.py`
- `thinking_layer/evaluation/golden.py`

Empty package initializers will be rewritten only when required by the new package layout.

### Heuristic and golden resources to delete

- `resources/query_lexicon.json`
- `resources/query_lexicon.reviewed.json`
- `resources/golden_questions.json`
- `resources/config/answer_noise.json`
- `resources/config/answer_ranking.json`
- `resources/config/cross_regulator_confidence.json`
- `resources/config/evaluation_rubrics.json`
- `resources/config/evidence_confidence.json`
- `resources/config/retrieval_ranking.json`
- `resources/config/semantic_retrieval.json`

Extraction configuration is not automatically trusted. The following files will be reviewed against the rewritten parser and either rewritten or deleted if their settings no longer have a measured purpose:

- `resources/config/extraction_heuristics.json`
- `resources/config/extraction_spot_check.json`
- `resources/config/lexicon_extraction.json`
- `resources/indonesian-stopwords-complete.txt`

### Current backend tests to delete

- `tests/acceptance/test_live_query_api.py`
- `tests/browser_api_app.py`
- `tests/test_answer_alignment.py`
- `tests/test_answer_noise.py`
- `tests/test_answer_quality.py`
- `tests/test_api.py`
- `tests/test_citations.py`
- `tests/test_corpus_audit.py`
- `tests/test_corpus_hygiene.py`
- `tests/test_evidence_answer.py`
- `tests/test_extraction.py`
- `tests/test_extraction_pipeline.py`
- `tests/test_geometry.py`
- `tests/test_golden_evaluation.py`
- `tests/test_imports_cli.py`
- `tests/test_legal_units.py`
- `tests/test_metadata.py`
- `tests/test_normalization.py`
- `tests/test_pipeline_contract.py`
- `tests/test_pjp_title_retrieval.py`
- `tests/test_query_planning.py`
- `tests/test_query_presenter.py`
- `tests/test_query_service_enumeration.py`
- `tests/test_retrieval_legal_constraints.py`
- `tests/test_topic_coverage.py`

The `tests/` tree will then be recreated from an empty directory. No assertion or fixture will be copied without being rewritten from the new public contract or an independently reviewed legal target.

### Stale reports to delete

- `reports/golden_full_terminal.json`
- `reports/golden_preflight_terminal.json`
- `reports/golden_smoke_terminal.json`
- `reports/golden_terminal_analysis.md`
- obsolete entries in `reports/REPORT_INDEX.md`

`reports/ocr_needed.json` remains because it is the authoritative exclusion list. Corpus inventory reports may be regenerated in a new format; they are not compatibility artifacts.

### Generated artifacts to destroy and recreate

The implementation must discover the exact paths through `thinking_layer/config/paths.py`, then delete the generated artifacts for:

- legal-unit blocks;
- source-corpus rows;
- regulation catalog;
- document catalog;
- SQLite search and citation database;
- semantic indexes, if present;
- cached evaluation output;
- generated reports that encode the old schema.

Saved non-OCR raw page extraction may be reused only as input. It does not define the new legal-unit or index contract.

## New package layout

### Domain contracts to add

- `thinking_layer/domain/legal.py`
  - instrument identity, source document, lifecycle relation, legal node, contextual unit, and citation models.
- `thinking_layer/domain/query.py`
  - `QuerySpec`, explicit constraints, answer mode, requested predicate, requested shape, and ambiguity model.
- `thinking_layer/domain/evidence.py`
  - document candidate, provision candidate, evidence group, and independent gate results.
- `thinking_layer/domain/response.py`
  - one API response contract with document results, findings, citations, limitations, and diagnostics.

### Corpus implementation to add

- `thinking_layer/corpus/parser.py`
  - parse hierarchy and source spans from eligible saved raw pages.
- `thinking_layer/corpus/catalog.py`
  - construct non-colliding regulation and source-document records.
- `thinking_layer/corpus/lifecycle.py`
  - build and validate source-backed lifecycle relations.
- `thinking_layer/corpus/context.py`
  - construct complete contextual units without destroying atomic citation targets.
- `thinking_layer/corpus/builder.py`
  - orchestrate a clean full build and emit a reproducibility manifest.
- `thinking_layer/corpus/eligibility.py`
  - load `reports/ocr_needed.json`, exclude those files, and emit coverage limitations.

### Index implementation to add

- `thinking_layer/indexing/schema.py`
  - define the only accepted SQLite schema.
- `thinking_layer/indexing/bm25.py`
  - generic lexical indexing and scoring with no prompt-specific boosts.
- `thinking_layer/indexing/repository.py`
  - typed database reads for catalog, nodes, context, and citations.
- `thinking_layer/indexing/build.py`
  - create a new database atomically from accepted corpus outputs.

### Retrieval implementation to add

- `thinking_layer/retrieval/query_spec.py`
  - parse explicit syntax and construct a typed query contract.
- `thinking_layer/retrieval/document_search.py`
  - rank canonical regulation documents.
- `thinking_layer/retrieval/provision_search.py`
  - rank claim-bearing units within selected documents.
- `thinking_layer/retrieval/gates.py`
  - independently validate document relevance, claim relevance, lifecycle, citation integrity, answer shape, readability, and corpus scope.
- `thinking_layer/retrieval/pipeline.py`
  - orchestrate one execution path without fallbacks.

### Answer implementation to add

- `thinking_layer/answer/document_list.py`
  - render regulation-discovery results.
- `thinking_layer/answer/extractive.py`
  - render exact lookup and source-backed substantive findings.
- `thinking_layer/answer/comparison.py`
  - render independently supported sides without inventing missing comparisons.
- `thinking_layer/answer/renderer.py`
  - dispatch by answer mode and revalidate the final response.

### Evaluation implementation to add

- `thinking_layer/evaluation/datasets.py`
  - load development, negative, lifecycle, and sealed manifests.
- `thinking_layer/evaluation/citation_verifier.py`
  - resolve every citation from SQLite rather than trusting API output.
- `thinking_layer/evaluation/metrics.py`
  - report retrieval, citation, status, readability, lifecycle, refusal, and latency metrics separately.
- `thinking_layer/evaluation/runner.py`
  - exercise the real query pipeline and pinned database.
- `resources/evaluation/development.jsonl`
- `resources/evaluation/negatives.jsonl`
- `resources/evaluation/lifecycle.jsonl`
- `resources/evaluation/holdout.jsonl`
- `resources/regulation_relations.reviewed.json`

## Existing files to rewrite in place

These paths remain only because they are useful public entry points. Their internal contracts may break completely.

- `thinking_layer/cli.py`
  - replace old planning, evidence, answer, golden, and build commands with clean build, query, trace, evaluate, and audit commands.
- `thinking_layer/config/paths.py`
  - remove old generated paths and define the new build outputs.
- `thinking_layer/common/text.py`
  - keep only generic normalization proven by language-level tests.
- `thinking_layer/common/io.py`
  - support atomic writes and reproducibility manifests.
- `thinking_layer/observability.py`
  - record stage timings, candidate counts, gate failures, database hash, and skipped corpus coverage.
- `thinking_layer/api/app.py`
- `thinking_layer/api/dependencies.py`
- `thinking_layer/api/routers/queries.py`
- `thinking_layer/api/routers/documents.py`
- `thinking_layer/api/routers/health.py`
- `thinking_layer/api/schemas/queries.py`
- `thinking_layer/api/schemas/documents.py`
- `thinking_layer/api/schemas/health.py`
- `thinking_layer/api/presenters/queries.py`
- `thinking_layer/api/services/query_service.py`
- `thinking_layer/api/services/documents.py`
- `thinking_layer/api/services/health.py`
  - replace the old query and citation contract with the new domain models and database repository.
- `thinking_layer/api/routers/feedback.py`
- `thinking_layer/api/schemas/feedback.py`
- `thinking_layer/api/services/feedback.py`
  - either update to the new response identity or delete if feedback has no immediate evaluation use.
- `thinking_layer/corpus/audit.py`
- `thinking_layer/corpus/corpus_audit.py`
- `thinking_layer/corpus/quality.py`
- `thinking_layer/corpus/spot_check.py`
  - replace old block assumptions with new structural and coverage audits, or delete when duplicated by the builder.

The following old corpus files will be deleted after their required algorithms have been independently reimplemented in the new package layout:

- `thinking_layer/corpus/build.py`
- `thinking_layer/corpus/citations.py`
- `thinking_layer/corpus/extraction.py`
- `thinking_layer/corpus/extraction_pipeline.py`
- `thinking_layer/corpus/geometry.py`
- `thinking_layer/corpus/legal_units.py`
- `thinking_layer/corpus/metadata.py`
- `thinking_layer/corpus/normalization.py`
- `thinking_layer/corpus/parser_comparison.py`
- `thinking_layer/corpus/source_corpus.py`

This is algorithm extraction, not interface preservation. Old imports and generated fields will not survive.

## API hard cutover

`POST /queries` remains the conceptual entry point but its payload and response version are not preserved. The frontend will be broken until it is updated later.

The new response contains:

- `request_id`;
- `status`: `complete`, `partial`, `not_found`, `ambiguous`, or `unsupported_scope`;
- `mode`;
- `summary`;
- `documents` for document discovery;
- `findings` for provision answers;
- database-resolved `citations`;
- explicit `limitations`;
- independent `diagnostics`;
- `coverage`, including skipped OCR-needed documents;
- stage timings.

The following old behavior is removed:

- probability-like `confidence.score`;
- title-derived support for a finding;
- representative provision blocks standing in for documents;
- related-document output that is not independently relevant;
- hidden query expansions;
- arbitrary sibling enrichment;
- exact-prompt branches;
- successful status computed before final findings are validated.

## Test strategy: delete and rebuild

The new suite tests system behavior through real data boundaries. Mocks are permitted only for external failure injection such as a corrupt file or unavailable database. A mock may never be used as evidence of retrieval accuracy, citation validity, legal correctness, or API acceptance.

### New unit tests

- `tests/unit/domain/test_instrument_identity.py`
- `tests/unit/domain/test_query_spec.py`
- `tests/unit/corpus/test_parser_boundaries.py`
- `tests/unit/corpus/test_context_assembly.py`
- `tests/unit/corpus/test_ocr_exclusion.py`
- `tests/unit/corpus/test_lifecycle_relations.py`
- `tests/unit/indexing/test_schema.py`
- `tests/unit/retrieval/test_evidence_gates.py`
- `tests/unit/answer/test_response_contract.py`

Unit fixtures must be minimal source-like legal text with independently written expected structure. They must not copy runtime output into expected values.

### New integration tests

- `tests/integration/test_clean_corpus_build.py`
- `tests/integration/test_clean_index_build.py`
- `tests/integration/test_document_retrieval.py`
- `tests/integration/test_provision_retrieval.py`
- `tests/integration/test_citation_resolution.py`
- `tests/integration/test_query_pipeline.py`
- `tests/integration/test_api_real_database.py`

Integration tests build or use a pinned miniature SQLite database from source fixtures. They do not patch search results or inject expected candidates.

### New acceptance tests

- `tests/acceptance/test_document_discovery.py`
- `tests/acceptance/test_exact_lookup.py`
- `tests/acceptance/test_rule_questions.py`
- `tests/acceptance/test_definition_and_value.py`
- `tests/acceptance/test_comparison.py`
- `tests/acceptance/test_lifecycle.py`
- `tests/acceptance/test_refusal_and_scope.py`
- `tests/acceptance/test_paraphrase_families.py`
- `tests/acceptance/test_readability.py`
- `tests/acceptance/test_latency.py`

Acceptance tests call the real API with the current full database. They verify database-resolved citations and user-visible behavior. The two demonstrated questions must be included only as members of larger paraphrase families, never as special single-case gates.

### Evaluation datasets

- Development cases are visible and may diagnose failure classes.
- Each information need has independently written Indonesian paraphrases.
- Negatives reuse topics with the wrong issuer, predicate, entity, date, or legal unit.
- Lifecycle cases cover active, amended, revoked, partially revoked, unknown, and as-of queries.
- Holdout cases are split by legal information need and document family, not by wording.
- Holdout prompts remain sealed during tuning. Only aggregate metrics are inspected until a release cycle closes.

### Required metrics

- document Recall@5, Recall@10, MRR, and nDCG@10;
- provision Recall@5, Recall@20, MRR, and nDCG@20;
- exact-anchor accuracy;
- citation precision and recall;
- complete-context rate;
- answer-shape completeness;
- lifecycle correctness;
- false-answer and false-refusal rates;
- status macro-F1 and confusion matrix;
- paraphrase-family pass rate and worst-family score;
- p50, p95, and maximum latency;
- skipped-document count and corpus coverage;
- source, corpus, database, evaluation, configuration, and Git hashes.

No aggregate accuracy number may hide a failed citation, lifecycle, refusal, or worst-family gate.

## Implementation phases

### Phase 1: demolition

1. Create a Git checkpoint only for forensic recovery, not runtime compatibility.
2. Delete every file in the destruction manifest.
3. Delete the current `tests/` tree.
4. Delete old generated blocks, source corpus, catalogs, indexes, semantic artifacts, and evaluation caches.
5. Remove dead imports, commands, Makefile targets, dependencies, and README instructions.
6. Confirm that no old planner, search, confidence, composer, golden, or fallback symbol remains with `rg`.

Exit gate: the old backend cannot run and no compatibility path exists.

### Phase 2: domain and corpus truth layer

1. Implement domain models and OCR eligibility filtering.
2. Rewrite legal structure parsing against representative saved raw pages from multiple BI and OJK document families.
3. Build atomic legal nodes, explicit hierarchy, contextual units, and source spans.
4. Build collision-resistant instrument identity and source-document identity.
5. Build source-backed lifecycle relations and preserve unknown state.
6. Add structural audits for dangling fragments, missing lead-ins, duplicate identities, relation cycles, bad spans, and unresolved sources.
7. Write the new unit and clean-build integration tests.

Exit gate: eligible documents produce reproducible, readable, database-ready legal units; OCR-needed documents are absent and reported.

### Phase 3: clean database build

1. Implement the new schema and repository.
2. Build a fresh database from the rewritten corpus output.
3. Index regulation records separately from provision text.
4. Store exact citation nodes separately from contextual display units.
5. Resolve every legal node, context node, source span, and lifecycle relation through typed repository calls.
6. Emit a reproducibility manifest with all input and output hashes.

Exit gate: an empty environment can create the complete database in one documented command, and all citations resolve from it.

### Phase 4: typed query and two-stage retrieval

1. Implement `QuerySpec` without importing the old lexicon.
2. Use regex only for explicit legal syntax such as instrument number, year, Pasal, Ayat, Huruf, Angka, issuer names, and dates.
3. Treat non-explicit issuer associations as soft document-ranking signals.
4. Implement document search over canonical regulation records.
5. Implement provision search only inside selected document IDs.
6. Enforce claim-only passage relevance.
7. Implement independent evidence gates and ambiguity behavior.
8. Add real miniature-database integration tests before full-corpus tuning.

Exit gate: paraphrases share typed intent without exact-prompt branches, and irrelevant clauses cannot pass because their document title matches.

### Phase 5: answer and API cutover

1. Implement mode-specific renderers.
2. Assemble readable context only from stored source nodes.
3. Calculate final status after rendering and revalidation.
4. Replace API schemas, dependencies, services, presenters, routes, and OpenAPI contract.
5. Remove the numeric confidence field.
6. Expose coverage and lifecycle uncertainty explicitly.
7. Leave the frontend broken until the later frontend migration.

Exit gate: every finding is readable without opening the source, and opening its citations proves every rendered legal claim.

### Phase 6: real evaluation

1. Create independently reviewed development, negative, lifecycle, and sealed datasets.
2. Implement database-backed citation verification.
3. Implement separate metrics and hard failure gates.
4. Run acceptance tests against the real full database.
5. Measure the two demonstrated failure families across multiple paraphrases.
6. Diagnose failures by layer and failure class; never patch the prompt string.
7. Publish only reports containing exact dataset and database hashes.

Exit gate: the system passes the agreed thresholds across families, not merely the original questions.

### Phase 7: performance and later intelligence

1. Profile stage latency before changing ranking.
2. Optimize SQLite queries, candidate limits, tokenization, and cached immutable metadata.
3. Establish the deterministic lexical baseline.
4. Only then evaluate semantic retrieval, reranking, and constrained LLM query interpretation or synthesis behind isolated experiments.
5. Promote an experiment only when held-out retrieval improves without citation, lifecycle, refusal, coverage, or latency regression.

Exit gate: measured improvement over the clean baseline, never replacement by reputation or intuition.

## Build policy

The hard migration intentionally rebuilds generated artifacts. The accepted build is full and clean:

1. load the OCR exclusion list;
2. remove old generated outputs;
3. parse eligible saved non-OCR raw pages with the new parser;
4. build the regulation catalog and lifecycle graph;
5. build contextual and atomic legal units;
6. create a new SQLite database from empty;
7. run structural and citation audits;
8. run real-index evaluation;
9. publish hashes and skipped-document coverage.

There is no incremental build, old-schema reader, or fallback index during this migration.

## Definition of done

- No deleted module, heuristic resource, golden runner, old test, old report, fallback, or compatibility wrapper remains.
- `rg` finds no exact-prompt branch for known questions.
- One clean command reproduces the eligible corpus and database from saved non-OCR inputs.
- OCR is never invoked and all OCR-needed documents are explicitly excluded.
- Regulation identities do not collide.
- Lifecycle claims are source-backed or explicitly unknown.
- Document and provision retrieval are separate.
- Provision relevance is claim-only.
- Every rendered context unit is database-resolvable.
- Every accepted citation resolves and matches its claim.
- The API exposes no uncalibrated confidence score.
- The new tests contain no mocked retrieval success.
- Acceptance runs against the real API and full current database.
- Paraphrase families, negatives, lifecycle cases, readability, refusals, and latency meet defined gates.
- The demonstrated consumer-protection and advertising questions pass as members of generic families without special code.
- README and API documentation describe only the new architecture.

## Rule for every future patch

A patch is rejected when it:

- recognizes a specific prompt or expected answer;
- adds an issuer or regulation special case without a domain-level source-backed rule;
- changes a test expectation to match broken output;
- mocks retrieval or citations in an acceptance test;
- uses title relevance as claim support;
- hides unknown lifecycle state;
- restores an old schema, response field, fallback, or compatibility path;
- improves one visible case while worsening family or holdout metrics.

The only acceptable fixes change a general layer, explain the failure class, and improve independently measured behavior.
