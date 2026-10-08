# Marketing Operations

Five skills for the production work around a campaign: UTM-tagged links built from your own
conventions, images cropped and compressed for email with alt text written for you, branded
QR codes, and contact lists cleaned before they reach your database.

Built by [Knak](https://knak.com/?utm_source=claude&utm_medium=skill&utm_campaign=claude-plugin). The work these skills do is the same in every stack — they read
your conventions rather than imposing any.

## Skills

### `utm-generator`

Builds UTM-tagged links in batches, to your team's naming conventions rather than a generic
template. Give it a conventions doc — a spreadsheet, a Notion export, a markdown file — and it
becomes the source of truth. If you don't have one, it uses a GA4-aligned default aligned to
Default Channel Groups, and saves a copy you can edit. It also audits an existing conventions
doc and tells you where it will cause problems in reporting.

> *"Tag these five links for the spring campaign"* · *"Build UTMs for the webinar emails"* ·
> *"Is our UTM doc any good?"*

Every link in one campaign gets the same `utm_campaign`, which is what stops a single send
splitting into several rows in your analytics.

### `image-cropper`

Crops images to a size, a shape, or a fraction of their original — choosing the crop window by
what is actually in the picture rather than assuming the middle. It scores edge density,
colour and skin tone, and finds faces so a headshot stays a headshot and a group photo keeps
the whole group.

> *"Crop this square"* · *"Resize these to 600x400"* · *"Make this half the size"* ·
> *"Fit this to the hero slot"*

It shows a before-and-after preview and checks the result before handing it over, because no
scoring algorithm gets every image right. Where an image genuinely can't hold the shape you
asked for, it says so with the arithmetic and lists the shapes that would work.

### `image-compressor`

Shrinks images for email and landing pages without a visible quality hit, and writes alt text
for each one. Stills target 400KB, animated GIFs 1MB — the weights an email can carry without
clipping in Gmail. GIFs get palette reduction and a frame-rate cap first; if that isn't
enough, you're offered scaling, trimming and frame-dropping rather than having them applied
behind your back.

> *"Compress these for email"* · *"This GIF is too big"* · *"Write alt text for these"*

Crop before you compress. Compressing first bakes in the quality loss and cropping then throws
part of it away, so you pay for the same quality twice.

### `qr-code-generator`

Generates branded QR codes in batch — one per URL, your brand colours, your logo embedded in
the middle, each file named after the page it points to.

> *"Make QR codes for these event pages"* · *"QR code for the signup form, in our brand
> colours"*

### `list-upload`

Cleans, validates and deduplicates a contact-list CSV before anything is written to your
database. Country, state, phone, website and industry values are normalised to the API values
your platform actually accepts, so the import doesn't half-fail and leave you reconciling.

> *"Upload this list from the conference"* · *"Clean this CSV before it goes into Marketo"*

## Requirements

**Nothing to install.** Every skill checks for its own Python packages when it runs and
installs anything missing, quietly, in the background. You don't have to do a thing.

This matters most in Cowork, which gives every session a fresh container — so a setup
step run last week wouldn't have survived anyway. The skills handle it each time instead.
The first run of a session takes a few seconds longer while that happens; after that
it's instant.

If you use **Claude Code**, `/setup-for-claude-code` makes the install permanent on that
machine so even the first run is instant. It's a convenience, not a requirement, and the
plugin works identically without it.

For reference, this is what gets installed:

| Package | Needed by | Level |
|---|---|---|
| `Pillow` | image-compressor, image-cropper, qr-code-generator | required |
| `qrcode` | qr-code-generator | required |
| `phonenumbers`, `pycountry` | list-upload | required |
| `openpyxl` | utm-generator | required |
| `opencv-python-headless` | image-cropper — finds faces so crops keep them | required |
| `numpy` | image-cropper — faster scoring on large batches | optional |
| `pyoxipng` | image-compressor — smaller PNGs | optional |
| `gifsicle-bin` | image-compressor — smaller flat-colour GIFs (~18% on a logo); nothing on photographic ones | optional |

Anything marked optional is genuinely optional: the skill works without it and produces a
larger or less precise result rather than failing. `gifsicle` arrives as a normal Python
package, so there is no system tool to install by hand.

## Your files

So they stop asking you the same questions, the skills save a few plain markdown files
**into whatever folder you're already working in** — straight into it, not into sub-folders
and not into a folder named after the plugin. Work somewhere else next time and they simply
start fresh there.

| File | Written by | What it holds |
|---|---|---|
| `utm-conventions-<brand>.md` | utm-generator | Your link-tagging rules, named after whose they are |
| `qr-config.md` + your logo | qr-code-generator | Brand colours and which logo to use |
| `clay-functions.md` | list-upload | Your enrichment function IDs and what they return |
| `lead-schema.md` | list-upload | Your CRM and automation platform field names |
| `industry-mappings.json` | list-upload | Industry values worked out on past runs |

**None of this is required to start.** Every skill runs with no folder at all and tells you
what it could not save. It asks for one only when it has something worth keeping, and you can
say no.

The plugin also ships read-only starting points — a UTM conventions template and a contact
field schema. Copy them into your folder to customise; editing them in place doesn't survive a
plugin update.

## Optional connectors

Skills degrade rather than fail when a connector is missing, and each says what it could not
verify.

- **Your marketing automation platform** — `list-upload` writes the cleaned list. Built and
  tested against Marketo; without a connector it hands you a clean CSV instead.
- **Clay** — optional enrichment for `list-upload`. Cleaning and validation run either way.

## Companion plugin

**Email Marketing** covers the writing: briefs, copy scoring against the CHEETAH framework,
and newsletter content sourcing. The two are built to work together — the usual order is brief
or newsletter draft there, then UTMs and images here, then build and send.

## Licence

MIT. See [LICENSE](LICENSE).

`image-cropper` bundles the MIT-licensed YuNet face detection model from OpenCV Zoo
(Copyright (c) 2020 Shiqi Yu); its licence ships beside the model in
`skills/image-cropper/models/LICENSE`.

## Tested on macOS

These skills were built and tested on macOS. The Python packages they rely on ship Windows
and Linux builds, and the skills resolve `python3` or `python` to whichever the machine has,
so they should work elsewhere — but nothing here has been run on Windows or Linux, and the
shell commands throughout assume a POSIX shell (Git Bash or WSL on Windows).

One known limit: **Clay's CLI has no Windows build**, so `list-upload` falls back to the Clay
connector there, which is slower on long lists.
