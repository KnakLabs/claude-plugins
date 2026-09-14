---
name: newsletter-content-sourcer
description: >
  Put your newsletter drafting on autopilot: scans your chosen sources for what's worth covering, matches the tone and structure of your past editions, and hands you a finished draft ready to build. Go from blank page to build-ready draft in minutes.

  Triggers on requests to create, build, draft, or prepare a newsletter — including "build this month's newsletter", "draft the newsletter", "it's newsletter time", "what should go in the newsletter", "prepare the next edition", "curate content for our newsletter", or any mention of a named recurring newsletter alongside words like new, next, monthly, weekly, build, create, draft, or prepare.
metadata:
  version: "2.0.0"
---

# Newsletter content sourcer

Take a recurring newsletter from blank page to finished draft: gather the sources worth watching, surface what's new, and shape the topics the user picks into their newsletter format.

The skill runs in four tiers. Each tier writes what it learns to a file so it is only ever asked once. Always check for those files before asking anything.

| File | Written in | Purpose |
|---|---|---|
| `newsletter-sources.md` | Tier 1 | Where newsletter content comes from, plus cadence and audience |
| `newsletter-template.md` / `.html` | Tier 3 | Newsletter format, tone, and section structure |
| `newsletter-past-editions.md` | Tier 3 | Which topics each past edition covered, so nothing is repeated |

The skill runs in four tiers, and each is useful on its own. A run that stops after Tier 2 still tells the user what is worth covering; a run that finishes Tier 3 hands them a formatted draft they can paste anywhere; Tier 4 finds the images to go in it and is entirely optional.

## Naming a skill from another plugin

`/utm-generator`, `/image-cropper`, `/image-compressor` and `/qr-code-generator` live in the
**Knak Marketing Operations** plugin. Whenever you name one — in a next-steps list, in an
open question, in a table cell, anywhere — give the plugin and the way to get it in the same
breath, so the suggestion can be acted on the moment it is read:

> `/utm-generator` is in the **Knak Marketing Operations** plugin — add it from
> **Plugins → Discover** and search for **Knak**.

## Working folder

Files this skill saves — `newsletter-sources.md`, `newsletter-template.md`, `newsletter-past-editions.md` — go **directly into the folder the user connects**. Do not
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

> Before we start: do you want to connect a folder? I'll keep **your source list, your
> newsletter's format, and a record of what past editions covered** there — so I stop asking
> where your content comes from, stop asking what your newsletter looks like, and stop
> suggesting topics you have already run. The draft and its images land there too.
>
> Use the **Add folder** button and either point me at the folder you keep this work in, or
> create a new one. Then tell me and I'll pick it up.

**On a first run, put this at the top of the Tier 1 sources message rather than sending it
on its own.** Both questions want the same single reply, and asking them together lets
someone attach the folder and list their sources in one go. Send the folder ask by itself
only when `newsletter-sources.md` already exists and Tier 1 has nothing to ask.

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
`Newsletter format (2026).md` holds exactly what `newsletter-template.md` would. List the folder and
match on meaning:

- read the filenames in the connected folder
- match on the words that matter, in any spelling or separator — `newsletter-template.md`, `newsletter_template.md` and `our newsletter format.md` are all "the template file"
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

## Working principle: produce, then let them correct

Where something is uncertain — the format inferred from a screenshot, how long the teasers should run, which section a topic belongs in, what a button should say — make the call, produce the thing, and show it. Do not stop to check assumptions before doing the work. It is far easier for the user to react to a real draft than to answer an abstract question about structure, and every pre-emptive check makes the skill feel like an interview.

When you've made a judgement call the user might disagree with, say so in a line alongside the output ("I read four sections off the screenshots and kept teasers to about two sentences") so they know what to push back on. Then let them correct it.

The places to genuinely stop and wait are: choosing which topics to cover (Tier 2), approving the finished draft (Tier 3), and asking whether images are wanted before sourcing any (Tier 4). Everything else: decide, produce, show.

---

## Where files are saved — read this first

The config files above are only worth writing if the user can find them again next month. Resolve the save location **before** writing anything, and tell the user where it is.

1. **If a project or working folder is connected to the session** (the user has attached a folder), that folder is the home for all the config files. List it, read any config files already there, and write new ones back to it.

   **Match on intent, not filename.** The names in the table above are what this skill writes, not what it should search for. A file called `Newsletter Format.md` is the template; `Content Sources.md` is the sources file; last month's `.html` export is a past edition. Read the names and, where cheap, the opening lines, and work out what each file *is*. Say which file you used for what. If two plausibly fill the same role, ask rather than picking silently. This is the best case — the files persist between sessions, so the skill genuinely stops asking.
2. **If no folder is connected, ask for one before going any further.** The session's own workspace is temporary — anything written there vanishes when the session ends, which means every future run starts from scratch. So ask:

   > Before we start: I'll save a few small context files as we go — your content sources and your newsletter format — so I never have to ask you for them twice. Where should they live?
   >
   > Use the **Add folder** button and either:
   > - **point me at the folder you already keep newsletter work in**, or
   > - **create a new folder** (something like *Newsletter*) just for this.
   >
   > Then tell me and I'll pick it up.

   Wait for them to connect it, then confirm what you can see in it and carry on.

3. **Only if they decline or can't connect a folder**, fall back: write the files to the session workspace for this run, deliver every config file to them as a download (not just the newsletter draft), and say plainly — *"These are the files that stop me asking the same questions next time. Keep them somewhere and attach them when you next run this, or connect a folder and I'll manage them for you."*

Whichever path you're on, **name the location explicitly** the first time you write a file — "Saved `newsletter-sources.md` to your *Newsletter* folder" or "Here are your context files to keep." Never write a file and say nothing about where it went.

At the end of every run, list the files produced and where each one is. That includes the newsletter draft itself.

**Never write any of these into `${CLAUDE_PLUGIN_ROOT}`.** A plugin update replaces the plugin directory wholesale — every file, not just changed ones — so a template or coverage log saved there is destroyed at the next update, which is the whole point of keeping them in the user's own folder.

---

## Tier 1: Sources

**First, look for `newsletter-sources.md`** (in the connected folder, or attached by the user). If it exists and has content, read it and skip straight to Tier 2. Only mention it in passing (e.g. "Using the sources in `newsletter-sources.md` — tell me if you want to add any.").

If it does not exist, print the list of ideas below in full, then ask the user to reply with everything they want watched in a single message. Do not ask these one at a time.

**Open this message with the folder ask when no folder is connected** — the wording is under
[Working folder](#working-folder) above. One message, one reply: they attach the folder and
answer the sources question together.

> **Where should I look for content?** Send me whatever applies — links, names, or folder names — all in one message and I'll save it so you never have to answer this again:
>
> - **Your own blog or resources page** — usually the primary source; the newsletter exists to drive traffic to it
> - **Your company LinkedIn page** — announcements and posts that never became blog posts
> - **Competitor blogs or LinkedIn profiles** — what the rest of your category is publishing and posting
> - **A Gmail label or folder where competitor newsletters land** — the fastest way to see what others are covering (tell me the label name and I'll read it)
> - **Release notes or changelogs** of the platforms you work with — product changes your readers need to know about
> - **Blogs and forums from adjacent communities** — user groups, associations, partner companies
> - **LinkedIn profiles of influencers or influential companies** in your space
> - **Industry events and conference calendars** — timely hooks that age fast, so worth flagging early
> - **Anything else** — podcasts, YouTube channels, subreddits, Slack communities, an internal Notion page of story ideas

In the same message, also ask for two things: the newsletter's **cadence** (weekly, monthly, quarterly) and its **audience** in one line. Both get saved. Don't ask for the newsletter's name — Tier 3 finds it from a past edition.

When the reply comes back, write `newsletter-sources.md` to the resolved save location:

```markdown
# Newsletter sources
<!-- Written by newsletter-content-sourcer on YYYY-MM-DD. Edit anytime or say "update my newsletter sources". -->

- cadence: <weekly | monthly | quarterly | ad hoc>
- audience: <one line>

## Primary (own content)
- <label>: <URL>

## Secondary (industry / competitor)
- <label>: <URL, Gmail label, or connector + location>

## Notes
- <anything the user said about priorities, topics to avoid, etc.>
```

For each source, record **how** it is reached — a URL to fetch, a Gmail label to search, a Notion page, a LinkedIn page — so future runs don't have to re-discover it.

If a source needs a tool that isn't connected (Gmail for a newsletter label, Notion for an idea page), search the connector registry and suggest the connector so the user can connect it in one click. Record it in `newsletter-sources.md` regardless; a source that can't be read this run is still worth keeping.

---

## Tier 2: Surface the topics

Read `newsletter-past-editions.md` first if it exists, so you can tell a genuinely new topic from one that already ran. Then work through the sources in `newsletter-sources.md` in parallel and find everything published since the last edition (use the cadence to set the window). For each item, capture the title, URL, date, and why a reader would care.

Guidance by source type:

- **Own blog / resources** — everything new. These are the primary candidates, since the newsletter exists partly to drive traffic to them.
- **Gmail label of competitor newsletters** — search the label over the period and read the recent ones. Note recurring themes and anything the user's own newsletter hasn't touched. This is usually the highest-signal source and the one most often skipped.
- **LinkedIn** — pages frequently block scraping. Try web search first (`site:linkedin.com "<company>" <year>`). If that comes back thin and LinkedIn matters to this newsletter, offer the browser: ask the user to sign in to LinkedIn in Chrome, then use the browser tools to open the company page or profile and read the recent posts directly. Only offer this once; if they decline, move on.
- **Release notes / changelogs** — look for changes that affect the reader's day-to-day, not every minor fix.
- **Events** — check what's imminent. Event-tied content ages fastest, so flag the deadline.

### Competitor sources are for intelligence only — never for promotion

Competitor blogs, LinkedIn profiles, and newsletters are read to understand **what the market is talking about**: which themes are getting attention, which questions readers clearly have, and which angles nobody has covered well. That's it.

Never, under any circumstances:

- link to a competitor's blog post, landing page, webinar, or resource
- name or describe a competitor's product, feature, release, or announcement as newsletter content
- recommend, praise, or quote a competitor
- frame a topic in a way that sends the reader to a competitor to learn more

Instead, take the **underlying topic** and cover it from the user's own perspective, linking to the user's own content. If a competitor's post reveals a topic the user's audience clearly cares about and the user has nothing published on it, surface it in Tier 2 as a **content gap** — flagged as "worth writing" — rather than as something to feature this edition.

Industry news, platform release notes, events, and community content are different and can be linked freely. The rule is about competitors specifically. If it's ambiguous whether a source counts as a competitor, ask the user rather than guessing.

### Output of this tier

Present the findings as **broad topic coverage, not a laid-out newsletter**. One short paragraph per topic, in rough order of how strong the candidate looks. Each paragraph should carry: what the topic is, why it's relevant to this audience right now, and the source link. No section labels, no button copy, no subject lines, no fixed count — surface everything credible you found, even if it's more than an edition can hold.

Make clear they can pick a subset or take all of them, tell you to go deeper on one, add a topic you didn't find, name one to lead with, or hold one for a future edition.

### Close with a hand-off into Tier 3

End the message with a single ask that rolls the topic choice and the next step together. **Check for `newsletter-template.md` / `.html` first** — the wording depends on whether you already know the format:

**First run (no template file yet)** — the ask has to cover the format too, so lead with it:

> Those are the topics worth covering. Tell me which ones you want in (or say "all of them"), and I'll need to know what your newsletter looks like so I can draft it in your format — options below.

Then print the format options and let them answer both in one message.

**Later runs (template file exists)** — you already know the format, so don't mention it:

> Those are the topics worth covering. Want me to draft the newsletter from these? Let me know if there are any you definitely want in, or any to leave out — otherwise I'll pick the strongest ones and you can move things around when you see the draft.

Don't shape anything into newsletter format until they've answered.

---

## Tier 3: Shape the chosen topics into the newsletter format

Now that the topics are agreed, work out what the newsletter is supposed to look like.

**Look in the connected folder before asking for anything.** Beyond `newsletter-template.md` / `.html` and `newsletter-past-editions.md`, check for any past newsletter the user has already put there — an `.html` export, a screenshot, a PDF, a saved email. People drop last month's edition into the folder precisely so you'll use it. If you find one, read it, say which file you used, and go straight to drafting. **HTML is a format reference.** Read the section order, the copy lengths, the button wording and the markup structure out of it, and write the edition as markdown.

Only if the folder has nothing usable, print the format options (this is the block Tier 2's first-run hand-off promised):

> Here's how I can pick up your newsletter's format — any one of these works:
>
> 1. **Paste or upload the HTML** of your most recent newsletter — a one-time read is enough, and it gives me the most exact picture of your structure and copy lengths.
> 2. **Upload images or screenshots** of your last newsletter — a full-length screenshot, a PDF, or a few screenshots stitching the email together. I can read the layout and copy straight off the picture.
>
> Whichever you pick, I'll save what I learn so I won't ask again.

**If they paste or upload HTML:** read it and extract the same things.

**If they upload images, screenshots, or a PDF:** read them directly — you can see them. Pull out the section order and count, the heading style and length, roughly how long the teaser copy runs, the button labels and their wording style, and the tone of the subject line if it's visible in the screenshot. Note the visual structure too (single column, side-by-side blocks, dividers between sections) since that shapes how much copy each section needs.

If several screenshots cover one email, treat them as a single edition top to bottom rather than separate newsletters — assume the order they were uploaded in and say what you assumed. If part of a screenshot is cut off or too low-resolution to read, make your best guess at that section, flag which bit you couldn't make out, and keep going.

Don't stop to get your read of the format signed off. Draft the newsletter against what you inferred, show it, and note in a line or two what you took from the screenshots ("looks like four sections, short teasers, buttons reading 'Read more'") so the user can correct anything you got wrong when they see it in context.

**If they'd rather skip:** shape the content into a sensible newsletter structure of your own choosing, sized to the number of topics they picked, and don't ask again this session.

### Write the template file

Save to the resolved save location — `newsletter-template.html` if you have real HTML worth keeping verbatim, otherwise `newsletter-template.md`:

```markdown
# Newsletter template
<!-- Written by newsletter-content-sourcer on YYYY-MM-DD. Source: <uploaded HTML | uploaded screenshots>. -->

- newsletter_name: <name, if found>

## Structure
1. <section> — <purpose, typical length>
...

## Voice and tone
- <observations, with a real example line or two>

## Subject line style
- <examples from past editions>

## Button labels used
- <examples>
```

### Write the past-coverage file

`newsletter-past-editions.md` goes to the same save location and is the running record of what has already gone out. Keep it out of the template file: the template describes a format that barely changes, while this grows by a row every run — mixing the two means re-reading the whole format spec just to check whether a topic is a repeat, and it makes the template harder to hand to someone as a format reference.

```markdown
# Previous newsletter content
<!-- Maintained by newsletter-content-sourcer. Append one row per edition; never rewrite history. -->

| Edition | Date | Topics |
|---|---|---|
| <name or number> | YYYY-MM-DD | <topic>; <topic>; <topic> |
```

Seed it with every edition you read while inferring the format — if you read three past editions, all three get rows, not just the most recent.

This file is the most valuable thing the skill accumulates, so **append to it at the end of every run**, even when the edition is never built anywhere. A run that stops after the draft still produced an edition.

If a topic the user chose in Tier 2 turns out to be covered in a recent edition, don't halt — draft it with a fresh angle if there is one, or leave it out and say which edition already covered it, so they can overrule you when they see the draft.

### Produce the draft

Map the chosen topics onto the structure you found: assign each one to a section, write the headings, the teaser copy at the length past editions use, the button labels in the newsletter's own style, and the destination URLs.

**Strip the tracking off every destination URL.** Links lifted from a post, a partner page or someone's share often carry that site's own parameters — `utm_*`, `gclid`, `fbclid`, `mc_cid`, or a vendor's private ones. Left in, the edition reports as somebody else's traffic. Keep everything before the `?` plus any parameter the page needs to work, and leave tagging to `/utm-generator` in the **Knak Marketing Operations** plugin. Say which links you cleaned. If there are more approved topics than the structure comfortably holds, group the weaker ones into a short round-up section or flag them for the next edition.

Also propose **three subject line options**, matched to the voice of past subject lines in the template file. Say which one you'd send.

Show the full draft section by section and get approval.

---

## Tier 4: Images

**Only after the draft is approved.** Sourcing images for topics that then get cut
is wasted work, and it is the slowest part of the run.

Ask first — some teams drop images in themselves, and the offer is one line:

> Want me to find images for this edition? I'll pull them from the posts you're
> linking to, save them to your folder and show you each one, then work out what size
> each slot needs and write the alt text.

If they say no, stop here and go to delivery.

### 1. Work out what size each slot needs

**If you have the HTML, it already answers this** — read it rather than asking. Two
places carry the size:

- **The `width` and `height` attributes** on the `<img>` tags, which are what the
  email client actually honours
- **The filenames** of whatever is in there now — `hero-600x300.jpg` is telling you
  exactly what fits

If the template has one and not the other, trust the `width` attribute. If it has
neither, take the width of the containing table or cell.

**If there is no HTML** — the format came from screenshots, or the template step was
skipped — you have to ask, but don't ask cold. Most email templates are 600px wide,
so propose that and let them correct it:

> I don't have the HTML, so I'll size the images for a 600px-wide template: 600×300
> for the hero, 280×180 for the smaller ones. If your template is a different width,
> tell me and I'll resize.

A screenshot gets you closer than nothing: measure the image against the full width
of the email in the screenshot and apply that proportion to whatever width they
confirm. Say that's what you did, since it's an estimate.

Record the sizes you settle on in `newsletter-template.md`, so the next edition
doesn't ask again.

**Every slot wants double.** A slot displaying at 600px wants a 1200px image
held to 600 by the `width` attribute, or it looks soft on any modern screen. Quote
the doubled number as the target size — the `width` attribute does the
constraining, not the file.

### 2. Find the images

Work down this ladder and stop at the first rung that works. Say which one you
used, because it tells the user how solid the image is.

1. **The image URL itself.** Fetch it directly. Image files sit on a CDN path that
   outlives the page they were on — a post URL that now redirects will usually
   still have a working image URL from when you first read it. This is the rung
   that works most often and nobody tries first.
2. **The live post.** Read the page and take the `og:image`, or the first
   in-content image.
3. **The site's feed**, when the post redirects and you no longer have the image
   URL. `/feed/` or `/rss/` on a WordPress site lists recent posts with their
   images embedded in `<content:encoded>` — parse the `<img src>` out of that HTML
   rather than looking for a `<media:content>` tag, which most feeds don't set.

   **Its reach is a post count, not a date.** A feed carries roughly the last ten
   posts, so a blog posting monthly gives you a year and one posting weekly gives
   you ten weeks. If the post is older than that window it will not be there, and
   no amount of retrying changes that.

   **Plenty of sites have no feed at all.** Anything on Vercel, Webflow or a
   headless CMS usually 404s on `/feed/`. Check `/sitemap.xml` instead, which those
   sites almost always have.
4. **Screenshot it.** When nothing can be downloaded, open the page in the browser
   and screenshot the image. Say you did — a screenshot is lower quality than the
   original and the user may prefer to supply their own.

If a topic ends up with no usable image, say which one and leave the slot as it is.
Don't substitute something unrelated to fill a hole.

### 3. Download them, save them, show them

**A URL is not an image.** Download every one you found and write it into the folder as a
real file, named for what it is — `ai-agents-hero.jpg`, not `image1.jpg` and not whatever
the CDN called it. Keep the original at full size; sizing comes later.

**Then show them, without being asked.** Display every image you downloaded so the user can
see what they are getting. This is part of the job, not an offer to make — a filename and a
source URL tell someone nothing about whether the picture is any good, and the wrong image
found early is cheap to replace and expensive to discover at build time. Where an image can
only be shown by downloading it first, download it.

Show them in slot order, each labelled with the slot it is for, and name any slot that came
up empty in the same list rather than leaving a silent gap.

Seeing them is also what makes the rest of this tier possible: alt text written off a
filename is a guess, and you cannot say whether an image suits its slot without looking
at it.

### 4. Write the alt text

Now that you can see each image, write one line per image, describing what is in it for
someone who cannot see it. Write
what the picture shows and why it is there — "inbox placement dashboard showing a
rising delivery rate" rather than "chart" or "image of a dashboard". Decorative
dividers and spacers take an empty `alt` attribute instead.

### 5. Hand over the files and say where they go

**Every image ships as a real PNG or JPEG file. Never base64, never a local path.**
A `data:` URI is stripped by Gmail, does not render in Outlook, and pushes the HTML
toward the 102KB size at which Gmail clips the message. A local path resolves to
nothing on anyone else's machine. Both look fine in a preview and fail on send,
which is the worst way for something to break.

The files are already in their folder from step 3. What remains is uploading them to the
user's marketing automation platform or CDN and swapping the `src`. Make that mechanical
rather than a puzzle — give them a table:

| File | Replaces the `src` in | Target size | Alt text |
|---|---|---|---|
| `ai-agents-hero.jpg` | first `<img>` in the hero block | 1200×600, displays at 600×300 | Marketer reviewing an AI-drafted email on a laptop |
| `deliverability-thumb.jpg` | `<img>` in section 2 | 560×360, displays at 280×180 | Inbox placement dashboard showing a rising delivery rate |

And say it in a line: *"Upload these to your platform, then swap each `src` for the
uploaded URL. The `width` and `height` attributes already in the template are
correct — leave them alone."*

## Deliver the files

Produce the files and hand them over. Don't ask whether they want them; they asked for a newsletter, so give them one:

- **The markdown file**, always. Section by section, ready to paste into a builder or circulate for review. Name it `<newsletter-name>-<month>-<year>.md`.
- **The image files and their table**, whenever Tier 4 ran.

Write the markdown so it maps onto the template one section at a time — the same
section order, the same headings, the same button labels — so whoever builds the
edition can work straight down it.

**Send the files into the chat with SendUserFile as well as writing them to the folder.** The folder is where they live afterwards; the chat is where the user is now.

**Also append this edition to `newsletter-past-editions.md`** — one row, topics separated by semicolons. Do this as part of delivery, so the record stays complete on every run.

## Next steps: the Knak Marketing Operations plugin

These are separate skills in a separate plugin. Mention them once, after the draft has been
delivered, and only the ones that actually apply to what just happened. Name the plugin and
say how to get it (add it from **Plugins → Discover** and search for **Knak**), so the suggestion is actionable as read.

- **`/utm-generator`** — in the **Knak Marketing Operations** plugin. Every link in the edition needs tagging, and they all need the *same*
  `utm_campaign` or the edition splits into several rows in reporting. It builds them from the
  team's conventions doc in one batch.
- **`/image-cropper`** then **`/image-compressor`** — both in the **Knak Marketing Operations** plugin. The images sourced in Tier 4 come through
  at whatever size they were published at. The cropper fits them to the slot, the compressor
  gets them under the weight an email can carry. Crop first: compressing first bakes in quality
  loss that cropping then throws away.

The natural order is: source the content and its images (here) → UTMs → crop and compress the images → build the edition → send.

Don't offer UTM generation before the topics are locked — the campaign name depends on the
edition, so tagging early just means doing it twice.

## Edge cases

- **Nothing new published since the last edition** — lean on industry news, event coverage, or resurface a strong older post. Ask whether anything is about to publish that's worth waiting for.
- **The user picks a topic that has no matching page** — write the copy anyway and either link to the closest relevant page or note that no link exists yet.
- **The user picks more topics than an edition holds** — say so, propose which to hold for next time, and let them decide.
- **LinkedIn won't load** — expected. Try web search, then offer the sign-in-and-browse route once, then move on.
- **A source in `newsletter-sources.md` can't be reached** (dead URL, connector disconnected) — say so plainly, carry on with the rest, and ask whether to update or drop it from the file.
- **Screenshots are cut off, blurry, or out of order** — do your best with what's legible, draft anyway, and flag the section you couldn't read so the user can fix it or send a better shot. Don't halt the run over it.
- **The user wants a newsletter now, with no patience for source setup** — offer to run once from just their blog URL, then suggest full source setup afterwards so the next run is better.
- **The strongest topic found is a competitor's announcement** — don't feature it. Cover the underlying theme from the user's own angle, or log it as a content gap. Say clearly why you didn't include the competitor link.
- **No folder is connected to the session** — ask them to add one before starting: their existing newsletter folder, or a new one created for this. Only if they decline should you fall back to delivering the context files as downloads for them to keep.
