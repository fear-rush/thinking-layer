from __future__ import annotations

import unittest

from thinking_layer.answer.alignment import answer_alignment
from thinking_layer.answer.composer import compose_template_answer, evidence_claim_text
from thinking_layer.retrieval.evidence import evidence_confidence
from thinking_layer.retrieval.planning import build_query_plan


def answer_item(
    *,
    block_id: str,
    claim: str,
    document: str,
    page: int = 1,
    pasal: str = "Pasal 1",
    support_score: float = 10.0,
) -> dict[str, object]:
    return {
        "file_id": "file-1",
        "block_id": block_id,
        "chunk_schema_version": 2,
        "source_block_ids": [block_id],
        "unit_path": [pasal],
        "legal_path": {"pasal": pasal},
        "anchors": [],
        "source_spans": [],
        "page_start": page,
        "score": support_score,
        "support_score": support_score,
        "citation_quality": "document_page_pasal",
        "section_type": "pasal",
        "extraction_flags": [],
        "assembled_text": claim,
        "text": claim,
        "snippet": claim,
        "citation": {
            "document": document,
            "page": page,
            "page_start": page,
            "page_end": page,
            "pasal": pasal,
            "text": f"{document}, hlm. {page}, {pasal}",
            "quality": "document_page_pasal",
        },
    }


class AnswerAlignmentTests(unittest.TestCase):
    def test_adversarial_unsupported_facts_do_not_align_to_legal_evidence(self) -> None:
        unrelated = [
            (
                "Berapa suhu AC di kantor Bank Indonesia?",
                "Bank wajib memperoleh izin untuk melakukan kegiatan usaha.",
                "Perizinan Bank",
            ),
            (
                "Apakah OJK wajib menyediakan teh manis di ruang rapat?",
                "Perusahaan wajib menyampaikan laporan tahunan kepada OJK.",
                "Pelaporan Perusahaan",
            ),
            (
                "Apakah pegawai OJK wajib memakai seragam warna ungu?",
                "Perusahaan wajib menjaga kecukupan aset dan liabilitas.",
                "Perusahaan Asuransi",
            ),
        ]
        for query, claim, document in unrelated:
            with self.subTest(query=query):
                alignment = answer_alignment(
                    query,
                    {"assembled_text": claim, "citation": {"document": document}},
                )
                self.assertFalse(alignment.accepted)

    def test_valid_definition_and_bounded_enumeration_align(self) -> None:
        definition = answer_alignment(
            "Apa definisi Kontrak Perwaliamanatan?",
            {
                "assembled_text": "Kontrak Perwaliamanatan adalah perjanjian antara Emiten dan Wali Amanat.",
                "citation": {"document": "Peraturan Wali Amanat"},
            },
        )
        enumeration = answer_alignment(
            "Apa aktivitas Penyedia Jasa Pembayaran?",
            {
                "assembled_text": "Aktivitas Penyedia Jasa Pembayaran meliputi penatausahaan sumber dana dan layanan remitansi.",
                "citation": {"document": "Penyedia Jasa Pembayaran"},
            },
        )
        self.assertTrue(definition.accepted)
        self.assertTrue(enumeration.accepted)

        minimum_duties = answer_alignment(
            "Apa tugas minimum Sekretaris Perusahaan menurut POJK 35 Tahun 2014?",
            {
                "assembled_text": "Fungsi sekretaris perusahaan melaksanakan tugas paling kurang mengikuti perkembangan Pasar Modal.",
                "citation": {"document": "Sekretaris Perusahaan Emiten atau Perusahaan Publik"},
            },
        )
        self.assertTrue(minimum_duties.accepted)
        self.assertFalse(minimum_duties.value_required)

        prohibition = answer_alignment(
            "Apa larangan OJK bagi PUJK terkait data pribadi konsumen?",
            {
                "assembled_text": "PUJK dilarang memberikan data pribadi Konsumen kepada pihak lain sebagai syarat penggunaan layanan.",
                "citation": {"document": "Pelindungan Konsumen"},
            },
        )
        unrelated_data_rule = answer_alignment(
            "Apa larangan OJK bagi PUJK terkait data pribadi konsumen?",
            {
                "assembled_text": "PUJK wajib memberitahukan Konsumen mengenai sumber data pribadi yang diperoleh.",
                "citation": {"document": "Pelindungan Konsumen"},
            },
        )
        self.assertTrue(prohibition.accepted)
        self.assertFalse(unrelated_data_rule.accepted)

        exact_permission = answer_alignment(
            "Berapa batas pembawaan UKA yang wajib memperoleh izin BI?",
            {
                "assembled_text": "Pembawaan UKA paling sedikit Rp1.000.000.000 wajib memperoleh Izin Pembawaan UKA dari Bank Indonesia.",
                "citation": {"document": "Pembawaan Uang Kertas Asing"},
            },
        )
        different_approval = answer_alignment(
            "Berapa batas pembawaan UKA yang wajib memperoleh izin BI?",
            {
                "assembled_text": "Pembawaan UKA paling sedikit Rp1.000.000.000 wajib memperoleh Persetujuan Pembawaan UKA.",
                "citation": {"document": "Perubahan Pembawaan Uang Kertas Asing"},
            },
        )
        self.assertTrue(exact_permission.accepted)
        self.assertFalse(different_approval.accepted)
        self.assertIn("legal_anchor_not_supported:izin", different_approval.reasons)

        compound_obligation = answer_alignment(
            "Di mana bank wajib menempatkan pusat data dan kapan boleh di luar Indonesia?",
            {
                "assembled_text": "Bank wajib menempatkan Pusat Data di wilayah Indonesia.",
                "citation": {"document": "Penyelenggaraan Teknologi Informasi oleh Bank Umum"},
            },
        )
        compound_permission = answer_alignment(
            "Di mana bank wajib menempatkan pusat data dan kapan boleh di luar Indonesia?",
            {
                "assembled_text": "Bank dapat menempatkan Pusat Data di luar wilayah Indonesia sepanjang memperoleh izin OJK.",
                "citation": {"document": "Penyelenggaraan Teknologi Informasi oleh Bank Umum"},
            },
        )
        self.assertTrue(compound_obligation.accepted)
        self.assertTrue(compound_permission.accepted)

    def test_lifecycle_question_requires_explicit_lifecycle_provenance(self) -> None:
        query = "Apakah POJK 31 Tahun 2016 masih berlaku?"
        plan = build_query_plan(query)
        item = {
            "issuer": "OJK",
            "is_primary": True,
            "has_page": True,
            "has_article": True,
            "matched_exact_phrases": ["POJK 31 Tahun 2016"],
            "lexical_support": 1.0,
            "regulation_type": "POJK",
            "number": "31",
            "year": "2016",
            "citation": {"document": "POJK Nomor 31 Tahun 2016", "page": 1, "pasal": "Pasal 1"},
            "snippet": "POJK Nomor 31 Tahun 2016 mengatur usaha pergadaian.",
        }
        confidence = evidence_confidence([item], ["OJK"], plan, query)

        self.assertEqual(confidence["label"], "weak")
        self.assertTrue(confidence["must_say_not_found"])
        self.assertIn("lifecycle_provenance_unavailable", confidence["reasons"])

        answer = compose_template_answer(
            {"query": query, "confidence": confidence, "plan": plan, "documents": []}
        )
        self.assertEqual(answer["status"], "not_found")
        self.assertEqual(answer["findings"], [])
        self.assertEqual(answer["citations"], [])
        self.assertIn("keberlakuan tidak dapat dipastikan", answer["summary"])

    def test_composer_prunes_off_target_item_even_when_it_scores_higher(self) -> None:
        query = "Apa definisi Kontrak Perwaliamanatan?"
        correct = answer_item(
            block_id="correct",
            claim="Kontrak Perwaliamanatan adalah perjanjian antara Emiten dan Wali Amanat.",
            document="Peraturan Wali Amanat",
            support_score=10.0,
        )
        unrelated = answer_item(
            block_id="unrelated",
            claim="Perusahaan wajib menyampaikan laporan tahunan kepada OJK.",
            document="Pelaporan Perusahaan",
            support_score=100.0,
        )
        pack = {
            "query": query,
            "confidence": {"label": "strong", "score": 0.9, "must_say_not_found": False},
            "plan": {"issuers": ["OJK"]},
            "documents": [
                {"issuer": "OJK", "document": "Pelaporan Perusahaan", "citations": [unrelated]},
                {"issuer": "OJK", "document": "Peraturan Wali Amanat", "citations": [correct]},
            ],
        }

        answer = compose_template_answer(pack)

        self.assertEqual(len(answer["findings"]), 1)
        self.assertIn("Kontrak Perwaliamanatan adalah", answer["findings"][0]["text"])
        self.assertEqual([citation["block_id"] for citation in answer["citations"]], ["correct"])

    def test_pack_with_only_unusable_claim_is_strict_not_found(self) -> None:
        query = "Apa larangan OJK bagi PUJK terkait data pribadi konsumen?"
        unrelated = answer_item(
            block_id="unrelated-data-rule",
            claim="PUJK wajib memberitahukan Konsumen mengenai sumber data pribadi yang diperoleh.",
            document="Pelindungan Konsumen",
            support_score=100.0,
        )
        pack = {
            "query": query,
            "confidence": {"label": "strong", "score": 0.9, "must_say_not_found": False},
            "plan": {"issuers": ["OJK"]},
            "documents": [{"issuer": "OJK", "document": "Pelindungan Konsumen", "citations": [unrelated]}],
        }

        answer = compose_template_answer(pack)

        self.assertEqual(answer["status"], "not_found")
        self.assertEqual(answer["findings"], [])
        self.assertEqual(answer["citations"], [])
        self.assertEqual(answer["related_documents"], [])
        self.assertTrue(answer["confidence"]["must_say_not_found"])

    def test_per_document_cap_is_enforced_and_documents_used_accumulates(self) -> None:
        query = "Apa kewajiban pelaporan Bank?"
        items = [
            answer_item(
                block_id=f"item-{index}",
                claim=f"Bank wajib menyampaikan laporan berkala tahap {index} kepada OJK.",
                document="Pelaporan Bank",
                page=index,
                pasal=f"Pasal {index}",
                support_score=20.0 - index,
            )
            for index in range(1, 4)
        ]
        pack = {
            "query": query,
            "confidence": {"label": "strong", "score": 0.9, "must_say_not_found": False},
            "plan": {"issuers": ["OJK"]},
            "documents": [{"issuer": "OJK", "document": "Pelaporan Bank", "citations": items}],
        }

        answer = compose_template_answer(pack, max_citations_per_document=2)

        self.assertEqual(answer["citation_count"], 2)
        self.assertEqual(len(answer["documents_used"]), 1)
        self.assertEqual(len(answer["documents_used"][0]["citations"]), 2)

    def test_narrow_yes_no_rule_uses_only_the_best_citation(self) -> None:
        query = "Apakah QRIS wajib digunakan untuk setiap pembayaran dengan QR Code di Indonesia?"
        exact = answer_item(
            block_id="qris-required",
            claim="QRIS wajib digunakan dalam setiap transaksi pembayaran yang difasilitasi dengan QR Code Pembayaran.",
            document="Implementasi QRIS",
            support_score=20.0,
        )
        adjacent = answer_item(
            block_id="qris-adjacent",
            claim="Penyelenggara wajib memastikan QR Code Pembayaran menggunakan standar QRIS.",
            document="Implementasi QRIS",
            support_score=10.0,
        )
        pack = {
            "query": query,
            "confidence": {"label": "strong", "score": 0.9, "must_say_not_found": False},
            "plan": {"issuers": ["BI"], "legal_constraints": {}},
            "documents": [{"issuer": "BI", "document": "Implementasi QRIS", "citations": [exact, adjacent]}],
        }

        answer = compose_template_answer(pack)

        self.assertEqual(answer["citation_count"], 1)
        self.assertEqual(answer["citations"][0]["block_id"], "qris-required")

    def test_permission_question_prefers_cited_exception_over_base_prohibition(self) -> None:
        query = "Bolehkah lembaga keuangan membagikan data pelanggan ke perusahaan lain?"
        prohibition = answer_item(
            block_id="base-prohibition",
            claim="Penyelenggara dilarang memberikan data Konsumen kepada pihak lain.",
            document="Pelindungan Konsumen BI",
            support_score=20.0,
        )
        exception = answer_item(
            block_id="consent-exception",
            claim="Larangan tidak berlaku jika Konsumen memberikan persetujuan secara tertulis kepada Penyelenggara.",
            document="Pelindungan Konsumen BI",
            support_score=18.0,
        )
        prohibition["answer_alignment"] = {"accepted": True}
        exception["answer_alignment"] = {"accepted": True}
        pack = {
            "query": query,
            "confidence": {"label": "partial", "score": 0.7, "must_say_not_found": False},
            "plan": {"issuers": ["BI"], "ambiguity": "institution_type", "legal_constraints": {}},
            "documents": [{"issuer": "BI", "document": "Pelindungan Konsumen BI", "citations": [prohibition, exception]}],
        }

        answer = compose_template_answer(pack)

        self.assertEqual(answer["status"], "partial")
        self.assertEqual(answer["citations"][0]["block_id"], "consent-exception")
        self.assertIn("jenis lembaga", " ".join(answer["limitations"]).casefold())

    def test_compound_question_keeps_the_two_requested_same_pasal_siblings(self) -> None:
        query = "Berapa lama perpanjangan penyelesaian pengaduan PUJK dan kapan konsumen harus diberi tahu?"
        rows = [
            answer_item(
                block_id="baseline",
                claim="PUJK wajib menyelesaikan pengaduan tertulis paling lama 20 hari kerja.",
                document="Layanan Pengaduan",
                pasal="Pasal 16",
                support_score=30.0,
            ),
            answer_item(
                block_id="extension",
                claim="PUJK dapat memperpanjang jangka waktu paling lama 20 hari kerja.",
                document="Layanan Pengaduan",
                pasal="Pasal 16",
                support_score=25.0,
            ),
            answer_item(
                block_id="notice",
                claim="Perpanjangan wajib diberitahukan secara tertulis kepada Konsumen sebelum jangka waktu berakhir.",
                document="Layanan Pengaduan",
                pasal="Pasal 16",
                support_score=24.0,
            ),
        ]
        for row, ayat in zip(rows, ("(1)", "(2)", "(4)"), strict=True):
            row["legal_path"] = {"pasal": "Pasal 16", "ayat": ayat}
            row["citation"]["ayat"] = ayat
            row["citation"]["text"] = f"Layanan Pengaduan, Pasal 16, ayat {ayat}"
            row["answer_alignment"] = {"accepted": True}
        pack = {
            "query": query,
            "confidence": {"label": "strong", "score": 0.9, "must_say_not_found": False},
            "plan": {"issuers": ["OJK"], "legal_constraints": {}},
            "documents": [{"issuer": "OJK", "document": "Layanan Pengaduan", "citations": rows}],
        }

        answer = compose_template_answer(pack)

        self.assertEqual({citation["block_id"] for citation in answer["citations"]}, {"extension", "notice"})

    def test_channel_question_prefers_operative_rule_over_explanation(self) -> None:
        query = "Melalui kanal apa Pelapor menyampaikan laporan debitur dan koreksi laporan debitur SLIK?"
        explanation = answer_item(
            block_id="explanation",
            claim=(
                '(1) Yang dimaksud dengan "menyampaikan Laporan Debitur secara daring" adalah '
                "mengirim rekaman data melalui jaringan yang terhubung dengan SLIK."
            ),
            document="Pelaporan SLIK",
            support_score=30.0,
        )
        direct = answer_item(
            block_id="direct-channel",
            claim="(1) Pelapor harus menyampaikan Laporan Debitur dan koreksi Laporan Debitur secara daring melalui SLIK.",
            document="Pelaporan SLIK",
            support_score=15.0,
        )
        for row in (explanation, direct):
            row["answer_alignment"] = {"accepted": True}
        pack = {
            "query": query,
            "confidence": {"label": "strong", "score": 0.9, "must_say_not_found": False},
            "plan": {"issuers": ["OJK"], "legal_constraints": {}},
            "documents": [{"issuer": "OJK", "document": "Pelaporan SLIK", "citations": [explanation, direct]}],
        }

        answer = compose_template_answer(pack)

        self.assertEqual(answer["citation_count"], 1)
        self.assertEqual(answer["citations"][0]["block_id"], "direct-channel")

    def test_location_question_prefers_direct_rule_pasal_over_reference_heavy_follow_on(self) -> None:
        query = "Di mana bank wajib menempatkan pusat data dan pusat pemulihan bencana, dan kapan boleh di luar Indonesia?"
        specs = [
            ("follow-on-obligation", "Pasal 36", "(3)", "Bank wajib memastikan data di luar Indonesia tidak digunakan selain sebagaimana dimaksud dalam Pasal 35.", 32.0),
            ("follow-on-permit", "Pasal 36", "(1)", "Bank dapat mengajukan permohonan izin penempatan Pusat Data di luar Indonesia sebagaimana dimaksud dalam Pasal 35.", 31.0),
            ("domestic-rule", "Pasal 35", "(1)", "Bank wajib menempatkan Pusat Data dan Pusat Pemulihan Bencana di wilayah Indonesia.", 25.0),
            ("overseas-rule", "Pasal 35", "(2)", "Bank dapat menempatkan Pusat Data di luar wilayah Indonesia sepanjang memperoleh izin OJK.", 24.0),
        ]
        rows = []
        for block_id, pasal, ayat, claim, score in specs:
            row = answer_item(block_id=block_id, claim=claim, document="Teknologi Informasi Bank", pasal=pasal, support_score=score)
            row["legal_path"] = {"pasal": pasal, "ayat": ayat}
            row["citation"]["ayat"] = ayat
            row["citation"]["text"] = f"Teknologi Informasi Bank, {pasal}, ayat {ayat}"
            row["answer_alignment"] = {"accepted": True}
            rows.append(row)
        pack = {
            "query": query,
            "confidence": {"label": "strong", "score": 0.9, "must_say_not_found": False},
            "plan": {"issuers": ["OJK"], "legal_constraints": {}},
            "documents": [{"issuer": "OJK", "document": "Teknologi Informasi Bank", "citations": rows}],
        }

        answer = compose_template_answer(pack)

        self.assertEqual({citation["block_id"] for citation in answer["citations"]}, {"domestic-rule", "overseas-rule"})

    def test_enumeration_aggregate_is_complete_and_human_readable(self) -> None:
        claim = evidence_claim_text(
            {
                "section_type": "enumeration_aggregate",
                "assembled_text": (
                    "Pasal 5 Fungsi sekretaris perusahaan melaksanakan tugas paling kurang: "
                    "huruf a mengikuti perkembangan Pasar Modal dan peraturan... peraturan terkait; "
                    "huruf b memberikan masukan kepada Direksi dan Dewan Komisaris untuk mematuhi perundang- undangan; "
                    "huruf c membantu pelaksanaan tata kelola perusahaan; "
                    "huruf d sebagai penghubung dengan pemegang saham, OJK, dan pemangku kepentingan lainnya."
                ),
            }
        )

        self.assertIn("\n  - a. mengikuti perkembangan", claim)
        self.assertIn("\n  - d. sebagai penghubung", claim)
        self.assertIn("tata kelola perusahaan", claim)
        self.assertIn("peraturan terkait", claim)
        self.assertIn("perundang-undangan", claim)
        self.assertNotIn("...", claim)


if __name__ == "__main__":
    unittest.main()
