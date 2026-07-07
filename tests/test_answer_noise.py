from __future__ import annotations

import unittest

from thinking_layer.answer.noise import classify_answer_noise, should_use_claim_in_answer


class AnswerNoiseTests(unittest.TestCase):
    def test_legal_preamble_is_rejected_by_default(self) -> None:
        text = (
            "PERATURAN BANK INDONESIA NOMOR 22/8/PBI/2020 TENTANG PERIZINAN "
            "DENGAN RAHMAT TUHAN YANG MAHA ESA GUBERNUR BANK INDONESIA, Menimbang: ..."
        )
        classification = classify_answer_noise(text)
        self.assertEqual(classification.category, "legal_preamble")
        self.assertFalse(classification.explicit_allowed)
        self.assertFalse(should_use_claim_in_answer({"text": text}))

    def test_explicit_query_allows_requested_boilerplate_category(self) -> None:
        text = "Mengingat : Undang-Undang Nomor 23 Tahun 1999 tentang Bank Indonesia."
        classification = classify_answer_noise(text, query="apa dasar hukum dan mengingat dari aturan ini?")
        self.assertEqual(classification.category, "legal_basis_reference")
        self.assertTrue(classification.explicit_allowed)
        self.assertTrue(should_use_claim_in_answer({"text": text}, query="apa dasar hukum dan mengingat dari aturan ini?"))

    def test_substantive_pasal_is_allowed(self) -> None:
        text = "Pasal 2 (1) Prinsip perizinan terpadu Bank Indonesia melalui FO Perizinan meliputi transparan dan akuntabel."
        classification = classify_answer_noise(text)
        self.assertEqual(classification.category, "substantive")
        self.assertTrue(should_use_claim_in_answer({"text": text}))


if __name__ == "__main__":
    unittest.main()
