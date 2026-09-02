"""Seed companies (structured data only, no artifacts).

Content is backend-authored placeholder data: a small set of realistic firms
used so the app has a sensible starting state. It is inserted only when the
``companies`` table is empty and never overwrites user-entered data.
"""

from datetime import datetime, timezone

SEED_COMPANIES = [
    {
        "name": "Acme Manufacturing",
        "industry": "Manufacturing",
        "hq_location": "Berlin, DE",
        "website": "https://acme.example.com",
        "contact_email": "hello@acme.example.com",
        "contact_phone": "+49 30 1234 5678",
        "description": "Industrial components and precision machining for European OEMs.",
    },
    {
        "name": "Bluewave Logistics",
        "industry": "Logistics & Supply Chain",
        "hq_location": "Rotterdam, NL",
        "website": "https://bluewave.example.nl",
        "contact_email": "ops@bluewave.example.nl",
        "contact_phone": "+31 10 456 7890",
        "description": "Ocean and road freight forwarding with cold-chain specialization.",
    },
    {
        "name": "Cobalt Energy Partners",
        "industry": "Energy",
        "hq_location": "Houston, US",
        "website": "https://cobalt.example.com",
        "contact_email": "ir@cobalt.example.com",
        "contact_phone": "+1 713 555 0134",
        "description": "Renewable energy asset development and project financing.",
    },
    {
        "name": "Nakamura Robotics",
        "industry": "Robotics & Automation",
        "hq_location": "Osaka, JP",
        "website": "https://nakamura.example.jp",
        "contact_email": "sales@nakamura.example.jp",
        "contact_phone": "+81 6 9876 5432",
        "description": "Industrial automation arms and vision systems for factories.",
    },
    {
        "name": "Verde Agro",
        "industry": "Agriculture",
        "hq_location": "São Paulo, BR",
        "website": "https://verde.example.br",
        "contact_email": "comercial@verde.example.br",
        "contact_phone": "+55 11 2345 6789",
        "description": "Sustainable soy and coffee sourcing across South America.",
    },
    {
        "name": "Lumen Financial",
        "industry": "Financial Services",
        "hq_location": "London, UK",
        "website": "https://lumen.example.co.uk",
        "contact_email": "contact@lumen.example.co.uk",
        "contact_phone": "+44 20 7123 4567",
        "description": "Corporate treasury advisory and cross-border payment services.",
    },
]


def seed_if_empty(conn) -> None:
    """Insert seed companies only when the companies table is empty."""
    count = conn.execute("SELECT COUNT(*) AS n FROM companies").fetchone()["n"]
    if count > 0:
        return
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    for company in SEED_COMPANIES:
        conn.execute(
            "INSERT INTO companies (name, industry, hq_location, website, "
            "contact_email, contact_phone, description, created_at, updated_at) "
            "VALUES (:name, :industry, :hq_location, :website, :contact_email, "
            ":contact_phone, :description, :created_at, :updated_at)",
            {**company, "created_at": now, "updated_at": now},
        )