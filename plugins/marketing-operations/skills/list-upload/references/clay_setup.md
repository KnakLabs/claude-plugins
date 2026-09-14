# Setting up the two Clay functions

This skill calls out to two **Clay functions** — one to validate email addresses, one to enrich a
person. Neither ships with the plugin, because a Clay function lives in your own workspace and its
ID is meaningless in anyone else's. You build them once, give the skill their IDs on first run,
and it records what it learns about them in `list-upload-knowledge/clay.md`.

**Treat the inputs and outputs below as a guide, not a contract.** If your functions take
different inputs or return different fields, that is fine — the first run tests whatever you have
and documents the real shape in `clay.md`, which is what the skill reads from then on. What
matters is that each function does the job described.

You can also build these somewhere other than Clay. The skill needs two capabilities — "validate
this email, and find a better one if it's bad" and "enrich this person" — and does not care what
provides them. If you use something else, still record the real inputs and outputs in `clay.md`.

---

## Function 1 — Email validation

**Purpose:** confirm an email is deliverable, and when it isn't, go find one that is.

**Suggested inputs:** `Email`, `First Name`, `Last Name`, `Company Name`

**The flow:**

1. Validate the incoming email with a validation provider (ZeroBounce is what this was built
   against; any equivalent works).
2. **If it comes back valid** — stop there and return that. No further lookups, no credits spent.
3. **If it does not come back valid:**
   a. Find the person's company domain from the company name.
   b. Feed that domain plus the other inputs into an **email waterfall** to find a candidate
      address.
   c. Validate the address the waterfall returned.
   d. Return the found email along with its validation status.

**Suggested output:**

```json
{ "status": "valid" }
```

or, when the waterfall ran:

```json
{
  "status": "<status of the incoming email>",
  "found_email": "<address the waterfall found>",
  "found_email_status": "valid" | "invalid" | "..."
}
```

The early exit at step 2 is the part worth getting right — it's what keeps a clean list cheap,
since most rows should stop there.

---

## Function 2 — Person enrichment

**Purpose:** fill in the firmographic and job-title fields a raw list is usually missing.

**Suggested inputs:** `Email`, `First Name`, `Last Name`, `Company`, `Job Title`

**The flow:**

1. Find the person's company domain.
2. Feed that plus the other inputs into a **LinkedIn URL waterfall** to find the person's profile.
3. With the LinkedIn URL and the original inputs, run:
   - a **company firmographics** lookup — employee count and range, revenue range
   - a **job title** lookup

**Suggested output** — any subset of:

| Field | What it is |
|---|---|
| `LinkedIn URL` | the person's profile |
| `size` | employee range, as a band |
| `employee_count` | employee count, as a number |
| `annual_revenue` | revenue range, as a band |
| `title` | job title |

Bands come back in whatever buckets the provider uses, which will rarely match the target CRM's
picklist. Mapping them is the skill's job, not the function's — see the enrichment step in
`SKILL.md`.

---

## Batching

Both functions are called for many records at a time, so build them to be run in batches rather
than one row per call. The skill sends **100 records per batch** by default and polls for
completion before sending the next, which keeps a failure cheap to retry. If your functions have
a different practical ceiling, note it in `clay.md` on first run and the skill will use that
instead.

---

## After you've built them

Run the skill and it will ask for the two function IDs, test each one against real records from
that first list, and write `list-upload-knowledge/clay.md` in your working folder recording the
IDs, the actual inputs each function needs, the shape it returns, how to read that output, and
the batch size. Every run after that reads `clay.md` and doesn't ask again.
