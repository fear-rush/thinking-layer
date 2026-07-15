from __future__ import annotations

import argparse

from .answer.composer import cmd_answer
from .answer.noise import cmd_answer_noise_audit
from .corpus.build import cmd_all, cmd_audit, cmd_build
from .corpus.extraction_pipeline import cmd_extract, cmd_rebuild_blocks, cmd_report
from .corpus.parser_comparison import cmd_parser_comparison
from .corpus.source_corpus import cmd_build_source_corpus
from .corpus.spot_check import cmd_extraction_spot_check
from .corpus.v2_audit import cmd_v2_corpus_audit
from .config.heuristic_audit import cmd_heuristics_audit
from .indexing.sqlite import cmd_build_index
from .indexing.semantic import cmd_build_semantic_index, cmd_semantic_search
from .lexicon.candidates import cmd_extract_lexicon_candidates
from .lexicon.merge import cmd_merge_lexicon
from .observability import cmd_trace_query
from .config.paths import ROOT
from .retrieval.evidence import cmd_evidence
from .retrieval.planning import cmd_plan_query
from .retrieval.search import cmd_planned_search, cmd_search
from .retrieval.topic_coverage import cmd_cross_regulator_coverage_audit

def main() -> None:
    parser = argparse.ArgumentParser(description="Local regulatory corpus processing utilities.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    audit_parser = subparsers.add_parser("audit", help="Write corpus audit reports.")
    audit_parser.set_defaults(func=cmd_audit)

    build_parser = subparsers.add_parser("build", help="Write canonical metadata and file manifest.")
    build_parser.add_argument("--hash", action="store_true", help="Compute sha256 hashes for existing files.")
    build_parser.set_defaults(func=cmd_build)

    extract_parser = subparsers.add_parser("extract", help="Extract documents with LiteParse and write page-aware blocks.")
    extract_parser.add_argument("--include-sikepo", action="store_true", help="Also extract Sikepo files. Off by default to avoid duplicate searchable documents.")
    extract_parser.add_argument("--file-id", action="append", default=None, help="Extract only this file_id. Can be repeated for OCR trials.")
    extract_parser.add_argument("--path-contains", default=None, help="Extract only manifest rows whose resolved path or title contains this text.")
    extract_parser.add_argument("--limit", type=int, default=None, help="Only extract the first N manifest files.")
    extract_parser.add_argument("--max-pages", type=int, default=1000, help="Maximum pages per file to parse.")
    extract_parser.add_argument("--target-pages", default=None, help="LiteParse page range, e.g. '1-5,10'. Useful for parser spot checks.")
    extract_parser.add_argument("--enable-ocr", action="store_true", help="Enable LiteParse OCR. Use with --ocr-server-url for PaddleOCR.")
    extract_parser.add_argument("--ocr-server-url", default=None, help="OCR HTTP endpoint, e.g. PaddleOCR at http://localhost:8829/ocr.")
    extract_parser.add_argument("--ocr-language", default=None, help="OCR language code. For Indonesian PaddleOCR tests prefer `en` because the documents use Latin script.")
    extract_parser.add_argument("--ocr-dpi", type=float, default=None, help="DPI for OCR extraction. Defaults to resources/config/extraction_heuristics.json.")
    extract_parser.add_argument("--ocr-num-workers", type=int, default=None, help="OCR worker count. Start with 1 on 16GB RAM.")
    extract_parser.add_argument("--resume", action="store_true", help="Append outputs and skip file IDs already present in extracted_documents.ndjson.")
    extract_parser.add_argument("--replace-existing", action="store_true", help="For explicit --file-id runs, replace existing extracted rows and blocks for those file IDs instead of rewriting the full output files.")
    extract_parser.add_argument("--progress-every", type=int, default=25, help="Print progress every N files. Use 0 to disable.")
    extract_parser.add_argument("--verbose", action="store_true", help="Print detailed extraction configuration, LiteParse timing logs, and per-document status.")
    extract_parser.set_defaults(func=cmd_extract)

    report_parser = subparsers.add_parser("report", help="Write extraction summary reports from existing outputs.")
    report_parser.set_defaults(func=cmd_report)

    rebuild_blocks_parser = subparsers.add_parser("rebuild-blocks", help="Rebuild v2 legal-unit blocks from saved raw LiteParse JSON.")
    rebuild_blocks_parser.add_argument("--file-id", action="append", default=None, help="Rebuild only an explicit saved-raw file ID.")
    rebuild_blocks_parser.add_argument("--replace-existing", action="store_true", help="Atomically replace blocks for explicit --file-id targets.")
    rebuild_blocks_parser.set_defaults(func=cmd_rebuild_blocks)

    extraction_spot_check_parser = subparsers.add_parser("extraction-spot-check", help="Spot-check extraction/citation quality for high-value documents.")
    extraction_spot_check_parser.add_argument("--source-corpus", default=None, help="Path to source_corpus.ndjson. Defaults to processed/source_corpus.ndjson.")
    extraction_spot_check_parser.set_defaults(func=cmd_extraction_spot_check)

    v2_audit_parser = subparsers.add_parser(
        "v2-corpus-audit",
        help="Audit generated v2 blocks/source corpus and fail on structural or source-hygiene violations.",
    )
    v2_audit_parser.add_argument("--blocks", default=None, help="Blocks NDJSON path. Defaults to processed/blocks.ndjson.")
    v2_audit_parser.add_argument(
        "--source-corpus",
        default=None,
        help="Source corpus NDJSON path. Defaults to processed/source_corpus.ndjson.",
    )
    v2_audit_parser.add_argument("--output", default=None, help="JSON report path. Defaults to reports/v2_corpus_audit.json.")
    v2_audit_parser.add_argument("--max-examples", type=int, default=5, help="Maximum examples retained per check.")
    v2_audit_parser.add_argument(
        "--report-only",
        action="store_true",
        help="Write and print the report without returning a failing exit status.",
    )
    v2_audit_parser.set_defaults(func=cmd_v2_corpus_audit)

    parser_comparison_parser = subparsers.add_parser("parser-comparison", help="Write small LiteParse vs MinerU/layout-parser comparison report.")
    parser_comparison_parser.set_defaults(func=cmd_parser_comparison)

    index_parser = subparsers.add_parser("build-index", help="Build persisted local BM25 search index.")
    index_parser.add_argument("--limit", type=int, default=None, help="Only index the first N blocks, for development.")
    index_parser.add_argument("--incremental", action="store_true", help="Append newly added source-corpus rows when the existing corpus is unchanged up to the previous index offset; otherwise rebuild safely.")
    index_parser.set_defaults(func=cmd_build_index)

    semantic_index_parser = subparsers.add_parser("build-semantic-index", help="Build an isolated persisted semantic index.")
    semantic_index_parser.add_argument("--model", default=None, help="SentenceTransformer model ID. Defaults to semantic retrieval config.")
    semantic_index_parser.add_argument("--limit", type=int, default=None, help="Only index the first N blocks for development.")
    semantic_index_parser.add_argument("--batch-size", type=int, default=None, help="Embedding batch size.")
    semantic_index_parser.add_argument("--normalize-embeddings", action=argparse.BooleanOptionalAction, default=None, help="Normalize embeddings before dot-product search.")
    semantic_index_parser.set_defaults(func=cmd_build_semantic_index)

    semantic_search_parser = subparsers.add_parser("semantic-search", help="Search the isolated persisted semantic index.")
    semantic_search_parser.add_argument("query", help="Semantic search query.")
    semantic_search_parser.add_argument("--issuer", choices=["OJK", "BI"], default=None)
    semantic_search_parser.add_argument("--source", choices=["peraturan-ojk", "ease-bi", "sikepo-ojk"], default=None)
    semantic_search_parser.add_argument("--role", default=None)
    semantic_search_parser.add_argument("--include-secondary", action="store_true")
    semantic_search_parser.add_argument("--limit", type=int, default=None, help="Result limit. Defaults to semantic retrieval config.")
    semantic_search_parser.set_defaults(func=cmd_semantic_search)

    source_corpus_parser = subparsers.add_parser("build-source-corpus", help="Write normalized citation-ready source corpus from extracted blocks.")
    source_corpus_parser.add_argument("--include-secondary", action="store_true", help="Include FAQ and summary rows. Off by default for a primary-first baseline.")
    source_corpus_parser.set_defaults(func=cmd_build_source_corpus)

    heuristics_audit_parser = subparsers.add_parser("heuristics-audit", help="Write configured heuristic values to reports/heuristics_audit.md.")
    heuristics_audit_parser.set_defaults(func=cmd_heuristics_audit)

    answer_noise_audit_parser = subparsers.add_parser("answer-noise-audit", help="Classify legal boilerplate/noise in the source corpus.")
    answer_noise_audit_parser.add_argument("--source-corpus", default=None, help="Path to source_corpus.ndjson. Defaults to processed/source_corpus.ndjson.")
    answer_noise_audit_parser.add_argument("--max-examples", type=int, default=None, help="Maximum examples per noise category.")
    answer_noise_audit_parser.set_defaults(func=cmd_answer_noise_audit)

    cross_coverage_parser = subparsers.add_parser("cross-regulator-coverage-audit", help="Audit direct topic coverage for cross-regulator questions.")
    cross_coverage_parser.add_argument("query", nargs="*", help="Optional query or queries. Defaults to configured audit queries.")
    cross_coverage_parser.add_argument("--max-searches", type=int, default=6, help="Maximum planned searches per query.")
    cross_coverage_parser.add_argument("--limit", type=int, default=10, help="Merged evidence blocks per query.")
    cross_coverage_parser.add_argument("--per-document-limit", type=int, default=2, help="Maximum evidence blocks per document.")
    cross_coverage_parser.set_defaults(func=cmd_cross_regulator_coverage_audit)

    search_parser = subparsers.add_parser("search", help="Search extracted citation blocks with local BM25.")
    search_parser.add_argument("query", help="Search query.")
    search_parser.add_argument("--issuer", choices=["OJK", "BI"], default=None, help="Restrict search to one issuer.")
    search_parser.add_argument("--source", choices=["peraturan-ojk", "ease-bi", "sikepo-ojk"], default=None, help="Restrict search to one source.")
    search_parser.add_argument("--role", default=None, help="Restrict search to one file role, e.g. primary_regulation.")
    search_parser.add_argument("--include-secondary", action="store_true", help="Include FAQ and summary blocks. Off by default for ad-hoc search.")
    search_parser.add_argument("--limit", type=int, default=10, help="Number of results.")
    search_parser.set_defaults(func=cmd_search)

    lexicon_parser = subparsers.add_parser("extract-lexicon-candidates", help="Derive entity/topic/alias candidates from local corpus artifacts.")
    lexicon_parser.add_argument("--min-score", type=float, default=0.0, help="Only write candidates with at least this score.")
    lexicon_parser.add_argument("--generated-min-score", type=float, default=12.0, help="Minimum score for generated lexicon draft entries.")
    lexicon_parser.add_argument("--generated-min-support", type=int, default=1, help="Minimum support count for generated lexicon draft entries.")
    lexicon_parser.add_argument("--report-limit", type=int, default=80, help="Maximum rows per candidate type in markdown report.")
    lexicon_parser.add_argument("--max-blocks", type=int, default=None, help="Only scan the first N blocks for fast iteration.")
    lexicon_parser.set_defaults(func=cmd_extract_lexicon_candidates)

    merge_lexicon_parser = subparsers.add_parser("merge-lexicon", help="Merge reviewed generated lexicon entries with resources/query_lexicon.json.")
    merge_lexicon_parser.add_argument(
        "--output",
        default=str(ROOT / "processed" / "lexicon" / "query_lexicon.merged.json"),
        help="Output path for the generated merge preview.",
    )
    merge_lexicon_parser.set_defaults(func=cmd_merge_lexicon)

    plan_parser = subparsers.add_parser("plan-query", help="Plan natural-language regulatory searches.")
    plan_parser.add_argument("query", help="Natural-language user query.")
    plan_parser.add_argument("--max-searches", type=int, default=12, help="Maximum planned searches.")
    plan_parser.set_defaults(func=cmd_plan_query)

    planned_search_parser = subparsers.add_parser("planned-search", help="Run natural-language query planning plus retrieval.")
    planned_search_parser.add_argument("query", help="Natural-language user query.")
    planned_search_parser.add_argument("--max-searches", type=int, default=12, help="Maximum planned searches.")
    planned_search_parser.add_argument("--limit", type=int, default=10, help="Number of merged results.")
    planned_search_parser.set_defaults(func=cmd_planned_search)

    evidence_parser = subparsers.add_parser("evidence", help="Build a conservative citation evidence pack for a natural-language question.")
    evidence_parser.add_argument("query", help="Natural-language user query.")
    evidence_parser.add_argument("--max-searches", type=int, default=8, help="Maximum planned searches.")
    evidence_parser.add_argument("--limit", type=int, default=12, help="Number of merged evidence blocks.")
    evidence_parser.add_argument("--per-document-limit", type=int, default=3, help="Maximum evidence blocks per document.")
    evidence_parser.add_argument("--write-report", action="store_true", help="Write markdown and JSON evidence reports.")
    evidence_parser.set_defaults(func=cmd_evidence)

    answer_parser = subparsers.add_parser("answer", help="Compose a deterministic citation-first answer from an evidence pack.")
    answer_parser.add_argument("query", help="Natural-language user query.")
    answer_parser.add_argument("--max-searches", type=int, default=8, help="Maximum planned searches.")
    answer_parser.add_argument("--limit", type=int, default=12, help="Number of merged evidence blocks.")
    answer_parser.add_argument("--per-document-limit", type=int, default=3, help="Maximum evidence blocks per document.")
    answer_parser.add_argument("--max-documents", type=int, default=6, help="Maximum documents to include in the answer.")
    answer_parser.add_argument("--max-citations-per-document", type=int, default=2, help="Maximum citations per document in the answer.")
    answer_parser.add_argument("--write-report", action="store_true", help="Write markdown and JSON answer reports.")
    answer_parser.set_defaults(func=cmd_answer)

    trace_parser = subparsers.add_parser("trace-query", help="Record query-plan, retrieval, refusal, citation, and answer observability.")
    trace_parser.add_argument("query", help="Natural-language user query.")
    trace_parser.add_argument("--max-searches", type=int, default=8, help="Maximum planned searches.")
    trace_parser.add_argument("--limit", type=int, default=12, help="Merged evidence blocks.")
    trace_parser.add_argument("--per-document-limit", type=int, default=3, help="Maximum evidence blocks per document.")
    trace_parser.add_argument("--max-documents", type=int, default=6, help="Maximum documents used in the answer.")
    trace_parser.add_argument("--max-citations-per-document", type=int, default=2, help="Maximum citations per document.")
    trace_parser.add_argument("--top-evidence", type=int, default=10, help="Number of evidence summaries to retain in the trace.")
    trace_parser.add_argument("--write-report", action="store_true", help="Write a JSON trace under reports/.")
    trace_parser.add_argument("--output", default=None, help="Optional JSON trace output path.")
    trace_parser.set_defaults(func=cmd_trace_query)

    all_parser = subparsers.add_parser("all", help="Run audit and build.")
    all_parser.add_argument("--hash", action="store_true", help="Compute sha256 hashes for existing files.")
    all_parser.set_defaults(func=cmd_all)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
