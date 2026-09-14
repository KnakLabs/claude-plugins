#!/usr/bin/env python3
"""
make_thumbnail_grid.py

Tile multiple images into one (or more) labeled contact-sheet grids, sized
for a vision model to describe in a single pass instead of one Read call per
image.

Why this exists: vision processing cost scales with an image's pixel
dimensions, not its file size. Reading N full-resolution originals one at a
time to write alt text is N slow vision passes. A grid of small, labeled
thumbnails lets one pass cover many images at once, and downscaling before
that pass (rather than reusing the email-compressed output) guarantees the
speedup applies even to images the compressor left untouched because they
were already under its size threshold.

Each cell is capped at --cell-size on its longest side (default 400px) and
stamped with a caption (its filename) so the model can tell cells apart in
its response. Grids are capped at --max-per-grid images (default 9, i.e. a
3x3 layout) -- past that, cells get too small to read reliably, so the
remainder spills into additional numbered grid files instead of cramming
everything into one image.

Usage:
    python3 make_thumbnail_grid.py INPUT_DIR -o OUTPUT_DIR
    python3 make_thumbnail_grid.py file1.jpg file2.png ... -o OUTPUT_DIR

Options:
    -o, --output-dir DIR     Where to write grid_1.jpg, grid_2.jpg, ...
    --cell-size PIXELS       Max width/height per thumbnail cell (default: 400)
    --max-per-grid N         Max images per grid file before spilling into
                              another grid (default: 9)
    --columns N              Columns per grid (default: auto, ceil(sqrt(n)))
    --caption-height PIXELS  Height reserved for each cell's filename caption
                              (default: 28)

Prints one line per grid file written, and a JSON manifest (grid file ->
ordered list of source filenames, left-to-right/top-to-bottom) to
OUTPUT_DIR/grid_manifest.json so the order stays unambiguous even if a
caption is too long to render legibly.
"""

import argparse
import json
import math
import re
import sys
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
    from PIL import Image, ImageDraw, ImageFont, ImageOps
except ImportError:
    print("Pillow is required. Install it with: pip install Pillow --break-system-packages", file=sys.stderr)
    sys.exit(1)

SUPPORTED_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".tiff", ".tif"}

# Same upload-hash-prefix pattern as compress_images.py -- strip it from
# captions too, so a grid cell reads "hero.jpg" rather than
# "0e581867-hero.jpg", which is what actually maps back to the real file.
_UPLOAD_PREFIX_RE = re.compile(r"^[0-9a-fA-F]{6,10}-(?=.)")


def display_name(filename):
    return _UPLOAD_PREFIX_RE.sub("", filename)


BG_COLOR = (24, 24, 24)
CAPTION_BG = (0, 0, 0)
CAPTION_FG = (255, 255, 255)
CELL_PADDING = 10
# Real transparency gets flattened onto white before it goes in a cell,
# instead of compositing onto the grid's dark canvas. Most of these images
# end up on a white email/landing-page background, so pasting alpha straight
# onto a dark cell backdrop makes a white-background asset read as having a
# black background -- that's not just a style difference, it will steer alt
# text off the real image (e.g. "black background" instead of transparent).
TRANSPARENCY_FLATTEN_COLOR = (255, 255, 255)


def gather_input_files(inputs):
    found = []
    for item in inputs:
        p = Path(item)
        if p.is_dir():
            for f in sorted(p.rglob("*")):
                if f.is_file() and f.suffix.lower() in SUPPORTED_EXTS:
                    found.append(f)
        elif p.is_file():
            if p.suffix.lower() in SUPPORTED_EXTS:
                found.append(p)
            else:
                print(f"Skipping unsupported file type: {p}", file=sys.stderr)
        else:
            print(f"Path not found, skipping: {p}", file=sys.stderr)
    return found


def load_font(size):
    for name in ("DejaVuSans.ttf", "Arial.ttf", "LiberationSans-Regular.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except Exception:
            continue
    return ImageFont.load_default()


def make_cell(src_path, cell_size, caption_height, font):
    """Return an image of exactly (cell_size, cell_size + caption_height)."""
    with Image.open(src_path) as im:
        im = ImageOps.exif_transpose(im) or im
        im = im.convert("RGBA") if im.mode in ("P", "LA", "RGBA") else im.convert("RGB")
        if im.mode == "RGBA":
            alpha = im.getchannel("A")
            if alpha.getextrema()[0] < 250:
                # Real transparency -- flatten onto white rather than let it
                # composite onto the dark cell backdrop later.
                flat = Image.new("RGB", im.size, TRANSPARENCY_FLATTEN_COLOR)
                flat.paste(im, mask=alpha)
                im = flat
            else:
                im = im.convert("RGB")
        thumb = im.copy()
        thumb.thumbnail((cell_size, cell_size), Image.LANCZOS)

    cell = Image.new("RGB", (cell_size, cell_size + caption_height), BG_COLOR)
    # Center the thumbnail in the image area.
    x = (cell_size - thumb.width) // 2
    y = (cell_size - thumb.height) // 2
    cell.paste(thumb, (x, y))

    draw = ImageDraw.Draw(cell)
    draw.rectangle([0, cell_size, cell_size, cell_size + caption_height], fill=CAPTION_BG)
    name = display_name(src_path.name)
    # Truncate long filenames so they don't overflow the cell width.
    max_chars = max(8, cell_size // 7)
    if len(name) > max_chars:
        name = name[: max_chars - 1] + "…"
    draw.text((6, cell_size + caption_height // 2), name, fill=CAPTION_FG,
              font=font, anchor="lm")
    return cell


def build_grid(files, cell_size, caption_height, columns):
    n = len(files)
    cols = columns or max(1, math.ceil(math.sqrt(n)))
    rows = math.ceil(n / cols)

    cell_w = cell_size
    cell_h = cell_size + caption_height
    grid_w = cols * cell_w + (cols + 1) * CELL_PADDING
    grid_h = rows * cell_h + (rows + 1) * CELL_PADDING

    grid = Image.new("RGB", (grid_w, grid_h), BG_COLOR)
    font = load_font(max(12, caption_height - 10))

    for idx, src in enumerate(files):
        r, c = divmod(idx, cols)
        cell = make_cell(src, cell_size, caption_height, font)
        x = CELL_PADDING + c * (cell_w + CELL_PADDING)
        y = CELL_PADDING + r * (cell_h + CELL_PADDING)
        grid.paste(cell, (x, y))

    return grid


def chunked(seq, n):
    for i in range(0, len(seq), n):
        yield seq[i:i + n]


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("inputs", nargs="+", help="Input directory or one/more image files")
    parser.add_argument("-o", "--output-dir", required=True)
    parser.add_argument("--cell-size", type=int, default=400)
    parser.add_argument("--max-per-grid", type=int, default=9)
    parser.add_argument("--columns", type=int, default=None)
    parser.add_argument("--caption-height", type=int, default=28)
    args = parser.parse_args()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    files = gather_input_files(args.inputs)
    if not files:
        print("No supported image files found.", file=sys.stderr)
        sys.exit(1)

    manifest = {}
    for i, batch in enumerate(chunked(files, args.max_per_grid), start=1):
        grid = build_grid(batch, args.cell_size, args.caption_height, args.columns)
        out_path = out_dir / f"grid_{i}.jpg"
        grid.save(out_path, format="JPEG", quality=88, optimize=True)
        manifest[out_path.name] = [f.name for f in batch]
        print(f"{out_path}: {len(batch)} image(s), {grid.width}x{grid.height}")

    manifest_path = out_dir / "grid_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2))
    print(f"\nManifest written to {manifest_path}")


if __name__ == "__main__":
    main()
