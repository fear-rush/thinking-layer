# Source-Understanding-First Rebuild Plan

Status: hard reset complete; source understanding is next. There is no accepted
corpus, parser, database, retrieval system, API, or accuracy claim.

Date of reset: 2026-07-16

Supported sources:

- `ease-bi`
- `peraturan-ojk`

Compatibility policy: none. Deleted modules, commands, generated schemas, file
formats, fixtures, and APIs will not receive compatibility wrappers.

OCR remains disabled, and OCR remediation is not part of this plan. If a file is
unreadable during source study, record `deferred_unreadable` and continue. Later
extraction and parsing must publish an OCR-needed report, but that report must not
delay document-role or layout research.

## 1. Why this reset exists

The previous migration moved too quickly from downloaded files to a large corpus.
It created a parser contract, legal AST, lifecycle graph, audits, and millions of
generated units before the two remaining sources had been described and measured
properly. Structural tests could pass while document roles were wrong. A BI
licensing guide could default to `primary_regulation`; passing serialization and
span checks did not make that classification legally correct.

This rebuild starts from a narrower question:

> What exactly did EASE-BI and Peraturan-OJK publish, how are their records and
> files organized, and which observable source evidence distinguishes normative
> regulations from abstracts, FAQs, explanations, attachments, forms, guidance,
> and unknown material?

No corpus architecture is accepted until that question has a reviewed answer.

## 2. Reset decisions already applied

The reset performs the following destructive changes:

1. Remove all prior output under `processed/`.
2. Remove the corpus builder, parser, normalizer, catalog, lifecycle, audit, and
   serialized legal-domain implementation under `thinking_layer/corpus/` and
   `thinking_layer/domain/`.
3. Remove the placeholder API, CLI, answer, retrieval, indexing, lexicon, and
   evaluation packages. They represented future architecture rather than verified
   source understanding.
4. Remove all backend tests and synthetic LiteParse fixtures. None are grandfathered
   into the new design.
5. Remove runtime dependencies for FastAPI, Uvicorn, Pydantic, Markdown-It, and
   LiteParse. Dependencies will be added only when a measured source task requires
   them.
6. Keep the frontend source unchanged but frozen. It has no backend contract during
   source research and is outside this plan until a later explicit cutover.

## 3. Measured starting facts

These are filesystem observations from the reset date, not accuracy claims and not
future contracts.

### 3.1 EASE-BI

- 81 per-record JSON metadata files and one aggregate NDJSON file.
- 80 downloaded files totaling approximately 63.5 MB.
- 68 PDFs, 9 DOCX files, and 3 XLSX files.
- Metadata tabs contain:
  - 51 PDF `Ketentuan` records;
  - 1 PDF `Ketentuan Terkait` record;
  - 3 PDF `FAQ` records;
  - 14 PDF, 9 DOCX, and 3 XLSX `Dokumen Persyaratan & Pedoman`
    records.
- The 68 PDFs contain 59 unique SHA-256 values.
- Four within-source duplicate-hash groups contain nine copies beyond the first.
- EASE metadata is useful for the tab, group path, label, source URL, media type,
  and saved path. It is generally not a complete legal-instrument catalog.

### 3.2 Peraturan-OJK

- 1,551 per-record JSON metadata files and one aggregate NDJSON file.
- 2,398 downloaded files totaling approximately 1.04 GB.
- 2,395 PDFs and 3 incomplete `.part` files.
- File-role labels in harvested metadata contain:
  - 1,952 `peraturan` files;
  - 237 `faq` files;
  - 206 `abstrak` files.
- Every per-record JSON currently supplies a title, regulation number, regulation
  type, year, effective date, and sector. Those are harvested assertions and still
  require document-level validation.
- Metadata regulation types include POJK, SEOJK, PPBI, SEBI, Bapepam
  classifications and regulations, statutes, government regulations, ministerial
  instruments, and ADK regulations. Therefore `peraturan-ojk` is an OJK publication
  portal, not a collection containing only OJK-issued instruments.
- Metadata years range from 1953 through 2027. Future, malformed, or surprising
  dates must be reported; they must not be silently normalized.
- The 2,395 PDFs contain 2,323 unique SHA-256 values.
- Sixty-nine within-source duplicate-hash groups contain 72 copies beyond the
  first.

### 3.3 Consequences of these facts

- A metadata record is not the same thing as a downloaded file.
- An OJK detail page is often a publication bundle containing multiple files with
  different semantic roles.
- A downloaded file is not automatically a regulation.
- A duplicate file occurrence is not a new legal instrument.
- A new byte sequence is not automatically a new legal instrument; two portal
  copies may render the same regulation differently.
- Source portal, issuer, instrument type, document role, media format, and layout
  family are separate dimensions.
- EASE-BI and Peraturan-OJK need separate source adapters and separate quality
  reporting.

### 3.4 Research methodology

The working method for Phases 1 and 2 is **grounded comparative documentary
analysis**. This is a project-specific name for a practical combination of
established methods; it is not presented as a new academic standard.

The methods have distinct jobs:

- **Diplomatic analysis** examines documentary genesis and authority: who created
  the document, in what official capacity, for what purpose, through which
  publication process, and which internal or external signs support authenticity
  and legal function.
- **Genre analysis** identifies recurring functional moves and zones such as title,
  authority, consideration, legal basis, dictum, definitions, operative provisions,
  closing, signature, explanation, and attachment. A move is a semantic function,
  not merely a font size or heading level.
- **Grounded qualitative coding and constant comparison** allow document roles,
  bundle patterns, layout families, and exceptions to emerge from actual files. The
  initial taxonomy is a hypothesis to challenge, not a label set to force.
- **Corpus profiling and content analysis** measure how prevalent the reviewed
  patterns are only after the codebook is stable enough to apply consistently.

The research sequence is:

1. Perform a direct walkthrough and write open observations without forcing the
   initial taxonomy.
2. Assign provisional codes to observed roles, structures, relationships, and
   anomalies.
3. Compare each new case with earlier cases and revise, merge, split, or retire
   codes when the evidence requires it.
4. Turn stable codes into a versioned codebook containing definitions, inclusion
   rules, exclusion rules, positive examples, negative boundary examples,
   counterexamples, and unresolved questions.
5. Use maximum-variation purposive sampling to discover the range of OJK cases.
6. After completing the planned variation-coverage grid, continue review in
   documented, pre-sized batches until two consecutive batches add no new document
   role, bundle shape, or layout family. This is the operational saturation rule,
   not proof that no unseen exception exists.
7. Freeze the discovery codebook, then draw a separate deterministic stratified
   random audit sample to estimate classification performance and expose missed
   patterns. Do not tune rules on this audit sample.
8. Profile the complete source inventory only after the human distinctions are
   explicit and reproducible.

EASE-BI is small enough for a complete file census. Peraturan-OJK requires both a
discovery set and a later audit set; a single “representative sample” is not enough.

### 3.5 Unit of review and annotation boundary

Human review must state which unit is being labeled:

- portal record;
- publication bundle;
- downloaded file occurrence;
- byte-identical content blob;
- semantic document;
- legal instrument;
- internal document zone or functional move.

Phases 1 and 2 label bundles, documents, roles, relationships, layout families, and
coarse functional moves. They do **not** annotate every `BAB`, `Bagian`, `Pasal`,
paragraph, or named entity. Fine-grained span or page-region annotation is deferred
until extraction preserves stable text and page coordinates.

Every formal review decision must include the source record, downloaded path,
content hash, pages or office-container parts inspected, portal assertion, observed
role, issuer and instrument-kind candidates, bundle relationship, layout-family
candidate, observed functional moves, supporting evidence, uncertainty, reviewer,
review date, and decision status.

## 4. Non-negotiable principles

### 4.1 Metadata is a sidecar, not legal text

Raw harvested metadata is retained unchanged and hashed. Parsed metadata may help
identify, group, sample, and validate files. Metadata text must never be appended,
prepended, blended, or indexed as though it came from a downloaded document.

Each usable metadata value receives one evidence status:

- `declared`: stated by the source portal;
- `observed`: derived directly from file bytes or container structure;
- `verified`: the portal assertion and downloaded document agree;
- `conflict`: both exist and disagree;
- `missing`: no usable value exists;
- `not_applicable`: the field does not apply to that document role.

Conflicts remain visible. The implementation must not choose a convenient value and
erase the disagreement.

### 4.2 Unknown is a valid result

No classifier may default an unrecognized file to `primary_instrument`. Unknown,
ambiguous, unsupported, and conflicting records remain outside normative parsing
until reviewed.

### 4.3 Preserve occurrences before deduplicating content

The inventory must retain every portal record and every downloaded path. Exact
content hashes may point several occurrences to one content blob, but provenance is
never deleted. Instrument-level reconciliation happens only after role and identity
evidence have been reviewed.

### 4.4 Measure one source family at a time

Results must be reported separately for:

- EASE-BI versus Peraturan-OJK;
- each media format;
- each document role;
- each layout family;
- text-native versus unsupported/image-only files;
- modern versus legacy publications where source evidence supports that grouping.

An aggregate success rate cannot hide a bad family.

### 4.5 No mock-based correctness

Mocks, monkeypatches, fabricated portal records, injected parser outputs, and copied
runtime output are prohibited as evidence of source understanding, extraction
quality, role classification, legal hierarchy, citation correctness, retrieval, or
API behavior.

Tests may cover a pure utility only after the utility has an independently useful
contract. Any legal or source-behavior expectation must refer to a real reviewed
EASE-BI or Peraturan-OJK record and its source hash.

### 4.6 No build pressure

There is no target corpus size and no incentive to maximize accepted documents.
Precision and honest exclusion are more important than coverage during this plan.

### 4.7 Minimal research tooling

The source trees, review files, and Git history are the system of record during
discovery. Use the smallest tools that expose evidence without introducing a new
platform:

- ordinary PDF viewing and page rendering for visual inspection;
- LibreOffice for DOCX and XLSX inspection;
- Markdown for narrative findings and a versioned codebook;
- JSONL for one-review-decision-per-record evidence;
- `rg`, `jq`, `file`, `shasum`, `pdfinfo`, `pdffonts`, `pdftotext`, and
  `pdftoppm` for read-only measurement and navigation.

Later extraction experiments may evaluate family-appropriate libraries such as
PyMuPDF for PDFs, `python-docx` for DOCX, and `openpyxl` for XLSX. No library is
selected merely because it is popular; it must solve a measured need for a reviewed
family.

Label Studio may be reconsidered only if stable page-region or span labels must be
produced at a scale that JSONL review can no longer support. Doccano, corpus-NLP
workbenches, Obsidian, and Zotero are not source-of-truth systems for this phase.
IFLA LRM, PROV-O, Dublin Core, and Akoma Ntoso may later be used as comparison
references for identity, provenance, descriptive metadata, or legal-document
modeling, but their schemas will not be adopted before local evidence establishes a
need. Ontologies, RDF, knowledge graphs, ML, LLM classification, and embedding
pipelines are explicitly premature.

## 5. Identity and authority model to establish

The source-understanding layer must distinguish these identities:

1. `source_record_id`: one harvested portal record.
2. `publication_bundle_id`: one portal detail page or EASE list entry and all files
   attached to it.
3. `source_file_occurrence_id`: one path referenced by one source record.
4. `content_blob_id`: SHA-256 of the downloaded bytes.
5. `document_identity`: one semantic document after reviewed role classification.
6. `instrument_identity`: issuer, instrument kind, normalized number, and year,
   created only from verified evidence.

Authority rules:

- Downloaded bytes are authoritative for document wording and visual structure.
- The portal record is authoritative only for what the portal declared.
- A portal URL establishes provenance, not legal validity.
- Filename and directory names are hints, not final identity evidence.
- A document title page or equivalent explicit source statement may verify portal
  metadata.
- Lifecycle status is not inferred from a portal category, title similarity, year,
  or newer-looking file. It requires explicit reviewed evidence.

## 6. Document taxonomy to review

The initial semantic role vocabulary is deliberately small:

- `primary_instrument`: the normative instrument itself;
- `abstract`: a portal-authored abstract or summary;
- `faq`: questions and answers about an instrument or topic;
- `explanation`: an official explanatory section or separate explanation document;
- `attachment`: an attachment governed by an instrument;
- `form_template`: a form, spreadsheet, letter template, or submission template;
- `guideline`: procedural or implementation guidance that is not itself classified
  as the primary instrument;
- `supporting_material`: other related official material;
- `unknown`: insufficient or conflicting evidence;
- `deferred_unreadable`: cannot currently be read with the ordinary tools in use;
  this result is recorded without starting a remediation workstream.

Instrument kind is separate from document role. Examples include POJK, SEOJK, PADK,
PBI, PADG, SEBI, statute, government regulation, ministerial regulation, decision,
and legacy Bapepam instruments.

Layout family is also separate. It will be discovered from reviewed files rather
than hard-coded from agency names.

## 7. Target source-understanding flow

```text
actual EASE publication bundles --------+
actual OJK publication bundles ----------+--> direct human walkthrough
                                                       |
                                                       v
                                      open coding of observed evidence
                                                       |
                                                       v
                                      constant comparison in review batches
                                                       |
                                                       v
                                      versioned codebook and source map
                                                       |
                                                       v
                                      reviewed roles, bundles, and layouts
                                                       |
                                                       v
data/*.json + downloads/**/* -----------> inventory automation
                                                       |
                                                       v
                                      measured metadata and duplicate profile
                                                       |
                                                       v
                                      rules derived from reviewed evidence
                                                       |
                                                       v
                                      independent stratified random audit
                                                       |
                                                       v
                                      extraction experiment by one family
```

The flow stops at any failed gate. It does not continue automatically to a corpus.

## 8. Implementation phases

### Phase 0: hard reset

Status: complete.

Work:

- delete `processed/` and stale reports;
- delete premature backend contracts and synthetic tests;
- remove unused runtime dependencies;
- document the two-source boundary;
- add a baseline check that rejects old processed output.

Exit gate:

- only `ease-bi` and `peraturan-ojk` exist under both `data/` and `downloads/`;
- `processed/` does not exist;
- no backend parser, corpus builder, database, retrieval, answer, or API is runnable;
- the dependency lock matches the reset project configuration.

### Phase 1: direct source walkthrough

Purpose: understand the documents before designing automation.

Files to add:

- `docs/sources/ease-bi-walkthrough.md`
- `docs/sources/peraturan-ojk-walkthrough.md`
- `docs/sources/open-questions.md`
- `resources/source_review/walkthrough.jsonl`

Do not add application code or tests in this phase.

Work:

1. Open the EASE-BI metadata records and their downloaded files together. Follow the
   tab and group hierarchy as a user of the portal would see it.
2. Open representative Peraturan-OJK detail records as publication bundles. Compare
   the page metadata with each attached `peraturan`, `abstrak`, and `faq` file.
3. Start the OJK walkthrough with maximum-variation cases selected across portal
   file kind, declared regulation type, year band, sector, bundle size, duplicate
   status, and suspicious or confusing filenames. This is a discovery set, not a
   random accuracy sample.
4. Apply diplomatic questions to each case: creator, issuer, authority, intended
   function, publication context, signs of validation, relation to other bundle
   files, and whether the file is itself normative.
5. Record genre moves and internal zones without assuming their order or requiring
   predefined names. Distinguish semantic function from typography.
6. Open-code recurring document roles, bundle shapes, title-page patterns,
   explanation/attachment boundaries, forms, tables, and legacy differences. Keep
   the initial taxonomy challengeable.
7. Record confusing cases, contradictions, negative boundary cases, and
   counterexamples without solving them in code.
8. If a file is unreadable, mark it `deferred_unreadable` and continue immediately.
   Do not investigate or repair it during this phase.
9. Capture paths, hashes, inspected pages, and evidence for every documented example
   so observations remain tied to the actual bytes.

Exit gate:

- the two walkthrough documents describe how each source publishes information;
- provisional codes are grounded in real examples and explicitly marked as
  provisional;
- important counterexamples and unknowns are recorded;
- no parser, classifier, schema, or generalized source model has been written.

### Phase 2: reviewed document and bundle map

Purpose: turn the walkthrough into human-reviewed evidence without automating the
conclusions yet.

Files to add:

- `resources/source_review/review_manifest.json`
- `resources/source_review/codebook.json`
- `resources/source_review/document_roles.jsonl`
- `resources/source_review/layout_families.jsonl`
- `resources/source_review/publication_bundles.jsonl`
- `resources/source_review/metadata_conflicts.jsonl`
- `resources/source_review/audit_manifest.json`
- `resources/source_review/audit_labels.jsonl`
- `docs/sources/review-guide.md`
- `docs/sources/document-role-taxonomy.md`

Do not add classifier tests in this phase.

Work:

1. Review every EASE-BI file because the collection is currently small.
2. Review Peraturan-OJK in maximum-variation discovery batches covering all portal
   file kinds, major regulation types, year bands, sectors, single-file bundles,
   multi-file bundles, duplicate files, and confusing filenames.
3. Include every rare category encountered during the walkthrough.
4. Use constant comparison after every batch. Record whether a code was added,
   split, merged, renamed, retired, or left unresolved and why.
5. Build a versioned codebook. Every stable code must have a definition, unit of
   analysis, inclusion rule, exclusion rule, positive example, negative boundary
   example, and known counterexample or an explicit statement that none is yet known.
6. Record the reviewer decision, evidence page or office-container part, evidence
   text or visual description,
   document role, instrument-kind candidate, layout-family candidate, uncertainty,
   and source hashes.
7. Describe relationships inside a publication bundle without assuming that all
   files are part of the normative instrument.
8. Label coarse functional moves only when they help distinguish roles or layouts.
   Do not perform exhaustive `BAB`/`Pasal`/entity span annotation.
9. Allow `unknown`, competing interpretations, and reviewer disagreement.
10. Continue discovery until two consecutive documented OJK batches add no new role,
    bundle shape, or layout family, after the planned variation-coverage grid is
    complete. Define the batch size in the review guide before this check begins and
    do not change it retroactively. Record the batch composition and result; do not
    claim universal completeness from saturation.
11. After freezing the discovery codebook, create a deterministic stratified random
    OJK audit manifest from records not used to develop the codebook. Stratify using
    known source variables without pre-labeling the answer. Pre-register the sample
    size rationale, seed, selection algorithm, strata, and inclusion probabilities.
12. Review and lock the audit labels using only the frozen codebook and source
    evidence, before exposing classifier predictions to the reviewer.
13. Never generate a human review label from classifier output, and never revise the
    frozen codebook or rules using audit answers without declaring a new version and
    drawing a new untouched audit set.

Exit gate:

- all EASE-BI files have reviewed roles or explicit unknowns;
- OJK discovery batches meet the documented operational saturation rule;
- a frozen codebook contains positive, negative, and counterexample evidence;
- a separate deterministic stratified random audit manifest and locked human labels
  exist and have not been used to develop rules;
- every label resolves to unchanged source bytes;
- disagreements remain visible;
- the taxonomy explains actual documents rather than hypothetical formats.

### Phase 3: lossless two-source inventory

Purpose: automate only the source relationships already understood in Phases 1 and
2. This is the first phase that adds backend code.

Files to add:

- `thinking_layer/sources/__init__.py`
- `thinking_layer/sources/models.py`
- `thinking_layer/sources/hashing.py`
- `thinking_layer/sources/inventory.py`
- `thinking_layer/sources/serialization.py`
- `thinking_layer/sources/cli.py`
- `thinking_layer/sources/adapters/__init__.py`
- `thinking_layer/sources/adapters/ease_bi.py`
- `thinking_layer/sources/adapters/peraturan_ojk.py`
- `tests/source_acceptance/test_inventory_reconciliation.py`

Work:

1. Read only per-record JSON files; compare aggregate NDJSON separately.
2. Preserve raw record paths and SHA-256 values.
3. Resolve every declared saved path and discover every downloaded occurrence.
4. Record extension, basic file signature, size, SHA-256, source URL, portal record,
   publication bundle, and raw role assertion.
5. Report missing files, unreferenced files, duplicates, reused paths, incomplete
   `.part` files, malformed records, and conflicts.
6. Preserve every occurrence even when content hashes match.
7. Do not extract document text or infer legal meaning.
8. Write disposable output under `artifacts/source-understanding/inventory/`.

Required artifacts:

- `source_records.ndjson`
- `source_file_occurrences.ndjson`
- `content_blobs.ndjson`
- `inventory_manifest.json`
- `inventory_findings.ndjson`

Exit gate:

- all metadata records and downloaded files are accounted for;
- counts reconcile separately for each source;
- outputs preserve source hashes and reviewed bundle relationships;
- rerunning without input changes produces identical semantic output.

### Phase 4: metadata characterization

Purpose: measure portal assertions using the document understanding already captured.

Files to add:

- `thinking_layer/sources/profile.py`
- `thinking_layer/sources/metadata_fields.py`
- `docs/sources/ease-bi.md`
- `docs/sources/peraturan-ojk.md`
- `docs/sources/metadata-authority.md`
- `tests/source_acceptance/test_metadata_profiles.py`

Work:

1. Measure field presence, null rate, type consistency, cardinality, and unexpected
   values separately by source.
2. Compare EASE tabs, groups, titles, labels, content types, URLs, and paths with the
   reviewed files.
3. Compare OJK regulation types, file kinds, numbers, dates, sectors, and bundle
   membership with reviewed evidence.
4. Preserve contradictions rather than normalizing them away.
5. Detect repeated numbers and hashes without assuming semantic duplication.
6. Document each field as a retained raw assertion, verified candidate, conflict,
   ignored value, or unresolved value.
7. Do not create final instrument identities yet.

Exit gate:

- both source profiles are reviewed against real documents;
- normalized fields have explicit provenance;
- metadata wording is never treated as document wording;
- unknown and conflicting values remain visible.

### Phase 5: role and bundle classification

Purpose: implement only the distinctions demonstrated by reviewed source evidence.

Files to add:

- `thinking_layer/sources/roles.py`
- `thinking_layer/sources/classification.py`
- `thinking_layer/sources/bundles.py`
- `tests/source_acceptance/test_document_roles.py`
- `tests/source_acceptance/test_publication_bundles.py`

Work:

1. Apply source-specific portal assertions first as declared evidence.
2. Validate those assertions using filename, media type, first-page evidence, and
   bundle relationships only where the review set demonstrates a general rule.
3. Keep role, instrument kind, and layout family in separate fields.
4. Return `unknown` for missing or conflicting evidence.
5. Never use numeric marker shape alone to identify a regulation.
6. Never treat abstract, FAQ, form, or guideline content as normative because it
   mentions Pasal or an instrument number.
7. Report a confusion matrix and false-primary count independently for each source
   and layout family.
8. Report discovery/development results separately from untouched audit results. Do
   not tune a rule, threshold, exception, or taxonomy definition on audit answers
   and continue calling that sample independent.
9. Treat EASE-BI classifier results as agreement with the reviewed census, not an
   independent estimate of unseen-file accuracy. For the OJK audit, report both raw
   stratum results and population-weighted estimates when sampling probabilities
   differ.

Exit gate:

- zero reviewed abstracts, FAQs, forms, guidelines, or unknown files are classified
  as primary instruments;
- every classification includes inspectable evidence and a rule identifier;
- family-specific results are published without a hidden aggregate;
- failed families remain excluded rather than patched with filename exceptions.

### Phase 6: layout-family discovery

Purpose: understand structure before writing a legal parser.

Files to add:

- `thinking_layer/sources/layouts.py`
- `thinking_layer/sources/layout_evidence.py`
- `docs/sources/layouts/ease-bi.md`
- `docs/sources/layouts/peraturan-ojk-modern.md`
- `docs/sources/layouts/peraturan-ojk-legacy.md`
- `tests/source_acceptance/test_layout_family_assignments.py`

Work:

1. Inspect title pages, headers, footers, page numbering, normative openings,
   chapters, articles, explanations, signatures, attachments, lists, and tables.
2. Separate portal/document role from visual layout family.
3. Identify documents containing multiple internal zones.
4. Record unreadable layouts as deferred and continue with readable examples.
5. Define family membership from observable structure, not agency reputation.
6. Start with the smallest coherent family, expected to be modern text-native OJK
   primary instruments, but confirm that expectation from review data.

Exit gate:

- every reviewed primary document has a reviewed layout family or `unknown`;
- each accepted family has documented positive and negative boundary examples;
- no legal hierarchy parser exists yet.

### Phase 7: extraction experiments

Purpose: select extraction behavior using measured real documents rather than parser
convenience.

Files to add only after the experiment design is reviewed:

- `thinking_layer/extraction/`
- `resources/extraction_review/`
- `tests/extraction_acceptance/`
- `docs/extraction/experiment.md`
- `reports/ocr_needed.json`
- `reports/ocr_needed.md`

Work:

1. Define review measurements before selecting or pinning an extraction library.
2. Run extraction only on the readable reviewed sample. Deferred unreadable files do
   not block the experiment.
3. Measure title fidelity, paragraph order, list nesting, table structure, page
   anchors, repeated furniture, character corruption, missing text, and attachment
   boundaries.
4. Report results by source, media type, role, and layout family.
5. Preserve extractor raw output and configuration as disposable experiment
   artifacts, not canonical corpus input.
6. Add an extractor dependency only after it wins the documented experiment.
7. Do not repair missing legal wording heuristically.
8. Whenever extraction indicates that a file or particular pages need OCR, rebuild
   `reports/ocr_needed.json` and its readable Markdown companion. Each finding must
   include the source, source-record path, downloaded path, source URL when present,
   byte hash, document role when known, reason, affected page numbers when known,
   detecting stage, and tool/configuration evidence.
9. The OCR-needed report is informational. Do not run OCR, and do not stop work on
   other readable documents because the report is non-empty.

Exit gate:

- the selected extractor has reviewed family-specific evidence;
- every accepted extracted block maps to source bytes and a source page or office
  container location;
- unsupported families remain excluded;
- the OCR-needed JSON and Markdown reports exist, even when their finding lists are
  empty, and account for every unreadable file or page encountered by the experiment;
- no full-source extraction has run.

### Phase 8: minimal legal parsing by family

Purpose: parse one proven family without pretending the same grammar fits everything.

Files are intentionally not named until Phase 6 establishes the family boundaries.
Creating generic `corpus`, `legal_ast`, or `parser` packages before that decision is
prohibited.

Work:

1. Begin with one reviewed, text-native, primary-instrument layout family.
2. Define its expected legal anchors and zone transitions from reviewed documents.
3. Parse only explicit source structure.
4. Preserve unparsed blocks and coverage gaps.
5. Test against independently reviewed real documents, including negative role and
   boundary examples.
6. Add another layout family only through a separate measured acceptance gate.
7. Address BI PDF regulations, BI guidance, BI FAQ, DOCX, and XLSX separately; do not
   force them through the OJK parser.
8. If parsing discovers an unreadable file or page not already reported, add it to
   the same OCR-needed reports with parser-stage evidence. Never silently drop the
   affected pages or describe a partially read document as complete.

Exit gate:

- the selected family has measured anchor precision and recall;
- false normative anchors are zero on reviewed negative roles;
- source order, wording, and locations are preserved;
- excluded content is counted and explained;
- every parser-discovered OCR need resolves to an entry in both OCR-needed reports.

### Phase 9: corpus decision checkpoint

Only after Phases 1 through 8 pass may the project decide whether a corpus model,
database, retrieval pipeline, API, or frontend migration should exist.

At this checkpoint, write a new plan based on measured source facts. Do not carry
forward schemas or module names from the deleted implementation merely because they
previously existed.

## 9. Accuracy definitions

The word `accuracy` must name a measured property:

- inventory accuracy: metadata/file reconciliation against actual paths;
- file accuracy: detected format and basic properties against inspected files;
- role accuracy: reviewed document-role classification;
- identity accuracy: issuer/type/number/year agreement with explicit document
  evidence;
- extraction fidelity: wording, order, structure, and location preservation;
- anchor accuracy: legal hierarchy precision and recall;
- coverage: included, excluded, unsupported, unknown, and duplicate occurrences.

There is no valid single overall accuracy number.

## 10. Testing rules

1. Do not restore the deleted synthetic LiteParse fixtures.
2. Do not use mocks to claim successful parsing, classification, citation,
   retrieval, or API behavior.
3. Do not write expected output by copying current runtime output.
4. Every source-behavior fixture must identify its original source record, path,
   byte hash, review decision, and minimization method if minimized.
5. Prefer acceptance checks that read the actual local source trees.
6. A missing local source tree is a failed source acceptance run, not a passing
   skipped test in release validation.
7. Pure utility tests may cover hashing, deterministic serialization, and strict
   normalization, but they do not count as source accuracy.
8. Negative examples are mandatory for every classifier and parser family.
9. Tests must assert exclusions and unknowns, not only successes.
10. Any change to reviewed labels requires an explicit human review diff.

## 11. Files removed by the reset

Removed implementation areas:

- `thinking_layer/corpus/`
- `thinking_layer/domain/`
- `thinking_layer/answer/`
- `thinking_layer/retrieval/`
- `thinking_layer/indexing/`
- `thinking_layer/evaluation/`
- `thinking_layer/lexicon/`
- `thinking_layer/api/`
- `thinking_layer/common/`
- `thinking_layer/cli.py`

Removed tests and fixtures:

- `tests/fixtures/fresh_liteparse/`
- `tests/unit/corpus/`
- `tests/unit/domain/`
- `tests/integration/test_clean_corpus_build.py`
- the remaining backend test package markers

Removed generated or stale state:

- `processed/`

## 12. Files retained intentionally

- `data/ease-bi/` and `downloads/ease-bi/` as local source inputs;
- `data/peraturan-ojk/` and `downloads/peraturan-ojk/` as local source inputs;
- `thinking_layer/config/paths.py` with only source and artifact locations;
- the root Python package marker;
- project tooling configuration;
- the frontend source, frozen and out of scope;
- this plan and the reset README.

## 13. Files that must not be added yet

Until the corresponding checkpoint passes, do not add:

- a corpus builder;
- a legal JSON AST;
- a SQLite schema;
- lexical or semantic indexes;
- query planning or retrieval;
- answer rendering;
- API query routes;
- frontend integration changes;
- lifecycle inference;
- LLM, embedding, reranking, NER, or graph dependencies;
- an ontology, RDF model, or knowledge graph;
- an Akoma Ntoso, IFLA LRM, Dublin Core, or PROV-O implementation;
- Label Studio, doccano, or another annotation server before stable annotation units
  and scale justify one;
- a second note database used as an unofficial source of truth;
- compatibility modules under deleted import paths.

## 14. Definition of source-understanding done

This plan is complete only when:

- the two source trees reconcile completely;
- reviewed document roles and layout families are understood before automation;
- exact duplicates preserve provenance without multiplying content;
- EASE-BI is fully role-reviewed;
- Peraturan-OJK discovery has reached the documented operational saturation rule;
- the versioned codebook defines inclusion, exclusion, positive, negative, and
  counterexample evidence for stable codes;
- Peraturan-OJK has a deterministic stratified random audit set kept independent
  from codebook and rule development;
- document roles, instrument kinds, and layout families are separated;
- no unknown file becomes a primary regulation by default;
- metadata conflicts are explicit;
- extraction quality is measured on real readable reviewed files;
- later extraction and parsing produce complete machine-readable and human-readable
  OCR-needed reports without making OCR a blocker;
- one layout family is parsed accurately with real negative cases;
- every claim reports exclusions and family-specific coverage;
- no mock or synthetic fixture is used as evidence of legal correctness;
- a new corpus/database plan is written from these results rather than inherited
  from the deleted architecture.
