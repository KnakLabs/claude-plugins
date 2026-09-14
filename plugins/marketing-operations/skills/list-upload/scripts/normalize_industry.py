"""
normalize_industry.py — Map incoming industry values to SFDC picklist values.

Uses a JSON lookup cache (industry_mapping_cache.json) for fast, deterministic
matching. Values not found in the cache are flagged for manual review so that
reasoning is only applied once per unique unknown value, not once per record.

Usage:
    python3 normalize_industry.py input.csv output.csv --col INDUSTRY
    python3 normalize_industry.py input.csv output.csv --col INDUSTRY --cache /path/to/industry_mapping_cache.json
    python3 normalize_industry.py input.csv output.csv --col INDUSTRY \
        --extra-mappings /path/to/working-folder/list-upload-knowledge/industry_mappings.json

The cache file defaults to industry_mapping_cache.json in the same directory as
this script. That bundled file is a read-only seed: it lives inside the plugin, so
a plugin update overwrites it and anything added there is lost. Mappings learned on
a run belong in --extra-mappings, a file in the user's own working folder, which is
merged over the seed and wins on conflict. A missing --extra-mappings file is not an
error — it just means nothing has been learned yet.
"""

import argparse
import csv
import json
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


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_CACHE = os.path.join(SCRIPT_DIR, "industry_mapping_cache.json")


def _read_mappings(path):
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    # Strip metadata keys (prefixed with _) and lowercase all keys
    return {k.lower().strip(): v for k, v in raw.items() if not k.startswith("_")}


def load_cache(cache_path, extra_path=None):
    """Bundled seed, with the user's learned mappings merged over the top.

    The seed ships inside the plugin and is replaced on every plugin update, so
    it can only be read. extra_path points at the user's own working folder and
    wins on conflict, which is what lets a team correct a seed mapping that is
    wrong for them rather than fighting it on every run.
    """
    cache = _read_mappings(cache_path)
    if extra_path and os.path.exists(extra_path):
        cache.update(_read_mappings(extra_path))
    return cache


def normalize_industry(raw_value, cache):
    """
    Returns (normalized_value, status) where status is one of:
      'ok'         — found in cache, value replaced
      'exact'      — incoming value already matches an SFDC value exactly
      'unchanged'  — value was empty, left as-is
      'unresolved' — not in cache, needs manual mapping
    """
    if not raw_value or not raw_value.strip():
        return raw_value, "unchanged"

    key = raw_value.lower().strip()

    if key in cache:
        return cache[key], "ok"

    # Check if the value is already a valid SFDC value (case-insensitive)
    sfdc_values_lower = {v.lower(): v for v in cache.values()}
    if key in sfdc_values_lower:
        return sfdc_values_lower[key], "exact"

    return raw_value, "unresolved"


def main():
    parser = argparse.ArgumentParser(description="Normalize industry values to SFDC picklist.")
    parser.add_argument("input", help="Input CSV file path")
    parser.add_argument("output", help="Output CSV file path")
    parser.add_argument("--col", required=True, help="Name of the industry column in the CSV")
    parser.add_argument("--cache", default=DEFAULT_CACHE, help="Path to the bundled seed industry_mapping_cache.json")
    parser.add_argument("--extra-mappings", default=None,
                        help="Path to the working folder's industry_mappings.json. Merged over "
                             "the seed and wins on conflict. Absent file is fine.")
    args = parser.parse_args()

    if not os.path.exists(args.cache):
        print(f"ERROR: Cache file not found: {args.cache}", file=sys.stderr)
        sys.exit(1)

    cache = load_cache(args.cache, args.extra_mappings)

    with open(args.input, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames

        if args.col not in fieldnames:
            print(f"ERROR: Column '{args.col}' not found. Available columns: {fieldnames}", file=sys.stderr)
            sys.exit(1)

        rows = list(reader)

    status_col = "industry_status"
    out_fieldnames = fieldnames + [status_col]

    unresolved = []
    counts = {"ok": 0, "exact": 0, "unchanged": 0, "unresolved": 0}

    for row in rows:
        original = row[args.col]
        normalized, status = normalize_industry(original, cache)
        row[args.col] = normalized
        row[status_col] = status
        counts[status] += 1
        if status == "unresolved":
            unresolved.append(original)

    with open(args.output, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=out_fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    # Summary
    print(f"\nIndustry normalization complete")
    print(f"  Mapped via cache:   {counts['ok']}")
    print(f"  Already SFDC value: {counts['exact']}")
    print(f"  Empty (unchanged):  {counts['unchanged']}")
    print(f"  Unresolved:         {counts['unresolved']}")
    print(f"\nOutput written to: {args.output}")

    if unresolved:
        unique_unresolved = sorted(set(unresolved))
        target = args.extra_mappings or "list-upload-knowledge/industry_mappings.json in the working folder"
        print(f"\n⚠️  UNRESOLVED VALUES — add mappings to {target}")
        print("   (never to the bundled seed — a plugin update overwrites it)")
        for v in unique_unresolved:
            print(f'  "{v.lower()}": "<SFDC value>"')
    else:
        print("\n✅ All values resolved.")


if __name__ == "__main__":
    main()
