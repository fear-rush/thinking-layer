from __future__ import annotations

import argparse
import importlib.util
import json
from collections import Counter
from pathlib import Path
from typing import Any

from ..common.io import read_json
from ..common.text import normalize_space
from ..config.paths import PROCESSED_DIR, REPORTS_DIR, ROOT, SOURCE_CORPUS_PATH


SAMPLE_CASES = [
    {
        "name": "BI QRIS Office Matrix",
        "file_id": "ease-bi-dokumen-persyaratan-pedoman-1201-0-matriks-dokumen-tambahan-untuk-pengembangan-qris",
        "focus_pages": [1],
        "reason": "Recently recovered Office document; table-heavy operational QRIS requirements.",
    },
    {
        "name": "BI SNAP Office Matrix",
        "file_id": "ease-bi-dokumen-persyaratan-pedoman-1256-0-matriks-tambahan-pengembangan-dengan-snap",
        "focus_pages": [1, 2, 3],
        "reason": "Recently recovered Office document; SNAP implementation requirements with tables and lists.",
    },
    {
        "name": "BI SNAP Functional Test XLSX",
        "file_id": "ease-bi-dokumen-persyaratan-pedoman-1206-0-skenario-pengujian",
        "focus_pages": [1, 2, 3],
        "reason": "Large spreadsheet conversion with many empty converted pages; good stress case for XLSX layout.",
    },
    {
        "name": "OJK GMRA Attachment",
        "file_id": "peraturan-ojk-global-master-repurchase-agreement-indonesia-2-lampiran-3-gmra-pdf",
        "focus_pages": [44, 62, 86],
        "reason": "Long PDF attachment with dense legal/table content and known citation-sensitive retrieval hits.",
    },
]


def raw_liteparse_files() -> list[Path]:
    raw_dir = PROCESSED_DIR / "raw" / "liteparse"
    return sorted(raw_dir.glob("*.json"))


def raw_liteparse_path(file_id: str) -> Path | None:
    prefix = f"{file_id}-"
    matches = [path for path in raw_liteparse_files() if path.name.startswith(prefix)]
    return matches[0] if matches else None


def source_rows_for_file(file_id: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not SOURCE_CORPUS_PATH.exists():
        return rows
    with SOURCE_CORPUS_PATH.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("file_id") == file_id:
                rows.append(row)
    return rows


def page_number(page: dict[str, Any], index: int) -> int:
    value = page.get("page_num") or page.get("page") or index + 1
    try:
        return int(value)
    except (TypeError, ValueError):
        return index + 1


def page_summary(page: dict[str, Any], index: int) -> dict[str, Any]:
    text = normalize_space(str(page.get("text") or ""))
    markdown = normalize_space(str(page.get("markdown") or ""))
    return {
        "page": page_number(page, index),
        "width": page.get("width"),
        "height": page.get("height"),
        "text_chars": len(text),
        "markdown_chars": len(markdown),
        "text_item_count": page.get("text_item_count") or len(page.get("text_items") or []),
        "table_marker_count": markdown.count("|"),
        "heading_marker_count": markdown.count("#"),
        "text_preview": text[:280],
        "markdown_preview": markdown[:280],
    }


def liteparse_case_report(case: dict[str, Any]) -> dict[str, Any]:
    file_id = str(case["file_id"])
    raw_path = raw_liteparse_path(file_id)
    rows = source_rows_for_file(file_id)
    section_types = Counter(str(row.get("section_type")) for row in rows)
    citation_quality = Counter(str(row.get("citation_quality")) for row in rows)
    extraction_methods = Counter(str(row.get("extraction_method")) for row in rows)
    result: dict[str, Any] = {
        **case,
        "raw_path": str(raw_path.relative_to(ROOT)) if raw_path else None,
        "source_rows": len(rows),
        "section_types": dict(section_types.most_common()),
        "citation_quality": dict(citation_quality.most_common()),
        "extraction_methods": dict(extraction_methods.most_common()),
    }
    if not raw_path:
        result["status"] = "missing_raw_liteparse_output"
        result["pages"] = []
        return result

    raw = read_json(raw_path)
    pages = raw.get("pages") or []
    focus_pages = {int(page) for page in case.get("focus_pages") or []}
    result.update(
        {
            "status": raw.get("status"),
            "resolved_path": raw.get("resolved_path"),
            "page_count": len(pages),
            "total_text_chars": len(normalize_space(str(raw.get("text") or ""))),
            "liteparse_options": raw.get("liteparse_options"),
            "pages": [
                page_summary(page, index)
                for index, page in enumerate(pages)
                if not focus_pages or page_number(page, index) in focus_pages
            ],
        }
    )
    return result


def candidate_parser_status() -> dict[str, Any]:
    layoutparser_available = importlib.util.find_spec("layoutparser") is not None
    mineru_available = importlib.util.find_spec("mineru") is not None
    return {
        "layoutparser": {
            "available_in_project_env": layoutparser_available,
            "detectron2_backend_available_in_project_env": False,
            "isolated_probe_results": [
                {
                    "command": "uv run --with layoutparser python -c 'import layoutparser as lp; ...'",
                    "result": "installed layoutparser 0.3.4, Detectron2LayoutModel not exposed",
                },
                {
                    "command": "uv run --with 'layoutparser[layoutmodels]' python -c 'import layoutparser as lp; ...'",
                    "result": "installed layoutparser 0.3.4 plus torch/torchvision/timm, Detectron2LayoutModel still not exposed",
                },
                {
                    "command": "uv run --with layoutparser --with torchvision --with 'detectron2 @ git+https://github.com/facebookresearch/detectron2.git@v0.5' ...",
                    "result": "failed to build detectron2 under Python 3.14 build isolation because torch is not declared as a build dependency",
                },
            ],
            "docs_basis": "LayoutParser docs show PubLayNet comparison requires Detectron2LayoutModel with a Detectron2 backend.",
        },
        "mineru": {
            "available_in_project_env": mineru_available,
            "cli_available": False,
            "probe_results": ["mineru not found", "magic-pdf not found"],
        },
    }


def build_parser_comparison_report() -> dict[str, Any]:
    return {
        "purpose": "Compare current LiteParse baseline against a small MinerU/layout-parser sample before switching parsers.",
        "candidate_parser_status": candidate_parser_status(),
        "cases": [liteparse_case_report(case) for case in SAMPLE_CASES],
        "decision": {
            "summary": "Do not switch parsers yet.",
            "reasons": [
                "Current LiteParse baseline has extracted all manifest files and preserves page-level citation anchors.",
                "LayoutParser's useful layout-detection path is not currently runnable in the Python 3.14 project environment without extra Detectron2 build work.",
                "MinerU is not part of the active baseline: it is a full document parser rather than a LiteParse OCR backend, and full-corpus runtime is not acceptable on the current local machine.",
                "The recovered Office cases are now searchable, and XLSX/table layout remains the main quality risk to review visually.",
            ],
            "next_actions": [
                "Run visual page checks for the sampled QRIS, SNAP, XLSX, and GMRA pages.",
                "Keep PaddleOCR as the selective OCR backend integrated through LiteParse.",
                "Prioritize table-specific handling for XLSX and regulation attachments before replacing the whole parser.",
            ],
        },
    }


def write_parser_comparison_report(report: dict[str, Any], md_path: Path, json_path: Path) -> None:
    lines = [
        "# Parser Comparison Sample",
        "",
        "Small comparison gate before switching away from LiteParse.",
        "",
        "## Candidate Parser Availability",
        "",
    ]
    layoutparser = report["candidate_parser_status"]["layoutparser"]
    mineru = report["candidate_parser_status"]["mineru"]
    lines.extend(
        [
            f"- LayoutParser in project env: `{layoutparser['available_in_project_env']}`",
            f"- LayoutParser Detectron2 backend in project env: `{layoutparser['detectron2_backend_available_in_project_env']}`",
            f"- MinerU Python package in project env: `{mineru['available_in_project_env']}`",
            f"- MinerU CLI available: `{mineru['cli_available']}`",
            "",
            "LayoutParser documentation indicates a meaningful layout-detection comparison needs `Detectron2LayoutModel` with a Detectron2 backend, for example PubLayNet. Local isolated probes installed base LayoutParser, but the Detectron2 backend was not available; the documented Detectron2 Git dependency did not build cleanly under this Python 3.14 environment.",
            "",
            "## LiteParse Baseline Sample",
            "",
            "| Case | Pages | Rows | Section Types | Citation Quality | Notes |",
            "|---|---:|---:|---|---|---|",
        ]
    )
    for case in report["cases"]:
        section_types = ", ".join(f"{key}: {value}" for key, value in case.get("section_types", {}).items()) or "-"
        citation_quality = ", ".join(f"{key}: {value}" for key, value in case.get("citation_quality", {}).items()) or "-"
        lines.append(
            f"| {case['name']} | {case.get('page_count', 0)} | {case.get('source_rows', 0)} | "
            f"{section_types} | {citation_quality} | {case['reason']} |"
        )

    for case in report["cases"]:
        lines.extend(
            [
                "",
                f"## {case['name']}",
                "",
                f"- File ID: `{case['file_id']}`",
                f"- Source path: `{case.get('resolved_path')}`",
                f"- Raw LiteParse output: `{case.get('raw_path')}`",
                f"- Status: `{case.get('status')}`",
                f"- Pages: `{case.get('page_count')}`",
                f"- Source rows: `{case.get('source_rows')}`",
                f"- Extraction methods: `{case.get('extraction_methods')}`",
                "",
                "### Focus Pages",
                "",
            ]
        )
        for page in case.get("pages") or []:
            lines.extend(
                [
                    f"- Page `{page['page']}`: text `{page['text_chars']}` chars, markdown `{page['markdown_chars']}` chars, text items `{page['text_item_count']}`, table markers `{page['table_marker_count']}`, headings `{page['heading_marker_count']}`",
                    f"  - Text: {page['text_preview']}",
                    f"  - Markdown: {page['markdown_preview']}",
                ]
            )

    decision = report["decision"]
    lines.extend(["", "## Decision", "", decision["summary"], "", "Reasons:"])
    lines.extend(f"- {reason}" for reason in decision["reasons"])
    lines.extend(["", "Next actions:"])
    lines.extend(f"- {action}" for action in decision["next_actions"])

    md_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def cmd_parser_comparison(_args: argparse.Namespace) -> None:
    REPORTS_DIR.mkdir(exist_ok=True)
    report = build_parser_comparison_report()
    md_path = REPORTS_DIR / "parser_comparison_sample.md"
    json_path = REPORTS_DIR / "parser_comparison_sample.json"
    write_parser_comparison_report(report, md_path, json_path)
    print(f"Wrote {md_path.relative_to(ROOT)}")
    print(f"Wrote {json_path.relative_to(ROOT)}")
