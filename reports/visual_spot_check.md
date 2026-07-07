# Visual Spot Check

Rendered page review for high-value extraction cases after selective OCR and Office replacement.

## Scope

Rendered with LibreOffice for Office files and `pypdfium2` for page images. Temporary render outputs were written under `/private/tmp/thinking-layer-visual-check`.

| Case | Source | Pages Reviewed | Visual Finding | Extraction Risk |
|---|---|---:|---|---|
| BI QRIS Office Matrix | `downloads/ease-bi/dokumen-persyaratan-pedoman/2. Dokumen Pedoman dan Persyaratan Permohonan Persetujuan dan Pelaporan SP Ritel/j. Matriks Tambahan Dokumen Pengembangan QRIS.docx` | 1 | Table is legible with clear columns for requirement, document availability, and explanation. | LiteParse captures the table as Markdown, but metadata fields above the table are flattened and may lose label/value pairing. |
| BI SNAP Office Matrix | `downloads/ease-bi/dokumen-persyaratan-pedoman/4. Standar Nasional Open API Pembayaran (SNAP)/Matriks Tambahan_Pengembangan dengan SNAP.docx` | 1-3 | Page 1 is a clear table. Pages 2-3 are continuation pages with most useful text in the rightmost explanation column and mostly blank left columns. | Continuation pages can lose row/column context; page 3 has table borders visually but weak table markers in extracted Markdown. |
| BI SNAP Functional Test XLSX | `downloads/ease-bi/dokumen-persyaratan-pedoman/4. Standar Nasional Open API Pembayaran (SNAP)/Skenario Functional Test_v.2810.xlsx` | 1-3 | Page 1 is a linked table of contents. Pages 2-3 are clean spreadsheet tables. Page 3 starts mid-table. | Extracted Markdown rows are useful, but page-boundary continuation creates synthetic table starts and can separate rows from the original header. |
| OJK GMRA Attachment | `downloads/peraturan-ojk/global-master-repurchase-agreement-indonesia/Lampiran 3 GMRA.pdf` | 44, 62, 86 | Bilingual two-column layout is visually legible. Text is dense and aligned by paragraph pairs. | Reading order can interleave English and Indonesian column text; retrieval remains useful, but answer snippets may mix languages or split paired clauses. |

## Findings

- No rendered sample showed clipped text, black pages, unreadable glyphs, or failed Office conversion.
- The recovered QRIS/SNAP Office files are visually valid and searchable enough for the current baseline.
- The weakest area is table continuity, especially continuation pages where the header row is absent or where the source page starts in the middle of an XLSX table.
- GMRA-style bilingual attachments need caution because visual columns do not always map cleanly to single-language answer snippets.

## Decision

Keep LiteParse plus selective PaddleOCR as the baseline. Do not add MinerU to the active path for this corpus on the current local machine. The next extraction-quality work should be table-specific handling for XLSX and regulation attachments, not a parser replacement.

## Follow-Up Work

- Add table-continuation handling for XLSX pages that start mid-table.
- Preserve table headers across page boundaries for Office and spreadsheet conversions.
- Add a targeted check for bilingual two-column pages so final answer snippets prefer Indonesian text when available.
- Keep visual spot checks as a regression gate when extraction heuristics change.
