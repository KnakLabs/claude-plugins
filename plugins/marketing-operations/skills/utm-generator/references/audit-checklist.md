# Conventions doc audit checklist

Run through this list when the user asks for a conventions audit (either "audit" or "both" at the start of the skill). Report findings as a short, plain-language list — not every item will apply to every doc, and an empty/near-empty result ("this looks solid, one small note...") is a fine outcome. Don't manufacture issues to seem thorough.

## Formatting consistency

- **Casing**: are all values lowercase? Mixed casing (e.g. `Facebook` in one row, `facebook` in another) fragments reporting into duplicate rows.
- **Delimiter consistency**: is one separator style used throughout (hyphens recommended) rather than a mix of hyphens, underscores, and spaces?
- **Illegal characters**: any values containing spaces, `&`, `?`, `#`, or other characters that would break a URL when appended?

## Structural issues

- **Paid vs. organic social collapsed**: does the doc use the same `utm_medium` for paid and organic activity on the same platform? This is the most common and most damaging convention mistake — it silently merges paid and organic performance in reports.
- **utm_source duplicating utm_medium**: e.g. `utm_source=email` and `utm_medium=email` — source should say *where* (list/platform/partner name), medium should say *how* (channel type).
- **Missing common channels**: does the doc cover email, paid social, organic social, paid search, and display at minimum? Flag gaps but don't assume every org needs every channel (e.g. a B2B company with no SMS program doesn't need an SMS row).
- **Campaign naming not chronologically sortable**: if `utm_campaign` examples exist, check whether they lead with a date/period (e.g. `2026-q3-...`) or bury the date elsewhere/omit it, which makes campaigns hard to sort in a spreadsheet or report over time.

## What NOT to flag

- Org-specific channels or naming quirks that are internally consistent — consistency matters more than matching this skill's generic template exactly.
- Minor stylistic choices that don't affect reporting accuracy (e.g. whether campaign names are hyphenated with the objective vs. the audience first), unless the user asks for a stricter review.

## Presentation

- Deliver the audit as a short, scannable list, not a wall of text — plain language over jargon.
- If the same conventions doc was already audited earlier in the conversation and hasn't changed, don't repeat the same findings — just note that it was already covered.
- If both "generate" and "audit" were requested together, always finish generating and delivering the UTM table first, then present the audit afterward. Never let the audit block or delay the table.
