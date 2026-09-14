---
name: list-upload
description: >
  Clean, validate, dedupe, and upload a contact list straight into your MAP: normalizing phone numbers, countries, states, and industries along the way. Hand over a messy event export and get back a pristine list that can be imported directly into your MAP using its connector.

  Triggers on wanting to import a list, upload contacts, process event attendees, or clean a CSV before uploading to Marketo.
---

# List Upload

Clean, validate, deduplicate, and upload a contact list CSV into Marketo.

The platform-specific steps below are written against **Marketo**, **Salesforce** and **Clay**,
which is what this skill was built and tested on. Where your stack differs the work still applies
— substitute the equivalent calls for CRM lookup, email validation and enrichment, and say which
steps you could not run rather than reporting them as done. Field API names and picklist values
are read from whatever connectors are present, never assumed.

## Supporting Files

- `${CLAUDE_PLUGIN_ROOT}/skills/list-upload/references/schema.md` — **read-only seed.** Standard field API names, plus custom fields with `???` API names and example picklist values. Resolve real custom-field names and picklist values from the connectors and record them in `lead-schema.md` in the working folder, which is the live version.
- `${CLAUDE_PLUGIN_ROOT}/skills/list-upload/references/clay_setup.md` — how to build the two Clay functions this skill calls. Hand this to the user when they don't have them yet.
- `${CLAUDE_PLUGIN_ROOT}/skills/list-upload/references/salesforce-state-codes.md` — State/province codes for 10 countries (AU, BR, CA, CN, IN, IE, IT, JP, MX, US)
- `${CLAUDE_PLUGIN_ROOT}/skills/list-upload/references/iso-country-codes-salesforce.md` — Country name → ISO Alpha-2 code mapping
- `${CLAUDE_PLUGIN_ROOT}/skills/list-upload/scripts/normalize_country.py` — Converts country name values to ISO Alpha-2 codes. Accepts a CSV, a column name, and an output path. Uses a hardcoded lookup table for common variants (e.g. "USA" → "US", "UK" → "GB") with pycountry fuzzy search as fallback. Flags any values it cannot resolve.
- `${CLAUDE_PLUGIN_ROOT}/skills/list-upload/scripts/normalize_phone.py` — Normalizes phone numbers to E.164 format (+CCXXXXXXXXXX) using Google's libphonenumber (phonenumbers library). Takes the ISO Alpha-2 country column as a region hint for bare local numbers. Flags numbers it cannot parse for manual review. Run ${CLAUDE_PLUGIN_ROOT}/skills/list-upload/scripts/normalize_country.py first so region hints are already ISO codes.
- `${CLAUDE_PLUGIN_ROOT}/skills/list-upload/scripts/normalize_state.py` — Converts state/province names and abbreviations to 2-letter codes for the 10 Salesforce-supported countries (AU, BR, CA, CN, IN, IE, IT, JP, MX, US). Skips records from unsupported countries. Flags any values it cannot resolve.
- `${CLAUDE_PLUGIN_ROOT}/skills/list-upload/scripts/normalize_website.py` — Strips website URLs to bare domain only, removing protocol, www., trailing slashes, paths, and query strings (e.g. `https://www.example.com/page?ref=nav` → `example.com`).
- `${CLAUDE_PLUGIN_ROOT}/skills/list-upload/scripts/normalize_industry.py` — Maps incoming industry values (abbreviations, shorthands, event-specific labels) to the correct SFDC Industry API value using a JSON lookup cache. Flags any values not found in the cache for manual review. CLI: `python3 ${CLAUDE_PLUGIN_ROOT}/skills/list-upload/scripts/normalize_industry.py input.csv output.csv --col INDUSTRY`
- `${CLAUDE_PLUGIN_ROOT}/skills/list-upload/scripts/industry_mapping_cache.json` — the **read-only seed** lookup table for `normalize_industry.py`. Keys are lowercased incoming values; values are SFDC API values. Pre-populated with ~100 common mappings. Never edit this file — see "Working folder" below for where learned mappings go.

## Working folder

Files this skill saves — `clay-functions.md`, `clay-tasks.md`, `lead-schema.md`, `industry-mappings.json`, plus the CSVs it produces — go **directly into the folder the user connects**. Do not
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

**If no folder is connected, ask at the start of the run — before the first question you could have avoided asking:**

> Before we start: do you want to connect a folder? I'll keep **your field mappings, your
> enrichment function IDs, and the industry values we work out** there, so the next list skips
> the mapping questions entirely — and the cleaned CSVs land in that folder.
>
> Use the **Add folder** button and either point me at the folder you keep this work in, or
> create a new one. Then tell me and I'll pick it up.

**Keep "Add folder" bold when you write this out.** It is the name of a button they have to find on screen, and bold is what makes it findable in a paragraph of text.

**Ask this in an ordinary message, never as a multiple-choice question.** Connecting a
folder is something the user does in the interface — a picker can only offer a button
that says yes, and then they still have to go and do it. Say it in a sentence and let
them attach the folder in their next reply.

If they decline, carry on and hand over anything you would have saved as a download, saying what
it is for. **Never write into `${CLAUDE_PLUGIN_ROOT}`** — a plugin update replaces the plugin
directory wholesale, so anything saved there is gone at the next update.

**Files are not shared between folders.** If another skill ran somewhere else, its files are
there, not here. Where a file is missing, fall back to the bundled default and say you did —
never assume a file exists because another skill would have written one.

### Finding files — match on what a file is, not what it is called

**Never look only for an exact filename.** People rename things, and a file called
`Marketo fields (2026).md` holds exactly what `lead-schema.md` would. List the folder and
match on meaning:

- read the filenames in the connected folder
- match on the words that matter, in any spelling or separator — `lead-schema.md`, `lead_schema.md` and `our field names.md` are all "the field schema file"
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

## Where this is running, and why it matters

Check it once, at the very start:

```bash
python3 -c "import os; print('cowork' if os.path.isdir('/mnt/user-data') or os.path.isdir('/mnt/outputs') else ('claude-code' if os.environ.get('CLAUDECODE') else 'unknown'))"
```

**Check for Cowork first.** Cowork *is* Claude Code running in a cloud container, so
`CLAUDECODE` is set in both places; the `/mnt` folders exist only in the container.

**In Cowork, say this before the work starts:**

> One thing worth knowing before we begin: running this in **Claude Code** — the **Code** tab
> in your Claude desktop app — makes it quite a bit faster.
>
> Salesforce has a command-line tool that looks your whole list up in one query, about
> 20 seconds for a few thousand records. It signs in through your browser, which this
> environment has no way to open, so here I look Salesforce up through the connector instead —
> the same lookup, written out in batches, usually 10 to 15 minutes.
>
> Clay's tool works in both places, and in Claude Code it stays signed in. Here I have to
> install it and have you approve a sign-in every session, because each one gets a fresh
> machine.
>
> Happy either way — say the word and I'll carry on here.

Their answer settles it: carry on in Cowork through the connectors, or let them move and pick
the run up there. Either route completes the job; the difference is time and repeated sign-ins.

**In Claude Code**, `/setup-for-claude-code` installs both CLIs and signs them in, once per
machine. `sf org list` and `clay whoami` say whether that has already happened.

## Before you ask anything: start the dependency install

This skill's Python packages may not be present — Cowork hands every session a fresh
container, so nothing installed last time survives. **Kick the install off in the
background as your very first action**, then carry straight on with the questions
below while it runs:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/ensure_deps.py list-upload &
```

Don't wait for it, don't mention it, and don't make the user watch it. By the time
they have answered, it has finished. If it fails the scripts still run and degrade
honestly — there is nothing here for the user to fix.

## First use of a Clay function — find it, confirm it, record it

**Ask for a folder in your first message.** The files the user has already given you live
only in the chat until a folder exists, so this one belongs at the start. Every other
question in this skill belongs in the step that uses the answer. The wording is under
[Working folder](#working-folder) above.

Run the steps below at the point each function is first needed — **email validation at Step
2, person enrichment at Step 4 or Step 6** — so the run reaches them having already delivered
the column mapping and a sorted list. Once `clay-functions.md` records a function, every
later run reads it and asks nothing.

1. **Find the function with `list_subroutines`.** It returns each function's id, name,
   description and required inputs, which makes the id a lookup you can do yourself. Match on what the description says the function does: an email
   validator validates an address and falls back to a waterfall when it fails; a person
   enricher returns a LinkedIn profile, firmographics and job title. Show the user the one
   you picked — its name, what it does, and the inputs it takes — and get a yes before
   spending credits on it.
   - Where several plausibly match, list them and let the user choose.
   - **Record the full, prefixed id.** `list_subroutines` and the run responses report it
     stripped — `t_0tj...` — while Clay's own Integrations panel shows `function:t_0tj...`.
     The prefixed form is the one that works everywhere, and the CLI needs it, so that is
     what goes into `clay-functions.md`. Where only the stripped form is to hand, write it
     with `function:` in front.
   - Where nothing returned fits, ask the user for the function id and hand them
     `${CLAUDE_PLUGIN_ROOT}/skills/list-upload/references/clay_setup.md`, which describes what
     each function should do. Offer to carry on without it for this run.
2. **Test each one against real records from the list being processed.** Don't invent test data —
   the first list is the best test material available, and the records have to be processed anyway.
   Pick deliberately: for validation, one record whose email looks sound and one that looks
   doubtful, so both the valid path and the waterfall path get exercised. Tell the user which
   records you used and that testing spends provider credits.
3. **Write `clay-functions.md`** from what the test actually returned — not from what
   `clay_setup.md` says it should return. If the user's functions take different inputs or return
   different fields, the file records theirs.

```markdown
# Clay functions
<!-- Written by list-upload on YYYY-MM-DD from live test calls. -->

## Email validation
- routine_id: <the full id from Clay's Integrations panel, e.g. function:t_0tj...>
- inputs required: <exact input names the function accepted>
- returns: <the real JSON shape, both branches if both were seen>
- how to read it: <which field means deliverable, which carries a replacement address>
- batch size: <what was used, and any ceiling hit>
- notes: <early-exit behaviour, anything surprising>

## Person enrichment
- routine_id: <the full id from Clay's Integrations panel, e.g. function:t_0tj...>
- inputs required: <exact input names>
- returns: <field names and what each holds — bands vs numbers matters here>
- how to read it: <which fields map to which CRM field, and which need band remapping>
- batch size: <what was used>
- notes: <fields that came back empty, provider quirks>
```

4. **Batching belongs in this file.** Record the batch size that worked and how completion was
   polled, because that is the part most likely to differ between workspaces and the part most
   expensive to rediscover. Default to **1,000 records per batch** — the maximum
   `run_subroutine_direct` accepts — polling until complete before sending the next.
5. Say where the file went, and that the next run will be quicker for it. **If no folder was
   connected**, still produce `clay-functions.md` and hand it over as a download — the function IDs and the
   tested output shape are the single most expensive thing in this skill to rediscover.

If a later run finds `clay-functions.md` but a call fails in a way the file doesn't explain, re-test that
one function and update the file rather than working around it silently.

## Connectors Required

- Marketo MCP
- Salesforce MCP
- Clay MCP (or an equivalent validation/enrichment platform) — two functions, whose IDs come from
  `clay-functions.md` in the working folder and are **never hardcoded here**, since a
  function ID only exists in the workspace that built it:
  - **Email validation** — validate, and on failure find and validate a replacement (Step 2)
  - **Person enrichment** — LinkedIn profile, firmographics, job title (Steps 4 and 6)

  If `clay-functions.md` doesn't exist yet, run the first-run setup below. If the user has no such functions
  at all, give them `${CLAUDE_PLUGIN_ROOT}/skills/list-upload/references/clay_setup.md` and offer
  to continue without validation and enrichment — the clean, dedupe and upload steps all still
  work, and the report says which columns went unfilled.

## Marketo tools — match on what they do

Tool names differ between Marketo MCPs. The names below are the ones the official Marketo MCP
uses; another connector may call the same capability something else. **Read the tool
descriptions and match on what each one does**, then name the tool you matched for each
capability as you use it, so a wrong match is visible and correctable.

| What the skill needs it to do | In the official Marketo MCP |
|---|---|
| Find a program by name | `get_program_by_name` |
| List the static lists inside a program | `browse_lists`, scoped to that program |
| Read person fields, their API names and picklist values | `describe_lead` |
| Look up people by email in bulk | `get_leads_by_filter` |
| Import a CSV of people into a static list — upserting each person and adding them to the list in one job | absent; `custom_import_leads_csv` with `list_id` in the [WFP Marketo MCP](https://github.com/tyron-pretorius/marketo-mcp) |
| Create or update people record by record | absent; `custom_sync_leads` in the WFP Marketo MCP |
| Add existing people to a static list, leaving their field values as they are | absent; `custom_add_leads_to_list` in the WFP Marketo MCP |

The first four carry every step of this skill. The last three are listed because people ask
why the skill hands the list over rather than uploading it: the official MCP offers none of
them, and even where a connector does, writing every record into a tool call takes longer than
Marketo's own importer — see [Hand the list over for import](#hand-the-list-over-for-import).

## Salesforce tools — match on what they do

Salesforce is read-only here: it is looked up in Step 3 and never written to.

**The CLI is the route for the lookup itself** — `sf data export bulk` takes the whole list in
one query and writes the rows to a file, so neither the addresses nor the results pass through
the conversation. Step 3 has the commands.

A connector covers the same ground where the CLI is absent, and the names vary between
connectors the same way Marketo's do — match on what the tool descriptions say each one does.

| What the skill needs it to do | Commonly named |
|---|---|
| Query Contact and Lead by email and return named fields — `SELECT <fields> FROM Contact WHERE Email IN (…)`, and the same again for Lead | `soqlQuery` |
| Read an object's fields and their API names, to confirm what `schema.md` records | `getObjectSchema` |

A SOQL query tool covers both lookups on its own, so a connector offering one has everything
this skill asks of Salesforce — at the cost of writing each batch of addresses into a tool
call. Where the CLI and a connector are both absent, Step 3 builds the comparison from Marketo
alone and names the columns that went unfilled.

---

## Phase-by-phase execution

**A step that produces a file for the user to review ends with their go-ahead.** Those are
Step 0's mapping table, Step 3's CRM comparison, Step 4's deduplication file, Step 5's
normalization file and Step 6's finalized list. After finishing one:
1. Share the output file(s) produced in that step
2. Summarise what was done in plain text
3. Ask the user to confirm before proceeding to the next step

**Every other step reports and carries on.** Say what it did in a line or two and begin the
next one in the same turn. The user is waiting on a clean list, and a step with nothing to
review is a step they would wave through.

---

## Input Source

The list may be provided as a CSV file or a Google Sheets link.

- If a Google Sheets URL is provided, check for a `gid` parameter (e.g. `?gid=1579843534`). If present, read **only that specific tab** — do not default to the first tab.
- Export or read the relevant tab as tabular data before proceeding.

---

## Step 0 — Column Mapping

Before any processing, map each CSV column header to its corresponding Marketo API field name using `${CLAUDE_PLUGIN_ROOT}/skills/list-upload/references/schema.md` and the field list read from the connector.

**Decide every column yourself, then show the whole mapping as one table.** Reasoning covers
abbreviations, case variations, synonyms and semantic meaning — `HOTLEAD` → `Hot_Lead__c`,
`NOTES` → `Personal_Notes__c`, `JOBTITLE` → `title`, `LI` → `linkedInProfileURL`.

Where two fields could hold the same column, pick the better one and give the reason in a
word or two: the wider field for free text, the picklist for a value that has to match on
sync, the general field over a lead-specific variant. Where a column has no home, map it to
*ignore*. Where a column needs converting to land in its field — a raw employee count going
into an employee-range picklist — say that in the note.

One message, one table, four columns:

| CSV Column | Sample value | Maps to | Note |
|---|---|---|---|
| EMPLOYEES | 5000 | employee-range picklist | banded on the way in |
| COUNTRY | United States | `CountryCode` | ISO Alpha-2, picklist |
| Address One / Two | 100 King St W, Suite 400 | `address` | combined; textarea holds the length |
| Special Offers | TRUE | — | ignored |

Close with one line — *"Tell me anything you'd map differently and I'll redo it, otherwise
I'll start cleaning"* — and wait for the reply.

**Ambiguity is shown as a choice already made.** The table gives the user something concrete
to react to, and correcting one row costs them a sentence.

---

## Step 1 — Pre-processing

1. Sort the sheet by email address
2. If a full name column is present (and separate first/last name columns are absent), use Python to split it into `firstName` and `lastName` columns

State what this step did in one line and continue straight into Step 2 in the same turn. A
step that changed nothing is worth saying so — *"names were already in separate columns, so
there was nothing to split — moving on to email validation"* — and then the next step's work
begins.

---

## Step 2 — Email Validation

**Check for Clay first, before reading any further into this step.** Three places to look:
`clay-functions.md` in the working folder, a signed-in CLI (`clay whoami`), or a Clay
connector in this session.

**Where all three are missing, ask — rather than assuming either way:**

> Email validation and enrichment in this skill run on **Clay**. It checks whether each address
> is real, finds a replacement where one isn't, and can fill in LinkedIn profile, company size
> and revenue for the people who are new to you.
>
> Do you have a Clay account?
>
> - **Yes — set up the command-line tool** *(recommended)* — about a minute, and it handles any
>   list size in one go
> - **Yes — I'll connect Clay's connector instead** — nothing to install, slower on long lists
> - **No — skip validation and enrichment** — I clean, dedupe and normalize without them

Their answer routes the rest of this step:

- **CLI** — [Setting up the Clay CLI](#setting-up-the-clay-cli) below, then carry on
- **Connector** — they add it in their Claude connector settings and tell you when it's there
- **Skip** — say the line below and go to Step 3. Nothing else in this step applies: no route
  comparison, no install, no sign-in.

> I'll skip email validation, so your addresses go through as they are and the `Email Status`
> columns stay empty. I'll note it in the summary. Everything else runs as normal — the CRM
> lookup, deduplication and the cleaning.

Plenty of teams clean lists without a validation provider, and that run is a complete one. A
skip here also skips enrichment in Step 6, so say so once rather than asking again.

**Where they have a Clay account but no functions built yet**, hand them
`${CLAUDE_PLUGIN_ROOT}/skills/list-upload/references/clay_setup.md`, which describes the two
functions to build, and carry on without validation for this run.

---

With Clay present, use the email validation function recorded in `clay-functions.md`, or find
it now with `list_subroutines` under [First use of a Clay function](#first-use-of-a-clay-function--find-it-confirm-it-record-it). It validates each email and, when the address doesn't
come back valid, finds the company domain and runs an email waterfall to find and validate a
replacement.

### Two ways to reach Clay, and why the size of the list decides

Clay can be reached through its **connector** or through its **command-line tool**, and they
differ in one way that matters enormously once a list gets big.

**The connector carries the records inside the message the agent writes.** Every row — name,
email, company — is typed out in full before the request is sent. Measured on a real run:
**250 records took 1 minute 48 seconds** to write out, before Clay started any work at all.

**Clay's own processing is the other half, and it is the same either way.** Measured on a
2,287-address validation run: **2,277 finished in 3 minutes — about 12 records a second — and
the last 10 took a further 5 minutes**, because an address that fails validation then runs a
waterfall to find a replacement. Total, 8 minutes. The tail follows how many addresses fail,
not how long the list is.

So the figure to give the user is submission **plus** processing:

| List size | Through the CLI | Through the connector |
|---|---|---|
| 250 | 1–3 minutes | 3–5 minutes |
| 500 | 2–4 minutes | 6–8 minutes |
| 1,000 | 2–6 minutes | 9–13 minutes |
| 2,500 | 3–8 minutes | 21–26 minutes |
| 5,000 | 7–13 minutes | 43–49 minutes |

The lower figure in each range is most of the results; the upper is the last few clearing the
waterfall. The connector column adds the time spent writing the records into tool calls, which
the CLI does not pay.

That cost is per pass. Email validation is one pass and enrichment is another, so a 2,500-row
list that gets both runs the clock twice.

**The command-line tool sends the file itself.** The agent writes one command, the file goes
from the folder straight to Clay, and the results come back as a file. A 2,500-row list costs
the same few seconds as a 3-row one.

**Set the CLI up and send every list through it.** The setup happens once per computer and
from then on the submission stops mattering. The connector is what carries the work wherever
the CLI can't be set up — an environment that blocks Clay's addresses, or a user who would
rather not install anything — and the table above is what that costs them.

### Put the time to the user, then validate

Once the route is settled, give them the number and let them choose:

> Validating your 2,287 addresses through Clay takes about **8 minutes** — most results back
> within 3, and the rest are addresses that failed and are having a replacement found.
>
> That figure is from another Clay workspace, and speed varies between them. I can time yours
> first if you'd rather work from a real number — a 50-address test takes under a minute.
>
> - **Time it first** — a short test, then a real time estimate *(recommended)*
> - **Proceed with email validation**
> - **Skip email validation**

**Where they ask for a timing, measure rather than estimate.** Submit a small batch — 50
addresses is enough — time it from submission to `complete`, and scale up, saying plainly that
the tail depends on how many addresses turn out to be invalid.

**Where they skip it**, carry on and say so in the step's summary: the `Email Status` columns
stay empty, no replacement addresses are found, and every address goes forward as given.

### Setting up the Clay CLI

Do this before sending anything. Where the run is happening decides how much work it is:

```bash
python3 -c "import os; print('cowork' if os.path.isdir('/mnt/user-data') or os.path.isdir('/mnt/outputs') else ('claude-code' if os.environ.get('CLAUDECODE') else 'unknown'))"
```

**Check for Cowork first.** Cowork *is* Claude Code running in a cloud container, so
`CLAUDECODE` is set in both places. The `/mnt` folders exist only in the container.

#### In Claude Code

The setup takes about a minute and needs nobody's permission, and it holds afterwards: the
binary and the sign-in both live on the user's own machine. Where `/setup-for-claude-code`
has already been run there, both are in place and `clay whoami` confirms it in one call.
Go to **Install and sign in** below.

#### In Cowork

Cowork containers reach the internet through an allowlist, and Clay's addresses are absent
from it by default — every one of them answers `403` from the proxy before the request
reaches Clay. The CLI reports a blocked `api.clay.com` as a sign-in failure, which reads as
an auth problem and is really a network one.

**Three hosts have to be allowed, and they are on separate domains:**

| Host | What needs it |
|---|---|
| `api.clay.com` | signing in, starting runs, polling status |
| `clay-tool-runs-production.s3.us-east-1.amazonaws.com` | uploading the JSONL, and downloading the results — the same bucket serves both |
| `developers.clay.com` | Clay's documentation, where a run needs to look something up |

The bucket is the one that gets missed, because allowing the first domain makes sign-in and
`runs start` work, and the failure only appears at the upload.

Say this, and let the user choose:

> The quickest way to send a list to Clay is its command-line tool, and it needs two web
> addresses that Cowork blocks by default. Two ways forward:
>
> **Run this in Claude Code instead** — the **Code** tab in your Claude desktop app. The tool
> installs there in about a minute and everything works. This is the faster route today.
>
> **Or ask your Claude administrator to allow these three addresses:**
> `api.clay.com`, `clay-tool-runs-production.s3.us-east-1.amazonaws.com` and
> `developers.clay.com`. It's a one-time change on their side, and after that Cowork works
> the same as Claude Code. All three are needed — the middle one is the storage the list
> file itself travels through.
>
> In the meantime I can carry on here through the Clay connector — it works fine, it will
> just spend about **<N>** minutes sending your list across before Clay starts.

Fill `<N>` from the table above for their actual row count, so the trade is concrete.

**Once those addresses are allowed, install the CLI here on every run.** Cowork hands each
session a brand-new container, so the binary and the signed-in session from last time are
both gone — **Install and sign in** below runs in full, start to finish, every time. Budget
about a minute for the install and a browser approval from the user for the sign-in, and say
so up front rather than partway through:

> Quick one before I start: Cowork gives me a fresh machine each session, so I need to
> install Clay's tool and have you approve a sign-in. Takes about a minute, and then your
> whole list goes across in seconds.

Where the user would rather skip that each session, the connector is there and the run
carries on without it.

#### Install and sign in

The CLI ships in Clay's own repository, as a launcher that downloads a checksum-verified
binary for the current platform on first use. (The `clay` and `clay-cli` packages on npm are
unrelated projects by other authors.)

**Look for an existing install before cloning anything.** In Claude Code there usually is
one — `/setup-for-claude-code` puts it at a fixed path and signs it in. In Cowork there never
is, and this check costs one call to find that out:

```bash
CLAY=$(command -v clay || echo ~/.clay/agent-plugins/clay/bin/clay)
"$CLAY" whoami
```

That returns the workspace and user when the CLI is installed and signed in — go straight to
sending the list. Where the binary is missing, install it:

```bash
mkdir -p ~/.clay && rm -rf ~/.clay/agent-plugins
git clone -q --depth 1 https://github.com/clay-run/agent-plugins.git ~/.clay/agent-plugins
~/.clay/agent-plugins/clay/bin/clay --version
```

A signed-in CLI returns the workspace and user. Otherwise sign in with the device flow, which
works without a local browser. It waits for approval, so run it in the background:

```bash
~/.clay/agent-plugins/clay/bin/clay login --device > /tmp/clay_login.log 2>&1 &
sleep 5; cat /tmp/clay_login.log
```

Give the user the URL and code it prints and wait for them to approve it before going on.
The session is stored in `~/.config/clay/config.json`, so in Claude Code this happens once
per computer and in Cowork it happens once per session, along with the install above.

#### Sending the list through the CLI

1. **Write the records to a JSONL file with a script** — one line per person, shaped
   `{"id": "row-0", "inputs": {…}}`, with the input names `clay-functions.md` records.
   Building it from the CSV in Python is what keeps the rows out of the conversation, which
   is the whole point of this route.
2. **Submit the file.** Up to 50,000 rows per run:
   ```bash
   clay routines runs start <routine id> --bulk rows.jsonl
   ```
   It returns a `routineRunId` immediately.
3. **Write the `routineRunId` into `clay-tasks.md`** before anything else.
4. **Poll with an until-loop**, which waits on the run's own status rather than on a guessed
   duration:
   ```bash
   until out=$(clay routines runs get "$RUN" 2>&1); echo "$out" | grep -q '"status": "complete"'; do
     echo "$out"; sleep 15
   done; echo "$out"
   ```
   Each pass prints `status`, `total` and `finished`, so progress is visible while it runs. A
   long foreground `sleep` chained ahead of a command is refused, which is what this form
   avoids.
5. **On `complete` it returns a `resultUrl`.** Download it and read from the file:
   ```bash
   curl -s "<resultUrl>" -o clay_results.jsonl
   ```
   One JSON object per line — `{"id", "status", "result"}` — and `result` holds exactly what
   the connector returns, so everything downstream reads the same.

**Exit codes say what to fix:**

| Code | Meaning | What fixes it |
|---|---|---|
| 6 | `not_found` | The routine exists but API & CLI access is switched off. In Clay, open the function → **Integrations** → tick **API & CLI** |
| 3 | `auth_forbidden` | The signed-in account can't run that routine |
| 2 | `validation_error` | A malformed JSONL row — the message names the line number |

**The routine id is the prefixed form**, `function:t_...`, as recorded in `clay-functions.md`.

### Running the function through the connector

This is the route wherever the CLI can't be set up.

- Call `run_subroutine_direct`, passing the validation routine id from `clay-functions.md` as its `subroutine_id` parameter — the tool names the parameter `subroutine_id`, and accepts the id with or without the `function:` prefix
- Required inputs per record: whatever `clay-functions.md` records — typically `Email`, `First Name`, `Last Name`, `Company Name`
- **Build the batches and make every call here, in this conversation.** Each call returns a
  `taskId`, and that id is the only route back to the results, so it belongs where you can
  read it and write it down as it arrives.
- **Batch size: up to 1,000 records per call, divided evenly.** `run_subroutine_direct`
  accepts a maximum of 1,000 input objects. Take the smallest number of batches that keeps
  every batch at 1,000 or under and split the rows equally between them — 2,287 records go as
  763, 762 and 762.
- **Write each `taskId` into the working folder the moment it returns**, ahead of polling and
  ahead of any other work. See [Clay task IDs](#clay-task-ids) below.
- **Submit every batch, then hand back to the user.** Send the batches one after another,
  writing each `taskId` into `clay-tasks.md` as it returns. Once they are all in, show the
  user the file, say how many batches went out and how many records each carries, and tell
  them Clay needs a minute:

  > Three batches are in — 763, 762 and 762 records. The task IDs are saved in
  > **clay-tasks.md**. Give Clay a minute to work through them, then tell me to fetch the
  > results.

  Their go-ahead is what starts the retrieval. Clay carries on working whether or not this
  conversation is watching it, and the task IDs in the file are what the results are read
  back with — at any point, in this run or a later one.

- **Retrieving.** Call `get-task-context` with each `taskId` from the file. Read
  `processedEntities` against `totalEntities` to see how far Clay has got, and `isComplete`
  to see it has finished — `isComplete` counts errors as finished. Results come back 100
  entities to a page: read `page`, `hasMore` and `totalEntities`, and keep paging while
  `hasMore` is true. Mark a row in `clay-tasks.md` as retrieved once its results are in the
  working CSV.
  - Where `isComplete` is false, say how many records are through and offer another minute.

### Clay task IDs

Every submission returns an id — a `taskId` from the connector, a `routineRunId` from the
CLI. Credits are spent when a batch is submitted; retrieving its results afterwards is free
and repeatable. That makes the id the most valuable thing produced in the run.

**Record each one in `clay-tasks.md` in the working folder as soon as it comes back:**

```markdown
# Clay task IDs
<!-- Written by list-upload. One row per submitted batch. -->

| Date | Function | Route | Run/Task ID | Rows | Covers | Retrieved |
|---|---|---|---|---|---|---|
| 2026-09-15 | Validate Email | cli | run_XXXX | 2287 | all | yes |
| 2026-09-15 | Validate Email | connector | mcp-task-YYYY | 762 | rows 764–1525 | no |
```

**Read this file at the start of every run.** Where it already lists a batch covering records
you are about to submit, retrieve against that id and take the results from there —
`clay routines runs get` for a CLI run, `get-task-context` for a connector one. The credits
for those records are already paid.

**Where a submission's outcome is unclear, retrieving against the recorded id answers it.** A
call that errored, a session that ended, a batch you are unsure went out — read how many
records the run reports finished, and submit only those the retrieval shows are genuinely
missing.

Without a connected folder, print the task IDs into the conversation as they arrive and say
what they are for, so the user can hand them back when the run is picked up again.

### Interpreting results

The function returns one of two response shapes — confirm against `clay-functions.md`, which records what this workspace's function actually returned when it was tested:

**Incoming email is valid:**
```json
{ "status": "valid" }
```

**Incoming email is invalid (waterfall ran):**
```json
{
  "status": "<incoming email status>",
  "found_email": "<new email address>",
  "found_email_status": "valid" | "invalid" | ...
}
```

### Updating the CSV

Add three columns to the working CSV:

| Column | Value |
|---|---|
| `Email Status` | The validation status of the original email |
| `Email Suggestion` | The `found_email` value if the waterfall found a replacement, otherwise blank |
| `Found Email Status` | The validation status of the found email, if one was returned |

### Handling invalid records

This whole section applies only where validation ran; a skipped Step 2 produces nothing to
handle here.

For any record where the original email is invalid **and** no valid replacement was found:
- Use reasoning to check for obvious misspellings using the person's name, company, and email domain pattern
- If still unresolvable, flag it for the user to review

Present the flagged records to the user and resolve together before proceeding.

**Where validation ran, only records with a confirmed valid email — original or replacement —
proceed to the steps below.** Where Step 2 was skipped there is nothing to gate on, so every
record carries on with the address it arrived with, and the run's summary says so.

After completing, share the output, summarise what was found, and ask the user to confirm before proceeding.

---

## Step 3 — Map & CRM Lookup

Take the list of unique email addresses — the validated ones where Step 2 ran, the addresses
as supplied where it was skipped — and query the platforms that are connected.

**Work with the connectors that are present.** With Salesforce absent, build the comparison
from Marketo alone and say so in this step, naming the columns that came back unfilled as a
result. The gap is easiest to judge sitting next to the data it affects.

### Price both lookups, then ask once

Each lookup costs what it costs before any data comes back, and the two differ by an order of
magnitude. Work both out first and put them to the user together.

**1. Establish the route each system has.**

| System | Route | Capacity |
|---|---|---|
| Salesforce | `sf` CLI, checked with `sf org list` | the whole list in one query per object |
| Salesforce | a connector, where the CLI is absent | the batch size its tool description states |
| Marketo | a connector | the batch size its tool description states |

Connectors cap an email filter differently, and often well below an id filter, because the
addresses travel in the URL. One allows 300 ids but 30 emails per call; another allows 300 and
asks for a retry at 100 after a gateway error. Read what each one says.

**2. Work out the time from the characters, not the request count.** Both APIs answer in 1–2
seconds. What a lookup costs is writing every address into a tool call, so the length of the
list sets the total — **about 150 characters a second**, measured across live runs. A
2,287-address list is roughly 60,000 characters, or **5 to 7 minutes per system**. Salesforce
through a connector pays that twice, since Contact and Lead are separate queries.

**Batch size changes the request count and the failure modes, and barely moves the clock.**
Measured: 76 requests of 30 addresses took 7.4 minutes, and 8 requests of 300 emit the same
60,000 characters. Take the larger batch for fewer round trips rather than for speed.

For a 2,287-address list:

| Route | Requests | Approximate time |
|---|---|---|
| Salesforce via the CLI | 2 | **about 20 seconds** |
| Salesforce via a connector | 16 at 300 per query | 10–15 minutes, both objects |
| Marketo via a connector | 8 at 300, or 76 at 30 | 5–7 minutes either way |

**3. Say what a partial answer actually costs, then ask.** Most Marketo instances are kept in
bidirectional sync with Salesforce, so the same person usually carries the same field values in
both. That makes a Salesforce-only lookup far closer to running both than the choice looks —
worth saying plainly, because half an hour of Marketo lookup is a real cost to weigh against a
gap that may be small.

What a Salesforce-only run genuinely misses: anyone who exists in Marketo and never synced
across, any field the sync doesn't carry, and anywhere the sync has fallen out of step.

Put that in the message, then the options:

> Here's what each lookup should cost for your 2,287 records:
>
> - **Salesforce** — 2 queries through the CLI, about 20 seconds
> - **Marketo** — 76 requests through the connector, roughly 7 minutes
>
> If your Marketo and Salesforce are kept in sync, the values will mostly match, so Salesforce
> alone gives you nearly the same picture. What you'd miss is anyone who's in Marketo but never
> synced across, or any Marketo person who has diverged from their Salesforce equivalent
> because of sync errors.
>
> These are estimates from the guidance in this skill. If you'd like accurate numbers for your
> own connectors, I can run a quick test with each one first.
>
> - **Time it first** — a short test against each connector, then real numbers
> - **Proceed with Both**
> - **Proceed with Salesforce Only**
> - **Proceed with Marketo Only**
> - **Neither** — I work from the CSV alone and skip the comparison

**Carry the consequence of a partial answer into Step 3's output rather than into the
question.** Where Marketo is skipped its records come back as new, so those people default to
*Upload & Update* — say that in the summary once the choice is made, where it is about their
actual data instead of a label on a button.

**Where they ask for timings, measure rather than estimate.** Send one batch to each system at
the batch size that system allows, time it end to end, and scale up:

> Tested on your connectors: Marketo took 31 seconds for 100 addresses, so 2,287 works out at
> about 12 minutes. Salesforce answered the whole list in 11 seconds. Go ahead?

The figures in the table above come from other people's runs and are a starting point, not a
promise — connector speed, list length and address length all move them. A measured number is
worth the half-minute it costs on a list that would otherwise run for ten.

**4. Where a wait is long, offer the faster route alongside the choice.** For Marketo:

> If you'd rather this took minutes than half an hour, there's a Marketo MCP that sends the
> whole lookup in a few requests — the tool to look for is **`custom_get_leads_by_filter`**,
> which takes 300 addresses at a time. Setup is at
> https://github.com/tyron-pretorius/marketo-mcp and this post walks through it:
> https://theworkflowpro.com/marketo-mcp/

And for Salesforce, where the CLI is absent, `/setup-for-claude-code` installs it in about a
minute and turns 10–20 minutes into 20 seconds.

Record the answer in the step's summary, so the comparison file and every later step say which
system each value came from.

### A large result is a success, not a limit

**A result too large to return inline is saved to a file and the tool reports where.** The call
succeeded and the records are on disk — read them from there with `offset`/`limit` or `jq`, and
keep the batch size. This applies to any connector: a Marketo lookup, a Salesforce `soqlQuery`,
a schema describe. A batch's response size follows how many records matched, so the same batch
size can return inline once and be persisted the next time.

### Salesforce — one query for the whole list

Salesforce takes the entire list in a single query through its own CLI, which reads the SOQL
from a file and writes the results to a file. Both directions stay out of the conversation, so
a 2,287-address list costs the same as a 3-address one. Measured on a real run: **585 Lead
matches in 9.2 seconds, 100 Contact matches in 10.2 seconds.**

**This route runs in Claude Code.** `sf` signs in through a local browser and this build has no
device flow, so a Cowork container — which has no browser, and blocks Salesforce's domains at
its proxy — uses the connector instead. The browserless alternatives (`sf org login jwt` with a
connected app and private key, or `sf org login sfdx-url`) need admin setup or move a
long-lived credential into a container that is thrown away at the end of the session. In Claude
Code, `/setup-for-claude-code` installs and signs the CLI in; `sf org list` confirms it.

1. **Build the query in a file with a script**, one per object:
   ```
   SELECT <mapped fields> FROM Lead WHERE Email IN ('a@x.com','b@y.com',…)
   ```
   SOQL allows 100,000 characters, and 2,287 addresses come to about 61,000 — so a list of
   this size goes in one query, with room for roughly 3,700 addresses before splitting.

2. **Run it through the bulk export**, which sends the query in a POST body and writes the
   rows to CSV:
   ```bash
   sf data export bulk --query-file lead.soql --output-file sfdc_lead.csv \
     --result-format csv --wait 10 --target-org <alias>
   ```

3. **Read the results from the CSV**, joining on email.

`sf data query` is the other way to run a SOQL statement, and it sends the query as a URL
parameter — a full-list query answers `Request Header Fields Too Large`. `sf data export
bulk` is the one that carries a list this size.

### Marketo — through the connector, at the batch size it states

Marketo has no equivalent CLI, so every address is written into a tool call at the batch size
its tool description allows. Send the batches, and report progress against the estimate given
in step 2 above so a long run stays legible.

### Fields to retrieve

Use `${CLAUDE_PLUGIN_ROOT}/skills/list-upload/references/schema.md` to find the correct API field names for both Marketo and Salesforce. For each platform, retrieve all fields that map to columns in the CSV. In addition, **always retrieve `linkedInProfileURL` and `website`** from both platforms regardless of whether they appear in the CSV — these are needed to resolve discrepancies in later steps.

For Salesforce, retrieve the same mapped fields using their SFDC API names as defined in `${CLAUDE_PLUGIN_ROOT}/skills/list-upload/references/schema.md`, confirming them against the object's own field list where a describe capability is available. Where a field exists in one platform but not the other, retrieve what is available and leave the other blank.

### Raw lookup files

- Save the Marketo lookup results to: `[YYYY-MM-DD]_[original_filename]_marketo_lookup.csv`
- Save the Salesforce lookup results to: `[YYYY-MM-DD]_[original_filename]_sfdc_lookup.csv`
- Add two columns to the working CSV:
  - `Found in Marketo` — `True` / `False`
  - `Found in Salesforce` — `True` / `False`

### CRM comparison file

For every person found in **either** Marketo or Salesforce, generate `[YYYY-MM-DD]_[filename]_crm_comparison.csv` and send it to the user. Build this file as follows:

- Sort all rows by email address
- For each matched person, output up to three consecutive rows grouped together:
  - A `csv` row — the values from the cleaned working CSV
  - A `marketo` row — the values returned from Marketo (leave all fields blank if not found there)
  - A `sfdc` row — the values returned from Salesforce (leave all fields blank if not found there)
- Add a `_source` column as the first column with values `csv`, `marketo`, or `sfdc`
- Highlight (in plain text below the file) any field where the CSV value differs from what is in Marketo or Salesforce — call out the specific field, the CSV value, and the CRM value so the user can make an informed decision
- **Resolve those differences CSV first, then Marketo, then Salesforce** — the CSV is first-party data and the most recently collected. Apply that ranking to the differences you just listed and say so in the same message: *"Where these disagree I'm taking the CSV value, then Marketo, then Salesforce — say the word if you'd rank them differently."* The same ranking carries into Step 4 deduplication, and a reordering asked for here applies from that point on.
- People **not** found in either system are excluded from this file

### Upload Status

After sharing the CRM comparison file and walking through any flagged discrepancies, add an `Upload Status` column to the working CSV. For every person found in Marketo or Salesforce, agree on their status with the user before proceeding:

**Offer the statuses the available tools can carry out.** Check them against
[Marketo tools](#marketo-tools--match-on-what-they-do) before showing the list:

| Status | What it does | Which import mode it needs |
|---|---|---|
| **Upload & Update** *(default)* | uploads the record and refreshes existing field values from the CSV | **Default** |
| **Upload Only** | adds the person to the list and leaves their existing field values alone | **Skip new people and updates** |
| **Exclude from Upload** | leaves this person out entirely | neither file |

Each status maps onto one of the two List Import Modes in Marketo's importer, which is what
Step 7 splits the file by.

Where a status has no tool behind it, offer the ones that do and say so in a line: *"Your
Marketo connector imports and updates in one step, so everyone uploaded will have their fields
refreshed from the CSV — tell me who to leave out."* The pointer at the end of Step 6 covers
someone who needs the missing option.

People **not** found in either CRM system default to **Upload & Update** automatically — no decision needed.

Once Upload Status is confirmed for all matched records, and any field corrections from the comparison have been applied to the working CSV, proceed to Step 4.

After completing, share the lookup files, summarise what was found, and ask the user to confirm before proceeding.

---

## Step 4 — Deduplication

Identify rows in the CSV that refer to the same person (same email, or strong name+company match) and merge them into a single row. Use the source of truth ranking from Step 3, and the CRM lookup data it produced, to decide winning field values.

### Merge rules

- If one row has `firstName` but no `lastName`, and another has `lastName` but no `firstName`, the merged row takes both
- If emails differ and validation ran, take the address it confirmed valid. Without validation, take the address whose domain matches the company's website, and where neither does, the one on the more complete row
- If names or company names conflict, check the email address domain and any LinkedIn profile URL for clues on which is correct
- If country and phone number conflict, use each to infer the other (e.g. a +44 number implies UK; a US address implies a +1 prefix)
- For any other discrepancy, apply the source of truth ranking from Step 3

### When confidence is below 70%

If you cannot resolve a discrepancy with at least 70% confidence:
1. Ask the user whether they want to use the Clay Enrich Person function and/or web search to resolve it
2. If the user agrees to enrichment: send it the same way Step 2 sent validation. Through the connector, call `run_subroutine_direct`, passing the enrichment routine id from `clay-functions.md` as its `subroutine_id` parameter, with the inputs it records (typically `Email`, `First Name`, `Last Name`, `Company`, `Job Title`). It returns the fields `clay-functions.md` lists — typically `LinkedIn URL`, `size` (employee range), `annual_revenue` (range), `employee_count`, `title`. Poll `get-task-context` until `isComplete: true`, recording the `taskId` in `clay-tasks.md` as it returns. If the enrichment returns the needed information, skip web search.
   - **After receiving enrichment results, map the returned values to the target instance's real picklist values before writing to the CSV.** Take those from `lead-schema.md` if it records them, otherwise read them from the connector. The bundled `schema.md` holds examples from one instance, not a standard — never write a value sourced from it without checking.
     - employee range → the nearest employee-range picklist value in the target instance. Where the provider's range spans several buckets or doesn't align, choose the bucket containing its midpoint.
     - revenue range → the nearest revenue-range picklist value, same midpoint logic.
     - **Never write a provider's raw value directly** — only a value confirmed to exist in the target picklist. A value that isn't in the picklist fails at sync time, which is far more expensive to unpick than checking first.
3. Only use web search as a last resort and only if the user explicitly requested it. Search using the person's LinkedIn URL if present, otherwise search by name and company
4. Save enrichment results to: `[YYYY-MM-DD]_[original_filename]_enrichment.csv`
5. Save web search results to: `[YYYY-MM-DD]_[original_filename]_websearch.csv`

### Deduplication output file

Generate `[YYYY-MM-DD]_[filename]_deduplication.csv` and send it to the user. Build this file as follows:

- Sort all rows by email address
- For each email that appears more than once, output all the original duplicate rows grouped together, followed immediately by a single **WINNER** row showing the merged values selected for each field
- Add a `_row_type` column as the first column with values `duplicate` (for each original row) or `WINNER` (for the merged result row)
- Records with no duplicates are **not** included in this file — it only shows groups where merging occurred
- After sending the file, summarise the deduplication in plain text (e.g. "Removed 7 duplicates across 6 email groups") and **ask the user to confirm the winner rows look correct before proceeding to Step 5**

---

## Step 5 — Data Validation

Work through each of the following fields if present in the CSV:

**Ask which form the user wants for country and state, once, before running either script:**

> Country and state can come out either way — codes (`US`, `CA`) or names (`United States`,
> `California`). Which suits where this list is going?

Marketo and Salesforce both accept either, and which one is right depends on the target field:
a picklist constrained to ISO codes takes codes, a free-text field usually holds names. Where
`lead-schema.md` already records the form those fields hold, use it and say so rather than
asking again. Pass their answer as `--to code` or `--to name` to both scripts, so the two
columns agree.

### Country
- Run `${CLAUDE_PLUGIN_ROOT}/skills/list-upload/scripts/normalize_country.py` against the working CSV, passing the country column name and `--to code` or `--to name`
- The script handles common variants and abbreviations via its hardcoded table, then falls back to pycountry fuzzy search
- For any value the script flags as unresolved, use reasoning to find the correct ISO Alpha-2 mapping (e.g. "Congo" → "CD") and apply it manually

### State
- Run `${CLAUDE_PLUGIN_ROOT}/skills/list-upload/scripts/normalize_state.py` against the working CSV, passing the state and country column names and the same `--to` value used for country. The script reads the country column as either a code or a name, so the order of the two runs is free.
- The script covers 10 countries only (AU, BR, CA, CN, IN, IE, IT, JP, MX, US) and automatically skips records from unsupported countries
- For any value the script flags as unresolved, use reasoning to find the correct 2-letter code and apply it manually
- Cross-check that the resolved state code belongs to the correct country (e.g. don't apply US codes to a Canadian record)

### City
- Correct any clear misspellings using reasoning

### Phone
Use a **hybrid approach**:
1. Run `${CLAUDE_PLUGIN_ROOT}/skills/list-upload/scripts/normalize_phone.py` against the working CSV (run ${CLAUDE_PLUGIN_ROOT}/skills/list-upload/scripts/normalize_country.py first so the country column is already ISO Alpha-2 — the script uses it as a region hint for bare local numbers)
2. For any number the script flags as `invalid` or `parse_error`, fall back to LLM reasoning — use the country, name, and any other row context to infer the correct E.164 format and apply it manually
3. If neither the script nor reasoning can resolve a number, flag it for the user to review
4. Ensure all phone numbers have a leading `+` (the script guarantees this for any number it successfully parses)

### Industry

**Validate the seed's target values against the real picklist first, once per working folder.**
Read the target instance's actual `Industry` picklist from the connector and check every distinct
target value in the bundled seed against it. The seed maps onto **Salesforce's 32 standard
Industry values**, which is right for an org that never touched the field and wrong for one that
replaced it — a GICS-derived list with `Software`, `Retailing` and `Banks` is a common
replacement, and only 8 of its values overlap with the standard set.

Report the overlap in one line ("44 of your 68 picklist values differ from the standard set —
I'll remap as I go"), record the real picklist in `lead-schema.md`, and resolve against that from
then on. The seed's **keys** stay useful regardless: the 178 incoming variants (`saas`, `mfg`,
`non-profit`) are generic, and only the targets depend on the org.

- If an `industry` column is present, run `${CLAUDE_PLUGIN_ROOT}/skills/list-upload/scripts/normalize_industry.py` against the working CSV, passing the industry column name
- The script looks up each value (case-insensitive) in the merged mapping table — the bundled seed plus `industry-mappings.json` from the working folder, with the working-folder entries winning on conflict — and applies the matching SFDC API value. Pass the working-folder file to the script with `--extra-mappings` if it exists.
- For any value the script flags as `unresolved`, **or any value whose seed target isn't in the real picklist**, work out the correct value from the instance's actual picklist, apply it to the working CSV, and add the mapping to `industry-mappings.json` in the working folder — never to the bundled seed. Don't ask the user to do this mapping themselves. Only surface a value if two options in their picklist are genuinely equally plausible and the distinction matters (e.g. "Banking" could be "Banks" or "Diversified Financial Services" depending on context).
- Watch for label/API divergence rather than assuming it. Salesforce's standard value is "Not for Profit" for both label and API name; one customized instance had the label "Not For Profit" against the API value `Not_For_Profit`, with every other label matching its API value. Confirm against the connector.

### Website
- Run `${CLAUDE_PLUGIN_ROOT}/skills/list-upload/scripts/normalize_website.py` against the working CSV, passing the website column name
- The script strips protocol, www., paths, query strings, and trailing slashes to leave a bare domain

### Normalization output file

After running all validation, generate `[YYYY-MM-DD]_[filename]_normalization.csv` and send it to the user. Build this file as follows:

- Sort all rows by email address
- **Only include records where at least one field value changed** during validation — unchanged records are excluded
- For each changed record, output two consecutive rows: the original values first, then the normalized values directly beneath it
- Add a `_row_type` column as the first column with values `original` or `normalized`
- After sending the file, call out any ambiguous or flagged cases (e.g. phone/country mismatches) explicitly in plain text and **ask the user to confirm the normalized values look correct before proceeding to Step 6**

---

## Step 6 — Final Review and Optional Enrichment

1. Generate `[YYYY-MM-DD]_[filename]_finalized_list.csv` from the current working data and send it to the user — this is the exact list that will be uploaded to Marketo
2. **Offer enrichment with its time attached**, for the net-new records — those found in
   neither Marketo nor Salesforce. Where Clay is absent, say the enrichment columns stay empty
   and move on; the finalized list is already complete without them. Count them first, take the time from the table under
   [Two ways to reach Clay](#two-ways-to-reach-clay-and-why-the-size-of-the-list-decides),
   and put it the same way Step 2 put validation:

   > **412** of your records are new to both systems. Enriching them through Clay fills in
   > LinkedIn profile, company size, revenue range and employee count where Clay can find them —
   > on a list this size, expect somewhere around **10 to 15 minutes**.
   >
   > That range is from someone else's Clay workspace, and enrichment speed varies a lot
   > between them. I'd suggest timing yours first — 20 records, about two minutes.
   >
   > - **Time it first** — a short test, then a real time estimate *(recommended)*
   > - **Proceed with enrichment**
   > - **Skip enrichment**

   **Enrichment runs on a different clock from validation, so the Step 2 table does not apply
   here.** Measured on one workspace: **10 records took 1 minute 53 seconds, 50 took 3 minutes
   36**. Five times the records for less than twice the time — it runs records concurrently, so
   the cost grows far more slowly than the count, and both runs ended with a straggler or two
   finishing a couple of minutes after the rest.

   | Net-new records | Rough expectation |
   |---|---|
   | 10 | ~2 minutes |
   | 50 | ~4 minutes |
   | 250 | ~8 minutes |
   | 1,000 | ~25 minutes |

   **Everything past 50 in that table is extrapolation from two points on one workspace, so
   lead with the test rather than the number.** Concurrency, plan and provider load all move it,
   and nothing here has been measured above 50 records:

   > I can time this on your Clay first — 20 records takes about two minutes and then the
   > estimate is yours rather than mine. Worth it before committing to a few thousand.

   Where they skip, say so in the summary — the enrichment columns stay empty and the finalized
   list is the one already on screen.

   - **By default, only enrich records where `Found in Marketo = False` AND `Found in Salesforce = False`** — people already in the CRM are assumed to have sufficient data
   - If the user explicitly wants to enrich existing CRM records as well, ask them to confirm before doing so
   - To run enrichment: send it the way Step 2 sent validation. Through the connector, call `run_subroutine_direct`, passing the enrichment routine id from `clay-functions.md` as its `subroutine_id` parameter, with the inputs it records. Poll `get-task-context` until `isComplete: true`. Send in the batch size `clay-functions.md` records (up to 1,000 per call, divided evenly), and record each `taskId` in `clay-tasks.md` as it returns.
   - **After receiving enrichment results, map the returned values to the target instance's real picklist values before writing to the CSV.** Take those from `lead-schema.md` if it records them, otherwise read them from the connector. The bundled `schema.md` holds examples from one instance, not a standard — never write a value sourced from it without checking.
     - employee range → the nearest employee-range picklist value in the target instance. Where the provider's range spans several buckets or doesn't align, choose the bucket containing its midpoint.
     - revenue range → the nearest revenue-range picklist value, same midpoint logic.
     - **Never write a provider's raw value directly** — only a value confirmed to exist in the target picklist. A value that isn't in the picklist fails at sync time, which is far more expensive to unpick than checking first.
3. Do **not** re-enrich anyone already processed during the deduplication step (Step 4)
4. Save any enrichment results to: `[YYYY-MM-DD]_[filename]_enrichment.csv`
5. **The finalized list is the deliverable.** Present it as the finished clean list and ask
   them to check it: *"Here's your cleaned list — 2,241 records. Have a look, and tell me when
   you're happy for me to split it for import."*

   Step 7 then writes the import-ready files and explains how to load them. A run that ends at
   the CSV ends well — save `lead-schema.md` and `industry-mappings.json` either way, since the
   schema and the industry mappings are worth keeping whatever happens next.

---

## Step 7 — Save what you learned, and hand the list over

**Record what you resolved, so the next list skips it.** Two files, written into the folder
as part of finishing:

- **`lead-schema.md`** — the real API names you resolved from the connectors, including the
  custom fields that arrive as `???` in the bundled seed. This is the live version; the seed
  in `references/` is read-only and a plugin update overwrites it.
- **`industry-mappings.json`** — every industry value you worked out on this run, merged
  over anything already there. Mappings are the slowest part of a first import and the
  easiest to lose.

Without a folder, hand both over with the cleaned CSV and say what they save next time.

### Hand the list over for import

**The upload itself happens in Marketo's own interface, and the files this step produces are
what goes into it.** Uploading through a connector means writing every record into a tool call
one character at a time — **upwards of 10 minutes for 1,000 records**, against a file picker
and a few clicks in Marketo's importer. The official Marketo MCP has no create-or-update
capability at all as of September 2027, so for most people the question is moot; where a
connector does offer one, the importer still wins.

### Split the file by what each group needs

Marketo's importer applies one **List Import Mode** to a whole file, and the two modes the
`Upload Status` column distinguishes are exactly the two the wizard offers. So write one file
per group:

| File | Who is in it | List Import Mode to choose |
|---|---|---|
| `upload_and_update_[date]_[filename].csv` | `Upload & Update` — their fields are refreshed from the CSV | **Default** |
| `upload_only_[date]_[filename].csv` | `Upload Only` — added to the list with their existing data untouched | **Skip new people and updates** |

Write the second file only where records carry that status. Where every record is
`Upload & Update`, one file is the whole deliverable and the mode is **Default**.

`Exclude from Upload` records go into neither file. Say how many were left out.

### What to tell them

> Your cleaned list is ready — **2,241 records**, split into two files because they need
> different import settings:
>
> - **upload_and_update_2026-09-16_q3-webinar.csv** — 1,829 people. In Marketo, choose
>   **List Import Mode: Default**. Their fields get refreshed from this file.
> - **upload_only_2026-09-16_q3-webinar.csv** — 412 people. Choose **List Import Mode: Skip
>   new people and updates**. They're added to the list with their existing data left alone.
>
> In Marketo: **Database → Import List**, pick the file, set the mode, map the columns, and
> choose the program's list on the last step. The column headers are already Marketo API field
> names, so the mapping should come up matched.
>
> 46 records were excluded and are in neither file.

**Where a list needs splitting across several Marketo lists** — attendees and registrants, say
— ask which column decides and write one file per destination, naming each after its list.
Show the counts before writing:

> Splitting on `Attended`: 575 records to 02-Attended, 1,666 to 01-Registered. Shall I write
> those as two files?

### Deliver the files

Write them into the connected folder and **send them into the chat with SendUserFile as well**.
The folder is where they live afterwards; the chat is where the user is now. Without a folder,
the chat copies are the deliverable.

---

## Output File Naming Convention

File type comes first so it is visible in the Cowork outputs panel without truncation.

| File | Name |
|---|---|
| Marketo lookup | `marketo_lookup_[YYYY-MM-DD]_[filename].csv` |
| Salesforce lookup | `sfdc_lookup_[YYYY-MM-DD]_[filename].csv` |
| CRM comparison | `crm_comparison_[YYYY-MM-DD]_[filename].csv` |
| Deduplication review | `deduplication_[YYYY-MM-DD]_[filename].csv` |
| Normalization review | `normalization_[YYYY-MM-DD]_[filename].csv` |
| Finalized list | `finalized_list_[YYYY-MM-DD]_[filename].csv` |
| Enrichment results | `enrichment_[YYYY-MM-DD]_[filename].csv` |
| Web search results | `websearch_[YYYY-MM-DD]_[filename].csv` |
| Import file — fields refreshed | `upload_and_update_[YYYY-MM-DD]_[filename].csv` |
| Import file — list only | `upload_only_[YYYY-MM-DD]_[filename].csv` |
