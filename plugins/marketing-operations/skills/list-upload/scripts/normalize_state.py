"""
normalize_state.py — Convert state/province names and abbreviations to 2-letter codes.

Covers the 10 countries Salesforce supports for state/province picklists:
AU, BR, CA, CN, IN, IE, IT, JP, MX, US

Records from unsupported countries are skipped automatically (state left as-is).
Flags any values it cannot resolve for manual review.

Usage:
    python3 normalize_state.py input.csv output.csv --col STATE --country-col COUNTRY
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


# State/province maps per country (ISO Alpha-2 country code → {lowercased name/abbrev → 2-letter code})
STATE_MAPS = {
    "US": {
        "alabama": "AL", "al": "AL",
        "alaska": "AK", "ak": "AK",
        "arizona": "AZ", "az": "AZ",
        "arkansas": "AR", "ar": "AR",
        "california": "CA", "ca": "CA",
        "colorado": "CO", "co": "CO",
        "connecticut": "CT", "ct": "CT",
        "delaware": "DE", "de": "DE",
        "florida": "FL", "fl": "FL",
        "georgia": "GA", "ga": "GA",
        "hawaii": "HI", "hi": "HI",
        "idaho": "ID", "id": "ID",
        "illinois": "IL", "il": "IL",
        "indiana": "IN", "in": "IN",
        "iowa": "IA", "ia": "IA",
        "kansas": "KS", "ks": "KS",
        "kentucky": "KY", "ky": "KY",
        "louisiana": "LA", "la": "LA",
        "maine": "ME", "me": "ME",
        "maryland": "MD", "md": "MD",
        "massachusetts": "MA", "ma": "MA",
        "michigan": "MI", "mi": "MI",
        "minnesota": "MN", "mn": "MN",
        "mississippi": "MS", "ms": "MS",
        "missouri": "MO", "mo": "MO",
        "montana": "MT", "mt": "MT",
        "nebraska": "NE", "ne": "NE",
        "nevada": "NV", "nv": "NV",
        "new hampshire": "NH", "nh": "NH",
        "new jersey": "NJ", "nj": "NJ",
        "new mexico": "NM", "nm": "NM",
        "new york": "NY", "ny": "NY",
        "north carolina": "NC", "nc": "NC",
        "north dakota": "ND", "nd": "ND",
        "ohio": "OH", "oh": "OH",
        "oklahoma": "OK", "ok": "OK",
        "oregon": "OR", "or": "OR",
        "pennsylvania": "PA", "pa": "PA",
        "rhode island": "RI", "ri": "RI",
        "south carolina": "SC", "sc": "SC",
        "south dakota": "SD", "sd": "SD",
        "tennessee": "TN", "tn": "TN",
        "texas": "TX", "tx": "TX",
        "utah": "UT", "ut": "UT",
        "vermont": "VT", "vt": "VT",
        "virginia": "VA", "va": "VA",
        "washington": "WA", "wa": "WA",
        "west virginia": "WV", "wv": "WV",
        "wisconsin": "WI", "wi": "WI",
        "wyoming": "WY", "wy": "WY",
        "district of columbia": "DC", "dc": "DC", "washington dc": "DC", "washington d.c.": "DC",
    },
    "CA": {
        "alberta": "AB", "ab": "AB",
        "british columbia": "BC", "bc": "BC",
        "manitoba": "MB", "mb": "MB",
        "new brunswick": "NB", "nb": "NB",
        "newfoundland and labrador": "NL", "newfoundland": "NL", "nl": "NL",
        "northwest territories": "NT", "nt": "NT",
        "nova scotia": "NS", "ns": "NS",
        "nunavut": "NU", "nu": "NU",
        "ontario": "ON", "on": "ON",
        "prince edward island": "PE", "pei": "PE", "pe": "PE",
        "quebec": "QC", "qc": "QC", "québec": "QC",
        "saskatchewan": "SK", "sk": "SK",
        "yukon": "YT", "yt": "YT",
    },
    "AU": {
        "australian capital territory": "ACT", "act": "ACT",
        "new south wales": "NSW", "nsw": "NSW",
        "northern territory": "NT", "nt": "NT",
        "queensland": "QLD", "qld": "QLD",
        "south australia": "SA", "sa": "SA",
        "tasmania": "TAS", "tas": "TAS",
        "victoria": "VIC", "vic": "VIC",
        "western australia": "WA", "wa": "WA",
    },
    "BR": {
        "acre": "AC", "ac": "AC",
        "alagoas": "AL", "al": "AL",
        "amapá": "AP", "amapa": "AP", "ap": "AP",
        "amazonas": "AM", "am": "AM",
        "bahia": "BA", "ba": "BA",
        "ceará": "CE", "ceara": "CE", "ce": "CE",
        "distrito federal": "DF", "df": "DF",
        "espírito santo": "ES", "espirito santo": "ES", "es": "ES",
        "goiás": "GO", "goias": "GO", "go": "GO",
        "maranhão": "MA", "maranhao": "MA", "ma": "MA",
        "mato grosso": "MT", "mt": "MT",
        "mato grosso do sul": "MS", "ms": "MS",
        "minas gerais": "MG", "mg": "MG",
        "pará": "PA", "para": "PA", "pa": "PA",
        "paraíba": "PB", "paraiba": "PB", "pb": "PB",
        "paraná": "PR", "parana": "PR", "pr": "PR",
        "pernambuco": "PE", "pe": "PE",
        "piauí": "PI", "piaui": "PI", "pi": "PI",
        "rio de janeiro": "RJ", "rj": "RJ",
        "rio grande do norte": "RN", "rn": "RN",
        "rio grande do sul": "RS", "rs": "RS",
        "rondônia": "RO", "rondonia": "RO", "ro": "RO",
        "roraima": "RR", "rr": "RR",
        "santa catarina": "SC", "sc": "SC",
        "são paulo": "SP", "sao paulo": "SP", "sp": "SP",
        "sergipe": "SE", "se": "SE",
        "tocantins": "TO", "to": "TO",
    },
    "CN": {
        "anhui": "AH", "ah": "AH",
        "beijing": "BJ", "bj": "BJ",
        "chongqing": "CQ", "cq": "CQ",
        "fujian": "FJ", "fj": "FJ",
        "gansu": "GS", "gs": "GS",
        "guangdong": "GD", "gd": "GD",
        "guangxi": "GX", "gx": "GX",
        "guizhou": "GZ", "gz": "GZ",
        "hainan": "HI", "hi": "HI",
        "hebei": "HE", "he": "HE",
        "heilongjiang": "HL", "hl": "HL",
        "henan": "HA", "ha": "HA",
        "hubei": "HB", "hb": "HB",
        "hunan": "HN", "hn": "HN",
        "inner mongolia": "NM", "nei mongol": "NM", "nm": "NM",
        "jiangsu": "JS", "js": "JS",
        "jiangxi": "JX", "jx": "JX",
        "jilin": "JL", "jl": "JL",
        "liaoning": "LN", "ln": "LN",
        "ningxia": "NX", "nx": "NX",
        "qinghai": "QH", "qh": "QH",
        "shaanxi": "SN", "sn": "SN",
        "shandong": "SD", "sd": "SD",
        "shanghai": "SH", "sh": "SH",
        "shanxi": "SX", "sx": "SX",
        "sichuan": "SC", "sc": "SC",
        "tianjin": "TJ", "tj": "TJ",
        "tibet": "XZ", "xizang": "XZ", "xz": "XZ",
        "xinjiang": "XJ", "xj": "XJ",
        "yunnan": "YN", "yn": "YN",
        "zhejiang": "ZJ", "zj": "ZJ",
    },
    "IN": {
        "andhra pradesh": "AP", "ap": "AP",
        "arunachal pradesh": "AR", "ar": "AR",
        "assam": "AS", "as": "AS",
        "bihar": "BR", "br": "BR",
        "chhattisgarh": "CG", "cg": "CG",
        "goa": "GA", "ga": "GA",
        "gujarat": "GJ", "gj": "GJ",
        "haryana": "HR", "hr": "HR",
        "himachal pradesh": "HP", "hp": "HP",
        "jharkhand": "JH", "jh": "JH",
        "karnataka": "KA", "ka": "KA",
        "kerala": "KL", "kl": "KL",
        "madhya pradesh": "MP", "mp": "MP",
        "maharashtra": "MH", "mh": "MH",
        "manipur": "MN", "mn": "MN",
        "meghalaya": "ML", "ml": "ML",
        "mizoram": "MZ", "mz": "MZ",
        "nagaland": "NL", "nl": "NL",
        "odisha": "OR", "orissa": "OR", "or": "OR",
        "punjab": "PB", "pb": "PB",
        "rajasthan": "RJ", "rj": "RJ",
        "sikkim": "SK", "sk": "SK",
        "tamil nadu": "TN", "tn": "TN",
        "telangana": "TS", "ts": "TS",
        "tripura": "TR", "tr": "TR",
        "uttar pradesh": "UP", "up": "UP",
        "uttarakhand": "UK", "uk": "UK",
        "west bengal": "WB", "wb": "WB",
        "delhi": "DL", "dl": "DL", "new delhi": "DL",
        "chandigarh": "CH", "ch": "CH",
        "puducherry": "PY", "pondicherry": "PY", "py": "PY",
    },
    "IE": {
        "carlow": "CW", "cw": "CW",
        "cavan": "CN", "cn": "CN",
        "clare": "CE", "ce": "CE",
        "cork": "CO", "co": "CO",
        "donegal": "DL", "dl": "DL",
        "dublin": "D", "d": "D",
        "galway": "G", "g": "G",
        "kerry": "KY", "ky": "KY",
        "kildare": "KE", "ke": "KE",
        "kilkenny": "KK", "kk": "KK",
        "laois": "LS", "ls": "LS",
        "leitrim": "LM", "lm": "LM",
        "limerick": "LK", "lk": "LK",
        "longford": "LD", "ld": "LD",
        "louth": "LH", "lh": "LH",
        "mayo": "MO", "mo": "MO",
        "meath": "MH", "mh": "MH",
        "monaghan": "MN", "mn": "MN",
        "offaly": "OY", "oy": "OY",
        "roscommon": "RN", "rn": "RN",
        "sligo": "SO", "so": "SO",
        "tipperary": "TA", "ta": "TA",
        "waterford": "WD", "wd": "WD",
        "westmeath": "WH", "wh": "WH",
        "wexford": "WX", "wx": "WX",
        "wicklow": "WW", "ww": "WW",
    },
    "IT": {
        "agrigento": "AG", "ag": "AG",
        "alessandria": "AL", "al": "AL",
        "ancona": "AN", "an": "AN",
        "aosta": "AO", "ao": "AO",
        "arezzo": "AR", "ar": "AR",
        "ascoli piceno": "AP", "ap": "AP",
        "asti": "AT", "at": "AT",
        "avellino": "AV", "av": "AV",
        "bari": "BA", "ba": "BA",
        "barletta-andria-trani": "BT", "bt": "BT",
        "belluno": "BL", "bl": "BL",
        "benevento": "BN", "bn": "BN",
        "bergamo": "BG", "bg": "BG",
        "biella": "BI", "bi": "BI",
        "bologna": "BO", "bo": "BO",
        "bolzano": "BZ", "bz": "BZ",
        "brescia": "BS", "bs": "BS",
        "brindisi": "BR", "br": "BR",
        "cagliari": "CA", "ca": "CA",
        "caltanissetta": "CL", "cl": "CL",
        "campobasso": "CB", "cb": "CB",
        "caserta": "CE", "ce": "CE",
        "catania": "CT", "ct": "CT",
        "catanzaro": "CZ", "cz": "CZ",
        "chieti": "CH", "ch": "CH",
        "como": "CO", "co": "CO",
        "cosenza": "CS", "cs": "CS",
        "cremona": "CR", "cr": "CR",
        "crotone": "KR", "kr": "KR",
        "cuneo": "CN", "cn": "CN",
        "enna": "EN", "en": "EN",
        "fermo": "FM", "fm": "FM",
        "ferrara": "FE", "fe": "FE",
        "firenze": "FI", "fi": "FI", "florence": "FI",
        "foggia": "FG", "fg": "FG",
        "forlì-cesena": "FC", "fc": "FC",
        "frosinone": "FR", "fr": "FR",
        "genova": "GE", "ge": "GE", "genoa": "GE",
        "gorizia": "GO", "go": "GO",
        "grosseto": "GR", "gr": "GR",
        "imperia": "IM", "im": "IM",
        "isernia": "IS", "is": "IS",
        "la spezia": "SP", "sp": "SP",
        "l'aquila": "AQ", "aq": "AQ",
        "latina": "LT", "lt": "LT",
        "lecce": "LE", "le": "LE",
        "lecco": "LC", "lc": "LC",
        "livorno": "LI", "li": "LI",
        "lodi": "LO", "lo": "LO",
        "lucca": "LU", "lu": "LU",
        "macerata": "MC", "mc": "MC",
        "mantova": "MN", "mn": "MN",
        "massa-carrara": "MS", "ms": "MS",
        "matera": "MT", "mt": "MT",
        "messina": "ME", "me": "ME",
        "milano": "MI", "mi": "MI", "milan": "MI",
        "modena": "MO", "mo": "MO",
        "monza e brianza": "MB", "mb": "MB",
        "napoli": "NA", "na": "NA", "naples": "NA",
        "novara": "NO", "no": "NO",
        "nuoro": "NU", "nu": "NU",
        "oristano": "OR", "or": "OR",
        "padova": "PD", "pd": "PD",
        "palermo": "PA", "pa": "PA",
        "parma": "PR", "pr": "PR",
        "pavia": "PV", "pv": "PV",
        "perugia": "PG", "pg": "PG",
        "pesaro e urbino": "PU", "pu": "PU",
        "pescara": "PE", "pe": "PE",
        "piacenza": "PC", "pc": "PC",
        "pisa": "PI", "pi": "PI",
        "pistoia": "PT", "pt": "PT",
        "pordenone": "PN", "pn": "PN",
        "potenza": "PZ", "pz": "PZ",
        "prato": "PO", "po": "PO",
        "ragusa": "RG", "rg": "RG",
        "ravenna": "RA", "ra": "RA",
        "reggio calabria": "RC", "rc": "RC",
        "reggio emilia": "RE", "re": "RE",
        "rieti": "RI", "ri": "RI",
        "rimini": "RN", "rn": "RN",
        "roma": "RM", "rm": "RM", "rome": "RM",
        "rovigo": "RO", "ro": "RO",
        "salerno": "SA", "sa": "SA",
        "sassari": "SS", "ss": "SS",
        "savona": "SV", "sv": "SV",
        "siena": "SI", "si": "SI",
        "siracusa": "SR", "sr": "SR",
        "sondrio": "SO", "so": "SO",
        "sud sardegna": "SU", "su": "SU",
        "taranto": "TA", "ta": "TA",
        "teramo": "TE", "te": "TE",
        "terni": "TR", "tr": "TR",
        "torino": "TO", "to": "TO", "turin": "TO",
        "trapani": "TP", "tp": "TP",
        "trento": "TN", "tn": "TN",
        "treviso": "TV", "tv": "TV",
        "trieste": "TS", "ts": "TS",
        "udine": "UD", "ud": "UD",
        "varese": "VA", "va": "VA",
        "venezia": "VE", "ve": "VE", "venice": "VE",
        "verbano-cusio-ossola": "VB", "vb": "VB",
        "vercelli": "VC", "vc": "VC",
        "verona": "VR", "vr": "VR",
        "vibo valentia": "VV", "vv": "VV",
        "vicenza": "VI", "vi": "VI",
        "viterbo": "VT", "vt": "VT",
    },
    "JP": {
        "hokkaido": "01", "01": "01",
        "aomori": "02", "02": "02",
        "iwate": "03", "03": "03",
        "miyagi": "04", "04": "04",
        "akita": "05", "05": "05",
        "yamagata": "06", "06": "06",
        "fukushima": "07", "07": "07",
        "ibaraki": "08", "08": "08",
        "tochigi": "09", "09": "09",
        "gunma": "10", "10": "10",
        "saitama": "11", "11": "11",
        "chiba": "12", "12": "12",
        "tokyo": "13", "13": "13",
        "kanagawa": "14", "14": "14",
        "niigata": "15", "15": "15",
        "toyama": "16", "16": "16",
        "ishikawa": "17", "17": "17",
        "fukui": "18", "18": "18",
        "yamanashi": "19", "19": "19",
        "nagano": "20", "20": "20",
        "shizuoka": "22", "22": "22",
        "aichi": "23", "23": "23",
        "mie": "24", "24": "24",
        "shiga": "25", "25": "25",
        "kyoto": "26", "26": "26",
        "osaka": "27", "27": "27",
        "hyogo": "28", "28": "28",
        "nara": "29", "29": "29",
        "wakayama": "30", "30": "30",
        "tottori": "31", "31": "31",
        "shimane": "32", "32": "32",
        "okayama": "33", "33": "33",
        "hiroshima": "34", "34": "34",
        "yamaguchi": "35", "35": "35",
        "tokushima": "36", "36": "36",
        "kagawa": "37", "37": "37",
        "ehime": "38", "38": "38",
        "kochi": "39", "39": "39",
        "fukuoka": "40", "40": "40",
        "saga": "41", "41": "41",
        "nagasaki": "42", "42": "42",
        "kumamoto": "43", "43": "43",
        "oita": "44", "44": "44",
        "miyazaki": "45", "45": "45",
        "kagoshima": "46", "46": "46",
        "okinawa": "47", "47": "47",
    },
    "MX": {
        "aguascalientes": "AG", "ag": "AG",
        "baja california": "BC", "bc": "BC",
        "baja california sur": "BS", "bs": "BS",
        "campeche": "CM", "cm": "CM",
        "chiapas": "CS", "cs": "CS",
        "chihuahua": "CH", "ch": "CH",
        "ciudad de méxico": "DF", "ciudad de mexico": "DF", "df": "DF", "mexico city": "DF",
        "coahuila": "CO", "co": "CO",
        "colima": "CL", "cl": "CL",
        "durango": "DG", "dg": "DG",
        "guanajuato": "GT", "gt": "GT",
        "guerrero": "GR", "gr": "GR",
        "hidalgo": "HG", "hg": "HG",
        "jalisco": "JA", "ja": "JA",
        "estado de méxico": "EM", "estado de mexico": "EM", "em": "EM",
        "michoacán": "MI", "michoacan": "MI", "mi": "MI",
        "morelos": "MO", "mo": "MO",
        "nayarit": "NA", "na": "NA",
        "nuevo león": "NL", "nuevo leon": "NL", "nl": "NL",
        "oaxaca": "OA", "oa": "OA",
        "puebla": "PU", "pu": "PU",
        "querétaro": "QT", "queretaro": "QT", "qt": "QT",
        "quintana roo": "QR", "qr": "QR",
        "san luis potosí": "SL", "san luis potosi": "SL", "sl": "SL",
        "sinaloa": "SI", "si": "SI",
        "sonora": "SO", "so": "SO",
        "tabasco": "TB", "tb": "TB",
        "tamaulipas": "TM", "tm": "TM",
        "tlaxcala": "TL", "tl": "TL",
        "veracruz": "VE", "ve": "VE",
        "yucatán": "YU", "yucatan": "YU", "yu": "YU",
        "zacatecas": "ZA", "za": "ZA",
    },
}

SUPPORTED_COUNTRIES = set(STATE_MAPS.keys())


def _as_country_code(country_value):
    """Accept an ISO Alpha-2 code or a country name and return the code.

    The country column holds names when normalize_country.py was run with
    --to name, so the state lookup resolves either form before matching.
    """
    v = (country_value or "").strip()
    if len(v) == 2:
        return v.upper()
    try:
        import normalize_country
        code, status = normalize_country.normalize_country(v)
        if status in ("ok", "fuzzy"):
            return code.upper()
    except Exception:
        pass
    return v.upper()


def code_to_state_name(code, country_code):
    """2-letter code -> the state/province name, within one country's map.

    The maps hold many spellings per code (full name, abbreviation, the code
    itself). The full name is the longest of them, so that is what comes back.
    """
    country = _as_country_code(country_code)
    if country not in SUPPORTED_COUNTRIES:
        return None
    target = (code or "").strip().upper()
    best = None
    for spelling, mapped in STATE_MAPS[country].items():
        if mapped == target and len(spelling) > 2:
            if best is None or len(spelling) > len(best):
                best = spelling
    return best.title() if best else None


def normalize_state(raw_state, country_code):
    """
    Returns (normalized_value, status) where status is one of:
      'ok'          — found in map, replaced
      'unchanged'   — value was empty, left as-is
      'skipped'     — country not in supported list, left as-is
      'unresolved'  — country is supported but state not found in map
    """
    if not raw_state or not raw_state.strip():
        return raw_state, "unchanged"

    country = _as_country_code(country_code)

    if country not in SUPPORTED_COUNTRIES:
        return raw_state, "skipped"

    key = raw_state.lower().strip()
    state_map = STATE_MAPS[country]

    if key in state_map:
        return state_map[key], "ok"

    return raw_state, "unresolved"


def normalize_state_to(raw_state, country_code, to="code"):
    """Resolve to a code first, then render in the requested direction."""
    value, status = normalize_state(raw_state, country_code)
    if to == "name" and status == "ok":
        name = code_to_state_name(value, country_code)
        if name:
            return name, status
        return value, "unresolved"
    return value, status


def main():
    parser = argparse.ArgumentParser(
        description="Normalize state/province values to 2-letter codes or to state names.")
    parser.add_argument("input", help="Input CSV file path")
    parser.add_argument("output", help="Output CSV file path")
    parser.add_argument("--col", required=True, help="Name of the state column in the CSV")
    parser.add_argument("--country-col", required=True, help="Name of the ISO Alpha-2 country column")
    parser.add_argument("--to", choices=["code", "name"], default="code",
                        help="Output form: 'code' for the 2-letter code (default), 'name' for the state name")
    args = parser.parse_args()

    with open(args.input, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames

        if args.col not in fieldnames:
            print(f"ERROR: Column '{args.col}' not found. Available columns: {fieldnames}", file=sys.stderr)
            sys.exit(1)

        if args.country_col not in fieldnames:
            print(f"ERROR: Country column '{args.country_col}' not found. Available columns: {fieldnames}", file=sys.stderr)
            sys.exit(1)

        rows = list(reader)

    status_col = "state_status"
    out_fieldnames = fieldnames + [status_col]

    unresolved = []
    counts = {"ok": 0, "unchanged": 0, "skipped": 0, "unresolved": 0}

    for row in rows:
        raw_state = row[args.col]
        country = row.get(args.country_col, "")
        normalized, status = normalize_state_to(raw_state, country, to=args.to)
        row[args.col] = normalized
        row[status_col] = status
        counts[status] += 1
        if status == "unresolved":
            unresolved.append({"state": raw_state, "country": country})

    with open(args.output, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=out_fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nState normalization complete")
    print(f"  Mapped:                    {counts['ok']}")
    print(f"  Empty (unchanged):         {counts['unchanged']}")
    print(f"  Skipped (unsupported country): {counts['skipped']}")
    print(f"  Unresolved:                {counts['unresolved']}")
    print(f"\nOutput written to: {args.output}")

    if unresolved:
        seen = set()
        print(f"\n⚠️  UNRESOLVED STATE VALUES — resolve manually:")
        for item in unresolved:
            key = (item["state"], item["country"])
            if key not in seen:
                seen.add(key)
                print(f'  Country={item["country"]} | State="{item["state"]}"')
    else:
        print("\n✅ All supported-country state values resolved.")


if __name__ == "__main__":
    main()
