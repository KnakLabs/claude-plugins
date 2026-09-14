"""
normalize_phone.py — Normalize phone numbers to E.164 format (+CCXXXXXXXXXX).

Uses Google's libphonenumber (phonenumbers library). Takes the ISO Alpha-2 country
column as a region hint for bare local numbers (e.g. "555-1234" + "US" → "+15551234").
Run normalize_country.py first so the country column already contains ISO Alpha-2 codes.
Flags numbers it cannot parse for manual review.

Usage:
    python3 normalize_phone.py input.csv output.csv --col PHONE --country-col COUNTRY
    python3 normalize_phone.py input.csv output.csv --col PHONE
"""

import argparse
import csv
import os
import sys

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

try:
    import phonenumbers
    from phonenumbers import NumberParseException
except ImportError:
    print("ERROR: phonenumbers library not installed. Run: pip install phonenumbers --break-system-packages", file=sys.stderr)
    sys.exit(1)


def normalize_phone(raw_value, region_hint=None):
    """
    Returns (normalized_value, status) where status is one of:
      'ok'          — parsed and formatted as E.164
      'unchanged'   — value was empty, left as-is
      'parse_error' — could not parse the number
      'invalid'     — parsed but not a valid number
    """
    if not raw_value or not raw_value.strip():
        return raw_value, "unchanged"

    cleaned = raw_value.strip()

    # Try parsing with region hint first, then without
    parse_attempts = []
    if region_hint and len(region_hint.strip()) == 2:
        parse_attempts.append(region_hint.strip().upper())
    parse_attempts.append(None)  # Fallback: no region hint (works for numbers with country code)

    for region in parse_attempts:
        try:
            parsed = phonenumbers.parse(cleaned, region)
            if phonenumbers.is_valid_number(parsed):
                e164 = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
                return e164, "ok"
            else:
                # Parsed but invalid — try next region
                continue
        except NumberParseException:
            continue

    # All attempts failed — check if we at least got a parse
    for region in parse_attempts:
        try:
            phonenumbers.parse(cleaned, region)
            return raw_value, "invalid"
        except NumberParseException:
            continue

    return raw_value, "parse_error"


def main():
    parser = argparse.ArgumentParser(description="Normalize phone numbers to E.164 format.")
    parser.add_argument("input", help="Input CSV file path")
    parser.add_argument("output", help="Output CSV file path")
    parser.add_argument("--col", required=True, help="Name of the phone column in the CSV")
    parser.add_argument("--country-col", default=None, help="Name of the ISO Alpha-2 country column (used as region hint)")
    args = parser.parse_args()

    with open(args.input, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames

        if args.col not in fieldnames:
            print(f"ERROR: Column '{args.col}' not found. Available columns: {fieldnames}", file=sys.stderr)
            sys.exit(1)

        if args.country_col and args.country_col not in fieldnames:
            print(f"WARNING: Country column '{args.country_col}' not found — proceeding without region hints.", file=sys.stderr)
            args.country_col = None

        rows = list(reader)

    status_col = "phone_status"
    out_fieldnames = fieldnames + [status_col]

    flagged = []
    counts = {"ok": 0, "unchanged": 0, "parse_error": 0, "invalid": 0}

    for row in rows:
        original = row[args.col]
        region = row.get(args.country_col, "").strip() if args.country_col else None
        normalized, status = normalize_phone(original, region_hint=region)
        row[args.col] = normalized
        row[status_col] = status
        counts[status] += 1
        if status in ("parse_error", "invalid"):
            flagged.append({"original": original, "status": status, "region": region or ""})

    with open(args.output, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=out_fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nPhone normalization complete")
    print(f"  Normalized to E.164: {counts['ok']}")
    print(f"  Empty (unchanged):   {counts['unchanged']}")
    print(f"  Invalid (parsed):    {counts['invalid']}")
    print(f"  Parse errors:        {counts['parse_error']}")
    print(f"\nOutput written to: {args.output}")

    if flagged:
        print(f"\n⚠️  FLAGGED NUMBERS — review manually:")
        for item in flagged:
            region_str = f" (region hint: {item['region']})" if item["region"] else ""
            print(f'  [{item["status"]}] "{item["original"]}"{region_str}')
    else:
        print("\n✅ All numbers normalized.")


if __name__ == "__main__":
    main()
