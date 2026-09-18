---
name: qr-code-generator
description: >
  Generate logo-embedded QR codes in your brand colors: feed it a batch of landing page URLs and get back one QR code per URL, all generated at once and named to match their corresponding landing page.

  Triggers on asking to make a QR code, wanting a QR code with your logo in the middle, wanting QR codes in your brand colors, mentioning "QR Code Monkey" or a similar generator, or giving a list of URLs (e.g. landing pages, event pages, blog posts) that each need their own QR code. Also triggers if you're preparing print materials, event signage, business cards, or packaging and need scannable codes generated.
---

# QR Code Generator

Generate scannable, on-brand QR codes for one or more URLs, each with a logo image dropped in the center — the same idea as QR Code Monkey, but run locally via a bundled Python script so there's no third-party site involved.

## Working folder

Files this skill saves — `qr-config.md`, your logo file, and the codes it generates — go **directly into the folder the user connects**. Do not
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

> Before we start: do you want to connect a folder? I'll keep **your logo file and your
> brand colours** there, so next time you won't have to upload the logo or tell me the
> colours again — and every code I generate lands in that folder instead of a download
> you have to go and find.
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
`Brand colours (2026).md` holds exactly what `qr-config.md` would. List the folder and
match on meaning:

- read the filenames in the connected folder
- match on the words that matter, in any spelling or separator — `qr-config.md`, `qr_config.md` and `our brand colours.md` are all "the QR config file"
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

## Before you ask anything: start the dependency install

This skill's Python packages may not be present — Cowork hands every session a fresh
container, so nothing installed last time survives. **Kick the install off in the
background as your very first action**, then carry straight on with the questions
below while it runs:

**Find the Python interpreter first — one command, and it names what to use for every
script in this skill:**

```bash
PY=""; for c in python3 python; do
  command -v "$c" >/dev/null 2>&1 && "$c" -c "pass" 2>/dev/null && { PY="$c"; break; }
done
[ -n "$PY" ] && echo "python ok: $PY" || echo "python missing"
```

**Use whatever it names wherever this skill writes `python3`.** macOS and Linux generally
answer `python3`; a Windows install from python.org answers `python`.

**On `python missing`, tell the user what fits their machine** — `uname -s` says which
(`Darwin`, `Linux`, or `MINGW`/`MSYS` under Git Bash on Windows):

- **macOS** — Python ships with the OS but needs Apple's developer tools switched on once:

  > Your Mac has Python but hasn't switched it on yet. Run `xcode-select --install` and click
  > through the installer that appears. A few minutes, and it doesn't need your password.

- **Windows** — install from [python.org](https://www.python.org/downloads/), ticking **Add
  python.exe to PATH** on the first screen, or run `winget install Python.Python.3.12`.

- **Linux** — `sudo apt install python3` on Debian and Ubuntu, `sudo dnf install python3` on
  Fedora.

Wait for them, re-run the check, and carry on once it names an interpreter.

Everything in this skill that runs a script needs it, so this is worth the one command.

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/ensure_deps.py qr-code-generator &
```

Don't wait for it, don't mention it, and don't make the user watch it. By the time
they have answered, it has finished. If it fails the scripts still run and degrade
honestly — there is nothing here for the user to fix.

## What this skill needs from the user

Check `qr-config.md` and the working folder first — only ask for what isn't already there. If any
of these is genuinely missing, ask; don't guess or invent it:

0. **A folder to work in** — this belongs in the *same* opening message as the questions below,
   not as a remark after the codes are delivered. By then it has cost the user the setup
   questions it exists to prevent, and the logo they just uploaded is still only in the chat.
   Ask it first, in the wording under [Working folder](#working-folder) above. If they decline,
   carry on and hand everything over as downloads.
1. **URL(s)** — one or a list. Before generating anything, check whether they carry UTM parameters and ask whether they should — see [Tag the URLs first](#tag-the-urls-first) below. Treat this as a gate rather than an aside: unlike a link in an email, the tracking on a printed code cannot be changed afterwards.
2. **Logo/image** — check `qr-config.md`, then whether an image was attached to the conversation, then the working folder, before asking. If nothing is found, ask the user to provide one. A QR code can be generated without a logo (plain code), but only do that if the user explicitly says they don't want one — the whole point of this skill is replicating QR Code Monkey's branded look.
3. **Brand colors** — a foreground (module) color and a background color, as hex codes (e.g. `#1A1A1A` on `#FFFFFF`). Check `qr-config.md` first, then attached brand assets or the working folder for anything that looks like a brand colour reference; otherwise ask — **and offer to read them off the logo rather than making them look the codes up**:

   > What colours should the codes use? Give me the two hex codes — module and background — or
   > say the word and I'll pull them straight out of the logo you just sent.

   If they take the offer, run the script's `--suggest-colors` on the logo. It reports each
   colour with its share of the image and its contrast on white, and recommends a pair that
   will actually scan. Reading the values rather than eyeballing them matters because a brand
   colour that looks strong on a slide is often too light to be read as a QR module.

   **A QR code is read by threshold, not by hue.** Dark modules on a light background is the
   whole mechanism, so a very pale brand colour may be unusable no matter how on-brand it is.
   The script warns when the pair is too close to read; take that warning seriously and offer
   dark modules with the brand colour kept in the logo instead. Where it doesn't warn, the
   colours are fine — hand them over without commentary.

This skill is meant to be shared and used by people outside of any one organization, so always ask rather than assuming a default brand — there's no fallback logo or palette baked in.

**Match the kind of question to the kind of answer.** A multiple-choice question only works
when you can write the answers out in advance — logo or plain, brand colours or black on
white, which of three tagging routes. **A hex code and a logo file are neither**: one is an
arbitrary value and the other is an upload, and pushing them through a choice widget gets you
an unanswerable question and a dead end for the user. Ask for those in plain chat, in one
message, and say what you already have so they only supply the gap:

> I've got the URLs. Two things left: attach your logo (PNG with a transparent background
> works best), and tell me the two hex codes — the module colour and the background, e.g.
> `#1A1A1A` on `#FFFFFF`.

## Tag the URLs first

A QR code is a link that arrives with no referrer, so an untagged one lands in analytics as
Direct traffic — the signage, print run or packaging that carried it looks like it produced
nothing. And this is the one place the mistake is not recoverable: re-tagging means
regenerating every code and reprinting whatever it went on.

So **ask before generating**, whenever a URL in the batch has no UTM parameters and points at
a domain the user owns. **Offer the two ways of getting there as a choice, not a yes/no.** A
bare "want me to add UTM parameters?" gets answered "yes", and yes reads as *you* add them —
so what ships is a guess at the team's conventions rather than the conventions themselves,
printed and unfixable.

> These URLs aren't UTM-tagged, so scans will land in analytics as Direct traffic. Once the
> codes are printed that can't be changed. How do you want to handle it?
>
> 1. **Run `/utm-generator`** — builds the tags from your team's conventions doc, so these
>    match every other link in the campaign. Best if you have one, or want to start one.
> 2. **Use QR defaults** — `utm_source=qr`, `utm_medium=print` (or `offline`), and a campaign
>    name you give me. Quick, and fine when there's no conventions doc to match.
> 3. **Leave them untagged** — scans will report as Direct traffic.

- **`/utm-generator`** → hand off, then generate the codes from the URLs it returns. It applies
  the team's own conventions doc, normalizes casing and separators, and appends correctly to
  URLs that already carry a query string.
- **QR defaults** → append the parameters here, and say plainly what they are: generic values
  that have not been checked against any conventions doc, so they may not match the rest of
  the campaign. Offer `/utm-generator` once more if they later mention a conventions doc.
- **Untagged** → generate from the URLs as given, and don't raise it a second time.

Put this as a multiple-choice question rather than open text, so the three options are visible
side by side and a one-word answer can't land on the wrong one.

Skip the question entirely when the URLs already carry UTMs, or when the destination isn't the
user's own property — a third-party event page, an app store listing — since tagging a domain
they don't measure achieves nothing.

## Why high error correction matters

Placing a logo over the middle of a QR code covers some of its data modules. The script always generates codes at the "H" (highest, ~30% recoverable) error correction level specifically so the code still scans reliably once the logo and its white backing plate are placed on top. Don't lower this — it's what makes the logo overlay technique actually work.

## Running the generator

Use `${CLAUDE_PLUGIN_ROOT}/skills/qr-code-generator/scripts/generate_qr.py`. It takes one or more URLs and produces one PNG per URL, batching everything in a single run:

```bash
python ${CLAUDE_PLUGIN_ROOT}/skills/qr-code-generator/scripts/generate_qr.py \
  --urls "https://example.com/blog/email-marketing-tips" "https://example.com/pricing" \
  --logo /path/to/logo.png \
  --fg-color "#1A1A1A" \
  --bg-color "#FFFFFF" \
  --output-dir ./qr-codes
```

Arguments:
- `--urls` — space-separated list; wrap each in quotes. Works with a single URL too.
- `--urls-file` (optional) — path to a text file with one URL per line (`#` comments allowed). Use this instead of `--urls` for large batches (e.g. a spreadsheet column pasted into a `.txt` file) rather than typing dozens of URLs on the command line. One of `--urls` or `--urls-file` is required, and they can be combined.
- `--logo` (optional) — path to the logo image. Applied to the center of every code in the batch.
- `--fg-color` / `--bg-color` (optional) — hex colors; default to black on white if omitted. The script checks contrast between them and prints a warning (not a hard stop) if the two colors are too close in luminance to scan reliably — pass that warning along to the user rather than silently proceeding.
- `--output-dir` (optional) — where PNGs are saved; defaults to the current directory.
- `--logo-size-ratio` (optional) — how large the logo is relative to the code, as a fraction (default `0.25` = 25%). Rarely needs changing; only adjust if the user asks for a bigger/smaller logo.
- `--size` (optional) — approximate output edge length in pixels (default `1000`), rounded to a whole number of pixels per module. Bump this up for print use (e.g. banners, posters); the default is plenty for screens and standard print.
- `--jobs` (optional) — worker processes for the batch. `0` (default) picks automatically: one per CPU core, used once the batch reaches 8 URLs. No need to touch this.
- `--force` (optional) — only use this if the user explicitly wants to proceed despite a logo-coverage error (see below). Don't pass it preemptively.

Batches are parallelized across CPU cores automatically, and the logo is loaded and resized once for the whole run rather than per URL, so a large batch costs far less than one run per URL. Prefer a single invocation with every URL over looping the script.

### The logo-coverage guardrail

Before generating anything, the script checks how much of the QR code the logo (plus its backing plate) would cover, using the shortest URL in the batch as the worst case. If coverage would climb past roughly 17% — the point past which real-world scanning starts failing, even though error correction level H nominally tolerates far more — it refuses to generate and suggests a smaller `--logo-size-ratio`. Between about 16-17% it still generates but warns that the result should be tested on a phone before printing. If the user insists on generating anyway (e.g. they've already tested it works, or accept the risk), pass `--force`, but tell them plainly that the codes very likely won't scan.

## Naming generated files

Each output PNG is automatically named from the URL itself, not a generic "qr-code-1.png" — the script derives a human-friendly slug from the last meaningful path segment of the URL (e.g. `https://knak.com/blog/email-marketing-tips` becomes `email-marketing-tips.png`). A root URL like `https://knak.com/` falls back to the domain name (`knak-com.png`). If two URLs would produce the same name, the script appends `-2`, `-3`, etc. so nothing gets overwritten. No need to rename files after the fact — this happens automatically for every URL in the batch.

## After generating

**Then save what makes the next run shorter.** The codes are outputs; these two are the
reason someone doesn't have to set this up again:

- **`qr-config.md`** — the foreground and background hex codes, the logo's filename, and
  anything they corrected you on.

  ```markdown
  # QR code settings
  <!-- Written by qr-code-generator on YYYY-MM-DD. Edit anytime. -->

  - fg_color: #1A1A1A
  - bg_color: #FFFFFF
  - logo: <filename as saved in this folder>
  - notes: <anything they corrected>
  ```

- **The logo file itself**, copied into the folder. A logo that only exists as a chat
  attachment is gone next session, and re-uploading it is the single most annoying part
  of running this twice.

Without a folder, hand both over alongside the codes and say what they're for.

Once the script finishes, it prints a per-URL success/failure summary. Report that back to the user in plain language (which codes were made, where they were saved), and deliver the PNG file(s) to them. If any URL failed (e.g. bad logo path), surface the specific error rather than the whole batch failing silently. Pass along any warnings the script printed about logo coverage or color contrast — those are the cases most likely to produce a code that looks fine but will not scan.
