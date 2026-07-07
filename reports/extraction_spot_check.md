# Extraction Spot Check

Focused review of high-value regulation areas using the current citation-ready source corpus.

- Source: `processed/source_corpus.ndjson`

## Summary

| Target | Rows | Documents | Page rate | Pasal/Ayat rate | Table rate | Warnings |
|---|---:|---:|---:|---:|---:|---|
| BI PJP | 2099 | 3 | 1.0 | 0.98 | 0.146 | `markdown_table_artifact`, `very_short_text` |
| BI PIP | 1616 | 3 | 1.0 | 0.979 | 0.116 | `markdown_table_artifact`, `very_short_text` |
| BI Sistem Pembayaran | 3044 | 6 | 1.0 | 0.984 | 0.102 | `markdown_table_artifact`, `very_short_text` |
| OJK APU PPT | 7378 | 15 | 1.0 | 0.93 | 0.084 | `markdown_table_artifact`, `very_short_text` |
| OJK Consumer Protection | 3286 | 8 | 1.0 | 0.962 | 0.155 | `form_placeholder_text`, `markdown_table_artifact`, `very_short_text` |
| OJK SLIK | 6910 | 6 | 1.0 | 0.621 | 0.349 | `form_placeholder_text`, `high_document_page_only_rate`, `markdown_table_artifact`, `very_short_text` |
| OJK BPR BPRS | 43839 | 89 | 1.0 | 0.855 | 0.133 | `form_placeholder_text`, `markdown_table_artifact`, `very_short_text` |
| OJK Modal Ventura | 17703 | 24 | 1.0 | 0.995 | 0.163 | `form_placeholder_text`, `markdown_table_artifact`, `very_short_text` |
| OJK Perusahaan Pembiayaan | 29818 | 43 | 1.0 | 0.926 | 0.123 | `form_placeholder_text`, `markdown_table_artifact`, `very_short_text` |
| OJK Aset Keuangan Digital | 5485 | 6 | 1.0 | 0.843 | 0.138 | `form_placeholder_text`, `markdown_table_artifact`, `very_short_text` |

## BI PJP

- Issuer: `BI`
- Title patterns: `['Penyedia Jasa Pembayaran', 'PBI No.23/6/PBI/2021']`
- Rows: `2099`
- Documents: `3`
- Section types: `{'pasal': 1102, 'ayat': 587, 'table': 306, 'heading': 84, 'paragraph': 18, 'list_item': 2}`
- Citation quality: `{'document_page_pasal': 1454, 'document_page_pasal_ayat': 602, 'document_page': 43}`
- Issue counts: `{'very_short_text': 625, 'markdown_table_artifact': 306}`
- Warnings: `['markdown_table_artifact', 'very_short_text']`

### Evidence Probe

- Query: `peraturan BI tentang penyedia jasa pembayaran apa saja?`
- Confidence: `strong` score `0.964`

- `BI` `document_page_pasal_ayat` `ayat`: PBI No.23/6/PBI/2021 - Penyedia Jasa Pembayaran, hlm. 4, Pasal 1, ayat (1)
  - Snippet: (1) PJP menyelenggarakan aktivitas yang meliputi:
- `BI` `document_page` `paragraph`: PBI No.23/6/PBI/2021 - Penyedia Jasa Pembayaran, hlm. 2
  - Snippet: 2. Peraturan Bank Indonesia Nomor 22/23/PBI/2020 tentang Sistem Pembayaran (Lembaran Negara Republik Indonesia Tahun 2020 Nomor 311, Tambahan Lembaran Negara Republik Indonesia Nomor 6610); MEMUTUSKAN: Menetapkan : PERATURAN BANK INDONESIA TENTANG PENYEDIA JASA PEMBAYARAN. BAB I KETENTUAN UMUM
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
  - Flags: `['markdown_table_artifact']`
  - Text: | pengaturan | akses | ke | industri, | penyelenggaraan, | |---|---|---|---|---| | pengakhiran penyelenggaraan kegiatan, | | | | pengawasan, |

- `document_page` `paragraph`: PBI No.23/6/PBI/2021 - Penyedia Jasa Pembayaran, hlm. 1
  - Flags: `[]`
  - Text: PERATURAN BANK INDONESIA NOMOR 23/6/PBI/2021 TENTANG PENYEDIA JASA PEMBAYARAN DENGAN RAHMAT TUHAN YANG MAHA ESA GUBERNUR BANK INDONESIA, Menimbang : a. bahwa reformasi pengaturan sistem pembayaran termasuk penyediaan jasa pembayaran, perlu dilakukan sejalan dengan pemenuhan prinsip penyelenggaraan sistem pembayaran yang cepat, mudah, murah, aman, dan andal, 

- `document_page` `paragraph`: PBI No.23/6/PBI/2021 - Penyedia Jasa Pembayaran, hlm. 1
  - Flags: `[]`
  - Text: mengakomodasi perkembangan model bisnis dan inovasi penyediaan jasa pembayaran dari penyelenggara kepada pengguna jasa, serta keterhubungan dengan penyelenggara atau pihak lain dalam penyelenggaraan sistem pembayaran dalam mendukung digitalisasi ekonomi dan keuangan; c. bahwa perkembangan aktivitas penyediaan jasa sistem pembayaran menuntut dilakukannya peng

- `document_page` `paragraph`: PBI No.23/6/PBI/2021 - Penyedia Jasa Pembayaran, hlm. 1
  - Flags: `[]`
  - Text: dan pemrosesan data dan/atau informasi sistem pembayaran;


## BI PIP

- Issuer: `BI`
- Title patterns: `['Penyelenggara Infrastruktur Sistem Pembayaran', 'PBI No.23/7/PBI/2021']`
- Rows: `1616`
- Documents: `3`
- Section types: `{'pasal': 905, 'ayat': 469, 'table': 188, 'heading': 41, 'paragraph': 13}`
- Citation quality: `{'document_page_pasal': 1105, 'document_page_pasal_ayat': 477, 'document_page': 34}`
- Issue counts: `{'very_short_text': 525, 'markdown_table_artifact': 188}`
- Warnings: `['markdown_table_artifact', 'very_short_text']`

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
  - Flags: `['markdown_table_artifact']`
  - Text: | a. | Kliring; dan/atau | |---|---| | b. | Penyelesaian Akhir, | | bagi | kepentingan anggota PIP. |

- `document_page` `paragraph`: PBI No.23/7/PBI/2021 - Penyelenggara Infrastruktur Sistem Pembayaran, hlm. 1
  - Flags: `[]`
  - Text: PERATURAN BANK INDONESIA NOMOR 23/7/PBI/2021 TENTANG PENYELENGGARA INFRASTRUKTUR SISTEM PEMBAYARAN DENGAN RAHMAT TUHAN YANG MAHA ESA GUBERNUR BANK INDONESIA, Menimbang : a. bahwa reformasi pengaturan sistem pembayaran bertujuan untuk mencari titik keseimbangan antara upaya optimalisasi peluang inovasi digital untuk menciptakan sistem pembayaran yang cepat, m

- `document_page` `paragraph`: PBI No.23/7/PBI/2021 - Penyelenggara Infrastruktur Sistem Pembayaran, hlm. 1
  - Flags: `[]`
  - Text: mengakomodasi kebutuhan pengaturan berdasarkan perkembangan inovasi dan model bisnis di bidang sistem pembayaran dan penyesuaian ketentuan sistem pembayaran yang berlaku saat ini; c. bahwa perkembangan aktivitas penyelenggaraan infrastruktur sistem pembayaran menuntut dilakukannya penguatan fungsi penyelenggaraan infrastruktur yang dilakukan oleh otoritas da

- `document_page` `heading`: PBI No.23/7/PBI/2021 - Penyelenggara Infrastruktur Sistem Pembayaran, hlm. 2
  - Flags: `[]`
  - Text: d. bahwa berdasarkan pertimbangan sebagaimana dimaksud


## BI Sistem Pembayaran

- Issuer: `BI`
- Title patterns: `['Sistem Pembayaran']`
- Rows: `3044`
- Documents: `6`
- Section types: `{'pasal': 1726, 'ayat': 917, 'table': 311, 'heading': 64, 'paragraph': 26}`
- Citation quality: `{'document_page_pasal': 2063, 'document_page_pasal_ayat': 932, 'document_page': 49}`
- Issue counts: `{'very_short_text': 969, 'markdown_table_artifact': 311}`
- Warnings: `['markdown_table_artifact', 'very_short_text']`

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
  - Flags: `['markdown_table_artifact']`
  - Text: | meningkatkan | efektivitas | pengawasan | serta | |---|---|---|---| | pengawasan berbasis teknologi | | dalam kewajiban | |

- `document_page` `paragraph`: PBI No.22/23/PBI/2020 - Sistem Pembayaran, hlm. 1
  - Flags: `[]`
  - Text: PERATURAN BANK INDONESIA NOMOR 22/23/PBI/2020 TENTANG SISTEM PEMBAYARAN DENGAN RAHMAT TUHAN YANG MAHA ESA GUBERNUR BANK INDONESIA, Menimbang : a. bahwa perkembangan digitalisasi dan inovasi sistem pembayaran di satu sisi meningkatkan efisiensi industri sistem pembayaran dan percepatan inklusi ekonomi dan keuangan digital, di sisi lain meningkatkan risiko den

- `document_page` `paragraph`: PBI No.22/23/PBI/2020 - Sistem Pembayaran, hlm. 1
  - Flags: `[]`
  - Text: pembayaran menuntut dilakukannya penataan kembali industri sistem pembayaran melalui reformasi pengaturan sistem pembayaran; c. bahwa diperlukan pengaturan sistem pembayaran yang efektif dan responsif yang meliputi seluruh aspek penyelenggaraan sistem pembayaran guna mengakomodasi perkembangan ekonomi dan keuangan digital; d. bahwa berdasarkan pertimbangan s

- `document_page` `paragraph`: PBI No.22/23/PBI/2020 - Sistem Pembayaran, hlm. 1
  - Flags: `[]`
  - Text: dimaksud dalam huruf a, huruf b, dan huruf c, perlu menetapkan Peraturan Bank Indonesia tentang Sistem Pembayaran;


## OJK APU PPT

- Issuer: `OJK`
- Title patterns: `['Anti Pencucian Uang', 'Pencegahan Pendanaan Terorisme']`
- Rows: `7378`
- Documents: `15`
- Section types: `{'pasal': 4815, 'ayat': 944, 'table': 619, 'heading': 618, 'paragraph': 244, 'list_item': 99, 'attachment': 39}`
- Citation quality: `{'document_page_pasal': 5847, 'document_page_pasal_ayat': 1014, 'document_page': 517}`
- Issue counts: `{'very_short_text': 1068, 'markdown_table_artifact': 628}`
- Warnings: `['markdown_table_artifact', 'very_short_text']`

### Evidence Probe

- Query: `aturan OJK tentang APU PPT untuk bank`
- Confidence: `strong` score `0.961`

- `OJK` `document_page_pasal_ayat` `ayat`: Penerapan Program Anti Pencucian Uang dan Pencegahan Pendanaan Terorisme di Sektor Perbankan, hlm. 2, Pasal 13, ayat (1)
  - Snippet: 4. Mengacu ke dalam Pasal 13 POJK APU dan PPT, Bank wajib memiliki kebijakan dan prosedur penerapan program APU dan PPT dalam rangka pengelolaan dan mitigasi risiko Pencucian Uang dan/atau Pendanaan Terorisme yang disesuaikan dengan tingkat risiko yang melekat pada masing-masing Bank. 5. Berdasarkan Pasal 67 ayat (1) POJK APU dan PPT, Bank yang telah
- `OJK` `document_page_pasal_ayat` `ayat`: Peraturan Bank Indonesia tentang Penerapan Program Anti Pencucian Uang dan Pencegahan Pendanaan Terorisme bagi Bank Umum, hlm. 6, Pasal 2, ayat (1)
  - Snippet: Pasal 2 (1) Bank wajib menerapkan program APU dan PPT. (2) Dalam penerapan program APU dan PPT, Bank wajib berpedoman pada
- `OJK` `document_page_pasal_ayat` `ayat`: Peraturan Bank Indonesia tentang Penerapan Program Anti Pencucian Uang dan Pencegahan Pendanaan Terorisme bagi Bank Umum, hlm. 8, Pasal 2, ayat (2)
  - Snippet: **(1) (2)** **(1)** **(2)** **a.** **b.** **c.** **- 8 -**
- `OJK` `document_page_pasal_ayat` `ayat`: Penerapan Program Anti Pencucian Uang, Pencegahan Pendanaan Terorisme, dan Pencegahan Pendanaan Proliferasi Senjata Pemusnah Massal di Sektor Jasa Keuangan, hlm. 6, Pasal 2, ayat (1)
  - Snippet: Pasal 2 (1) PJK sebagaimana dimaksud dalam Pasal 1 angka 1 terdiri

### Extraction Examples

- `document_page_pasal_ayat` `ayat`: Penerapan Program Anti Pencucian Uang, Pencegahan Pendanaan Terorisme, dan Pencegahan Pendanaan Proliferasi Senjata Pemusnah Massal bagi Pedagang Aset Keuangan Digital, hlm. 29, Pasal 25, ayat (1)
  - Flags: `[]`
  - Text: 2) Proses verifikasi face to face dapat dikecualikan dengan proses verifikasi tanpa tatap muka (verifikasi non-face to *face) dengan ketentuan sebagai berikut:* a) verifikasi *non-face to face* dilakukan dengan menggunakan perangkat lunak milik Pedagang dengan perangkat keras milik Pedagang atau perangkat keras milik Nasabah atau calon Nasabah. Contoh: peran

- `document_page_pasal` `pasal`: Penerapan Program Anti Pencucian Uang, Pencegahan Pendanaan Terorisme, dan Pencegahan Pendanaan Proliferasi Senjata Pemusnah Massal di Sektor Jasa Keuangan, hlm. 3, Pasal 1
  - Flags: `['very_short_text']`
  - Text: Pasal 1

- `document_page` `table`: Penerapan Program Anti Pencucian Uang, Pencegahan Pendanaan Terorisme, dan Pencegahan Pendanaan Proliferasi Senjata Pemusnah Massal di Sektor Jasa Keuangan, hlm. 2
  - Flags: `['markdown_table_artifact']`
  - Text: | Jasa | Keuangan | Nomor | 12/POJK.01/2017 | tentang | |---|---|---|---|---| | Penerapan | Anti | Pencucian | Uang dan | Pencegahan |

- `document_page` `paragraph`: Penerapan Program Anti Pencucian Uang, Pencegahan Pendanaan Terorisme, dan Pencegahan Pendanaan Proliferasi Senjata Pemusnah Massal di Sektor Jasa Keuangan, hlm. 1
  - Flags: `[]`
  - Text: OTORITAS JASA KEUANGAN REPUBLIK INDONESIA SALINAN PERATURAN OTORITAS JASA KEUANGAN REPUBLIK INDONESIA NOMOR 8 TAHUN 2023 TENTANG PENERAPAN PROGRAM ANTI PENCUCIAN UANG, PENCEGAHAN PENDANAAN TERORISME, DAN PENCEGAHAN PENDANAAN PROLIFERASI SENJATA PEMUSNAH MASSAL DI SEKTOR JASA KEUANGAN DENGAN RAHMAT TUHAN YANG MAHA ESA DEWAN KOMISIONER OTORITAS JASA KEUANGAN,

- `document_page` `attachment`: Pedoman Penerapan Program Anti Pencucian Uang dan Pencegahan Pendanaan Terorisme di Sektor Industri Keuangan Non-Bank, hlm. 1
  - Flags: `[]`
  - Text: LAMPIRAN I SURAT EDARAN OTORITAS JASA KEUANGAN NOMOR 37 /SEOJK.05/2017 TENTANG PEDOMAN PENERAPAN PROGRAM ANTI PENCUCIAN UANG DAN PENCEGAHAN PENDANAAN TERORISME DI SEKTOR INDUSTRI KEUANGAN NON BANK

- `document_page` `paragraph`: Penerapan Program Anti Pencucian Uang, Pencegahan Pendanaan Terorisme, dan Pencegahan Pendanaan Proliferasi Senjata Pemusnah Massal di Sektor Jasa Keuangan, hlm. 1
  - Flags: `[]`
  - Text: Menimbang : a. bahwa untuk melakukan penguatan pencegahan tindak pidana pencucian uang, tindak pidana pendanaan terorisme, dan pendanaan proliferasi senjata pemusnah massal serta untuk mewujudkan integritas di sektor jasa keuangan, Otoritas Jasa Keuangan berkomitmen untuk mendukung regulasi yang sesuai dengan perkembangan prinsip internasional yang mengatur 


## OJK Consumer Protection

- Issuer: `OJK`
- Title patterns: `['Pelindungan Konsumen', 'Perlindungan Konsumen', 'Pengaduan Konsumen']`
- Rows: `3286`
- Documents: `8`
- Section types: `{'pasal': 1434, 'ayat': 1115, 'table': 510, 'heading': 138, 'paragraph': 76, 'list_item': 13}`
- Citation quality: `{'document_page_pasal': 1894, 'document_page_pasal_ayat': 1267, 'document_page': 125}`
- Issue counts: `{'very_short_text': 619, 'markdown_table_artifact': 510, 'form_placeholder_text': 11}`
- Warnings: `['form_placeholder_text', 'markdown_table_artifact', 'very_short_text']`

### Evidence Probe

- Query: `aturan OJK tentang pelindungan konsumen jasa keuangan`
- Confidence: `strong` score `0.825`

- `OJK` `document_page_pasal_ayat` `ayat`: Pelindungan Konsumen dan Masyarakat di Sektor Jasa Keuangan, hlm. 5, Pasal 4, ayat (2)
  - Snippet: dan/atau mewakili kepentingan PUJK memperlakukan atau melayani Konsumen secara tidak diskriminatif sebagaimana dimaksud pada ayat (2). (4) PUJK dilarang melakukan tindakan yang melanggar ketentuan peraturan perundang-undangan atau norma yang berlaku di masyarakat yang dapat menimbulkan
- `OJK` `document_page_pasal` `pasal`: Pelindungan Konsumen dan Masyarakat di Sektor Jasa Keuangan, hlm. 5, Pasal 2
  - Snippet: BAB II KETENTUAN PELINDUNGAN KONSUMEN DAN MASYARAKAT DI SEKTOR JASA KEUANGAN Bagian Kesatu Prinsip Pelindungan Konsumen
- `OJK` `document_page_pasal_ayat` `ayat`: Penilaian Sendiri Terhadap Pemenuhan Ketentuan Pelindungan Konsumen dan Masyarakat di Sektor Jasa Keuangan, hlm. 1, Pasal 87, ayat (4)
  - Snippet: Sehubungan dengan amanat Pasal 87 ayat (4) Peraturan Otoritas Jasa Keuangan Nomor 22 Tahun 2023 tentang Pelindungan Konsumen dan Masyarakat di Sektor Jasa Keuangan (Lembaran Negara Republik Indonesia Tahun 2023 Nomor 40/OJK, Tambahan Lembaran Negara Republik Indonesia Nomor 62/OJK) dan kebutuhan Pelaku Usaha Jasa Keuangan mengenai petunjuk pelaksanaan tentang penilaian sendiri terhadap pemenuhan ketentuan pelindungan...
- `OJK` `document_page_pasal_ayat` `ayat`: Gugatan oleh Otoritas Jasa Keuangan untuk Pelindungan Konsumen di Sektor Jasa Keuangan, hlm. 1, Pasal 30, ayat (1)
  - Snippet: Jasa Keuangan berwenang melakukan pembelaan hukum berupa pengajuan gugatan untuk memperoleh kembali harta kekayaan milik pihak yang dirugikan dan/atau untuk memperoleh ganti kerugian dari pihak yang menyebabkan kerugian sesuai ketentuan Pasal 30 ayat (1) huruf b dan Pasal 30 ayat (2) Undang-Undang Nomor 21 Tahun 2011 tentang Otoritas Jasa Keuangan sebagaimana telah diubah dengan Undang-Undang Nomor 4 Tahun 2023 tenta...

### Extraction Examples

- `document_page_pasal_ayat` `ayat`: Gugatan oleh Otoritas Jasa Keuangan untuk Pelindungan Konsumen di Sektor Jasa Keuangan, hlm. 1, Pasal 30, ayat (1)
  - Flags: `[]`
  - Text: Jasa Keuangan berwenang melakukan pembelaan hukum berupa pengajuan gugatan untuk memperoleh kembali harta kekayaan milik pihak yang dirugikan dan/atau untuk memperoleh ganti kerugian dari pihak yang menyebabkan kerugian sesuai ketentuan Pasal 30 ayat (1) huruf b dan Pasal 30 ayat (2) Undang-Undang Nomor 21 Tahun 2011 tentang Otoritas Jasa Keuangan sebagaiman

- `document_page_pasal` `pasal`: Penilaian Sendiri Terhadap Pemenuhan Ketentuan Pelindungan Konsumen dan Masyarakat di Sektor Jasa Keuangan, hlm. 1, Pasal 87
  - Flags: `[]`
  - Text: 1. Lembaga Jasa Keuangan yang selanjutnya disingkat LJK adalah lembaga yang melaksanakan kegiatan di sektor perbankan, pasar modal, perasuransian, dana pensiun, modal ventura, lembaga keuangan mikro, lembaga pembiayaan, dan lembaga jasa keuangan lainnya. 2. Pelaku Usaha Jasa Keuangan yang selanjutnya disingkat PUJK adalah: a. LJK dan/atau pihak yang melakuka

- `document_page` `table`: Pelindungan Konsumen dan Masyarakat di Sektor Jasa Keuangan, hlm. 1
  - Flags: `['markdown_table_artifact']`
  - Text: | konsumen | dan | masyarakat, kesadaran pelaku usaha jasa keuangan; | serta | menumbuhkan | |---|---|---|---|---| | bahwa | terdapat | perkembangan konsumen dan masyarakat di sektor jasa keuangan yang | aspek | pelindungan | | disebabkan | oleh | penambahan konsumen dan masyarakat, perluasan pelaku usaha jasa | prinsip | pelindungan |

- `document_page` `paragraph`: Pelindungan Konsumen dan Masyarakat di Sektor Jasa Keuangan, hlm. 1
  - Flags: `[]`
  - Text: OTORITAS JASA KEUANGAN REPUBLIK INDONESIA SALINAN PERATURAN OTORITAS JASA KEUANGAN REPUBLIK INDONESIA NOMOR 22 TAHUN 2023 TENTANG PELINDUNGAN KONSUMEN DAN MASYARAKAT DI SEKTOR JASA KEUANGAN DENGAN RAHMAT TUHAN YANG MAHA ESA DEWAN KOMISIONER OTORITAS JASA KEUANGAN, Menimbang : a. bahwa dengan berlakunya Undang-Undang Nomor 4 Tahun 2023 tentang Pengembangan da

- `document_page` `paragraph`: Pelindungan Konsumen dan Masyarakat di Sektor Jasa Keuangan, hlm. 1
  - Flags: `[]`
  - Text: keuangan, dan digitalisasi produk dan/atau layanan di sektor jasa keuangan, dan perkembangan industri jasa keuangan yang makin kompleks dan dinamis, sehingga perlu dilakukan penguatan pengaturan mengenai pelindungan konsumen dan masyarakat di sektor jasa keuangan; c. bahwa Peraturan Otoritas Jasa Keuangan Nomor 6/POJK.07/2022 tentang Perlindungan Konsumen da

- `document_page` `paragraph`: Pelindungan Konsumen dan Masyarakat di Sektor Jasa Keuangan, hlm. 1
  - Flags: `[]`
  - Text: dalam huruf a, huruf b, dan huruf c, perlu menetapkan Peraturan Otoritas Jasa Keuangan tentang Pelindungan Konsumen dan Masyarakat di Sektor Jasa Keuangan; Mengingat : 1. Undang-Undang Nomor 21 Tahun 2011 tentang Otoritas Jasa Keuangan (Lembaran Negara Republik Indonesia Tahun 2011 Nomor 111, Tambahan Lembaran Negara Republik Indonesia Nomor 5253) sebagaiman


## OJK SLIK

- Issuer: `OJK`
- Title patterns: `['Sistem Layanan Informasi Keuangan', 'SLIK', 'Informasi Debitur']`
- Rows: `6910`
- Documents: `6`
- Section types: `{'table': 2409, 'pasal': 2251, 'paragraph': 1026, 'list_item': 426, 'heading': 418, 'ayat': 380}`
- Citation quality: `{'document_page_pasal': 3894, 'document_page': 2634, 'document_page_pasal_ayat': 382}`
- Issue counts: `{'markdown_table_artifact': 2405, 'very_short_text': 945, 'form_placeholder_text': 30}`
- Warnings: `['form_placeholder_text', 'high_document_page_only_rate', 'markdown_table_artifact', 'very_short_text']`

### Evidence Probe

- Query: `apa kewajiban bank terkait pelaporan SLIK?`
- Confidence: `strong` score `0.948`

- `OJK` `document_page_pasal_ayat` `ayat`: Pelaporan Melalui Sistem Pelaporan Otoritas Jasa Keuangan dan Transparansi Kondisi Keuangan bagi Bank Perekonomian Rakyat, hlm. 11, Pasal 14, ayat (1)
  - Snippet: ...sangkutan dikenai sanksi administratif berupa denda per jenis Laporan sebagaimana dimaksud dalam Pasal 14 ayat (1) POJK Pelaporan dan TKK BPR dan BPR Syariah, sebesar:
- `OJK` `document_page_pasal_ayat` `ayat`: Pelaporan dan Permintaan Informasi Debitur Melalui Sistem Layanan Informasi Keuangan (SEOJK SLIK), hlm. 11, Pasal 2, ayat (1)
  - Snippet: (1) bagi Debitur perseorangan (a) fotokopi identitas diri dengan menunjukkan identitas diri asli antara lain berupa Kartu Tanda Penduduk (KTP) untuk Warga Negara Indonesia (WNI) atau paspor untuk Warga Negara Asing (WNA); atau (b) surat kuasa asli, fotokopi identitas diri pemberi kuasa dan penerima kuasa dengan menunjukkan identitas diri asli dari pemberi kuasa dan penerima kuasa, dalam hal dikuasakan. (2) bagi Debit...
- `OJK` `document_page_pasal_ayat` `ayat`: Pelaporan Melalui Sistem Pelaporan Otoritas Jasa Keuangan dan Transparansi Kondisi Keuangan Bagi Bank Perekonomian Rakyat dan Bank Perekonomian Rakyat Syariah, hlm. 3, Pasal 1, ayat (1)
  - Snippet: ...ajib menyampaikan Laporan sebagaimana dimaksud pada ayat (1) kepada Otoritas Jasa Keuangan secara daring melalui Sistem Pelaporan Otoritas Jasa Keuangan. (3) Dalam hal terdapat kesalahan data dan/atau informasi dalam Laporan sebagaimana dimaksud pada ayat (2), BPR dan BPR Syariah wajib menyusun dan menyampaikan
- `OJK` `document_page_pasal_ayat` `ayat`: Pelaporan Bank Umum Melalui Sistem Pelaporan Otoritas Jasa Keuangan, hlm. 3, Pasal 4, ayat (1)
  - Snippet: dimaksud dalam Pasal 4 ayat (1) atau perubahannya

### Extraction Examples

- `document_page_pasal_ayat` `ayat`: Perubahan Kedua Atas Peraturan Otoritas Jasa Keuangan Nomor 18/POJK.03/2017 tentang Pelaporan dan Permintaan Informasi Debitur Melalui Sistem Layanan Informasi Keuangan (SLIK), hlm. 4, Pasal 2, ayat (1)
  - Flags: `[]`
  - Text: (1) Pihak yang wajib menjadi Pelapor meliputi:

- `document_page_pasal` `pasal`: Pelaporan dan Permintaan Informasi Debitur Melalui Sistem Layanan Informasi Keuangan (SEOJK SLIK), hlm. 2, Pasal 2
  - Flags: `[]`
  - Text: 1. Berdasarkan Pasal 2 POJK Perubahan POJK PPID SLIK, Pihak yang wajib menjadi Pelapor yaitu: a. Bank Umum yang meliputi:

- `document_page` `table`: Pelaporan dan Permintaan Informasi Debitur Melalui Sistem Layanan Informasi Keuangan, hlm. 2
  - Flags: `['markdown_table_artifact']`
  - Text: | b. | Bank Perekonomian Rakyat (BPR); | |---|---| | c. | Bank Perekonomian Rakyat Syariah (BPRS); | | d. | Lembaga Pembiayaan yang memberikan Fasilitas Penyediaan Dana: |

- `document_page` `paragraph`: Perubahan Atas Peraturan Otoritas Jasa Keuangan Nomor 18/POJK.03/2017 tentang Pelaporan dan Permintaan Informasi Debitur Melalui Sistem Layanan Informasi Keuangan (POJK SLIK), hlm. 1
  - Flags: `[]`
  - Text: SALINAN PERATURAN OTORITAS JASA KEUANGAN REPUBLIK INDONESIA NOMOR 64 /POJK.03/2020 TENTANG PERUBAHAN ATAS PERATURAN OTORITAS JASA KEUANGAN NOMOR 18/POJK.03/2017 TENTANG PELAPORAN DAN PERMINTAAN INFORMASI DEBITUR MELALUI SISTEM LAYANAN INFORMASI KEUANGAN DENGAN RAHMAT TUHAN YANG MAHA ESA DEWAN KOMISIONER OTORITAS JASA KEUANGAN, Menimbang : a. bahwa untuk memp

- `document_page` `paragraph`: Pelaporan dan Permintaan Informasi Debitur melalui Sistem Layanan Informasi Keuangan, hlm. 1
  - Flags: `[]`
  - Text: Yth. Direksi Lembaga Jasa Keuangan di tempat. SALINAN

- `document_page` `heading`: Pelaporan dan Permintaan Informasi Debitur melalui Sistem Layanan Informasi Keuangan, hlm. 1
  - Flags: `[]`
  - Text: # SURAT EDARAN OTORITAS JASA KEUANGAN NOMOR 50 /SEOJK.03/2017


## OJK BPR BPRS

- Issuer: `OJK`
- Title patterns: `['Bank Perekonomian Rakyat', 'Bank Perkreditan Rakyat', 'BPR', 'BPRS']`
- Rows: `43839`
- Documents: `89`
- Section types: `{'pasal': 21997, 'table': 5828, 'heading': 5594, 'ayat': 5581, 'paragraph': 2639, 'list_item': 1787, 'attachment': 413}`
- Citation quality: `{'document_page_pasal': 31616, 'document_page': 6447, 'document_page_pasal_ayat': 5776}`
- Issue counts: `{'very_short_text': 8371, 'markdown_table_artifact': 5893, 'form_placeholder_text': 241}`
- Warnings: `['form_placeholder_text', 'markdown_table_artifact', 'very_short_text']`

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

- `document_page_pasal` `pasal`: Penyelenggaraan Teknologi Informasi oleh Bank Perekonomian Rakyat dan Bank Perekonomian Rakyat Syariah, hlm. 1, Pasal 8
  - Flags: `[]`
  - Text: SALINAN PERATURAN ANGGOTA DEWAN KOMISIONER OTORITAS JASA KEUANGAN REPUBLIK INDONESIA NOMOR 43/PADK.03/2025 TENTANG PENYELENGGARAAN TEKNOLOGI INFORMASI OLEH BANK PEREKONOMIAN RAKYAT DAN BANK PEREKONOMIAN RAKYAT SYARIAH DENGAN RAHMAT TUHAN YANG MAHA ESA ANGGOTA DEWAN KOMISIONER OTORITAS JASA KEUANGAN, Menimbang : bahwa untuk melaksanakan ketentuan sebagaimana 

- `document_page_pasal` `table`: Penyelenggaraan Teknologi Informasi oleh Bank Perekonomian Rakyat dan Bank Perekonomian Rakyat Syariah, hlm. 2, Pasal 2
  - Flags: `['markdown_table_artifact']`
  - Text: | c. | Lampiran III yang memuat mengenai manajemen risiko penyelenggaraan TI oleh BPR dan BPR Syariah; | |---|---| | d. | Lampiran IV yang memuat mengenai pedoman ketahanan dan keamanan siber BPR dan BPR Syariah; | | e. | Lampiran V yang memuat mengenai pengelolaan data dan pelindungan data pribadi BPR dan BPR Syariah; dan |

- `document_page` `paragraph`: Rencana Bisnis Bank Perekonomian Rakyat, hlm. 1
  - Flags: `[]`
  - Text: Yth. Direksi Bank Perekonomian Rakyat di tempat. SALINAN SURAT EDARAN OTORITAS JASA KEUANGAN REPUBLIK INDONESIA NOMOR 24/SEOJK.03/2025 TENTANG RENCANA BISNIS BANK PEREKONOMIAN RAKYAT Sehubungan dengan Peraturan Otoritas Jasa Keuangan Nomor 15/POJK.03/2021 tentang Rencana Bisnis Bank Perkreditan Rakyat dan Bank Pembiayaan Rakyat Syariah (Lembaran Negara Repub

- `document_page` `attachment`: Rencana Bisnis Bank Perkreditan Rakyat, hlm. 1
  - Flags: `[]`
  - Text: LAMPIRAN SURAT EDARAN OTORITAS JASA KEUANGAN NOMOR 52 /SEOJK.03/2016 TENTANG RENCANA BISNIS BANK PERKREDITAN RAKYAT

- `document_page_pasal` `pasal`: Penyelenggaraan Teknologi Informasi oleh Bank Perekonomian Rakyat dan Bank Perekonomian Rakyat Syariah, hlm. 1, Pasal 8
  - Flags: `[]`
  - Text: Mengingat : 1. Undang-Undang Nomor 21 Tahun 2011 tentang Otoritas Jasa Keuangan (Lembaran Negara Republik Indonesia Tahun 2011 Nomor 111, Tambahan Lembaran Negara Republik Indonesia Nomor 5253) sebagaimana telah diubah dengan Undang-Undang Nomor 4 Tahun 2023 tentang Pengembangan dan Penguatan Sektor Keuangan (Lembaran Negara Republik Indonesia Tahun 2023 Nom


## OJK Modal Ventura

- Issuer: `OJK`
- Title patterns: `['Modal Ventura']`
- Rows: `17703`
- Documents: `24`
- Section types: `{'pasal': 9642, 'ayat': 4245, 'table': 2892, 'heading': 857, 'paragraph': 62, 'list_item': 5}`
- Citation quality: `{'document_page_pasal': 12955, 'document_page_pasal_ayat': 4665, 'document_page': 83}`
- Issue counts: `{'markdown_table_artifact': 2892, 'very_short_text': 2846, 'form_placeholder_text': 68}`
- Warnings: `['form_placeholder_text', 'markdown_table_artifact', 'very_short_text']`

### Evidence Probe

- Query: `aturan penyelenggaraan usaha perusahaan modal ventura`
- Confidence: `strong` score `1.0`

- `OJK` `document_page_pasal_ayat` `ayat`: Penyelenggaraan Usaha Perusahaan Modal Ventura dan Perusahaan Modal Ventura Syariah, hlm. 1, Pasal 106, ayat (6)
  - Snippet: OTORITAS JASA KEUANGAN REPUBLIK INDONESIA SALINAN PERATURAN OTORITAS JASA KEUANGAN REPUBLIK INDONESIA NOMOR 25 TAHUN 2023 TENTANG PENYELENGGARAAN USAHA PERUSAHAAN MODAL VENTURA DAN PERUSAHAAN MODAL VENTURA SYARIAH DENGAN RAHMAT TUHAN YANG MAHA ESA DEWAN KOMISIONER OTORITAS JASA KEUANGAN, Menimbang : bahwa untuk melaksanakan amanat Pasal 106 ayat (6),
- `OJK` `document_page_pasal_ayat` `ayat`: POJK tentang Penyelenggaraan Usaha Perusahaan Modal Ventura, hlm. 6, Pasal 2, ayat (1)
  - Snippet: Pasal 2 (1) PMV menyelenggarakan Usaha Modal Ventura yang
- `OJK` `document_page_pasal_ayat` `ayat`: POJK tentang Perizinan Usaha dan Kelembagaan Perusahaan Modal Ventura, hlm. 7, Pasal 2, ayat (1)
  - Snippet: Pasal 2 (1) PMV dan PMVS harus didirikan dalam bentuk badan
- `OJK` `document_page_pasal_ayat` `ayat`: Laporan Bulanan Perusahaan Modal Ventura dan Perusahaan Modal Ventura Syariah, hlm. 1, Pasal 2, ayat (6)
  - Snippet: Yth. 1. Direksi Perusahaan Modal Ventura; dan 2. Direksi Perusahaan Modal Ventura Syariah, di tempat. SALINAN SURAT EDARAN OTORITAS JASA KEUANGAN NOMOR 25 /SEOJK.05/2019 TENTANG LAPORAN BULANAN PERUSAHAAN MODAL VENTURA DAN PERUSAHAAN MODAL VENTURA SYARIAH Sehubungan dengan amanat Pasal 2 ayat (6), Pasal 4 ayat (6), dan Pasal 10 Peraturan Otoritas Jasa Keuangan Nomor 3/POJK.05/2013 tentang Laporan Bulanan Lembaga Jasa...

### Extraction Examples

- `document_page_pasal_ayat` `ayat`: Perubahan Atas Surat Edaran Otoritas Jasa Keuangan Nomor 25/SEOJK.05/2019 tentang Laporan Bulanan Perusahaan Modal Ventura dan Perusahaan Modal Ventura Syariah, hlm. 1, Pasal 128, ayat (4)
  - Flags: `[]`
  - Text: Sehubungan dengan amanat Pasal 128 ayat (4) Peraturan Otoritas Jasa Keuangan Nomor 25 Tahun 2023 tentang Penyelenggaraan Usaha Perusahaan Modal Ventura dan Perusahaan Modal Ventura Syariah (Lembaran Negara Republik Indonesia Tahun 2023 Nomor 43/OJK, Tambahan Lembaran Negara Republik Indonesia Nomor 65/OJK) dan mengingat adanya kebutuhan penyempurnaan pos-pos

- `document_page_pasal` `pasal`: Penerapan Manajemen Risiko Bagi Lembaga Pembiayaan, Perusahaan Modal Ventura, Lembaga Keuangan Mikro, dan Lembaga Jasa Keuangan Lainnya, hlm. 1, Pasal 5
  - Flags: `[]`
  - Text: dimaksud pada huruf a, perlu menetapkan Peraturan Anggota Dewan Komisioner Otoritas Jasa Keuangan tentang Penerapan Manajemen Risiko bagi Lembaga Pembiayaan, Perusahaan Modal Ventura, Lembaga Keuangan Mikro, dan Lembaga Jasa Keuangan Lainnya; Mengingat : 1. Peraturan Otoritas Jasa Keuangan Nomor 42 Tahun 2024 tentang Penerapan Manajemen Risiko Bagi Lembaga P

- `document_page_pasal` `table`: Penerapan Manajemen Risiko Bagi Lembaga Pembiayaan, Perusahaan Modal Ventura, Lembaga Keuangan Mikro, dan Lembaga Jasa Keuangan Lainnya, hlm. 1, Pasal 5
  - Flags: `['markdown_table_artifact']`
  - Text: | Lembaga | Keuangan | Mikro, | dan | Lembaga Jasa | |---|---|---|---|---| | Keuangan | Lainnya | (Lembaran Indonesia Tahun 2024 Nomor 55/OJK, Tambahan | Negara | Republik |

- `document_page` `paragraph`: Kantor Perwakilan Lembaga Pembiayaan, Perusahaan Modal Ventura, dan Lembaga Jasa Keuangan Lainnya yang Berkantor Pusat di Luar Negeri, hlm. 1
  - Flags: `[]`
  - Text: PERATURAN OTORITAS JASA KEUANGAN REPUBLIK INDONESIA NOMOR 41 TAHUN 2025 TENTANG KANTOR PERWAKILAN LEMBAGA PEMBIAYAAN, PERUSAHAAN MODAL VENTURA, DAN LEMBAGA JASA KEUANGAN LAINNYA YANG BERKANTOR PUSAT DI LUAR NEGERI DENGAN RAHMAT TUHAN YANG MAHA ESA DEWAN KOMISIONER OTORITAS JASA KEUANGAN, Menimbang : a. bahwa untuk mewujudkan kepastian hukum, keadilan,

- `document_page_pasal_ayat` `ayat`: Penerapan Manajemen Risiko Bagi Lembaga Pembiayaan, Perusahaan Modal Ventura, Lembaga Keuangan Mikro, dan Lembaga Jasa Keuangan Lainnya, hlm. 1, Pasal 2, ayat (4)
  - Flags: `[]`
  - Text: SALINAN PERATURAN ANGGOTA DEWAN KOMISIONER OTORITAS JASA KEUANGAN REPUBLIK INDONESIA NOMOR 48/PADK.06/2025 TENTANG PENERAPAN MANAJEMEN RISIKO BAGI LEMBAGA PEMBIAYAAN, PERUSAHAAN MODAL VENTURA, LEMBAGA KEUANGAN MIKRO, DAN LEMBAGA JASA KEUANGAN LAINNYA DENGAN RAHMAT TUHAN YANG MAHA ESA ANGGOTA DEWAN KOMISIONER OTORITAS JASA KEUANGAN, Menimbang : a. bahwa untuk

- `document_page_pasal_ayat` `ayat`: Penerapan Manajemen Risiko Bagi Lembaga Pembiayaan, Perusahaan Modal Ventura, Lembaga Keuangan Mikro, dan Lembaga Jasa Keuangan Lainnya, hlm. 1, Pasal 5, ayat (4)
  - Flags: `[]`
  - Text: Pasal 5 ayat (4), Pasal 25 ayat (4), Pasal 26 ayat (8), Pasal 27 ayat (2), Pasal 29 ayat (10), Pasal 33 ayat (9), Pasal 35 ayat (5), dan Pasal 36 ayat (6) Peraturan Otoritas Jasa Keuangan Nomor 42 Tahun 2024 tentang Penerapan Manajemen Risiko bagi Lembaga Pembiayaan, Perusahaan Modal Ventura, Lembaga Keuangan Mikro, dan Lembaga Jasa Keuangan Lainnya (Lembara


## OJK Perusahaan Pembiayaan

- Issuer: `OJK`
- Title patterns: `['Perusahaan Pembiayaan']`
- Rows: `29818`
- Documents: `43`
- Section types: `{'pasal': 16423, 'ayat': 5459, 'table': 3678, 'heading': 2249, 'attachment': 1524, 'paragraph': 434, 'list_item': 51}`
- Citation quality: `{'document_page_pasal': 21463, 'document_page_pasal_ayat': 6023, 'document_page': 2332}`
- Issue counts: `{'very_short_text': 4522, 'markdown_table_artifact': 3852, 'form_placeholder_text': 120}`
- Warnings: `['form_placeholder_text', 'markdown_table_artifact', 'very_short_text']`

### Evidence Probe

- Query: `aturan OJK tentang perusahaan pembiayaan`
- Confidence: `strong` score `0.968`

- `OJK` `document_page_pasal_ayat` `ayat`: Laporan Bulanan Perusahaan Pembiayaan dan Perusahaan Pembiayaan Syariah, hlm. 3, Pasal 2, ayat (1)
  - Snippet: Pasal 2 (1) Kewajiban Perusahaan Pembiayaan untuk
- `OJK` `document_page_pasal_ayat` `ayat`: Permohonan Perizinan, Persetujuan, dan Pelaporan Secara Elektronik bagi Perusahaan Pembiayaan dan Perusahaan Pembiayaan Syariah, hlm. 1, Pasal 114, ayat (5)
  - Snippet: Yth. 1. Direksi Perusahaan Pembiayaan; dan 2. Direksi Perusahaan Pembiayaan Syariah, di tempat. SALINAN SURAT EDARAN OTORITAS JASA KEUANGAN REPUBLIK INDONESIA NOMOR 20/SEOJK.06/2023 TENTANG PERMOHONAN PERIZINAN, PERSETUJUAN, DAN PELAPORAN SECARA ELEKTRONIK BAGI PERUSAHAAN PEMBIAYAAN DAN PERUSAHAAN PEMBIAYAAN SYARIAH Sehubungan dengan amanat Pasal 114 ayat (5) Peraturan Otoritas Jasa Keuangan Nomor 47/POJK.05/2020 ten...
- `OJK` `document_page_pasal_ayat` `ayat`: Laporan Bulanan Perusahaan Pembiayaan Syariah dan Unit Usaha Syariah dari Perusahaan Pembiayaan, hlm. 1, Pasal 2, ayat (6)
  - Snippet: Yth. 1. Direksi atau yang setara pada Perusahaan Pembiayaan Syariah; dan 2. Direksi atau yang setara pada Perusahaan Pembiayaan yang mempunyai Unit Usaha Syariah, di tempat. SALINAN SURAT EDARAN OTORITAS JASA KEUANGAN NOMOR 4/SEOJK.05/2016 TENTANG LAPORAN BULANAN PERUSAHAAN PEMBIAYAAN SYARIAH DAN UNIT USAHA SYARIAH DARI PERUSAHAAN PEMBIAYAAN Sehubungan dengan amanat Pasal 2 ayat (6), Pasal 4 ayat (6), dan Pasal 10 Pe...
- `OJK` `document_page_pasal_ayat` `ayat`: Perizinan Usaha dan Kelembagaan Perusahaan Pembiayaan, hlm. 6, Pasal 2, ayat (1)
  - Snippet: (1) Perusahaan harus didirikan dalam bentuk badan hukum: a. perseroan terbatas; atau b. koperasi. (2) Perusahaan yang berbentuk badan hukum perseroan terbatas sebagaimana dimaksud pada ayat (1) huruf a, sahamnya dimiliki oleh: a. warga negara Indonesia; b. badan usaha Indonesia; c. badan hukum Indonesia; d. badan usaha asing atau lembaga asing; e. negara Republik Indonesia; dan/atau

### Extraction Examples

- `document_page_pasal_ayat` `ayat`: Laporan Bulanan Perusahaan Pembiayaan dan Perusahaan Pembiayaan Syariah, hlm. 3, Pasal 2, ayat (1)
  - Flags: `[]`
  - Text: Pasal 2 (1) Kewajiban Perusahaan Pembiayaan untuk

- `document_page_pasal` `pasal`: Penyelenggaraan Beli Sekarang Bayar Nanti (Buy Now Pay Later) Bagi Perusahaan Pembiayaan dan Perusahaan Pembiayaan Syariah, hlm. 1, Pasal 19J
  - Flags: `[]`
  - Text: Nomor 59/OJK, Tambahan Lembaran Negara Republik Indonesia Nomor 127/OJK) sebagaimana telah diubah dengan Peraturan Otoritas Jasa Keuangan Nomor 35 Tahun 2025 tentang Perubahan Atas Peraturan Otoritas Jasa Keuangan Nomor 46 Tahun 2024 tentang Pengembangan dan Penguatan Perusahaan Pembiayaan, Perusahaan Pembiayaan Infrastruktur, dan Perusahaan Modal Ventura (L

- `document_page_pasal` `table`: Perubahan Peraturan Otoritas Jasa Keuangan 46 Tahun 2024 tentang Pengembangan dan Penguatan Perusahaan Pembiayaan, Perusahaan Pembiayaan Infrastruktur, dan Perusahaan Modal Ventura, hlm. 4, Pasal 71
  - Flags: `['markdown_table_artifact']`
  - Text: | yang | mengakibatkan | perubahan | PSP | wajib | |---|---|---|---|---| | memperoleh Keuangan. | persetujuan | dari | Otoritas | Jasa |

- `document_page` `paragraph`: Perubahan Atas Peraturan Otoritas Jasa Keuangan Nomor 4/POJK.05/2018 Tentang Perusahaan Pembiayaan Sekunder Perumahan, hlm. 1
  - Flags: `[]`
  - Text: OTORITAS JASA KEUANGAN REPUBLIK INDONESIA SALINAN PERATURAN OTORITAS JASA KEUANGAN REPUBLIK INDONESIA NOMOR 12 /POJK.05/2022 TENTANG PERUBAHAN ATAS PERATURAN OTORITAS JASA KEUANGAN NOMOR 4/POJK.05/2018 TENTANG PERUSAHAAN PEMBIAYAAN SEKUNDER PERUMAHAN DENGAN RAHMAT TUHAN YANG MAHA ESA DEWAN KOMISIONER OTORITAS JASA KEUANGAN, Menimbang : a. bahwa untuk menduku

- `document_page` `attachment`: Laporan Bulanan Perusahaan Pembiayaan Syariah dan Unit Usaha Syariah dari Perusahaan Pembiayaan, hlm. 1
  - Flags: `[]`
  - Text: LAMPIRAN I SURAT EDARAN OTORITAS JASA KEUANGAN NOMOR 4/SEOJK.05/2016 TENTANG LAPORAN BULANAN PERUSAHAAN PEMBIAYAAN SYARIAH DAN UNIT USAHA SYARIAH DARI PERUSAHAAN PEMBIAYAAN

- `document_page_pasal_ayat` `ayat`: Pengembangan dan Penguatan Perusahaan Pembiayaan, Perusahaan Pembiayaan Infrastruktur, dan Perusahaan Modal Ventura, hlm. 1, Pasal 106, ayat (6)
  - Flags: `[]`
  - Text: SALINAN PERATURAN OTORITAS JASA KEUANGAN REPUBLIK INDONESIA NOMOR 46 TAHUN 2024 TENTANG PENGEMBANGAN DAN PENGUATAN PERUSAHAAN PEMBIAYAAN, PERUSAHAAN PEMBIAYAAN INFRASTRUKTUR, DAN PERUSAHAAN MODAL VENTURA DENGAN RAHMAT TUHAN YANG MAHA ESA DEWAN KOMISIONER OTORITAS JASA KEUANGAN, Menimbang : bahwa untuk melaksanakan ketentuan Pasal 106 ayat (6), Pasal 107 ayat


## OJK Aset Keuangan Digital

- Issuer: `OJK`
- Title patterns: `['Aset Keuangan Digital', 'Aset Kripto']`
- Rows: `5485`
- Documents: `6`
- Section types: `{'pasal': 2742, 'ayat': 820, 'table': 757, 'heading': 517, 'paragraph': 352, 'list_item': 297}`
- Citation quality: `{'document_page_pasal': 3756, 'document_page': 930, 'document_page_pasal_ayat': 799}`
- Issue counts: `{'very_short_text': 927, 'markdown_table_artifact': 757, 'form_placeholder_text': 255}`
- Warnings: `['form_placeholder_text', 'markdown_table_artifact', 'very_short_text']`

### Evidence Probe

- Query: `aturan OJK tentang perdagangan aset keuangan digital termasuk aset kripto`
- Confidence: `strong` score `0.841`

- `OJK` `document_page_pasal_ayat` `ayat`: Penyelenggaraan Perdagangan Aset Keuangan Digital Termasuk Aset Kripto, hlm. 14, Pasal 12, ayat (1)
  - Snippet: PEMBERITAHUAN DIMULAINYA PERDAGANGAN ASET KRIPTO Dalam rangka melaksanakan amanat Pasal 12 ayat (1) POJK Nomor … tentang Penyelenggaraan Perdagangan Aset Keuangan Digital termasuk Aset Kripto terkait kewajiban Pedagang untuk memberitahukan dimulainya perdagangan Aset Kripto kepada Otoritas Jasa Keuangan, kami yang bertandatangan di bawah ini: Nama Pedagang : Kode Pedagang :
- `OJK` `document_page_pasal_ayat` `ayat`: Penyelenggaraan Perdagangan Aset Keuangan Digital Termasuk Aset Kripto, hlm. 1, Pasal 312, ayat (1)
  - Snippet: SALINAN PERATURAN OTORITAS JASA KEUANGAN REPUBLIK INDONESIA NOMOR 27 TAHUN 2024 TENTANG PENYELENGGARAAN PERDAGANGAN ASET KEUANGAN DIGITAL TERMASUK ASET KRIPTO DENGAN RAHMAT TUHAN YANG MAHA ESA DEWAN KOMISIONER OTORITAS JASA KEUANGAN, Menimbang : a. bahwa untuk mendukung perkembangan sektor jasa keuangan dan melaksanakan kewenangan pengaturan dan pengawasan sebagaimana dimaksud dalam Undang-Undang Nomor 4 Tahun 2023 t...
- `OJK` `document_page_pasal_ayat` `ayat`: Perubahan Atas Peraturan Otoritas Jasa Keuangan Nomor 27 Tahun 2024 tentang Penyelenggaraan Perdagangan Aset Keuangan Digital Termasuk Aset Kripto, hlm. 5, Pasal 3A, ayat (1)
  - Snippet: (1) Aset Keuangan Digital terdiri atas:
- `OJK` `document_page_pasal_ayat` `ayat`: Rencana Bisnis Penyelenggara Perdagangan Aset Keuangan Digital, hlm. 1, Pasal 76, ayat (8)
  - Snippet: Yth. Direksi Penyelenggara Perdagangan Aset Keuangan Digital, di tempat. SALINAN SURAT EDARAN OTORITAS JASA KEUANGAN REPUBLIK INDONESIA NOMOR 34/SEOJK.07/2025 TENTANG RENCANA BISNIS PENYELENGGARA PERDAGANGAN ASET KEUANGAN DIGITAL Sehubungan dengan amanat Pasal 76 ayat (8) Peraturan Otoritas Jasa Keuangan Nomor 27 Tahun 2024 tentang Penyelenggara Perdagangan Aset Keuangan Digital Termasuk Aset Kripto (Lembaran Negara ...

### Extraction Examples

- `document_page_pasal_ayat` `ayat`: Rencana Bisnis Penyelenggara Perdagangan Aset Keuangan Digital, hlm. 1, Pasal 76, ayat (8)
  - Flags: `[]`
  - Text: Yth. Direksi Penyelenggara Perdagangan Aset Keuangan Digital, di tempat. SALINAN SURAT EDARAN OTORITAS JASA KEUANGAN REPUBLIK INDONESIA NOMOR 34/SEOJK.07/2025 TENTANG RENCANA BISNIS PENYELENGGARA PERDAGANGAN ASET KEUANGAN DIGITAL Sehubungan dengan amanat Pasal 76 ayat (8) Peraturan Otoritas Jasa Keuangan Nomor 27 Tahun 2024 tentang Penyelenggara Perdagangan 

- `document_page_pasal` `pasal`: Perubahan Atas Peraturan Otoritas Jasa Keuangan Nomor 27 Tahun 2024 tentang Penyelenggaraan Perdagangan Aset Keuangan Digital Termasuk Aset Kripto, hlm. 2, Pasal 1
  - Flags: `[]`
  - Text: 106) diubah sebagai berikut: 1. Ketentuan Pasal 1 diubah sehingga berbunyi sebagai berikut:

- `document_page` `table`: Penilaian Kemampuan dan Kepatutan Serta Penilaian Kembali Bagi Pihak Utama di Sektor Inovasi Teknologi Sektor Keuangan serta Aset Keuangan Digital dan Aset Kripto, hlm. 2
  - Flags: `['markdown_table_artifact']`
  - Text: | 1) | calon | Pihak | Utama Penyelenggara IAKD merupakan: | pengendali, | yaitu | PSP | dari | |---|---|---|---|---|---|---|---| | | a) | | akan melakukan pembelian, | orang perseorangan dan/atau badan hukum yang | | menerima hibah, | |

- `document_page` `paragraph`: Penerapan Program Anti Pencucian Uang, Pencegahan Pendanaan Terorisme, dan Pencegahan Pendanaan Proliferasi Senjata Pemusnah Massal bagi Pedagang Aset Keuangan Digital, hlm. 1
  - Flags: `[]`
  - Text: Yth. Direksi Pedagang Aset Keuangan Digital, di tempat. SALINAN SURAT EDARAN OTORITAS JASA KEUANGAN REPUBLIK INDONESIA NOMOR 16/SEOJK.07/2025 TENTANG PENERAPAN PROGRAM ANTI PENCUCIAN UANG, PENCEGAHAN PENDANAAN TERORISME, DAN PENCEGAHAN PENDANAAN PROLIFERASI SENJATA PEMUSNAH MASSAL BAGI PEDAGANG ASET KEUANGAN DIGITAL Sehubungan dengan berlakunya Peraturan Oto

- `document_page` `paragraph`: Penilaian Kemampuan dan Kepatutan serta Penilaian Kembali bagi Pihak Utama di Sektor Inovasi Teknologi Sektor Keuangan serta Aset Keuangan Digital dan Aset Kripto, hlm. 1
  - Flags: `[]`
  - Text: SALINAN PERATURAN OTORITAS JASA KEUANGAN REPUBLIK INDONESIA NOMOR 16 TAHUN 2025 TENTANG PENILAIAN KEMAMPUAN DAN KEPATUTAN SERTA PENILAIAN KEMBALI BAGI PIHAK UTAMA DI SEKTOR INOVASI TEKNOLOGI SEKTOR KEUANGAN SERTA ASET KEUANGAN DIGITAL DAN ASET KRIPTO DENGAN RAHMAT TUHAN YANG MAHA ESA DEWAN KOMISIONER OTORITAS JASA KEUANGAN, Menimbang : a. bahwa untuk mencipt

- `document_page` `paragraph`: Penyelenggaraan Perdagangan Aset Keuangan Digital Termasuk Aset Kripto, hlm. 1
  - Flags: `[]`
  - Text: Yth. Direksi Penyelenggara Perdagangan Aset Keuangan Digital termasuk Aset Kripto, di tempat. SALINAN SURAT EDARAN OTORITAS JASA KEUANGAN REPUBLIK INDONESIA NOMOR 20/SEOJK.07/2024 TENTANG PENYELENGGARAAN PERDAGANGAN ASET KEUANGAN DIGITAL TERMASUK ASET KRIPTO Sehubungan dengan berlakunya Peraturan Otoritas Jasa Keuangan Nomor 27 Tahun 2024 tentang Penyelengga
