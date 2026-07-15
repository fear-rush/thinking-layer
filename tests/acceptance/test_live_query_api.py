from __future__ import annotations

import unittest

from fastapi.testclient import TestClient

from thinking_layer.api.app import create_app
from thinking_layer.indexing.sqlite import sqlite_index_is_current


class LiveQueryApiAcceptanceTests(unittest.TestCase):
    """Real HTTP acceptance checks; no stubs, patches, or fixture corpus."""

    @classmethod
    def setUpClass(cls) -> None:
        if not sqlite_index_is_current():
            raise RuntimeError(
                "Live acceptance requires a current processed/search_index/search.sqlite. "
                "Do not rebuild the corpus for this test; use the current generated index."
            )

    def test_pjp_advertising_question_returns_complete_primary_citations(self) -> None:
        question = "apa saja aturan periklanan yang harus dipenuhi oleh penyedia jasa pembayaran?"
        with TestClient(create_app()) as client:
            response = client.post("/queries", json={"question": question})

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "answerable")
        self.assertEqual(payload["confidence"]["label"], "strong")
        self.assertIn("menggunakan bahasa Indonesia", payload["answer"])
        self.assertIn("testimoni Konsumen", payload["answer"])
        self.assertIn("berizin dan diawasi oleh Bank Indonesia", payload["answer"])
        self.assertEqual(
            [
                (citation["page_start"], citation["pasal"], citation["ayat"])
                for citation in payload["citations"]
            ],
            [(4, "Pasal 7", "(1)"), (5, "Pasal 7", "(2)"), (5, "Pasal 7", "(3)")],
        )
        self.assertTrue(all(citation["file_id"] for citation in payload["citations"]))
        self.assertTrue(all(citation["source_block_ids"] for citation in payload["citations"]))


if __name__ == "__main__":
    unittest.main()
