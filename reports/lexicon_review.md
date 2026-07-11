# Lexicon Review

Date: 2026-07-11

The deterministic extractor scanned `537,355` blocks and produced `15,208` candidates. The generated report remains a review artifact; heading-only fragments, boilerplate, and generic single-word terms were not approved.

## Approved

- Entities: `8`
- Topics: `8`
- Alias handling: `KUPVA` was retained only as an alias of the reviewed `Kegiatan Usaha Penukaran Valuta Asing` entity.

Approved entries are stored in `resources/query_lexicon.reviewed.json` with review notes. The merged artifact is `resources/query_lexicon.merged.json`; the active runtime lexicon at `resources/query_lexicon.json` was intentionally left unchanged.

## Review Rules

- Prefer exact regulation titles or specific domain phrases with high title/definition support.
- Reject heading-only fragments and phrases containing form boilerplate or sentence residue.
- Reject generic terms such as `Perusahaan`, `Pembiayaan`, or `Layanan` when they do not identify a stable regulatory concept.
- Do not convert generated candidates into intents; intents remain manually authored user-behavior categories.

## Verification

The merged lexicon was loaded through the normal query-planning path and checked against representative transparency/reporting, BI central-banking, BPRS reporting, and financial-services marketing queries. Planning completed with the approved entities/topics recognized and without changing the active runtime lexicon.
