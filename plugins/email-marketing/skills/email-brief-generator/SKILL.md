---
name: email-brief-generator
description: >
  Turn a voice note, a winding paragraph, a transcript, or a handful of bullet points into a complete email brief (subject line, preview text, and body copy) built on the CHEETAH Email Framework. Just say 'create an email brief for the webinar' and skip the blank page entirely.

  Triggers on "write an email brief", "create an email brief", "brief me an email", "I need an email for X", "draft an email for this webinar/launch/newsletter", "here's a voice note about an email", "turn this into an email brief", or asking for subject line and preview text options for a campaign.
metadata:
  version: "3.0.0"
---

# Email brief generator

Turn raw direction into a brief someone can build from.

**Grading an email that already exists is a different skill** — `email-scorer`
scores copy against CHEETAH and rewrites the weak parts. If the user hands you
something written and asks how good it is, that is the one they want. If they hand
you something written and ask you to *improve* it, score it there first: the score
is what justifies the rewrite, and it comes back with the findings you would rebuild
from.

---

## Naming a skill from another plugin

`/utm-generator`, `/image-cropper`, `/image-compressor` and `/qr-code-generator` live in the
**Knak Marketing Operations** plugin. Whenever you name one — in a next-steps list, in an
open question, in a table cell, anywhere — give the plugin and the way to get it in the same
breath, so the suggestion can be acted on the moment it is read:

> `/utm-generator` is in the **Knak Marketing Operations** plugin — add it from
> **Plugins → Discover** and search for **Knak**.

## Working folder

Files this skill saves — `email-brief-config.md` and `brand-guidelines.md` — go **directly into the folder the user connects**. Do not
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

> Before we start: do you want to connect a folder? I'll keep **your sender details and your
> brand voice** there, so the next brief skips those questions entirely — and every brief I
> write lands in that folder.
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
`Email voice guide (2026).md` holds exactly what `brand-guidelines.md` would. List the folder and
match on meaning:

- read the filenames in the connected folder
- match on the words that matter, in any spelling or separator — `brand-guidelines.md`, `brand_guidelines.md` and `our tone of voice.md` are all "the brand voice file"
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

## The framework

Every piece of copy this skill produces is built on the **[CHEETAH Email
Framework](https://knak.com/resources/guides/cheetah/?utm_source=claude&utm_medium=skill&utm_campaign=claude-plugin)** — Captivate, Human,
Entertain, Easy, Transitions, Animate, Harmony, plus the top tip: be Valuable.

**Read `${CLAUDE_PLUGIN_ROOT}/skills/email-brief-generator/references/cheetah-framework.md` before writing or scoring anything.** It
carries the full framework, the rules under each letter, and the scoring rubric.
Don't work from the seven words alone — the substance is in the detail.

---

# Mode 1: Create a brief

## Step 1 — Read what they gave you

Input arrives in every shape. Handle all of them:

- **Voice note or audio** — transcribe and work from the transcript. People ramble in voice notes; that's fine, the point is the raw thinking.
- **A transcript** of a meeting, sales call or webinar — pull out the offer, the audience and the promise.
- **Bullet points or a pasted paragraph** — the normal case.
- **URLs** — fetch them, always, and write the copy against what the page actually says. A webinar registration page or blog post usually contains the offer, the date, the speakers and the value proposition. Reading the destination first is what keeps the email and the page telling the same story, so there is nothing to reconcile afterwards.

  **Strip the tracking off any link you lift out of source material.** A CTA copied from a
  blog post, a press release or a partner's page usually carries *their* tracking — `utm_*`,
  `gclid`, `fbclid`, `mc_cid`, `li_fat_id`, or a parameter private to whatever site you took
  it from.
  Ship those and the campaign reports as the other company's traffic, or as nothing at all.
  Put the bare URL in the brief, keep everything before the `?` plus any parameter the page
  genuinely needs to work, and note that tagging comes from `/utm-generator` in the **Knak
  Marketing Operations** plugin.
- **Images or screenshots** — read them directly. A slide, a poster, a past email.
- **Documents** — read them.

Extract everything you can before asking anything. Most of the required fields are
usually already in there.

## Step 2 — Check for saved defaults

Look in the connected folder, the working folder, and anything the user attached for a file
holding sender defaults — from-name, from-email, reply-to, brand voice, usual audiences.
**Match on what a file is, not what it's called:** this skill writes `email-brief-config.md`, but
a team's own `Email Defaults.md` or `sender-details.md` does the same job. List what's there,
read the names and opening lines, and use the first thing that plainly fits. If it exists, read
it — those questions are already answered. Mention it in passing
("Using the sender details in `email-brief-config.md`") and don't re-ask.

If there's no config file, you'll write one at the end of this run (Step 7).

**Brand voice lives in `brand-guidelines.md`, not here.** It is shared with `email-scorer`, so
a phrase banned there is avoided in the copy and caught in the score. Read it if it exists.

**If it doesn't, ask for it in the same message as everything else in Step 3 — never as a
separate question, and never only when a folder happens to be connected.** Brand voice is the
difference between copy that sounds like the company and copy that sounds like a language
model, so it is worth more than most of the fields in that table. Asking for it on its own
turns one message into two; asking for it only when a folder exists means most people are
never asked at all.

**Both files get written on every run, folder or no folder.** `email-brief-config.md` and
`brand-guidelines.md` are the whole reason the second brief is faster than the first. With a
folder they are saved into it; without one they are handed over as downloads with a line
saying what they're for. Producing them is what gives the user something to keep and a way to
skip the questions next time. They belong in the user's own folder or in their hands — a
plugin update replaces the contents of `${CLAUDE_PLUGIN_ROOT}` wholesale, so anything written
there is gone at the next update.

## Step 3 — Ask for what's genuinely missing

These are the required fields:

| Field | Notes |
|---|---|
| **Direction** — what the email is about | Bullets, URLs, images, transcript, voice note. Whatever they've got |
| **Goal** | The one action: webinar registrations, demo requests, sign-ups, downloads, replies, event attendance. Also: how will they know it worked? |
| **Audience** | Who, and what they already know about the sender |
| **Target send date** | Needed for the timing check and the sequence suggestion |
| **From name** | A person performs better than a company — say so if they give a team name |
| **From email** | |
| **Reply-to email** | Often the same as from; offer that as the default |
| **Brand voice** | Only when `brand-guidelines.md` isn't already there. A tone-of-voice guide, a messaging framework, or a couple of emails they like — or two lines describing how they want to sound and anything they never say |

Also useful, worth asking for in the same breath: the **destination URL** (so the
copy can be written against the page people will actually land on), and whether
this is a **one-off or part of a sequence**.

**Ask for all the gaps in one message.** A field-by-field interrogation is the
fastest way to make a skill feel unusable. List what you already worked out from
their input, then list only what's missing.

**Write the questions out as an ordinary message. Do not use the multiple-choice
question tool for this step.** Every answer here is something only the user can supply
in their own words — an email address, a date, a URL, a description of how the brand
should sound — and several of them arrive as an attachment or a connected folder rather
than as text at all. A picker can't carry any of that. Offered one, the user gets
options like *"I'll describe it / upload something"*, which is a button that means
"let me type instead": a whole extra round trip to get back to where a plain message
would have started. Print the list, let them reply once with everything, and let them
attach the folder and the voice guide in that same reply.

> Here's what I've got from your note: goal is webinar registrations, audience is
> marketing ops leads who already know you, sending the week of the 14th.
>
> Four things I still need — send them all in one reply:
> 1. From name and from email (reply-to too, if it's different)
> 2. Exact target send date
> 3. The registration page URL, if it exists yet
> 4. **Your brand voice** — upload a tone-of-voice guide, a messaging framework, or a
>    couple of emails you're happy with and I'll pull the rules out. Or just tell me in
>    two lines how you want to sound and anything you never say.

**Keep the brand voice item bolded and last.** It is the one that needs a beat of thought
rather than a fact off a form, so give it the position and the weight that earn it a
moment's attention. If they
answer everything else and ignore it, write the brief without a voice section and say so
plainly — better than guessing at a register they never agreed to.

If a field is missing and they're clearly not available to answer — a scheduled run,
an unattended session — make a sensible assumption, **state it at the top of the
brief**, and carry on. A brief with a flagged assumption beats no brief.

## Step 4 — Write the copy against CHEETAH

Now write **one** subject line, one preview text and one body — the version you'd
send. Not three of each: a first brief with nine pieces of copy in it is a
sorting exercise before it's a brief, and most of it gets discarded unread.
Variants are offered after delivery (Step 8) for the sends that actually warrant
a test.

The rules that matter most, from `${CLAUDE_PLUGIN_ROOT}/skills/email-brief-generator/references/cheetah-framework.md`:

- **Subject lines** must be actionable and specific. Keep them under ~45 characters where possible — that's where mobile inboxes truncate. Consider one deliberate emoji.
- **Preview text** extends the subject line, never repeats it. Hard limit: under 100 characters.
- **Body** — one goal, one CTA, repeated. Reader-focused: every claim passes the "and therefore, for you…" test. Written as a 1-to-1 message to one real person, not a broadcast. Short sentences, scannable, generous white space.

Show the character count on the subject line and preview text, since both have
limits worth seeing.

## Step 5 — Specify the design, not just the words

A brief that's only copy can't deliver **Transitions** or **Animate** — those are
design instructions. Fill the asset checklist in the template:

- Hero image: what it shows, dimensions, dark-mode behaviour, **and drafted alt text**
- Section transitions: name something other than a plain horizontal rule — curved divider, angled break, colour block running behind two sections
- Animation: what animates, why it's subtle, a meaningful static first frame, target file size under about 1MB
- Every outbound link that needs UTM tagging
- Footer requirements: unsubscribe, physical mailing address, preference centre

## Step 6 — Run the checks

One check, which goes in the brief.

**Timing and sequence.** Is the target send date a strong slot? (Monday morning and
Friday afternoon are the weakest for B2B.) Is there enough runway — copy approval,
design, build, QA and a test send usually need 5–7 working days? And propose the
full sequence the goal actually implies: a webinar is invite → reminder → last
chance → recording follow-up, not one email. Say plainly if they've asked for one
email where the goal needs three.

## Step 7 — Deliver

Build the brief from `${CLAUDE_PLUGIN_ROOT}/skills/email-brief-generator/references/brief-template.md` and
write it into the folder as `email-brief-<campaign-slug>-<YYYY-MM-DD>.md`. That write is the
delivery — hand it over as a download only when there is no folder to write to.

In the chat, show the useful part — the subject line, preview text and body — and
point at the file for the rest. Don't paste the whole brief into the conversation.

Then say, in one line, what built it:

> Content generated using the [CHEETAH Email Framework](https://knak.com/resources/guides/cheetah/?utm_source=claude&utm_medium=skill&utm_campaign=claude-plugin)
> — Knak's seven checks for emails that actually get opened and clicked.

**Write or update `email-brief-config.md`** so the next run asks less:

```markdown
# Email brief defaults
<!-- Written by email-brief on YYYY-MM-DD. Edit anytime, or say "update my email brief defaults". -->

- from_name: <name>
- from_email: <email>
- reply_to: <email>
- typical_audiences: <short list>
- usual_goals: <short list>
- notes: <anything they corrected you on, so you don't repeat it>
```

**Write `email-brief-config.md` and `brand-guidelines.md` every run, whether or not a folder
is connected.** With a folder, save them into it and say so in a few words. Without one, hand
them over alongside the brief and put the offer in the present tense — a folder attached
*now* still catches them:

> I've also made two small files — your sender details and your brand voice. **Attach a
> folder now and I'll save them there for next time**, and future briefs will skip those
> questions entirely. Otherwise just download them and send them back to me on your next run.

Frame it as the open offer it is. The files exist either way and a folder is one click
away, so the message to land is *"here they are, and I can keep them for you"*.

## Step 8 — Offer the extras, once

The brief is the deliverable. Two things are genuinely useful but bury it if they
arrive uninvited, so offer them **after** it has been handed over, in one message:

> Two optional add-ons if they'd help:
>
> - **A/B variants** — three subject lines and preview texts, or three versions of
>   the body, each testing a different angle with a hypothesis attached
> - **A CHEETAH scorecard** — all eight criteria scored with the reasoning, via
>   `/email-scorer`

**Write these as two bullets on their own lines, and stop there.** Run together as a
sentence they read as an afterthought and get skipped, which is the opposite of the
point. Anything about other skills belongs in the next section, in its own paragraph —
don't append it here.

**If they want variants**, ask which layer they want to test — subject and preview, or
body — and do one, not both. Make the three test different things; variants that differ
at random aren't a test, they're three options. Give each a hypothesis: curiosity vs.
plain benefit, urgency vs. evergreen value, question vs. statement, social proof vs.
self-claim, specific number vs. general promise. For body variants the axes are
different — lead with the problem vs. lead with the outcome, short vs. detailed, one
proof point vs. three — but the discipline is the same. Label the hypothesis, show the
character count on subject lines, and say which you'd send and why.

**One layer per send.** Testing subject A/B *and* body A/B at once makes the result
unattributable — say so when they ask for both, and offer to run the second test on the
next send.

**If they want the scorecard**, that is `/email-scorer` — hand it the brief you
just wrote. Don't score it here: the rubric and the rewrite discipline live there,
and two copies of the same scoring would drift apart.

Note as you hand over that the brief was written against CHEETAH in the first place,
so a high score is expected and the useful part is any criterion that still comes
back weak — usually Entertain on a conservative brand, or Harmony when the landing
page is not built yet.

## Next steps

Mention these once, at the end, and only the ones that are actually relevant to what
just happened.

**In this plugin:**

- **`/email-scorer`** — scores this brief against CHEETAH and rewrites what's weak. Offered in Step 8; mention it here only if they skipped that.

**From the Knak Marketing Operations plugin** — name it and say how to get it (add it from **Plugins → Discover** and search for **Knak**), so the suggestion is actionable as read:

- **`/utm-generator`** — in the **Knak Marketing Operations** plugin. The brief lists every link that needs tagging. It builds the tagged URLs to your team's naming conventions, so tracking stays consistent across the campaign.
- **`/image-cropper`** then **`/image-compressor`** — both in the **Knak Marketing Operations** plugin. The hero image, the transition graphic and the GIF all need to fit their slots and stay light enough not to clip in Gmail. The cropper shapes them, the compressor shrinks them and drafts alt text. Crop first: compressing first bakes in quality loss that cropping then throws away.

The natural order is: brief (here) → score → UTMs → crop and compress the images → build → send.

---

## Edge cases

- **A voice note that rambles and never states the goal** — infer the most likely goal, state your inference in one line at the top, and write the brief. Don't send them back to re-record.
- **The direction is a single URL and nothing else** — fetch it, extract offer, audience and date, write the brief, and flag every field you inferred.
- **The audience is "everyone"** — push back once, gently. An email for everyone captivates no one. Ask for the single most valuable segment, then write for them.
- **They ask for two CTAs** — write it their way, but score Easy honestly and say in one line what it will cost. Their campaign, their call.
- **The send date is in three days** — say it's tight and what will realistically get cut (usually QA and a proper test render). Offer a stripped-down single-variant version that can actually be built in time.
- **The brand can't do ENTERTAIN** — regulated industry, conservative buyer, internal comms. Score it Weak with the constraint named, and find the value elsewhere: clarity, brevity, respect for the reader's time.
- **The destination page doesn't exist yet** — say so in a line and list what the page must carry to match the email, so whoever builds it has the spec.
- **They want the brief in a different format** — a doc, a slide, a table for a project tool. The markdown file is the default, not a rule. Produce what they'll actually use.
