"""SQLite connection, schema initialization, and seed-on-empty.

The runtime storage root is anchored to the repository root (the parent of the
``backend`` package) rather than the process working directory so the app is
robust regardless of where it is launched from.

Sprint 01 rebuilt the data model (industries, countries, users, sessions,
locations, references, news_articles; ``companies`` now carries ``industry_id``
and has no free-form ``industry``/``hq_location``). The v0.1 database is not
migrated; per scope item u the operator flushes ``data/`` once before the first
run of this build.
"""

import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
_OVERRIDE_DB = os.environ.get("COMPANY_HUB_DB")
if _OVERRIDE_DB:
    DB_PATH = Path(_OVERRIDE_DB)
    ARTIFACTS_DIR = DB_PATH.parent / "artifacts"
else:
    DB_PATH = DATA_DIR / "company_hub.db"
    ARTIFACTS_DIR = DATA_DIR / "artifacts"

SCHEMA = """
CREATE TABLE IF NOT EXISTS industries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS countries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    token TEXT NOT NULL UNIQUE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS companies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    industry_id INTEGER REFERENCES industries(id),
    website TEXT,
    contact_email TEXT,
    contact_phone TEXT,
    description TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS locations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id INTEGER NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    label TEXT NOT NULL,
    address TEXT,
    city TEXT NOT NULL,
    country_code TEXT NOT NULL REFERENCES countries(code),
    type TEXT NOT NULL CHECK (type IN ('Headquarters','Office','Plant','Other'))
);

CREATE TABLE IF NOT EXISTS "references" (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id INTEGER NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    url TEXT NOT NULL,
    description TEXT,
    added_by TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS news_articles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id INTEGER NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    source TEXT NOT NULL,
    url TEXT NOT NULL,
    published_at TEXT NOT NULL,
    summary TEXT,
    is_scraped INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS artifacts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id INTEGER NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    original_name TEXT NOT NULL,
    stored_filename TEXT NOT NULL,
    content_type TEXT NOT NULL,
    size_bytes INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    source TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_locations_company ON locations(company_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_locations_one_hq
    ON locations(company_id) WHERE type = 'Headquarters';
CREATE INDEX IF NOT EXISTS idx_references_company ON "references"(company_id);
CREATE INDEX IF NOT EXISTS idx_news_company ON news_articles(company_id);
CREATE INDEX IF NOT EXISTS idx_artifacts_company ON artifacts(company_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_artifacts_one_logo
    ON artifacts(company_id) WHERE source = 'logo';
"""


def utc_now() -> str:
    """Current UTC time as an ISO-8601 string with a ``Z`` suffix."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def ensure_dirs() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def connection():
    """Short-lived connection committed on success, closed on exit."""
    conn = connect()
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    """Create runtime dirs, apply the schema, and seed when the companies table
    is empty. Idempotent."""
    ensure_dirs()
    with connection() as conn:
        conn.executescript(SCHEMA)
        from backend.data.seed import seed_if_empty

        seed_if_empty(conn)
