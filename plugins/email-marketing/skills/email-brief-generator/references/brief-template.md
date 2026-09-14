# Brief output template

Write the finished brief to a markdown file named
`email-brief-<short-campaign-slug>-<YYYY-MM-DD>.md` and deliver it to the user.

Keep every section. If a section genuinely does not apply, keep the heading and
write one line saying why — a reviewer needs to see that it was considered.

---

```markdown
# Email brief: <campaign name>

*Built with the [CHEETAH Email Framework](https://knak.com/resources/guides/cheetah/?utm_source=claude&utm_medium=skill&utm_campaign=claude-plugin) — YYYY-MM-DD*

## 1. Summary

| Field | Value |
|---|---|
| Goal | <the one action, and how success is measured> |
| Audience | <who, plus what they already know> |
| Target send date | <date, day of week> |
| From name | <name> |
| From email | <email> |
| Reply-to | <email> |
| Destination URL | <clean URL — any tracking from the source material stripped; tag it with `/utm-generator` in the Knak Marketing Operations plugin> |
| Primary CTA | <button label> |

**In one line:** <what this email asks whom to do, and why they'd care.>

## 2. Subject line variants

Here are some A/B testing variants.

| # | Subject line | Chars | Hypothesis being tested |
|---|---|---|---|
| A | <line> | <n> | <curiosity / benefit / urgency / social proof / question> |
| B | <line> | <n> | <different angle> |
| C | <line> | <n> | <different angle> |

**Recommended:** <letter> — <one sentence why.>

## 3. Preview text variants

Here are some A/B testing variants. Each pairs with the subject line of the same
letter and extends it rather than repeating it. All under 100 characters.

| # | Preview text | Chars | Pairs with |
|---|---|---|---|
| A | <line> | <n> | Subject A |
| B | <line> | <n> | Subject B |
| C | <line> | <n> | Subject C |

**Recommended:** <letter>.

## 4. Body variants

Here are some A/B testing variants.

### Variant A — <angle in 2–4 words, e.g. "Direct benefit">

**Testing:** <what this variant is betting on>

<Full body copy, laid out in the sections the builder will actually build:
preheader area, hero headline, body blocks, CTA, sign-off. Mark each block.>

### Variant B — <angle>

**Testing:** <...>

<Full body copy>

### Variant C — <angle>

**Testing:** <...>

<Full body copy>

**Recommended:** <letter> — <why.>

> Run one test at a time. Testing subject A/B *and* body A/B in the same send
> means you can't attribute the result to either.

## 5. Design & asset checklist

| Asset | Spec | Status |
|---|---|---|
| Hero image | <what it should show, dimensions, dark-mode note> | Needed |
| Alt text — hero | "<written alt text>" | Drafted |
| Section transition | <T in CHEETAH: curved divider / angled break / colour block — not a plain rule> | Needed |
| Animation | <A in CHEETAH: what animates, why it's subtle, static first frame, target file size under ~1MB> | Needed |
| CTA button | Label "<label>", links to <URL> | Ready |
| Links to tag | <list every outbound link needing UTMs> | Needed |
| Footer | Unsubscribe link, physical mailing address, preference centre | Required |

## 6. Landing page harmony (H)

| Check | Finding |
|---|---|
| Email headline vs LP headline | <do they continue each other?> |
| Offer stated in email vs on LP | <match / mismatch> |
| Visual continuity | <shared imagery, colour, layout?> |
| Form length vs size of ask | <n fields — appropriate / too long> |
| Verdict | <Aligned / Fix before send: ...> |

## 7. Send timing & sequence

- **Target send:** <date, day> — <lands on a good day / flag: Monday morning and Friday afternoon are the weakest slots for B2B>
- **Build runway:** <n days from today> — <enough / tight: copy approval, design, build, QA and a test send typically need 5–7 working days>
- **Suggested sequence for this goal:**

  | # | Email | Timing | Purpose |
  |---|---|---|---|
  | 1 | <e.g. Invitation> | <date> | <...> |
  | 2 | <e.g. Reminder> | <date> | <...> |
  | 3 | <e.g. Last chance> | <date> | <...> |

## 8. CHEETAH scorecard

This email was written against the [CHEETAH Email Framework](https://knak.com/resources/guides/cheetah/?utm_source=claude&utm_medium=skill&utm_campaign=claude-plugin),
so it should score well by default. If you're curious and want to see the scorecard, run
`/email-scorer` on this brief.

## 9. Open questions

- <anything assumed that the owner should confirm>
```
