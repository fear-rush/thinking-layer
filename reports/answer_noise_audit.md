# Answer Noise Audit

This report classifies legal boilerplate/noise patterns in `processed/source_corpus.ndjson` before changing answer behavior.

- Source: `processed/source_corpus.ndjson`
- Total blocks: `513240`
- Boilerplate/noise blocks: `10731`
- Boilerplate/noise rate: `0.02091`

## Category Summary

| Category | Policy | Count | Rate | Top section types |
|---|---:|---:|---:|---|
| `substantive` | `allow` | `502509` | `0.97909` | pasal: 258536, ayat: 86858, table: 61674, heading: 54097 |
| `promulgation` | `reject_by_default` | `6949` | `0.01354` | pasal: 4489, paragraph: 1223, heading: 498, ayat: 379 |
| `enactment` | `reject_by_default` | `1240` | `0.00242` | paragraph: 734, pasal: 267, heading: 120, table: 74 |
| `legal_preamble` | `reject_by_default` | `1141` | `0.00222` | paragraph: 789, pasal: 195, ayat: 79, heading: 51 |
| `legal_basis_reference` | `reject_by_default` | `931` | `0.00181` | paragraph: 721, pasal: 148, list_item: 32, ayat: 25 |
| `consideration` | `reject_by_default` | `309` | `0.0006` | paragraph: 236, pasal: 33, heading: 18, ayat: 18 |
| `letter_intro` | `reject_by_default` | `161` | `0.00031` | paragraph: 131, ayat: 16, pasal: 9, heading: 2 |

## `substantive`

- Description: Default category when no boilerplate category matches.
- Answer policy: `allow`
- Count: `502509`
- Rate: `0.97909`
- By issuer: `{'OJK': 472403, 'BI': 30106}`
- By role: `{'primary_regulation': 490769, 'attachment': 10004, 'operational_requirement': 1736}`
- By section type: `{'pasal': 258536, 'ayat': 86858, 'table': 61674, 'heading': 54097, 'paragraph': 20183, 'list_item': 11157, 'attachment': 10004}`
- Matched patterns: `{}`

### Examples

- `BI` `primary_regulation` `paragraph` - PBI No.22/8/PBI/2020 - Perizinan Terpadu Bank Indonesia Melalui Front Office Perizinan
  - Citation: `PBI No.22/8/PBI/2020 - Perizinan Terpadu Bank Indonesia Melalui Front Office Perizinan, hlm. 1`
  - Patterns: `[]`
  - Text: Indonesia memberikan perizinan di bidang moneter, makroprudensial, serta sistem pembayaran dan pengelolaan uang rupiah; c. bahwa untuk meningkatkan aspek pelayanan dan tata kelola yang transparan, akuntabel, efektif, dan efisien

- `BI` `primary_regulation` `table` - PBI No.22/8/PBI/2020 - Perizinan Terpadu Bank Indonesia Melalui Front Office Perizinan
  - Citation: `PBI No.22/8/PBI/2020 - Perizinan Terpadu Bank Indonesia Melalui Front Office Perizinan, hlm. 1`
  - Patterns: `[]`
  - Text: | dalam | penyampaian | permohonan | perizinan, | Bank | |---|---|---|---|---| | Indonesia | memandang | perlu | untuk | memberikan |

- `BI` `primary_regulation` `paragraph` - PBI No.22/8/PBI/2020 - Perizinan Terpadu Bank Indonesia Melalui Front Office Perizinan
  - Citation: `PBI No.22/8/PBI/2020 - Perizinan Terpadu Bank Indonesia Melalui Front Office Perizinan, hlm. 1`
  - Patterns: `[]`
  - Text: pelayanan perizinan terpadu secara elektronik dengan dukungan aplikasi; d. bahwa berdasarkan pertimbangan sebagaimana dimaksud dalam huruf a, huruf b, dan huruf c, perlu menetapkan Peraturan Bank Indonesia tentang Perizinan Terpadu Bank Indonesia Melalui Front Office Perizinan;

- `BI` `primary_regulation` `pasal` - PBI No.22/8/PBI/2020 - Perizinan Terpadu Bank Indonesia Melalui Front Office Perizinan
  - Citation: `PBI No.22/8/PBI/2020 - Perizinan Terpadu Bank Indonesia Melalui Front Office Perizinan, hlm. 2, Pasal 1`
  - Patterns: `[]`
  - Text: Pasal 1 Dalam Peraturan Bank Indonesia ini yang dimaksud dengan:

- `BI` `primary_regulation` `pasal` - PBI No.22/8/PBI/2020 - Perizinan Terpadu Bank Indonesia Melalui Front Office Perizinan
  - Citation: `PBI No.22/8/PBI/2020 - Perizinan Terpadu Bank Indonesia Melalui Front Office Perizinan, hlm. 2, Pasal 1`
  - Patterns: `[]`
  - Text: 1. Bank adalah bank sebagaimana dimaksud dalam Undang- Undang mengenai perbankan, dan bank syariah sebagaimana dimaksud dalam Undang-Undang mengenai perbankan syariah. 2. Lembaga Selain Bank adalah badan usaha bukan Bank yang didirikan berdasarkan hukum Indonesia. 3. Pemohon adalah pihak yang mengajukan permohonan perizinan kepada Bank Indonesia. 4. *Front O

- `BI` `primary_regulation` `pasal` - PBI No.22/8/PBI/2020 - Perizinan Terpadu Bank Indonesia Melalui Front Office Perizinan
  - Citation: `PBI No.22/8/PBI/2020 - Perizinan Terpadu Bank Indonesia Melalui Front Office Perizinan, hlm. 2, Pasal 1`
  - Patterns: `[]`
  - Text: Perizinan adalah fungsi perizinan di Bank Indonesia yang berhubungan langsung dengan Pemohon. 5. Konsultasi Awal adalah pelayanan berupa pemberian informasi awal kepada Pemohon.

- `BI` `primary_regulation` `pasal` - PBI No.22/8/PBI/2020 - Perizinan Terpadu Bank Indonesia Melalui Front Office Perizinan
  - Citation: `PBI No.22/8/PBI/2020 - Perizinan Terpadu Bank Indonesia Melalui Front Office Perizinan, hlm. 3, Pasal 1`
  - Patterns: `[]`
  - Text: 6. Hak Akses adalah hak yang diberikan kepada Pemohon berupa nama pengguna dan kata kunci untuk mengakses aplikasi perizinan Bank Indonesia.

- `BI` `primary_regulation` `ayat` - PBI No.22/8/PBI/2020 - Perizinan Terpadu Bank Indonesia Melalui Front Office Perizinan
  - Citation: `PBI No.22/8/PBI/2020 - Perizinan Terpadu Bank Indonesia Melalui Front Office Perizinan, hlm. 3, Pasal 2, ayat (1)`
  - Patterns: `[]`
  - Text: Pasal 2 (1) Prinsip perizinan terpadu Bank Indonesia melalui FO


## `promulgation`

- Description: Promulgation/signature/state-gazette material usually found near closing pages.
- Answer policy: `reject_by_default`
- Count: `6949`
- Rate: `0.01354`
- By issuer: `{'OJK': 6683, 'BI': 266}`
- By role: `{'primary_regulation': 6875, 'attachment': 70, 'operational_requirement': 4}`
- By section type: `{'pasal': 4489, 'paragraph': 1223, 'heading': 498, 'ayat': 379, 'table': 259, 'attachment': 70, 'list_item': 31}`
- Matched patterns: `{'Lembaran\\s+Negara': 4895, 'Tambahan\\s+Lembaran\\s+Negara': 3136, '\\bDitetapkan\\s+di\\b': 2710, '\\bDiundangkan\\s+di\\b': 756, '\\bMENTERI\\s+HUKUM\\s+DAN\\s+HAK\\s+ASASI\\s+MANUSIA\\b': 696}`

### Examples

- `BI` `primary_regulation` `pasal` - PBI No.22/8/PBI/2020 - Perizinan Terpadu Bank Indonesia Melalui Front Office Perizinan
  - Citation: `PBI No.22/8/PBI/2020 - Perizinan Terpadu Bank Indonesia Melalui Front Office Perizinan, hlm. 10, Pasal 22`
  - Patterns: `['Lembaran\\s+Negara', '\\bDiundangkan\\s+di\\b', '\\bDitetapkan\\s+di\\b', '\\bMENTERI\\s+HUKUM\\s+DAN\\s+HAK\\s+ASASI\\s+MANUSIA\\b']`
  - Text: Agar setiap orang mengetahuinya, memerintahkan pengundangan Peraturan Bank Indonesia ini dengan penempatannya dalam Lembaran Negara Republik Indonesia. Ditetapkan di Jakarta pada tanggal 29 April 2020 GUBERNUR BANK INDONESIA, TTD PERRY WARJIYO Diundangkan di Jakarta pada tanggal 30 April 2020................... MENTERI HUKUM DAN HAK ASASI MANUSIA REPUBLIK IN

- `BI` `primary_regulation` `pasal` - PBI No.22/8/PBI/2020 - Perizinan Terpadu Bank Indonesia Melalui Front Office Perizinan
  - Citation: `PBI No.22/8/PBI/2020 - Perizinan Terpadu Bank Indonesia Melalui Front Office Perizinan, hlm. 10, Pasal 22`
  - Patterns: `['Lembaran\\s+Negara']`
  - Text: TTD YASONNA H. LAOLY LEMBARAN NEGARA REPUBLIK INDONESIA TAHUN 2020 NOMOR 127

- `BI` `primary_regulation` `pasal` - PBI No.22/8/PBI/2020 - Perizinan Terpadu Bank Indonesia Melalui Front Office Perizinan
  - Citation: `PBI No.22/8/PBI/2020 - Perizinan Terpadu Bank Indonesia Melalui Front Office Perizinan, hlm. 19, Pasal 22`
  - Patterns: `['Lembaran\\s+Negara', 'Tambahan\\s+Lembaran\\s+Negara']`
  - Text: Cukup jelas. TAMBAHAN LEMBARAN NEGARA REPUBLIK INDONESIA NOMOR 6511

- `BI` `primary_regulation` `paragraph` - PBI No.23/15/PBI/2021 tentang Layanan Kebanksentralan
  - Citation: `PBI No.23/15/PBI/2021 tentang Layanan Kebanksentralan, hlm. 2`
  - Patterns: `['Lembaran\\s+Negara', 'Tambahan\\s+Lembaran\\s+Negara']`
  - Text: Nomor 3843) sebagaimana telah beberapa kali diubah terakhir dengan Undang-Undang Nomor 6 Tahun 2009 tentang Penetapan Peraturan Pemerintah Pengganti Undang-Undang Nomor 2 Tahun 2008 tentang Perubahan Kedua atas Undang- Undang Nomor 23 Tahun 1999 tentang Bank Indonesia Menjadi Undang-Undang (Lembaran Negara Republik Indonesia Tahun 2009 Nomor 7, Tambahan Lemb

- `BI` `primary_regulation` `pasal` - PBI No.23/15/PBI/2021 tentang Layanan Kebanksentralan
  - Citation: `PBI No.23/15/PBI/2021 tentang Layanan Kebanksentralan, hlm. 33, Pasal 62`
  - Patterns: `['Lembaran\\s+Negara', '\\bDiundangkan\\s+di\\b', '\\bDitetapkan\\s+di\\b', '\\bMENTERI\\s+HUKUM\\s+DAN\\s+HAK\\s+ASASI\\s+MANUSIA\\b']`
  - Text: Agar setiap orang mengetahuinya, memerintahkan pengundangan Peraturan Bank Indonesia ini dengan penempatannya dalam Lembaran Negara Republik Indonesia. Ditetapkan di Jakarta pada tanggal 10 September 2021 GUBERNUR BANK INDONESIA, TTD PERRY WARJIYO Diundangkan di Jakarta pada tanggal 10 September 2021.................... MENTERI HUKUM DAN HAK ASASI MANUSIA RE

- `BI` `primary_regulation` `pasal` - PBI No.23/15/PBI/2021 tentang Layanan Kebanksentralan
  - Citation: `PBI No.23/15/PBI/2021 tentang Layanan Kebanksentralan, hlm. 33, Pasal 62`
  - Patterns: `['Lembaran\\s+Negara']`
  - Text: TTD YASONNA H. LAOLY LEMBARAN NEGARA REPUBLIK INDONESIA TAHUN 2021 NOMOR 216....

- `BI` `primary_regulation` `pasal` - PADG Nomor 12 Tahun 2024 - Perizinan Terpadu Bank Indonesia Melalui Front Office Perizinan
  - Citation: `PADG Nomor 12 Tahun 2024 - Perizinan Terpadu Bank Indonesia Melalui Front Office Perizinan, hlm. 14, Pasal 31`
  - Patterns: `['\\bDitetapkan\\s+di\\b']`
  - Text: Peraturan Anggota Dewan Gubernur ini mulai berlaku pada tanggal ditetapkan. Agar setiap orang mengetahuinya, memerintahkan penempatan Peraturan Anggota Dewan Gubernur ini dengan penempatannya dalam Berita Negara Republik Indonesia. Ditetapkan di Jakarta pada tanggal 30 September 2024......................... ANGGOTA DEWAN GUBERNUR, TTD DESTRY DAMAYANTI

- `BI` `primary_regulation` `pasal` - PBI No.22/23/PBI/2020 - Sistem Pembayaran
  - Citation: `PBI No.22/23/PBI/2020 - Sistem Pembayaran, hlm. 50, Pasal 122`
  - Patterns: `['Lembaran\\s+Negara', '\\bDiundangkan\\s+di\\b', '\\bDitetapkan\\s+di\\b', '\\bMENTERI\\s+HUKUM\\s+DAN\\s+HAK\\s+ASASI\\s+MANUSIA\\b']`
  - Text: Agar setiap orang mengetahuinya, memerintahkan pengundangan Peraturan Bank Indonesia ini dengan penempatannya dalam Lembaran Negara Republik Indonesia. Ditetapkan di Jakarta pada tanggal 29 Desember 2020 GUBERNUR BANK INDONESIA, TTD PERRY WARJIYO Diundangkan di Jakarta pada tanggal 30 Desember 2020 MENTERI HUKUM DAN HAK ASASI MANUSIA REPUBLIK INDONESIA,


## `enactment`

- Description: MEMUTUSKAN/Menetapkan enactment bridge text before substantive articles.
- Answer policy: `reject_by_default`
- Count: `1240`
- Rate: `0.00242`
- By issuer: `{'OJK': 1169, 'BI': 71}`
- By role: `{'primary_regulation': 1237, 'attachment': 2, 'operational_requirement': 1}`
- By section type: `{'paragraph': 734, 'pasal': 267, 'heading': 120, 'table': 74, 'ayat': 43, 'attachment': 2}`
- Matched patterns: `{'\\bMenetapkan\\s*:': 1041, '\\bMEMUTUSKAN\\s*:': 944}`

### Examples

- `BI` `primary_regulation` `paragraph` - PBI No.22/8/PBI/2020 - Perizinan Terpadu Bank Indonesia Melalui Front Office Perizinan
  - Citation: `PBI No.22/8/PBI/2020 - Perizinan Terpadu Bank Indonesia Melalui Front Office Perizinan, hlm. 2`
  - Patterns: `['\\bMEMUTUSKAN\\s*:', '\\bMenetapkan\\s*:']`
  - Text: MEMUTUSKAN: Menetapkan : PERATURAN BANK INDONESIA TENTANG PERIZINAN TERPADU BANK INDONESIA MELALUI FRONT OFFICE PERIZINAN. BAB I KETENTUAN UMUM

- `BI` `primary_regulation` `paragraph` - PBI No.23/15/PBI/2021 tentang Layanan Kebanksentralan
  - Citation: `PBI No.23/15/PBI/2021 tentang Layanan Kebanksentralan, hlm. 2`
  - Patterns: `['\\bMEMUTUSKAN\\s*:', '\\bMenetapkan\\s*:']`
  - Text: MEMUTUSKAN: Menetapkan : PERATURAN BANK INDONESIA TENTANG LAYANAN KEBANKSENTRALAN. BAB I KETENTUAN UMUM

- `BI` `primary_regulation` `paragraph` - PADG Nomor 12 Tahun 2024 - Perizinan Terpadu Bank Indonesia Melalui Front Office Perizinan
  - Citation: `PADG Nomor 12 Tahun 2024 - Perizinan Terpadu Bank Indonesia Melalui Front Office Perizinan, hlm. 1`
  - Patterns: `['\\bMEMUTUSKAN\\s*:', '\\bMenetapkan\\s*:']`
  - Text: MEMUTUSKAN: Menetapkan : PERATURAN ANGGOTA DEWAN GUBERNUR TENTANG PERATURAN PELAKSANAAN PERIZINAN TERPADU BANK INDONESIA MELALUI FRONT OFFICE PERIZINAN.

- `BI` `primary_regulation` `paragraph` - PBI No.22/23/PBI/2020 - Sistem Pembayaran
  - Citation: `PBI No.22/23/PBI/2020 - Sistem Pembayaran, hlm. 2`
  - Patterns: `['\\bMEMUTUSKAN\\s*:', '\\bMenetapkan\\s*:']`
  - Text: 2. Undang-Undang Nomor 3 Tahun 2011 tentang Transfer Dana (Lembaran Negara Republik Indonesia Tahun 2011 Nomor 39, Tambahan Lembaran Negara Republik Indonesia Nomor 5204); MEMUTUSKAN: Menetapkan : PERATURAN BANK INDONESIA TENTANG SISTEM PEMBAYARAN. BAB I KETENTUAN UMUM

- `BI` `primary_regulation` `table` - PADG No.23/18/PADG/2021 tentang Peraturan Pelaksanaan Layanan Kebanksentralan
  - Citation: `PADG No.23/18/PADG/2021 tentang Peraturan Pelaksanaan Layanan Kebanksentralan, hlm. 1`
  - Patterns: `['\\bMEMUTUSKAN\\s*:']`
  - Text: | Menimbang | bahwa Peraturan Bank Indonesia mengenai layanaii a. kebariksentralan perlu didukung dengan peraturan pelaksanaan terkait layanan kebanksentralan; b. bahwa berdasarkan pertimbangan sebagaimana dimaksud dalam huru! a, perlu menetapkan Peraturan Anggota Dewan Gubernur tentaiig Peraturan Pelaksanaan Layanan Kebanksentralan; | |---|---| | Mengingat 

- `BI` `primary_regulation` `paragraph` - PBI No.23/6/PBI/2021 - Penyedia Jasa Pembayaran
  - Citation: `PBI No.23/6/PBI/2021 - Penyedia Jasa Pembayaran, hlm. 2`
  - Patterns: `['\\bMEMUTUSKAN\\s*:', '\\bMenetapkan\\s*:']`
  - Text: 2. Peraturan Bank Indonesia Nomor 22/23/PBI/2020 tentang Sistem Pembayaran (Lembaran Negara Republik Indonesia Tahun 2020 Nomor 311, Tambahan Lembaran Negara Republik Indonesia Nomor 6610); MEMUTUSKAN: Menetapkan : PERATURAN BANK INDONESIA TENTANG PENYEDIA JASA PEMBAYARAN. BAB I KETENTUAN UMUM

- `BI` `primary_regulation` `pasal` - PBI No.23/6/PBI/2021 - Penyedia Jasa Pembayaran
  - Citation: `PBI No.23/6/PBI/2021 - Penyedia Jasa Pembayaran, hlm. 39, Pasal 61`
  - Patterns: `['\\bMenetapkan\\s*:']`
  - Text: Bank Indonesia dapat menggunakan klasifikasi PJP sebagai pertimbangan dalam menetapkan: a. arah pengembangan infrastruktur Sistem Pembayaran Bank Indonesia; dan/atau b. perlakuan dalam penyelenggaraan infrastruktur Bank Indonesia dan/atau kebijakan standardisasi.

- `BI` `primary_regulation` `pasal` - PBI No.23/6/PBI/2021 - Penyedia Jasa Pembayaran
  - Citation: `PBI No.23/6/PBI/2021 - Penyedia Jasa Pembayaran, hlm. 90, Pasal 150`
  - Patterns: `['\\bMenetapkan\\s*:']`
  - Text: Indonesia dapat menetapkan: a. kewajiban dan aspek prudensial penyelenggaraan meliputi: 1. fitur, fasilitas dan batasan penyelenggaraan akses ke Sumber Dana; 2. skema harga atas penyelenggaraan akses ke Sumber Dana; 3. standar penyelenggaraan akses ke Sumber Dana; 4. suku bunga, denda keterlambatan, dan minimum pembayaran bagi akses ke Sumber Dana berupa ins


## `legal_preamble`

- Description: Opening title/regulator/preamble text, usually first-page material before operative rules.
- Answer policy: `reject_by_default`
- Count: `1141`
- Rate: `0.00222`
- By issuer: `{'OJK': 1089, 'BI': 52}`
- By role: `{'primary_regulation': 1114, 'attachment': 26, 'operational_requirement': 1}`
- By section type: `{'paragraph': 789, 'pasal': 195, 'ayat': 79, 'heading': 51, 'attachment': 26, 'table': 1}`
- Matched patterns: `{'DENGAN\\s+RAHMAT\\s+TUHAN\\s+YANG\\s+MAHA\\s+ESA': 800, '^(?:OTORITAS\\s+JASA\\s+KEUANGAN|BANK\\s+INDONESIA)\\s+REPUBLIK\\s+INDONESIA': 514, '^(?:SALINAN\\s+)?PERATURAN\\s+(?:OTORITAS\\s+JASA\\s+KEUANGAN|BANK\\s+INDONESIA|ANGGOTA\\s+DEWAN\\s+GUBERNUR)(?:\\s+REPUBLIK\\s+INDONESIA)?\\s+NOMOR\\b': 452, '^(?:SALINAN\\s+)?SURAT\\s+EDARAN\\s+(?:OTORITAS\\s+JASA\\s+KEUANGAN|BANK\\s+INDONESIA)(?:\\s+REPUBLIK\\s+INDONESIA)?\\s+NOMOR\\b': 45, '^(?:SALINAN\\s+)?KEPUTUSAN\\s+(?:DEWAN\\s+KOMISIONER\\s+OTORITAS\\s+JASA\\s+KEUANGAN|GUBERNUR\\s+BANK\\s+INDONESIA|KETUA\\s+BAPEPAM|KETUA\\s+BADAN\\s+PENGAWAS\\s+PASAR\\s+MODAL)\\s+NOMOR\\b': 4}`

### Examples

- `BI` `primary_regulation` `paragraph` - PBI No.22/8/PBI/2020 - Perizinan Terpadu Bank Indonesia Melalui Front Office Perizinan
  - Citation: `PBI No.22/8/PBI/2020 - Perizinan Terpadu Bank Indonesia Melalui Front Office Perizinan, hlm. 1`
  - Patterns: `['DENGAN\\s+RAHMAT\\s+TUHAN\\s+YANG\\s+MAHA\\s+ESA', '^(?:SALINAN\\s+)?PERATURAN\\s+(?:OTORITAS\\s+JASA\\s+KEUANGAN|BANK\\s+INDONESIA|ANGGOTA\\s+DEWAN\\s+GUBERNUR)(?:\\s+REPUBLIK\\s+INDONESIA)?\\s+NOMOR\\b']`
  - Text: PERATURAN BANK INDONESIA NOMOR 22/8/PBI/2020 TENTANG PERIZINAN TERPADU BANK INDONESIA MELALUI FRONT OFFICE PERIZINAN DENGAN RAHMAT TUHAN YANG MAHA ESA GUBERNUR BANK INDONESIA, Menimbang : a. bahwa guna mewujudkan tujuan Bank Indonesia untuk mencapai dan memelihara kestabilan nilai rupiah, Bank Indonesia memiliki tugas di bidang moneter, makroprudensial, sert

- `BI` `primary_regulation` `paragraph` - PBI No.23/15/PBI/2021 tentang Layanan Kebanksentralan
  - Citation: `PBI No.23/15/PBI/2021 tentang Layanan Kebanksentralan, hlm. 1`
  - Patterns: `['^(?:SALINAN\\s+)?PERATURAN\\s+(?:OTORITAS\\s+JASA\\s+KEUANGAN|BANK\\s+INDONESIA|ANGGOTA\\s+DEWAN\\s+GUBERNUR)(?:\\s+REPUBLIK\\s+INDONESIA)?\\s+NOMOR\\b']`
  - Text: PERATURAN BANK INDONESIA NOMOR 23/15/PBI/2021

- `BI` `primary_regulation` `paragraph` - PBI No.23/15/PBI/2021 tentang Layanan Kebanksentralan
  - Citation: `PBI No.23/15/PBI/2021 tentang Layanan Kebanksentralan, hlm. 1`
  - Patterns: `['DENGAN\\s+RAHMAT\\s+TUHAN\\s+YANG\\s+MAHA\\s+ESA']`
  - Text: DENGAN RAHMAT TUHAN YANG MAHA ESA GUBERNUR BANK INDONESIA, Menimbang : a. bahwa untuk mendukung pelaksanaan tugas Bank Indonesia dalam bidang moneter, makroprudensial, serta sistem pembayaran dan pengelolaan uang rupiah, Bank Indonesia memberikan layanan kebanksentralan; b. bahwa dalam memberikan layanan kebanksentralan

- `BI` `primary_regulation` `paragraph` - PADG Nomor 12 Tahun 2024 - Perizinan Terpadu Bank Indonesia Melalui Front Office Perizinan
  - Citation: `PADG Nomor 12 Tahun 2024 - Perizinan Terpadu Bank Indonesia Melalui Front Office Perizinan, hlm. 1`
  - Patterns: `['DENGAN\\s+RAHMAT\\s+TUHAN\\s+YANG\\s+MAHA\\s+ESA']`
  - Text: DENGAN RAHMAT TUHAN YANG MAHA ESA ANGGOTA DEWAN GUBERNUR BANK INDONESIA, Menimbang : a. bahwa Bank Indonesia memberikan perizinan terpadu di bidang moneter, makroprudensial, dan sistem pembayaran secara elektronik; b. bahwa Peraturan Anggota Dewan Gubernur Nomor 22/12/PADG/2020 tentang Peraturan Pelaksanaan Perizinan Terpadu Bank Indonesia Melalui Front Offi

- `BI` `primary_regulation` `paragraph` - PBI No.22/23/PBI/2020 - Sistem Pembayaran
  - Citation: `PBI No.22/23/PBI/2020 - Sistem Pembayaran, hlm. 1`
  - Patterns: `['DENGAN\\s+RAHMAT\\s+TUHAN\\s+YANG\\s+MAHA\\s+ESA', '^(?:SALINAN\\s+)?PERATURAN\\s+(?:OTORITAS\\s+JASA\\s+KEUANGAN|BANK\\s+INDONESIA|ANGGOTA\\s+DEWAN\\s+GUBERNUR)(?:\\s+REPUBLIK\\s+INDONESIA)?\\s+NOMOR\\b']`
  - Text: PERATURAN BANK INDONESIA NOMOR 22/23/PBI/2020 TENTANG SISTEM PEMBAYARAN DENGAN RAHMAT TUHAN YANG MAHA ESA GUBERNUR BANK INDONESIA, Menimbang : a. bahwa perkembangan digitalisasi dan inovasi sistem pembayaran di satu sisi meningkatkan efisiensi industri sistem pembayaran dan percepatan inklusi ekonomi dan keuangan digital, di sisi lain meningkatkan risiko den

- `BI` `primary_regulation` `paragraph` - PBI No.23/6/PBI/2021 - Penyedia Jasa Pembayaran
  - Citation: `PBI No.23/6/PBI/2021 - Penyedia Jasa Pembayaran, hlm. 1`
  - Patterns: `['DENGAN\\s+RAHMAT\\s+TUHAN\\s+YANG\\s+MAHA\\s+ESA', '^(?:SALINAN\\s+)?PERATURAN\\s+(?:OTORITAS\\s+JASA\\s+KEUANGAN|BANK\\s+INDONESIA|ANGGOTA\\s+DEWAN\\s+GUBERNUR)(?:\\s+REPUBLIK\\s+INDONESIA)?\\s+NOMOR\\b']`
  - Text: PERATURAN BANK INDONESIA NOMOR 23/6/PBI/2021 TENTANG PENYEDIA JASA PEMBAYARAN DENGAN RAHMAT TUHAN YANG MAHA ESA GUBERNUR BANK INDONESIA, Menimbang : a. bahwa reformasi pengaturan sistem pembayaran termasuk penyediaan jasa pembayaran, perlu dilakukan sejalan dengan pemenuhan prinsip penyelenggaraan sistem pembayaran yang cepat, mudah, murah, aman, dan andal, 

- `BI` `primary_regulation` `paragraph` - PBI No.23/11/PBI/2021 - Standar Nasional Sistem Pembayaran
  - Citation: `PBI No.23/11/PBI/2021 - Standar Nasional Sistem Pembayaran, hlm. 1`
  - Patterns: `['DENGAN\\s+RAHMAT\\s+TUHAN\\s+YANG\\s+MAHA\\s+ESA']`
  - Text: Menimbang : a. b. c. d. PERATURAN BANK INDONESIA NOMOR 23/ 11 /PBI/2021 TENTANG STANDAR NASIONAL SISTEM PEMBAYARAN DENGAN RAHMAT TUHAN YANG MAHA ESA GUBERNUR BANK INDONESIA, bahwa reformasi pengaturan sistem pembayaran perlu dilakukan sejalan dengan pemenuhan prinsip penyelenggaraan sistem pembayaran yang cepat, mudah, murah, aman, dan andal, dengan tetap me

- `BI` `primary_regulation` `paragraph` - PBI No.23/7/PBI/2021 - Penyelenggara Infrastruktur Sistem Pembayaran
  - Citation: `PBI No.23/7/PBI/2021 - Penyelenggara Infrastruktur Sistem Pembayaran, hlm. 1`
  - Patterns: `['DENGAN\\s+RAHMAT\\s+TUHAN\\s+YANG\\s+MAHA\\s+ESA', '^(?:SALINAN\\s+)?PERATURAN\\s+(?:OTORITAS\\s+JASA\\s+KEUANGAN|BANK\\s+INDONESIA|ANGGOTA\\s+DEWAN\\s+GUBERNUR)(?:\\s+REPUBLIK\\s+INDONESIA)?\\s+NOMOR\\b']`
  - Text: PERATURAN BANK INDONESIA NOMOR 23/7/PBI/2021 TENTANG PENYELENGGARA INFRASTRUKTUR SISTEM PEMBAYARAN DENGAN RAHMAT TUHAN YANG MAHA ESA GUBERNUR BANK INDONESIA, Menimbang : a. bahwa reformasi pengaturan sistem pembayaran bertujuan untuk mencari titik keseimbangan antara upaya optimalisasi peluang inovasi digital untuk menciptakan sistem pembayaran yang cepat, m


## `legal_basis_reference`

- Description: Mengingat/statutory reference lists that cite enabling laws rather than the answer itself.
- Answer policy: `reject_by_default`
- Count: `931`
- Rate: `0.00181`
- By issuer: `{'OJK': 887, 'BI': 44}`
- By role: `{'primary_regulation': 930, 'operational_requirement': 1}`
- By section type: `{'paragraph': 721, 'pasal': 148, 'list_item': 32, 'ayat': 25, 'heading': 3, 'table': 2}`
- Matched patterns: `{'\\bMengingat\\s*:': 931}`

### Examples

- `BI` `primary_regulation` `paragraph` - PBI No.22/8/PBI/2020 - Perizinan Terpadu Bank Indonesia Melalui Front Office Perizinan
  - Citation: `PBI No.22/8/PBI/2020 - Perizinan Terpadu Bank Indonesia Melalui Front Office Perizinan, hlm. 2`
  - Patterns: `['\\bMengingat\\s*:']`
  - Text: Mengingat : Undang-Undang Nomor 23 Tahun 1999 tentang Bank Indonesia (Lembaran Negara Republik Indonesia Tahun 1999 Nomor 66, Tambahan Lembaran Negara Republik Indonesia Nomor 3843) sebagaimana telah beberapa kali diubah, terakhir dengan Undang-Undang Nomor 6 Tahun 2009 tentang Penetapan Peraturan Pemerintah Pengganti Undang-Undang Nomor 2 Tahun 2008 tentang

- `BI` `primary_regulation` `paragraph` - PBI No.23/15/PBI/2021 tentang Layanan Kebanksentralan
  - Citation: `PBI No.23/15/PBI/2021 tentang Layanan Kebanksentralan, hlm. 1`
  - Patterns: `['\\bMengingat\\s*:']`
  - Text: infrastruktur layanan secara elektronik dengan dukungan aplikasi layanan Bank Indonesia; c. bahwa berdasarkan pertimbangan sebagaimana dimaksud dalam huruf a dan huruf b, perlu menetapkan Peraturan Bank Indonesia tentang Layanan Kebanksentralan; Mengingat : Undang-Undang Nomor 23 Tahun 1999 tentang Bank Indonesia (Lembaran Negara Republik Indonesia Tahun 199

- `BI` `primary_regulation` `paragraph` - PADG Nomor 12 Tahun 2024 - Perizinan Terpadu Bank Indonesia Melalui Front Office Perizinan
  - Citation: `PADG Nomor 12 Tahun 2024 - Perizinan Terpadu Bank Indonesia Melalui Front Office Perizinan, hlm. 1`
  - Patterns: `['\\bMengingat\\s*:']`
  - Text: dalam huruf a dan huruf b, perlu menetapkan Peraturan Anggota Dewan Gubernur tentang Peraturan Pelaksanaan Perizinan Terpadu Bank Indonesia Melalui Front Office Perizinan; Mengingat : Peraturan Bank Indonesia Nomor 22/8/PBI/2020 tentang Perizinan Terpadu Bank Indonesia Melalui Front Office Perizinan (Lembaran Negara Republik Indonesia Tahun 2020 Nomor 127, T

- `BI` `primary_regulation` `paragraph` - PBI No.22/23/PBI/2020 - Sistem Pembayaran
  - Citation: `PBI No.22/23/PBI/2020 - Sistem Pembayaran, hlm. 2`
  - Patterns: `['\\bMengingat\\s*:']`
  - Text: Mengingat : 1. Undang-Undang Nomor 23 Tahun 1999 tentang Bank Indonesia (Lembaran Negara Republik Indonesia Tahun 1999 Nomor 66, Tambahan Lembaran Negara Republik Indonesia Nomor 3843) sebagaimana telah beberapa kali diubah, terakhir dengan Undang-Undang Nomor 6 Tahun 2009 tentang Penetapan Peraturan Pemerintah Pengganti Undang-Undang Nomor 2 Tahun 2008 tent

- `BI` `primary_regulation` `paragraph` - PBI No.23/6/PBI/2021 - Penyedia Jasa Pembayaran
  - Citation: `PBI No.23/6/PBI/2021 - Penyedia Jasa Pembayaran, hlm. 2`
  - Patterns: `['\\bMengingat\\s*:']`
  - Text: dalam huruf a, huruf b, dan huruf c, perlu menetapkan Peraturan Bank Indonesia tentang Penyedia Jasa Pembayaran; Mengingat : 1. Undang-Undang Nomor 23 Tahun 1999 tentang Bank Indonesia (Lembaran Negara Republik Indonesia Tahun 1999 Nomor 66, Tambahan Lembaran Negara Republik Indonesia Nomor 3843) sebagaimana telah beberapa kali diubah terakhir dengan Undang-

- `BI` `primary_regulation` `paragraph` - PBI No.23/11/PBI/2021 - Standar Nasional Sistem Pembayaran
  - Citation: `PBI No.23/11/PBI/2021 - Standar Nasional Sistem Pembayaran, hlm. 2`
  - Patterns: `['\\bMengingat\\s*:']`
  - Text: Peraturan Bank Indonesia tentang Standar Nasional Sistem Pembayaran; Mengingat : 1. Undang-Undang Nomor 23 Tahun 1999 tentang Bank Indonesia (Lembaran Negara Republik Indonesia Tahun 1999 Nomor 66, Tambahan Lembaran Negara Republik Indonesia Nomor 3843) sebagaimana telah beberapa kali diubah terakhir dengan Undang-Undang Nomor 6 Tahun 2009 tentang Penetapan 

- `BI` `primary_regulation` `paragraph` - PBI No.23/7/PBI/2021 - Penyelenggara Infrastruktur Sistem Pembayaran
  - Citation: `PBI No.23/7/PBI/2021 - Penyelenggara Infrastruktur Sistem Pembayaran, hlm. 2`
  - Patterns: `['\\bMengingat\\s*:']`
  - Text: dalam huruf a, huruf b, dan huruf c, perlu menetapkan Peraturan Bank Indonesia tentang Penyelenggara Infrastruktur Sistem Pembayaran; Mengingat : 1. Undang-Undang Nomor 23 Tahun 1999 tentang Bank Indonesia (Lembaran Negara Republik Indonesia Tahun 1999 Nomor 66, Tambahan Lembaran Negara Republik Indonesia Nomor 3843) sebagaimana telah beberapa kali diubah te

- `BI` `primary_regulation` `paragraph` - PADG No.23/15/PADG/2021 - Implementasi Standar Nasional Open Application Programming Interface Pembayaran
  - Citation: `PADG No.23/15/PADG/2021 - Implementasi Standar Nasional Open Application Programming Interface Pembayaran, hlm. 2`
  - Patterns: `['\\bMengingat\\s*:']`
  - Text: *Programming Interface Pembayaran;* Mengingat : 1. Peraturan Bank Indonesia Nomor 22/23/PBI/2020 tentang Sistem Pembayaran (Lembaran Negara Republik Indonesia Tahun 2020 Nomor 311, Tambahan Lembaran Negara Republik Indonesia Nomor 6610); 2. Peraturan Bank Indonesia Nomor 23/6/PBI/2021 tentang Penyedia Jasa Pembayaran (Lembaran Negara Republik Indonesia Tahun


## `consideration`

- Description: Menimbang/konsiderans material that explains reasons but usually does not state operative obligations.
- Answer policy: `reject_by_default`
- Count: `309`
- Rate: `0.0006`
- By issuer: `{'OJK': 308, 'BI': 1}`
- By role: `{'primary_regulation': 309}`
- By section type: `{'paragraph': 236, 'pasal': 33, 'heading': 18, 'ayat': 18, 'table': 4}`
- Matched patterns: `{'\\bMenimbang\\s*:': 309}`

### Examples

- `BI` `primary_regulation` `heading` - PBI No.14/23/PBI/2012 - Transfer Dana
  - Citation: `PBI No.14/23/PBI/2012 - Transfer Dana, hlm. 1`
  - Patterns: `['\\bMenimbang\\s*:']`
  - Text: # Menimbang: a. bahwa untuk menjaga keamanan dan kelancaran sistem pembayaran serta memberikan kepastian

- `OJK` `primary_regulation` `ayat` - Pedoman Penyampaian Informasi oleh Emiten atau Perusahaan Publik dalam Rangka Penyusunan Daftar Efek Syariah dan Pedoman Bagi Pihak Penerbit Daftar Efek Syariah
  - Citation: `Pedoman Penyampaian Informasi oleh Emiten atau Perusahaan Publik dalam Rangka Penyusunan Daftar Efek Syariah dan Pedoman Bagi Pihak Penerbit Daftar Efek Syariah, hlm. 1, Pasal 7, ayat (3)`
  - Patterns: `['\\bMenimbang\\s*:']`
  - Text: Menimbang : a. bahwa untuk memberikan pedoman penyampaian informasi oleh emiten dan perusahaan publik dalam rangka penyusunan daftar efek syariah serta memberikan pedoman bagi pihak penerbit daftar efek syariah, Otoritas Jasa Keuangan perlu menetapkan ketentuan yang mengaturnya; b. bahwa untuk melaksanakan amanat Pasal 7 dan Pasal 21 ayat (3) serta menindakl

- `OJK` `primary_regulation` `paragraph` - Penyediaan Informasi dan Penyampaian Informasi untuk Pemasaran Produk dan Layanan Jasa Keuangan
  - Citation: `Penyediaan Informasi dan Penyampaian Informasi untuk Pemasaran Produk dan Layanan Jasa Keuangan, hlm. 1`
  - Patterns: `['\\bMenimbang\\s*:']`
  - Text: Menimbang : a. bahwa dengan berlakunya Undang-Undang Nomor 4 Tahun 2023 tentang Pengembangan dan Penguatan Sektor Keuangan terdapat penguatan kewenangan Otoritas Jasa Keuangan untuk menyusun peraturan pelindungan konsumen dan masyarakat termasuk mengenai penyediaan informasi, penyampaian informasi untuk pemasaran, dan ringkasan informasi produk dan/atau laya

- `OJK` `primary_regulation` `paragraph` - Perubahan Atas Peraturan Otoritas Jasa Keuangan Nomor 49 Tahun 2024 tentang Pengawasan, Penetapan Status Pengawasan, dan Tindak Lanjut Pengawasan Lembaga Pembiayaan, Perusahaan Modal Ventura, Lembaga Keuangan Mikro, dan Lembaga Jasa Keuangan Lainnya
  - Citation: `Perubahan Atas Peraturan Otoritas Jasa Keuangan Nomor 49 Tahun 2024 tentang Pengawasan, Penetapan Status Pengawasan, dan Tindak Lanjut Pengawasan Lembaga Pembiayaan, Perusahaan Modal Ventura, Lembaga Keuangan Mikro, dan Lembaga Jasa Keuangan Lainnya, hlm. 1`
  - Patterns: `['\\bMenimbang\\s*:']`
  - Text: DEWAN KOMISIONER OTORITAS JASA KEUANGAN, Menimbang : a. bahwa dengan adanya perlambatan kondisi perekonomian yang berdampak pada kemampuan membayar bagi debitur dan pada rasio ekuitas terhadap modal disetor dan untuk menyesuaikan penambahan pemberlakuan masa peralihan atas parameter rasio ekuitas terhadap modal disetor bagi Lembaga Keuangan Mikro sehingga Pe

- `OJK` `primary_regulation` `ayat` - Perubahan atas POJK Nomor 28/POJK.05/2015 tentang Pembubaran, Likuidasi, dan Kepailitan Perusahaan Asuransi, Perusahaan Asuransi Syariah, Perusahaan Reasuransi, dan Perusahaan Reasuransi Syariah
  - Citation: `Perubahan atas POJK Nomor 28/POJK.05/2015 tentang Pembubaran, Likuidasi, dan Kepailitan Perusahaan Asuransi, Perusahaan Asuransi Syariah, Perusahaan Reasuransi, dan Perusahaan Reasuransi Syariah, hlm. 1, Pasal 50, ayat (1)`
  - Patterns: `['\\bMenimbang\\s*:']`
  - Text: Menimbang : a. bahwa untuk meningkatkan efektivitas pelaksanaan pembubaran, likuidasi, dan kepailitan perusahaan asuransi, perusahaan asuransi syariah, perusahaan reasuransi, dan perusahaan reasuransi syariah, serta untuk melaksanakan ketentuan Pasal 50 ayat (1) dan ayat (2), dan Pasal 51 ayat (4) Undang-Undang Nomor 40 Tahun 2014 tentang Perasuransian sebag

- `OJK` `primary_regulation` `ayat` - Perubahan Atas Peraturan Otoritas Jasa Keuangan Nomor 69/POJK.05/2016 tentang Penyelenggaraan Usaha Perusahaan Asuransi, Perusahaan Asuransi Syariah, Perusahaan Reasuransi, dan Perusahaan Reasuransi Syariah
  - Citation: `Perubahan Atas Peraturan Otoritas Jasa Keuangan Nomor 69/POJK.05/2016 tentang Penyelenggaraan Usaha Perusahaan Asuransi, Perusahaan Asuransi Syariah, Perusahaan Reasuransi, dan Perusahaan Reasuransi Syariah, hlm. 1, Pasal 5, ayat (5)`
  - Patterns: `['\\bMenimbang\\s*:']`
  - Text: Menimbang : a. bahwa untuk melaksanakan ketentuan Pasal 5 ayat (5),

- `OJK` `primary_regulation` `paragraph` - Penerapan Program Anti Pencucian Uang, Pencegahan Pendanaan Terorisme, dan Pencegahan Pendanaan Proliferasi Senjata Pemusnah Massal di Sektor Jasa Keuangan
  - Citation: `Penerapan Program Anti Pencucian Uang, Pencegahan Pendanaan Terorisme, dan Pencegahan Pendanaan Proliferasi Senjata Pemusnah Massal di Sektor Jasa Keuangan, hlm. 1`
  - Patterns: `['\\bMenimbang\\s*:']`
  - Text: Menimbang : a. bahwa untuk melakukan penguatan pencegahan tindak pidana pencucian uang, tindak pidana pendanaan terorisme, dan pendanaan proliferasi senjata pemusnah massal serta untuk mewujudkan integritas di sektor jasa keuangan, Otoritas Jasa Keuangan berkomitmen untuk mendukung regulasi yang sesuai dengan perkembangan prinsip internasional yang mengatur 

- `OJK` `primary_regulation` `ayat` - Perubahan Kedua Atas Peraturan Otoritas Jasa Keuangan Nomor 71/POJK.05/2016 Tentang Kesehatan Keuangan Perusahaan Asuransi Dan Perusahaan Reasuransi
  - Citation: `Perubahan Kedua Atas Peraturan Otoritas Jasa Keuangan Nomor 71/POJK.05/2016 Tentang Kesehatan Keuangan Perusahaan Asuransi Dan Perusahaan Reasuransi, hlm. 1, Pasal 83, ayat (6)`
  - Patterns: `['\\bMenimbang\\s*:']`
  - Text: Menimbang : a. bahwa dalam mengelola risiko terkait penempatan investasi dan menjaga kesehatan keuangan, perusahaan asuransi dan perusahaan reasuransi harus menerapkan prinsip kehati-hatian; b. bahwa untuk melaksanakan ketentuan Pasal 83 ayat (6) Undang-Undang Nomor 4 Tahun 2023 tentang Pengembangan dan Penguatan Sektor Jasa Keuangan dan untuk melakukan miti


## `letter_intro`

- Description: OJK/BI circular-letter introductory material before concrete provisions.
- Answer policy: `reject_by_default`
- Count: `161`
- Rate: `0.00031`
- By issuer: `{'OJK': 161}`
- By role: `{'primary_regulation': 159, 'attachment': 2}`
- By section type: `{'paragraph': 131, 'ayat': 16, 'pasal': 9, 'heading': 2, 'attachment': 2, 'table': 1}`
- Matched patterns: `{'\\bdi\\s+tempat\\b.*\\bSALINAN\\s+SURAT\\s+EDARAN\\b': 126, '\\bYth\\.?\\s+(?:Direksi|Pengurus|Dewan\\s+Komisioner)': 65, 'Sehubungan\\s+dengan\\s+amanat': 15}`

### Examples

- `OJK` `primary_regulation` `paragraph` - Perubahan Atas Surat Edaran Otoritas Jasa Keuangan Nomor 25/SEOJK.05/2019 tentang Laporan Bulanan Perusahaan Modal Ventura dan Perusahaan Modal Ventura Syariah
  - Citation: `Perubahan Atas Surat Edaran Otoritas Jasa Keuangan Nomor 25/SEOJK.05/2019 tentang Laporan Bulanan Perusahaan Modal Ventura dan Perusahaan Modal Ventura Syariah, hlm. 1`
  - Patterns: `['\\bdi\\s+tempat\\b.*\\bSALINAN\\s+SURAT\\s+EDARAN\\b']`
  - Text: Yth. 1. Direksi Perusahaan Modal Ventura; dan 2. Direksi Perusahaan Modal Ventura Syariah, di tempat. SALINAN SURAT EDARAN OTORITAS JASA KEUANGAN REPUBLIK INDONESIA NOMOR 23/SEOJK.06/2025 TENTANG PERUBAHAN ATAS SURAT EDARAN OTORITAS JASA KEUANGAN NOMOR 25/SEOJK.05/2019 TENTANG LAPORAN BULANAN PERUSAHAAN MODAL VENTURA DAN PERUSAHAAN MODAL VENTURA SYARIAH

- `OJK` `primary_regulation` `paragraph` - Lembaga Pemeringkat dan Peringkat yang Diakui Otoritas Jasa Keuangan
  - Citation: `Lembaga Pemeringkat dan Peringkat yang Diakui Otoritas Jasa Keuangan, hlm. 1`
  - Patterns: `['\\bdi\\s+tempat\\b.*\\bSALINAN\\s+SURAT\\s+EDARAN\\b']`
  - Text: Yth. 1. 2. 3. 4. 5. Direksi Bank Umum Konvensional; Direksi Bank Umum Syariah; Direksi Bank Perekonomian Rakyat; Direksi Bank Perekonomian Rakyat Syariah; dan Direksi Lembaga Pemeringkat, di tempat. SALINAN SURAT EDARAN OTORITAS JASA KEUANGAN REPUBLIK INDONESIA NOMOR 27/SEOJK.03/2025 TENTANG LEMBAGA PEMERINGKAT DAN PERINGKAT YANG DIAKUI OTORITAS JASA KEUANGA

- `OJK` `primary_regulation` `paragraph` - Laporan Penerapan Tata Kelola yang Baik Bagi Lembaga Pembiayaan, Perusahaan Modal Ventura, Lembaga Keuangan Mikro, dan Lembaga Jasa Keuangan Lainnya
  - Citation: `Laporan Penerapan Tata Kelola yang Baik Bagi Lembaga Pembiayaan, Perusahaan Modal Ventura, Lembaga Keuangan Mikro, dan Lembaga Jasa Keuangan Lainnya, hlm. 1`
  - Patterns: `['\\bdi\\s+tempat\\b.*\\bSALINAN\\s+SURAT\\s+EDARAN\\b']`
  - Text: Yth. 1. Direksi Perusahaan Pembiayaan; 2. Direksi Perusahaan Pembiayaan Infrastruktur; 3. Direksi Perusahaan Modal Ventura; 4. Direksi Lembaga Keuangan Mikro; 5. Direksi Perusahaan Pergadaian; dan 6. Direksi Penyelenggara Layanan Pendanaan Bersama Berbasis Teknologi Informasi, di tempat. SALINAN SURAT EDARAN OTORITAS JASA KEUANGAN NOMOR 28/SEOJK.06/2025 TENT

- `OJK` `primary_regulation` `paragraph` - Verifikasi Pesanan dan Dana, Alokasi Penjatahan dan Penyelesaian Pemesanan Efek dalam Penawaran Umum Saham Secara Elektronik
  - Citation: `Verifikasi Pesanan dan Dana, Alokasi Penjatahan dan Penyelesaian Pemesanan Efek dalam Penawaran Umum Saham Secara Elektronik, hlm. 1`
  - Patterns: `['\\bdi\\s+tempat\\b.*\\bSALINAN\\s+SURAT\\s+EDARAN\\b']`
  - Text: Yth. 1. 2. 3. 4. 5. 6. 7. Direksi Emiten; Direksi Perusahaan Efek; Direksi Bursa Efek; Direksi Lembaga Penyimpanan dan Penyelesaian; Direksi Lembaga Kliring dan Penjaminan; Direksi Biro Administrasi Efek; dan Pemodal atau Investor Pasar Modal Indonesia, di tempat. SALINAN SURAT EDARAN OTORITAS JASA KEUANGAN REPUBLIK INDONESIA NOMOR 25/SEOJK.04/2025 TENTANG V

- `OJK` `primary_regulation` `paragraph` - Penilaian Kemampuan dan Kepatutan Serta Penilaian Kembali Bagi Pihak Utama di Sektor Inovasi Teknologi Sektor Keuangan serta Aset Keuangan Digital dan Aset Kripto
  - Citation: `Penilaian Kemampuan dan Kepatutan Serta Penilaian Kembali Bagi Pihak Utama di Sektor Inovasi Teknologi Sektor Keuangan serta Aset Keuangan Digital dan Aset Kripto, hlm. 1`
  - Patterns: `['\\bdi\\s+tempat\\b.*\\bSALINAN\\s+SURAT\\s+EDARAN\\b']`
  - Text: Yth. Pihak Utama Penyelenggara Inovasi Teknologi Sektor Keuangan, Aset Keuangan Digital dan Aset Kripto, di tempat. SALINAN SURAT EDARAN OTORITAS JASA KEUANGAN REPUBLIK INDONESIA NOMOR 21/SEOJK.07/2025 TENTANG PENILAIAN KEMAMPUAN DAN KEPATUTAN SERTA PENILAIAN KEMBALI BAGI PIHAK UTAMA DI SEKTOR INOVASI TEKNOLOGI KEUANGAN, SERTA ASET KEUANGAN DIGITAL DAN ASET 

- `OJK` `primary_regulation` `paragraph` - Sertifikasi Kompetensi Kerja bagi Perusahaan Perasuransian, Lembaga Penjamin, Dana Pensiun, serta Lembaga Khusus Bidang Perasuransian, Penjaminan, dan Dana Pensiun
  - Citation: `Sertifikasi Kompetensi Kerja bagi Perusahaan Perasuransian, Lembaga Penjamin, Dana Pensiun, serta Lembaga Khusus Bidang Perasuransian, Penjaminan, dan Dana Pensiun, hlm. 1`
  - Patterns: `['\\bdi\\s+tempat\\b.*\\bSALINAN\\s+SURAT\\s+EDARAN\\b']`
  - Text: Yth. Yth. 1. Direksi Perusahaan Perasuransian; 2. Direksi Lembaga Penjamin; 3. Pengurus Dana Pensiun; dan 4. Direksi Lembaga Khusus Bidang Perasuransian, Penjaminan, dan Dana Pensiun, di tempat. SALINAN SURAT EDARAN OTORITAS JASA KEUANGAN REPUBLIK INDONESIA NOMOR 12/SEOJK.05/2025 TENTANG SERTIFIKASI KOMPETENSI KERJA BAGI PERUSAHAAN PERASURANSIAN, LEMBAGA PEN

- `OJK` `primary_regulation` `paragraph` - Penyampaian Laporan Kepemilikan atau Setiap Perubahan Kepemilikan Saham Perusahaan Terbuka dan Laporan Aktivitas Menjaminkan Saham Perusahaan Terbuka Secara Elektronik
  - Citation: `Penyampaian Laporan Kepemilikan atau Setiap Perubahan Kepemilikan Saham Perusahaan Terbuka dan Laporan Aktivitas Menjaminkan Saham Perusahaan Terbuka Secara Elektronik, hlm. 1`
  - Patterns: `['\\bdi\\s+tempat\\b.*\\bSALINAN\\s+SURAT\\s+EDARAN\\b']`
  - Text: Yth. 1. Direksi PT Kustodian Sentral Efek Indonesia; 2. Direksi PT Bursa Efek Indonesia; 3. Direksi Perusahaan Terbuka; 4. Direksi Perusahaan Efek yang Melakukan Kegiatan Usaha Sebagai Perantara Pedagang Efek; 5. Direksi Biro Adminstrasi Efek; dan 6. Direksi Bank Kustodian, di tempat SALINAN SURAT EDARAN OTORITAS JASA KEUANGAN REPUBLIK INDONESIA NOMOR 10/SEO

- `OJK` `primary_regulation` `paragraph` - Bentuk dan Susunan Laporan Berkala Perusahaan Pialang Asuransi, Perusahaan Pialang Reasuransi, dan Perusahaan Penilaian Kerugian Asuransi
  - Citation: `Bentuk dan Susunan Laporan Berkala Perusahaan Pialang Asuransi, Perusahaan Pialang Reasuransi, dan Perusahaan Penilaian Kerugian Asuransi, hlm. 1`
  - Patterns: `['\\bdi\\s+tempat\\b.*\\bSALINAN\\s+SURAT\\s+EDARAN\\b']`
  - Text: Yth. 1. Direksi Perusahaan Pialang Asuransi; 2. Direksi Perusahaan Pialang Reasuransi; dan 3. Direksi Perusahaan Penilai Kerugian Asuransi, di tempat. SALINAN SURAT EDARAN OTORITAS JASA KEUANGAN REPUBLIK INDONESIA NOMOR 13/SEOJK.05/2025 TENTANG BENTUK DAN SUSUNAN LAPORAN BERKALA PERUSAHAAN PIALANG ASURANSI, PERUSAHAAN PIALANG REASURANSI, DAN
