#!/usr/bin/env python3
"""
generate_qr.py — Batch-generate branded QR codes with a centered logo,
similar to QR Code Monkey (https://www.qrcode-monkey.com/).

Usage:
    python generate_qr.py \
        --urls "https://example.com/blog/my-great-post" "https://example.com/pricing" \
        --logo /path/to/logo.png \
        --fg-color "#1A1A1A" \
        --bg-color "#FFFFFF" \
        --output-dir ./qr-codes

Only --urls (or --urls-file) is required. If --logo is omitted, plain QR
codes are generated (no center image). If colors are omitted, standard
black-on-white is used.

Each QR code is saved as a PNG named after a human-friendly slug derived
from the URL (e.g. "https://knak.com/blog/email-marketing-tips" ->
"email-marketing-tips.png"). If two URLs would produce the same name,
a numeric suffix is added to keep filenames unique.

Every code is rendered at error correction level H (~30% recoverable),
which is what makes the center logo overlay safe.
"""

import argparse
import os
import re
import sys
from concurrent.futures import ProcessPoolExecutor
from urllib.parse import urlparse

import qrcode
from qrcode.constants import ERROR_CORRECT_H
from PIL import Image, UnidentifiedImageError

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
    _ensure("qr-code-generator")
except Exception:
    pass
# --------------------------------------------------------------------------

# Default rendered edge length in pixels (before rounding to whole modules).
DEFAULT_SIZE = 1000

# Fraction of the code's area the logo plate may cover before we warn /
# refuse. Measured against zbar with the default 0.25 ratio: every URL
# length still decodes at up to ~15.5% coverage, and failures start
# appearing around 16-17%. Level H nominally recovers ~30% of codewords,
# but that budget is also spent on print defects and camera angle, so the
# usable ceiling is far below the theoretical one.
COVERAGE_WARN = 0.16

# Foreground/background contrast below this reads unreliably on a phone camera. One
# number, used both to warn on colours the user chose and to pick one off their logo,
# so the script never calls the same pair fine in one place and marginal in another.
CONTRAST_MIN = 3.0
COVERAGE_MAX = 0.17

# Longest slug we will build a filename from (leaves room for "-12.png").
MAX_SLUG_LEN = 120

# Batches at least this large are worth the process-pool startup cost.
PARALLEL_THRESHOLD = 8

# Populated once per process (main process, or each pool worker) so a
# batch never re-opens and re-scales the same logo file per URL.
_LOGO_CACHE = {}
_LOGO_PATH = None


def slugify_url(url: str) -> str:
    """Turn a URL into a short, human-friendly filename base.

    Prefers the last meaningful path segment (e.g. a blog post or page
    slug). Falls back to the domain name for root URLs like
    "https://example.com/" or "https://example.com".
    """
    parsed = urlparse(url if "://" in url else f"https://{url}")
    path = parsed.path.strip("/")

    segment = ""
    if path:
        # Use the last path segment, dropping any file extension and query-ish junk.
        segment = path.split("/")[-1]
        segment = re.sub(r"\.\w+$", "", segment)  # drop .html, .php, etc.

    if not segment:
        # Root URL (or just a domain) — use the domain name instead.
        segment = parsed.netloc or url
        if segment.lower().startswith("www."):
            segment = segment[4:]

    # Normalize: lowercase, replace separators with hyphens, strip anything
    # that isn't alphanumeric or a hyphen.
    segment = segment.lower().replace("_", "-").replace(" ", "-")
    segment = re.sub(r"[^a-z0-9\-]", "", segment)
    segment = re.sub(r"-+", "-", segment).strip("-")

    # Filesystems cap a name at 255 bytes; a long slug plus ".png" and any
    # deduplication suffix has to stay under that or the save fails.
    segment = segment[:MAX_SLUG_LEN].strip("-")

    return segment or "qr-code"


def unique_filename(base: str, used: set) -> str:
    name = base
    counter = 2
    while name in used:
        name = f"{base}-{counter}"
        counter += 1
    used.add(name)
    return name


def hex_to_rgb(hex_color: str):
    raw = hex_color
    hex_color = hex_color.strip().lstrip("#")
    if len(hex_color) == 3:
        hex_color = "".join(c * 2 for c in hex_color)
    if not re.fullmatch(r"[0-9a-fA-F]{6}", hex_color):
        raise ValueError(f"invalid hex color {raw!r} — expected something like '#1A1A1A' or '#FFF'")
    return tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))


def contrast_ratio(rgb_a, rgb_b) -> float:
    """WCAG relative-luminance contrast ratio between two colors."""
    def luminance(rgb):
        channels = []
        for value in rgb:
            v = value / 255.0
            channels.append(v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4)
        r, g, b = channels
        return 0.2126 * r + 0.7152 * g + 0.0722 * b

    lighter, darker = sorted((luminance(rgb_a), luminance(rgb_b)), reverse=True)
    return (lighter + 0.05) / (darker + 0.05)


def validate_logo(path, bg_rgb):
    """Open the logo once, up front, so problems surface as instructions.

    Without this the first read happens inside the coverage probe, and an
    unreadable file escapes as a raw UnidentifiedImageError traceback — after
    the user has already answered every question, and with nothing telling
    them the fix is a different file format.
    """
    try:
        with Image.open(path) as im:
            im.load()
            logo = im.convert("RGBA")
    except UnidentifiedImageError:
        if os.path.splitext(path)[1].lower() == ".svg":
            print(f"Error: {path} is an SVG. This script draws raster images (PNG, JPEG, "
                  f"GIF, WebP, TIFF, BMP); SVG is vector and needs a rendering engine "
                  f"Pillow does not include. Export a PNG at 512px or larger — with a "
                  f"transparent background — and pass that instead.", file=sys.stderr)
        else:
            print(f"Error: could not read {path} as an image. Supported formats are PNG, "
                  f"JPEG, GIF, WebP, TIFF and BMP; a transparent PNG gives the best "
                  f"result.", file=sys.stderr)
        sys.exit(1)
    except OSError as e:
        print(f"Error: could not read {path}: {e}", file=sys.stderr)
        sys.exit(1)

    # A logo is pasted using itself as the mask, so one with no transparency
    # lands as a full rectangle — its own background included. That is only
    # visible when that background differs from the code's, so check the
    # corners before warning rather than crying wolf on every opaque logo.
    if logo.getchannel("A").getextrema()[0] == 255:
        w, h = logo.size
        corners = [logo.getpixel(xy)[:3] for xy in ((0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1))]
        if any(sum(abs(c - b) for c, b in zip(corner, bg_rgb)) > 30 for corner in corners):
            print(f"Warning: {os.path.basename(path)} has no transparent background, so it "
                  f"will render as a solid rectangle over the code rather than just the "
                  f"mark. Export it as a PNG with transparency, or set --bg-color to match "
                  f"the logo's own background.", file=sys.stderr)


def _init_worker(logo_path):
    """Pool initializer: remember the logo path for this worker process."""
    global _LOGO_PATH
    _LOGO_PATH = logo_path


def prepared_logo(target_px: int):
    """Return the logo scaled to fit target_px, cached per process.

    A batch typically produces codes of identical size, so this opens and
    resamples the source image once instead of once per URL.
    """
    if _LOGO_PATH is None:
        return None
    cached = _LOGO_CACHE.get(target_px)
    if cached is None:
        logo = Image.open(_LOGO_PATH)
        logo.load()
        logo = logo.convert("RGBA")
        logo.thumbnail((target_px, target_px), Image.LANCZOS)
        _LOGO_CACHE[target_px] = logo
        cached = logo
    return cached


def render_qr(url: str, fg_rgb, bg_rgb, size: int):
    """Build the QR image from the raw module matrix, at the requested size.

    The matrix is drawn at one pixel per module into a two-color palette
    image, then upscaled by a whole-number factor. That skips both the
    per-module rectangle drawing and any color quantization, and it keeps
    every module exactly the same width — no rounding shimmer that
    scanners have to work around.
    """
    qr = qrcode.QRCode(error_correction=ERROR_CORRECT_H, border=4)
    qr.add_data(url)
    qr.make(fit=True)

    matrix = qr.get_matrix()  # includes the quiet-zone border
    grid = len(matrix)
    base = Image.frombytes("P", (grid, grid),
                           bytes(1 if cell else 0 for row in matrix for cell in row))
    base.putpalette(list(bg_rgb) + list(fg_rgb))  # index 0 = background, 1 = module

    box = max(1, round(size / grid))
    img = base.resize((grid * box, grid * box), Image.NEAREST)
    return img, qr.modules_count, box


def compose(url: str, output_path: str, fg_rgb, bg_rgb, size: int,
            logo_size_ratio: float):
    """Generate a single branded QR code and save it as a PNG."""
    img, modules, box = render_qr(url, fg_rgb, bg_rgb, size)
    qr_width, qr_height = img.size
    coverage = 0.0

    logo_target = int(min(qr_width, qr_height) * logo_size_ratio)
    logo = prepared_logo(logo_target)

    if logo is not None:
        img = img.convert("RGB")

        # Backing plate (in the background color) behind the logo so it
        # stays legible against dark modules, with a small margin.
        pad = max(10, logo_target // 10)
        plate_size = (logo.size[0] + pad * 2, logo.size[1] + pad * 2)
        plate = Image.new("RGB", plate_size, bg_rgb)

        # Coverage is measured against the code proper, excluding the
        # quiet-zone border, since only real modules carry data.
        code_px = float(modules * box)
        coverage = (plate_size[0] * plate_size[1]) / (code_px * code_px)

        plate_pos = ((qr_width - plate_size[0]) // 2, (qr_height - plate_size[1]) // 2)
        img.paste(plate, plate_pos)

        logo_pos = ((qr_width - logo.size[0]) // 2, (qr_height - logo.size[1]) // 2)
        img.paste(logo, logo_pos, logo)

    save_png(img, output_path)
    return coverage


def save_png(img, output_path):
    """Write the PNG.

    A logo-free code arrives here as a two-color palette image and is
    written straight out: that encodes several times faster than RGB and
    lands about a quarter of the size. Once a logo is composited the image
    is RGB, and it stays RGB — re-packing it into a palette costs far more
    encode time than the smaller file is worth, and quantizing would risk
    altering the logo's colors.
    """
    img.save(output_path, "PNG")


def _generate_task(job):
    """Pool-friendly wrapper: returns a plain tuple, never raises."""
    url, output_path, fg_rgb, bg_rgb, size, ratio = job
    try:
        coverage = compose(url, output_path, fg_rgb, bg_rgb, size, ratio)
        return (url, output_path, "ok", coverage)
    except Exception as e:  # noqa: BLE001 - one bad URL must not kill the batch
        return (url, None, f"error: {e}", 0.0)


def read_urls_file(path: str):
    urls = []
    with open(path, "r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line and not line.startswith("#"):
                urls.append(line)
    return urls


def suggest_colors(logo_path, top=6):
    """Print the logo's dominant colours as hex, with a scannable recommendation.

    A QR code is read by threshold, not by hue: what matters is that the modules
    are much darker than the background. Brand colours are often mid-tone, so the
    darkest prominent one is usually the only safe foreground, and the answer is
    sometimes "your brand colour will not scan, use it as an accent instead".
    """
    from PIL import Image
    im = Image.open(logo_path).convert("RGBA")
    px = [(r, g, b) for r, g, b, a in im.getdata() if a > 128]
    if not px:
        print("Logo is fully transparent — no colours to read.")
        return 1
    q = Image.new("RGB", (len(px), 1))
    q.putdata(px)
    q = q.quantize(colors=top, method=Image.MEDIANCUT).convert("RGB")
    counts = sorted(q.getcolors(1 << 24), key=lambda c: -c[0])
    total = sum(c for c, _ in counts)

    print(f"Colours in {os.path.basename(logo_path)}:\n")
    rows = []
    for count, rgb in counts:
        hexv = "#%02X%02X%02X" % rgb
        share = 100.0 * count / total
        rows.append((hexv, rgb, share))
        print(f"  {hexv}   {share:5.1f}% of the logo   contrast on white: {contrast_ratio(rgb, (255, 255, 255)):.1f}:1")

    dark = [r for r in rows if contrast_ratio(r[1], (255, 255, 255)) >= CONTRAST_MIN and r[2] >= 5.0]
    print()
    if dark:
        best = max(dark, key=lambda r: contrast_ratio(r[1], (255, 255, 255)))
        print(f"Recommended: --fg-color {best[0]} --bg-color #FFFFFF "
              f"({contrast_ratio(best[1], (255, 255, 255)):.1f}:1 — scans reliably)")
    else:
        best = max(rows, key=lambda r: contrast_ratio(r[1], (255, 255, 255)))
        print(f"None of these is dark enough to scan reliably on white. The closest is "
              f"{best[0]} at {contrast_ratio(best[1], (255, 255, 255)):.1f}:1.\n"
              f"Use #1A1A1A modules on #FFFFFF and keep the brand colour in "
              f"the logo itself.")
    return 0


def main():
    parser = argparse.ArgumentParser(description="Batch-generate branded QR codes with a centered logo.")
    parser.add_argument("--urls", nargs="*", default=[], help="One or more URLs to encode.")
    parser.add_argument("--urls-file", default=None,
                        help="Path to a text file with one URL per line ('#' comments allowed). "
                             "Use this instead of --urls for large batches.")
    parser.add_argument("--logo", default=None, help="Path to a logo/image to place in the center of every QR code.")
    parser.add_argument("--fg-color", default="#000000", help="Foreground (module) hex color, e.g. #1A1A1A")
    parser.add_argument("--bg-color", default="#FFFFFF", help="Background hex color, e.g. #FFFFFF")
    parser.add_argument("--output-dir", default=".", help="Directory to save generated PNGs into.")
    parser.add_argument("--logo-size-ratio", type=float, default=0.25,
                        help="Logo width/height as a fraction of the QR code size (default 0.25 = 25%%).")
    parser.add_argument("--size", type=int, default=DEFAULT_SIZE,
                        help=f"Approximate output edge length in pixels (default {DEFAULT_SIZE}). "
                             "Rounded to a whole number of pixels per module.")
    parser.add_argument("--jobs", type=int, default=0,
                        help="Worker processes for the batch. 0 (default) picks automatically.")
    parser.add_argument("--force", action="store_true",
                        help="Generate even if the logo would cover too much of the code to scan reliably.")
    parser.add_argument("--suggest-colors", metavar="LOGO",
                        help="Read a logo and print its dominant colours as hex, with a "
                             "foreground/background pair that will actually scan. Use this "
                             "instead of asking the user to look up their brand hex codes.")
    args = parser.parse_args()

    if args.suggest_colors:
        sys.exit(suggest_colors(args.suggest_colors))

    urls = list(args.urls)
    if args.urls_file:
        try:
            urls.extend(read_urls_file(args.urls_file))
        except OSError as e:
            print(f"Error: could not read --urls-file: {e}", file=sys.stderr)
            sys.exit(1)
    if not urls:
        parser.error("provide at least one URL via --urls or --urls-file")

    # Validate everything once, up front, so a typo fails immediately
    # instead of once per URL after the batch has already started.
    try:
        fg_rgb = hex_to_rgb(args.fg_color)
        bg_rgb = hex_to_rgb(args.bg_color)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    ratio = contrast_ratio(fg_rgb, bg_rgb)
    if ratio < CONTRAST_MIN:
        print(f"Warning: foreground and background contrast is only {ratio:.1f}:1 — "
              f"scanners may fail to read these codes. Pick a darker foreground "
              f"or lighter background.", file=sys.stderr)

    if args.logo:
        if not os.path.isfile(args.logo):
            print(f"Error: logo file not found: {args.logo}", file=sys.stderr)
            sys.exit(1)
        validate_logo(args.logo, bg_rgb)

    if not 0 < args.logo_size_ratio < 1:
        print(f"Error: --logo-size-ratio must be between 0 and 1 (got {args.logo_size_ratio}).", file=sys.stderr)
        sys.exit(1)

    if args.size < 100:
        print(f"Error: --size must be at least 100 pixels (got {args.size}).", file=sys.stderr)
        sys.exit(1)

    os.makedirs(args.output_dir, exist_ok=True)

    # Identical URLs would race on the same output file and waste work.
    seen_urls = set()
    unique_urls = []
    for url in urls:
        if url not in seen_urls:
            seen_urls.add(url)
            unique_urls.append(url)
    duplicates = len(urls) - len(unique_urls)

    used_names = set()
    jobs = []
    for url in unique_urls:
        name = unique_filename(slugify_url(url), used_names)
        output_path = os.path.join(args.output_dir, f"{name}.png")
        jobs.append((url, output_path, fg_rgb, bg_rgb, args.size, args.logo_size_ratio))

    _init_worker(args.logo)

    # Check the logo overlay before committing the batch to disk. The
    # shortest URL is the worst case: fewer modules means the quiet-zone
    # border eats a bigger share of the image, so the same logo covers
    # proportionally more of the code, and small versions have fewer
    # error-correction blocks to spend.
    if args.logo:
        worst = min(jobs, key=lambda job: len(job[0]))
        probe_coverage = compose(worst[0], os.devnull, fg_rgb, bg_rgb,
                                 args.size, args.logo_size_ratio)
        if probe_coverage > COVERAGE_MAX and not args.force:
            print(f"Error: the logo would cover {probe_coverage:.0%} of the QR code for "
                  f"{worst[0]}, past the ~{COVERAGE_MAX:.0%} that stays reliably scannable "
                  f"at error correction level H. Lower --logo-size-ratio "
                  f"(try {args.logo_size_ratio * 0.8:.2f}) or pass --force to generate anyway.",
                  file=sys.stderr)
            sys.exit(1)
        elif probe_coverage > COVERAGE_WARN:
            print(f"Warning: the logo covers {probe_coverage:.0%} of the QR code for "
                  f"{worst[0]}. That is close to the point where codes stop scanning — "
                  f"test this one on a phone before printing.", file=sys.stderr)
        if probe_coverage > COVERAGE_MAX and args.force:
            print(f"Warning: --force set, generating anyway at {probe_coverage:.0%} coverage. "
                  f"These codes very likely will NOT scan. Test every one before use.",
                  file=sys.stderr)

    workers = args.jobs if args.jobs > 0 else min(len(jobs), (os.cpu_count() or 1))
    if len(jobs) >= PARALLEL_THRESHOLD and workers > 1:
        with ProcessPoolExecutor(max_workers=workers,
                                 initializer=_init_worker,
                                 initargs=(args.logo,)) as pool:
            results = list(pool.map(_generate_task, jobs, chunksize=4))
    else:
        results = [_generate_task(job) for job in jobs]

    print("\nQR code generation results:")
    for url, path, status, _ in results:
        if status == "ok":
            print(f"  ✓ {url} -> {path}")
        else:
            print(f"  ✗ {url} -> {status}")

    if duplicates:
        print(f"  ({duplicates} duplicate URL(s) skipped)")

    failures = [r for r in results if r[2] != "ok"]
    if failures:
        sys.exit(1)


if __name__ == "__main__":
    main()
