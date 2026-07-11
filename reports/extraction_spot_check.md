# Extraction Spot Check

Focused review of high-value regulation areas using the current citation-ready source corpus.

- Source: `processed/source_corpus.ndjson`

## Summary

| Target | Rows | Documents | Page rate | Pasal/Ayat rate | Table rate | Warnings |
|---|---:|---:|---:|---:|---:|---|
| BI PJP | 2099 | 3 | 1.0 | 0.98 | 0.146 | `very_short_text` |
| BI PIP | 1616 | 3 | 1.0 | 0.979 | 0.116 | `very_short_text` |
| BI Sistem Pembayaran | 3044 | 6 | 1.0 | 0.984 | 0.102 | `very_short_text` |
| OJK APU PPT | 7507 | 15 | 1.0 | 0.923 | 0.082 | `very_short_text` |
| OJK Consumer Protection | 3531 | 8 | 1.0 | 0.955 | 0.144 | `form_placeholder_text`, `very_short_text` |
| OJK SLIK | 7024 | 6 | 1.0 | 0.646 | 0.343 | `form_placeholder_text`, `high_document_page_only_rate`, `very_short_text` |
| OJK BPR BPRS | 45142 | 89 | 1.0 | 0.837 | 0.129 | `form_placeholder_text`, `very_short_text` |
| OJK Modal Ventura | 18403 | 24 | 1.0 | 0.982 | 0.157 | `form_placeholder_text`, `very_short_text` |
| OJK Perusahaan Pembiayaan | 30742 | 44 | 1.0 | 0.921 | 0.12 | `form_placeholder_text`, `very_short_text` |
| OJK Aset Keuangan Digital | 5804 | 6 | 1.0 | 0.82 | 0.13 | `form_placeholder_text`, `very_short_text` |

## BI PJP

- Issuer: `BI`
- Title patterns: `['Penyedia Jasa Pembayaran', 'PBI No.23/6/PBI/2021']`
- Rows: `2099`
- Documents: `3`
- Section types: `{'pasal': 1329, 'ayat': 360, 'table': 306, 'heading': 84, 'paragraph': 18, 'list_item': 2}`
- Citation quality: `{'document_page_pasal': 1661, 'document_page_pasal_ayat': 272, 'document_page_pasal_ayat_huruf': 123, 'document_page': 43}`
- Issue counts: `{'very_short_text': 625}`
- Warnings: `['very_short_text']`

### Evidence Probe

- Query: `peraturan BI tentang penyedia jasa pembayaran apa saja?`
- Confidence: `strong` score `0.982`

- `BI` `document_page_pasal_ayat` `ayat`: PBI No.23/6/PBI/2021 - Penyedia Jasa Pembayaran, hlm. 4, Pasal 1, ayat (1)
  - Snippet: (1) PJP menyelenggarakan aktivitas yang meliputi:
- `BI` `document_page` `paragraph`: PBI No.23/6/PBI/2021 - Penyedia Jasa Pembayaran, hlm. 2
  - Snippet: 2. Peraturan Bank Indonesia Nomor 22/23/PBI/2020 tentang Sistem Pembayaran (Lembaran Negara Republik Indonesia Tahun 2020 Nomor 311, Tambahan Lembaran Negara Republik Indonesia Nomor 6610); MEMUTUSKAN: Menetapkan: PERATURAN BANK INDONESIA TENTANG PENYEDIA JASA PEMBAYARAN. BAB I KETENTUAN UMUM
- `BI` `document_page_pasal_ayat` `ayat`: PBI No.22/23/PBI/2020 - Sistem Pembayaran, hlm. 5, Pasal 5, ayat (1)
  - Snippet: Pasal 5 (1) Penyelenggara jasa Sistem Pembayaran terdiri atas:
- `BI` `document_page_pasal_ayat` `ayat`: PBI No.23/11/PBI/2021 - Standar Nasional Sistem Pembayaran, hlm. 4, Pasal 2, ayat (1)
  - Snippet: Pasal 2 (1) Kebijakan Standar Nasional bertujuan untuk:

### Extraction Examples

- `document_page_pasal_ayat` `ayat`: PBI No.23/6/PBI/2021 - Penyedia Jasa Pembayaran, hlm. 4, Pasal 1, ayat (1)
  - Flags: `[]`
  - Text: (1) PJP menyelenggarakan aktivitas yang meliputi:

- `document_page_pasal` `pasal`: PBI No.23/6/PBI/2021 - Penyedia Jasa Pembayaran, hlm. 2, Pasal 1
  - Flags: `[]`
  - Text: Pasal 1 Dalam Peraturan Bank Indonesia ini yang dimaksud dengan:

- `document_page` `table`: PBI No.23/6/PBI/2021 - Penyedia Jasa Pembayaran, hlm. 1
  - Flags: `[]`
  - Text: pengaturan - akses - ke - industri, - penyelenggaraan,; pengakhiran penyelenggaraan kegiatan, - pengawasan,

- `document_page` `paragraph`: PBI No.23/6/PBI/2021 - Penyedia Jasa Pembayaran, hlm. 1
  - Flags: `[]`
  - Text: PERATURAN BANK INDONESIA NOMOR 23/6/PBI/2021 TENTANG PENYEDIA JASA PEMBAYARAN DENGAN RAHMAT TUHAN YANG MAHA ESA GUBERNUR BANK INDONESIA, Menimbang: a. bahwa reformasi pengaturan sistem pembayaran termasuk penyediaan jasa pembayaran, perlu dilakukan sejalan dengan pemenuhan prinsip penyelenggaraan sistem pembayaran yang cepat, mudah, murah, aman, dan andal, d

- `document_page` `paragraph`: PBI No.23/6/PBI/2021 - Penyedia Jasa Pembayaran, hlm. 1
  - Flags: `[]`
  - Text: mengakomodasi perkembangan model bisnis dan inovasi penyediaan jasa pembayaran dari penyelenggara kepada pengguna jasa, serta keterhubungan dengan penyelenggara atau pihak lain dalam penyelenggaraan sistem pembayaran dalam mendukung digitalisasi ekonomi dan keuangan; c. bahwa perkembangan aktivitas penyediaan jasa sistem pembayaran menuntut dilakukannya peng

- `document_page` `paragraph`: PBI No.23/6/PBI/2021 - Penyedia Jasa Pembayaran, hlm. 1
  - Flags: `[]`
  - Text: dan pemrosesan data dan/atau informasi sistem pembayaran


## BI PIP

- Issuer: `BI`
- Title patterns: `['Penyelenggara Infrastruktur Sistem Pembayaran', 'PBI No.23/7/PBI/2021']`
- Rows: `1616`
- Documents: `3`
- Section types: `{'pasal': 1086, 'ayat': 288, 'table': 188, 'heading': 41, 'paragraph': 13}`
- Citation quality: `{'document_page_pasal': 1273, 'document_page_pasal_ayat': 205, 'document_page_pasal_ayat_huruf': 104, 'document_page': 34}`
- Issue counts: `{'very_short_text': 531}`
- Warnings: `['very_short_text']`

### Evidence Probe

- Query: `aturan BI tentang penyelenggara infrastruktur sistem pembayaran`
- Confidence: `strong` score `1.0`

- `BI` `document_page_pasal_ayat` `ayat`: PBI No.23/7/PBI/2021 - Penyelenggara Infrastruktur Sistem Pembayaran, hlm. 6, Pasal 2, ayat (1)
  - Snippet: Pasal 2 (1) Dalam tahapan pemrosesan transaksi pembayaran, PIP
- `BI` `document_page_pasal` `pasal`: PBI No.23/7/PBI/2021 - Penyelenggara Infrastruktur Sistem Pembayaran, hlm. 29, Pasal 47
  - Snippet: Pembayaran Bank Indonesia; dan b. pihak lain yang menyelenggarakan infrastruktur Sistem Pembayaran di industri.
- `BI` `document_page_pasal_ayat` `ayat`: · Dokumen Persyaratan Penetapan Penyelenggara Infrastruktur Sistem Pembayaran (PIP) - Bank, hlm. 4, Pasal 20, ayat (3)
  - Snippet: mengajukan permohonan; dan d. tidak termasuk dalam daftar hitam nasional penarik cek atau bilyet giro kosong yang ditatausahakan Bank Indonesia pada saat mengajukan permohonan. Surat pernyataan dibuat dengan bermeterai cukup. Pemegang saham yang menyampaikan surat pernyataan dimaksud adalah pemegang saham sebagaimana dimaksud dalam Pasal 20 ayat (3) PBI Penyelenggara Infrastruktur Sistem Pembayaran. Surat pernyataan ...
- `BI` `document_page_pasal_ayat` `ayat`: · Dokumen Persyaratan Penetapan Penyelenggara Infrastruktur Sistem Pembayaran(PIP)- Lembaga Selain Bank, hlm. 9, Pasal 20, ayat (3)
  - Snippet: ...g saham yang menyampaikan surat pernyataan dimaksud adalah pemegang saham sebagaimana dimaksud dalam Pasal 20 ayat (3) PBI Penyelenggara Infrastruktur Sistem Pembayaran. Surat pernyataan dan jaminan memuat pernyataan bahwa perusahaan tidak sedang dalam: a. pengenaan sanksi; dan/atau b. proses hukum perkara pidana, perdata, dan/atau kepailitan.

### Extraction Examples

- `document_page_pasal_ayat` `ayat`: PBI No.23/7/PBI/2021 - Penyelenggara Infrastruktur Sistem Pembayaran, hlm. 6, Pasal 2, ayat (1)
  - Flags: `[]`
  - Text: Pasal 2 (1) Dalam tahapan pemrosesan transaksi pembayaran, PIP

- `document_page_pasal` `pasal`: PBI No.23/7/PBI/2021 - Penyelenggara Infrastruktur Sistem Pembayaran, hlm. 2, Pasal 1
  - Flags: `[]`
  - Text: Pasal 1 Dalam Peraturan Bank Indonesia ini yang dimaksud dengan:

- `document_page_pasal` `table`: PBI No.23/7/PBI/2021 - Penyelenggara Infrastruktur Sistem Pembayaran, hlm. 6, Pasal 2
  - Flags: `[]`
  - Text: a. Kliring; dan/atau; b. Penyelesaian Akhir,

- `document_page` `paragraph`: PBI No.23/7/PBI/2021 - Penyelenggara Infrastruktur Sistem Pembayaran, hlm. 1
  - Flags: `[]`
  - Text: PERATURAN BANK INDONESIA NOMOR 23/7/PBI/2021 TENTANG PENYELENGGARA INFRASTRUKTUR SISTEM PEMBAYARAN DENGAN RAHMAT TUHAN YANG MAHA ESA GUBERNUR BANK INDONESIA, Menimbang: a. bahwa reformasi pengaturan sistem pembayaran bertujuan untuk mencari titik keseimbangan antara upaya optimalisasi peluang inovasi digital untuk menciptakan sistem pembayaran yang cepat, mu

- `document_page` `paragraph`: PBI No.23/7/PBI/2021 - Penyelenggara Infrastruktur Sistem Pembayaran, hlm. 1
  - Flags: `[]`
  - Text: mengakomodasi kebutuhan pengaturan berdasarkan perkembangan inovasi dan model bisnis di bidang sistem pembayaran dan penyesuaian ketentuan sistem pembayaran yang berlaku saat ini; c. bahwa perkembangan aktivitas penyelenggaraan infrastruktur sistem pembayaran menuntut dilakukannya penguatan fungsi penyelenggaraan infrastruktur yang dilakukan oleh otoritas da

- `document_page` `heading`: PBI No.23/7/PBI/2021 - Penyelenggara Infrastruktur Sistem Pembayaran, hlm. 2, huruf d
  - Flags: `[]`
  - Text: d. bahwa berdasarkan pertimbangan sebagaimana dimaksud


## BI Sistem Pembayaran

- Issuer: `BI`
- Title patterns: `['Sistem Pembayaran']`
- Rows: `3044`
- Documents: `6`
- Section types: `{'pasal': 2056, 'ayat': 587, 'table': 311, 'heading': 64, 'paragraph': 26}`
- Citation quality: `{'document_page_pasal': 2376, 'document_page_pasal_ayat': 414, 'document_page_pasal_ayat_huruf': 205, 'document_page': 49}`
- Issue counts: `{'very_short_text': 979}`
- Warnings: `['very_short_text']`

### Evidence Probe

- Query: `aturan sistem pembayaran Bank Indonesia`
- Confidence: `strong` score `0.999`

- `BI` `document_page_pasal_ayat` `ayat`: PBI No.23/7/PBI/2021 - Penyelenggara Infrastruktur Sistem Pembayaran, hlm. 6, Pasal 2, ayat (1)
  - Snippet: Pasal 2 (1) Dalam tahapan pemrosesan transaksi pembayaran, PIP
- `BI` `document_page_pasal` `pasal`: PBI No.23/7/PBI/2021 - Penyelenggara Infrastruktur Sistem Pembayaran, hlm. 29, Pasal 47
  - Snippet: Pembayaran Bank Indonesia; dan b. pihak lain yang menyelenggarakan infrastruktur Sistem Pembayaran di industri.
- `BI` `document_page_pasal_ayat` `ayat`: PBI No.22/23/PBI/2020 - Sistem Pembayaran, hlm. 5, Pasal 5, ayat (1)
  - Snippet: Pasal 5 (1) Penyelenggara jasa Sistem Pembayaran terdiri atas:
- `BI` `document_page` `paragraph`: PBI No.22/23/PBI/2020 - Sistem Pembayaran, hlm. 1
  - Snippet: pembayaran menuntut dilakukannya penataan kembali industri sistem pembayaran melalui reformasi pengaturan sistem pembayaran; c. bahwa diperlukan pengaturan sistem pembayaran yang efektif dan responsif yang meliputi seluruh aspek penyelenggaraan sistem pembayaran guna mengakomodasi perkembangan ekonomi dan keuangan digital; d. bahwa berdasarkan pertimbangan sebagaimana

### Extraction Examples

- `document_page_pasal_ayat` `ayat`: PBI No.22/23/PBI/2020 - Sistem Pembayaran, hlm. 5, Pasal 5, ayat (1)
  - Flags: `[]`
  - Text: Pasal 5 (1) Penyelenggara jasa Sistem Pembayaran terdiri atas:

- `document_page_pasal` `pasal`: PBI No.22/23/PBI/2020 - Sistem Pembayaran, hlm. 2, Pasal 1
  - Flags: `[]`
  - Text: Pasal 1 Dalam Peraturan Bank Indonesia ini yang dimaksud dengan:

- `document_page_pasal` `table`: PBI No.22/23/PBI/2020 - Sistem Pembayaran, hlm. 5, Pasal 3
  - Flags: `[]`
  - Text: meningkatkan - efektivitas - pengawasan - serta; pengawasan berbasis teknologi - dalam kewajiban

- `document_page` `paragraph`: PBI No.22/23/PBI/2020 - Sistem Pembayaran, hlm. 1
  - Flags: `[]`
  - Text: PERATURAN BANK INDONESIA NOMOR 22/23/PBI/2020 TENTANG SISTEM PEMBAYARAN DENGAN RAHMAT TUHAN YANG MAHA ESA GUBERNUR BANK INDONESIA, Menimbang: a. bahwa perkembangan digitalisasi dan inovasi sistem pembayaran di satu sisi meningkatkan efisiensi industri sistem pembayaran dan percepatan inklusi ekonomi dan keuangan digital, di sisi lain meningkatkan risiko deng

- `document_page` `paragraph`: PBI No.22/23/PBI/2020 - Sistem Pembayaran, hlm. 1
  - Flags: `[]`
  - Text: pembayaran menuntut dilakukannya penataan kembali industri sistem pembayaran melalui reformasi pengaturan sistem pembayaran; c. bahwa diperlukan pengaturan sistem pembayaran yang efektif dan responsif yang meliputi seluruh aspek penyelenggaraan sistem pembayaran guna mengakomodasi perkembangan ekonomi dan keuangan digital; d. bahwa berdasarkan pertimbangan s

- `document_page` `paragraph`: PBI No.22/23/PBI/2020 - Sistem Pembayaran, hlm. 1
  - Flags: `[]`
  - Text: dimaksud dalam huruf a, huruf b, dan huruf c, perlu menetapkan Peraturan Bank Indonesia tentang Sistem Pembayaran


## OJK APU PPT

- Issuer: `OJK`
- Title patterns: `['Anti Pencucian Uang', 'Pencegahan Pendanaan Terorisme']`
- Rows: `7507`
- Documents: `15`
- Section types: `{'pasal': 5051, 'ayat': 708, 'table': 619, 'heading': 618, 'paragraph': 244, 'faq': 103, 'list_item': 99, 'attachment': 39, 'abstrak': 26}`
- Citation quality: `{'document_page_pasal': 6143, 'document_page': 581, 'document_page_pasal_ayat_huruf': 415, 'document_page_pasal_ayat': 368}`
- Issue counts: `{'very_short_text': 1085}`
- Warnings: `['very_short_text']`

### Evidence Probe

- Query: `aturan OJK tentang APU PPT untuk bank`
- Confidence: `strong` score `0.961`

- `OJK` `document_page_pasal_ayat` `ayat`: Penerapan Program Anti Pencucian Uang dan Pencegahan Pendanaan Terorisme di Sektor Perbankan, hlm. 2, Pasal 13, ayat (1)
  - Snippet: 4. Mengacu ke dalam Pasal 13 POJK APU dan PPT, Bank wajib memiliki kebijakan dan prosedur penerapan program APU dan PPT dalam rangka pengelolaan dan mitigasi risiko Pencucian Uang dan/atau Pendanaan Terorisme yang disesuaikan dengan tingkat risiko yang melekat pada masing-masing Bank. 5. Berdasarkan Pasal 67 ayat (1) POJK APU dan PPT, Bank yang telah
- `OJK` `document_page_pasal_ayat` `ayat`: Peraturan Bank Indonesia tentang Penerapan Program Anti Pencucian Uang dan Pencegahan Pendanaan Terorisme bagi Bank Umum, hlm. 6, Pasal 2, ayat (1)
  - Snippet: Pasal 2 (1) Bank wajib menerapkan program APU dan PPT. (2) Dalam penerapan program APU dan PPT, Bank wajib berpedoman pada
- `OJK` `document_page_pasal_ayat` `ayat`: Peraturan Bank Indonesia tentang Penerapan Program Anti Pencucian Uang dan Pencegahan Pendanaan Terorisme bagi Bank Umum, hlm. 8, Pasal 1, ayat (2)
  - Snippet: **(1) (2)** **(1)** **(2)** **a.** **b.** **c.** **- 8 -**
- `OJK` `document_page_pasal_ayat` `ayat`: Penerapan Program Anti Pencucian Uang, Pencegahan Pendanaan Terorisme, dan Pencegahan Pendanaan Proliferasi Senjata Pemusnah Massal di Sektor Jasa Keuangan, hlm. 6, Pasal 2, ayat (1)
  - Snippet: Pasal 2 (1) PJK sebagaimana dimaksud dalam Pasal 1 angka 1 terdiri

### Extraction Examples

- `document_page_pasal_ayat` `ayat`: Penerapan Program Anti Pencucian Uang, Pencegahan Pendanaan Terorisme, dan Pencegahan Pendanaan Proliferasi Senjata Pemusnah Massal bagi Pedagang Aset Keuangan Digital, hlm. 29, Pasal 25, ayat (1)
  - Flags: `[]`
  - Text: 2) Proses verifikasi face to face dapat dikecualikan dengan proses verifikasi tanpa tatap muka (verifikasi non-face to *face) dengan ketentuan sebagai berikut:* a) verifikasi *non-face to face* dilakukan dengan menggunakan perangkat lunak milik Pedagang dengan perangkat keras milik Pedagang atau perangkat keras milik Nasabah atau calon Nasabah. Contoh: peran

- `document_page_pasal` `pasal`: Penerapan Program Anti Pencucian Uang, Pencegahan Pendanaan Terorisme, dan Pencegahan Pendanaan Proliferasi Senjata Pemusnah Massal bagi Pedagang Aset Keuangan Digital, hlm. 25, Pasal 25
  - Flags: `[]`
  - Text: 1) permintaan informasi mengenai calon Nasabah, bukti identitas serta informasi dan/atau dokumen pendukung dari calon Nasabah sebagaimana dimaksud dalam Pasal 25, Pasal 26, Pasal 27, Pasal 28, dan Pasal 29 Peraturan Otoritas Jasa Keuangan mengenai penerapan program APU, PPT, dan PPPSPM di sektor jasa keuangan

- `document_page` `table`: Penerapan Program Anti Pencucian Uang, Pencegahan Pendanaan Terorisme, dan Pencegahan Pendanaan Proliferasi Senjata Pemusnah Massal bagi Pedagang Aset Keuangan Digital, hlm. 3
  - Flags: `[]`
  - Text: mengolah, - menganalisis, - menyimpan, - menampilkan,; mengumumkan, informasi elektronik. - mengirimkan, - dan/atau - menyebarkan

- `document_page` `paragraph`: Penerapan Program Anti Pencucian Uang, Pencegahan Pendanaan Terorisme, dan Pencegahan Pendanaan Proliferasi Senjata Pemusnah Massal bagi Pedagang Aset Keuangan Digital, hlm. 1
  - Flags: `[]`
  - Text: Yth. Direksi Pedagang Aset Keuangan Digital, di tempat. SALINAN SURAT EDARAN OTORITAS JASA KEUANGAN REPUBLIK INDONESIA NOMOR 16/SEOJK.07/2025 TENTANG PENERAPAN PROGRAM ANTI PENCUCIAN UANG, PENCEGAHAN PENDANAAN TERORISME, DAN PENCEGAHAN PENDANAAN PROLIFERASI SENJATA PEMUSNAH MASSAL BAGI PEDAGANG ASET KEUANGAN DIGITAL Sehubungan dengan berlakunya Peraturan Oto

- `document_page` `attachment`: Pedoman Penerapan Program Anti Pencucian Uang dan Pencegahan Pendanaan Terorisme di Sektor Industri Keuangan Non-Bank, hlm. 1
  - Flags: `[]`
  - Text: LAMPIRAN I SURAT EDARAN OTORITAS JASA KEUANGAN NOMOR 37 /SEOJK.05/2017 TENTANG PEDOMAN PENERAPAN PROGRAM ANTI PENCUCIAN UANG DAN PENCEGAHAN PENDANAAN TERORISME DI SEKTOR INDUSTRI KEUANGAN NON BANK

- `document_page` `heading`: Penerapan Program Anti Pencucian Uang, Pencegahan Pendanaan Terorisme, dan Pencegahan Pendanaan Proliferasi Senjata Pemusnah Massal bagi Pedagang Aset Keuangan Digital, hlm. 1
  - Flags: `['very_short_text']`
  - Text: I. KETENTUAN UMUM


## OJK Consumer Protection

- Issuer: `OJK`
- Title patterns: `['Pelindungan Konsumen', 'Perlindungan Konsumen', 'Pengaduan Konsumen']`
- Rows: `3531`
- Documents: `8`
- Section types: `{'pasal': 1829, 'ayat': 720, 'table': 510, 'faq': 225, 'heading': 138, 'paragraph': 76, 'abstrak': 20, 'list_item': 13}`
- Citation quality: `{'document_page_pasal': 2607, 'document_page_pasal_ayat': 468, 'document_page_pasal_ayat_huruf': 294, 'document_page': 162}`
- Issue counts: `{'very_short_text': 632, 'form_placeholder_text': 11}`
- Warnings: `['form_placeholder_text', 'very_short_text']`

### Evidence Probe

- Query: `aturan OJK tentang pelindungan konsumen jasa keuangan`
- Confidence: `partial` score `0.777`

- `OJK` `document_page_pasal_ayat` `ayat`: Pelindungan Konsumen dan Masyarakat di Sektor Jasa Keuangan, hlm. 5, Pasal 3, ayat (1)
  - Snippet: (1) PUJK dalam menyelenggarakan kegiatan usaha wajib menerapkan prinsip Pelindungan Konsumen.
- `OJK` `document_page_pasal` `pasal`: Pelindungan Konsumen dan Masyarakat di Sektor Jasa Keuangan, hlm. 5, Pasal 2
  - Snippet: BAB II KETENTUAN PELINDUNGAN KONSUMEN DAN MASYARAKAT DI SEKTOR JASA KEUANGAN Bagian Kesatu Prinsip Pelindungan Konsumen
- `OJK` `document_page_pasal_ayat` `ayat`: Penilaian Sendiri Terhadap Pemenuhan Ketentuan Pelindungan Konsumen dan Masyarakat di Sektor Jasa Keuangan, hlm. 1, Pasal 87, ayat (4)
  - Snippet: Sehubungan dengan amanat Pasal 87 ayat (4) Peraturan Otoritas Jasa Keuangan Nomor 22 Tahun 2023 tentang Pelindungan Konsumen dan Masyarakat di Sektor Jasa Keuangan (Lembaran Negara Republik Indonesia Tahun 2023 Nomor 40/OJK, Tambahan Lembaran Negara Republik Indonesia Nomor 62/OJK) dan kebutuhan Pelaku Usaha Jasa Keuangan mengenai petunjuk pelaksanaan tentang penilaian sendiri terhadap pemenuhan ketentuan pelindungan...
- `OJK` `document_page_pasal` `faq`: Pelindungan Konsumen dan Masyarakat di Sektor Jasa Keuangan, hlm. 2, Pasal 6
  - Snippet: Berdasarkan Pasal 6 POJK ini dicantumkan apabila terdapat Konsumen yang beriktikad tidak baik maka PUJK berhak atas pelindungan hukum. Contoh dari iktikad tidak baik Konsumen antara lain Konsumen menyerahkan agunan yang bersumber dari tindak

### Extraction Examples

- `document_page_pasal_ayat_huruf` `ayat`: Gugatan oleh Otoritas Jasa Keuangan untuk Pelindungan Konsumen di Sektor Jasa Keuangan, hlm. 1, Pasal 30, ayat (1), huruf b
  - Flags: `[]`
  - Text: Jasa Keuangan berwenang melakukan pembelaan hukum berupa pengajuan gugatan untuk memperoleh kembali harta kekayaan milik pihak yang dirugikan dan/atau untuk memperoleh ganti kerugian dari pihak yang menyebabkan kerugian sesuai ketentuan Pasal 30 ayat (1) huruf b dan Pasal 30 ayat (2) Undang-Undang Nomor 21 Tahun 2011 tentang Otoritas Jasa Keuangan sebagaiman

- `document_page_pasal` `pasal`: Gugatan oleh Otoritas Jasa Keuangan untuk Pelindungan Konsumen di Sektor Jasa Keuangan, hlm. 1, Pasal 30
  - Flags: `[]`
  - Text: dimaksud dalam huruf a dan huruf b, perlu menetapkan Peraturan Otoritas Jasa Keuangan tentang Gugatan oleh Otoritas Jasa Keuangan untuk Pelindungan Konsumen di Sektor Jasa Keuangan; Mengingat: 1. Undang-Undang Nomor 21 Tahun 2011 tentang Otoritas Jasa Keuangan (Lembaran Negara Republik Indonesia Tahun 2011 Nomor 111, Tambahan Lembaran Negara Republik Indones

- `document_page_pasal` `table`: Gugatan oleh Otoritas Jasa Keuangan untuk Pelindungan Konsumen di Sektor Jasa Keuangan, hlm. 2, Pasal 1
  - Flags: `[]`
  - Text: Indonesia, - perusahaan - pembiayaan - sekunder; perumahan, bersama berbasis teknologi informasi, dan lembaga - penyelenggara - layanan - pendanaan

- `document_page` `paragraph`: Gugatan oleh Otoritas Jasa Keuangan untuk Pelindungan Konsumen di Sektor Jasa Keuangan, hlm. 1
  - Flags: `[]`
  - Text: PERATURAN OTORITAS JASA KEUANGAN REPUBLIK INDONESIA NOMOR 38 TAHUN 2025 TENTANG GUGATAN OLEH OTORITAS JASA KEUANGAN UNTUK PELINDUNGAN KONSUMEN DI SEKTOR JASA KEUANGAN DENGAN RAHMAT TUHAN YANG MAHA ESA DEWAN KOMISIONER OTORITAS JASA KEUANGAN, Menimbang: a. bahwa Otoritas Jasa Keuangan dibentuk dengan tujuan agar keseluruhan kegiatan di dalam sektor jasa keuan

- `document_page_pasal` `pasal`: Gugatan oleh Otoritas Jasa Keuangan untuk Pelindungan Konsumen di Sektor Jasa Keuangan, hlm. 2, Pasal 30
  - Flags: `[]`
  - Text: 2. Undang-Undang Nomor 4 Tahun 2023 tentang Pengembangan dan Penguatan Sektor Keuangan (Lembaran Negara Republik Indonesia Tahun 2023 Nomor 4, Tambahan Lembaran Negara Republik Indonesia Nomor 6845); MEMUTUSKAN: Menetapkan: PERATURAN OTORITAS JASA KEUANGAN TENTANG GUGATAN OLEH OTORITAS JASA KEUANGAN UNTUK PELINDUNGAN KONSUMEN DI SEKTOR JASA KEUANGAN.

- `document_page_pasal` `pasal`: Gugatan oleh Otoritas Jasa Keuangan untuk Pelindungan Konsumen di Sektor Jasa Keuangan, hlm. 2, Pasal 30
  - Flags: `['very_short_text']`
  - Text: BAB I KETENTUAN UMUM


## OJK SLIK

- Issuer: `OJK`
- Title patterns: `['Sistem Layanan Informasi Keuangan', 'SLIK', 'Informasi Debitur']`
- Rows: `7024`
- Documents: `6`
- Section types: `{'table': 2409, 'pasal': 2031, 'paragraph': 1029, 'ayat': 795, 'heading': 418, 'list_item': 228, 'faq': 100, 'abstrak': 14}`
- Citation quality: `{'document_page_pasal': 3520, 'document_page': 2747, 'document_page_pasal_ayat_huruf': 580, 'document_page_pasal_ayat': 177}`
- Issue counts: `{'very_short_text': 963, 'form_placeholder_text': 30}`
- Warnings: `['form_placeholder_text', 'high_document_page_only_rate', 'very_short_text']`

### Evidence Probe

- Query: `apa kewajiban bank terkait pelaporan SLIK?`
- Confidence: `strong` score `0.951`

- `OJK` `document_page_pasal_ayat` `ayat`: Pelaporan Melalui Sistem Pelaporan Otoritas Jasa Keuangan dan Transparansi Kondisi Keuangan bagi Bank Perekonomian Rakyat, hlm. 11, Pasal 14, ayat (1)
  - Snippet: ...sangkutan dikenai sanksi administratif berupa denda per jenis Laporan sebagaimana dimaksud dalam Pasal 14 ayat (1) POJK Pelaporan dan TKK BPR dan BPR Syariah, sebesar:
- `OJK` `document_page_pasal_ayat` `ayat`: Pelaporan dan Permintaan Informasi Debitur Melalui Sistem Layanan Informasi Keuangan (SEOJK SLIK), hlm. 11, Pasal 2, ayat (1)
  - Snippet: (1) bagi Debitur perseorangan (a) fotokopi identitas diri dengan menunjukkan identitas diri asli antara lain berupa Kartu Tanda Penduduk (KTP) untuk Warga Negara Indonesia (WNI) atau paspor untuk Warga Negara Asing (WNA); atau (b) surat kuasa asli, fotokopi identitas diri pemberi kuasa dan penerima kuasa dengan menunjukkan identitas diri asli dari pemberi kuasa dan penerima kuasa, dalam hal dikuasakan. (2) bagi Debit...
- `OJK` `document_page_pasal_ayat` `ayat`: Pelaporan Bank Umum Melalui Sistem Pelaporan Otoritas Jasa Keuangan, hlm. 3, Pasal 5, ayat (1)
  - Snippet: Pasal 5 (1) Penunjukan penanggung jawab pelaporan sebagaimana
- `OJK` `document_page_pasal_ayat` `ayat`: Pelaporan Bank Umum Melalui Sistem Pelaporan Otoritas Jasa Keuangan, hlm. 3, Pasal 2, ayat (1)
  - Snippet: Pasal 2 (1) Bank wajib menyusun dan menyampaikan Laporan

### Extraction Examples

- `document_page_pasal_ayat` `ayat`: Perubahan Kedua Atas Peraturan Otoritas Jasa Keuangan Nomor 18/POJK.03/2017 tentang Pelaporan dan Permintaan Informasi Debitur Melalui Sistem Layanan Informasi Keuangan (SLIK), hlm. 4, Pasal 2, ayat (1)
  - Flags: `[]`
  - Text: (1) Pihak yang wajib menjadi Pelapor meliputi:

- `document_page_pasal` `pasal`: Perubahan Kedua Atas Peraturan Otoritas Jasa Keuangan Nomor 18/POJK.03/2017 tentang Pelaporan dan Permintaan Informasi Debitur Melalui Sistem Layanan Informasi Keuangan (SLIK), hlm. 2, Pasal 1
  - Flags: `[]`
  - Text: 1. Ketentuan angka 2, angka 4, angka 5, angka 9, dan angka 12 Pasal 1 diubah, serta di antara angka 6b dan angka 7 disisipkan 5 (lima) angka, yakni angka 6c, angka 6d, angka 6e, angka 6f, dan angka 6g, sehingga Pasal 1 berbunyi sebagai berikut:

- `document_page` `table`: Perubahan Kedua Atas Peraturan Otoritas Jasa Keuangan Nomor 18/POJK.03/2017 tentang Pelaporan dan Permintaan Informasi Debitur Melalui Sistem Layanan Informasi Keuangan (SLIK), hlm. 1
  - Flags: `[]`
  - Text: Nomor - 64/POJK.03/2020 - tentang - Perubahan - atas; Peraturan 18/POJK.03/2017 tentang Pelaporan dan Permintaan - Otoritas - Jasa - Keuangan - Nomor

- `document_page` `paragraph`: Perubahan Kedua Atas Peraturan Otoritas Jasa Keuangan Nomor 18/POJK.03/2017 tentang Pelaporan dan Permintaan Informasi Debitur Melalui Sistem Layanan Informasi Keuangan (SLIK), hlm. 1
  - Flags: `[]`
  - Text: SALINAN PERATURAN OTORITAS JASA KEUANGAN REPUBLIK INDONESIA NOMOR 11 TAHUN 2024 TENTANG PERUBAHAN KEDUA ATAS PERATURAN OTORITAS JASA KEUANGAN NOMOR 18/POJK.03/2017 TENTANG PELAPORAN DAN PERMINTAAN INFORMASI DEBITUR MELALUI SISTEM LAYANAN INFORMASI KEUANGAN DENGAN RAHMAT TUHAN YANG MAHA ESA DEWAN KOMISIONER OTORITAS JASA KEUANGAN, Menimbang: a. bahwa untuk me

- `document_page` `paragraph`: Perubahan Kedua Atas Peraturan Otoritas Jasa Keuangan Nomor 18/POJK.03/2017 tentang Pelaporan dan Permintaan Informasi Debitur Melalui Sistem Layanan Informasi Keuangan (SLIK), hlm. 1
  - Flags: `[]`
  - Text: komprehensif diperlukan penambahan informasi pendukung aktivitas penyediaan dana, meliputi pertanggungan/pengelolaan risiko, penjaminan, dan layanan pendanaan bersama berbasis teknologi informasi yang diberikan oleh sektor perasuransian, modal ventura, lembaga keuangan mikro, lembaga pembiayaan, dan lembaga jasa keuangan lainnya; b. bahwa dengan adanya penam

- `document_page` `paragraph`: Perubahan Kedua Atas Peraturan Otoritas Jasa Keuangan Nomor 18/POJK.03/2017 tentang Pelaporan dan Permintaan Informasi Debitur Melalui Sistem Layanan Informasi Keuangan (SLIK), hlm. 1
  - Flags: `[]`
  - Text: informasi yang dilaporkan sebagaimana dimaksud dalam huruf a, perlu dilakukan penyesuaian terhadap Peraturan Otoritas Jasa Keuangan Nomor 18/POJK.03/2017 tentang Pelaporan dan Permintaan Informasi Debitur melalui Sistem Layanan Informasi Keuangan sebagaimana telah diubah dengan Peraturan Otoritas Jasa Keuangan


## OJK BPR BPRS

- Issuer: `OJK`
- Title patterns: `['Bank Perekonomian Rakyat', 'Bank Perkreditan Rakyat', 'BPR', 'BPRS']`
- Rows: `45142`
- Documents: `89`
- Section types: `{'pasal': 23508, 'table': 5828, 'heading': 5594, 'ayat': 4147, 'paragraph': 2660, 'list_item': 1689, 'faq': 1034, 'attachment': 413, 'abstrak': 269}`
- Citation quality: `{'document_page_pasal': 33163, 'document_page': 7563, 'document_page_pasal_ayat': 2540, 'document_page_pasal_ayat_huruf': 1876}`
- Issue counts: `{'very_short_text': 8502, 'form_placeholder_text': 243}`
- Warnings: `['form_placeholder_text', 'very_short_text']`

### Evidence Probe

- Query: `aturan OJK untuk BPR dan BPRS`
- Confidence: `strong` score `0.888`

- `OJK` `document_page_pasal_ayat` `ayat`: Bank Perekonomian Rakyat dan Bank Perekonomian Rakyat Syariah, hlm. 1, Pasal 16, ayat (3)
  - Snippet: SALINAN PERATURAN OTORITAS JASA KEUANGAN REPUBLIK INDONESIA NOMOR 7 TAHUN 2024 TENTANG BANK PEREKONOMIAN RAKYAT DAN BANK PEREKONOMIAN RAKYAT SYARIAH DENGAN RAHMAT TUHAN YANG MAHA ESA DEWAN KOMISIONER OTORITAS JASA KEUANGAN, Menimbang: bahwa untuk melaksanakan ketentuan Pasal 16 ayat (3), Pasal 18 ayat (3), Pasal 19A ayat (2), Pasal 23 ayat (3), Pasal 28 ayat (4), Pasal 28A ayat (3), dan Pasal 37 ayat (6) Undang-Undan...
- `OJK` `document_page_pasal_ayat` `ayat`: Kualitas Aset Bank Perekonomian Rakyat Syariah, hlm. 5, Pasal 3, ayat (1)
  - Snippet: Pasal 3 (1) BPR Syariah wajib melakukan penilaian dan penetapan
- `OJK` `document_page` `paragraph`: Penyelenggaraan Produk Bank Perekonomian Rakyat Syariah, hlm. 1
  - Snippet: ... Edaran Otoritas Jasa Keuangan ini yang dimaksud dengan: a. Bank Perekonomian Rakyat Syariah yang selanjutnya disingkat BPRS adalah jenis bank syariah yang dalam kegiatannya tidak memberikan jasa dalam lalu lintas giral secara langsung.
- `OJK` `document_page_pasal_ayat` `ayat`: Penyelenggaraan Teknologi Informasi oleh Bank Perekonomian Rakyat dan Bank Perekonomian Rakyat Syariah, hlm. 3, Pasal 2, ayat (1)
  - Snippet: (1) BPR dan BPR Syariah wajib menerapkan tata kelola TI yang baik dalam penyelenggaraan TI. (2) Dalam menerapkan tata kelola TI yang baik sebagaimana dimaksud pada ayat (1), BPR dan BPR Syariah mempertimbangkan faktor paling sedikit:

### Extraction Examples

- `document_page_pasal_ayat` `ayat`: Penyelenggaraan Teknologi Informasi oleh Bank Perekonomian Rakyat dan Bank Perekonomian Rakyat Syariah, hlm. 3, Pasal 2, ayat (1)
  - Flags: `[]`
  - Text: (1) BPR dan BPR Syariah wajib menerapkan tata kelola TI yang baik dalam penyelenggaraan TI. (2) Dalam menerapkan tata kelola TI yang baik sebagaimana dimaksud pada ayat (1), BPR dan BPR Syariah mempertimbangkan faktor paling sedikit:

- `document_page_pasal` `pasal`: Penyelenggaraan Teknologi Informasi oleh Bank Perekonomian Rakyat dan Bank Perekonomian Rakyat Syariah, hlm. 2, Pasal 1
  - Flags: `['very_short_text']`
  - Text: Pasal 1

- `document_page` `table`: Penyelenggaraan Teknologi Informasi oleh Bank Perekonomian Rakyat dan Bank Perekonomian Rakyat Syariah, hlm. 1
  - Flags: `[]`
  - Text: penyelenggaraan - teknologi - informasi - sehingga; Peraturan - Jasa 75/POJK.03/2016 tentang Standar Penyelenggaraan - Keuangan - Nomor

- `document_page` `paragraph`: Penyelenggaraan Teknologi Informasi oleh Bank Perekonomian Rakyat dan Bank Perekonomian Rakyat Syariah, hlm. 1
  - Flags: `[]`
  - Text: PERATURAN OTORITAS JASA KEUANGAN REPUBLIK INDONESIA NOMOR 34 TAHUN 2025 TENTANG PENYELENGGARAAN TEKNOLOGI INFORMASI OLEH BANK PEREKONOMIAN RAKYAT DAN BANK PEREKONOMIAN RAKYAT SYARIAH DENGAN RAHMAT TUHAN YANG MAHA ESA DEWAN KOMISIONER OTORITAS JASA KEUANGAN, Menimbang: a. bahwa untuk mendukung proses bisnis dalam melakukan aktivitas operasional guna meningkat

- `document_page` `attachment`: Rencana Bisnis Bank Perkreditan Rakyat, hlm. 1
  - Flags: `[]`
  - Text: LAMPIRAN SURAT EDARAN OTORITAS JASA KEUANGAN NOMOR 52 /SEOJK.03/2016 TENTANG RENCANA BISNIS BANK PERKREDITAN RAKYAT

- `document_page` `paragraph`: Penyelenggaraan Teknologi Informasi oleh Bank Perekonomian Rakyat dan Bank Perekonomian Rakyat Syariah, hlm. 1
  - Flags: `[]`
  - Text: pemanfaatan teknologi informasi, diperlukan penguatan pengaturan aspek tata kelola, manajemen risiko, serta ketahanan dan keamanan siber dalam


## OJK Modal Ventura

- Issuer: `OJK`
- Title patterns: `['Modal Ventura']`
- Rows: `18403`
- Documents: `24`
- Section types: `{'pasal': 11209, 'table': 2892, 'ayat': 2678, 'heading': 857, 'faq': 500, 'abstrak': 200, 'paragraph': 62, 'list_item': 5}`
- Citation quality: `{'document_page_pasal': 15074, 'document_page_pasal_ayat': 1720, 'document_page_pasal_ayat_huruf': 1273, 'document_page': 336}`
- Issue counts: `{'very_short_text': 2883, 'form_placeholder_text': 68}`
- Warnings: `['form_placeholder_text', 'very_short_text']`

### Evidence Probe

- Query: `aturan penyelenggaraan usaha perusahaan modal ventura`
- Confidence: `strong` score `0.98`

- `OJK` `document_page_pasal_ayat` `ayat`: Penyelenggaraan Usaha Perusahaan Modal Ventura dan Perusahaan Modal Ventura Syariah, hlm. 1, Pasal 106, ayat (6)
  - Snippet: OTORITAS JASA KEUANGAN REPUBLIK INDONESIA SALINAN PERATURAN OTORITAS JASA KEUANGAN REPUBLIK INDONESIA NOMOR 25 TAHUN 2023 TENTANG PENYELENGGARAAN USAHA PERUSAHAAN MODAL VENTURA DAN PERUSAHAAN MODAL VENTURA SYARIAH DENGAN RAHMAT TUHAN YANG MAHA ESA DEWAN KOMISIONER OTORITAS JASA KEUANGAN, Menimbang: bahwa untuk melaksanakan amanat Pasal 106 ayat (6),
- `OJK` `document_page_pasal_ayat` `ayat`: POJK tentang Penyelenggaraan Usaha Perusahaan Modal Ventura, hlm. 6, Pasal 2, ayat (1)
  - Snippet: Pasal 2 (1) PMV menyelenggarakan Usaha Modal Ventura yang
- `OJK` `document_page_pasal_ayat` `ayat`: POJK tentang Perizinan Usaha dan Kelembagaan Perusahaan Modal Ventura, hlm. 7, Pasal 2, ayat (1)
  - Snippet: Pasal 2 (1) PMV dan PMVS harus didirikan dalam bentuk badan
- `OJK` `document_page_pasal_ayat` `faq`: Penyelenggaraan Usaha Perusahaan Modal Ventura dan Perusahaan Modal Ventura Syariah, hlm. 1, Pasal 106, ayat (6)
  - Snippet: ...engembangan dan Penguatan Sektor Keuangan dan dalam rangka mendukung perkembangan industri dan kebutuhan hukum terhadap penyelenggaraan usaha perusahaan modal ventura, yang berdampak pada perlu disesuaikannya Peraturan Otoritas Jasa Keuangan Nomor 35/POJK.05/2015 tentang Penyelenggaraan Usaha Perusahaan Modal Ventura dan Perusahaan Modal Ventura Syariah.

### Extraction Examples

- `document_page_pasal_ayat` `ayat`: Perubahan Atas Surat Edaran Otoritas Jasa Keuangan Nomor 25/SEOJK.05/2019 tentang Laporan Bulanan Perusahaan Modal Ventura dan Perusahaan Modal Ventura Syariah, hlm. 1, Pasal 128, ayat (4)
  - Flags: `[]`
  - Text: Sehubungan dengan amanat Pasal 128 ayat (4) Peraturan Otoritas Jasa Keuangan Nomor 25 Tahun 2023 tentang Penyelenggaraan Usaha Perusahaan Modal Ventura dan Perusahaan Modal Ventura Syariah (Lembaran Negara Republik Indonesia Tahun 2023 Nomor 43/OJK, Tambahan Lembaran Negara Republik Indonesia Nomor 65/OJK) dan mengingat adanya kebutuhan penyempurnaan pos-pos

- `document_page_pasal` `pasal`: Perubahan Atas Surat Edaran Otoritas Jasa Keuangan Nomor 25/SEOJK.05/2019 tentang Laporan Bulanan Perusahaan Modal Ventura dan Perusahaan Modal Ventura Syariah, hlm. 1, Pasal 128
  - Flags: `[]`
  - Text: 1. Ketentuan Romawi V diubah sehingga berbunyi sebagai berikut: 1. Penyampaian Laporan Bulanan disampaikan kepada Otoritas Jasa Keuangan secara daring melalui sistem jaringan komunikasi data Otoritas Jasa Keuangan. 2. Dalam menyampaikan Laporan Bulanan sebagaimana dimaksud pada angka 1, petugas penyusun sebagaimana dimaksud dalam Romawi IV angka 2 harus memi

- `document_page_pasal` `table`: Perubahan Atas Surat Edaran Otoritas Jasa Keuangan Nomor 25/SEOJK.05/2019 tentang Laporan Bulanan Perusahaan Modal Ventura dan Perusahaan Modal Ventura Syariah, hlm. 3, Pasal 128
  - Flags: `[]`
  - Text: a. Kepala Departemen Pengawasan Lembaga Pembiayaan, Perusahaan Modal Ventura, dan Lembaga Keuangan Khusus bagi Perusahaan dan UUS yang berkantor pusat di wilayah Jakarta, Bogor, Depok, Tangerang, Bekasi; atau b. Kepala Kantor OJK setempat sesuai dengan wilayah tempat kedudukan kantor pusat Perusahaan dan UUS.

- `document_page` `paragraph`: Perubahan Atas Surat Edaran Otoritas Jasa Keuangan Nomor 25/SEOJK.05/2019 tentang Laporan Bulanan Perusahaan Modal Ventura dan Perusahaan Modal Ventura Syariah, hlm. 1
  - Flags: `[]`
  - Text: Yth. 1. Direksi Perusahaan Modal Ventura; dan 2. Direksi Perusahaan Modal Ventura Syariah, di tempat. SALINAN SURAT EDARAN OTORITAS JASA KEUANGAN REPUBLIK INDONESIA NOMOR 23/SEOJK.06/2025 TENTANG PERUBAHAN ATAS SURAT EDARAN OTORITAS JASA KEUANGAN NOMOR 25/SEOJK.05/2019 TENTANG LAPORAN BULANAN PERUSAHAAN MODAL VENTURA DAN PERUSAHAAN MODAL VENTURA SYARIAH

- `document_page_pasal` `heading`: Perubahan Atas Surat Edaran Otoritas Jasa Keuangan Nomor 25/SEOJK.05/2019 tentang Laporan Bulanan Perusahaan Modal Ventura dan Perusahaan Modal Ventura Syariah, hlm. 1, Pasal 128
  - Flags: `[]`
  - Text: I. Beberapa ketentuan dalam Surat Edaran Otoritas Jasa Keuangan Nomor 25/SEOJK.05/2019 tentang Laporan Bulanan Perusahaan Modal Ventura dan Perusahaan Modal Ventura Syariah, diubah sebagai berikut:

- `document_page_pasal` `pasal`: Perubahan Atas Surat Edaran Otoritas Jasa Keuangan Nomor 25/SEOJK.05/2019 tentang Laporan Bulanan Perusahaan Modal Ventura dan Perusahaan Modal Ventura Syariah, hlm. 1, Pasal 128
  - Flags: `[]`
  - Text: 4. Dalam hal Perusahaan melakukan perubahan alamat surat elektronik pengguna (email user) sebagaimana dimaksud pada angka 3, Direksi harus menyampaikan permohonan perubahan akses sistem jaringan komunikasi data Otoritas Jasa Keuangan sebagaimana dimaksud pada angka 2 sesuai dengan format 3 sebagaimana tercantum dalam Lampiran IV yang merupakan bagian tidak t


## OJK Perusahaan Pembiayaan

- Issuer: `OJK`
- Title patterns: `['Perusahaan Pembiayaan']`
- Rows: `30742`
- Documents: `44`
- Section types: `{'pasal': 18306, 'ayat': 3941, 'table': 3703, 'heading': 2300, 'attachment': 1524, 'paragraph': 435, 'abstrak': 282, 'faq': 200, 'list_item': 51}`
- Citation quality: `{'document_page_pasal': 23755, 'document_page': 2596, 'document_page_pasal_ayat': 2339, 'document_page_pasal_ayat_huruf': 2052}`
- Issue counts: `{'very_short_text': 4675, 'form_placeholder_text': 125}`
- Warnings: `['form_placeholder_text', 'very_short_text']`

### Evidence Probe

- Query: `aturan OJK tentang perusahaan pembiayaan`
- Confidence: `strong` score `0.992`

- `OJK` `document_page_pasal_ayat` `ayat`: Laporan Bulanan Perusahaan Pembiayaan dan Perusahaan Pembiayaan Syariah, hlm. 3, Pasal 2, ayat (1)
  - Snippet: Pasal 2 (1) Kewajiban Perusahaan Pembiayaan untuk
- `OJK` `document_page_pasal_ayat` `ayat`: Permohonan Perizinan, Persetujuan, dan Pelaporan Secara Elektronik bagi Perusahaan Pembiayaan dan Perusahaan Pembiayaan Syariah, hlm. 1, Pasal 114, ayat (5)
  - Snippet: Yth. 1. Direksi Perusahaan Pembiayaan; dan 2. Direksi Perusahaan Pembiayaan Syariah, di tempat. SALINAN SURAT EDARAN OTORITAS JASA KEUANGAN REPUBLIK INDONESIA NOMOR 20/SEOJK.06/2023 TENTANG PERMOHONAN PERIZINAN, PERSETUJUAN, DAN PELAPORAN SECARA ELEKTRONIK BAGI PERUSAHAAN PEMBIAYAAN DAN PERUSAHAAN PEMBIAYAAN SYARIAH Sehubungan dengan amanat Pasal 114 ayat (5) Peraturan Otoritas Jasa Keuangan Nomor 47/POJK.05/2020 ten...
- `OJK` `document_page_pasal_ayat` `ayat`: Laporan Bulanan Perusahaan Pembiayaan Syariah dan Unit Usaha Syariah dari Perusahaan Pembiayaan, hlm. 1, Pasal 2, ayat (6)
  - Snippet: Yth. 1. Direksi atau yang setara pada Perusahaan Pembiayaan Syariah; dan 2. Direksi atau yang setara pada Perusahaan Pembiayaan yang mempunyai Unit Usaha Syariah, di tempat. SALINAN SURAT EDARAN OTORITAS JASA KEUANGAN NOMOR 4/SEOJK.05/2016 TENTANG LAPORAN BULANAN PERUSAHAAN PEMBIAYAAN SYARIAH DAN UNIT USAHA SYARIAH DARI PERUSAHAAN PEMBIAYAAN Sehubungan dengan amanat Pasal 2 ayat (6), Pasal 4 ayat (6), dan Pasal 10 Pe...
- `OJK` `document_page_pasal_ayat` `ayat`: Perizinan Usaha dan Kelembagaan Perusahaan Pembiayaan, hlm. 7, Pasal 3, ayat (2)
  - Snippet: Pasal 3 ayat (2), harus diajukan oleh Direksi kepada OJK dengan menggunakan format 1 sebagaimana tercantum dalam Lampiran yang merupakan bagian tidak terpisahkan dari Peraturan OJK ini. (2) Pengajuan permohonan izin usaha sebagaimana

### Extraction Examples

- `document_page_pasal_ayat` `ayat`: Laporan Bulanan Perusahaan Pembiayaan dan Perusahaan Pembiayaan Syariah, hlm. 3, Pasal 2, ayat (1)
  - Flags: `[]`
  - Text: Pasal 2 (1) Kewajiban Perusahaan Pembiayaan untuk

- `document_page_pasal` `pasal`: Laporan Bulanan Perusahaan Pembiayaan dan Perusahaan Pembiayaan Syariah, hlm. 3, Pasal 1
  - Flags: `['very_short_text']`
  - Text: Pasal 1

- `document_page` `table`: Laporan Bulanan Perusahaan Pembiayaan dan Perusahaan Pembiayaan Syariah, hlm. 1
  - Flags: `[]`
  - Text: LAPORAN BULANAN - PERUSAHAAN PEMBIAYAAN - DAN PERUSAHAAN; PEMBIAYAAN - SYARIAH

- `document_page` `paragraph`: Laporan Bulanan Perusahaan Pembiayaan dan Perusahaan Pembiayaan Syariah, hlm. 1
  - Flags: `[]`
  - Text: SALINAN PERATURAN ANGGOTA DEWAN KOMISIONER OTORITAS JASA KEUANGAN REPUBLIK INDONESIA NOMOR 45/PADK.06/2025 TENTANG

- `document_page` `attachment`: Laporan Bulanan Perusahaan Pembiayaan Syariah dan Unit Usaha Syariah dari Perusahaan Pembiayaan, hlm. 1
  - Flags: `[]`
  - Text: LAMPIRAN I SURAT EDARAN OTORITAS JASA KEUANGAN NOMOR 4/SEOJK.05/2016 TENTANG LAPORAN BULANAN PERUSAHAAN PEMBIAYAAN SYARIAH DAN UNIT USAHA SYARIAH DARI PERUSAHAAN PEMBIAYAAN

- `document_page` `paragraph`: Laporan Bulanan Perusahaan Pembiayaan dan Perusahaan Pembiayaan Syariah, hlm. 1
  - Flags: `[]`
  - Text: DENGAN RAHMAT TUHAN YANG MAHA ESA ANGGOTA DEWAN KOMISIONER OTORITAS JASA KEUANGAN, Menimbang: a. bahwa untuk kebutuhan pelaporan terhadap pembiayaan dan perusahaan pembiayaan syariah, perlu dilakukan penyempurnaan terhadap ketentuan mengenai laporan bulanan perusahaan pembiayaan sebagaimana telah diatur dalam Surat Edaran Otoritas Jasa Keuangan Nomor 3/SEOJK


## OJK Aset Keuangan Digital

- Issuer: `OJK`
- Title patterns: `['Aset Keuangan Digital', 'Aset Kripto']`
- Rows: `5804`
- Documents: `6`
- Section types: `{'pasal': 2864, 'table': 757, 'ayat': 679, 'heading': 517, 'paragraph': 368, 'list_item': 300, 'faq': 275, 'abstrak': 44}`
- Citation quality: `{'document_page_pasal': 3969, 'document_page': 1097, 'document_page_pasal_ayat_huruf': 408, 'document_page_pasal_ayat': 330}`
- Issue counts: `{'very_short_text': 953, 'form_placeholder_text': 256}`
- Warnings: `['form_placeholder_text', 'very_short_text']`

### Evidence Probe

- Query: `aturan OJK tentang perdagangan aset keuangan digital termasuk aset kripto`
- Confidence: `partial` score `0.756`

- `OJK` `document_page_pasal_ayat` `ayat`: Penyelenggaraan Perdagangan Aset Keuangan Digital Termasuk Aset Kripto, hlm. 14, Pasal 12, ayat (1)
  - Snippet: PEMBERITAHUAN DIMULAINYA PERDAGANGAN ASET KRIPTO Dalam rangka melaksanakan amanat Pasal 12 ayat (1) POJK Nomor … tentang Penyelenggaraan Perdagangan Aset Keuangan Digital termasuk Aset Kripto terkait kewajiban Pedagang untuk memberitahukan dimulainya perdagangan Aset Kripto kepada Otoritas Jasa Keuangan, kami yang bertandatangan di bawah ini: Nama Pedagang: Kode Pedagang:
- `OJK` `document_page_pasal_ayat` `ayat`: Penyelenggaraan Perdagangan Aset Keuangan Digital Termasuk Aset Kripto, hlm. 1, Pasal 312, ayat (1)
  - Snippet: SALINAN PERATURAN OTORITAS JASA KEUANGAN REPUBLIK INDONESIA NOMOR 27 TAHUN 2024 TENTANG PENYELENGGARAAN PERDAGANGAN ASET KEUANGAN DIGITAL TERMASUK ASET KRIPTO DENGAN RAHMAT TUHAN YANG MAHA ESA DEWAN KOMISIONER OTORITAS JASA KEUANGAN, Menimbang: a. bahwa untuk mendukung perkembangan sektor jasa keuangan dan melaksanakan kewenangan pengaturan dan pengawasan sebagaimana dimaksud dalam Undang-Undang Nomor 4 Tahun 2023 te...
- `OJK` `document_page` `faq`: Penyelenggaraan Perdagangan Aset Keuangan Digital Termasuk Aset Kripto, hlm. 1
  - Snippet: Digital; dan g) mekanisme dan tata cara penyampaian pemberitahuan perdagangan Aset Kripto, hasil evaluasi atas Aset Kripto dalam Daftar Aset Kripto, rencana bisnis Penyelenggara Perdagangan Aset Keuangan Digital, serta Laporan Berkala dan Laporan Insidental.
- `OJK` `document_page_pasal_ayat` `faq`: Penyelenggaraan Perdagangan Aset Keuangan Digital Termasuk Aset Kripto, hlm. 1, Pasal 8, ayat (1)
  - Snippet: POJK ini disusun dalam rangka menjalankan amanat peralihan tugas pengaturan dan pengawasan terkait Aset Keuangan Digital termasuk Aset Kripto sebagaimana tercantum dalam Undang-Undang Nomor 4 Tahun 2023 tentang Pengembangan dan Penguatan Sektor Keuangan (UU P2SK), dengan ketentuan antara lain sebagai berikut: a. Pasal 8 ayat (1) dan Pasal 216 ayat (1) UU P2SK, yang pada pokoknya menyatakan bahwa OJK melaksanakan tuga...

### Extraction Examples

- `document_page_pasal_ayat` `ayat`: Rencana Bisnis Penyelenggara Perdagangan Aset Keuangan Digital, hlm. 1, Pasal 76, ayat (8)
  - Flags: `[]`
  - Text: Yth. Direksi Penyelenggara Perdagangan Aset Keuangan Digital, di tempat. SALINAN SURAT EDARAN OTORITAS JASA KEUANGAN REPUBLIK INDONESIA NOMOR 34/SEOJK.07/2025 TENTANG RENCANA BISNIS PENYELENGGARA PERDAGANGAN ASET KEUANGAN DIGITAL Sehubungan dengan amanat Pasal 76 ayat (8) Peraturan Otoritas Jasa Keuangan Nomor 27 Tahun 2024 tentang Penyelenggara Perdagangan 

- `document_page_pasal` `pasal`: Rencana Bisnis Penyelenggara Perdagangan Aset Keuangan Digital, hlm. 1, Pasal 76
  - Flags: `[]`
  - Text: 1. Aset Keuangan Digital adalah aset keuangan yang disimpan atau direpresentasikan secara digital, termasuk di dalamnya aset kripto. 2. Aset Kripto adalah representasi digital dari nilai yang dapat disimpan dan ditransfer menggunakan teknologi yang memungkinkan penggunaan buku besar terdistribusi seperti *blockchain untuk memverifikasi transaksinya dan memas

- `document_page_pasal` `table`: Rencana Bisnis Penyelenggara Perdagangan Aset Keuangan Digital, hlm. 3, Pasal 76
  - Flags: `[]`
  - Text: a. produk, aktivitas, dan layanan yang akan ditawarkan; b. target jumlah konsumen; c. target nilai dan volume perdagangan; dan d. informasi lainnya (jika ada).

- `document_page` `paragraph`: Perubahan Atas Peraturan Otoritas Jasa Keuangan Nomor 27 Tahun 2024 tentang Penyelenggaraan Perdagangan Aset Keuangan Digital Termasuk Aset Kripto, hlm. 1
  - Flags: `[]`
  - Text: PERATURAN OTORITAS JASA KEUANGAN REPUBLIK INDONESIA NOMOR 23 TAHUN 2025 TENTANG PERUBAHAN ATAS PERATURAN OTORITAS JASA KEUANGAN NOMOR 27 TAHUN 2024 TENTANG PENYELENGGARAAN PERDAGANGAN ASET KEUANGAN DIGITAL TERMASUK ASET KRIPTO DENGAN RAHMAT TUHAN YANG MAHA ESA DEWAN KOMISIONER OTORITAS JASA KEUANGAN, Menimbang: a. bahwa dengan berkembangnya pasar atas produk

- `document_page_pasal` `heading`: Rencana Bisnis Penyelenggara Perdagangan Aset Keuangan Digital, hlm. 1, Pasal 76
  - Flags: `[]`
  - Text: I. KETENTUAN UMUM Dalam Surat Edaran Otoritas Jasa Keuangan ini yang dimaksud dengan:

- `document_page_pasal` `pasal`: Rencana Bisnis Penyelenggara Perdagangan Aset Keuangan Digital, hlm. 1, Pasal 76
  - Flags: `[]`
  - Text: 3. Penyelenggara Bursa Aset Keuangan Digital termasuk Aset Kripto yang selanjutnya disebut Bursa adalah badan usaha yang menyelenggarakan dan menyediakan sistem dan/atau sarana untuk memfasilitasi kegiatan terkait perdagangan Aset Keuangan
