# Source Corpus Baseline

This report validates the normalized, citation-ready corpus used before retrieval and answer composition.

## Summary

- Source corpus rows: 537355
- Documents: 1562
- Files: 2471
- Sources: `{'ease-bi': 31713, 'peraturan-ojk': 505642}`
- Issuers: `{'BI': 31713, 'OJK': 505642}`
- Source priority: `{'primary': 521902, 'secondary': 15453}`
- File roles: `{'primary_regulation': 509613, 'operational_requirement': 2185, 'secondary_faq': 11498, 'secondary_summary': 3955, 'attachment': 10104}`
- Section types: `{'paragraph': 24917, 'table': 62382, 'pasal': 292827, 'ayat': 64572, 'heading': 56759, 'list_item': 10341, 'faq': 11508, 'abstrak': 3945, 'attachment': 10104}`
- Citation quality: `{'document_page': 73996, 'document_page_pasal': 394602, 'document_page_pasal_ayat': 40115, 'document_page_pasal_ayat_huruf': 28642}`

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

- `OJK|KLASIFIKASI BAPEPAM|kep- 02 /pm/2004|2004` | III. D.1. Penyelenggara Perdagangan Surat Utang Negara Berdasarkan Keputusan Ketua Badan Pengawas Pasar Modal
- `OJK|KLASIFIKASI BAPEPAM|kep- 09/bl/2006|2006` | V.B.2. Perizinan Wakil Agen Penjual Efek Reksa Dana Berdasarkan Keputusan Badan Pengawas Pasar Modal dan Lembaga Keuangan
- `OJK|KLASIFIKASI BAPEPAM|kep- 10/bl/2006|2016` | V.B.3. Pendaftaran Agen Penjual Efek Reksa Dana Berdasarkan Keputusan Ketua Badan Pengawas Pasar Modal dan Lembaga Keuangan
- `OJK|KLASIFIKASI BAPEPAM|kep- 108 /bl/2008|2008` | III. C8. Komisaris Lembaga Penyimpanan dan Penyelesaian Berdasarkan Keputusan Ketua Badan Pengawas Pasar Modal dan Lembaga Keuangan
- `OJK|KLASIFIKASI BAPEPAM|kep- 13/bl/2009|2009` | III. B3. Direktur Lembaga Kliring dan Penjaminan Berdasarkan Keputusan Ketua Badan Pengawas Pasar Modal dan Lembaga Keuangan
- `OJK|KLASIFIKASI BAPEPAM|kep- 14/bl/2009|2009` | III. C.3. Direktur Lembaga Penyimpanan dan Penyelesaian Berdasarkan Keputusan Ketua Badan Pengawas Pasar Modal
- `OJK|KLASIFIKASI BAPEPAM|kep- 178/bl/2008|2008` | V.G.5. Perubahan Peraturan tentang Fungsi Manajer Investasi Berkaitan dengan Efek Beragun Aset (Asset Backed Securities) Berdasarkan Keputusan Ketua Badan Pengawas Pasar Modal dan Lembaga Keuangan
- `OJK|KLASIFIKASI BAPEPAM|kep- 181/bl/2007|2016` | II.J.1. Pengenaan Biaya Tahunan Atas Bursa Efek, Lembaga Kliring dan Penjaminan, serta Lembaga Penyimpanan Berdasarkan Keputusan Ketua Badan Pengawas Pasar Modal dan Lembaga Keuangan
- `OJK|KLASIFIKASI BAPEPAM|kep- 27/pm/2000|2000` | V.D.8. Kegiatan Perusahaan Efek di Berbagai Lokasi Berdasarkan Keputusan Ketua Badan Pengawas Pasar Modal
- `OJK|KLASIFIKASI BAPEPAM|kep- 29/pm/1998|1998` | III. C6. Prosedur Operasi dan Pengendalian Intern Lembaga Penyimpana dan Penyelesaian Berdasarkan Keputusan Ketua Badan Pengawas Pasar Modal
- `OJK|KLASIFIKASI BAPEPAM|kep- 309/bl/2008|2008` | VI. C3. Hubungan Kredit dan Penjaminan Antara Wali Amanat dengan Emiten Berdasarkan Keputusan Ketua Badan Pengawas Pasar Modal dan Lembaga Keuangan
- `OJK|KLASIFIKASI BAPEPAM|kep- 327/bl/2012|2012` | VI. B2. Pembuatan Nomor tunggal Identitas Pemodal pada Lembaga Penyimpanan dan Penyelesaian Oleh Biro Administrasi Efek atau Emiten dan Perusahaan Publik yang Menyelenggarakan Administrasi Efek Sendiri
- `OJK|KLASIFIKASI BAPEPAM|kep- 334 /bl/2007|2007` | V.A.1. Perizinan Perusahaan Efek Berdasarkan Keputusan Ketua Badan Pengawas Pasar Modal dan Lembaga Keuangan
- `OJK|KLASIFIKASI BAPEPAM|kep- 39/pm/2003|2003` | III. E.1. Kontrak Berjangka dan Opsi Atas Efek atau Indeks Efek Berdasarkan Keputusan Ketua Badan Pengawas Pasar Modal
- `OJK|KLASIFIKASI BAPEPAM|kep- 401/bl/2008|2008` | XI. B2. Pembelian Kembali saham yang Dikeluarkan Oleh Emiten atau Perusahaan Publikdalam Kondisi Pasar yang Berpotensi Krisis
