"""Sprint 01 seed content.

Seeds the six-industry standard list, the standard country list, and exactly six
real companies (one per seeded industry) each with a single Headquarters
location. Content is backend-authored: the architecture specifies the shape and
quantity (six industries; a curated ~50-100 entry country list covering the G20
plus ``JP``/``KR``/``GB``/``CH``/``FR``; six named companies with structured
fields and one HQ each) but not every value.

Seeding runs only when the ``companies`` table is empty and never overwrites
user-entered data. Country/industry inserts are ``INSERT OR IGNORE`` so a
partially present standard list never crashes a re-seed; companies are inserted
only as part of the empty-``companies`` gate.
"""

from datetime import datetime, timezone

SEED_INDUSTRIES = [
    "Manufacturing",
    "Technology",
    "Finance",
    "Healthcare",
    "Energy",
    "Retail",
]

# Standard country list. Fixed this sprint (no runtime country-management UI).
# ``code`` is the ISO 3166-1 alpha-2 code; the United Kingdom is stored as
# ``GB`` / "United Kingdom" (the scope/brief "UK" maps to this record).
COUNTRIES = {
    "DZ": "Algeria",
    "AR": "Argentina",
    "AU": "Australia",
    "AT": "Austria",
    "AZ": "Azerbaijan",
    "BH": "Bahrain",
    "BD": "Bangladesh",
    "BY": "Belarus",
    "BE": "Belgium",
    "BR": "Brazil",
    "BG": "Bulgaria",
    "CA": "Canada",
    "CL": "Chile",
    "CN": "China",
    "CO": "Colombia",
    "HR": "Croatia",
    "CZ": "Czechia",
    "DK": "Denmark",
    "EG": "Egypt",
    "EE": "Estonia",
    "ET": "Ethiopia",
    "FI": "Finland",
    "FR": "France",
    "DE": "Germany",
    "GH": "Ghana",
    "GR": "Greece",
    "HK": "Hong Kong",
    "HU": "Hungary",
    "IS": "Iceland",
    "IN": "India",
    "ID": "Indonesia",
    "IR": "Iran",
    "IQ": "Iraq",
    "IE": "Ireland",
    "IL": "Israel",
    "IT": "Italy",
    "JP": "Japan",
    "JO": "Jordan",
    "KZ": "Kazakhstan",
    "KE": "Kenya",
    "KR": "South Korea",
    "KW": "Kuwait",
    "LV": "Latvia",
    "LB": "Lebanon",
    "LT": "Lithuania",
    "LU": "Luxembourg",
    "MY": "Malaysia",
    "MT": "Malta",
    "MX": "Mexico",
    "MA": "Morocco",
    "NL": "Netherlands",
    "NZ": "New Zealand",
    "NG": "Nigeria",
    "NO": "Norway",
    "OM": "Oman",
    "PK": "Pakistan",
    "PE": "Peru",
    "PH": "Philippines",
    "PL": "Poland",
    "PT": "Portugal",
    "QA": "Qatar",
    "RO": "Romania",
    "RU": "Russia",
    "SA": "Saudi Arabia",
    "RS": "Serbia",
    "SG": "Singapore",
    "SK": "Slovakia",
    "SI": "Slovenia",
    "ZA": "South Africa",
    "ES": "Spain",
    "LK": "Sri Lanka",
    "SE": "Sweden",
    "CH": "Switzerland",
    "TW": "Taiwan",
    "TH": "Thailand",
    "TR": "Turkey",
    "UA": "Ukraine",
    "AE": "United Arab Emirates",
    "GB": "United Kingdom",
    "US": "United States",
    "UY": "Uruguay",
    "VE": "Venezuela",
    "VN": "Vietnam",
}

# Six real companies — one of the biggest players in each seeded industry.
# Each carries all structured fields plus exactly one Headquarters location.
# Fields are real-world plausible public details; content is backend-authored.
SEED_COMPANIES = [
    {
        "name": "Toyota Motor",
        "industry": "Manufacturing",
        "website": "https://global.toyota",
        "contact_email": "info@global.toyota",
        "contact_phone": "+81 3 3817 7111",
        "description": (
            "Japanese multinational automotive manufacturer and one of the "
            "world's largest carmakers by volume."
        ),
        "hq": {"label": "Global HQ", "city": "Toyota City", "country_code": "JP"},
    },
    {
        "name": "Samsung Electronics",
        "industry": "Technology",
        "website": "https://www.samsung.com",
        "contact_email": "contact@samsung.com",
        "contact_phone": "+82 2 2255 0114",
        "description": (
            "South Korean multinational electronics corporation spanning "
            "consumer electronics, semiconductors, and displays."
        ),
        "hq": {"label": "Global HQ", "city": "Seoul", "country_code": "KR"},
    },
    {
        "name": "HSBC",
        "industry": "Finance",
        "website": "https://www.hsbc.com",
        "contact_email": "contact@hsbc.com",
        "contact_phone": "+44 20 7991 8888",
        "description": (
            "British universal bank and financial services group headquartered "
            "in London."
        ),
        "hq": {"label": "Global HQ", "city": "London", "country_code": "GB"},
    },
    {
        "name": "Novartis",
        "industry": "Healthcare",
        "website": "https://www.novartis.com",
        "contact_email": "info@novartis.com",
        "contact_phone": "+41 61 324 1111",
        "description": (
            "Swiss multinational pharmaceutical and biotechnology company."
        ),
        "hq": {"label": "Global HQ", "city": "Basel", "country_code": "CH"},
    },
    {
        "name": "Shell",
        "industry": "Energy",
        "website": "https://www.shell.com",
        "contact_email": "contact@shell.com",
        "contact_phone": "+44 20 7934 1234",
        "description": (
            "British multinational oil and gas company with operations across "
            "the energy value chain."
        ),
        "hq": {"label": "Global HQ", "city": "London", "country_code": "GB"},
    },
    {
        "name": "Carrefour",
        "industry": "Retail",
        "website": "https://www.carrefour.com",
        "contact_email": "contact@carrefour.com",
        "contact_phone": "+33 1 41 04 26 26",
        "description": (
            "French multinational retail and wholesaling corporation and one "
            "of the world's largest grocery chains."
        ),
        "hq": {"label": "Global HQ", "city": "Paris", "country_code": "FR"},
    },
]


def _seed_timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def seed_if_empty(conn) -> None:
    """Insert industries, countries, and the six companies (each with one
    Headquarters location) only when the companies table is empty."""
    count = conn.execute("SELECT COUNT(*) AS n FROM companies").fetchone()["n"]
    if count > 0:
        return
    now = _seed_timestamp()

    industry_ids: dict[str, int] = {}
    for name in SEED_INDUSTRIES:
        conn.execute(
            "INSERT OR IGNORE INTO industries (name, created_at) VALUES (?, ?)",
            (name, now),
        )
        row = conn.execute(
            "SELECT id FROM industries WHERE name = ?", (name,)
        ).fetchone()
        industry_ids[name] = row["id"]

    for code, name in sorted(COUNTRIES.items(), key=lambda kv: kv[1].lower()):
        conn.execute(
            "INSERT OR IGNORE INTO countries (code, name, created_at) "
            "VALUES (?, ?, ?)",
            (code, name, now),
        )

    for company in SEED_COMPANIES:
        cur = conn.execute(
            "INSERT INTO companies (name, industry_id, website, contact_email, "
            "contact_phone, description, created_at, updated_at) "
            "VALUES (:name, :industry_id, :website, :contact_email, "
            ":contact_phone, :description, :created_at, :updated_at)",
            {
                "name": company["name"],
                "industry_id": industry_ids[company["industry"]],
                "website": company["website"],
                "contact_email": company["contact_email"],
                "contact_phone": company["contact_phone"],
                "description": company["description"],
                "created_at": now,
                "updated_at": now,
            },
        )
        hq = company["hq"]
        conn.execute(
            "INSERT INTO locations (company_id, label, address, city, "
            "country_code, type) VALUES (?, ?, NULL, ?, ?, 'Headquarters')",
            (cur.lastrowid, hq["label"], hq["city"], hq["country_code"]),
        )
