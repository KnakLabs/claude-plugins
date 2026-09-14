"""
normalize_website.py — Strip website URLs to bare domain only.

Removes protocol (http/https), www., trailing slashes, paths, query strings,
and fragments. Leaves only the bare domain (e.g. example.com).

Examples:
    https://www.example.com/page?ref=nav  →  example.com
    http://example.com/                   →  example.com
    www.example.com                       →  example.com
    example.com                           →  example.com

Usage:
    python3 normalize_website.py input.csv output.csv --col WEBSITE
"""

import argparse
import csv
import os
import re
import sys
from urllib.parse import urlparse

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
    _ensure("list-upload")
except Exception:
    pass
# --------------------------------------------------------------------------


def normalize_website(raw_value):
    """
    Returns (normalized_value, status) where status is one of:
      'ok'        — successfully stripped to bare domain
      'unchanged' — value was empty, left as-is
      'invalid'   — could not extract a recognisable domain
    """
    if not raw_value or not raw_value.strip():
        return raw_value, "unchanged"

    url = raw_value.strip()

    # Add scheme if missing so urlparse can handle it
    if not re.match(r'^https?://', url, re.IGNORECASE):
        url = "https://" + url

    try:
        parsed = urlparse(url)
        netloc = parsed.netloc.lower()

        # Strip www. prefix
        if netloc.startswith("www."):
            netloc = netloc[4:]

        # Strip port if present (e.g. example.com:443)
        netloc = netloc.split(":")[0]

        # Basic sanity check — must have at least one dot and no spaces
        if "." in netloc and " " not in netloc and netloc:
            return netloc, "ok"
        else:
            return raw_value, "invalid"
    except Exception:
        return raw_value, "invalid"


def main():
    parser = argparse.ArgumentParser(description="Normalize website URLs to bare domain.")
    parser.add_argument("input", help="Input CSV file path")
    parser.add_argument("output", help="Output CSV file path")
    parser.add_argument("--col", required=True, help="Name of the website column in the CSV")
    args = parser.parse_args()

    with open(args.input, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames

        if args.col not in fieldnames:
            print(f"ERROR: Column '{args.col}' not found. Available columns: {fieldnames}", file=sys.stderr)
            sys.exit(1)

        rows = list(reader)

    status_col = "website_status"
    out_fieldnames = fieldnames + [status_col]

    invalid = []
    counts = {"ok": 0, "unchanged": 0, "invalid": 0}

    for row in rows:
        original = row[args.col]
        normalized, status = normalize_website(original)
        row[args.col] = normalized
        row[status_col] = status
        counts[status] += 1
        if status == "invalid":
            invalid.append(original)

    with open(args.output, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=out_fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nWebsite normalization complete")
    print(f"  Normalized to bare domain: {counts['ok']}")
    print(f"  Empty (unchanged):         {counts['unchanged']}")
    print(f"  Invalid (could not parse): {counts['invalid']}")
    print(f"\nOutput written to: {args.output}")

    if invalid:
        unique_invalid = sorted(set(invalid))
        print(f"\n⚠️  INVALID VALUES — review manually:")
        for v in unique_invalid:
            print(f'  "{v}"')
    else:
        print("\n✅ All values processed.")


if __name__ == "__main__":
    main()
