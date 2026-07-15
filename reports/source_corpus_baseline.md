# Source Corpus Baseline

This report validates the normalized, citation-ready corpus used before retrieval and answer composition.

## Summary

- Source corpus rows: 398930
- Duplicate source blocks skipped: 1
- Exact duplicate primary rows excluded: 15897
- Exact duplicate primary files excluded: 41
- Unreadable table rows quarantined: 52
- Rows whose legal issuer differs from the hosting source: 35629
- Documents: 1346
- Files: 1506
- Sources: `{'ease-bi': 28460, 'peraturan-ojk': 370470}`
- Issuers: `{'BI': 64089, 'OJK': 334841}`
- Source priority: `{'primary': 396777, 'secondary': 2153}`
- File roles: `{'primary_regulation': 394444, 'operational_requirement': 1501, 'secondary_summary': 748, 'secondary_faq': 1405, 'attachment': 832}`
- Section types: `{'angka': 80333, 'huruf': 150974, 'ayat': 96141, 'pasal': 31024, 'enumeration_aggregate': 37297, 'abstrak': 748, 'faq': 1405, 'point': 38, 'subpoint': 60, 'item': 78, 'attachment': 832}`
- Lifecycle status: `{'unknown': 398930}`
- Citation quality: `{'document_page_pasal': 98096, 'document_page_pasal_ayat_huruf': 105361, 'document_page_pasal_ayat': 105271, 'document_page': 90026, 'document_page_section': 176}`

## Sikepo Metadata Coverage

Sikepo is treated as enrichment metadata, not as the primary OJK text source.

- Primary OJK regulation keys: 1513
- Sikepo regulation keys: 422
- Strict matched keys: 93
- Strict primary OJK keys without Sikepo metadata: 1420
- Strict Sikepo keys without primary OJK document: 329
- Loose matched keys: 94
- Loose primary OJK keys without Sikepo metadata: 1416
- Loose Sikepo keys without primary OJK document: 328

## Citation Contract

- Answer composition may cite document and page when `citation_quality` is at least `document_page`.
- Answer composition may cite Pasal/Ayat only when those fields are present on the evidence block.
- For FAQ, abstrak, attachment, DOCX, and XLSX blocks, missing Pasal/Ayat is acceptable and must not be invented.
- If evidence is weak or missing, the answer layer must say not found instead of filling gaps.

## Primary OJK Without Sikepo Examples

- `BI|PBI|10/ 1 /pbi/2008|2008` | Peraturan Bank Indonesia tentang Perubahan atas Peraturan Bank Indonesia Nomor 8/5/PBI/2006 tentang Mediasi Perbankan
- `BI|PBI|10/ 15 /pbi/2008|2008` | Peraturan Bank Indonesia tentang Kewajiban Penyediaan Modal Minimum Bank Umum
- `BI|PBI|10/ 19 /pbi/2008|2008` | Peraturan Bank Indonesia tentang Giro Wajib Minimum Bank Umum pada Bank Indonesia dalam Rupiah dan Valuta Asing
- `BI|PBI|10/ 23 /pbi/2008|2008` | Peraturan Bank Indonesia tentang Perubahan atas Peraturan Bank Indonesia Nomor 6/21/PBI/2004 tentang Giro Wajib Minimum dalam Rupiah dan Valuta Asing bagi Bank Umum yang Melaksanakan Kegiatan Usaha berdasarkan Prinsip Syariah
- `BI|PBI|10/ 24 /pbi/2008|2008` | Peraturan Bank Indonesia tentang Perubahan Kedua atas Peraturan Bank Indonesia Nomor 8/21/PBI/2006 tentang Penilaian Kualitas Aktiva Bank Umum yang Melaksanakan Kegiatan Usaha berdasarkan Prinsip Syariah
- `BI|PBI|10/ 25 /pbi/2008|2008` | Peraturan Bank Indonesia tentang Perubahan atas Peraturan Bank Indonesia Nomor 10/19/PBI/2008 tentang Giro Wajib Minimum Bank Umum pada Bank Indonesia dalam Rupiah dan Valuta Asing
- `BI|PBI|10/ 27 /pbi/2008|2008` | Peraturan Bank Indonesia tentang Perubahan atas Peraturan Bank Indonesia Nomor 6/9/PBI/2004 tentang Tindak Lanjut Pengawasan dan Penetapan Status Bank
- `BI|PBI|10/ 39 /pbi/2008|2008` | Peraturan Bank Indonesia tentang Peraturan Pelaksanaan Penanganan Khusus Permasalahan Perbankan Pascabencana Nasional di Provinsi Nanggroe Aceh Darussalam dan Kepulauan Nias Provinsi Sumatera Utara
- `BI|PBI|10/17/pbi/2008|2016` | Peraturan Bank Indonesia tentang Produk Bank Syariah dan Unit Usaha Syariah
- `BI|PBI|10/3/pbi/2008|2008` | Peraturan Bank Indonesia tentang Laporan Kantor Pusat Bank Umum
- `BI|PBI|10/32/pbi/2008|2008` | Peraturan Bank Indonesia tentang Komite Perbankan Syariah
- `BI|PBI|10/5/pbi/2008|2008` | Peraturan Bank Indonesia tentang Perubahan atas Peraturan Bank Indonesia Nommor 5/6/PBI/2003 tentang Surat Kredit Berdokumen dalam Negeri
- `BI|PBI|11/ 1 /pbi/2009|2009` | Peraturan Bank Indonesia tentang Bank Umum
- `BI|PBI|11/ 15 /pbi/2009|2009` | Peraturan Bank Indonesia tentang Perubahan Kegiatan Usaha Bank Konvensional menjadi Bank Syariah
- `BI|PBI|11/ 19 /pbi/2009|2009` | Peraturan Bank Indonesia tentang Sertifikasi Manajemen Risiko bagi Pengurus dan Pejabat Bank Umum
