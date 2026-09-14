---
name: image-cropper
description: >
  Crop any image to the exact size or shape you need (square, banner, thumbnail) using face detection and an algorithm that looks at detail, color, and contrast to find the focus of an image instead of a blind crop. Crop one image or a whole batch at once. Every result comes with a before/after preview so nothing ships until you've checked it.

  Triggers on wanting an image cropped, resized to specific dimensions, made square, made into a banner or a thumbnail, fitted to a placeholder in an email or landing page, or reshaped for a social or ad slot. Also triggers on "crop this", "make this square", "resize to 600x400", "make this half the size", "fit this to the hero slot", "turn this into a thumbnail", or any request that changes an image's shape rather than just its file size.
metadata:
  version: "1.0.0"
---

# Image cropper

Crop images to a size or a shape, and check the result before handing it over.

The script picks the window; you check it. That second half is not optional —
a bad crop is worse than a slightly-off one, and no scoring algorithm gets every
image right.

## Working folder

Cropped images and their previews go **directly into the folder the user
connects**. Don't create sub-folders for them, and don't create a folder named
after this plugin.

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

**No folder? Do the work anyway, and raise it at the end.** This skill has nothing to
remember about the user — no config, no brand rules, nothing a folder would save them
answering next time. A folder only decides where the crops land, and they are just as
deliverable as downloads. Crop first, so the first thing they see is the thing they asked
for. Then, at delivery:

> If you'd rather these landed in a folder on your machine instead of as downloads,
> attach one with the **Add folder** button and say the word — I'll write them straight
> there.

**Keep "Add folder" bold when you write this out.** It is the name of a button they have to find on screen, and bold is what makes it findable in a paragraph of text.

Say it once, after the crops are delivered, and drop it if they don't take it up. Never
hold the work back for it, and never open with it.

**Never write into `${CLAUDE_PLUGIN_ROOT}`** — a plugin update replaces the plugin
directory wholesale, so anything saved there is gone at the next update.

## Before you ask anything: start the dependency install

This skill's Python packages may not be present — Cowork hands every session a fresh
container, so nothing installed last time survives. **Kick the install off in the
background as your very first action**, then carry straight on with the questions
below while it runs:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/ensure_deps.py image-cropper &
```

Don't wait for it, don't mention it, and don't make the user watch it. By the time
they have answered, it has finished. If it fails the scripts still run and degrade
honestly — there is nothing here for the user to fix.

## Step 1 — Work out what shape they want
**Ask for a folder in your first message, alongside whatever else you need.** Raised after the work is delivered it has already cost the user the questions it exists to prevent, and the files they gave you are still only in the chat. The wording is under [Working folder](#working-folder) above.


The user will say it in one of three ways. Map it onto the right flag and don't
ask them to restate it in pixels:

| They say | Flag |
|---|---|
| "600 by 400", "1200x628" | `--size 600x400` |
| "600px wide", "make it 400 tall" | `--size 600w` / `--size 400h` — keeps the shape |
| "square", "16:9", "a banner", "portrait for stories" | `--aspect square` / `16:9` / `banner` / `story` |
| "half the size", "a third", "50%" | `--scale half` / `1/3` / `50%` |

`--aspect` takes `1:1`, `16:9`, `4:5` and any other ratio, plus the names
`square`, `portrait`, `landscape`, `story` and `banner`.

**`--scale` doesn't crop, it resamples** — same shape, fewer pixels. If someone
says "make it half the size" meaning *half the width, cropped to fit a slot*,
that's `--size`, not `--scale`. When it's genuinely ambiguous, say which you used
in one line rather than asking.

If they've named a destination instead of a size — "the hero slot", "the
thumbnail in the newsletter" — and you know the dimensions, use them and say so.
If you don't, ask for the pixels once.

## Step 2 — Crop

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/image-cropper/scripts/crop_images.py <files or folder> \
  -o <output dir> --aspect square
```

The script scores every candidate window on edge density, colour saturation and
skin tone, and keeps the one holding most of what a reader would look at.

**Faces outrank all of that.** OpenCV's YuNet detector finds every face and pulls
the crop toward them, weighted by size — so a headshot centres on the face, and a
group photo keeps the cluster rather than picking one head. Faces are ranked at
full resolution, not on the scoring thumbnail, because two faces 70 and 65 pixels
wide both shrink to 5 pixels and the order would come out of rounding.

**Where faces and text compete, the faces win, and that is sometimes wrong.** On a
promotional graphic with a headline above a row of speaker photos, the crop will
hold the photos and slice the heading. Step 3 is how that gets caught — it is the
single most common reason to override the automatic choice.

For each image it prints the window it chose and why, how much of the frame it
trimmed, and writes a `<name>-preview.png` showing the original with the crop
drawn on it beside the result.

### When the script says POOR FIT

Some images cannot hold the shape being asked for, and no amount of nudging fixes
it. The script says so, with the arithmetic:

```
POOR FIT: 2 of 5 faces fall outside the crop; 48% of the frame has to go.
Every face would fit at: 3:2, 16:9, 2:1, 3:1.
Deliver this crop, then say what was lost — don't iterate.
```

**Take it at its word and skip Step 4.** Iterating produces a second equally
compromised crop and costs the user time for nothing. Still look at the preview
once — you need to describe what was lost — then go to Step 5.

It fires only when something identifiable is gone: a face mostly outside the
window, or under 55% of the picture's detail inside it. Trimming a lot on its own
is not a problem — a square cropped to 16:9 always loses 44%, whatever is in it —
so trim is reported as context alongside a real finding, never as the finding.

## Step 3 — Look at the preview, every time

**Read the preview file.** This is the step that makes the skill trustworthy — it is where
a sliced heading or a clipped logo gets caught, while it still costs one re-run to fix.

What to check:

- **Is the subject whole?** A face with the top of the head cut, a logo clipped
  at the edge, a chart missing its axis labels — all technically high-scoring
  crops, all wrong.
- **Did any text survive intact?** On screenshots and UI captures the heading is
  usually the point, and it is often at the top where a centre crop cuts it.
- **Is there anything left of the context?** A product shot cropped so tight it
  could be anything has lost the thing that made it useful.
- **On an abstract graphic**, accept it. When there's no subject, any crop is a
  reasonable crop, and hunting for a better one wastes the user's time.
- **On a graphic with both faces and a headline**, check the headline specifically.
  The face detector will have pulled the crop toward the people, and the words are
  usually what the image is for.

## Step 4 — Correct it if it's wrong

Re-run with `--focus-point X,Y`, where X and Y are fractions of the width and
height of the **original**. `0.5,0.5` is dead centre; `0.5,0.25` is centred a
quarter of the way down.

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/image-cropper/scripts/crop_images.py photo.jpg \
  -o out/ --aspect banner --focus-point 0.5,0.3
```

Read the preview off the new run too. **Two attempts, maximum.** If the second is
still wrong the image can't hold that shape — stop and go to Step 5.

Don't iterate silently. Say what was wrong with the first crop and what you moved,
so the user can tell you're looking rather than re-rolling.

Skip this step entirely when the script reported POOR FIT.

## Step 5 — Name the files, then deliver

### Give uninformative files a real name

The script names each crop after the original with `-cropped` before the extension —
`hero.jpg` becomes `hero-cropped.jpg` — and strips any upload-hash prefix first, so
`834b9174 image.png` arrives as `image-cropped.png`. That leaves the cases where the
original name never said anything: `image`, `img`, `IMG_4821`, `DSC_0031`, `photo`,
`screenshot`, `Screen Shot 2026-07-30 at 14.22.11`, `untitled`, `unnamed`, `download`,
`copy`, `final`, `pasted-image-3`, a bare number, a hash, or just the dimensions
(`1080x1080`) — alone or with a number attached.

**Rename those from what you saw in Step 3.** You looked at every preview to check the
crop, so the name costs nothing extra: three or four words, lowercase, hyphenated, drawn
from the subject.

| Original | What the preview showed | Rename to |
|---|---|---|
| `834b9174 image.png` | Character holding a trophy under a headline | `champion-trophy-cropped.png` |
| `IMG_4821.HEIC` | Runner in starting blocks on a blue track | `runner-starting-blocks-cropped.jpg` |
| `Untitled.png` | Product screenshot of a pricing table | `pricing-table-cropped.png` |

Rules, matching `image-compressor` so a file keeps the same name through both:

- **Keep a name that already says something.** `fsr-cover-image.jpg`, `hero-banner.png`
  and `well-done-wow.gif` are useful as they are — appending `-cropped` is the whole job.
  A name like `fsr-ad-04b-1080x1080.jpg` records the campaign, the asset, the variant and
  the size, none of which is visible in the picture; renaming it throws four facts away
  and breaks the match with wherever the user has the original filed.
- **When unsure, keep the original.** A mediocre name costs nothing; replacing a
  meaningful one costs the thread back to where it was filed.
- **Keep the `-cropped` suffix** either way, so nothing collides with the original.
- **Keep the extension the script chose** — a cropped GIF comes back as a PNG.
- **Say which files you renamed and what from**, so a wrong guess is one line to correct.

Rename after the script finishes and before delivering, and rename the crop only — the
previews are working artifacts.

### Deliver

Send the cropped images. **Don't send the previews** — they're a working artifact
for the check in Step 3, not a deliverable.

Say for each image what shape it is now and anything you had to give up:

> Cropped to 1200×628. Kept the heading and the table; the file list below them
> didn't fit — the crop had to lose 45% of the frame to make 16:9.

Where you overrode the automatic choice, say so in a line, so the user knows a
judgement was made on their behalf.

### Where the crop was compromised, offer the way out

Hand over the crop they asked for — they asked for it, so they get it — then be
straight about the cost and lead with the cheapest fix:

> Here's the square crop. It can't work on this image: two of the five speakers
> fall outside it and half the heading goes with them — 48% of the frame has to
> go to make a square.
>
> Everyone fits at 16:9, 3:2 or 2:1. Want one of those instead?
>
> If it has to be square, tell me what matters more — the heading, or all five
> speakers? I can keep either, not both. Otherwise this one probably wants
> laying out again for square.

Four routes, in the order they cost the user something:

1. **A different shape** — free, and usually the answer. Use the shapes the script
   says would fit; don't guess at them.
2. **What must survive** — ask that, not "how would you like it cropped". "The
   heading or the speakers?" is a question someone can answer in three words, and
   it maps straight onto a focus point.
3. **A different image** — when the source was never going to work at that shape.
4. **A redesign** — last, because it is the most work. Say it plainly when the
   image is a graphic whose layout assumes its original shape.

Never present a compromised crop as finished, and never bury the problem under
the file. One or two sentences, up front.

## Edge cases

- **The image is already the right shape** — the script says so and copies it at
  the requested size. Don't present that as a crop.
- **The target is larger than the source** — cropping can't add pixels. Say the
  source is too small and give its real dimensions, rather than upscaling into a
  soft image.
- **An animated GIF** — only the first frame is cropped, and the output is a PNG.
  Say so; if they need the animation kept, that's a different job.
- **A batch where one image is wrong** — re-run just that one with a focus point.
  Don't re-crop the whole set.
- **They want the same crop across a set** (a row of testimonial headshots) — the
  automatic window will differ per image, which is right for faces and wrong for a
  uniform grid. Use the same `--focus-point` for all of them if consistency
  matters more than individual framing, and say which you chose.

## Next steps

- **`/image-compressor`** — in this plugin. Cropped files are still at full quality and
  often too heavy for an email. Run it on the crops, and it drafts the alt text too.
  Always this order: compressing first bakes in quality loss that cropping then throws away.
