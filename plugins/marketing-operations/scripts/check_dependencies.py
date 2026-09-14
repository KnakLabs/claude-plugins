#!/usr/bin/env python3
"""
check_dependencies.py — report which of the plugin's dependencies are installed.

Run with no arguments for a readable report, or --json for a machine-readable
one. Exits 1 when something required is missing, so a command can branch on it.

Adding a dependency means one line in REQUIREMENTS below.
"""

import argparse
import importlib.util
import json
import shutil
import subprocess
import sys

# kind: "pip" or "binary"
# level: "required" — a skill fails without it
#        "better"   — a skill works, but produces a worse result
REQUIREMENTS = [
    # module/binary,     install name,      kind,     level,      used by,                              what it does
    ("PIL",              "Pillow",          "pip",    "required", "image-compressor, image-cropper, qr-code-generator", "reads and writes images"),
    ("qrcode",           "qrcode",          "pip",    "required", "qr-code-generator",                  "builds the QR matrix"),
    ("phonenumbers",     "phonenumbers",    "pip",    "required", "list-upload",                        "parses phone numbers to E.164"),
    ("pycountry",        "pycountry",       "pip",    "required", "list-upload",                        "maps country names to ISO codes"),
    ("openpyxl",         "openpyxl",        "pip",    "required", "utm-generator",                      "writes the .xlsx link table"),
    ("oxipng",           "pyoxipng",        "pip",    "better",   "image-compressor",                   "smaller PNGs than Pillow alone"),
    ("cv2",              "opencv-python-headless", "pip", "required", "image-cropper",                  "finds faces so crops keep them"),
    ("numpy",            "numpy",           "pip",    "better",   "image-cropper",                      "much faster crop scoring on batches"),
    ("gifsicle",         "gifsicle-bin",    "binary", "better",   "image-compressor",                   "smaller flat-colour GIFs (~18% on a logo); nothing on photographic ones"),
]

BREW_HINT = {"gifsicle": "brew install gifsicle"}


def present(name, kind):
    if kind == "binary":
        return shutil.which(name) is not None
    return importlib.util.find_spec(name) is not None


def audit():
    rows = []
    for mod, install, kind, level, used_by, what in REQUIREMENTS:
        rows.append({"module": mod, "install": install, "kind": kind, "level": level,
                     "used_by": used_by, "what": what, "present": present(mod, kind)})
    return rows


def main():
    ap = argparse.ArgumentParser(description="Check the plugin's Python and system dependencies.")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--install-missing", action="store_true",
                    help="pip install --user everything missing. System binaries are "
                         "reported with their install command rather than run.")
    args = ap.parse_args()

    rows = audit()
    if args.json:
        print(json.dumps({"python": sys.executable, "dependencies": rows}, indent=2))
        return 1 if any(not r["present"] and r["level"] == "required" for r in rows) else 0

    missing_req = [r for r in rows if not r["present"] and r["level"] == "required"]
    missing_opt = [r for r in rows if not r["present"] and r["level"] == "better"]

    print(f"Python: {sys.executable}\n")
    for level, title in (("required", "Required"), ("better", "Better if installed")):
        print(title)
        for r in [x for x in rows if x["level"] == level]:
            mark = "OK     " if r["present"] else "MISSING"
            print(f"  {mark}  {r['install']:24} {r['what']}")
            if not r["present"]:
                print(f"{'':11}{'':24} needed by {r['used_by']}")
        print()

    if not missing_req and not missing_opt:
        print("Everything is installed.")
        return 0

    if missing_req:
        print("Without the required packages these skills fail on first run:")
        for skill in sorted({s.strip() for r in missing_req for s in r["used_by"].split(",")}):
            print(f"  {skill}")
        print()

    pips = [r["install"] for r in rows if not r["present"] and r["kind"] == "pip"]
    bins = [r["install"] for r in rows if not r["present"] and r["kind"] == "binary"]

    if args.install_missing and pips:
        cmd = [sys.executable, "-m", "pip", "install", "--user", *pips]
        print("Installing: " + " ".join(pips) + "\n")
        rc = subprocess.call(cmd)
        if rc != 0:
            print("\npip failed. Run it yourself:\n  " + " ".join(cmd))
    elif pips:
        print("To install the Python packages:")
        print(f"  {sys.executable} -m pip install --user " + " ".join(pips) + "\n")

    for b in bins:
        print(f"{b} is a system tool, not a Python package. Install it with:")
        print(f"  {BREW_HINT.get(b, 'your package manager')}\n")

    return 1 if missing_req else 0


if __name__ == "__main__":
    sys.exit(main())
