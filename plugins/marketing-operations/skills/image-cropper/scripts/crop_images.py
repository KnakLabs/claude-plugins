#!/usr/bin/env python3
"""
crop_images.py — crop images to a target size or shape, choosing the window by
what is actually in the picture rather than assuming the middle.

A centre crop is a coin flip. It cuts the heading off a screenshot, and on a
photo it only works when the subject happens to be centred. This scores every
candidate window on edge density, colour saturation and skin tone, and keeps the
one holding the most of what a reader would look at.

Usage:
    python3 crop_images.py photo.jpg -o out/ --size 600x400
    python3 crop_images.py *.jpg      -o out/ --aspect square
    python3 crop_images.py photo.jpg  -o out/ --scale 0.5
    python3 crop_images.py photo.jpg  -o out/ --size 1200x628 --focus-point 0.3,0.25

Requires Pillow. Uses OpenCV for face detection when it is installed, and works
without it.
"""

import argparse
import os
import re
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, UnidentifiedImageError

# --- dependency bootstrap -------------------------------------------------
# Cowork hands every session a fresh container, so this skill's packages may not
# be installed yet and no setup step will have survived from last time. Install
# them quietly here. Failure is not fatal: the script carries on with whatever it
# can still do, and says so where the result is affected.
import os as _os
import sys as _sys

_sys.path.insert(0, _os.path.abspath(_os.path.join(
    _os.path.dirname(_os.path.abspath(__file__)), "..", "..", "..", "scripts")))
try:
    from ensure_deps import ensure as _ensure
    _ensure("image-cropper")
except Exception:
    pass
# --------------------------------------------------------------------------

SUPPORTED = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff", ".tif", ".gif"}
SCORE_SIZE = 120          # long edge of the thumbnail the scoring runs on
CENTRE_PULL = 0.28        # tie-break toward the middle, so ties do not fly to a corner


# --------------------------------------------------------------------------
# what the user asked for
# --------------------------------------------------------------------------

# Uploaded files often arrive with an opaque hash glued onto the front of the real
# filename ("834b9174 image.jpg", "0e581867-hero.png") -- an artifact of the upload
# pipeline rather than anything about the picture. Stripped from the stem before
# naming the output, so the crop is named after the real filename. Mirrors the same
# rule in image-compressor. Only a pure hex run of 6-10 chars followed by a
# separator with more name after it, so a genuine name starting with hex-looking
# characters is unlikely to be caught.
_UPLOAD_PREFIX_RE = re.compile(r"^[0-9a-fA-F]{6,10}[-_ ](?=.)")


def clean_stem(stem):
    """The filename with any upload-hash prefix removed."""
    return _UPLOAD_PREFIX_RE.sub("", stem).strip() or stem


def parse_target(size, aspect, scale, src_w, src_h):
    """Work out the output width and height from whichever option was given.

    Returns (width, height, description). Exactly one of size/aspect/scale is
    expected; --size wins if more than one is passed.
    """
    if size:
        m = re.fullmatch(r"\s*(\d+)\s*[x×]\s*(\d+)\s*", size)
        if m:
            return int(m.group(1)), int(m.group(2)), f"{m.group(1)}x{m.group(2)}"
        m = re.fullmatch(r"\s*(\d+)\s*(w|wide|h|high|tall)\s*", size, re.I)
        if m:                                    # one dimension, keep the shape
            n, which = int(m.group(1)), m.group(2).lower()
            if which in ("w", "wide"):
                return n, round(n * src_h / src_w), f"{n}px wide"
            return round(n * src_w / src_h), n, f"{n}px tall"
        raise ValueError(f"could not read --size {size!r}; try 600x400, 600w or 400h")

    if aspect:
        a = aspect.strip().lower()
        named = {"square": (1, 1), "portrait": (4, 5), "landscape": (16, 9),
                 "story": (9, 16), "banner": (3, 1)}
        if a in named:
            aw, ah = named[a]
        else:
            m = re.fullmatch(r"\s*(\d+(?:\.\d+)?)\s*[:/]\s*(\d+(?:\.\d+)?)\s*", a)
            if not m:
                raise ValueError(f"could not read --aspect {aspect!r}; try 1:1, 16:9 or square")
            aw, ah = float(m.group(1)), float(m.group(2))
        # largest box of that shape that fits inside the source
        if src_w / src_h > aw / ah:
            h = src_h
            w = round(h * aw / ah)
        else:
            w = src_w
            h = round(w * ah / aw)
        return w, h, f"{a} ({w}x{h})"

    if scale:
        f = parse_scale(scale)
        return max(1, round(src_w * f)), max(1, round(src_h * f)), f"{int(f * 100)}% of the original"

    raise ValueError("give one of --size, --aspect or --scale")


def parse_scale(text):
    """'half', '50%', '0.5' and '1/3' all mean the same thing."""
    t = str(text).strip().lower()
    words = {"half": 0.5, "third": 1 / 3, "quarter": 0.25, "two-thirds": 2 / 3, "three-quarters": 0.75}
    if t in words:
        return words[t]
    if t.endswith("%"):
        return float(t[:-1]) / 100
    m = re.fullmatch(r"(\d+)\s*/\s*(\d+)", t)
    if m:
        return int(m.group(1)) / int(m.group(2))
    f = float(t)
    return f / 100 if f > 1 else f


# --------------------------------------------------------------------------
# where the interesting part is
# --------------------------------------------------------------------------

def interest_map(im):
    """A per-pixel score on a small thumbnail: edges, saturation, skin.

    These three between them stand in for "what a person looks at first" —
    detail, colour, and faces. It is the same idea smartcrop uses, kept small
    enough to run on Pillow alone.
    """
    small = im.convert("RGB")
    small.thumbnail((SCORE_SIZE, SCORE_SIZE), Image.LANCZOS)
    w, h = small.size
    edges = small.convert("L").filter(ImageFilter.FIND_EDGES).getdata()
    rgb = small.getdata()
    sat = small.convert("HSV").getdata()

    scores = []
    for i in range(w * h):
        r, g, b = rgb[i]
        skin = 1.0 if (r > 95 and g > 40 and b > 20 and r > g and r > b
                       and abs(r - g) > 15 and max(r, g, b) - min(r, g, b) > 15) else 0.0
        scores.append(edges[i] / 255.0 + (sat[i][1] / 255.0) * 0.3 + skin * 1.8)
    return scores, w, h


YUNET = Path(__file__).resolve().parent.parent / "models" / "face_detection_yunet_2023mar.onnx"


def face_boxes(path):
    """Faces in *source* pixel coordinates, largest first, or [] if none.

    Uses OpenCV's YuNet detector, not the old Haar cascades — those were removed
    in OpenCV 5, and YuNet is better anyway: it holds up on faces at an angle and
    produces far fewer false positives on busy backgrounds. The model is a 227KB
    file bundled beside this script, so nothing is downloaded at run time.

    Ranking happens here, at full resolution, deliberately. Converting to the
    scoring thumbnail first truncates a 72px face and a 65px face to the same
    5px box, so the order comes out of rounding rather than the picture.
    """
    try:
        import cv2
    except ImportError:
        return []
    if not YUNET.is_file():
        return []
    try:
        img = cv2.imread(str(path))
        if img is None:
            return []
        ih, iw = img.shape[:2]
        det = cv2.FaceDetectorYN.create(str(YUNET), "", (320, 320), 0.85, 0.3, 5000)
        det.setInputSize((iw, ih))
        _, faces = det.detect(img)
        if faces is None or len(faces) == 0:
            return []
        boxes = []
        for f in faces:
            x, y, fw, fh = (float(v) for v in f[:4])
            x, y = max(0.0, x), max(0.0, y)
            boxes.append((x, y, min(fw, iw - x), min(fh, ih - y)))
        return sorted(boxes, key=lambda b: -b[2] * b[3])
    except Exception:
        return []


def integral(scores, w, h):
    """Prefix sums, so scoring a window is four lookups instead of a loop."""
    ii = [0.0] * ((w + 1) * (h + 1))
    for y in range(h):
        row = 0.0
        for x in range(w):
            row += scores[y * w + x]
            ii[(y + 1) * (w + 1) + (x + 1)] = ii[y * (w + 1) + (x + 1)] + row
    return ii


def window_sum(ii, w, x0, y0, x1, y1):
    W = w + 1
    return (ii[y1 * W + x1] - ii[y0 * W + x1] - ii[y1 * W + x0] + ii[y0 * W + x0])


def best_window(im, path, target_w, target_h, focus_point=None):
    """Pick the crop window in source coordinates, and say why it was picked."""
    src_w, src_h = im.size
    # the crop box has the target's shape, as large as fits inside the source
    ar = target_w / target_h
    if src_w / src_h > ar:
        box_h, box_w = src_h, round(src_h * ar)
    else:
        box_w, box_h = src_w, round(src_w / ar)
    box_w, box_h = min(box_w, src_w), min(box_h, src_h)
    max_x, max_y = src_w - box_w, src_h - box_h

    if focus_point:
        fx, fy = focus_point
        x = int(round(fx * src_w - box_w / 2))
        y = int(round(fy * src_h - box_h / 2))
        return (max(0, min(x, max_x)), max(0, min(y, max_y)), box_w, box_h,
                f"centred on the point you gave ({fx:.2f}, {fy:.2f})", [], None, 0, 0)

    if max_x == 0 and max_y == 0:
        return 0, 0, box_w, box_h, "already the right shape, nothing to trim", [], None, 0, 0

    scores, tw, th = interest_map(im)
    ii = integral(scores, tw, th)
    bw = max(1, round(box_w * tw / src_w))
    bh = max(1, round(box_h * th / src_h))
    bw, bh = min(bw, tw), min(bh, th)

    faces = face_boxes(path)
    reason = "the densest detail in the frame"
    if faces:
        # Boost every face, scaled by how big it is relative to the biggest, so a
        # group photo keeps the cluster instead of centring on one head — while a
        # face in the background still counts for less than the one in front.
        biggest = faces[0][2] * faces[0][3]
        for fx, fy, fw, fh in faces:
            weight = 6.0 * ((fw * fh) / biggest) ** 0.5
            x0, y0 = int(fx * tw / src_w), int(fy * th / src_h)
            x1, y1 = int((fx + fw) * tw / src_w) + 1, int((fy + fh) * th / src_h) + 1
            for y in range(max(0, y0 - 1), min(th, y1 + 1)):
                for x in range(max(0, x0 - 1), min(tw, x1 + 1)):
                    scores[y * tw + x] += weight
        ii = integral(scores, tw, th)
        bx, by, bw_, bh_ = faces[0]
        where = f"{(bx + bw_ / 2) / src_w:.0%} across, {(by + bh_ / 2) / src_h:.0%} down"
        reason = (f"the largest of {len(faces)} faces, at {where}" if len(faces) > 1
                  else f"a face at {where}")

    step = max(1, min(tw, th) // 40)
    best, best_score = (0, 0), -1.0
    for y in range(0, th - bh + 1, step):
        for x in range(0, tw - bw + 1, step):
            s = window_sum(ii, tw, x, y, x + bw, y + bh)
            # gentle pull to the middle so a tie does not land in a corner
            cx, cy = (x + bw / 2) / tw, (y + bh / 2) / th
            s *= 1.0 - CENTRE_PULL * ((cx - 0.5) ** 2 + (cy - 0.5) ** 2) * 2
            if s > best_score:
                best, best_score = (x, y), s

    x = int(round(best[0] * src_w / tw))
    y = int(round(best[1] * src_h / th))
    return (max(0, min(x, max_x)), max(0, min(y, max_y)), box_w, box_h, reason,
            faces, scores, tw, th)


# --------------------------------------------------------------------------
# output
# --------------------------------------------------------------------------

# Shapes worth suggesting when the requested one cannot hold the subject.
CANDIDATE_ASPECTS = {"square": (1, 1), "4:5": (4, 5), "3:2": (3, 2),
                     "16:9": (16, 9), "2:1": (2, 1), "3:1": (3, 1)}


def fitting_aspects(faces, src_w, src_h, exclude=None):
    """Which standard shapes could hold every face at once.

    Answering "this will not work as a square" is only useful next to "it works
    at 16:9", and that is arithmetic rather than judgement: take the box that
    encloses every face and ask which aspect ratios leave a window at least that
    big.
    """
    if len(faces) < 2:
        return []
    x0 = min(f[0] for f in faces); x1 = max(f[0] + f[2] for f in faces)
    y0 = min(f[1] for f in faces); y1 = max(f[1] + f[3] for f in faces)
    need_w, need_h = x1 - x0, y1 - y0
    out = []
    for name, (aw, ah) in CANDIDATE_ASPECTS.items():
        if name == exclude:
            continue
        if src_w / src_h > aw / ah:
            bh = src_h; bw = round(bh * aw / ah)
        else:
            bw = src_w; bh = round(bw * ah / aw)
        if bw >= need_w and bh >= need_h:
            out.append(name)
    return out


def diagnose(src_w, src_h, box, faces, scores, tw, th, requested):
    """What the crop costs, in facts the caller can repeat to the user.

    The point is to separate "this needs a nudge" from "this shape cannot work
    for this picture", without the caller having to guess from a thumbnail.
    """
    x, y, bw, bh = box
    trimmed = 100 - round(100 * (bw * bh) / (src_w * src_h))

    # how much of the interest in the picture the window actually holds
    ii = integral(scores, tw, th)
    total = window_sum(ii, tw, 0, 0, tw, th) or 1.0
    wx0, wy0 = int(x * tw / src_w), int(y * th / src_h)
    wx1, wy1 = min(tw, int((x + bw) * tw / src_w) + 1), min(th, int((y + bh) * th / src_h) + 1)
    kept_interest = round(100 * window_sum(ii, tw, wx0, wy0, wx1, wy1) / total)

    # A face counts as lost only when most of it is gone. Letterboxing a portrait
    # always clips the crown or the chin, and calling that a lost face would flag
    # every headshot cropped to 16:9 — which is a perfectly normal thing to do.
    faces_lost = []
    for fx, fy, fw, fh in faces:
        ox = max(0.0, min(fx + fw, x + bw) - max(fx, x))
        oy = max(0.0, min(fy + fh, y + bh) - max(fy, y))
        if (ox * oy) / max(1.0, fw * fh) < 0.6:
            faces_lost.append((fx, fy, fw, fh))

    # Trimming a lot is not itself a problem: a square cropped to 16:9 always
    # loses 44%, whatever is in it. A concern needs something identifiable to be
    # lost — a face, or most of the detail. Trim is then reported as context, so
    # the user knows why, rather than as the finding on its own.
    concerns = []
    if faces_lost:
        concerns.append(f"{len(faces_lost)} of {len(faces)} faces fall outside the crop")
    if kept_interest < 55:
        concerns.append(f"only {kept_interest}% of the detail in the picture is inside the window")
    if concerns and trimmed >= 40:
        concerns.append(f"{trimmed}% of the frame has to go")

    alternatives = fitting_aspects(faces, src_w, src_h, exclude=requested) if faces_lost else []
    return {"trimmed_pct": trimmed, "interest_kept_pct": kept_interest,
            "faces": len(faces), "faces_lost": len(faces_lost),
            "concerns": concerns, "fits_instead": alternatives}


def make_preview(im, box, result, out_path):
    """Original with the crop drawn on it, beside the result, for a quick look."""
    x, y, w, h = box
    left = im.convert("RGB").copy()
    d = ImageDraw.Draw(left, "RGBA")
    d.rectangle([0, 0, left.width, left.height], fill=(0, 0, 0, 110))
    left.paste(im.convert("RGB").crop((x, y, x + w, y + h)), (x, y))
    d = ImageDraw.Draw(left)
    d.rectangle([x, y, x + w - 1, y + h - 1], outline=(255, 60, 60), width=max(2, im.width // 250))

    tile = 460
    lr = left.copy(); lr.thumbnail((tile, tile), Image.LANCZOS)
    rr = result.convert("RGB").copy(); rr.thumbnail((tile, tile), Image.LANCZOS)
    pad, label = 12, 22
    canvas = Image.new("RGB", (lr.width + rr.width + pad * 3, max(lr.height, rr.height) + pad * 2 + label), (250, 250, 250))
    canvas.paste(lr, (pad, pad + label))
    canvas.paste(rr, (pad * 2 + lr.width, pad + label))
    d = ImageDraw.Draw(canvas)
    d.text((pad, 6), f"BEFORE {im.width}x{im.height} — red box is the crop", fill=(40, 40, 40))
    d.text((pad * 2 + lr.width, 6), f"AFTER {result.width}x{result.height}", fill=(40, 40, 40))
    canvas.save(out_path, "PNG")


def gather(inputs):
    out = []
    for raw in inputs:
        p = Path(raw)
        if p.is_dir():
            out += [f for f in sorted(p.rglob("*")) if f.suffix.lower() in SUPPORTED]
        elif p.suffix.lower() in SUPPORTED:
            out.append(p)
    return out


def main():
    ap = argparse.ArgumentParser(description="Crop images to a size or shape, choosing the window by content.")
    ap.add_argument("inputs", nargs="+")
    ap.add_argument("-o", "--output-dir", required=True)
    ap.add_argument("--size", help="600x400, or 600w / 400h to set one side and keep the shape")
    ap.add_argument("--aspect", help="1:1, 16:9, or square / portrait / landscape / story / banner")
    ap.add_argument("--scale", help="half, 50%%, 0.5 or 1/3 — same shape, smaller")
    ap.add_argument("--focus-point", help="X,Y as fractions of width and height, e.g. 0.3,0.25. "
                                          "Overrides the automatic choice — this is the knob to turn "
                                          "after looking at a preview.")
    ap.add_argument("--no-preview", action="store_true", help="skip the before/after preview")
    args = ap.parse_args()

    if not (args.size or args.aspect or args.scale):
        ap.error("give one of --size, --aspect or --scale")

    focus = None
    if args.focus_point:
        try:
            fx, fy = (float(v) for v in args.focus_point.split(","))
            focus = (min(max(fx, 0.0), 1.0), min(max(fy, 0.0), 1.0))
        except ValueError:
            ap.error("--focus-point wants two numbers between 0 and 1, e.g. 0.3,0.25")

    files = gather(args.inputs)
    if not files:
        print("No supported images found.", file=sys.stderr)
        sys.exit(1)

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    previews = 0

    for path in files:
        try:
            with Image.open(path) as im:
                im.load()
                src_w, src_h = im.size
                tw, th, desc = parse_target(args.size, args.aspect, args.scale, src_w, src_h)
                x, y, bw, bh, reason, faces, scores, stw, sth = best_window(
                    im, path, tw, th, focus)
                cropped = im.convert("RGB").crop((x, y, x + bw, y + bh))
                if (bw, bh) != (tw, th):
                    cropped = cropped.resize((tw, th), Image.LANCZOS)

                out_path = out_dir / f"{clean_stem(path.stem)}-cropped{path.suffix if path.suffix.lower() != '.gif' else '.png'}"
                cropped.save(out_path)

                d = (diagnose(src_w, src_h, (x, y, bw, bh), faces, scores, stw, sth,
                              (args.aspect or "").strip().lower())
                     if scores else {"trimmed_pct": 100 - round(100 * (bw * bh) / (src_w * src_h)),
                                     "concerns": [], "fits_instead": [], "faces": 0, "faces_lost": 0})

                print(f"{path.name}: {src_w}x{src_h} -> {tw}x{th} ({desc}); "
                      f"kept the window at {x},{y} — {reason}; "
                      f"{d['trimmed_pct']}% of the frame trimmed")
                if d["concerns"]:
                    print(f"  POOR FIT: {'; '.join(d['concerns'])}.")
                    if d["fits_instead"]:
                        print(f"  Every face would fit at: {', '.join(d['fits_instead'])}.")
                    print("  Deliver this crop, then say what was lost — don't iterate, "
                          "no window of this shape holds it all.")

                if not args.no_preview:
                    pv = out_dir / f"{clean_stem(path.stem)}-preview.png"
                    make_preview(im, (x, y, bw, bh), cropped, pv)
                    previews += 1
        except UnidentifiedImageError:
            print(f"{path.name}: not a readable image, skipped", file=sys.stderr)
        except Exception as e:
            print(f"{path.name}: {e}", file=sys.stderr)

    if previews:
        print(f"\n{previews} before/after preview(s) in {out_dir} — look at these before shipping the crops.")


if __name__ == "__main__":
    main()
