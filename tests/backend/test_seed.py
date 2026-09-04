"""Seed-on-empty contents: industries, countries, companies with locations,
references, news, and logos."""

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


def test_seed_has_references_news_locations_and_logos(client):
    conn = _conn(client)
    for row in conn.execute("SELECT id, name FROM companies").fetchall():
        cid = row["id"]

        refs = conn.execute(
            'SELECT COUNT(*) AS n FROM "references" WHERE company_id = ?', (cid,)
        ).fetchone()["n"]
        assert refs == 2, f"{row['name']} should have exactly two references"

        news = conn.execute(
            "SELECT COUNT(*) AS n, COALESCE(SUM(is_scraped), 0) AS s "
            "FROM news_articles WHERE company_id = ?",
            (cid,),
        ).fetchone()
        assert news["n"] >= 3, f"{row['name']} should have at least three news articles"
        assert news["s"] == 0, f"{row['name']} news should be hand-authored, not scraped"

        logos = conn.execute(
            "SELECT COUNT(*) AS n FROM artifacts "
            "WHERE company_id = ? AND source = 'logo'",
            (cid,),
        ).fetchone()["n"]
        assert logos == 1, f"{row['name']} should have exactly one logo"

        locs = conn.execute(
            "SELECT COUNT(*) AS n FROM locations WHERE company_id = ?", (cid,)
        ).fetchone()["n"]
        assert locs >= 2, f"{row['name']} should have its HQ plus extra locations"
    conn.close()