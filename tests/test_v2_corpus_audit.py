from __future__ import annotations

import argparse
from contextlib import redirect_stdout
from copy import deepcopy
from io import StringIO
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from thinking_layer.corpus.v2_audit import audit_v2_artifacts, cmd_v2_corpus_audit


def valid_row(block_id: str = "block-1", **overrides: object) -> dict[str, object]:
    legal_path = {"pasal": "Pasal 1", "ayat": "(1)"}
    row: dict[str, object] = {
        "chunk_schema_version": 2,
        "block_id": block_id,
        "node_id": block_id,
        "file_id": "bi-pbi-1-2026",
        "issuer": "BI",
        "regulation_type": "PBI",
        "file_role": "primary_regulation",
        "unit_type": "ayat",
        "section_type": "ayat",
        "document_part": "normative",
        "page_start": 1,
        "page_end": 1,
        "anchors": {"page_start": 1, "line_start": 1, "page_end": 1, "line_end": 1},
        "legal_path": legal_path,
        "display_text": "(1) Bank wajib menyampaikan laporan.",
        "retrieval_text": "Pasal 1 ayat (1). Bank wajib menyampaikan laporan.",
        "text": "(1) Bank wajib menyampaikan laporan.",
        "source_block_ids": [block_id],
        "citation_admission": "atomic_leaf",
        "searchable_primary": True,
        "legal_unit": {
            "type": "ayat",
            "document_part": "normative",
            "legal_path": legal_path,
            "source_spans": [
                {
                    "span_id": f"{block_id}-span-1",
                    "page": 1,
                    "line_start": 1,
                    "line_end": 1,
                    "text": "(1) Bank wajib menyampaikan laporan.",
                }
            ],
        },
    }
    row.update(overrides)
    return row


class V2CorpusAuditTests(unittest.TestCase):
    def test_clean_v2_fixture_passes_every_gate(self) -> None:
        block = valid_row()
        source = deepcopy(block)

        report = audit_v2_artifacts([block], [source])

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["summary"]["failed_checks"], 0)
        self.assertTrue(all(check["count"] == 0 for check in report["checks"].values()))

    def test_normative_use_of_penjelasan_is_not_an_explanation_boundary(self) -> None:
        block = valid_row(
            display_text="(1) Bank wajib memberikan keterangan dan/atau penjelasan tertulis.",
            retrieval_text="Pasal 1 ayat (1). Bank wajib memberikan penjelasan tertulis.",
        )

        report = audit_v2_artifacts([block], [deepcopy(block)])

        self.assertEqual(report["checks"]["document_part_contamination"]["count"], 0)

    def test_each_structural_and_source_hygiene_violation_is_reported(self) -> None:
        blocks = [valid_row("clean")]
        sources = [deepcopy(blocks[0])]

        non_v2 = valid_row("non-v2", chunk_schema_version=1)
        blocks.append(non_v2)
        sources.append(valid_row("non-v2"))

        dangling = valid_row("dangling", display_text="(2) Ketentuan sebagaimana dimaksud pada ayat")
        blocks.append(dangling)
        sources.append(deepcopy(dangling))

        oversized = valid_row(
            "oversized",
            unit_type="pasal",
            section_type="pasal",
            page_start=1,
            page_end=3,
            legal_path={"pasal": "Pasal 122"},
            display_text="Pasal 122 " + ("Perusahaan wajib menyampaikan laporan. " * 45),
            retrieval_text="Pasal 122 " + ("Perusahaan wajib menyampaikan laporan. " * 45),
            legal_unit={
                "type": "pasal",
                "document_part": "normative",
                "legal_path": {"pasal": "Pasal 122"},
                "source_spans": [{"span_id": "oversized-span", "page": 1, "text": "Pasal 122"}],
            },
        )
        blocks.append(oversized)
        sources.append(deepcopy(oversized))

        url = valid_row("url", retrieval_text="Pasal 1 https://jdih.ojk.go.id/")
        blocks.append(url)
        sources.append(deepcopy(url))

        empty_path = valid_row(
            "empty-path",
            legal_path={},
            legal_unit={
                "type": "ayat",
                "document_part": "normative",
                "legal_path": {},
                "source_spans": [{"span_id": "empty-span", "page": 1, "text": "teks"}],
            },
        )
        blocks.append(empty_path)
        sources.append(deepcopy(empty_path))

        issuer = valid_row("issuer", issuer="OJK", regulation_type="PBI")
        blocks.append(issuer)
        sources.append(deepcopy(issuer))

        duplicate = valid_row(
            "duplicate",
            searchable_primary=False,
            primary_duplicate_status="duplicate",
            primary_duplicate_of_file_id="preferred",
        )
        blocks.append(deepcopy(duplicate))
        sources.append(duplicate)

        table = valid_row(
            "table",
            unit_type="table",
            section_type="table",
            display_text="| Komponen | Rumus |\n|---|---|\n| DRC | ∑ Wi × Li = DRC |",
            retrieval_text="Tabel DRC ∑ Wi × Li = DRC",
            legal_unit={
                "type": "table",
                "document_part": "normative",
                "legal_path": {"pasal": "Pasal 1", "ayat": "(1)"},
                "source_spans": [{"span_id": "table-span", "page": 1, "text": "table"}],
            },
        )
        blocks.append(table)
        sources.append(deepcopy(table))

        explanation = valid_row(
            "explanation",
            unit_type="pasal",
            section_type="pasal",
            legal_path={"pasal": "Pasal 2"},
            display_text="Pasal 2 Cukup jelas.",
            retrieval_text="Pasal 2 Cukup jelas.",
            legal_unit={
                "type": "pasal",
                "document_part": "normative",
                "legal_path": {"pasal": "Pasal 2"},
                "source_spans": [{"span_id": "explanation-span", "page": 20, "text": "Cukup jelas."}],
            },
        )
        blocks.append(explanation)
        sources.append(deepcopy(explanation))

        report = audit_v2_artifacts(blocks, sources, max_examples=1)

        self.assertEqual(report["status"], "fail")
        self.assertEqual(report["summary"]["failed_checks"], 9)
        self.assertTrue(all(report["checks"][name]["count"] >= 1 for name in report["checks"]))
        self.assertTrue(all(len(report["checks"][name]["examples"]) <= 1 for name in report["checks"]))

    def test_command_writes_concise_json_and_controls_failure_exit(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            blocks_path = root / "blocks.ndjson"
            source_path = root / "source.ndjson"
            output_path = root / "audit.json"
            bad = valid_row("bad", issuer="OJK", regulation_type="PBI")
            blocks_path.write_text(json.dumps(bad) + "\n", encoding="utf-8")
            source_path.write_text(json.dumps(bad) + "\n", encoding="utf-8")
            args = argparse.Namespace(
                blocks=str(blocks_path),
                source_corpus=str(source_path),
                output=str(output_path),
                max_examples=2,
                report_only=False,
            )

            with redirect_stdout(StringIO()), self.assertRaisesRegex(SystemExit, "1"):
                cmd_v2_corpus_audit(args)

            args.report_only = True
            stdout = StringIO()
            with redirect_stdout(stdout):
                cmd_v2_corpus_audit(args)

            compact = json.loads(stdout.getvalue())
            written = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertEqual(compact["status"], "fail")
        self.assertEqual(written, compact)
        self.assertEqual(compact["checks"]["issuer_instrument_mismatch"]["count"], 1)


if __name__ == "__main__":
    unittest.main()
