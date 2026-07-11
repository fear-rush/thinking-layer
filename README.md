# thinking-layer

Local-first baseline pipeline for answering Indonesian financial regulation questions with citation-aware retrieval.

This project is intentionally not LLM-first yet. The current baseline focuses on the hard production parts before answer generation: corpus audit, file manifest normalization, document extraction, citation-aware blocks, deterministic query planning, lexical retrieval, evidence packing, and deterministic answer composition.

## What This Project Does

The current baseline is designed for questions such as:

- `apa saja peraturan periklanan yang harus dipatuhi oleh bank?`
- `berikan aku aturan terkait penyedia jasa pembayaran dari BI dan OJK`
- `komparasi peraturan OJK dan BI terkait penyedia jasa pembayaran`
- `sanksi apa kalau bank terlambat menyampaikan laporan ke OJK?`

The system must cite best-effort `document`, `page`, `Pasal`, and `Ayat` when those fields are available. If evidence is weak or missing, the answer layer must say the information was not found instead of guessing.

## Corpus Baseline

Canonical searchable regulations currently come from:

- `data/peraturan-ojk`: primary OJK regulation metadata and files.
- `data/ease-bi`: primary BI regulation metadata and files.
- `data/sikepo-ojk`: loaded for audit, file manifest, duplicate analysis, and future enrichment, but not merged into canonical OJK search documents yet.

This is deliberate. `peraturan-ojk` has broader regulation coverage, while `sikepo-ojk` has richer metadata. The baseline keeps primary text coverage stable first, then measures where Sikepo metadata can enrich later.

OCR remains opt-in per file rather than enabled for the normal full-corpus pass. Scanned or text-poor PDFs are listed in `reports/ocr_needed.*` and should be re-extracted with `--replace-existing --enable-ocr` after a one-page quality check. Office documents require LibreOffice; otherwise they are reported as `libreoffice_not_found`.

Current local extraction status after selective OCR and Office replacement:

- Extracted rows: `2,475`
- Extracted blocks: `537,355`
- Remaining skipped / OCR-needed / failed rows: `0`

The BI Office operational documents, including QRIS/SNAP matrices, are now extracted and included in the source corpus and search index.

## Project Structure

Pipeline code lives under `thinking_layer/`:

- `config/paths.py`: repository paths and shared file constants.
- `common/io.py`: JSON and NDJSON helpers.
- `common/text.py`: text normalization and slug helpers.
- `corpus/metadata.py`: source records, canonical IDs, file manifest helpers, and file-role classification.
- `corpus/audit.py`: corpus audit checks and audit report rendering.
- `corpus/extraction.py`: LiteParse page normalization, OCR-status classification, and page-aware block extraction helpers.
- `corpus/extraction_pipeline.py`: extraction CLI orchestration and extraction/OCR reports.
- `corpus/citations.py`: citation quality, section typing, source priority, and source-corpus block normalization.
- `corpus/build.py`: canonical metadata/file-manifest build and audit CLI commands.
- `corpus/source_corpus.py`: citation-ready source corpus build and Sikepo metadata coverage report.
- `indexing/lexical.py`: stopwords, tokenization, in-memory BM25 index, lexical scoring, result formatting.
- `indexing/semantic.py`: isolated SentenceTransformers-compatible dense index and search path.
- `indexing/sqlite.py`: persisted SQLite index build/read/search.
- `indexing/title.py`: document-title representatives and title retrieval.
- `retrieval/query_tools.py`: query lexicon loading, pattern matching, and query overlap helpers.
- `retrieval/planning.py`: natural-language query planning.
- `retrieval/search.py`: planned search orchestration, result scoring, deduplication, and search CLI commands.
- `retrieval/__init__.py`: package marker for retrieval modules.
- `evaluation/retrieval.py`: retrieval smoke and natural-language evaluation.
- `retrieval/evidence.py`: citation-first evidence packs and evidence CLI command.
- `answer/composer.py`: deterministic answer composer and answer CLI command.
- `answer/quality.py`: deterministic answer-quality checks.
- `evaluation/evidence.py`: evidence evaluation.
- `evaluation/answer.py`: answer evaluation.
- `evaluation/holdout.py`: external holdout workflow.
- `evaluation/natural.py`: broad natural-language retrieval evaluation.
- `evaluation/semantic.py`: bounded BM25, dense-model, and RRF retrieval benchmark.
- `lexicon/candidates.py`: deterministic lexicon candidate extraction and generated draft lexicon.
- `lexicon/merge.py`: reviewed/generated lexicon merge.
- `cli.py`: command-line parser only.

The old `scripts/regulatory_pipeline.py` entrypoint has been removed. Use:

```bash
uv run python -m thinking_layer.cli --help
```

## Quick Start

Run the full local baseline in this order:

```bash
uv run python -m thinking_layer.cli all
uv run python -m thinking_layer.cli extract --progress-every 25 --verbose
uv run python -m thinking_layer.cli report
uv run python -m thinking_layer.cli build-source-corpus --include-secondary
uv run python -m thinking_layer.cli build-index

# Optional semantic-retrieval spike; this is separate from the BM25 baseline.
uv run python -m thinking_layer.cli build-semantic-index --model intfloat/multilingual-e5-small --batch-size 32
```

Use `--resume` only when continuing an interrupted full extraction run. For targeted OCR or Office retries, use `--file-id ... --replace-existing` so the existing corpus rows are preserved.

Then test retrieval and answers:

```bash
uv run python -m thinking_layer.cli search "penyedia jasa pembayaran" --include-secondary --limit 10
uv run python -m thinking_layer.cli semantic-search "peraturan BI tentang penyedia jasa pembayaran" --issuer BI --include-secondary --limit 10
uv run python -m thinking_layer.cli evidence "peraturan BI tentang penyedia jasa pembayaran apa saja?" --max-searches 6 --limit 8 --per-document-limit 2 --write-report
uv run python -m thinking_layer.cli answer "peraturan BI tentang penyedia jasa pembayaran apa saja?" --max-searches 6 --limit 8 --per-document-limit 2 --write-report
```

## Try System Output

Use these commands to inspect how the system plans, retrieves evidence, and composes answers.

### 1. Inspect Query Planning

```bash
uv run python -m thinking_layer.cli plan-query "apa saja peraturan periklanan yang harus dipatuhi oleh bank?" --max-searches 6
```

```bash
uv run python -m thinking_layer.cli plan-query "komparasi peraturan OJK dan BI terkait penyedia jasa pembayaran" --max-searches 8
```

### 2. Inspect Raw Retrieval Results

```bash
uv run python -m thinking_layer.cli search "penyedia jasa pembayaran" --include-secondary --limit 10
```

```bash
uv run python -m thinking_layer.cli planned-search "apa kewajiban bank terkait pelaporan SLIK?" --max-searches 6 --limit 8
```

```bash
uv run python -m thinking_layer.cli planned-search "aturan apa yang mengatur iklan produk bank dan promosi ke nasabah?" --max-searches 6 --limit 8
```

### 3. Inspect Citation Evidence Pack

```bash
uv run python -m thinking_layer.cli evidence "peraturan BI tentang penyedia jasa pembayaran apa saja?" --max-searches 6 --limit 8 --per-document-limit 2 --write-report
```

```bash
uv run python -m thinking_layer.cli evidence "apa saja peraturan periklanan yang harus dipatuhi oleh bank?" --max-searches 6 --limit 8 --per-document-limit 2 --write-report
```

```bash
uv run python -m thinking_layer.cli evidence "komparasi peraturan OJK dan BI terkait penyedia jasa pembayaran" --max-searches 8 --limit 10 --per-document-limit 2 --write-report
```

### 4. Inspect Final Deterministic Answer

```bash
uv run python -m thinking_layer.cli answer "peraturan BI tentang penyedia jasa pembayaran apa saja?" --max-searches 6 --limit 8 --per-document-limit 2 --write-report
```

```bash
uv run python -m thinking_layer.cli answer "apa saja peraturan periklanan yang harus dipatuhi oleh bank?" --max-searches 6 --limit 8 --per-document-limit 2 --write-report
```

```bash
uv run python -m thinking_layer.cli answer "komparasi peraturan OJK dan BI terkait penyedia jasa pembayaran" --max-searches 8 --limit 10 --per-document-limit 2 --write-report
```

### 5. Inspect Not-Found Behavior

```bash
uv run python -m thinking_layer.cli evidence "aturan yang mengatur planet mars untuk bank" --max-searches 6 --limit 8 --per-document-limit 2 --write-report
```

```bash
uv run python -m thinking_layer.cli answer "aturan yang mengatur planet mars untuk bank" --max-searches 6 --limit 8 --per-document-limit 2 --write-report
```

Commands with `--write-report` write Markdown and JSON files under `reports/` using the query slug in the filename.

## CLI Commands

### Audit And Build Metadata

```bash
uv run python -m thinking_layer.cli audit
uv run python -m thinking_layer.cli build
uv run python -m thinking_layer.cli all
```

Use `--hash` when you want SHA-256 hashes in the file manifest:

```bash
uv run python -m thinking_layer.cli all --hash
```

Outputs:

- `reports/corpus_audit.json`
- `reports/corpus_audit.md`
- `processed/canonical_regulations.ndjson`
- `processed/file_manifest.ndjson`

### Extract Documents

```bash
uv run python -m thinking_layer.cli extract --progress-every 25 --verbose
```

Useful development run:

```bash
uv run python -m thinking_layer.cli extract --limit 10 --progress-every 5 --verbose
```

Options:

- `--resume`: append outputs and skip file IDs already present in `processed/extracted_documents.ndjson`.
- `--limit N`: extract only first `N` manifest rows.
- `--max-pages N`: cap pages per file.
- `--target-pages RANGE`: pass a LiteParse page range such as `1-5,10` for focused extraction checks.
- `--enable-ocr`: enable LiteParse OCR for this run.
- `--ocr-server-url URL`: OCR HTTP endpoint, for example PaddleOCR at `http://localhost:8829/ocr`.
- `--ocr-language LANG`: OCR language code. Use `en` for the current Indonesian regulation corpus because the documents use Latin script and this avoids PaddleOCR model reloads.
- `--ocr-dpi N`: OCR DPI. Start with `150`; lower to `100` for very slow scans, and raise only after a one-page quality check.
- `--ocr-num-workers N`: OCR worker count. Start with `1` on a 16GB Mac.
- `--replace-existing`: for explicit `--file-id` runs, replace existing extracted rows and blocks for those file IDs instead of rewriting the full output files. Failed replacements preserve existing extracted rows and blocks.
- `--verbose`: print LiteParse timing logs, selected options, per-document status, and output counts.
- `--include-sikepo`: also extract Sikepo files. Off by default to avoid duplicate searchable documents.

LiteParse parser behavior is configured in `resources/config/extraction_heuristics.json`. OCR remains disabled by default for the normal corpus pass. The current baseline profile uses Markdown output, image mode `off`, link extraction, word-box emission, geometry-backed table/list reconstruction, and a table/list-aware block splitter. Files with little or no extractable text, parse failures, and Office files skipped because LibreOffice is missing are reported in `reports/ocr_needed.*`.

Selective OCR replacement flow:

1. Run or restore the normal no-OCR extraction first:

```bash
uv run python -m thinking_layer.cli extract --progress-every 25 --verbose
```

2. Start the optimized PaddleOCR service in another terminal:

The LiteParse PaddleOCR service is vendored under `./liteparse/ocr/paddleocr`. On Apple Silicon, prefer the local `uv` service first. The Docker path can start correctly but still crash inside PaddlePaddle native runtime with a segmentation fault after image decode/model initialization.

```bash
cd ./liteparse/ocr/paddleocr
uv python install 3.12
uv python pin 3.12
uv sync

PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK=True \
PADDLEOCR_TEXT_DETECTION_MODEL=PP-OCRv5_mobile_det \
PADDLEOCR_TEXT_DET_LIMIT_SIDE_LEN=960 \
PADDLEOCR_CPU_THREADS=4 \
PADDLEOCR_TEXT_RECOGNITION_BATCH_SIZE=8 \
uv run python server.py
```

This folder is already a uv project because LiteParse ships a `pyproject.toml` there. Use `uv python pin 3.12` to select Python `3.12` for the existing project. Do not run `uv init` inside this folder unless the `pyproject.toml` is missing.

After `uv python install 3.12`, `which python` may still return `python not found`. That is acceptable. uv installs a versioned executable such as `python3.12` and uses it through `uv run`. Verify with:

```bash
uv python find 3.12
uv run python --version
```

Only add uv's executable directory to your shell path if you want to call `python3.12` directly:

```bash
export PATH="$HOME/.local/bin:$PATH"
which python3.12
```

If `uv sync` fails with `Python downloads are set to 'never'` or `Python preference is set to 'only system'`, your uv config still disallows managed Python. Change uv back to managed Python or install Python `3.12` with your system package manager first, then rerun `uv sync`.

3. Benchmark one page before replacing a whole file:

```bash
uv run python -m thinking_layer.cli extract \
  --file-id FILE_ID_FROM_REPORTS_OCR_NEEDED_JSON \
  --target-pages 1 \
  --max-pages 1 \
  --replace-existing \
  --enable-ocr \
  --ocr-server-url http://localhost:8829/ocr \
  --ocr-language en \
  --ocr-dpi 150 \
  --ocr-num-workers 1 \
  --progress-every 1 \
  --verbose
```

4. Replace the full file only after the one-page run is stable:

```bash
uv run python -m thinking_layer.cli extract \
  --file-id FILE_ID_FROM_REPORTS_OCR_NEEDED_JSON \
  --replace-existing \
  --enable-ocr \
  --ocr-server-url http://localhost:8829/ocr \
  --ocr-language en \
  --ocr-dpi 150 \
  --ocr-num-workers 1 \
  --progress-every 1 \
  --verbose
```

Use `reports/ocr_needed.json` to choose `FILE_ID_FROM_REPORTS_OCR_NEEDED_JSON`. Do not run full-corpus OCR first. On an M1 Pro 16GB Mac, the validated profile was roughly 7-9 seconds per scanned page at `150 DPI` with `--ocr-num-workers 1`. `--ocr-num-workers 2` did not improve throughput in local tests because the single PaddleOCR server instance contends inside Paddle/PaddleOCR.

To process all remaining OCR-needed primary regulations:

```bash
jq -r '.[] | select((.reason // .extraction_reason) != "libreoffice_not_found") | select(.file_role == "primary_regulation") | .file_id' reports/ocr_needed.json |
while read -r file_id; do
  uv run python -m thinking_layer.cli extract \
    --file-id "$file_id" \
    --replace-existing \
    --enable-ocr \
    --ocr-server-url http://localhost:8829/ocr \
    --ocr-language en \
    --ocr-dpi 150 \
    --ocr-num-workers 1 \
    --progress-every 1 \
    --verbose
done
```

For a bad PDF that fails only at the trailing page boundary, use a bounded `--target-pages` replacement after confirming a single page parses. Example:

```bash
uv run python -m thinking_layer.cli extract \
  --file-id FILE_ID_FROM_REPORTS_OCR_NEEDED_JSON \
  --replace-existing \
  --target-pages 1-50 \
  --max-pages 50 \
  --progress-every 1 \
  --verbose
```

PaddleOCR troubleshooting on Mac/OrbStack:

- If the server log ends with `FatalError: Segmentation fault`, treat it as a PaddlePaddle runtime failure, not a retrieval or answer-quality signal.
- Use `--ocr-language en` for this corpus. If you pass `id`, PaddleOCR may reload a Latin model and slow the run without improving Indonesian legal text extraction.
- If Docker segfaults, retry the local `uv` server above before changing extraction code.
- If local PaddleOCR also segfaults, switch the OCR trial to LiteParse's EasyOCR service instead of adding ranking hacks:

```bash
cd ./liteparse/ocr/easyocr
uv python install 3.12
uv python pin 3.12
uv sync
uv run python server.py
```

Then point extraction at EasyOCR:

```bash
uv run python -m thinking_layer.cli extract \
  --enable-ocr \
  --ocr-server-url http://localhost:8828/ocr \
  --ocr-language en \
  --ocr-dpi 150 \
  --ocr-num-workers 1 \
  --file-id FILE_ID_FROM_REPORTS_OCR_NEEDED_JSON \
  --replace-existing \
  --target-pages 1 \
  --progress-every 1 \
  --verbose
```

Office documents and LibreOffice:

LiteParse needs LibreOffice for `.docx`, `.xlsx`, `.pptx`, `.odt`, `.ods`, and `.odp` files. If `soffice` or `libreoffice` is not on `PATH`, these rows are skipped with `libreoffice_not_found` and listed in `reports/ocr_needed.*`. This is important for operational BI documents such as QRIS/SNAP matrices; queries like `apa saja kelengkapan atau matriks yang diperlukan dalam pengembangan qris?` may be incomplete until these files are extracted.

PDF visual spot checks use the project dependencies `pypdfium2` and `pillow`. Poppler is also required for the CLI fallback renderer (`pdftoppm`). On macOS, install it with:

```bash
brew install poppler
```

On macOS:

```bash
brew install --cask libreoffice
export PATH="/Applications/LibreOffice.app/Contents/MacOS:$PATH"
which soffice
```

Then replace the skipped Office rows:

```bash
jq -r '.[] | select((.reason // .extraction_reason) == "libreoffice_not_found") | .file_id' reports/ocr_needed.json |
while read -r file_id; do
  uv run python -m thinking_layer.cli extract \
    --file-id "$file_id" \
    --replace-existing \
    --progress-every 1 \
    --verbose
done
```

After OCR or Office replacements, always refresh downstream artifacts:

```bash
uv run python -m thinking_layer.cli report
uv run python -m thinking_layer.cli build-source-corpus --include-secondary
uv run python -m thinking_layer.cli build-index
```

Outputs:

- `processed/extracted_documents.ndjson`
- `processed/blocks.ndjson`
- `processed/raw/liteparse/*.json` with page text, Markdown, text-item geometry, and word boxes
- `reports/ocr_needed.json`
- `reports/ocr_needed.md`

Refresh extraction reports from existing outputs:

```bash
uv run python -m thinking_layer.cli report
```

Spot-check extraction and citation quality for high-value regulation areas:

```bash
uv run python -m thinking_layer.cli extraction-spot-check
```

### Build Citation-Ready Corpus

```bash
uv run python -m thinking_layer.cli build-source-corpus --include-secondary
```

Outputs:

- `processed/source_corpus.ndjson`
- `reports/source_corpus_baseline.json`
- `reports/source_corpus_baseline.md`

This corpus is the retrieval contract. Each row contains issuer, source, source priority, file role, document identity, page, section type, best-effort `Pasal`/`Ayat`, citation text, and citation quality.

### Build Search Index

```bash
uv run python -m thinking_layer.cli build-index
```

Outputs:

- `processed/search_index/metadata.json`
- `processed/search_index/docs.ndjson`
- `processed/search_index/terms.ndjson`
- `processed/search_index/postings.ndjson`
- `processed/search_index/search.sqlite`

When `processed/source_corpus.ndjson` exists, indexing uses that file instead of raw blocks. The SQLite index stores block-level terms and document-title rows.

### Search And Query Planning

Lexical search:

```bash
uv run python -m thinking_layer.cli search "SLIK pelaporan debitur" --issuer OJK --role primary_regulation
uv run python -m thinking_layer.cli search "SNAP Open API Pembayaran" --issuer BI --include-secondary
```

Natural-language query planning:

```bash
uv run python -m thinking_layer.cli plan-query "apa saja peraturan periklanan yang harus dipatuhi oleh bank?"
uv run python -m thinking_layer.cli planned-search "apa saja peraturan periklanan yang harus dipatuhi oleh bank?" --max-searches 6 --limit 8
```

The planner uses:

- `resources/query_lexicon.json`
- `resources/indonesian-stopwords-complete.txt`

Indonesian stopwords are loaded at runtime from `resources/indonesian-stopwords-complete.txt`; they are not hardcoded in Python.

Phrase-level boosts are configured in `resources/query_lexicon.json` under `exact_phrases`; domain phrase lists should not be hidden in Python code.

### Lexicon Candidate Extraction

Generate deterministic entity/topic/alias candidates from the corpus:

```bash
uv run python -m thinking_layer.cli extract-lexicon-candidates --generated-min-score 16 --report-limit 80
```

Outputs:

- `processed/lexicon/candidates.json`
- `reports/lexicon_candidates.md`
- `resources/query_lexicon.generated.json`
- `resources/query_lexicon.reviewed.json`
- `resources/query_lexicon.merged.json`

Generated lexicon files are intentionally not kept in the clean baseline. Regenerate them only when doing lexicon review. If you create a reviewed file, merge it explicitly:

```bash
uv run python -m thinking_layer.cli merge-lexicon --output resources/query_lexicon.merged.json
```

### Evidence And Answer Composition

Build evidence:

```bash
uv run python -m thinking_layer.cli evidence "peraturan BI tentang penyedia jasa pembayaran apa saja?" --max-searches 6 --limit 8 --per-document-limit 2 --write-report
```

Compose answer:

```bash
uv run python -m thinking_layer.cli answer "peraturan BI tentang penyedia jasa pembayaran apa saja?" --max-searches 6 --limit 8 --per-document-limit 2 --write-report
```

The current answer composer is deterministic and template-based. It is not an LLM answer writer. It lists related documents, emits citation-backed evidence bullets, avoids known noisy extraction fragments, preserves citation quality, and says `Tidak ditemukan dalam dokumen yang tersedia` when the evidence pack requires refusal.

### Evaluations

Run fast unit tests for core pipeline contracts:

```bash
uv run python -m unittest discover -s tests -v
```

These tests cover metadata normalization, file-role classification, citation quality, source-corpus citation contracts, query planning, evidence confidence, answer status, and import/CLI wiring. They are intended to catch refactor regressions quickly; they do not replace retrieval quality evaluation.

Run development-set evaluations:

```bash
uv run python -m thinking_layer.cli smoke-test --max-searches 6 --limit 8
uv run python -m thinking_layer.cli eval-natural --max-searches 6 --limit 6
uv run python -m thinking_layer.cli eval-evidence --max-searches 6 --result-limit 10 --per-document-limit 2
uv run python -m thinking_layer.cli eval-answer --max-searches 6 --result-limit 10 --per-document-limit 2
uv run python -m thinking_layer.cli eval-answer-quality --max-searches 6 --result-limit 10 --per-document-limit 2
```

Development evaluation files:

- `resources/gold_questions.json`
- `resources/answer_quality_questions.json`

Current development reports:

- `reports/REPORT_INDEX.md`: concise map of every current report.
- `reports/retrieval_smoke_test.md`: 10/10 accepted, average score `0.998` after primary-first ranking correction.
- `reports/natural_language_eval.md`: 15/15 accepted, average score `0.999`.
- `reports/evidence_eval.md`: 30/30 accepted, average score `0.990`.
- `reports/answer_eval.md`: 30/30 accepted, average score `0.988`.
- `reports/answer_quality_eval.md`: 12/12 accepted, average score `1.000`.
- `reports/blind_external_holdout_manifest.json`: reviewer-owned holdout; evidence `18/19`, answer `18/19`, answer quality `9/10`.
- `reports/blind_external_holdout_triage.md`: classified holdout failures; the holdout is consumed and must not be used for tuning.
- `reports/semantic_retrieval_benchmark.md`: bounded three-model BM25/dense/RRF comparison; dense and RRF do not yet beat BM25.
- `reports/extraction_spot_check.md`: extraction/citation spot check for high-value BI/OJK regulation areas.
- `reports/parser_comparison_sample.md`: small LiteParse vs MinerU/layout-parser comparison gate before parser switching.
- `reports/visual_spot_check.md`: rendered page review for QRIS, SNAP, XLSX, and GMRA extraction quality.
- `reports/cross_regulator_coverage_audit.md`: direct-vs-adjacent topic coverage audit for BI/OJK comparison queries.
- `reports/answer_noise_audit.md`: legal boilerplate/noise audit for final answer composition.

Current extraction report:

- `reports/extraction_summary.md`: `2,475` extracted rows, `537,355` blocks, and `0` remaining skipped/OCR-needed/failed files.
- `reports/ocr_needed.md`: currently reports `0` skipped/OCR-needed files.

These are useful regression checks, not proof of real-world accuracy. The development set was created while tuning the pipeline.

### External Holdout

For honest validation, use the reviewer-owned external holdout files:

- `resources/holdout_questions.external.json`
- `resources/answer_quality_questions.external.json`

The current checked-in files are reviewer-owned and were written before the validation run. They are now a consumed blind holdout: do not tune code or labels against them without recording that the run is no longer blind. Create a fresh holdout set for any post-failure tuning.

The consumed blind run was executed with:

```bash
uv run python -m thinking_layer.cli validate-holdout \
  --gold-file resources/holdout_questions.external.json \
  --quality-file resources/answer_quality_questions.external.json \
  --report-prefix blind_external_holdout \
  --max-searches 6 \
  --result-limit 10 \
  --per-document-limit 2
```

Outputs:

- `reports/<prefix>_evidence.md`
- `reports/<prefix>_answer.md`
- `reports/<prefix>_answer_quality.md`
- `reports/<prefix>_manifest.json`
- `reports/<prefix>_review_checklist.md`

Do not use dry-run template reports as validation evidence.

The blind run produced `18/19` evidence, `18/19` answer, and `9/10` answer-quality acceptance. See `reports/blind_external_holdout_triage.md` for failure classification.

## Retrieval And Answer Requirements

The retrieval and answer layers should keep these constraints:

- Rank primary regulation files before FAQ, abstract, summary, and operational guidance files.
- Support cross-regulator questions across OJK and BI.
- For cross-regulator questions, do not treat adjacent evidence as direct evidence. Each requested issuer must have title, definition, or snippet evidence containing the requested topic or approved alias before the answer can be `strong`/`answerable`.
- Cite document and page whenever available.
- Cite `Pasal` and `Ayat` only when extracted from the evidence block.
- Never invent missing `Pasal`, `Ayat`, dates, or document titles.
- Say not found when evidence is weak, conflicting, or missing.
- Keep legal boilerplate out of final findings unless the user explicitly asks about preamble, considerations, legal basis metadata, promulgation, or enactment text.
- Keep Sikepo as measured enrichment until merge quality is validated.
- Keep OCR selective and measured: add OCR text to the index only after a focused replacement run improves extraction quality for the affected file.

## Concrete Next-Step Checklist

### 1. Finish Modular Refactor

- [x] Remove old `scripts/regulatory_pipeline.py` entrypoint.
- [x] Split foundation modules: paths, IO, text, metadata.
- [x] Split audit, extraction, and citation helpers.
- [x] Move foundation modules into `config/`, `common/`, and `corpus/`.
- [x] Split and remove `core.py`.
- [x] Split flat `lexicon.py` into `lexicon/candidates.py` and `lexicon/merge.py`.
- [x] Split `retrieval.py` into:
  - `indexing/lexical.py`
  - `indexing/sqlite.py`
  - `indexing/title.py`
  - `retrieval/query_tools.py`
  - `retrieval/planning.py`
  - `retrieval/search.py`
  - `evaluation/retrieval.py`
- [x] Split `answers.py` into:
  - `retrieval/evidence.py`
  - `answer/composer.py`
  - `answer/quality.py`
  - `evaluation/evidence.py`
  - `evaluation/answer.py`
  - `evaluation/holdout.py`
  - `evaluation/natural.py`
- [x] Replace transitional `from ... import *` imports with explicit imports.
- [x] Remove obsolete `answers.py` compatibility shim.
- [x] Add focused tests around metadata normalization, citation extraction, query planning, evidence packing, answer status, and import wiring.

### 2. Make Heuristics Explicit Before Tuning

This phase is behavior-preserving. Do not tune accuracy here. The goal is to make every manual weight, threshold, domain phrase, and noisy-pattern filter visible and auditable before adding embeddings or LLM answer composition.

- [x] Delete confirmed dead/stale code:
  - duplicate `NATURAL_LANGUAGE_EVALS` in `thinking_layer/evaluation/holdout.py`
  - unused `NOISY_ANSWER_PATTERNS` in `thinking_layer/evaluation/answer.py`
  - stale `SMOKE_QUERIES` in `thinking_layer/indexing/lexical.py`
  - unused `sqlite_planned_search()` if no CLI/runtime path needs it
- [x] Add `thinking_layer/config/heuristics.py` as the typed loader/validator for heuristic config.
- [x] Add split subsystem config files under `resources/config/`:
  - `retrieval_ranking.json`
  - `evidence_confidence.json`
  - `answer_ranking.json`
  - `evaluation_rubrics.json`
  - `extraction_heuristics.json`
  - `lexicon_extraction.json`
- [x] Move current runtime weights and thresholds into those config files without changing values.
- [x] Move domain terms embedded in Python code into lexicon/config where appropriate, including sector-alignment terms and intent broadening terms.
- [x] Move noisy legal boilerplate patterns into config and label them as corpus-noise filters.
- [x] Deduplicate in-memory BM25 and SQLite BM25 ranking helpers so both paths share the same scoring constants.
- [x] Add `reports/heuristics_audit.md` listing each heuristic, value, category, runtime impact, rationale, and calibration status.
- [x] Run unit tests and all development evaluations after the refactor.
- [x] If metrics change, investigate and report the reason instead of adding query-specific shortcuts. See `reports/regression_audit.md`.

Heuristic categories should be explicit:

- `standard_ir`: accepted retrieval constants such as BM25 `k1` and `b`.
- `manual_domain_policy`: project policy such as primary regulation ranking above FAQ/summary.
- `manual_domain_seed`: manually seeded regulatory terms or sector aliases.
- `corpus_noise_filter`: boilerplate/noise patterns observed in extracted legal documents.
- `parser_heuristic`: extraction thresholds or regexes used to form blocks/citations.
- `evaluation_rubric`: development scoring weights and pass thresholds.

### 3. Validate Baseline Honestly

- [x] Freeze current development reports as regression baseline.
- [x] Initialize external holdout files from templates.
- [x] Add external holdout reviewer guide.
- [x] Create blind external holdout questions before looking at outputs.
- [x] Run `validate-holdout` with report prefix `blind_external_holdout`.
- [x] Classify failures as retrieval/refusal-boundary and gold-label/evaluation-rubric issues. See `reports/blind_external_holdout_triage.md`.
- [x] Do not tune code against the blind holdout; the consumed holdout is preserved without post-run tuning.

### 4. Urgent Answer Correctness Fixes

These fixes must happen before semantic retrieval, embedding indexes, or LLM answer composition. The current failures are answer-layer correctness issues, not model-selection issues.

- [x] Add corpus-backed answer-noise audit for legal boilerplate patterns:
  - `DENGAN RAHMAT TUHAN YANG MAHA ESA`
  - `Menimbang`
  - `Mengingat`
  - `MEMUTUSKAN`
  - `Menetapkan`
  - `Lembaran Negara` / `Tambahan Lembaran Negara`
  - first-page title/preamble blocks
  - OJK/BI circular letter intros such as `Sehubungan dengan amanat`
- [x] Add `resources/config/answer_noise.json` with auditable categories:
  - `legal_preamble`
  - `consideration`
  - `legal_basis_reference`
  - `enactment`
  - `promulgation`
  - `letter_intro`
  - `substantive`
- [x] Add `thinking_layer/answer/noise.py` to classify evidence items before final answer selection.
- [x] Update answer composer ranking so substantive `Pasal`/`Ayat`/definition/obligation evidence wins over boilerplate when both exist.
- [x] Reject boilerplate from final `Temuan` bullets by default; allow it only for explicit user queries about preamble, legal considerations, enactment, promulgation, or legal-basis metadata.
- [x] Add `reports/answer_noise_audit.md` showing corpus frequency, examples, section types, and post-fix answer impact.
- [x] Add direct-topic coverage checks for cross-regulator queries.
- [x] Add `resources/config/cross_regulator_confidence.json` defining strict direct evidence:
  - topic or approved alias appears in document title, definition block, or cited snippet
  - generic adjacent terms do not count as direct evidence
  - each requested issuer must satisfy direct evidence before `strong`/`answerable`
- [x] Add `thinking_layer/retrieval/topic_coverage.py` as the topic-coverage module.
- [x] Return `partial` for cross-regulator questions when one requested issuer lacks direct topic-bearing evidence.
- [x] In partial cross-regulator answers, explicitly state which issuer lacks direct evidence for the requested topic; adjacent evidence must not be presented as direct findings.
- [x] Add `reports/cross_regulator_coverage_audit.md` with the PJP case and other BI/OJK comparison cases.
- [x] Re-run and preserve results for:
  - unit tests
  - smoke retrieval eval
  - natural-language eval
  - evidence eval
  - answer eval
  - answer-quality eval
  - reviewer-owned blind external holdout
- [x] Do not weaken answer-quality noise checks or relabel the PJP case as answerable without manual legal review.

### 5. Improve Extraction Quality

- [x] Review `reports/ocr_needed.md`.
- [x] Write prioritized extraction-quality review.
- [x] Add extraction/citation spot-check report for high-value documents.
- [x] Preserve LiteParse text-item geometry/word boxes in raw extraction output.
- [x] Add table/list-aware Markdown block splitting before retrieval indexing.
- [x] Decide OCR path for scanned PDFs: selective LiteParse + optimized PaddleOCR fallback, `en` language for Latin-script Indonesian documents, OCR off by default for the normal corpus pass.
- [x] Run PaddleOCR samples from `reports/ocr_needed.md`, compare output against the no-OCR baseline, and use `--replace-existing` for accepted file-level OCR replacements.
- [x] OCR-replace all primary-regulation OCR-needed files and selected secondary/operational OCR-needed PDFs, then rebuild source corpus and search index.
- [x] Recover `seojk 11-2015.pdf` with bounded `--target-pages 1-50` after full-file parsing hit a trailing page boundary error.
- [x] Install LibreOffice and extract the remaining `12` Office operational documents, especially QRIS/SNAP matrices.
- [x] Compare LiteParse extraction against a small MinerU/layout-parser sample before switching parsers.
- [x] Add document/page visual spot checks for high-value failed cases.
- [x] Improve Pasal/Ayat/Huruf extraction for non-standard formats.
- [x] Add table-specific handling for XLSX and regulation attachments.

### 6. Improve Lexicon And Query Understanding

- [x] Regenerate and review `reports/lexicon_candidates.md` when resuming lexicon work.
- [x] Approve a reviewed subset of high-confidence generated entities/topics/aliases. See `reports/lexicon_review.md`.
- [x] Merge the reviewed lexicon into the separately tested `resources/query_lexicon.merged.json`; keep the active runtime lexicon unchanged until a broader evaluation gate.
- [ ] Keep intents mostly manual because they represent user behavior, not document vocabulary.
- [ ] Add failure-driven aliases only when supported by corpus evidence or real user queries.

### 7. Benchmark Hybrid Retrieval Before Adoption

Current decision: keep BM25/title retrieval as the production baseline. On the bounded 5,000-block benchmark, the best dense/RRF result did not exceed BM25, so semantic retrieval is not enabled in the normal search, evidence, or answer paths.

- [x] Keep BM25/title retrieval as the production baseline and freeze its current reports.
- [x] Add a SentenceTransformers-compatible semantic retriever behind a separate CLI/runtime path.
- [x] Benchmark a bounded multilingual model matrix selected by Indonesian coverage, retrieval task results, license, model size, and local latency; do not select solely by aggregate MTEB rank. See `reports/semantic_retrieval_benchmark.md`; full-corpus rerun remains pending.
- [x] Build a persisted dense index with model ID, normalization, dimension, corpus signature, and chunking metadata for a bounded 5,000-block smoke index; full-corpus benchmarking remains pending.
- [x] Compare BM25-only, dense-only, and BM25+dense Reciprocal Rank Fusion on bounded retrieval metrics. The current result does not justify adoption: dense retrieval is substantially below BM25 and RRF does not improve it. Evidence, answer, quality, and fresh-holdout comparisons remain pending.
- [x] Measure bounded Recall@5/10/20, MRR, expected-document recall, and issuer coverage. Citation coverage, refusal precision, and evidence-noise rate remain pending until a candidate improves retrieval.
- [ ] Add a top-50/100 reranking experiment using a cross-encoder or late-interaction model only after hybrid retrieval clears the evaluation gates.
- [ ] Keep role, issuer, direct-topic, and citation-confidence gates after semantic retrieval and reranking.
- [ ] Only introduce query expansion, CRAG-style retrieval correction, or LLM answer composition after the hybrid baseline is measured and stable.

Next concrete step: rerun the benchmark over the full `537,355`-block source corpus, then evaluate any candidate that clears retrieval gates through evidence, answer-quality, and a fresh holdout. Do not promote a model based on the bounded benchmark alone.

### 8. Later Research Options

- [ ] Evaluate grounded multi-query expansion with RRF only if vocabulary-mismatch failures remain after hybrid retrieval.
- [ ] Evaluate hierarchical or graph retrieval for regulation references, supersession, and source timelines.
- [ ] Evaluate late-interaction retrieval if single-vector embeddings miss article-level legal distinctions.

### 9. Production Hardening Later

- [ ] Add incremental ingestion and stale-index detection.
- [ ] Add source/version timeline handling for regulation updates.
- [ ] Add permission model if the corpus becomes user-specific or restricted.
- [ ] Add observability for query plans, retrieved evidence, refusal reasons, and citation quality.
- [ ] Add API/service wrapper only after local CLI behavior is stable.
