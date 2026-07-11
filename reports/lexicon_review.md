# Lexicon Review

Date: 2026-07-11

The deterministic extractor scanned `537,355` blocks and produced `15,208` candidates. The generated report remains a review artifact; heading-only fragments, boilerplate, and generic single-word terms were not approved.

## Approved

- Entities: `8`
- Topics: `8`
- Existing alias handling: `KUPVA` was retained only as an alias of the reviewed `Kegiatan Usaha Penukaran Valuta Asing` entity.
- Failure-driven alias updates: `2`
  - `pelindungan konsumen` -> `consumer_protection` topic; corpus support count `10,875`.
  - `uji kemampuan dan kepatutan` -> `fit_and_proper` topic; corpus support count `16,972`.

Approved entries and alias updates are stored in `resources/query_lexicon.reviewed.json` with review notes. The merged artifact is `resources/query_lexicon.merged.json`, and the two approved aliases are now applied to the active runtime lexicon at `resources/query_lexicon.json`.

## Review Rules

- Prefer exact regulation titles or specific domain phrases with high title/definition support.
- Reject heading-only fragments and phrases containing form boilerplate or sentence residue.
- Reject generic terms such as `Perusahaan`, `Pembiayaan`, or `Layanan` when they do not identify a stable regulatory concept.
- Do not convert generated candidates into intents; intents remain manually authored user-behavior categories.

## Verification

The merged lexicon was loaded through the normal query-planning path and checked against representative transparency/reporting, BI central-banking, BPRS reporting, and financial-services marketing queries. The alias-specific plans recognized `consumer_protection` for BI/OJK comparison wording and `fit_and_proper` for the Indonesian regulatory phrase.

The post-merge serial gates passed: unit tests `52/52`, natural-language evaluation `15/15` (average `0.989`), evidence `30/30` (average `0.990`), answer `30/30` (average `0.988`), and answer quality `12/12` (average `1.000`). The natural-language average is lower than the prior checked-in `0.999`, but no question became unacceptable, and comparing plans with and without the aliases showed no gold-query plan changes; the difference is limited to regenerated ranking/Pasal ordering.
