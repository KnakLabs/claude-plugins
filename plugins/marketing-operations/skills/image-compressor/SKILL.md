---
name: image-compressor
description: >
  Compress images for email and landing pages using intelligent Python algorithms to maintain sharpness and image quality, and get alt text written for each image automatically: compress a single image, a batch of uploaded images, or every image in a folder on your computer all in one go.

  Triggers on wanting to shrink image file size for email/web use, prep images before uploading to Marketo/Knak/a landing page builder, reduce load time, or asking for "compress this image/these images," "optimize images for email," "make this image smaller," or "write alt text for this image."
---

# Image Compressor & Alt Text Writer

Prepares images for email and landing page use: shrinks file size without a visible
quality hit, and writes an accessibility-friendly alt text suggestion for each image.
These two jobs split cleanly by who's better at them — compression is deterministic,
so a script handles it; alt text requires actually looking at the image and
understanding its role on the page, so that's on you.

## Working folder

Files this skill saves — the compressed images, and the thumbnail grid when it builds one — go
**directly into the folder the user connects**. Do not create sub-folders for them, and do not
create a folder named after this plugin. People pick a folder to suit the task at hand, and
burying files two levels beneath it helps nobody.

**Saving means writing a real file into that folder.** Work out the folder's actual path,
write each file straight there with a file-writing tool, and check it arrived. A document
card in the conversation is not a saved file — it lives in the chat, not on their machine,
and the folder stays empty.

**A folder can arrive late.** When one is connected partway through — or at the very end,
after the work is already delivered — go back and save everything that belongs in it, not
just whatever happens next. That includes files gathered earlier in the conversation, like
an uploaded logo or a voice guide — save those too, so they keep the settings that produced
the work alongside the work itself.

**Keep the path out of the conversation.** *"I'll put these in your folder"* beforehand and
*"Saved to your folder"* afterwards is all anyone needs — reading a long path back to someone
tells them nothing they don't already know. Name the files, not the directory. If a write
fails, say so plainly rather than reporting a save that never happened.

**Folder connected? Write into it and say so once.** The compressed files land there in
Step 3, so the whole closing message is *"Saved to your folder"* alongside the summary table.

**No folder? Do the work anyway, and raise it at the end.** This skill has nothing to
remember about the user — no config, no brand rules, nothing a folder would save them
answering next time. A folder only decides where the output lands, and the output is
just as deliverable as downloads. Compress first, so the first thing they see is the thing
they asked for. Then, with the
files in hand:

> These are ready to upload. If you'd rather they landed in a folder on your machine
> instead of as downloads, attach one with the **Add folder** button and say the word —
> I'll write them straight there.

**Keep "Add folder" bold when you write this out.** It is the name of a button they have to find on screen, and bold is what makes it findable in a paragraph of text.

Say it once, after delivery, and drop it if they don't take it up. Never hold the work
back for it, and never open with it.

**Never write into `${CLAUDE_PLUGIN_ROOT}`** — a plugin update replaces the plugin
directory wholesale, so anything saved there is gone at the next update.

## Step 1: Compress and write alt text

Do both, every time. Alt text is wanted on nearly every image headed for an email
or a landing page, and looking at each image is also what makes it possible to
give the badly-named ones a real filename.

Skip a half only when the user has already ruled it out in their own words —
"just make these smaller, I have the alt text", or "don't resize them, I just
need alt text". Take them at their word and say which half you skipped, so they
can correct you in one line.

## Step 2: Gather the images

Images can come from three places — figure out which applies:

- **Uploaded directly in chat**: already sitting under the uploads directory —
  don't explore it (no listing the directory, then a separate search over what
  got listed; that's two tool calls for what one does). Go straight for the
  images with a single Glob call for image extensions against the uploads root,
  e.g. `Glob(pattern="**/*.{jpg,jpeg,png,gif,webp,bmp,tiff}")` scoped to the
  uploads directory (adjust the pattern syntax if brace expansion isn't
  supported — a handful of per-extension Glob calls in one batch is still one
  round trip's worth of latency, unlike a list-then-filter search).
- **A folder on the user's computer**: use `device_list_dir` to see what's there, then
  `device_stage_files` to bring the relevant images into the workspace. If the user
  says "the images in my X folder," process every supported image in it (jpg, jpeg,
  png, gif, webp, bmp, tiff) rather than asking them to name each file — that's the
  bulk case this skill is built for.
- **A mix of both** — handle it, nothing stops you from combining sources.

## Step 3: Compress

Skip this step entirely if the user only wanted alt text.

Run the bundled script on the whole batch at once (don't loop over files one at a
time — the script already handles a directory or a file list, and runs the batch
in parallel across CPU cores):

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/image-compressor/scripts/compress_images.py <input_dir_or_files...> -o <output_dir>
```

**`<output_dir>` is the connected folder itself.** Pass its top-level path, so the script
writes the compressed files straight into the folder the user chose. Where no folder is
connected, use the session's working directory.

Defaults that suit email/landing-page work out of the box:
- Max width 1200px, and max 4,000,000 total pixels (downscales anything larger,
  preserving aspect ratio; never upscales a smaller image — the pixel cap is what
  reins in unusually tall images like long infographics without a hard height limit
  making them illegible)
- JPEG/WebP quality 82 (visually lossless for photos at typical display sizes)
- `--format auto` (the default): each image is routed to whichever email-safe
  format suits its actual content, rather than just keeping the input format.
  Photographs go to JPEG; flat graphics (logos, screenshots, charts, text-heavy
  images) go to a quantized PNG, since JPEG tends to add visible ringing around
  hard edges and text; anything with real transparency stays PNG; animated GIFs
  are re-encoded frame-by-frame rather than flattened to a single frame. The
  photo-vs-graphic call is measured (checking whether a 256-colour palette is
  visually indistinguishable from the original), not guessed from the file
  extension — a screenshot saved as a JPEG still gets treated as a graphic.

This still never emits WebP or AVIF unless explicitly asked for via `--format
webp`, so the auto-routed output stays safe for Outlook desktop and other clients
that don't render those formats reliably. If the user confirms the images are
landing-page-only (no email use), WebP is worth suggesting for extra savings —
mention it as an option rather than assuming it.

### Size budgets

The script targets **400KB for stills** and **1MB for animated GIFs** — the weights an
email can carry without clipping in Gmail or crawling on mobile data. Both are defaults — you
don't pass anything. If the user names a different limit, `--max-bytes` and
`--max-bytes-animated` take it, and `0` turns one off.

Stills are handled end to end: the highest quality that fits, then downscaling if
quality alone can't get there.

**The frame rate is always capped at 12.5fps.** GIFs are routinely recorded at 25fps
or more, far beyond what the format needs — a reaction clip at 12.5fps looks the same
and is half the data. The stride is derived from the source rate, so a GIF already at
or below 12.5fps is left alone rather than made choppier.

**After that, the order depends on what is in the picture**, because the cheapest
lever is not the same for a logo and a video clip. The script measures which it is
rather than guessing, and says which path it took.

- **Flat graphics** — logos, screen recordings, charts, anything with hard edges and
  few colours. The palette is nearly free here, so it runs down to 32 colours and
  usually gets there without touching anything else.
- **Photographic clips** — video, gradients, skin tones, stage lighting. The palette
  is the *most* destructive lever on this content: quantizing produces visible banding
  and dithering long before it produces a small file. So the frame rate goes to 8fps
  first, then the frame size to 90%, 80%, 70%, and the palette is floored at 128
  colours.

That second path is worth understanding, because it is the one that surprises people.
A 6MB stage-lit reaction clip lands at 864KB by going to 8fps at 70% size with its
full palette intact — where reducing to 32 colours got to roughly the same size and
looked obviously worse. 8fps reads fine on almost anything except fast camera pans.

**Trimming is never automatic.** Losing the end of a clip can lose the point of it,
so that one is always the user's call.

### When a GIF is still over budget

Report the size it reached and offer the levers, with what each costs:

| Lever | Flag | Cost |
|---|---|---|
| Scale it down | `--gif-scale 0.9` | Smaller on screen. Often the cheapest — 0.9 is hard to notice |
| Lower the frame rate further | `--gif-target-fps 8` | Choppier; 8fps is visible on fast motion, fine on a slow pan |
| Trim it shorter | `--gif-trim 2s` | Loses the tail; good when the payoff lands early |

**Say which you'd pick and why**, then let the user overrule you. Don't apply a
visible change and mention it afterwards, and don't hand back an over-budget file as
though it were done — it will fail QA, and a heavy GIF is a real problem in an inbox.

If nothing gets there without wrecking it, say so and offer the alternative that
isn't a compromise: a static image with a play-button treatment linking to the video.

Output files are named after the original with `-compressed` appended before the
extension (e.g. `hero.jpg` → `hero-compressed.jpg`), so the compressed version
never collides with or overwrites the original and it's obvious which is which
once both are sitting in the same folder. Any opaque upload-hash prefix that
was glued onto the front of an uploaded file's name (e.g. `0e581867-hero.jpg`)
is stripped automatically, so the compressed output is named after the real
filename, not the upload artifact.

### Give uninformative files a real name

`-compressed` on the end of a name that meant nothing to begin with still means
nothing. Uploads routinely arrive as `image.jpg`, `image-2.png`, `IMG_4821.HEIC`,
`Screenshot 2026-07-30 at 14.22.11.png`, `Untitled.png`, `download.jpg` or
`pasted-image-3.png` — a name assigned by a phone or a browser, not by anyone
describing the picture. Handing those back as `image-compressed.jpg` leaves the
user renaming files by hand before they can upload them anywhere.

**Use the alt text from Step 4 to rename those files.** You have just looked at
every image to describe it, so the name costs nothing extra: three or four
words, lowercase, hyphenated, drawn from the subject rather than the alt text
verbatim.

A name carries nothing when it is one of these, alone or with a number attached:
`image`, `img`, `IMG_4821`, `DSC_0031`, `photo`, `picture`, `screenshot`,
`Screen Shot 2026-07-30 at 14.22.11`, `untitled`, `unnamed`, `download`,
`copy`, `final`, `pasted-image-3`, a bare number, a hash or UUID, or just the
dimensions (`1080x1080`). **If you are unsure, keep the original.** Leaving a
mediocre name alone costs the user nothing; replacing a meaningful one costs
them the thread back to wherever they filed it.

| Original | Alt text | Rename to |
|---|---|---|
| `image.jpg` | "Closed stainless steel elevator doors in a dimly lit, empty elevator car" | `elevator-doors-compressed.jpg` |
| `image-2.png` | decorative scroll banner, `alt=""` | `parchment-scroll-banner-compressed.png` |
| `IMG_4821.HEIC` | "Runner in starting blocks on a blue athletics track" | `runner-starting-blocks-compressed.jpg` |

Rules:

- **Never rename a file whose name already says something.** `fsr-cover-image.jpg`,
  `well-done-wow.gif` and `hero-banner.png` are already useful — appending
  `-compressed` is the whole job. This matters more than it looks: a name like
  `fsr-ad-04b-1080x1080.jpg` records the campaign, the asset type, the variant
  and the size, none of which is visible in the picture. Vision would call it
  "runner on a track" and throw four facts away. Renaming also breaks the match
  with wherever the user has the original filed.
- **Keep the `-compressed` suffix** either way, so nothing collides with the original.
- **Keep the extension the script chose**, which may differ from the source when the
  format was converted.
- **Say which files you renamed and what from**, in the delivery table, so a wrong
  guess is one line to correct rather than something discovered later.
- **If the user ruled out alt text**, leave every name alone. Don't run a vision
  pass purely to rename — say once that alt text would also have got the
  badly-named files renamed, and leave it at that.

Rename after the script finishes, and before delivering.

The script writes `compression_report.json` in the output directory with
before/after sizes, chosen format, and any notes for every file — read it and use
it to build the summary in Step 5. It never produces a file larger than the
original (falling back to a straight copy when compression wouldn't help).

If a particular image needs different treatment (e.g. a full-bleed hero image that
should stay larger, or a strict byte cap for one specific asset), run that one
separately with `--max-width` / `--quality` / `--max-bytes` overrides rather than
forcing one setting on a batch with very different image roles.

## Step 4: Write alt text

Skip this step entirely if the user only wanted compression.

Do NOT `Read` each original image one at a time — vision processing cost scales
with an image's pixel dimensions, not its file size, so reading N full-resolution
originals means N slow vision passes, and reusing the Step 3 compressed output
doesn't help either for any image that was already under the compressor's size
threshold (same pixel dimensions, just fewer bytes). Instead, batch the whole set
into one or more labeled contact-sheet grids sized for fast, single-pass reading:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/image-compressor/scripts/make_thumbnail_grid.py <input_dir_or_files...> -o <grid_output_dir>
```

- Caps each thumbnail at 400px on its longest side and labels it with its
  (hash-stripped) filename, so one `Read` of a grid file covers up to 9 images at
  once instead of 9 separate reads.
- Batches spill into `grid_1.jpg`, `grid_2.jpg`, ... automatically once a batch
  exceeds `--max-per-grid` (default 9) — past that, cells get too small to read
  reliably, so more images means more grid files, not smaller cells.
- Writes `grid_manifest.json` (grid file → ordered source filenames) in the output
  directory — use it to keep captions and images matched up unambiguously even if
  a long filename got truncated in its caption.

`Read` each grid file (not the originals) and write alt text for every image
in it, matching cells to filenames via the manifest and the on-image captions.
For a batch of 9 or fewer this is one `Read` call total instead of one per image.

Good alt text for email/landing page images:

- Describes what's in the image and, where relevant, why it's there (a product
  screenshot, a headshot, a diagram) rather than just naming the file
- Skips "image of" / "picture of" — screen readers already announce it's an image
- Stays under about 125 characters so screen readers don't cut it off
- For purely decorative images (background textures, spacers) says so explicitly
  and suggests an empty alt attribute (`alt=""`) instead of forcing a description
- Mentions the CTA text if the image *is* a button/CTA graphic, since that's what
  a screen reader user needs to know to act on it

If a thumbnail is too small or low-detail to describe confidently (dense
diagrams, small text), it's fine to fall back to a single full-resolution `Read`
for just that one image rather than guessing from the grid.

**Now rename any file whose original name said nothing** — see "Give
uninformative files a real name" in Step 3. This is the point where it becomes
possible, because you have just described every image. Do it before delivering,
so the files the user receives are the renamed ones.

## Step 5: Deliver

If compression ran, present one summary per image as a short table (filename —
noting the original name where you renamed it,
before → after, alt text if that ran too) since that's the kind of multi-row
comparison a table clarifies rather than obscures. Put the percent saved in the
same "before → after" cell rather than a separate column or a note underneath,
e.g. `588.9KB → 62.4KB (89% saved)` — that's the number people scan for first, so
it belongs right next to the sizes it's comparing. If only alt text ran, the same
table works with the size columns dropped.

If compression ran, send the compressed image files to the user with
SendUserFile — never send the grid files, those are scratch artifacts for
writing alt text, not a deliverable.

**When a folder is connected the files are already in it**, written there by Step 3. Say so
in a few words — *"Saved to your folder"* — and send them with SendUserFile as well, so they
are also to hand in the conversation. Use `device_commit_files` where the write has to be
committed back to the user's machine.

## Next steps

- **`/image-cropper`** — in this plugin. Use it *before* this skill whenever an image is the
  wrong shape for its slot, rather than letting the template squash it. Cropping a compressed
  image throws away quality that was already paid for.
