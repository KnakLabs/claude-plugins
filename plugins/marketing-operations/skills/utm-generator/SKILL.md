---
name: utm-generator
description: >
  Build consistent, campaign-ready UTM links in bulk: tag a whole batch of URLs for a campaign at once, using either your own team's naming conventions or Google Analytics best practice. Also audits an existing UTM conventions doc for gaps before they cost you tracking.

  Triggers on wanting to add UTM parameters to one or more URLs, build campaign tracking links, tag links for email/paid social/paid search/display/affiliate/SMS/QR codes, batch-tag multiple links for the same campaign, or check/review/audit a UTM conventions document (CSV, spreadsheet, Notion page, or markdown file) for consistency and best practice. Triggers even without the word "UTM" — "add tracking links," "tag these links for the campaign," "build campaign URLs," or uploading/referencing a UTM naming convention doc all count.
---

# UTM Generator

Generate correctly-formatted UTM-tagged links in batches, using the user's own naming conventions as the source of truth whenever they've supplied one — and optionally audit that conventions doc for best-practice issues.

## Why this exists

Hand-building UTM links is repetitive and error-prone: inconsistent casing/delimiters silently fragment analytics reports (e.g. `Facebook` vs `facebook` become two different sources), and mixing up paid vs. organic social on the same platform is the single most common mistake teams make. This skill handles the mechanical, deterministic parts (formatting, appending params to a URL without clobbering existing query strings, keeping values consistent) so the user only has to make the calls that require judgment (which channel, which campaign).

## Before you ask anything: start the dependency install

This skill's Python packages may not be present — Cowork hands every session a fresh
container, so nothing installed last time survives. **Kick the install off in the
background as your very first action**, then carry straight on with the questions
below while it runs:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/ensure_deps.py utm-generator &
```

Don't wait for it, don't mention it, and don't make the user watch it. By the time
they have answered, it has finished. If it fails the scripts still run and degrade
honestly — there is nothing here for the user to fix.

## Working folder

Files this skill saves — `utm-conventions-<brand>.md`, plus the link tables it builds — go **directly into the folder the user connects**. Do not
create sub-folders for them, and do not create a folder named after this plugin. People pick a
folder to suit the task at hand: someone doing QR codes may connect a folder already called *QR
Codes*, and burying files two levels beneath it helps nobody.

Filenames carry their own topic, so they stay readable whether the folder is dedicated to one job
or holds work from several skills.

**Saving means writing a real file into that folder.** Work out the folder's actual path,
write each file straight there with a file-writing tool, and check it arrived. A document
card in the conversation is not a saved file — it lives in the chat, not on their machine,
and the folder stays empty.

**A folder can arrive late.** When one is connected partway through — or at the very end,
after the work is already delivered — go back and save everything that belongs in it, not
just whatever happens next. That includes files gathered earlier in the conversation, like
an uploaded logo or a voice guide — save those too, so they keep the settings that produced
the work alongside the work itself.

**Keep the path out of the conversation.** *"I'll keep these in your folder"* beforehand and
*"Saved to your folder"* afterwards is all anyone needs — reading a long path back to someone
tells them nothing they don't already know. Name the files, not the directory. If a write
fails, say so plainly rather than reporting a save that never happened.

**The folder is asked for in Step 0**, alongside the conventions question, so both arrive in
one message and the user answers them together. Keep **Add folder** bold when you write it
out — it is the name of a button they have to find on screen, and bold is what makes it
findable in a paragraph of text.

If they decline, carry on and hand over anything you would have saved as a download, saying what
it is for. **Never write into `${CLAUDE_PLUGIN_ROOT}`** — a plugin update replaces the plugin
directory wholesale, so anything saved there is gone at the next update.

**Files are not shared between folders.** If another skill ran somewhere else, its files are
there, not here. Where a file is missing, fall back to the bundled default and say you did —
never assume a file exists because another skill would have written one.

### Finding files — match on what a file is, not what it is called

**Never look only for an exact filename.** People rename things, and a file called
`Tracking rules (2026).md` holds exactly what `utm-conventions-<brand>.md` would. List the folder and
match on meaning:

- read the filenames in the connected folder
- match on the words that matter, in any spelling or separator — `utm-conventions-knak.md`, `utm_conventions.md` and `our UTM rules.md` are all "the conventions file"
- if a name is ambiguous, open it and look at the first few lines before deciding
- if two files could both be it, ask rather than guessing
- if nothing matches, treat it as absent and use the bundled default

Say which file you used whenever it was not the obvious default name, so the user can correct you.

### Attachments and archives

When the user attaches files you draw on — a brand kit, a design system, a messaging doc — keep
what is reusable rather than reading it once and letting it go, or they will be re-uploading the
same thing every run.

- **Zip and other archives:** unpack them, and save the assets worth reusing into the connected
  folder — logo variants, colour or token definitions, fonts. Say what you kept and what you
  skipped.
- **Large archives:** if unpacking would copy more than a few tens of megabytes, say what is in
  it and ask before saving rather than filling the folder silently.
- **Documents** (PDF, DOCX, XLSX): distil them into a short markdown file rather than copying the
  original, and name it for what it holds.

## Step 0 — Settle the conventions before writing any option label

Everything downstream quotes a `utm_source` or `utm_medium` from one governing set of values.
This step establishes which set that is, and it finishes before the first option label is
written.

**1. Take the job from what they asked for.** A message with links in it wants tagging; a
message with a conventions doc attached and no links wants an audit; one with both wants
both. Where the request genuinely reads either way, say which you took it as in a line and
carry on — they will correct you in three words if you have it wrong.

**2. Look in the connected folder.** If any `utm-conventions-*.md` or a recognizable tracking
guide is there, read it and say which file you used. The suffix varies, since a team's file is
named after the brand, so match on the stem rather than a whole filename. A folder already
holding their conventions settles this step on its own — go straight to step 5.

**3. Ask for whatever is still missing, in one message.**

> Before I build these — two quick things:
>
> - **Do you have a UTM naming convention** your team already uses? A doc, a spreadsheet,
>   a Notion page, anything — paste or upload it and I'll build to your rules. If not, I'll
>   use a GA4-aligned default and tell you what it assumes.
> - **Want to connect a folder?** Use the **Add folder** button and I'll keep your
>   conventions there, so future links follow your own rules without re-uploading a doc —
>   and every link table lands there too.

Send it as an ordinary message rather than a question card: one answer is an upload and the
other is something they do in the interface, and neither fits a set of options written in
advance. Keep **Add folder** bold — it is the name of a button they have to find on screen.

**4. Stop and wait for the reply.** This message ends your turn. Their answer is what every
option label is built from, so the cards come after it.

**5. Load whichever source their answer points to.**

- **They gave you a doc.** Read it directly — structure varies a lot between teams, so parse
  it flexibly rather than expecting a fixed schema; look for columns or sections that map to
  channel, `utm_source` and `utm_medium`. Save a normalized copy back to the working folder
  per the section above. Once loaded it is the source of truth: build strictly from the values
  it contains, not from the generic template.
- **They have none, or declined.** Read
  `${CLAUDE_PLUGIN_ROOT}/skills/utm-generator/references/utm-conventions-ga4.md` and say
  plainly that you are using a GA4-aligned default rather than their own conventions.

**6. Quote values verbatim from whichever governs.** The question cards are the only part of
this workflow the user actually reads and approves. Writing a medium value into an option
label from memory — `organic-social` when the correct GA4-recognized value is `social`, say —
means the user clicks "yes" on a value that never gets used, and then has to be told afterward
that the link differs from what they approved. That erodes trust in the whole output even when
the generated link is right. So quote source and medium values straight from the loaded doc or
template, and where a value legitimately isn't in either — a platform the doc doesn't cover —
say so in the option description rather than inventing one.

If you do catch a mismatch after the fact, tell the user plainly which value you used and why,
rather than letting them discover it in the table.

The conventions loaded here are also what gets reviewed in the convention audit, when the
request called for one.

## Step 1 — (If generating) Ask about utm_content / utm_term

Ask, as part of the same information-gathering prompt as Step 2, whether the user wants either parameter appended. Read `${CLAUDE_PLUGIN_ROOT}/skills/utm-generator/references/utm-conventions-ga4.md`'s "utm_content and utm_term" section for when each is actually useful (multiple creatives/links in one campaign → utm_content; paid search keyword → utm_term) — most links need neither, so don't add them by default.

Before asking for values outright, check whether the conversation already contains enough to infer them (e.g. the user mentioned "hero CTA vs. footer CTA," or a target keyword) and propose those as suggestions to confirm rather than asking from a blank slate.

## Step 2 — Information gathering: use interactive question cards, not free-text prompts

**Start this step once the value set is settled** — their doc read, or the user's word that
they have none. Every option label here quotes a `utm_source` or `utm_medium` from that set,
so it is the thing the cards are made of.

Cowork does not support a literal modal pop-up or native dropdown menus, but its interactive multiple-choice question tool is the closest equivalent and should be used for this step rather than asking everything as open-ended chat questions. Structure it like this:

1. **Channel first**, as its own question with the channel options as choices (email, paid social, organic social, paid search, display, affiliate, SMS, QR code, etc.) — drawn from the conventions doc, or from the bundled template once the user has said they have no doc of their own.
2. **Source second**, as an immediate follow-up question whose options are filtered to match the channel just picked (e.g. picking "Paid social" surfaces only the platforms relevant to paid social — `facebook`, `linkedin`, `x`, `reddit` — not the full list). This is the cascading channel → source behavior: two quick successive question cards, not one card.
3. **utm_content / utm_term**, bundled as one or two questions inside a single card (per Step 1) — don't split these into separate rounds.
4. **Campaign name**, presented as a question whose first option is an auto-suggested `utm_campaign` value (built from channel, source, the destination URL/page, and any campaign context already given in the conversation) with a second option to type a custom one instead. Compute the time period for this suggestion from the current date (current quarter or month) unless the user has already specified a different period — only ask about the period separately if they want to override it.

Batch efficiency: gather this campaign-level information **once per campaign**, not once per URL. If the user gives multiple URLs for the same campaign, apply the same channel/source/campaign/content/term to all of them in one pass (unless they indicate a URL needs a different `utm_content`, e.g. distinct CTAs — ask which value goes with which URL only in that case).

Mixed channels in one batch: a set of URLs often spans channels rather than sharing one — e.g. three blog posts where one goes in an email, one in an organic post, one behind paid spend. Don't force a single channel choice on the batch. When the channel question comes back with more than one answer, or the user's phrasing implies different destinations for different links, group the URLs by channel and ask the source question once per group. `utm_campaign` can still be shared across the whole batch (which is what makes cross-channel comparison possible in reporting) — it's `utm_source`/`utm_medium` that vary per group. Confirm the grouping back to the user before generating so a link doesn't end up tagged for the wrong channel.

## Step 2.5 — (Paid search only) Offer a tracking template instead of per-URL tagging

When the channel is paid search, raise this before collecting URLs, because it changes what you collect. Google Ads and Microsoft Advertising both accept an account-, campaign-, or ad-group-level **tracking template** using the `{lpurl}` token:

```
{lpurl}?utm_source=google&utm_medium=cpc&utm_campaign=2026-q3-brand&utm_term={keyword}
```

`{lpurl}` resolves to whatever final URL the ad points at, so one template tags every landing page in scope at once — including pages added later. That's strictly less work than tagging each destination by hand, and it removes the failure mode where a new ad ships untagged because someone forgot. Present it as the default recommendation for paid search, with per-URL tagging as the fallback for teams whose account structure or approval process means they can't touch platform settings.

To build one, run the script with `{lpurl}` as the URL — braces pass through untouched, and the "Full Tagged URL" it returns is the exact string to paste into the platform's tracking template field. Read `${CLAUDE_PLUGIN_ROOT}/skills/utm-generator/references/utm-conventions-ga4.md`'s ValueTrack section for the token values themselves.

**Also ask whether auto-tagging is already enabled.** Google Ads auto-tagging appends `gclid` (Microsoft: `msclkid`), and GA4 prefers that click ID over manual UTMs when both are present on the same URL. The result is reports that disagree with each other: the Google Ads-linked reports attribute by `gclid` while anything keyed to `utm_source`/`utm_medium` — custom explorations, BigQuery, a downstream CRM — reads the UTMs, and the two won't reconcile. Neither setup is wrong on its own; the trouble is not knowing which one a given report used. Flag the overlap and let the user decide, rather than quietly adding a second attribution signal to an account that already has one. If they're unsure whether auto-tagging is on, that's worth checking before the links ship.

## Step 3 — Collect the destination URLs

Ask for the URL(s) if not already given. If the user is tagging an internal link (same domain as the destination, e.g. two pages on the company's own site linking to each other), flag this — tagging internal links resets attribution in GA4 and creates false new sessions. Confirm before proceeding.

**Skip a destination that isn't the user's own property** — a third-party event page, a
partner's site, an app store listing, another vendor's release notes — since tagging a
domain they don't measure achieves nothing. The parameters land in that company's
analytics, not theirs.

Work out which is which from the domains in front of you: the ones matching the site they
are tagging *for* are theirs, the rest are somebody else's. Where a batch mixes both,
tag their own and hand the others back untagged in the same table, with a line saying
which and why — a newsletter linking out to three vendors is normal, and the user should
see that you noticed rather than wonder why two rows look different.

## Step 4 — Generate the table

Use `${CLAUDE_PLUGIN_ROOT}/skills/utm-generator/scripts/build_utm_table.py` to do the actual formatting and URL construction rather than hand-building the strings — it lowercases values, converts spaces/underscores to hyphens, strips illegal characters, and correctly appends UTM params to URLs that may already have query strings, without clobbering existing params.

1. Write a JSON campaign spec (see the script's docstring for the exact shape) with `utm_source`, `utm_medium`, `utm_campaign`, optional `utm_content`/`utm_term`, and the list of URLs (each with its own optional per-row overrides).
2. Run: `python ${CLAUDE_PLUGIN_ROOT}/skills/utm-generator/scripts/build_utm_table.py <spec.json> <output_basename>`
3. It writes `<output_basename>.csv` (always) and `<output_basename>.xlsx` (if openpyxl is available) with exactly three columns: **Base URL**, **UTM Parameters**, **Full Tagged URL** — matching what the user asked for (links on their own, UTM parameters on their own, and the combined tagged links).
4. Check the script's `warnings` output for any rows missing a required field, and resolve those with the user before delivering.

The script takes one `utm_source`/`utm_medium` pair per spec, so a batch spanning several channels needs one spec per channel group. Run it once per group, then combine the resulting rows into a single CSV/XLSX when they share a `utm_campaign` — one campaign should arrive as one file the user can drop into a tracker, even though it took several runs to build.

Genuinely distinct campaigns are the opposite case: keep those in separate files/sections rather than merging, so a tracker row never mixes two campaigns.

**Skipped destinations still get a row.** Put the ones you left untagged from Step 3 in the
same table with the Base URL filled in and the tagged column showing the plain link, so the
user has every URL from their email in one place and can see at a glance which carry
tracking. Name them once underneath rather than annotating every row.

## Step 5 — Deliver the output

**Write the normalized conventions into the folder as part of delivering.** It is what makes
the next batch match this one.

**Name the file after whose rules it holds.** When the user supplied their own doc, use
`utm-conventions-<brand>.md` — `utm-conventions-knak.md`, `utm-conventions-acme.md` — taking
the brand from the doc, the domains being tagged, or the company they have already named,
lowercase and hyphenated. The `-ga4` suffix belongs to a file built from the bundled
template, where GA4's defaults are the source. A filename that names the owner tells the
next person to open the folder that these are their team's real rules, worth reading and
worth keeping.

If they uploaded their own doc, note in the file that it came from them and don't overwrite
anything they wrote by hand. Without a folder, hand it
over with the link table and say it's the file that keeps future links consistent.

Show the table in the chat (read the CSV back and render it as a markdown table) **and** deliver the CSV/XLSX file so the user has something reusable for a campaign tracker or spreadsheet.

Write the files into the working folder if one is connected, named `utm-links-<campaign>-<YYYY-MM-DD>.csv` / `.xlsx`, and say where they went. With no folder connected, deliver them as downloads instead. Either way the files are a deliverable, not an option to offer.

**Once the table is delivered, offer the one case for tagging an external link.** Any run
that skipped a destination gets this, however many were skipped — the table goes out with
those links plain, and the offer comes after it as a question the user can say yes to:

> The <n> links to sites you don't own are untagged, since those parameters would land in
> their analytics rather than yours. One exception if it applies: if you measure clicks in
> your email platform rather than GA4, the click is counted as the link leaves the email —
> so a `utm_content` value would still tell you which card was clicked, even on their
> domain. Want me to add those?

Deliver first and offer second, so the default stands on its own and the exception is a
choice made with the table already in hand.

## Step 6 — Convention audit (only when the request called for one)

Where the request was an audit, or an audit as well as tagging, review the loaded conventions doc against `${CLAUDE_PLUGIN_ROOT}/skills/utm-generator/references/audit-checklist.md` and report findings in plain language. For "both," this always runs *after* the table has been generated and delivered — never let the audit block or delay the table itself.

If this exact conventions doc was already audited earlier in the conversation and hasn't changed, don't repeat the same findings — just note that it's already been covered. A revised or different doc gets a fresh audit of its own.

## Reference files

- `${CLAUDE_PLUGIN_ROOT}/skills/utm-generator/references/utm-conventions-ga4.md` — the fallback UTM convention template (universal formatting rules, channel → source/medium mapping aligned to GA4's Default Channel Groups, example values for common platforms including AI assistants, campaign naming structure). Use this only when the user has no conventions doc of their own.
- `${CLAUDE_PLUGIN_ROOT}/skills/utm-generator/references/audit-checklist.md` — what to check when auditing a conventions doc, and what NOT to flag as an issue.
- `${CLAUDE_PLUGIN_ROOT}/skills/utm-generator/scripts/build_utm_table.py` — deterministic UTM formatting and table-building script; always use this rather than hand-constructing UTM strings or URLs.
