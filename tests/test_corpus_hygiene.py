from __future__ import annotations

import unittest

from thinking_layer.corpus.build import annotate_primary_file_duplicates


def primary(
    file_id: str,
    *,
    canonical_id: str = "bi-pbi-10-tahun-2024",
    fingerprint: str = "same-content",
    issuer: str = "BI",
    source: str = "ease-bi",
) -> dict[str, object]:
    return {
        "file_id": file_id,
        "canonical_id": canonical_id,
        "dedupe_content_sha256": fingerprint,
        "issuer": issuer,
        "source": source,
        "file_role": "primary_regulation",
    }


class CorpusHygieneTests(unittest.TestCase):
    def test_exact_primary_copies_select_one_deterministic_searchable_file(self) -> None:
        manifests = [
            primary("ease-bi-pbi-10-copy-b"),
            primary("ojk-hosted-pbi-10", source="peraturan-ojk"),
            primary("ease-bi-pbi-10-copy-a"),
        ]

        summary = annotate_primary_file_duplicates(manifests)
        by_id = {item["file_id"]: item for item in manifests}

        self.assertEqual(summary["exact_primary_duplicate_groups"], 1)
        self.assertEqual(summary["suppressed_searchable_primary_files"], 2)
        self.assertTrue(by_id["ease-bi-pbi-10-copy-a"]["searchable_primary"])
        self.assertEqual(by_id["ease-bi-pbi-10-copy-a"]["primary_duplicate_status"], "preferred")
        self.assertFalse(by_id["ease-bi-pbi-10-copy-b"]["searchable_primary"])
        self.assertEqual(
            by_id["ease-bi-pbi-10-copy-b"]["primary_duplicate_of_file_id"],
            "ease-bi-pbi-10-copy-a",
        )
        self.assertFalse(by_id["ojk-hosted-pbi-10"]["searchable_primary"])

    def test_same_canonical_id_with_different_text_is_not_deduplicated(self) -> None:
        manifests = [
            primary("original", fingerprint="original-text"),
            primary("corrected", fingerprint="corrected-text"),
        ]

        summary = annotate_primary_file_duplicates(manifests)

        self.assertEqual(summary["exact_primary_duplicate_groups"], 0)
        self.assertTrue(all(item["searchable_primary"] for item in manifests))
        self.assertTrue(all(item["primary_duplicate_status"] == "unique" for item in manifests))

    def test_same_bytes_do_not_collapse_distinct_legal_instruments(self) -> None:
        manifests = [
            primary("base-regulation", canonical_id="ojk-pojk-1-2024", issuer="OJK", source="peraturan-ojk"),
            primary("amending-regulation", canonical_id="ojk-pojk-2-2024", issuer="OJK", source="peraturan-ojk"),
        ]

        summary = annotate_primary_file_duplicates(manifests)

        self.assertEqual(summary["exact_primary_duplicate_groups"], 0)
        self.assertTrue(all(item["searchable_primary"] for item in manifests))


if __name__ == "__main__":
    unittest.main()
