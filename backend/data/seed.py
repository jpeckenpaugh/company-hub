"""Sprint 01 seed content, enriched with real references, news, locations, and
logos.

Seeds the six-industry standard list, the standard country list, and exactly six
real companies (one per seeded industry). Each company carries all structured
fields, a Headquarters location, one or two further real locations, two curated
references (a Wikipedia article and an official about/company-profile page),
four or five genuine recent news articles (``is_scraped = 0`` — hand-authored,
not scraped), and a raster logo whose bytes are committed under
``backend/data/logos/`` and copied into artifact storage at seed time.

Content is backend-authored: the architecture specifies the shape and quantity
(six industries; a curated ~50-100 entry country list covering the G20 plus
``JP``/``KR``/``GB``/``CH``/``FR``; six named companies with structured fields,
one HQ and a few locations each, two references, several news articles, and one
logo) but not every value. References use ``added_by = admin@localhost`` to mark
them as backend-seeded rather than user-added.

Seeding runs only when the ``companies`` table is empty and never overwrites
user-entered data. Country/industry inserts are ``INSERT OR IGNORE`` so a
partially present standard list never crashes a re-seed; companies are inserted
only as part of the empty-``companies`` gate.
"""

from datetime import datetime, timezone
from pathlib import Path

from backend.services import storage

_SEED_LOGOS_DIR = Path(__file__).resolve().parent / "logos"

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

# Additional real locations per company (the Headquarters already comes from
# ``SEED_COMPANIES``). Deliberately avoids adding GB/FR locations to companies
# that are not headquartered there so the country-filter results stay stable.
SEED_EXTRA_LOCATIONS = {
    "Toyota Motor": [
        {"label": "Tokyo Head Office", "address": "1-4-18 Koraku, Bunkyo-ku",
         "city": "Tokyo", "country_code": "JP", "type": "Office"},
        {"label": "Nagoya Office", "address": "4-7-1 Meieki, Nakamura-ku",
         "city": "Nagoya", "country_code": "JP", "type": "Office"},
        {"label": "Toyota Motor Manufacturing Kentucky",
         "address": "1001 Cherry Blossom Way", "city": "Georgetown",
         "country_code": "US", "type": "Plant"},
    ],
    "Samsung Electronics": [
        {"label": "Samsung Electronics America HQ",
         "address": "85 Challenger Road", "city": "Ridgefield Park",
         "country_code": "US", "type": "Office"},
        {"label": "Samsung R&D Institute India", "city": "Bangalore",
         "country_code": "IN", "type": "Office"},
    ],
    "HSBC": [
        {"label": "HSBC Hong Kong", "address": "1 Queen's Road Central",
         "city": "Hong Kong", "country_code": "HK", "type": "Office"},
        {"label": "HSBC Bank USA HQ", "address": "452 Fifth Avenue",
         "city": "New York", "country_code": "US", "type": "Office"},
    ],
    "Novartis": [
        {"label": "Novartis US HQ", "address": "One Health Plaza",
         "city": "East Hanover", "country_code": "US", "type": "Office"},
        {"label": "Novartis Corporate Center", "city": "Hyderabad",
         "country_code": "IN", "type": "Office"},
    ],
    "Shell": [
        {"label": "Shell International B.V.", "address": "Carel van Bylandtlaan 16",
         "city": "The Hague", "country_code": "NL", "type": "Office"},
        {"label": "Shell USA HQ", "address": "150 N. Dairy Ashford Road",
         "city": "Houston", "country_code": "US", "type": "Office"},
    ],
    "Carrefour": [
        {"label": "Carrefour Spain HQ", "city": "Madrid",
         "country_code": "ES", "type": "Office"},
        {"label": "Carrefour Brazil HQ", "city": "São Paulo",
         "country_code": "BR", "type": "Office"},
    ],
}

# Two curated references per company: a Wikipedia article and an official
# about/company-profile page. ``added_by`` is fixed to ``admin@localhost`` at
# insert time.
SEED_REFERENCES = {
    "Toyota Motor": [
        {"title": "Toyota Motor Corporation — Wikipedia",
         "url": "https://en.wikipedia.org/wiki/Toyota_Motor_Corporation",
         "description": "Overview of Toyota Motor Corporation: history, products, financials, and global operations."},
        {"title": "Company Profile — Toyota Global",
         "url": "https://global.toyota/en/company/profile/overview/index.html",
         "description": "Official company profile with head office locations, employee counts, and key corporate facts."},
    ],
    "Samsung Electronics": [
        {"title": "Samsung Electronics — Wikipedia",
         "url": "https://en.wikipedia.org/wiki/Samsung_Electronics",
         "description": "Overview of Samsung Electronics: history, business divisions, products, and financials."},
        {"title": "About Us — Samsung",
         "url": "https://www.samsung.com/us/about-us/company-info/",
         "description": "Samsung's official about page covering its business areas and corporate facts."},
    ],
    "HSBC": [
        {"title": "HSBC — Wikipedia",
         "url": "https://en.wikipedia.org/wiki/HSBC",
         "description": "Overview of HSBC Holdings: history, global footprint, and financial data."},
        {"title": "Who we are — HSBC",
         "url": "https://www.hsbc.com/who-we-are",
         "description": "HSBC's official overview of its businesses, strategy, and global reach."},
    ],
    "Novartis": [
        {"title": "Novartis — Wikipedia",
         "url": "https://en.wikipedia.org/wiki/Novartis",
         "description": "Overview of Novartis: history, therapeutic areas, and financial information."},
        {"title": "About us — Novartis",
         "url": "https://www.novartis.com/about-us",
         "description": "Novartis's official about page covering strategy, innovation, and key facts."},
    ],
    "Shell": [
        {"title": "Shell plc — Wikipedia",
         "url": "https://en.wikipedia.org/wiki/Shell_plc",
         "description": "Overview of Shell plc: history, business model, and financial data."},
        {"title": "Who we are — Shell",
         "url": "https://www.shell.com/who-we-are.html",
         "description": "Shell's official overview of the company, its people, and how it operates."},
    ],
    "Carrefour": [
        {"title": "Carrefour — Wikipedia",
         "url": "https://en.wikipedia.org/wiki/Carrefour",
         "description": "Overview of Carrefour: history, formats, and global presence."},
        {"title": "About the group — Carrefour",
         "url": "https://www.carrefour.com/en/group",
         "description": "Carrefour's official group page with store counts, revenue, and employees."},
    ],
}

# Genuine recent news articles per company (all 2026, ``is_scraped = 0``).
SEED_NEWS = {
    "Toyota Motor": [
        {"title": "Toyota weighs hydrogen power for trucks that ship auto parts",
         "source": "The Japan Times", "url": "https://www.japantimes.co.jp/business/2026/09/04/companies/toyota-hydrogen-trucks/",
         "published_at": "2026-09-04",
         "summary": "Toyota is considering hydrogen power for trucks shipping auto parts and, eventually, its factories as alternative fuels gain favor after the Iran war pushed up fuel prices."},
        {"title": "Toyota delays launch of Highlander EV, its first US-made electric",
         "source": "Nikkei Asia", "url": "https://asia.nikkei.com/business/automobiles/electric-vehicles/toyota-delays-launch-of-highlander-ev-its-first-us-made-electric",
         "published_at": "2026-09-03",
         "summary": "Toyota pushed the launch of its first US-built electric vehicle — the Highlander EV — to 2027 or later because of delays in starting production."},
        {"title": "Japan's Toyota reports hefty profit on cheap yen, car sales",
         "source": "AP News", "url": "https://apnews.com/article/toyota-japan-automakers-earnings-currencyhormuz-8745600b3a3c8b5239d63d9892b56f9c",
         "published_at": "2026-08-04",
         "summary": "Toyota's fiscal first-quarter net profit nearly doubled to 1.48 trillion yen ($9.4 billion) on solid US and India demand and a favorable exchange rate."},
        {"title": "Trump's Canada tariffs likely to hit Toyota and Honda profits, analysts say",
         "source": "Nikkei Asia", "url": "https://asia.nikkei.com/business/automobiles/trump-s-canada-tariffs-likely-to-hit-toyota-and-honda-profits-analysts-say",
         "published_at": "2026-09-04",
         "summary": "Analysts expect US President Trump's 50% tariff on vehicles produced in Canada to hit profits at Toyota and Honda, which both manufacture there."},
    ],
    "Samsung Electronics": [
        {"title": "Top Traders Pile Into Samsung Electronics on Payout Hopes",
         "source": "Seoul Economic Daily", "url": "https://en.sedaily.com/news/2026/09/04/top-traders-pile-into-samsung-electronics-on-payout-hopes",
         "published_at": "2026-09-04",
         "summary": "High-return traders piled into Samsung Electronics shares on expectations of further shareholder returns from the company's record, AI-fueled profits."},
        {"title": "Samsung asked to pay $15B in advance for power",
         "source": "Reuters via The Manila Times", "url": "https://www.manilatimes.net/2026/09/04/business/foreign-business/samsung-asked-to-pay-15b-in-advance-for-power/2418241",
         "published_at": "2026-09-04",
         "summary": "Korea Electric Power Corp. proposed Samsung Electronics pay 20 trillion won ($15 billion) in advance for power through 2031 to help fund grid expansion for chip fabs."},
        {"title": "Samsung Unveils 'CUBE' Strategy to Break AI Chip Limits",
         "source": "Seoul Economic Daily", "url": "https://en.sedaily.com/finance/2026/09/02/samsung-unveils-cube-strategy-to-break-ai-chip-limits",
         "published_at": "2026-09-02",
         "summary": "Samsung presented its 'CUBE' memory strategy at SEMICON Taiwan 2026, optimizing logic-memory placement and outlining a roadmap through eighth-generation HBM5."},
        {"title": "Build in US or pay: Trump revives chip tariff threat",
         "source": "The Korea Herald", "url": "https://www.koreaherald.com/article/10861765",
         "published_at": "2026-09-03",
         "summary": "The Trump administration revived targeted semiconductor tariffs, pressing Samsung and SK hynix to expand US production; their combined $41 billion in US projects may or may not qualify for relief."},
    ],
    "HSBC": [
        {"title": "HSBC Holdings plc Interim Results 2026",
         "source": "HSBC", "url": "https://www.hsbc.com/news-and-views/news/media-releases/2026/hsbc-holdings-plc-interim-results-2026",
         "published_at": "2026-08-04",
         "summary": "HSBC reported first-half 2026 profit before tax up 23% to $19.5 billion, approved a second interim dividend of $0.10 per share, and announced a share buy-back of up to $1 billion."},
        {"title": "BNP Paribas, HSBC Complete Swift Blockchain Treasury Payment",
         "source": "CoinTrust", "url": "https://www.cointrust.com/market-news/bnp-paribas-hsbc-complete-swift-blockchain-treasury-payment",
         "published_at": "2026-09-04",
         "summary": "BNP Paribas and HSBC completed the first corporate treasury payment using Swift's blockchain-based shared ledger, moving funds for Siemens between euro and sterling accounts."},
        {"title": "HSBC shares carry 'sell' rating as broker says valuation leaves no room for disappointment",
         "source": "Proactive Investors", "url": "https://www.proactiveinvestors.com/companies/news/1098051/hsbc-shares-carry-sell-rating-as-broker-says-valuation-leaves-no-room-for-disappointment-1098051.html",
         "published_at": "2026-09-03",
         "summary": "Shore Capital reiterated a sell rating on HSBC, warning the shares' valuation leaves no room for disappointment after a 62% rise over the past 12 months."},
    ],
    "Novartis": [
        {"title": "Novartis remibrutinib, a high-efficacy oral BTK inhibitor, significantly reduces relapse rates in Phase III RMS trials",
         "source": "Novartis", "url": "https://www.novartis.com/news/media-releases/novartis-remibrutinib-high-efficacy-oral-btk-inhibitor-significantly-reduces-relapse-rates-and-shows-favorable-safety-profile-phase-iii-rms-trials",
         "published_at": "2026-09-01",
         "summary": "Novartis reported positive Phase III REMODEL-1/-2 results showing its oral BTK inhibitor remibrutinib significantly reduced relapse rates in relapsing multiple sclerosis versus teriflunomide."},
        {"title": "Novartis signs $3.2bn drug delivery agreement with Alteogen",
         "source": "Pharmaceutical Technology", "url": "https://www.pharmaceutical-technology.com/news/novartis-3bn-agreement-alteogen-drug-delivery/",
         "published_at": "2026-09-03",
         "summary": "Novartis signed an agreement with Alteogen worth up to $3.22 billion for exclusive global rights to develop subcutaneous formulations using Alteogen's ALT-B4 technology."},
        {"title": "Novartis to cut up to 130 Basel jobs in biologics restructuring",
         "source": "Swiss Observer", "url": "https://swissobserver.com/news/novartis-to-cut-130-basel-jobs-in-biologics-restructuring/",
         "published_at": "2026-09-03",
         "summary": "Novartis plans to cut up to 130 Basel jobs by the end of 2027 as it winds down small-scale biologics production at its Kleinbasel site."},
        {"title": "Novartis halts clinical trials following patient deaths",
         "source": "SWI swissinfo.ch", "url": "https://www.swissinfo.ch/eng/pharma-supply-chains/novartis-halts-clinical-trials-following-patient-deaths/91987556",
         "published_at": "2026-09-01",
         "summary": "Novartis paused eight clinical trials of its experimental CAR-T therapy rap-cel in autoimmune and neurological indications after three patients died from a severe immune reaction."},
    ],
    "Shell": [
        {"title": "Shell completes acquisition of ARC Resources",
         "source": "Shell / PR Newswire", "url": "https://www.prnewswire.com/news-releases/shell-completes-acquisition-of-arc-resources-302868173.html",
         "published_at": "2026-09-02",
         "summary": "Shell completed its acquisition of Canada's ARC Resources, adding about 370 kboe/d across liquids and gas and strengthening its position in the Montney basin."},
        {"title": "Shell Takes Stakes in BP Exploration Prospects in Brazil and the U.S. Gulf",
         "source": "OilPrice.com", "url": "https://oilprice.com/Company-News/Shell-Takes-Stakes-in-BP-Exploration-Prospects-in-Brazil-and-the-US-Gulf.html",
         "published_at": "2026-09-02",
         "summary": "Shell will take a 50% interest in the Tupinambá block offshore Brazil and a 30% interest in five US Gulf leases containing the Conifer prospect, with BP remaining operator."},
        {"title": "ECOnnect Energy to Deliver Shell-Backed LNG Project in Bahamas",
         "source": "Rigzone", "url": "https://www.rigzone.com/news/econnect_energy_to_deliver_shellbacked_lng_project_in_bahamas-05-aug-2026-184299-article/",
         "published_at": "2026-08-05",
         "summary": "ECOnnect Energy won a contract to deliver a floating LNG import terminal for Shell's New Providence Gas joint venture in the Bahamas."},
        {"title": "ACMobility, Shell open 8 EV charging hubs across the Philippines",
         "source": "The Manila Times", "url": "https://www.manilatimes.net/2026/08/03/tmt-newswire/acmobility-shell-open-8-ev-charging-hubs-across/2396518",
         "published_at": "2026-08-03",
         "summary": "ACMobility and Shell Pilipinas opened eight EV charging hubs at Shell Mobility stations across the Philippines, part of a plan for 50 stations with more than 100 charge points."},
    ],
    "Carrefour": [
        {"title": "Carrefour re-enters India with Indian partner Apparel Group",
         "source": "The Hindu BusinessLine", "url": "https://www.thehindubusinessline.com/companies/carrefour-re-enters-india-with-indian-partner-apparel-group/article71424800.ece",
         "published_at": "2026-09-03",
         "summary": "Carrefour re-entered the Indian market with Dubai-based Apparel Group, opening its first store in Greater Noida and planning 50 stores in three years."},
        {"title": "Carrefour eyes acquisitions to accelerate India expansion",
         "source": "The Economic Times", "url": "https://economictimes.indiatimes.com/industry/services/retail/carrefour-eyes-acquisitions-to-accelerate-india-expansion/articleshow/133741555.cms",
         "published_at": "2026-09-03",
         "summary": "Carrefour is weighing acquisitions of struggling food retailers in India to expand faster than its announced 50-store target, after re-entering via a franchise partnership."},
        {"title": "ChatGPT Shopping Assistant Rolled Out By Carrefour Belgium",
         "source": "ESM Magazine", "url": "https://www.esmmagazine.com/technology/carrefour-belgium-rolls-out-chatgpt-shopping-assistant-320121",
         "published_at": "2026-09-04",
         "summary": "Carrefour Belgium launched a smart shopping assistant within ChatGPT, developed with Mealz.ai — the first such integration in the country."},
        {"title": "Carrefour returns to growth in Brazil, improves profitability in Q2",
         "source": "Valor International", "url": "https://valorinternational.globo.com/business/news/2026/07/24/carrefour-returns-to-growth-in-brazil-improves-profitability-in-q2.ghtml",
         "published_at": "2026-07-24",
         "summary": "Carrefour returned to sales growth in Brazil in Q2 2026 and improved profitability, with first-half recurring operating income up 5.8% to €359 million."},
    ],
}

# One raster logo per company. Bytes are committed under ``backend/data/logos/``
# (PNG so the PDF service can embed them) and copied into artifact storage at
# seed time with ``source = 'logo'``.
SEED_LOGOS = {
    "Toyota Motor": {"file": "toyota.png"},
    "Samsung Electronics": {"file": "samsung.png"},
    "HSBC": {"file": "hsbc.png"},
    "Novartis": {"file": "novartis.png"},
    "Shell": {"file": "shell.png"},
    "Carrefour": {"file": "carrefour.png"},
}


def _seed_timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def seed_if_empty(conn) -> None:
    """Insert industries, countries, and the six companies — each with a
    Headquarters location, extra locations, references, news, and a logo — only
    when the companies table is empty."""
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
        company_id = cur.lastrowid
        hq = company["hq"]
        conn.execute(
            "INSERT INTO locations (company_id, label, address, city, "
            "country_code, type) VALUES (?, ?, NULL, ?, ?, 'Headquarters')",
            (company_id, hq["label"], hq["city"], hq["country_code"]),
        )

        for loc in SEED_EXTRA_LOCATIONS.get(company["name"], []):
            conn.execute(
                "INSERT INTO locations (company_id, label, address, city, "
                "country_code, type) VALUES (?, ?, ?, ?, ?, ?)",
                (
                    company_id,
                    loc["label"],
                    loc.get("address"),
                    loc["city"],
                    loc["country_code"],
                    loc["type"],
                ),
            )

        for ref in SEED_REFERENCES.get(company["name"], []):
            conn.execute(
                "INSERT INTO \"references\" (company_id, title, url, description, "
                "added_by, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    company_id,
                    ref["title"],
                    ref["url"],
                    ref.get("description"),
                    "admin@localhost",
                    now,
                    now,
                ),
            )

        for article in SEED_NEWS.get(company["name"], []):
            conn.execute(
                "INSERT INTO news_articles (company_id, title, source, url, "
                "published_at, summary, is_scraped, created_at, updated_at) "
                "VALUES (?, ?, ?, ?, ?, ?, 0, ?, ?)",
                (
                    company_id,
                    article["title"],
                    article["source"],
                    article["url"],
                    article["published_at"],
                    article.get("summary"),
                    now,
                    now,
                ),
            )

        logo = SEED_LOGOS.get(company["name"])
        if logo is not None:
            logo_path = _SEED_LOGOS_DIR / logo["file"]
            if logo_path.is_file():
                content = logo_path.read_bytes()
                stored_filename = f"seed-logo{logo_path.suffix}"
                storage.save(company_id, stored_filename, content)
                conn.execute(
                    "INSERT INTO artifacts (company_id, original_name, "
                    "stored_filename, content_type, size_bytes, created_at, "
                    "source) VALUES (?, ?, ?, ?, ?, ?, 'logo')",
                    (
                        company_id,
                        logo_path.name,
                        stored_filename,
                        logo.get("content_type", "image/png"),
                        len(content),
                        now,
                    ),
                )
