"""
normalize_country.py — Convert country name/abbreviation values to ISO Alpha-2 codes.

Uses a hardcoded lookup table for common variants (e.g. "USA" → "US", "UK" → "GB")
then falls back to pycountry fuzzy search for anything not in the table.
Flags values it cannot resolve for manual review.

Usage:
    python3 normalize_country.py input.csv output.csv --col COUNTRY
    python3 normalize_country.py input.csv output.csv --col COUNTRY --no-fuzzy
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


# Hardcoded lookup: lowercased incoming value → ISO Alpha-2
COUNTRY_MAP = {
    # United States
    "usa": "US",
    "u.s.a.": "US",
    "u.s.": "US",
    "united states": "US",
    "united states of america": "US",
    "us": "US",
    "america": "US",

    # United Kingdom
    "uk": "GB",
    "u.k.": "GB",
    "united kingdom": "GB",
    "great britain": "GB",
    "britain": "GB",
    "england": "GB",
    "scotland": "GB",
    "wales": "GB",
    "northern ireland": "GB",

    # Canada
    "canada": "CA",
    "ca": "CA",
    "can": "CA",

    # Australia
    "australia": "AU",
    "au": "AU",
    "aus": "AU",

    # Germany
    "germany": "DE",
    "deutschland": "DE",
    "de": "DE",
    "ger": "DE",

    # France
    "france": "FR",
    "fr": "FR",

    # Netherlands
    "netherlands": "NL",
    "the netherlands": "NL",
    "holland": "NL",
    "nl": "NL",

    # Sweden
    "sweden": "SE",
    "se": "SE",

    # Norway
    "norway": "NO",
    "no": "NO",

    # Denmark
    "denmark": "DK",
    "dk": "DK",

    # Finland
    "finland": "FI",
    "fi": "FI",

    # Switzerland
    "switzerland": "CH",
    "ch": "CH",
    "swiss": "CH",

    # Austria
    "austria": "AT",
    "at": "AT",

    # Belgium
    "belgium": "BE",
    "be": "BE",

    # Ireland
    "ireland": "IE",
    "republic of ireland": "IE",
    "ie": "IE",

    # Spain
    "spain": "ES",
    "es": "ES",
    "españa": "ES",

    # Italy
    "italy": "IT",
    "it": "IT",
    "italia": "IT",

    # Portugal
    "portugal": "PT",
    "pt": "PT",

    # Poland
    "poland": "PL",
    "pl": "PL",

    # Czech Republic / Czechia
    "czech republic": "CZ",
    "czechia": "CZ",
    "cz": "CZ",

    # Hungary
    "hungary": "HU",
    "hu": "HU",

    # Romania
    "romania": "RO",
    "ro": "RO",

    # Russia
    "russia": "RU",
    "russian federation": "RU",
    "ru": "RU",

    # Turkey
    "turkey": "TR",
    "türkiye": "TR",
    "tr": "TR",

    # India
    "india": "IN",
    "in": "IN",
    "ind": "IN",

    # China
    "china": "CN",
    "cn": "CN",
    "prc": "CN",
    "people's republic of china": "CN",

    # Japan
    "japan": "JP",
    "jp": "JP",
    "jpn": "JP",

    # South Korea
    "south korea": "KR",
    "korea": "KR",
    "republic of korea": "KR",
    "kr": "KR",

    # Singapore
    "singapore": "SG",
    "sg": "SG",

    # Hong Kong
    "hong kong": "HK",
    "hk": "HK",

    # Taiwan
    "taiwan": "TW",
    "tw": "TW",
    "republic of china": "TW",

    # Malaysia
    "malaysia": "MY",
    "my": "MY",

    # Indonesia
    "indonesia": "ID",
    "id": "ID",

    # Philippines
    "philippines": "PH",
    "ph": "PH",
    "the philippines": "PH",

    # Thailand
    "thailand": "TH",
    "th": "TH",

    # Vietnam
    "vietnam": "VN",
    "viet nam": "VN",
    "vn": "VN",

    # New Zealand
    "new zealand": "NZ",
    "nz": "NZ",

    # Brazil
    "brazil": "BR",
    "brasil": "BR",
    "br": "BR",

    # Mexico
    "mexico": "MX",
    "méxico": "MX",
    "mx": "MX",

    # Argentina
    "argentina": "AR",
    "ar": "AR",

    # Chile
    "chile": "CL",
    "cl": "CL",

    # Colombia
    "colombia": "CO",
    "co": "CO",

    # Peru
    "peru": "PE",
    "perú": "PE",
    "pe": "PE",

    # South Africa
    "south africa": "ZA",
    "za": "ZA",
    "rsa": "ZA",

    # Nigeria
    "nigeria": "NG",
    "ng": "NG",

    # Egypt
    "egypt": "EG",
    "eg": "EG",

    # Kenya
    "kenya": "KE",
    "ke": "KE",

    # Ghana
    "ghana": "GH",
    "gh": "GH",

    # Israel
    "israel": "IL",
    "il": "IL",

    # United Arab Emirates
    "united arab emirates": "AE",
    "uae": "AE",
    "ae": "AE",

    # Saudi Arabia
    "saudi arabia": "SA",
    "ksa": "SA",
    "sa": "SA",

    # Qatar
    "qatar": "QA",
    "qa": "QA",

    # Kuwait
    "kuwait": "KW",
    "kw": "KW",

    # Bahrain
    "bahrain": "BH",
    "bh": "BH",

    # Pakistan
    "pakistan": "PK",
    "pk": "PK",

    # Bangladesh
    "bangladesh": "BD",
    "bd": "BD",

    # Sri Lanka
    "sri lanka": "LK",
    "lk": "LK",

    # Congo (Democratic Republic)
    "congo": "CD",
    "democratic republic of congo": "CD",
    "dr congo": "CD",
    "drc": "CD",
    "democratic republic of the congo": "CD",

    # Congo (Republic)
    "republic of the congo": "CG",
    "republic of congo": "CG",

    # Greece
    "greece": "GR",
    "gr": "GR",

    # Croatia
    "croatia": "HR",
    "hr": "HR",

    # Slovakia
    "slovakia": "SK",
    "sk": "SK",

    # Slovenia
    "slovenia": "SI",
    "si": "SI",

    # Bulgaria
    "bulgaria": "BG",
    "bg": "BG",

    # Serbia
    "serbia": "RS",
    "rs": "RS",

    # Ukraine
    "ukraine": "UA",
    "ua": "UA",

    # Luxembourg
    "luxembourg": "LU",
    "lu": "LU",

    # Malta
    "malta": "MT",
    "mt": "MT",

    # Cyprus
    "cyprus": "CY",
    "cy": "CY",

    # Estonia
    "estonia": "EE",
    "ee": "EE",

    # Latvia
    "latvia": "LV",
    "lv": "LV",

    # Lithuania
    "lithuania": "LT",
    "lt": "LT",
}


def code_to_name(alpha2):
    """ISO Alpha-2 -> the country's common name. Returns None when unresolvable."""
    a2 = (alpha2 or "").strip().upper()
    if len(a2) != 2:
        return None
    try:
        import pycountry
        c = pycountry.countries.get(alpha_2=a2)
        if c:
            return getattr(c, "common_name", None) or c.name
    except Exception:
        pass
    # Fallback for the common cases when pycountry is unavailable: invert the
    # hardcoded table, preferring the longest spelling, which is the full name
    # rather than an abbreviation.
    best = None
    for name, code in COUNTRY_MAP.items():
        if code == a2 and (best is None or len(name) > len(best)):
            best = name
    return best.title() if best else None


def normalize_country(raw_value, use_fuzzy=True, to="code"):
    """
    Returns (value, status). With to="code" the value is an ISO Alpha-2 code;
    with to="name" it is the country's name. Status is one of:
      'ok'         — resolved via hardcoded table
      'fuzzy'      — resolved via pycountry fuzzy search
      'unchanged'  — value was empty, left as-is
      'unresolved' — could not be mapped
    """
    if not raw_value or not raw_value.strip():
        return raw_value, "unchanged"

    key = raw_value.lower().strip()

    # Exact match in hardcoded table
    if key in COUNTRY_MAP:
        return COUNTRY_MAP[key], "ok"

    # Check if already a valid ISO Alpha-2 (2-letter uppercase)
    if len(key) == 2 and key.upper() == raw_value.strip():
        # Assume it's already an ISO code — pass through uppercased
        return raw_value.strip().upper(), "ok"

    # Fuzzy fallback via pycountry
    if use_fuzzy:
        try:
            import pycountry
            results = pycountry.countries.search_fuzzy(raw_value.strip())
            if results:
                return results[0].alpha_2, "fuzzy"
        except Exception:
            pass

    return raw_value, "unresolved"


def normalize_country_to(raw_value, use_fuzzy=True, to="code"):
    """Resolve to a code first, then render in the requested direction."""
    value, status = normalize_country(raw_value, use_fuzzy=use_fuzzy)
    if to == "name" and status in ("ok", "fuzzy"):
        name = code_to_name(value)
        if name:
            return name, status
        return value, "unresolved"
    return value, status


def main():
    parser = argparse.ArgumentParser(
        description="Normalize country values to ISO Alpha-2 codes or to country names.")
    parser.add_argument("input", help="Input CSV file path")
    parser.add_argument("output", help="Output CSV file path")
    parser.add_argument("--col", required=True, help="Name of the country column in the CSV")
    parser.add_argument("--no-fuzzy", action="store_true", help="Disable pycountry fuzzy search fallback")
    parser.add_argument("--to", choices=["code", "name"], default="code",
                        help="Output form: 'code' for ISO Alpha-2 (default), 'name' for the country name")
    args = parser.parse_args()

    use_fuzzy = not args.no_fuzzy

    with open(args.input, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames

        if args.col not in fieldnames:
            print(f"ERROR: Column '{args.col}' not found. Available columns: {fieldnames}", file=sys.stderr)
            sys.exit(1)

        rows = list(reader)

    status_col = "country_status"
    out_fieldnames = fieldnames + [status_col]

    unresolved = []
    counts = {"ok": 0, "fuzzy": 0, "unchanged": 0, "unresolved": 0}

    for row in rows:
        original = row[args.col]
        normalized, status = normalize_country_to(original, use_fuzzy=use_fuzzy, to=args.to)
        row[args.col] = normalized
        row[status_col] = status
        counts[status] += 1
        if status == "unresolved":
            unresolved.append(original)

    with open(args.output, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=out_fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nCountry normalization complete")
    print(f"  Mapped via table:   {counts['ok']}")
    print(f"  Mapped via fuzzy:   {counts['fuzzy']}")
    print(f"  Empty (unchanged):  {counts['unchanged']}")
    print(f"  Unresolved:         {counts['unresolved']}")
    print(f"\nOutput written to: {args.output}")

    if unresolved:
        unique_unresolved = sorted(set(unresolved))
        print(f"\n⚠️  UNRESOLVED VALUES — resolve manually:")
        for v in unique_unresolved:
            print(f'  "{v}"')
    else:
        print("\n✅ All values resolved.")


if __name__ == "__main__":
    main()
