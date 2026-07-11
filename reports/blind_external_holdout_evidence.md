# Evidence Evaluation

- Questions: 19
- Accepted: 18/19
- Average score: 0.945
- By behavior: `{'answerable': 13, 'not_found': 3, 'partial': 3}`
- Report kind: `external_holdout`

## Failures

### blind_not_found_staff_uniform

- Query: `apa ketentuan BI mengenai warna seragam petugas pemasaran bank?`
- Expected: `not_found`
- Score: `0.0`
- Confidence: `strong` / not_found `False`
- Failure reasons: `['expected not_found but evidence did not require refusal']`
- Document hits: `[]`
- Issuer hits: `[]`
- Top documents:
  - `BI` `primary_regulation` - PADG No.20 Tahun 2023 - Tata Cara Pelaksanaan Pelindungan Konsumen Bank Indonesia
  - `BI` `primary_regulation` - PADG No.24/15/PADG/2022 - Laporan Pembawaan Uang Kertas Asing ke Dalam dan ke Luar Daerah Pabean Indonesia
  - `BI` `primary_regulation` - SEBI No.18/42/DKSP - Kegiatan Usaha Penukaran Valuta Asing Bukan Bank (KUPVA BB)
  - `BI` `primary_regulation` - PBI No.23/6/PBI/2021 - Penyedia Jasa Pembayaran
  - `BI` `primary_regulation` - PBI No.23/15/PBI/2021 tentang Layanan Kebanksentralan

## All Questions

### blind_bi_transfer_dana

- Accepted: `True`
- Score: `1.0`
- Expected: `answerable`
- Confidence: `strong` / not_found `False`
- Document hits: `['Transfer Dana']`
- Issuer hits: `['BI']`

### blind_bi_pengelolaan_uang_rupiah

- Accepted: `True`
- Score: `1.0`
- Expected: `answerable`
- Confidence: `strong` / not_found `False`
- Document hits: `['Pengelolaan Uang Rupiah']`
- Issuer hits: `['BI']`

### blind_bi_kupva_bukan_bank

- Accepted: `True`
- Score: `1.0`
- Expected: `answerable`
- Confidence: `strong` / not_found `False`
- Document hits: `['Penukaran Valuta Asing Bukan Bank']`
- Issuer hits: `['BI']`

### blind_bi_pasar_uang_valas

- Accepted: `True`
- Score: `1.0`
- Expected: `answerable`
- Confidence: `strong` / not_found `False`
- Document hits: `['Pasar Uang dan Pasar Valuta Asing']`
- Issuer hits: `['BI']`

### blind_bi_operasi_moneter

- Accepted: `True`
- Score: `1.0`
- Expected: `answerable`
- Confidence: `strong` / not_found `False`
- Document hits: `['Kepesertaan Operasi Moneter']`
- Issuer hits: `['BI']`

### blind_ojk_bank_kustodian

- Accepted: `True`
- Score: `1.0`
- Expected: `answerable`
- Confidence: `strong` / not_found `False`
- Document hits: `['Laporan Bank Umum Sebagai Kustodian']`
- Issuer hits: `['OJK']`

### blind_ojk_bmpk_bpr

- Accepted: `True`
- Score: `1.0`
- Expected: `answerable`
- Confidence: `strong` / not_found `False`
- Document hits: `['Batas Maksimum Pemberian Kredit']`
- Issuer hits: `['OJK']`

### blind_ojk_lcr_nsfr_syariah

- Accepted: `True`
- Score: `1.0`
- Expected: `answerable`
- Confidence: `strong` / not_found `False`
- Document hits: `['Liquidity Coverage Ratio']`
- Issuer hits: `['OJK']`

### blind_ojk_kebijakan_perkreditan

- Accepted: `True`
- Score: `1.0`
- Expected: `answerable`
- Confidence: `strong` / not_found `False`
- Document hits: `['Kebijakan Perkreditan']`
- Issuer hits: `['OJK']`

### blind_ojk_lembaga_keuangan_mikro

- Accepted: `True`
- Score: `1.0`
- Expected: `answerable`
- Confidence: `strong` / not_found `False`
- Document hits: `['Lembaga Keuangan Mikro']`
- Issuer hits: `['OJK']`

### blind_ojk_pergadaian

- Accepted: `True`
- Score: `1.0`
- Expected: `answerable`
- Confidence: `strong` / not_found `False`
- Document hits: `['Usaha Pergadaian']`
- Issuer hits: `['OJK']`

### blind_ojk_modal_ventura

- Accepted: `True`
- Score: `1.0`
- Expected: `answerable`
- Confidence: `strong` / not_found `False`
- Document hits: `['Penyelenggaraan Usaha Perusahaan Modal Ventura']`
- Issuer hits: `['OJK']`

### blind_ojk_laporan_dana_pensiun

- Accepted: `True`
- Score: `1.0`
- Expected: `answerable`
- Confidence: `strong` / not_found `False`
- Document hits: `['Laporan Berkala Dana Pensiun']`
- Issuer hits: `['OJK']`

### blind_cross_pjp

- Accepted: `True`
- Score: `0.95`
- Expected: `partial`
- Confidence: `partial` / not_found `False`
- Document hits: `['Penyedia Jasa Pembayaran']`
- Issuer hits: `['BI', 'OJK']`

### blind_cross_consumer_protection

- Accepted: `True`
- Score: `1.0`
- Expected: `partial`
- Confidence: `strong` / not_found `False`
- Document hits: `['Pelindungan Konsumen']`
- Issuer hits: `['BI', 'OJK']`

### blind_cross_apu_ppt

- Accepted: `True`
- Score: `1.0`
- Expected: `partial`
- Confidence: `strong` / not_found `False`
- Document hits: `['Anti Pencucian Uang']`
- Issuer hits: `['BI', 'OJK']`

### blind_not_found_office_furniture

- Accepted: `True`
- Score: `1.0`
- Expected: `not_found`
- Confidence: `weak` / not_found `True`
- Document hits: `[]`
- Issuer hits: `[]`

### blind_not_found_staff_uniform

- Accepted: `False`
- Score: `0.0`
- Expected: `not_found`
- Confidence: `strong` / not_found `False`
- Document hits: `[]`
- Issuer hits: `[]`

### blind_not_found_mars

- Accepted: `True`
- Score: `1.0`
- Expected: `not_found`
- Confidence: `weak` / not_found `True`
- Document hits: `[]`
- Issuer hits: `[]`

