# UTM conventions — starting template

Use this only until the team supplies their own conventions doc. Once they do, that doc is the
source of truth and this file is ignored rather than merged with it.

Keep this as the single place the rules live. Two convention files drift, and the failure
looks like a mismatch in the links rather than a mismatch in the rules.

## How to read this file

Rules here are not all the same kind, and it matters which is which:

- **[GA4]** — determined by Google Analytics. Change these and traffic lands in the wrong channel.
  Not negotiable.
- **[Universal]** — not GA4 rules, but ignoring them fragments reporting on any platform.
- **[Choice]** — your team's naming decision. Examples are illustrative, not standard. Replace
  them with whatever you already use.

## Universal formatting rules  **[Universal]**

Apply these to every UTM value generated, regardless of channel:

- **All lowercase.** GA4 and most platforms are case-sensitive, so `Facebook` and `facebook` are tracked as separate values. Lowercase every value before building the link.
- **Hyphens between words, not underscores or spaces.** `paid-social`, not `paid_social` or `paid social`. Spaces get URL-encoded as `%20`, which is ugly and error-prone.
- **No spaces or special characters** (`&`, `?`, `#`, etc.) in any UTM value — they break the URL.
- **Never tag internal links** (a link from one page on the same site to another). Doing so resets the session in GA4 and misattributes a returning visitor as a brand-new one. Flag this if a user asks to tag an internal link.
- **Keep values consistent across every campaign.** The whole point of a conventions doc is that "email" always means the same thing so reporting doesn't fragment into duplicate rows for the same channel.

## Channel → source and medium  **[GA4]**, except where the table says otherwise

Most medium values below are what GA4's Default Channel Groups actually match on — `email`,
`cpc`, `paid-social`, `social`, `display`, `affiliate`, `referral`, `sms`. Those you cannot
invent; a different spelling misses the channel.

Two rows are conventions rather than GA4 rules, and say so in the last column: `qr-code` and
`webinar` are not channels GA4 recognizes, so that traffic lands in Referral or Unassigned unless
someone has built a custom channel group for it. They are worth tagging consistently anyway —
you just can't expect the channel report to separate them on its own.

Maps `utm_source` / `utm_medium` pairs to GA4's Default Channel Groups so reporting rolls up correctly without manual reclassification.

| Channel | utm_source (examples) | utm_medium | Rolls up to (GA4) |
|---|---|---|---|
| Email | ESP or list name, e.g. `marketo`, `newsletter`, `nurture-list` | `email` | Email |
| Paid social | platform, e.g. `facebook`, `linkedin`, `instagram`, `x`, `reddit` | `paid-social` | Paid Social |
| Organic social | platform, e.g. `facebook`, `linkedin`, `instagram`, `x`, `reddit` | `social` | Organic Social |
| Paid search | engine, e.g. `google`, `bing`, `yahoo` | `cpc` | Paid Search |
| Organic search | (usually auto-captured, not hand-tagged) | `organic` | Organic Search |
| Display / programmatic | network, e.g. `google-display`, `the-trade-desk` | `display` | Display |
| Affiliate / partner | partner's name or domain | `affiliate` | Affiliates |
| Referral / sponsorship | referring site's domain | `referral` | Referral |
| SMS | SMS platform, e.g. `attentive` | `sms` | SMS |
| QR code (print, signage, packaging) | where the code lives, e.g. `event-banner`, `direct-mail`, `product-packaging` | `qr-code` | Referral (not natively recognized by GA4) |
| Webinar / virtual event platform | platform, e.g. `zoom`, `on24` | `webinar` | Referral or Other, depending on GA4 setup |
| Sales / SDR outreach | `sales-email` or the tool, e.g. `outreach` | `email` or `referral` | Email or Referral |

Notes:
- `utm_source` should name the specific place traffic came from, not repeat the medium. For email, the list name (e.g. `product-launch-list`) is usually more useful than just the ESP name, since it tells you which segment engaged.
- Paid vs. organic social is the single most common UTM mistake: same source (`facebook`), different medium (`paid-social` vs. `social`). Getting this backwards silently merges paid and organic performance in reporting — double check this pairing whenever the channel is social.

## Example utm_source values for common platforms  **[Choice]**

The same platform can fall under different channels depending on how it's being used — cross-reference with the channel table above to pick the right medium.

| Platform | utm_source | Typical utm_medium(s) |
|---|---|---|
| Google Ads | `google` | `cpc` (paid search) |
| Google Search (organic) | `google` | `organic` |
| Google Display Network | `google` | `display` |
| Bing Ads | `bing` | `cpc` |
| Bing (organic search) | `bing` | `organic` |
| Yahoo | `yahoo` | `cpc` or `organic` |
| Facebook | `facebook` | `paid-social` or `social` |
| X | `x` | `paid-social` or `social` |
| Reddit | `reddit` | `paid-social` or `social` |
| LinkedIn | `linkedin` | `paid-social` or `social` |
| YouTube | `youtube` | `paid-social`, `social`, or `video` |
| G2 Crowd | `g2` | `referral` (organic listing) or `affiliate` (sponsored placement) |
| ChatGPT | `chatgpt` | `ai-referral`* |
| Claude | `claude` | `ai-referral`* |
| Gemini | `gemini` | `ai-referral`* |
| Perplexity | `perplexity` | `ai-referral`* |
| Grok | `grok` | `ai-referral`* |

\* AI assistants/answer engines aren't a native GA4 channel group yet, so this traffic lands in "Referral" or "Unassigned" unless the user has set up a custom GA4 channel group for `ai-referral`. Mention this as a heads-up when suggesting these values — don't assume their GA4 is already configured for it.

## utm_campaign structure  **[Choice]**

Recommended pattern:

```
{year}{quarter or month}-{initiative/campaign name}
```

Examples: `2026-q3-product-launch`, `2026-08-webinar-ai-agents`, `2026-q4-blackfriday`

A leading date/period keeps campaigns sortable chronologically in any report or spreadsheet, and lets a recurring campaign name (e.g. `webinar-ai-agents`) be reused across periods without collision.

Default the period to the current quarter or month computed from today's date, unless the user specifies a different period. Auto-suggest a full campaign name from whatever channel/source/URL/context is already known, and offer it to the user as a pickable option alongside "type my own" — never require them to type a name from scratch unless they want to.

## utm_content and utm_term  **[Universal]** — when to use them

- **utm_content**: for distinguishing multiple links or creatives pointing to the same URL within the same campaign — e.g. two CTA buttons in one email, or two ad variants in the same ad set. Skip it if there's only one link per campaign/channel combination.
- **utm_term**: effectively paid-search-only, capturing the keyword driving the click. Skip it for every other channel.

Always ask upfront (bundled into one question) whether the user wants either parameter appended, rather than adding them by default — most links don't need them.

## Email sends

Everything above applies to email. These four are worth calling out because they come up on
every send.

**`utm_medium` must be exactly `email`.  [GA4]** Anything else — `e-mail`, `Email`, `newsletter`
— misses GA4's Email channel and splits the traffic into rows that never reconcile.

**One `utm_campaign` across every in-scope link in a send.  [Universal]** The single
highest-value rule here. One mismatched link splits a send into two campaign rows and no report
will reconcile them afterwards.

**UTMs are for web analytics only.** Not a convention, a correction — people assume otherwise
often enough to be worth stating. Campaign or program membership is set by the marketing
automation platform's own flow steps and automation. Nothing reads `utm_campaign` back to decide
who is in a program, so don't design campaign names hoping to drive membership from them.

**Always-on sends need something in the date slot.  [Choice]** A nurture stream or evergreen
welcome series has no send date, so a date-based campaign pattern has a gap. Pick a token and use
it consistently — `ong`, `evergreen` and `always-on` are all in use; none is standard. Whatever
you pick, keep it identical across every always-on campaign or you lose the ability to separate
evergreen traffic from dated campaigns.

**A/B variants belong in `utm_content`.  [Universal practice, [Choice] of token]** Separating
variants in `utm_content` is the canonical use of the field — without it the two arms are
indistinguishable and the test can't be read. The token is yours: `v1`/`v2`, `a`/`b` and
`variant-a` are all common.

## Which links are in scope

UTM parameters belong only on links to web properties the sender owns and measures. Every
subdomain of a listed domain counts.

**Your domains** — the skill asks for these on the first run and saves them here, then feeds them
to the checking script on every run afterwards:

```
owned_domains:
  - example.com
  - info.example.com
```

Until this is filled in, the script checks UTMs on every link in the email, which means
unsubscribe and social links get flagged even though they should never carry UTMs.

Out of scope by definition, and never flagged: social profile links, unsubscribe and
preference-centre links, view-in-browser links, `mailto:` links, calendar links, and any
third-party destination (event platforms, partner sites, app stores).

## Severity overrides (optional)  **[Choice]**

Fill this in only if your team wants specific severities —
anything left blank uses the skill's defaults.

| Finding | Severity |
|---|---|
| `utm_medium` is not `email` | |
| A required parameter is missing | |
| `utm_campaign` differs across links in one send | |
| A value contains a space, `%20`, `&`, `?` or `#` | |
| Two links to the same page share a `utm_content` | |

## ValueTrack placeholders (paid search)

On paid search, don't hand-write the keyword into `utm_term`. Use the platform's ValueTrack token and let it fill the value in at click time:

```
utm_term={keyword}
```

Google Ads and Microsoft Advertising both substitute `{keyword}` with the keyword that actually triggered the ad, so one link covers every keyword in the account and stays correct as keywords are added or paused. Hand-typed keyword values go stale the moment the keyword list changes, and they can't distinguish which of several keywords drove a given click.

Rules that matter when generating these:

- **Keep the braces and the exact case.** `{keyword}` has to reach the platform as literal `{keyword}` — brace-stripped, lowercased, or percent-encoded (`%7Bkeyword%7D`) tokens are never substituted and land in reports as literal text. `scripts/build_utm_table.py` handles this correctly; don't hand-build these strings.
- **Blank values in keywordless campaign types.** Performance Max, Dynamic Search Ads, and AI Max-style automated search campaigns don't match on advertiser keywords, so `{keyword}` resolves to an empty string and `utm_term=` arrives blank. That isn't a bug to chase — it's the token honestly reporting that no keyword was involved. Say so up front when a user is tagging those campaign types, so blank `utm_term` rows in GA4 don't get read as broken tracking. If they want something in the field regardless, a static value naming the campaign type (e.g. `utm_term=pmax-no-keyword`) is more honest than an invented keyword.
- **`{matchtype}` is a useful companion.** It resolves to `e`, `p`, or `b` (exact, phrase, broad) and answers a question `{keyword}` alone can't: whether broad match is quietly spending budget on loose queries. `utm_content` is the natural home for it when nothing else needs that slot — just keep the pairing consistent across campaigns so reporting stays comparable.

Other tokens teams commonly use: `{lpurl}` (the final URL, for tracking templates — see the paid-search step in SKILL.md), `{campaignid}` / `{adgroupid}`, `{device}`, `{network}`, and the `{ifmobile:x}` / `{ifnotmobile:y}` conditionals. Any `{...}` token passes through the generator untouched, so a team's existing convention works as-is.

Platforms differ, so don't carry Google's tokens somewhere they won't resolve: Meta uses its own dynamic parameters (e.g. `{{ad.name}}`, double braces), and LinkedIn has no equivalent for organic or most paid placements. An unsubstituted token is worse than no parameter at all, because it still looks like data.
