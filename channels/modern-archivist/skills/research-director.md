# Modern Archivist Research Director

Use this director for the `research` stage.

## Mission

Create `artifacts/research_packet.json`: a sourced evidence packet for a corporate/product failure autopsy.

## Inputs

- User brief or selected episode topic.
- Channel framing from `channels/modern-archivist/CHANNEL.md`.

## Output contract

`research_packet` should include:

- `topic`, `thesis`, `scope`, and `retrieved_at`.
- `timeline[]` with dated events and source IDs.
- `claims[]` with claim text, evidence rank, source IDs, and risk notes.
- `sources[]` with URL, title, publisher, author if known, retrieval date, and archive/local path if saved.
- `counterpoints[]` for charitable alternative explanations.
- `visual_leads[]` for logos, webpages, product shots, charts, filings, quotes, or archive material that the media stage can localize.
- `open_questions[]` for unresolved points.

## Workflow

1. Define the failure question in one sentence.
2. Build a dated timeline from primary sources first: company posts, filings, press releases, official docs, court/regulatory records, reputable interviews.
3. Add secondary analysis only after primary anchors exist.
4. Rank claims:
   - `primary`: directly supported by primary source.
   - `strong_secondary`: supported by multiple reputable secondary sources.
   - `context`: background explanation.
   - `interpretation`: useful but not asserted as fact.
5. Flag risky claims, disputed causality, and missing evidence.

## Success criteria

- `artifacts/research_packet.json` exists.
- Every factual claim has at least one source ID.
- Strong claims have primary or multiple-source support.
- Retrieval dates are present.
- Visual leads are explicit enough for `media_manifest`.
