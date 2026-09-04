"""Seed-on-empty contents: industries, countries, companies + one HQ each."""

from backend import db as db_module
from backend.data.seed import SEED_COMPANIES, SEED_INDUSTRIES


def _conn(client):
    return db_module.connect()


def test_seeded_industries(client):
    conn = _conn(client)
    rows = conn.execute("SELECT name FROM industries ORDER BY name").fetchall()
    assert [r["name"] for r in rows] == sorted(SEED_INDUSTRIES)
    conn.close()


def test_seeded_countries(client):
    conn = _conn(client)
    rows = conn.execute("SELECT code, name FROM countries").fetchall()
    assert len(rows) == 83
    assert {"code": "GB", "name": "United Kingdom"} in [dict(r) for r in rows]
    conn.close()


def test_seeded_companies_each_with_one_headquarters(client):
    conn = _conn(client)
    companies = conn.execute("SELECT id, name FROM companies").fetchall()
    assert len(companies) == 6
    assert {r["name"] for r in companies} == {c["name"] for c in SEED_COMPANIES}

    for row in companies:
        hqs = conn.execute(
            "SELECT COUNT(*) AS n FROM locations WHERE company_id = ? AND type = 'Headquarters'",
            (row["id"],),
        ).fetchone()["n"]
        assert hqs == 1, f"{row['name']} should have exactly one HQ"
    conn.close()


def test_seed_has_no_references_news_logos_or_artifacts(client):
    conn = _conn(client)
    for table in ("\"references\"", "news_articles", "artifacts"):
        n = conn.execute(f"SELECT COUNT(*) AS n FROM {table}").fetchone()["n"]
        assert n == 0, f"{table} should be empty at seed"
    conn.close()