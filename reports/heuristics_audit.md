# Heuristics Audit

This report lists behavior-affecting heuristic values loaded from `resources/config/`.
The current pass is behavior-preserving: values were externalized, not tuned.

## resources/config/answer_noise.json

- Description: Corpus-backed legal boilerplate classification for answer composition. Used first for audit, then for answer ranking.
- Calibrated: `False`

### `answer_noise.explicit_request_terms.legal_preamble`

- Value: `["dengan rahmat", "preambule", "pembukaan"]`
- Category: `manual_domain_policy`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `answer_noise.explicit_request_terms.consideration`

- Value: `["menimbang", "pertimbangan", "konsiderans", "latar belakang penerbitan"]`
- Category: `manual_domain_policy`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `answer_noise.explicit_request_terms.legal_basis_reference`

- Value: `["mengingat", "dasar hukum", "rujukan undang-undang", "landasan hukum"]`
- Category: `manual_domain_policy`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `answer_noise.explicit_request_terms.enactment`

- Value: `["memutuskan", "menetapkan", "amar putusan", "penetapan"]`
- Category: `manual_domain_policy`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `answer_noise.explicit_request_terms.promulgation`

- Value: `["lembaran negara", "tambahan lembaran negara", "diundangkan", "ditetapkan di", "tanggal berlaku"]`
- Category: `manual_domain_policy`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `answer_noise.explicit_request_terms.letter_intro`

- Value: `["sehubungan dengan amanat", "yth direksi", "surat edaran"]`
- Category: `manual_domain_policy`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `answer_noise.categories.legal_preamble.description`

- Value: `Opening title/regulator/preamble text, usually first-page material before operative rules.`
- Category: `corpus_noise_filter`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `answer_noise.categories.legal_preamble.patterns`

- Value: `["DENGAN\\s+RAHMAT\\s+TUHAN\\s+YANG\\s+MAHA\\s+ESA", "^(?:SALINAN\\s+)?PERATURAN\\s+(?:OTORITAS\\s+JASA\\s+KEUANGAN|BANK\\s+INDONESIA|ANGGOTA\\s+DEWAN\\s+GUBERNUR)(?:\\s+REPUBLIK\\s+INDONESIA)?\\s+NOMOR\\b", "^(?:SALINAN\\s+)?SURAT\\s+EDARAN\\s+(?:OTORITAS\\s+JASA\\s+KEUANGAN|BANK\\s+INDONESIA)(?:\\s+REPUBLIK\\s+INDONESIA)?\\s+NOMOR\\b", "^(?:SALINAN\\s+)?KEPUTUSAN\\s+(?:DEWAN\\s+KOMISIONER\\s+OTORITAS\\s+JASA\\s+KEUANGAN|GUBERNUR\\s+BANK\\s+INDONESIA|KETUA\\s+BAPEPAM|KETUA\\s+BADAN\\s+PENGAWAS\\s+PASAR\\s+MODAL)\\s+NOMOR\\b", "^(?:OTORITAS\\s+JASA\\s+KEUANGAN|BANK\\s+INDONESIA)\\s+REPUBLIK\\s+INDONESIA"]`
- Category: `corpus_noise_filter`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `answer_noise.categories.legal_preamble.answer_policy`

- Value: `reject_by_default`
- Category: `corpus_noise_filter`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `answer_noise.categories.consideration.description`

- Value: `Menimbang/konsiderans material that explains reasons but usually does not state operative obligations.`
- Category: `corpus_noise_filter`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `answer_noise.categories.consideration.patterns`

- Value: `["\\bMenimbang\\s*:", "\\bkonsiderans\\b"]`
- Category: `corpus_noise_filter`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `answer_noise.categories.consideration.answer_policy`

- Value: `reject_by_default`
- Category: `corpus_noise_filter`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `answer_noise.categories.legal_basis_reference.description`

- Value: `Mengingat/statutory reference lists that cite enabling laws rather than the answer itself.`
- Category: `corpus_noise_filter`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `answer_noise.categories.legal_basis_reference.patterns`

- Value: `["\\bMengingat\\s*:"]`
- Category: `corpus_noise_filter`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `answer_noise.categories.legal_basis_reference.answer_policy`

- Value: `reject_by_default`
- Category: `corpus_noise_filter`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `answer_noise.categories.enactment.description`

- Value: `MEMUTUSKAN/Menetapkan enactment bridge text before substantive articles.`
- Category: `corpus_noise_filter`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `answer_noise.categories.enactment.patterns`

- Value: `["\\bMEMUTUSKAN\\s*:", "\\bMenetapkan\\s*:"]`
- Category: `corpus_noise_filter`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `answer_noise.categories.enactment.answer_policy`

- Value: `reject_by_default`
- Category: `corpus_noise_filter`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `answer_noise.categories.promulgation.description`

- Value: `Promulgation/signature/state-gazette material usually found near closing pages.`
- Category: `corpus_noise_filter`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `answer_noise.categories.promulgation.patterns`

- Value: `["Lembaran\\s+Negara", "Tambahan\\s+Lembaran\\s+Negara", "\\bDiundangkan\\s+di\\b", "\\bDitetapkan\\s+di\\b", "\\bMENTERI\\s+HUKUM\\s+DAN\\s+HAK\\s+ASASI\\s+MANUSIA\\b"]`
- Category: `corpus_noise_filter`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `answer_noise.categories.promulgation.answer_policy`

- Value: `reject_by_default`
- Category: `corpus_noise_filter`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `answer_noise.categories.letter_intro.description`

- Value: `OJK/BI circular-letter introductory material before concrete provisions.`
- Category: `corpus_noise_filter`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `answer_noise.categories.letter_intro.patterns`

- Value: `["Sehubungan\\s+dengan\\s+amanat", "\\bYth\\.?\\s+(?:Direksi|Pengurus|Dewan\\s+Komisioner)", "\\bdi\\s+tempat\\b.*\\bSALINAN\\s+SURAT\\s+EDARAN\\b"]`
- Category: `corpus_noise_filter`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `answer_noise.categories.letter_intro.answer_policy`

- Value: `reject_by_default`
- Category: `corpus_noise_filter`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `answer_noise.categories.substantive.description`

- Value: `Default category when no boilerplate category matches.`
- Category: `corpus_noise_filter`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `answer_noise.categories.substantive.patterns`

- Value: `[]`
- Category: `corpus_noise_filter`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `answer_noise.categories.substantive.answer_policy`

- Value: `allow`
- Category: `corpus_noise_filter`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `answer_noise.ranking.default_reject_penalty`

- Value: `-100.0`
- Category: `corpus_noise_filter`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `answer_noise.ranking.category_penalty.legal_preamble`

- Value: `-120.0`
- Category: `corpus_noise_filter`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `answer_noise.ranking.category_penalty.consideration`

- Value: `-100.0`
- Category: `corpus_noise_filter`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `answer_noise.ranking.category_penalty.legal_basis_reference`

- Value: `-90.0`
- Category: `corpus_noise_filter`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `answer_noise.ranking.category_penalty.enactment`

- Value: `-100.0`
- Category: `corpus_noise_filter`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `answer_noise.ranking.category_penalty.promulgation`

- Value: `-120.0`
- Category: `corpus_noise_filter`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `answer_noise.ranking.category_penalty.letter_intro`

- Value: `-90.0`
- Category: `corpus_noise_filter`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `answer_noise.ranking.category_penalty.substantive`

- Value: `0.0`
- Category: `corpus_noise_filter`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `answer_noise.audit.max_examples_per_category`

- Value: `8`
- Category: `corpus_noise_filter`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `answer_noise.audit.example_chars`

- Value: `360`
- Category: `corpus_noise_filter`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

## resources/config/answer_ranking.json

- Description: Behavior-preserving answer composer heuristics. Values are manual and not calibrated yet.
- Calibrated: `False`

### `answer_ranking.claim_text.max_chars`

- Value: `420`
- Category: `corpus_noise_filter`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `answer_ranking.claim_text.min_boundary_chars`

- Value: `180`
- Category: `corpus_noise_filter`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `answer_ranking.claim_text.fallback_claim`

- Value: `Ketentuan relevan ditemukan pada sumber yang dikutip.`
- Category: `corpus_noise_filter`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `answer_ranking.claim_text.strip_regexes`

- Value: `["^\\.\\.\\.", "\\.\\.\\.$", "!\\[[^\\]]*\\]\\([^)]+\\)", "\\|[-:\\s|]+\\|", "^#+\\s*"]`
- Category: `corpus_noise_filter`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `answer_ranking.claim_text.table_pipe_replacement`

- Value: `; `
- Category: `corpus_noise_filter`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `answer_ranking.usable_claim.reject_lowercase_start`

- Value: `False`
- Category: `corpus_noise_filter`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `answer_ranking.usable_claim.reject_prefixes`

- Value: `["peraturan otoritas", "peraturan bank indonesia", "dengan rahmat", "menimbang", "penjelasan atas"]`
- Category: `corpus_noise_filter`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `answer_ranking.usable_claim.reject_fragments`

- Value: `["lembaran negara", "tambahan lembaran negara", "sehubungan dengan amanat"]`
- Category: `corpus_noise_filter`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `answer_ranking.usable_claim.all_caps_regex`

- Value: `^[A-Z\s/.\-0-9()]{40,}$`
- Category: `corpus_noise_filter`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `answer_ranking.usable_claim.reject_section_types`

- Value: `["table"]`
- Category: `corpus_noise_filter`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `answer_ranking.usable_claim.reject_extraction_flags`

- Value: `["markdown_table_artifact", "image_placeholder", "form_placeholder_text", "very_short_text"]`
- Category: `corpus_noise_filter`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `answer_ranking.usable_claim.section_type_query_allow_terms.table`

- Value: `["tabel", "table", "matriks", "lampiran", "formulir", "format", "template", "kolom", "xlsx", "excel"]`
- Category: `corpus_noise_filter`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `answer_ranking.usable_claim.extraction_flag_query_allow_terms.markdown_table_artifact`

- Value: `["tabel", "table", "matriks", "lampiran", "formulir", "format", "template", "kolom", "xlsx", "excel"]`
- Category: `corpus_noise_filter`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `answer_ranking.usable_claim.extraction_flag_query_allow_terms.form_placeholder_text`

- Value: `["formulir", "format", "template", "lampiran"]`
- Category: `corpus_noise_filter`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `answer_ranking.usable_claim.min_chars`

- Value: `30`
- Category: `corpus_noise_filter`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `answer_ranking.item_rank.query_overlap_weight`

- Value: `12.0`
- Category: `manual_domain_policy`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `answer_ranking.item_rank.matched_exact_phrase_bonus`

- Value: `8.0`
- Category: `manual_domain_policy`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `answer_ranking.item_rank.sanction_terms`

- Value: `["sanksi", "denda", "terlambat", "pelanggaran"]`
- Category: `manual_domain_policy`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `answer_ranking.item_rank.sanction_match_bonus`

- Value: `10.0`
- Category: `manual_domain_policy`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `answer_ranking.item_rank.section_type_bonus.ayat`

- Value: `4.0`
- Category: `manual_domain_policy`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `answer_ranking.item_rank.section_type_bonus.pasal`

- Value: `4.0`
- Category: `manual_domain_policy`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `answer_ranking.item_rank.citation_quality_bonus.document_page_pasal_ayat`

- Value: `3.0`
- Category: `manual_domain_policy`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `answer_ranking.item_rank.section_type_penalty.table`

- Value: `-6.0`
- Category: `manual_domain_policy`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `answer_ranking.item_rank.claim_prefix_penalty.peraturan otoritas`

- Value: `-10.0`
- Category: `manual_domain_policy`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `answer_ranking.item_rank.claim_prefix_penalty.peraturan bank indonesia`

- Value: `-10.0`
- Category: `manual_domain_policy`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `answer_ranking.item_rank.claim_prefix_penalty.dengan rahmat`

- Value: `-10.0`
- Category: `manual_domain_policy`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `answer_ranking.item_rank.claim_prefix_penalty.menimbang`

- Value: `-10.0`
- Category: `manual_domain_policy`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

## resources/config/cross_regulator_confidence.json

- Description: Strict direct-topic coverage gate for cross-regulator regulation/comparison questions.
- Calibrated: `False`

### `cross_regulator_confidence.coverage.enabled`

- Value: `True`
- Category: `manual_domain_policy`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `cross_regulator_confidence.coverage.min_issuers`

- Value: `2`
- Category: `manual_domain_policy`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `cross_regulator_confidence.coverage.comparison_intents`

- Value: `["compare_regulations", "find_regulations"]`
- Category: `manual_domain_policy`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `cross_regulator_confidence.coverage.direct_title_required_for_comparison`

- Value: `True`
- Category: `manual_domain_policy`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `cross_regulator_confidence.coverage.definition_section_types`

- Value: `["pasal", "ayat"]`
- Category: `manual_domain_policy`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `cross_regulator_confidence.coverage.definition_markers`

- Value: `["yang dimaksud dengan", "dalam peraturan ini yang dimaksud", "adalah"]`
- Category: `manual_domain_policy`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `cross_regulator_confidence.coverage.adjacent_only_label`

- Value: `adjacent_only`
- Category: `manual_domain_policy`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `cross_regulator_confidence.coverage.direct_label`

- Value: `direct`
- Category: `manual_domain_policy`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `cross_regulator_confidence.coverage.missing_label`

- Value: `missing`
- Category: `manual_domain_policy`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `cross_regulator_confidence.coverage.downgrade_label`

- Value: `partial`
- Category: `manual_domain_policy`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `cross_regulator_confidence.coverage.downgrade_reason`

- Value: `cross_regulator_missing_direct_topic_coverage`
- Category: `manual_domain_policy`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `cross_regulator_confidence.coverage.generic_adjacent_terms`

- Value: `["perizinan", "pelaporan", "pembayaran", "jasa keuangan", "aset keuangan digital", "aset kripto", "sistem pembayaran", "otoritas berwenang"]`
- Category: `manual_domain_policy`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `cross_regulator_confidence.audit.queries`

- Value: `["komparasi peraturan OJK dan BI terkait penyedia jasa pembayaran", "berikan aku aturan terkait penyedia jasa pembayaran dari BI dan OJK", "bandingkan aturan sistem pembayaran menurut BI dan OJK", "apa saja aturan APU PPT dari BI dan OJK yang perlu dipetakan?", "bandingkan ketentuan perlindungan konsumen dari BI dan OJK untuk jasa keuangan"]`
- Category: `manual_domain_policy`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

## resources/config/evaluation_rubrics.json

- Description: Behavior-preserving development evaluation rubrics. These are smoke/regression rubrics, not real-world accuracy claims.
- Calibrated: `False`

### `evaluation_rubrics.retrieval.top_title_count`

- Value: `5`
- Category: `evaluation_rubric`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `evaluation_rubrics.retrieval.top_issuer_count`

- Value: `8`
- Category: `evaluation_rubric`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `evaluation_rubrics.retrieval.top_citation_count`

- Value: `5`
- Category: `evaluation_rubric`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `evaluation_rubrics.retrieval.weights.title_score`

- Value: `0.45`
- Category: `evaluation_rubric`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `evaluation_rubrics.retrieval.weights.issuer_score`

- Value: `0.3`
- Category: `evaluation_rubric`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `evaluation_rubrics.retrieval.weights.page_citation_rate`

- Value: `0.15`
- Category: `evaluation_rubric`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `evaluation_rubrics.retrieval.weights.primary_rate`

- Value: `0.1`
- Category: `evaluation_rubric`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `evaluation_rubrics.retrieval.accepted_threshold`

- Value: `0.82`
- Category: `evaluation_rubric`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `evaluation_rubrics.evidence.top_document_count`

- Value: `8`
- Category: `evaluation_rubric`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `evaluation_rubrics.evidence.top_citation_count`

- Value: `5`
- Category: `evaluation_rubric`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `evaluation_rubrics.evidence.confidence_score.strong`

- Value: `1.0`
- Category: `evaluation_rubric`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `evaluation_rubrics.evidence.confidence_score.partial`

- Value: `0.75`
- Category: `evaluation_rubric`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `evaluation_rubrics.evidence.confidence_score.weak`

- Value: `0.0`
- Category: `evaluation_rubric`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `evaluation_rubrics.evidence.confidence_score.not_found`

- Value: `0.0`
- Category: `evaluation_rubric`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `evaluation_rubrics.evidence.weights.document_score`

- Value: `0.4`
- Category: `evaluation_rubric`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `evaluation_rubrics.evidence.weights.issuer_score`

- Value: `0.25`
- Category: `evaluation_rubric`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `evaluation_rubrics.evidence.weights.confidence_score`

- Value: `0.2`
- Category: `evaluation_rubric`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `evaluation_rubrics.evidence.weights.citation_score`

- Value: `0.15`
- Category: `evaluation_rubric`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `evaluation_rubrics.evidence.answerable_threshold`

- Value: `0.82`
- Category: `evaluation_rubric`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `evaluation_rubrics.evidence.partial_threshold`

- Value: `0.72`
- Category: `evaluation_rubric`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `evaluation_rubrics.answer.top_document_count`

- Value: `8`
- Category: `evaluation_rubric`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `evaluation_rubrics.answer.top_report_documents`

- Value: `5`
- Category: `evaluation_rubric`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `evaluation_rubrics.answer.status_score.answerable`

- Value: `1.0`
- Category: `evaluation_rubric`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `evaluation_rubrics.answer.status_score.partial`

- Value: `0.75`
- Category: `evaluation_rubric`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `evaluation_rubrics.answer.status_score.not_found`

- Value: `0.0`
- Category: `evaluation_rubric`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `evaluation_rubrics.answer.confidence_score.strong`

- Value: `1.0`
- Category: `evaluation_rubric`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `evaluation_rubrics.answer.confidence_score.partial`

- Value: `0.75`
- Category: `evaluation_rubric`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `evaluation_rubrics.answer.confidence_score.weak`

- Value: `0.0`
- Category: `evaluation_rubric`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `evaluation_rubrics.answer.confidence_score.not_found`

- Value: `0.0`
- Category: `evaluation_rubric`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `evaluation_rubrics.answer.weights.document_score`

- Value: `0.3`
- Category: `evaluation_rubric`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `evaluation_rubrics.answer.weights.issuer_score`

- Value: `0.25`
- Category: `evaluation_rubric`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `evaluation_rubrics.answer.weights.citation_score`

- Value: `0.2`
- Category: `evaluation_rubric`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `evaluation_rubrics.answer.weights.status_score`

- Value: `0.15`
- Category: `evaluation_rubric`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `evaluation_rubrics.answer.weights.confidence_score`

- Value: `0.1`
- Category: `evaluation_rubric`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `evaluation_rubrics.answer.answerable_threshold`

- Value: `0.82`
- Category: `evaluation_rubric`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `evaluation_rubrics.answer.partial_threshold`

- Value: `0.72`
- Category: `evaluation_rubric`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `evaluation_rubrics.answer_quality.default_min_citations`

- Value: `1`
- Category: `evaluation_rubric`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `evaluation_rubrics.answer_quality.not_found_min_citations`

- Value: `0`
- Category: `evaluation_rubric`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `evaluation_rubrics.answer_quality.default_max_answer_chars`

- Value: `5000`
- Category: `evaluation_rubric`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `evaluation_rubrics.answer_quality.primary_sources_first_threshold`

- Value: `0.75`
- Category: `evaluation_rubric`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `evaluation_rubrics.answer_quality.accepted_threshold`

- Value: `0.86`
- Category: `evaluation_rubric`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `evaluation_rubrics.answer_quality.noisy_answer_patterns`

- Value: `["!\\[[^\\]]*\\]\\([^)]+\\)", "\\|---", "DENGAN RAHMAT TUHAN YANG MAHA ESA", "\\bMenimbang\\s*:", "Cuplikan lanjutan dari evidence", "Lembaran Negara", "Tambahan Lembaran Negara", "Sehubungan dengan amanat"]`
- Category: `corpus_noise_filter`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `evaluation_rubrics.answer_quality.weights.status_matches_expected`

- Value: `0.18`
- Category: `evaluation_rubric`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `evaluation_rubrics.answer_quality.weights.not_found_has_no_citations`

- Value: `0.1`
- Category: `evaluation_rubric`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `evaluation_rubrics.answer_quality.weights.has_required_terms`

- Value: `0.14`
- Category: `evaluation_rubric`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `evaluation_rubrics.answer_quality.weights.has_uncertainty_terms`

- Value: `0.08`
- Category: `evaluation_rubric`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `evaluation_rubrics.answer_quality.weights.has_required_citation_terms`

- Value: `0.1`
- Category: `evaluation_rubric`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `evaluation_rubrics.answer_quality.weights.has_min_citations`

- Value: `0.1`
- Category: `evaluation_rubric`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `evaluation_rubrics.answer_quality.weights.source_lines_match_citation_count`

- Value: `0.08`
- Category: `evaluation_rubric`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `evaluation_rubrics.answer_quality.weights.has_required_issuers`

- Value: `0.08`
- Category: `evaluation_rubric`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `evaluation_rubrics.answer_quality.weights.primary_sources_first_enough`

- Value: `0.06`
- Category: `evaluation_rubric`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `evaluation_rubrics.answer_quality.weights.not_too_long`

- Value: `0.04`
- Category: `evaluation_rubric`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `evaluation_rubrics.answer_quality.weights.no_noisy_fragments`

- Value: `0.03`
- Category: `evaluation_rubric`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `evaluation_rubrics.answer_quality.weights.no_truncated_bullets`

- Value: `0.02`
- Category: `evaluation_rubric`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `evaluation_rubrics.answer_quality.weights.partial_has_uncertainty`

- Value: `0.01`
- Category: `evaluation_rubric`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `evaluation_rubrics.answer_quality.hard_checks`

- Value: `["status_matches_expected", "not_found_has_no_citations", "has_required_terms", "has_uncertainty_terms", "has_required_citation_terms", "has_min_citations", "source_lines_match_citation_count", "has_required_issuers", "not_too_long", "no_noisy_fragments", "no_truncated_bullets", "partial_has_uncertainty"]`
- Category: `evaluation_rubric`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

## resources/config/evidence_confidence.json

- Description: Behavior-preserving evidence confidence heuristics. Values are manual and not calibrated yet.
- Calibrated: `False`

### `evidence_confidence.item_support.title_overlap_weight`

- Value: `0.16`
- Category: `evaluation_rubric`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `evidence_confidence.item_support.snippet_overlap_weight`

- Value: `0.1`
- Category: `evaluation_rubric`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `evidence_confidence.item_support.matched_exact_phrase_weight`

- Value: `0.2`
- Category: `evaluation_rubric`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `evidence_confidence.item_support.max_lexical_support`

- Value: `1.0`
- Category: `evaluation_rubric`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `evidence_confidence.item_support.support_score_base_multiplier`

- Value: `0.75`
- Category: `evaluation_rubric`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `evidence_confidence.item_support.snippet_overlap_chars`

- Value: `1000`
- Category: `evaluation_rubric`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `evidence_confidence.item_support.exact_phrase_score_multiplier_per_phrase`

- Value: `0.15`
- Category: `evaluation_rubric`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `evidence_confidence.item_support.extraction_quality_multipliers.markdown_table_artifact`

- Value: `0.62`
- Category: `evaluation_rubric`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `evidence_confidence.item_support.extraction_quality_multipliers.image_placeholder`

- Value: `0.72`
- Category: `evaluation_rubric`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `evidence_confidence.item_support.extraction_quality_multipliers.form_placeholder_text`

- Value: `0.72`
- Category: `evaluation_rubric`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `evidence_confidence.item_support.extraction_quality_multipliers.very_short_text`

- Value: `0.7`
- Category: `evaluation_rubric`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `evidence_confidence.item_support.query_allows_table_terms`

- Value: `["tabel", "table", "matriks", "lampiran", "formulir", "format", "template", "kolom", "xlsx", "excel"]`
- Category: `evaluation_rubric`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `evidence_confidence.confidence_score.top_items`

- Value: `5`
- Category: `evaluation_rubric`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `evidence_confidence.confidence_score.weights.primary_rate`

- Value: `0.25`
- Category: `evaluation_rubric`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `evidence_confidence.confidence_score.weights.page_rate`

- Value: `0.2`
- Category: `evaluation_rubric`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `evidence_confidence.confidence_score.weights.article_rate`

- Value: `0.15`
- Category: `evaluation_rubric`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `evidence_confidence.confidence_score.weights.matched_phrase_rate`

- Value: `0.15`
- Category: `evaluation_rubric`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `evidence_confidence.confidence_score.weights.lexical_rate`

- Value: `0.15`
- Category: `evaluation_rubric`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `evidence_confidence.confidence_score.weights.query_coverage`

- Value: `0.1`
- Category: `evaluation_rubric`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `evidence_confidence.confidence_score.weights.expected_issuer_rate`

- Value: `0.05`
- Category: `evaluation_rubric`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `evidence_confidence.confidence_score.matched_phrase_normalizer`

- Value: `2`
- Category: `evaluation_rubric`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `evidence_confidence.confidence_score.strong_threshold`

- Value: `0.78`
- Category: `evaluation_rubric`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `evidence_confidence.confidence_score.partial_threshold`

- Value: `0.55`
- Category: `evaluation_rubric`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `evidence_confidence.confidence_score.generic_entities`

- Value: `["bank"]`
- Category: `evaluation_rubric`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `evidence_confidence.confidence_score.generic_query_coverage_threshold`

- Value: `0.75`
- Category: `evaluation_rubric`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `evidence_confidence.confidence_score.generic_lexical_rate_threshold`

- Value: `0.55`
- Category: `evaluation_rubric`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `evidence_confidence.confidence_score.low_coverage_query_threshold`

- Value: `0.65`
- Category: `evaluation_rubric`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `evidence_confidence.confidence_score.low_coverage_lexical_threshold`

- Value: `0.5`
- Category: `evaluation_rubric`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `evidence_confidence.confidence_score.partial_recovery_score_threshold`

- Value: `0.7`
- Category: `evaluation_rubric`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

## resources/config/extraction_heuristics.json

- Description: Behavior-preserving extraction heuristics. Values are manual and not calibrated yet.
- Calibrated: `False`

### `extraction_heuristics.liteparse.ocr_enabled`

- Value: `False`
- Category: `parser_heuristic`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `extraction_heuristics.liteparse.output_format`

- Value: `markdown`
- Category: `parser_heuristic`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `extraction_heuristics.liteparse.quiet`

- Value: `True`
- Category: `parser_heuristic`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `extraction_heuristics.liteparse.image_mode`

- Value: `off`
- Category: `parser_heuristic`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `extraction_heuristics.liteparse.extract_links`

- Value: `True`
- Category: `parser_heuristic`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `extraction_heuristics.liteparse.emit_word_boxes`

- Value: `True`
- Category: `parser_heuristic`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `extraction_heuristics.liteparse.preserve_very_small_text`

- Value: `False`
- Category: `parser_heuristic`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `extraction_heuristics.liteparse.dpi`

- Value: `150`
- Category: `parser_heuristic`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `extraction_heuristics.liteparse.num_workers`

- Value: `4`
- Category: `parser_heuristic`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `extraction_heuristics.sentence_blocks.flush_on_blank_min_chars`

- Value: `350`
- Category: `parser_heuristic`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `extraction_heuristics.sentence_blocks.hard_flush_min_chars`

- Value: `1200`
- Category: `parser_heuristic`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `extraction_heuristics.sentence_blocks.soft_flush_min_chars`

- Value: `550`
- Category: `parser_heuristic`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `extraction_heuristics.sentence_blocks.min_block_chars`

- Value: `8`
- Category: `parser_heuristic`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `extraction_heuristics.sentence_blocks.page_number_regex`

- Value: `-?\s*\d+\s*-?`
- Category: `parser_heuristic`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `extraction_heuristics.sentence_blocks.sentence_end_regex`

- Value: `[.;:]$`
- Category: `parser_heuristic`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `extraction_heuristics.sentence_blocks.table_separator_regex`

- Value: `^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?\s*$`
- Category: `parser_heuristic`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `extraction_heuristics.sentence_blocks.table_row_min_pipes`

- Value: `2`
- Category: `parser_heuristic`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `extraction_heuristics.sentence_blocks.preserve_table_rows`

- Value: `True`
- Category: `parser_heuristic`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `extraction_heuristics.sentence_blocks.list_item_starts_new_block`

- Value: `True`
- Category: `parser_heuristic`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `extraction_heuristics.sentence_blocks.table_context_prefix_max_chars`

- Value: `180`
- Category: `parser_heuristic`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `extraction_heuristics.headings.heading_regexes`

- Value: `["^#+\\s+\\S+", "^(BAB|BAGIAN|PARAGRAF)\\s+[IVXLCDM0-9]+\\\\b", "^(PASAL)\\s+\\d+[A-Z]?\\\\b", "^[IVXLCDM]+\\.\\s+\\S+", "^[A-Z]\\.\\s+[A-Z][A-Z\\s]{6,}$"]`
- Category: `parser_heuristic`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `extraction_heuristics.headings.pasal_heading_regex`

- Value: `^Pasal\s+\d+[A-Z]?\b`
- Category: `parser_heuristic`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `extraction_heuristics.headings.bab_heading_regex`

- Value: `^BAB\b`
- Category: `parser_heuristic`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `extraction_heuristics.headings.max_heading_path_items`

- Value: `4`
- Category: `parser_heuristic`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `extraction_heuristics.headings.heading_text_max_chars`

- Value: `120`
- Category: `parser_heuristic`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `extraction_heuristics.citations.pasal_regex`

- Value: `\bPasal\s+(\d+[A-Z]?)\b`
- Category: `parser_heuristic`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `extraction_heuristics.citations.ayat_regex`

- Value: `(^|\s)\((\d+[a-z]?)\)`
- Category: `parser_heuristic`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `extraction_heuristics.block_type.article_regex`

- Value: `\bpasal\s+\d+[a-z]?\b`
- Category: `parser_heuristic`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `extraction_heuristics.block_type.faq_question_scan_chars`

- Value: `180`
- Category: `parser_heuristic`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `extraction_heuristics.block_type.table_pipe_min_count`

- Value: `4`
- Category: `parser_heuristic`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `extraction_heuristics.block_type.list_item_regex`

- Value: `^(\(?\d+[a-z]?\)|[a-z]\.|[ivxlcdm]+\.)\s+`
- Category: `parser_heuristic`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `extraction_heuristics.raw_output.slug_max_chars`

- Value: `160`
- Category: `parser_heuristic`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `extraction_heuristics.ocr_status.empty_page_text_chars`

- Value: `20`
- Category: `parser_heuristic`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `extraction_heuristics.ocr_status.total_text_min_chars`

- Value: `100`
- Category: `parser_heuristic`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `extraction_heuristics.ocr_status.empty_page_ratio_threshold`

- Value: `0.7`
- Category: `parser_heuristic`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `extraction_heuristics.block_id.slug_max_chars`

- Value: `180`
- Category: `parser_heuristic`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

## resources/config/extraction_spot_check.json

- Description: High-value documents and queries for extraction/citation spot checks.
- Calibrated: `False`

### `extraction_spot_check.targets`

- Value: `[{"name": "BI PJP", "issuer": "BI", "title_patterns": ["Penyedia Jasa Pembayaran", "PBI No.23/6/PBI/2021"], "query": "peraturan BI tentang penyedia jasa pembayaran apa saja?"}, {"name": "BI PIP", "issuer": "BI", "title_patterns": ["Penyelenggara Infrastruktur Sistem Pembayaran", "PBI No.23/7/PBI/2021"], "query": "aturan BI tentang penyelenggara infrastruktur sistem pembayaran"}, {"name": "BI Sistem Pembayaran", "issuer": "BI", "title_patterns": ["Sistem Pembayaran"], "query": "aturan sistem pembayaran Bank Indonesia"}, {"name": "OJK APU PPT", "issuer": "OJK", "title_patterns": ["Anti Pencucian Uang", "Pencegahan Pendanaan Terorisme"], "query": "aturan OJK tentang APU PPT untuk bank"}, {"name": "OJK Consumer Protection", "issuer": "OJK", "title_patterns": ["Pelindungan Konsumen", "Perlindungan Konsumen", "Pengaduan Konsumen"], "query": "aturan OJK tentang pelindungan konsumen jasa keuangan"}, {"name": "OJK SLIK", "issuer": "OJK", "title_patterns": ["Sistem Layanan Informasi Keuangan", "SLIK", "Informasi Debitur"], "query": "apa kewajiban bank terkait pelaporan SLIK?"}, {"name": "OJK BPR BPRS", "issuer": "OJK", "title_patterns": ["Bank Perekonomian Rakyat", "Bank Perkreditan Rakyat", "BPR", "BPRS"], "query": "aturan OJK untuk BPR dan BPRS"}, {"name": "OJK Modal Ventura", "issuer": "OJK", "title_patterns": ["Modal Ventura"], "query": "aturan penyelenggaraan usaha perusahaan modal ventura"}, {"name": "OJK Perusahaan Pembiayaan", "issuer": "OJK", "title_patterns": ["Perusahaan Pembiayaan"], "query": "aturan OJK tentang perusahaan pembiayaan"}, {"name": "OJK Aset Keuangan Digital", "issuer": "OJK", "title_patterns": ["Aset Keuangan Digital", "Aset Kripto"], "query": "aturan OJK tentang perdagangan aset keuangan digital termasuk aset kripto"}]`
- Category: `evaluation_rubric`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `extraction_spot_check.thresholds.min_page_rate`

- Value: `0.98`
- Category: `evaluation_rubric`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `extraction_spot_check.thresholds.max_table_rate`

- Value: `0.45`
- Category: `evaluation_rubric`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `extraction_spot_check.thresholds.max_document_page_only_rate`

- Value: `0.35`
- Category: `evaluation_rubric`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `extraction_spot_check.thresholds.min_article_or_ayat_rate`

- Value: `0.35`
- Category: `evaluation_rubric`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `extraction_spot_check.audit.max_documents_per_target`

- Value: `5`
- Category: `evaluation_rubric`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `extraction_spot_check.audit.max_examples_per_target`

- Value: `6`
- Category: `evaluation_rubric`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `extraction_spot_check.audit.max_evidence_citations`

- Value: `4`
- Category: `evaluation_rubric`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

## resources/config/lexicon_extraction.json

- Description: Behavior-preserving lexicon candidate extraction filters, seed hints, patterns, and weights. Values are manual/corpus-noise heuristics and not calibrated yet.
- Calibrated: `False`

### `lexicon_extraction.generic_terms`

- Value: `["peraturan", "ketentuan", "peraturan perundang-undangan", "otoritas jasa keuangan", "bank indonesia", "cukup jelas", "sebagaimana dimaksud", "pasal", "ayat", "huruf", "nomor", "tahun"]` ... (24 items)
- Category: `corpus_noise_filter`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `lexicon_extraction.generic_fragments`

- Value: `["i umum", "cukup jelas", "yang dimaksud", "sebagaimana dimaksud", "dalam rangka", "mewujudkan tujuan", "mencapai stabilitas", "pemerintah republik indonesia telah menerbitkan", "lembaran negara", "tambahan lembaran negara", "pengembangan dan pengua", "yang selanjutnya disebut"]`
- Category: `corpus_noise_filter`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `lexicon_extraction.invalid_exact_terms`

- Value: `["pojk", "seojk", "pbi", "padg", "padk", "sebi", "undang", "surat edaran ojk", "surat edaran bank indonesia"]`
- Category: `manual_domain_seed`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `lexicon_extraction.invalid_markers`

- Value: `["|", "---", "#", "!", "[](", "*)", "**"]`
- Category: `manual_domain_seed`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `lexicon_extraction.topic_hints`

- Value: `["perizinan", "pelaporan", "laporan", "tata kelola", "manajemen risiko", "penyelenggaraan", "pelindungan", "perlindungan", "keterbukaan", "transparansi", "pemasaran", "promosi"]` ... (22 items)
- Category: `manual_domain_seed`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `lexicon_extraction.entity_hints`

- Value: `["bank", "bpr", "bprs", "perusahaan", "lembaga", "penyedia", "penyelenggara", "emiten", "reksa dana", "sukuk", "dana pensiun", "pergadaian"]` ... (20 items)
- Category: `manual_domain_seed`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `lexicon_extraction.title_phrase_patterns`

- Value: `["bank (?:umum(?: syariah)?|perekonomian rakyat(?: syariah)?|perkreditan rakyat|pembiayaan rakyat syariah|kustodian)", "perusahaan (?:asuransi|reasuransi|pembiayaan|modal ventura|pergadaian|efek|publik|penjaminan)(?: syariah)?", "lembaga (?:jasa keuangan|keuangan mikro|pembiayaan|penjamin(?:an)?|pendukung pasar uang|pengelola informasi perkreditan)", "dana pensiun(?: syariah)?", "pasar (?:modal|uang(?: dan pasar valuta asing)?)", "penyedia jasa pembayaran", "penyelenggara infrastruktur sistem pembayaran", "sistem pembayaran", "transfer dana", "uang elektronik", "gerbang pembayaran nasional", "quick response code indonesia standard"]` ... (26 items)
- Category: `manual_domain_seed`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `lexicon_extraction.validation.min_phrase_chars`

- Value: `3`
- Category: `manual_domain_seed`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `lexicon_extraction.validation.max_phrase_chars`

- Value: `160`
- Category: `manual_domain_seed`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `lexicon_extraction.validation.max_tokens`

- Value: `10`
- Category: `manual_domain_seed`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `lexicon_extraction.validation.single_token_min_chars`

- Value: `4`
- Category: `manual_domain_seed`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `lexicon_extraction.validation.single_token_alias_regex`

- Value: `[a-z]{2,6}`
- Category: `manual_domain_seed`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `lexicon_extraction.validation.alias_regex`

- Value: `[A-Z0-9-]{2,12}`
- Category: `manual_domain_seed`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `lexicon_extraction.validation.numeric_only_regex`

- Value: `[\d./\-\s]+`
- Category: `manual_domain_seed`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `lexicon_extraction.extraction.heading_max_tokens`

- Value: `7`
- Category: `manual_domain_seed`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `lexicon_extraction.extraction.alias_trigger_regex`

- Value: `disingkat|disebut|\([A-Z0-9][A-Z0-9./-]{1,20}\)`
- Category: `manual_domain_seed`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `lexicon_extraction.extraction.alias_sentence_max_chars`

- Value: `400`
- Category: `manual_domain_seed`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `lexicon_extraction.extraction.definition_scan_chars`

- Value: `2500`
- Category: `manual_domain_seed`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `lexicon_extraction.extraction.definition_detection_chars`

- Value: `1200`
- Category: `manual_domain_seed`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `lexicon_extraction.extraction.alias_scan_pages`

- Value: `[1, 2, 3]`
- Category: `manual_domain_seed`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `lexicon_extraction.extraction.definition_regex`

- Value: `(?:^|\s)(?:\d+\.\s*)?(?P<term>[A-ZÁÉÍÓÚÄËÏÖÜa-z0-9][^.;:\n]{3,120}?)\s+adalah\s+`
- Category: `manual_domain_seed`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `lexicon_extraction.extraction.alias_patterns`

- Value: `["(?P<long>[A-ZÁÉÍÓÚÄËÏÖÜa-z0-9][^.;:\\n]{4,120})\\s+yang\\s+selanjutnya\\s+disingkat\\s+(?P<alias>[A-Z0-9][A-Z0-9./-]{1,20})", "(?P<long>[A-ZÁÉÍÓÚÄËÏÖÜa-z0-9][^.;:\\n]{4,120})\\s+yang\\s+selanjutnya\\s+disebut\\s+(?P<alias>[A-Z][A-Za-z0-9./-]{1,40})", "(?P<long>[A-ZÁÉÍÓÚÄËÏÖÜa-z0-9][^.;:\\n]{4,100})\\s*\\((?P<alias>[A-Z0-9][A-Z0-9./-]{1,20})\\)"]`
- Category: `manual_domain_seed`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `lexicon_extraction.weights.title`

- Value: `8.0`
- Category: `manual_domain_seed`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `lexicon_extraction.weights.metadata_group_path`

- Value: `3.0`
- Category: `manual_domain_seed`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `lexicon_extraction.weights.metadata_field`

- Value: `2.0`
- Category: `manual_domain_seed`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `lexicon_extraction.weights.extracted_title`

- Value: `5.0`
- Category: `manual_domain_seed`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `lexicon_extraction.weights.heading`

- Value: `2.0`
- Category: `manual_domain_seed`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `lexicon_extraction.weights.definition`

- Value: `8.0`
- Category: `manual_domain_seed`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `lexicon_extraction.weights.alias_definition`

- Value: `7.0`
- Category: `manual_domain_seed`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `lexicon_extraction.weights.alias`

- Value: `7.0`
- Category: `manual_domain_seed`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `lexicon_extraction.weights.heading_only_multiplier`

- Value: `0.1`
- Category: `manual_domain_seed`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `lexicon_extraction.weights.primary_regulation_bonus`

- Value: `2.0`
- Category: `manual_domain_seed`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `lexicon_extraction.weights.issuer_bonus_max`

- Value: `2.0`
- Category: `manual_domain_seed`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `lexicon_extraction.weights.high_confidence_min_score`

- Value: `16`
- Category: `manual_domain_seed`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `lexicon_extraction.weights.medium_confidence_min_score`

- Value: `8`
- Category: `manual_domain_seed`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `lexicon_extraction.weights.generated_entities_limit`

- Value: `300`
- Category: `manual_domain_seed`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `lexicon_extraction.weights.generated_topics_limit`

- Value: `300`
- Category: `manual_domain_seed`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `lexicon_extraction.weights.max_examples`

- Value: `5`
- Category: `manual_domain_seed`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

## resources/config/retrieval_ranking.json

- Description: Behavior-preserving retrieval ranking heuristics. Values are manual unless noted as standard IR.
- Calibrated: `False`

### `retrieval_ranking.role_boost.primary_regulation`

- Value: `1.45`
- Category: `manual_domain_policy`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `retrieval_ranking.role_boost.attachment`

- Value: `1.2`
- Category: `manual_domain_policy`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `retrieval_ranking.role_boost.operational_requirement`

- Value: `1.1`
- Category: `manual_domain_policy`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `retrieval_ranking.role_boost.secondary_faq`

- Value: `0.75`
- Category: `manual_domain_policy`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `retrieval_ranking.role_boost.secondary_summary`

- Value: `0.65`
- Category: `manual_domain_policy`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `retrieval_ranking.bm25.k1`

- Value: `1.4`
- Category: `standard_ir`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `retrieval_ranking.bm25.b`

- Value: `0.75`
- Category: `standard_ir`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `retrieval_ranking.bm25.category`

- Value: `standard_ir`
- Category: `standard_ir`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `retrieval_ranking.candidate_selection.max_candidate_terms`

- Value: `6`
- Category: `manual_domain_policy`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `retrieval_ranking.candidate_selection.sqlite_min_match_when_candidate_terms_at_least`

- Value: `3`
- Category: `manual_domain_policy`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `retrieval_ranking.candidate_selection.sqlite_min_match`

- Value: `2`
- Category: `manual_domain_policy`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `retrieval_ranking.candidate_selection.sqlite_default_min_match`

- Value: `1`
- Category: `manual_domain_policy`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `retrieval_ranking.candidate_selection.sqlite_candidate_limit`

- Value: `50000`
- Category: `manual_domain_policy`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `retrieval_ranking.candidate_selection.sqlite_batch_size`

- Value: `900`
- Category: `manual_domain_policy`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `retrieval_ranking.lexical_score.exact_query_multiplier`

- Value: `1.35`
- Category: `manual_domain_policy`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `retrieval_ranking.lexical_score.all_phrase_terms_multiplier`

- Value: `1.15`
- Category: `manual_domain_policy`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `retrieval_ranking.lexical_score.phrase_term_min_chars`

- Value: `3`
- Category: `manual_domain_policy`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `retrieval_ranking.lexical_score.phrase_term_max_count_for_all_terms`

- Value: `6`
- Category: `manual_domain_policy`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `retrieval_ranking.lexical_score.title_hit_multiplier_per_hit`

- Value: `0.08`
- Category: `manual_domain_policy`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `retrieval_ranking.lexical_score.title_hit_max_boost`

- Value: `0.5`
- Category: `manual_domain_policy`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `retrieval_ranking.lexical_score.exact_phrase_title_multiplier`

- Value: `1.45`
- Category: `manual_domain_policy`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `retrieval_ranking.lexical_score.exact_phrase_text_multiplier`

- Value: `1.15`
- Category: `manual_domain_policy`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `retrieval_ranking.lexical_score.issuer_match_multiplier`

- Value: `1.08`
- Category: `manual_domain_policy`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `retrieval_ranking.balanced_issuer_search.min_per_issuer_limit`

- Value: `3`
- Category: `manual_domain_policy`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `retrieval_ranking.balanced_issuer_search.candidate_multiplier`

- Value: `3`
- Category: `manual_domain_policy`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `retrieval_ranking.balanced_issuer_search.ojk_pattern`

- Value: `ojk`
- Category: `manual_domain_policy`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `retrieval_ranking.balanced_issuer_search.bi_patterns`

- Value: `["bi", "bank indonesia"]`
- Category: `manual_domain_policy`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `retrieval_ranking.snippet.max_len`

- Value: `420`
- Category: `manual_domain_policy`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `retrieval_ranking.snippet.context_before_first_match`

- Value: `120`
- Category: `manual_domain_policy`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `retrieval_ranking.title_search.min_score`

- Value: `65.0`
- Category: `manual_domain_policy`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `retrieval_ranking.title_search.coverage_weight`

- Value: `60.0`
- Category: `manual_domain_policy`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `retrieval_ranking.title_search.title_coverage_weight`

- Value: `35.0`
- Category: `manual_domain_policy`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `retrieval_ranking.title_search.overlap_count_weight`

- Value: `4.0`
- Category: `manual_domain_policy`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `retrieval_ranking.title_search.exact_query_bonus`

- Value: `80.0`
- Category: `manual_domain_policy`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `retrieval_ranking.title_search.query_title_substring_bonus`

- Value: `45.0`
- Category: `manual_domain_policy`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `retrieval_ranking.title_search.all_query_tokens_bonus`

- Value: `35.0`
- Category: `manual_domain_policy`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `retrieval_ranking.title_search.ordered_query_bonus`

- Value: `35.0`
- Category: `manual_domain_policy`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `retrieval_ranking.title_search.short_title_max_tokens`

- Value: `2`
- Category: `manual_domain_policy`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `retrieval_ranking.title_search.long_query_min_tokens`

- Value: `4`
- Category: `manual_domain_policy`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `retrieval_ranking.title_search.short_title_min_coverage`

- Value: `0.75`
- Category: `manual_domain_policy`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `retrieval_ranking.title_search.short_title_penalty_multiplier`

- Value: `0.55`
- Category: `manual_domain_policy`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `retrieval_ranking.planned_result.rank_score_base`

- Value: `100.0`
- Category: `manual_domain_policy`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `retrieval_ranking.planned_result.rank_score_offset`

- Value: `5`
- Category: `manual_domain_policy`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `retrieval_ranking.planned_result.search_order_decay`

- Value: `0.1`
- Category: `manual_domain_policy`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `retrieval_ranking.planned_result.overlap_max_boost`

- Value: `0.6`
- Category: `manual_domain_policy`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `retrieval_ranking.planned_result.title_overlap_weight`

- Value: `0.1`
- Category: `manual_domain_policy`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `retrieval_ranking.planned_result.search_overlap_weight`

- Value: `0.04`
- Category: `manual_domain_policy`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `retrieval_ranking.planned_result.title_quality_base`

- Value: `0.7`
- Category: `manual_domain_policy`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `retrieval_ranking.planned_result.title_quality_max_bonus`

- Value: `0.7`
- Category: `manual_domain_policy`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `retrieval_ranking.planned_result.title_quality_score_divisor`

- Value: `160.0`
- Category: `manual_domain_policy`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `retrieval_ranking.planned_result.reason_boost.title`

- Value: `1.4`
- Category: `manual_domain_policy`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `retrieval_ranking.planned_result.reason_boost.topic`

- Value: `1.25`
- Category: `manual_domain_policy`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `retrieval_ranking.planned_result.reason_boost.intent`

- Value: `1.08`
- Category: `manual_domain_policy`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `retrieval_ranking.planned_result.reason_boost.entity`

- Value: `1.03`
- Category: `manual_domain_policy`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `retrieval_ranking.planned_result.reason_boost.default`

- Value: `0.9`
- Category: `manual_domain_policy`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `retrieval_ranking.sector_alignment.bank_umum_query_terms`

- Value: `["bank umum", "buk", "bus", "unit usaha syariah", "uus"]`
- Category: `manual_domain_seed`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `retrieval_ranking.sector_alignment.bpr_query_terms`

- Value: `["bpr", "bprs", "bank perekonomian rakyat", "bank perekonomian rakyat syariah", "bank perkreditan rakyat", "bank pembiayaan rakyat syariah"]`
- Category: `manual_domain_seed`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `retrieval_ranking.sector_alignment.bank_umum_title_terms`

- Value: `["bank umum", "buk", "bus", "unit usaha syariah"]`
- Category: `manual_domain_seed`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `retrieval_ranking.sector_alignment.bpr_title_terms`

- Value: `["bpr", "bprs", "bank perekonomian rakyat", "bank perekonomian rakyat syariah", "bank perkreditan rakyat", "bank pembiayaan rakyat syariah"]`
- Category: `manual_domain_seed`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `retrieval_ranking.sector_alignment.bank_umum_query_bpr_title_multiplier`

- Value: `0.55`
- Category: `manual_domain_seed`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `retrieval_ranking.sector_alignment.bpr_query_bank_umum_title_multiplier`

- Value: `0.7`
- Category: `manual_domain_seed`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `retrieval_ranking.query_planning.generic_bank_entity_names`

- Value: `["bank", "bank_umum", "bpr_bprs"]`
- Category: `manual_domain_seed`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `retrieval_ranking.query_planning.bank_entity_name`

- Value: `bank`
- Category: `manual_domain_seed`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `retrieval_ranking.query_planning.bank_entity_generic_patterns`

- Value: `["bank"]`
- Category: `manual_domain_seed`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `retrieval_ranking.query_planning.default_intent`

- Value: `find_regulations`
- Category: `manual_domain_seed`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `retrieval_ranking.query_planning.bank_default_issuer`

- Value: `OJK`
- Category: `manual_domain_seed`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `retrieval_ranking.query_planning.issuer_patterns.OJK`

- Value: `["ojk"]`
- Category: `manual_domain_seed`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `retrieval_ranking.query_planning.issuer_patterns.BI`

- Value: `["bi", "bank indonesia"]`
- Category: `manual_domain_seed`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `retrieval_ranking.query_planning.intent_expansions.sanctions.role`

- Value: `primary_regulation`
- Category: `manual_domain_seed`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `retrieval_ranking.query_planning.intent_expansions.sanctions.include_secondary`

- Value: `True`
- Category: `manual_domain_seed`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `retrieval_ranking.query_planning.intent_expansions.sanctions.queries`

- Value: `["sanksi administratif", "pelanggaran ketentuan", "denda teguran pencabutan izin"]`
- Category: `manual_domain_seed`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `retrieval_ranking.query_planning.intent_expansions.requirements.role`

- Value: `None`
- Category: `manual_domain_seed`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `retrieval_ranking.query_planning.intent_expansions.requirements.include_secondary`

- Value: `True`
- Category: `manual_domain_seed`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `retrieval_ranking.query_planning.intent_expansions.requirements.queries`

- Value: `["dokumen persyaratan", "formulir surat pernyataan", "matriks self assessment", "checklist kelengkapan dokumen"]`
- Category: `manual_domain_seed`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `retrieval_ranking.query_planning.intent_expansions.deadline.role`

- Value: `primary_regulation`
- Category: `manual_domain_seed`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `retrieval_ranking.query_planning.intent_expansions.deadline.include_secondary`

- Value: `True`
- Category: `manual_domain_seed`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `retrieval_ranking.query_planning.intent_expansions.deadline.queries`

- Value: `["paling lambat batas waktu penyampaian", "jangka waktu pelaporan", "tanggal penyampaian laporan"]`
- Category: `manual_domain_seed`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `retrieval_ranking.query_planning.intent_expansions.definition.role`

- Value: `primary_regulation`
- Category: `manual_domain_seed`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `retrieval_ranking.query_planning.intent_expansions.definition.include_secondary`

- Value: `True`
- Category: `manual_domain_seed`
- Affects runtime: `yes`
- Calibration status: `not calibrated`

### `retrieval_ranking.query_planning.intent_expansions.definition.queries`

- Value: `["pengertian definisi pasal 1", "ketentuan umum definisi"]`
- Category: `manual_domain_seed`
- Affects runtime: `yes`
- Calibration status: `not calibrated`
