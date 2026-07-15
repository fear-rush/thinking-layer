# Source Corpus Baseline

This report validates the normalized, citation-ready corpus used before retrieval and answer composition.

## Summary

- Source corpus rows: 357784
- Duplicate source blocks skipped: 1
- Exact duplicate primary rows excluded: 15531
- Exact duplicate primary files excluded: 41
- Unreadable table rows quarantined: 52
- Rows whose legal issuer differs from the hosting source: 34933
- Documents: 1503
- Files: 1679
- Sources: `{'ease-bi': 27886, 'peraturan-ojk': 329898}`
- Issuers: `{'BI': 62819, 'OJK': 294965}`
- Source priority: `{'primary': 355812, 'secondary': 1972}`
- File roles: `{'primary_regulation': 353870, 'operational_requirement': 1493, 'secondary_summary': 523, 'secondary_faq': 1449, 'attachment': 449}`
- Section types: `{'angka': 39018, 'huruf': 119040, 'ayat': 82923, 'pasal': 30435, 'enumeration_aggregate': 49963, 'point': 10924, 'subpoint': 13538, 'item': 9522, 'abstrak': 523, 'faq': 1449, 'attachment': 449}`
- Lifecycle status: `{'unknown': 357784}`
- Citation quality: `{'document_page_pasal': 91646, 'document_page_pasal_ayat_huruf': 97897, 'document_page_pasal_ayat': 99993, 'document_page': 13845, 'document_page_section': 54403}`

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
