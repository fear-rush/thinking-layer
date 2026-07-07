# Parser Comparison Sample

Small comparison gate before switching away from LiteParse.

## Candidate Parser Availability

- LayoutParser in project env: `False`
- LayoutParser Detectron2 backend in project env: `False`
- MinerU Python package in project env: `False`
- MinerU CLI available: `False`

LayoutParser documentation indicates a meaningful layout-detection comparison needs `Detectron2LayoutModel` with a Detectron2 backend, for example PubLayNet. Local isolated probes installed base LayoutParser, but the Detectron2 backend was not available; the documented Detectron2 Git dependency did not build cleanly under this Python 3.14 environment.

## LiteParse Baseline Sample

| Case | Pages | Rows | Section Types | Citation Quality | Notes |
|---|---:|---:|---|---|---|
| BI QRIS Office Matrix | 2 | 9 | heading: 4, paragraph: 3, table: 2 | document_page: 9 | Recently recovered Office document; table-heavy operational QRIS requirements. |
| BI SNAP Office Matrix | 6 | 29 | pasal: 16, table: 5, paragraph: 4, heading: 3, ayat: 1 | document_page_pasal: 20, document_page: 8, document_page_pasal_ayat: 1 | Recently recovered Office document; SNAP implementation requirements with tables and lists. |
| BI SNAP Functional Test XLSX | 126 | 165 | paragraph: 90, table: 55, heading: 20 | document_page: 165 | Large spreadsheet conversion with many empty converted pages; good stress case for XLSX layout. |
| OJK GMRA Attachment | 122 | 905 | attachment: 905 | document_page_pasal: 546, document_page: 353, document_page_pasal_ayat: 6 | Long PDF attachment with dense legal/table content and known citation-sensitive retrieval hits. |

## BI QRIS Office Matrix

- File ID: `ease-bi-dokumen-persyaratan-pedoman-1201-0-matriks-dokumen-tambahan-untuk-pengembangan-qris`
- Source path: `downloads/ease-bi/dokumen-persyaratan-pedoman/2. Dokumen Pedoman dan Persyaratan Permohonan Persetujuan dan Pelaporan SP Ritel/j. Matriks Tambahan Dokumen Pengembangan QRIS.docx`
- Raw LiteParse output: `processed/raw/liteparse/ease-bi-dokumen-persyaratan-pedoman-1201-0-matriks-dokumen-tambahan-untuk-pengembangan-qris-70630f8630be.json`
- Status: `extracted_ok`
- Pages: `2`
- Source rows: `9`
- Extraction methods: `{'markdown': 9}`

### Focus Pages

- Page `1`: text `1157` chars, markdown `1242` chars, text items `59`, table markers `42`, headings `5`
  - Text: April 2012 Matriks Tambahan Penjelasan Kelengkapan Dokumen Pendukung Pengembangan QRIS Data Pemohon Nama Pemohon : PT ……………… Jenis Permohonan : Permohonan Persetujuan Pengembangan ……………. Dokumen Surat : 1. Surat No…………….. tanggal …………….. perihal: ………………….. Dokumen1 No. Persyarata
  - Markdown: # Matriks Tambahan Penjelasan Kelengkapan Dokumen Pendukung Pengembangan QRIS ## Data Pemohon Nama Pemohon Jenis Permohonan ## Dokumen Surat : PT ……………… : Permohonan Persetujuan Pengembangan ……………. : 1. Surat No…………….. tanggal …………….. perihal: ………………….. --- | No. | Persyaratan Do

## BI SNAP Office Matrix

- File ID: `ease-bi-dokumen-persyaratan-pedoman-1256-0-matriks-tambahan-pengembangan-dengan-snap`
- Source path: `downloads/ease-bi/dokumen-persyaratan-pedoman/4. Standar Nasional Open API Pembayaran (SNAP)/Matriks Tambahan_Pengembangan dengan SNAP.docx`
- Raw LiteParse output: `processed/raw/liteparse/ease-bi-dokumen-persyaratan-pedoman-1256-0-matriks-tambahan-pengembangan-dengan-snap-e7e974975ca4.json`
- Status: `extracted_ok`
- Pages: `6`
- Source rows: `29`
- Extraction methods: `{'markdown': 27, 'geometry_list': 2}`

### Focus Pages

- Page `1`: text `1414` chars, markdown `1523` chars, text items `61`, table markers `45`, headings `4`
  - Text: April 2012 SNAP Dokumen No.xxx tanggal xxx Matriks Kelengkapan Dokumen Pendukung Bagi Penyedia Layanan Pengembangan Aktivitas dan/atau Pengembangan Produk yang Disertai Kerja Sama Berbasis SNAP Data Pemohon Nama Pemohon : PT ……………… Jenis Permohonan : Permohonan Persetujuan Pengem
  - Markdown: April 2012 **SNAP** Dokumen No.xxx tanggal xxx Matriks Kelengkapan Dokumen Pendukung Bagi Penyedia Layanan **Pengembangan Aktivitas dan/atau Pengembangan Produk yang Disertai Kerja Sama Berbasis SNAP** ## Data Pemohon | Nama Pemohon | : PT ……………… | |---|---| | Jenis Permohonan | 
- Page `2`: text `2017` chars, markdown `2074` chars, text items `56`, table markers `24`, headings `2`
  - Text: April 2012 layanan termasuk ketaatan terhadap ketentuan PADG SNAP.  Dokumen sebagaimana dimaksud dalam pasal 20 ayat (3) PADG SNAP dilengkapi dengan nomor dan tanggal dokumen. 3 Dokumen prosedur operasional standar Dokumen yang disampaikan: asesmen kelayakan pengguna layanan Dok
  - Markdown: layanan termasuk ketaatan terhadap ketentuan PADG SNAP. ---  Dokumen sebagaimana dimaksud dalam pasal 20 ayat (3) PADG SNAP dilengkapi dengan nomor dan tanggal dokumen. 3 Dokumen prosedur operasional standar **Dokumen yang disampaikan:** --- asesmen kelayakan pengguna layanan **
- Page `3`: text `2081` chars, markdown `2057` chars, text items `56`, table markers `0`, headings `0`
  - Text: April 2012 b. mengidentifikasi risiko dan mitigasi risiko terhadap proses bisnis dan teknologi informasi dari PJP Pengguna Layanan berdasarkan kebijakan dan kriteria masing-masing Penyedia Layanan 3. Mekanisme atau prosedur uji tuntas (due diligence) kepada pengguna atau calon pe
  - Markdown: b. mengidentifikasi risiko dan mitigasi risiko terhadap proses bisnis dan --- teknologi informasi dari PJP Pengguna Layanan berdasarkan kebijakan dan kriteria masing-masing Penyedia Layanan 3. Mekanisme atau prosedur uji tuntas (due diligence) kepada pengguna atau calon pengguna.

## BI SNAP Functional Test XLSX

- File ID: `ease-bi-dokumen-persyaratan-pedoman-1206-0-skenario-pengujian`
- Source path: `downloads/ease-bi/dokumen-persyaratan-pedoman/4. Standar Nasional Open API Pembayaran (SNAP)/Skenario Functional Test_v.2810.xlsx`
- Raw LiteParse output: `processed/raw/liteparse/ease-bi-dokumen-persyaratan-pedoman-1206-0-skenario-pengujian-0abd9537e916.json`
- Status: `extracted_ok`
- Pages: `126`
- Source rows: `165`
- Extraction methods: `{'markdown': 165}`

### Focus Pages

- Page `1`: text `435` chars, markdown `442` chars, text items `23`, table markers `0`, headings `4`
  - Text: Daftar Isi 1 Card Registration 12 Request for Payment 2 Account Registration 13 Interbank Bulk Transfer 3 Balance Service 14 Customer Top Up 4 Transaction History List 15 Bulk Cash In 5 Transaction History Detail 16 Transfer to Bank 6 Bank Statement 17 Transfer to OTC 7 Intrabank
  - Markdown: ## Daftar Isi 1 Card Registration 2 Account Registration 3 Balance Service 4 Transaction History List 5 Transaction History Detail 6 Bank Statement 7 Intrabank Transfer # 8 Interbank Transfer 9 RTGS Transfer 10 SKNBI Transfer 11 Transfer VA 12 Request for Payment 13 Interbank Bul
- Page `2`: text `1003` chars, markdown `1153` chars, text items `57`, table markers `66`, headings `0`
  - Text: No Service Scenario Expected Result Request 1.1 Any Service Access Token Invalid Error Code: 401xx01 Error Message: "Access Token Invalid" 1.2 Any Service Unauthorized . Signature Error Code: 401xx00 Error Message: "Unauthorized Signature" 1.3 Any Service Unauthorized . stringToS
  - Markdown: | No | Service | Scenario | Expected Result | Request | |---|---|---|---|---| | 1.1 | Any Service | Access Token Invalid | Error Code: 401xx01 Error Message: "Access Token Invalid" | | | 1.2 | Any Service | Unauthorized . Signature | Error Code: 401xx00 Error Message: "Unauthoriz
- Page `3`: text `1133` chars, markdown `1275` chars, text items `56`, table markers `66`, headings `0`
  - Text: 1.10 API Card Registration OTP Needed Response Code: 2000100 Response Message: "success" 1.11 API Card Registration Timeout Request to AIS Error Code: 5040100 Error Message: "Timeout Request to AIS" 1.12 API Card Registration Timeout Request to PIAS Error Code: 5040100 Error Mess
  - Markdown: | 1.10 | API Card Registration | OTP Needed | Response Code: 2000100 Response Message: "success" | | |---|---|---|---|---| | 1.11 | API Card Registration | Timeout Request to AIS | Error Code: 5040100 Error Message: "Timeout Request to AIS" | | | 1.12 | API Card Registration | Ti

## OJK GMRA Attachment

- File ID: `peraturan-ojk-global-master-repurchase-agreement-indonesia-2-lampiran-3-gmra-pdf`
- Source path: `downloads/peraturan-ojk/global-master-repurchase-agreement-indonesia/Lampiran 3 GMRA.pdf`
- Raw LiteParse output: `processed/raw/liteparse/peraturan-ojk-global-master-repurchase-agreement-indonesia-2-lampiran-3-gmra-pdf-6caae7534f43.json`
- Status: `extracted_ok`
- Pages: `122`
- Source rows: `905`
- Extraction methods: `{'markdown': 904, 'geometry_list': 1}`

### Focus Pages

- Page `44`: text `2798` chars, markdown `2797` chars, text items `73`, table markers `0`, headings `0`
  - Text: 44 messaging details, set out in Annex I hereto. rincinya disebutkan dalam Lampiran I Perjanjian ini. (b) Subject to sub-paragraph (c) below, any such notice or other (b) Dengan tunduk pada sub-paragraf (c) di bawah, setiap communication shall be effective- pemberitahuan atau kom
  - Markdown: messaging details, set out in Annex I hereto. rincinya disebutkan dalam Lampiran I Perjanjian ini. (b) Subject to sub-paragraph (c) below, any such notice or other communication shall be effective- (i) if in writing and delivered in person or by courier, at the time when it is de
- Page `62`: text `2184` chars, markdown `2187` chars, text items `64`, table markers `0`, headings `3`
  - Text: 62 Simple interest shall accrue daily and shall be payable as Bunga yang diperhitungkan dari jumlah pokok (simple interest) agreed between the parties or, failing agreement, monthly. akan dijumlahkan secara harian dan akan terutang sebagaimana disepakati oleh para pihak atau, apa
  - Markdown: Simple interest shall accrue daily and shall be payable as agreed between the parties or, failing agreement, monthly. Bunga yang diperhitungkan dari jumlah pokok (simple interest) akan dijumlahkan secara harian dan akan terutang sebagaimana disepakati oleh para pihak atau, apabil
- Page `86`: text `3058` chars, markdown `3055` chars, text items `77`, table markers `0`, headings `0`
  - Text: 86 deemed to accrue on a daily basis from (and including) tidak termasuk) tanggal penghitungan namun belum dibayar. the issue date or the last Income Payment Date (as the Untuk tujuan ini, Penghasilan yang belum dibayar harus case may be) to (but excluding) the next Income Paymen
  - Markdown: deemed to accrue on a daily basis from (and including) the issue date or the last Income Payment Date (as the case may be) to (but excluding) the next Income Payment Date or the maturity date (whichever is the earlier); tidak termasuk) tanggal penghitungan namun belum dibayar. Un

## Decision

Do not switch parsers yet.

Reasons:
- Current LiteParse baseline has extracted all manifest files and preserves page-level citation anchors.
- LayoutParser's useful layout-detection path is not currently runnable in the Python 3.14 project environment without extra Detectron2 build work.
- MinerU is not part of the active baseline: it is a full document parser rather than a LiteParse OCR backend, and full-corpus runtime is not acceptable on the current local machine.
- The recovered Office cases are now searchable, and XLSX/table layout remains the main quality risk to review visually.

Next actions:
- Run visual page checks for the sampled QRIS, SNAP, XLSX, and GMRA pages.
- Keep PaddleOCR as the selective OCR backend integrated through LiteParse.
- Prioritize table-specific handling for XLSX and regulation attachments before replacing the whole parser.
