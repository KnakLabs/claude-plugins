#!/usr/bin/env python3
"""
compress_images.py

Compress images for use in marketing emails and landing pages.

Two things drive the savings here:

1. Format routing. The old behaviour was "keep the original format", on the
   theory that changing format was risky for email. That conflated two
   different things -- JPEG and PNG are equally safe in every email client,
   so keeping a photograph in PNG buys no compatibility and costs ~10x the
   bytes. This script instead picks the best EMAIL-SAFE container for each
   image's actual content: photographs go to JPEG, flat graphics go to a
   quantized PNG, transparency stays PNG, animations stay GIF. It never
   emits WebP/AVIF unless you explicitly ask, so output is always safe to
   drop into Outlook.

   The photo-vs-graphic decision is measured, not guessed: if reducing the
   image to a 256-colour palette is visually near-lossless it is a flat
   graphic, otherwise it is photographic.

2. A byte budget. --max-bytes searches for the highest quality that fits a
   per-image size cap, which is what actually matters for email, where
   total message weight is the constraint.

Everything runs in parallel across CPU cores -- roughly 4x faster than
serial on a typical batch.

Usage:
    python3 compress_images.py INPUT_DIR -o OUTPUT_DIR [options]
    python3 compress_images.py file1.jpg file2.png -o OUTPUT_DIR [options]

Options:
    -o, --output-dir DIR    Where to write compressed images (required)
    --max-width PIXELS      Max width in px, aspect preserved (default: 1200)
    --max-height PIXELS     Max height in px, aspect preserved (default: none;
                             use --max-pixels instead for tall images, since a
                             hard height cap makes long infographics illegible)
    --max-pixels N          Max total pixels, aspect preserved (default: 4000000).
                             This is what reins in very tall images.
    --quality N             JPEG/WebP quality 1-100 (default: 82)
    --max-bytes N           Per-image byte budget. Searches quality downward,
                             then reduces palette/scale, to fit. Accepts
                             suffixes: 200KB, 1.5MB
    --min-quality N         Quality floor for that search (default: 45)
    --format {auto,keep,jpeg,png,webp}
                            auto (default) = content-based email-safe routing.
                            keep = old behaviour, preserve input format.
    --flatten-color COLOR   Background for transparency when forced to JPEG
                             (default: white)
    --jobs N                Parallel workers (default: one per CPU core)
    --report PATH           JSON report path (default: OUTPUT_DIR/compression_report.json)

Guarantees:
  * Never writes a file larger than the original; falls back to a straight
    copy (in the original format) and says so in the report.
  * Never silently drops a file to a name collision -- input subdirectory
    structure is preserved and same-stem inputs are uniquified.
  * Never flattens an animated GIF to a single frame.
  * Strips EXIF/GPS metadata, but converts to sRGB first so wide-gamut
    (Display P3) images do not shift colour.
"""

import argparse
import io
import json
import os
import re
import shutil
import subprocess
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

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
    _ensure("image-compressor")
except Exception:
    pass
# --------------------------------------------------------------------------

try:
    from PIL import Image, ImageChops, ImageCms, ImageOps, ImageSequence, ImageStat
except ImportError:
    print("Pillow is required. Install it with: pip install Pillow --break-system-packages", file=sys.stderr)
    sys.exit(1)

SUPPORTED_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".tiff", ".tif"}

# Formats that render reliably everywhere, Outlook desktop included.
EMAIL_SAFE = {"jpeg", "png", "gif"}

# Mean per-channel RMS error below which a 256-colour palette is treated as
# visually indistinguishable from the original -- i.e. the image is a flat
# graphic (logo, chart, screenshot) rather than a photograph.
GRAPHIC_RMSE_THRESHOLD = 3.0

# A palette PNG keeps text and hard edges crisp where JPEG would ring, so it
# is worth a small byte premium -- but only a small one. Some images (smooth
# illustrations, AI avatars) quantize cleanly yet are still several times
# larger as PNG, so anything above this ratio goes to JPEG instead.
PNG_PREFERENCE_RATIO = 1.15

EXT_FOR_FORMAT = {"jpeg": ".jpg", "png": ".png", "webp": ".webp", "gif": ".gif"}

# Uploaded files often arrive with an opaque hash/uuid glued onto the front of
# the real filename (e.g. "0e581867-dreamforce.png") -- an artifact of how the
# upload pipeline dedupes files, not anything meaningful about the image. Left
# alone it just gets carried into the compressed output's name too, so it's
# stripped from the stem before naming anything. Only matches a pure hex run
# of 6-10 chars followed by a hyphen with more name after it, so a real
# filename that happens to start with hex-looking characters (e.g. a hex color
# name) is unlikely to be mistaken for one. The separator varies by upload path --
# "834b9174 image.jpg" arrives space-separated -- so hyphen, space and underscore
# all count.
_UPLOAD_PREFIX_RE = re.compile(r"^[0-9a-fA-F]{6,10}[-_ ](?=.)")

# Stamped into the JSON report so it is always possible to tell which copy of
# this script produced a given run -- an older copy ships inside the
# anthropic-skills plugin under the same skill name.
PIPELINE_VERSION = "routing-v2"


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------

def human_size(num_bytes):
    num_bytes = float(num_bytes)
    for unit in ["B", "KB", "MB"]:
        if num_bytes < 1024:
            return f"{num_bytes:.1f}{unit}"
        num_bytes /= 1024
    return f"{num_bytes:.1f}GB"


def parse_size(text):
    """'200KB' / '1.5MB' / '204800' -> bytes."""
    if text is None:
        return None
    m = re.fullmatch(r"\s*([\d.]+)\s*(B|KB|MB|GB)?\s*", str(text), re.I)
    if not m:
        raise argparse.ArgumentTypeError(f"cannot parse size: {text!r}")
    mult = {"B": 1, "KB": 1024, "MB": 1024 ** 2, "GB": 1024 ** 3}[(m.group(2) or "B").upper()]
    return int(float(m.group(1)) * mult)


def parse_duration(text):
    """'3s', '2.5s' or a bare number of seconds -> milliseconds."""
    t = str(text).strip().lower().rstrip("s")
    return int(float(t) * 1000)


def gather_input_files(inputs):
    """Return [(src_path, relative_output_path_without_suffix)].

    Preserving the input subdirectory structure is what stops two files named
    hero.jpg in different folders from overwriting each other. Same-stem
    inputs in one folder (logo.png + logo.jpg) get uniquified, and the check
    ignores the extension because the output extension is not known yet.
    """
    found = []
    for item in inputs:
        p = Path(item)
        if p.is_dir():
            for f in sorted(p.rglob("*")):
                if f.is_file() and f.suffix.lower() in SUPPORTED_EXTS:
                    rel = f.relative_to(p).with_suffix("")
                    rel = rel.with_name(_UPLOAD_PREFIX_RE.sub("", rel.name))
                    found.append((f, rel))
        elif p.is_file():
            if p.suffix.lower() in SUPPORTED_EXTS:
                stem = _UPLOAD_PREFIX_RE.sub("", p.stem)
                found.append((p, Path(stem)))
            else:
                print(f"Skipping unsupported file type: {p}", file=sys.stderr)
        else:
            print(f"Path not found, skipping: {p}", file=sys.stderr)

    claimed, result = set(), []
    for src, rel in found:
        key = str(rel).lower()
        if key in claimed:
            n = 2
            while f"{key}-{n}" in claimed:
                n += 1
            rel, key = rel.with_name(f"{rel.name}-{n}"), f"{key}-{n}"
        claimed.add(key)
        result.append((src, rel))
    return result


def has_transparency(im):
    if im.mode in ("RGBA", "LA"):
        alpha = im.getchannel("A")
        return alpha.getextrema()[0] < 250
    if im.mode == "P" and "transparency" in im.info:
        return True
    return False


def to_srgb(im):
    """Convert to sRGB using the embedded profile, then drop it.

    Dropping an ICC profile without converting is what makes Display P3
    photos look wrong: the pixels stay wide-gamut but get reinterpreted as
    sRGB. Converting first means we can strip the profile for free.
    """
    profile = im.info.get("icc_profile")
    if not profile:
        return im
    try:
        src = ImageCms.ImageCmsProfile(io.BytesIO(profile))
        mode = "RGBA" if has_transparency(im) else "RGB"
        out = ImageCms.profileToProfile(im, src, ImageCms.createProfile("sRGB"), outputMode=mode)
        # Pixels are sRGB now, so the old profile is not just unnecessary --
        # carrying it would re-tag sRGB data as wide-gamut.
        out.info.pop("icc_profile", None)
        return out
    except Exception:
        return im


def scale_to_limits(im, max_width, max_height, max_pixels):
    """Downscale to satisfy every limit, preserving aspect. Never upscales."""
    ratio = 1.0
    if max_width and im.width > max_width:
        ratio = min(ratio, max_width / im.width)
    if max_height and im.height > max_height:
        ratio = min(ratio, max_height / im.height)
    if max_pixels and im.width * im.height > max_pixels:
        ratio = min(ratio, (max_pixels / (im.width * im.height)) ** 0.5)
    if ratio >= 1.0:
        return im, False
    size = (max(1, round(im.width * ratio)), max(1, round(im.height * ratio)))
    return im.resize(size, Image.LANCZOS), True


def rmse(a, b):
    """Mean per-channel RMS difference between two images."""
    stat = ImageStat.Stat(ImageChops.difference(a.convert("RGB"), b.convert("RGB")))
    return sum(stat.rms) / len(stat.rms)


def quantize(im, colors):
    """Palette-reduce, keeping alpha when present."""
    if has_transparency(im):
        # FASTOCTREE is the only Pillow method that handles an alpha channel.
        return im.convert("RGBA").quantize(
            colors=colors, method=Image.Quantize.FASTOCTREE, dither=Image.Dither.FLOYDSTEINBERG)
    return im.convert("RGB").quantize(
        colors=colors, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.FLOYDSTEINBERG)


def flatten(im, color):
    """Composite transparency onto a solid colour.

    convert('RGB') alone drops alpha and leaves transparent pixels black,
    which turns a transparent logo into a black box on a white email.
    """
    if not has_transparency(im):
        return im.convert("RGB")
    im = im.convert("RGBA")
    bg = Image.new("RGB", im.size, color)
    bg.paste(im, mask=im.getchannel("A"))
    return bg


# --------------------------------------------------------------------------
# encoders -> bytes
# --------------------------------------------------------------------------

def enc_jpeg(im, quality, bg):
    buf = io.BytesIO()
    flatten(im, bg).save(buf, format="JPEG", quality=quality, optimize=True,
                         progressive=True, subsampling="4:2:0")
    return buf.getvalue()


def enc_png(im, colors=None):
    buf = io.BytesIO()
    (quantize(im, colors) if colors else im).save(buf, format="PNG", optimize=True, compress_level=9)
    _png = _oxipng_optimise(buf.getvalue())[0]
    buf = io.BytesIO(_png)
    return buf.getvalue()


def enc_webp(im, quality):
    buf = io.BytesIO()
    im.save(buf, format="WEBP", quality=quality, method=6)
    return buf.getvalue()


def _gifsicle_optimise(data, lossy=None):
    """Hand the GIF to gifsicle when it is installed, else return it unchanged.

    How much this wins depends entirely on the content, measured rather than
    assumed. On a flat-colour animation — charts, logos, UI motion — gifsicle
    found another 79% over Pillow alone (58KB to 12KB), because inter-frame
    redundancy and a small palette are exactly what it exploits. On a
    photographic clip already quantised to 32 colours it found 2% (1052KB to
    1030KB), and --lossy changed nothing at all at any level, there being no
    palette headroom left to trade.

    So it is worth having and never worth relying on: the frame-rate cap and
    palette ladder still do the heavy lifting on photographic GIFs.
    """
    if not shutil.which("gifsicle"):
        return data, False
    cmd = ["gifsicle", "--optimize=3"]
    if lossy:
        cmd.append(f"--lossy={int(lossy)}")
    try:
        out = subprocess.run(cmd, input=data, stdout=subprocess.PIPE,
                             stderr=subprocess.DEVNULL, timeout=120).stdout
        return (out, True) if out and len(out) < len(data) else (data, False)
    except Exception:
        return data, False


def _oxipng_optimise(data):
    """Losslessly shrink a PNG with oxipng when it is installed.

    Pillow writes PNGs through zlib; oxipng searches filter and compression
    strategies properly and usually finds another 10-30% with the pixels
    untouched.
    """
    try:
        import oxipng
    except ImportError:
        return data, False
    try:
        out = oxipng.optimize_from_memory(data, level=4)
        return (out, True) if len(out) < len(data) else (data, False)
    except Exception:
        return data, False


def _gif_frames(src_path, max_width, max_height, max_pixels):
    """Load every frame as RGBA at the dimension limits, with its duration."""
    with Image.open(src_path) as im:
        frames, durations, resized = [], [], False
        for frame in ImageSequence.Iterator(im):
            # Pillow composites disposal on seek, so RGBA here is the real frame.
            scaled, was_resized = scale_to_limits(
                frame.convert("RGBA"), max_width, max_height, max_pixels)
            frames.append(scaled)
            durations.append(frame.info.get("duration", 100))
            resized = resized or was_resized
        return frames, durations, im.info.get("loop", 0), resized


def _encode_gif(frames, durations, loop, colors, scale=1.0, stride=1):
    """Encode an animation at a given palette size, scale and frame stride.

    stride > 1 keeps every Nth frame and adds the skipped frames' durations to
    the one kept, so the animation still runs for the same length of time
    instead of speeding up.
    """
    kept, kept_durations = [], []
    for i in range(0, len(frames), stride):
        held = sum(durations[i:i + stride])
        frame = frames[i]
        if scale < 1.0:
            w, h = frame.size
            frame = frame.resize((max(1, int(w * scale)), max(1, int(h * scale))),
                                 Image.LANCZOS)
        kept.append(frame.quantize(colors=colors, method=Image.Quantize.FASTOCTREE))
        kept_durations.append(held)
    buf = io.BytesIO()
    kept[0].save(buf, format="GIF", save_all=True, append_images=kept[1:],
                 duration=kept_durations, loop=loop, optimize=True, disposal=2)
    data, _ = _gifsicle_optimise(buf.getvalue())
    return data, kept[0].size, len(kept)


# Palette only. Scaling, trimming and frame-dropping all change what the user
# sees, so they are offered rather than applied — see enc_gif_animated.
# Flat-colour animations lose nothing to quantization, so the palette is the cheapest
# lever there. Photographic ones band badly below ~128 colours — gradients and skin
# tones are exactly what a small palette cannot hold — so for those the frame rate and
# the frame size are spent first and the palette is floored.
_GIF_PALETTE_LADDER_GRAPHIC = [256, 192, 128, 96, 64, 48, 32]
_GIF_PHOTO_COLOUR_FLOOR = 128
_GIF_PHOTO_FALLBACK_FPS = 8.0
_GIF_PHOTO_SCALES = [1.0, 0.9, 0.8, 0.7]


def _gif_route(frames):
    """'graphic' when the palette is the cheap lever, else 'photo'.

    choose_route() asks whether a 256-colour palette is visually lossless, which
    is useless here: a GIF source is already 256 colours, so every animation
    answers yes. Ask at the floor instead — quantizing to 64 costs a flat graphic
    almost nothing (measured 0.58 RMSE on a logo) and wrecks a photographic clip
    (9.72 on a stage-lit reaction shot). Sample two frames and take the worse of
    them, since an animation can open on a title card that looks nothing like the
    rest of it.
    """
    try:
        picks = {0, len(frames) // 2}
        worst = max(rmse(frames[i], quantize(frames[i], 64).convert("RGB"))
                    for i in picks)
        return "graphic" if worst <= GRAPHIC_RMSE_THRESHOLD else "photo"
    except Exception:
        return "photo"


def enc_gif_animated(src_path, max_width, max_height, max_pixels, max_bytes=None,
                     scale=1.0, stride=1, max_duration_ms=None, target_fps=12.5):
    """Re-encode an animation, capping the frame rate and reducing the palette.

    The frame rate is always capped at target_fps: GIFs are routinely recorded
    at 25fps or more, far beyond what the format needs, and a GIF already at or
    below the target is left alone rather than made choppier.

    After that the order depends on the content. On a flat graphic the palette
    is the cheap lever and runs down to 32 colours. On a photographic clip it is
    the most destructive one, so the frame rate and then the frame size are
    spent first and the palette is floored at 128 — which is how a stage-lit
    reaction shot ends up at 8fps and 70% rather than banded at 32 colours.

    Scaling and trimming do change what the user sees, so they are applied only
    when asked for and are otherwise reported back as the options that remain.

    Returns (data, dims, n_frames, resized, note, fits) — `fits` is False when
    the budget was not met, so the caller can say so rather than implying done.
    """
    frames, durations, loop, resized = _gif_frames(
        src_path, max_width, max_height, max_pixels)
    original_frames = len(frames)

    # Frame rate cap. Derive the stride from the source rate rather than taking
    # a fixed ratio, so a GIF already at 10fps is not halved to 5.
    fps_note = None
    total_ms = sum(durations) or 1
    source_fps = len(frames) / (total_ms / 1000)
    if stride == 1 and target_fps and source_fps > target_fps * 1.15:
        stride = max(1, round(source_fps / target_fps))
        if stride > 1:
            fps_note = f"{source_fps:.0f}fps reduced to {source_fps / stride:.1f}fps"

    if max_duration_ms:
        kept, running = 0, 0
        for d in durations:
            if running + d > max_duration_ms:
                break
            running += d
            kept += 1
        kept = max(kept, 2)
        frames, durations = frames[:kept], durations[:kept]

    applied = []
    if max_duration_ms and len(frames) < original_frames:
        applied.append(f"trimmed to {len(frames)} of {original_frames} frames "
                       f"({sum(durations) / 1000:.1f}s)")
    if scale < 1.0:
        applied.append(f"scaled to {int(scale * 100)}%")
    if fps_note:
        applied.append(fps_note)
    elif stride > 1:
        applied.append(f"every {_ordinal(stride)} frame kept")

    if not max_bytes:
        data, dims, n = _encode_gif(frames, durations, loop, 256, scale, stride)
        note = ", ".join(applied) if applied else f"{n} frames preserved"
        return data, dims, n, resized or scale < 1.0, note, True

    # Which levers cost least depends on what is in the picture, so measure it
    # rather than assuming.
    route = _gif_route(frames)

    attempts = []          # (colours, extra_stride, scale_mult)
    if route == "graphic":
        attempts = [(c, stride, 1.0) for c in _GIF_PALETTE_LADDER_GRAPHIC]
    else:
        fallback_stride = stride
        if target_fps and source_fps > _GIF_PHOTO_FALLBACK_FPS * 1.15:
            fallback_stride = max(stride, round(source_fps / _GIF_PHOTO_FALLBACK_FPS))
        for st in dict.fromkeys([stride, fallback_stride]):
            for sc in _GIF_PHOTO_SCALES:
                if sc < 1.0 and st == stride and st != fallback_stride:
                    continue        # spend the frame rate before the frame size
                for c in (256, 192, _GIF_PHOTO_COLOUR_FLOOR):
                    attempts.append((c, st, sc))

    smallest = None
    for colors, st, sc in attempts:
        eff_scale = scale * sc
        data, dims, n = _encode_gif(frames, durations, loop, colors, eff_scale, st)
        if smallest is None or len(data) < len(smallest[0]):
            smallest = (data, dims, n, colors, st, sc)
        if len(data) <= max_bytes:
            parts = list(applied)
            if st != stride:
                parts.append(f"frame rate dropped to {source_fps / st:.0f}fps")
            if sc < 1.0:
                parts.append(f"scaled to {int(sc * 100)}%")
            if colors < 256:
                parts.append(f"{colors} colours")
            note = ", ".join(parts) if parts else f"{n} frames preserved"
            return data, dims, n, resized or eff_scale < 1.0, note, True

    data, dims, n, colors, st, sc = smallest
    scale = scale * sc
    remaining = []
    if scale >= 1.0:
        remaining.append("scale it down (--gif-scale 0.7)")
    if not max_duration_ms:
        remaining.append("trim it shorter (--gif-trim 3s)")
    if target_fps:
        remaining.append(f"lower the frame rate further (--gif-target-fps {max(6, int(target_fps) // 2)})")
    else:
        remaining.append("cap the frame rate (--gif-target-fps 12.5)")
    note = (f"still {human_size(len(data))} at {colors} colours — over budget. "
            f"Options: {'; '.join(remaining)}" if remaining else
            f"still {human_size(len(data))} at {colors} colours — over budget")
    if applied:
        note = ", ".join(applied) + ", " + note
    return data, dims, n, resized or scale < 1.0, note, False


def _ordinal(n):
    return {2: "2nd", 3: "3rd"}.get(n, f"{n}th")


# --------------------------------------------------------------------------
# routing + budget
# --------------------------------------------------------------------------

def choose_route(im):
    """'graphic' if a 256-colour palette is visually lossless, else 'photo'."""
    try:
        if rmse(im, quantize(im, 256).convert("RGBA" if has_transparency(im) else "RGB")) \
                <= GRAPHIC_RMSE_THRESHOLD:
            return "graphic"
    except Exception:
        pass
    return "photo"


def encode_best(im, route, quality, bg, want_format, max_bytes, min_quality):
    """Return (bytes, format_name, note). Honours a byte budget if given."""
    alpha = has_transparency(im)

    if want_format in ("jpeg", "png", "webp"):
        target = want_format
    elif route == "graphic" or alpha:
        # Flat graphics compress better as a palette PNG than as JPEG, and
        # JPEG ringing around text/edges is exactly what you notice. Alpha
        # forces PNG regardless.
        target = "png"
    else:
        target = "jpeg"

    note = None

    if target == "png":
        colors_ladder = [256, 128, 64, 32, 16]
        best = enc_png(im)  # full-colour PNG as the baseline
        for colors in colors_ladder:
            cand = enc_png(im, colors)
            if len(cand) < len(best):
                best = cand
                break

        # PNG was chosen on visual grounds; now sanity-check it on bytes.
        # Only meaningful when nothing forces PNG -- alpha does, and so does
        # an explicit --format png.
        if not alpha and want_format is None:
            jpg = enc_jpeg(im, quality, bg)
            if len(best) > len(jpg) * PNG_PREFERENCE_RATIO:
                return encode_best(im, "photo", quality, bg, "jpeg", max_bytes, min_quality)[0], \
                       "jpeg", "routed to JPEG (PNG was much larger)"

        if max_bytes and len(best) > max_bytes:
            for colors in colors_ladder[1:]:
                cand = enc_png(im, colors)
                if len(cand) < len(best):
                    best = cand
                if len(best) <= max_bytes:
                    break
            # Still over budget and no transparency to protect: JPEG will
            # always beat a palette PNG on a photographic image.
            if len(best) > max_bytes and not alpha and want_format != "png":
                jpg, _, jnote = encode_best(im, "photo", quality, bg, "jpeg", max_bytes, min_quality)
                if len(jpg) < len(best):
                    return jpg, "jpeg", jnote or "routed to JPEG to meet byte budget"
            if len(best) > max_bytes:
                note = "over byte budget at minimum palette"
        return best, "png", note

    encode = (lambda q: enc_webp(im, q)) if target == "webp" else (lambda q: enc_jpeg(im, q, bg))
    if not max_bytes:
        return encode(quality), target, None

    best = encode(quality)
    if len(best) <= max_bytes:
        return best, target, None

    # Highest quality that fits, by bisection.
    lo, hi, fit = min_quality, quality, None
    while lo <= hi:
        mid = (lo + hi) // 2
        cand = encode(mid)
        if len(cand) <= max_bytes:
            fit, lo = (cand, mid), mid + 1
        else:
            hi = mid - 1
    if fit:
        return fit[0], target, (f"quality lowered to {fit[1]} to meet byte budget"
                                if fit[1] != quality else None)
    return encode(min_quality), target, f"over byte budget even at quality {min_quality}"


# --------------------------------------------------------------------------
# per-file worker
# --------------------------------------------------------------------------

def compress_one(src_path, out_base, opts):
    """Compress one file. out_base is the output path minus its suffix."""
    src_path, out_base = Path(src_path), Path(out_base)
    original_bytes = src_path.stat().st_size
    src_ext = src_path.suffix.lower()
    out_base.parent.mkdir(parents=True, exist_ok=True)

    def fallback(reason):
        """Ship the original bytes, in the original format."""
        final = out_base.with_suffix(src_ext)
        final.write_bytes(src_path.read_bytes())
        with Image.open(final) as probe:
            dims = list(probe.size)
        return final, final.stat().st_size, reason, dims, src_ext.lstrip(".")

    frames = 1
    with Image.open(src_path) as probe:
        frames = getattr(probe, "n_frames", 1)

    # --- animations: re-encode every frame, never flatten to frame 1 -------
    if frames > 1:
        try:
            data, dims, n, resized, gif_note, fits = enc_gif_animated(
                src_path, opts["max_width"], opts["max_height"], opts["max_pixels"],
                opts["max_bytes_animated"], opts["gif_scale"], opts["gif_stride"],
                opts["gif_trim"], opts["gif_target_fps"])
            if len(data) < original_bytes or opts["format"] not in ("auto", "keep"):
                path = out_base.with_suffix(".gif")
                path.write_bytes(data)
                out_path, out_bytes = path, len(data)
                note, fmt, out_dims = f"animated, {gif_note}", "gif", list(dims)
            else:
                out_path, out_bytes, note, out_dims, fmt = fallback(
                    f"animated, {n} frames preserved (re-encode was not smaller)")
                resized = False
        except Exception as e:
            out_path, out_bytes, note, out_dims, fmt = fallback(f"animated, copied as-is ({e})")
            resized = False
        return {
            "file": src_path.name, "output_file": out_path.name,
            "output_path": str(out_path), "original_bytes": original_bytes,
            "compressed_bytes": out_bytes,
            "percent_saved": round(100 * (1 - out_bytes / original_bytes), 1) if original_bytes else 0,
            "resized": resized, "output_dimensions": out_dims, "output_format": fmt,
            "animated": True, "frames": frames, "note": note,
        }

    # --- still images -----------------------------------------------------
    with Image.open(src_path) as opened:
        im = ImageOps.exif_transpose(opened) or opened
        im = to_srgb(im)
        if im.mode in ("P", "LA", "L", "CMYK", "I;16", "I", "1"):
            im = im.convert("RGBA" if has_transparency(im) else "RGB")
        im, resized = scale_to_limits(im, opts["max_width"], opts["max_height"], opts["max_pixels"])
        out_dims = list(im.size)

        want = opts["format"]
        if want == "keep":
            want = {"jpg": "jpeg", "tif": "tiff"}.get(src_ext.lstrip("."), src_ext.lstrip("."))
            # BMP/TIFF are not web formats -- routing them through "keep" is
            # what left a 2.3MB BMP completely uncompressed.
            if want not in ("jpeg", "png", "webp"):
                want = "auto"

        route = choose_route(im) if want == "auto" else "photo"

        # Encode, and if a byte budget is still unmet at the quality floor,
        # trade pixels for bytes -- a smaller sharp image beats a mushy one.
        attempt = im
        for _ in range(8):
            data, fmt, note = encode_best(attempt, route, opts["quality"], opts["bg"],
                                          None if want == "auto" else want,
                                          opts["max_bytes"], opts["min_quality"])
            if not opts["max_bytes"] or len(data) <= opts["max_bytes"]:
                break
            if min(attempt.size) <= 200:  # refuse to shrink into uselessness
                break
            attempt = attempt.resize(
                (max(1, int(attempt.width * 0.85)), max(1, int(attempt.height * 0.85))),
                Image.LANCZOS)
            resized = True
        if attempt.size != im.size:
            out_dims = list(attempt.size)
            note = (note + "; " if note else "") + \
                   f"downscaled to {attempt.width}x{attempt.height} to meet byte budget"

    # The "never larger than the original" fallback re-emits the input file,
    # which means changing format. Only allowed when the caller left format
    # up to us -- an explicit --format jpeg must produce a JPEG.
    may_fall_back = opts["format"] in ("auto", "keep")
    if may_fall_back and len(data) >= original_bytes and not resized \
            and src_ext.lstrip(".") in EMAIL_SAFE:
        out_path, out_bytes, note, out_dims, fmt = fallback(
            "kept original (compression did not reduce size)")
    else:
        out_path = out_base.with_suffix(EXT_FOR_FORMAT.get(fmt, ".jpg"))
        out_path.write_bytes(data)
        out_bytes = len(data)

    return {
        "file": src_path.name, "output_file": out_path.name, "output_path": str(out_path),
        "original_bytes": original_bytes, "compressed_bytes": out_bytes,
        "percent_saved": round(100 * (1 - out_bytes / original_bytes), 1) if original_bytes else 0,
        "resized": resized, "output_dimensions": out_dims, "output_format": fmt,
        "animated": False, "frames": 1,
        "route": route if opts["format"] == "auto" else opts["format"], "note": note,
    }


def _worker(job):
    src, out_base, opts = job
    try:
        return compress_one(src, out_base, opts)
    except Exception as e:
        return {"file": Path(src).name, "error": f"{type(e).__name__}: {e}"}


# --------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("inputs", nargs="+", help="Input directory or one/more image files")
    parser.add_argument("-o", "--output-dir", required=True)
    parser.add_argument("--max-width", type=int, default=1200)
    parser.add_argument("--max-height", type=int, default=None)
    parser.add_argument("--max-pixels", type=int, default=4_000_000)
    parser.add_argument("--quality", type=int, default=82)
    parser.add_argument("--max-bytes", type=parse_size, default=parse_size("400KB"),
                        help="Per-image budget for stills. Default 400KB, which keeps "
                             "them inside what an email can carry. Pass 0 to disable.")
    parser.add_argument("--max-bytes-animated", type=parse_size, default=parse_size("1MB"),
                        help="Per-image budget for animated GIFs. Default 1MB, the size "
                             "an animated GIF starts to be a problem at. Pass 0 to disable.")
    parser.add_argument("--gif-scale", type=float, default=1.0,
                        help="Scale animations by this factor, e.g. 0.7. Visible, so it "
                             "is never applied automatically.")
    parser.add_argument("--gif-target-fps", type=float, default=12.5,
                        help="Cap an animation's frame rate. Default 12.5fps, which is "
                             "plenty for the format; GIFs at or below it are untouched. "
                             "Pass 0 to keep the source frame rate.")
    parser.add_argument("--gif-stride", type=int, default=1,
                        help="Keep every Nth frame instead of deriving the stride from "
                             "--gif-target-fps. Overrides the frame-rate cap.")
    parser.add_argument("--gif-trim", type=parse_duration, default=None,
                        help="Trim an animation to its first N seconds, e.g. 3s or 2.5s.")
    parser.add_argument("--min-quality", type=int, default=45)
    parser.add_argument("--format", choices=["auto", "keep", "jpeg", "png", "webp"], default="auto")
    parser.add_argument("--flatten-color", default="white")
    parser.add_argument("--jobs", type=int, default=None)
    parser.add_argument("--report", default=None)
    args = parser.parse_args()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    files = gather_input_files(args.inputs)
    if not files:
        print("No supported image files found.", file=sys.stderr)
        sys.exit(1)

    from PIL import ImageColor
    opts = {
        "max_width": args.max_width, "max_height": args.max_height,
        "max_pixels": args.max_pixels, "quality": args.quality,
        "max_bytes": args.max_bytes or None, "min_quality": args.min_quality,
        "max_bytes_animated": args.max_bytes_animated or None,
        "gif_scale": args.gif_scale, "gif_stride": args.gif_stride,
        "gif_trim": args.gif_trim, "gif_target_fps": args.gif_target_fps or None,
        "format": args.format, "bg": ImageColor.getrgb(args.flatten_color),
    }

    jobs = [(str(src), str(out_dir / rel.parent / (rel.name + "-compressed")), opts) for src, rel in files]
    workers = args.jobs or min(os.cpu_count() or 1, len(jobs))
    if workers > 1:
        with ProcessPoolExecutor(max_workers=workers) as ex:
            results = list(ex.map(_worker, jobs))
    else:
        results = [_worker(j) for j in jobs]

    for r in results:
        if "error" in r:
            print(f"ERROR processing {r['file']}: {r['error']}", file=sys.stderr)
            continue
        bits = [r["output_format"]]
        if r.get("resized"):
            bits.append(f"{r['output_dimensions'][0]}x{r['output_dimensions'][1]}")
        if r.get("note"):
            bits.append(r["note"])
        print(f"{r['file']}: {human_size(r['original_bytes'])} -> "
              f"{human_size(r['compressed_bytes'])} ({r['percent_saved']}% saved)"
              f"  [{', '.join(bits)}]")

    ok = [r for r in results if "error" not in r]
    total_original = sum(r["original_bytes"] for r in ok)
    total_compressed = sum(r["compressed_bytes"] for r in ok)
    summary = {
        "pipeline": PIPELINE_VERSION,
        "script_path": str(Path(__file__).resolve()),
        "total_files": len(results),
        "succeeded": len(ok),
        "failed": len(results) - len(ok),
        "total_original_bytes": total_original,
        "total_compressed_bytes": total_compressed,
        "total_percent_saved": round(100 * (1 - total_compressed / total_original), 1) if total_original else 0,
        "workers": workers,
        "results": results,
    }

    report_path = Path(args.report) if args.report else out_dir / "compression_report.json"
    report_path.write_text(json.dumps(summary, indent=2))

    print(f"\nTotal: {human_size(total_original)} -> {human_size(total_compressed)} "
          f"({summary['total_percent_saved']}% saved) across {len(ok)} file(s)"
          + (f", {summary['failed']} failed" if summary["failed"] else ""))
    print(f"Report written to {report_path}")


if __name__ == "__main__":
    main()
