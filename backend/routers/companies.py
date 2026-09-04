"""Company CRUD + profile payloads.

Company payloads resolve controlled data at read time: ``industry`` is nested
``{id, name}``, ``hq_location`` is derived from the Headquarters location
(never stored), and ``logo_url`` points at the stored logo object. The generic
``artifacts_count`` excludes ``source = 'logo'`` rows.
"""

from fastapi import APIRouter, HTTPException

from backend.db import connection, utc_now
from backend.models import (
    artifact_to_dict,
    company_is_complete,
    location_to_dict,
    news_to_dict,
    reference_to_dict,
)
from backend.schemas import CompanyIn
from backend.services import storage

router = APIRouter(prefix="/companies", tags=["companies"])

_COMPANY_FIELDS = (
    "name",
    "industry_id",
    "website",
    "contact_email",
    "contact_phone",
    "description",
)


def _industry_map(conn) -> dict:
    return {
        r["id"]: {"id": r["id"], "name": r["name"]}
        for r in conn.execute("SELECT id, name FROM industries")
    }


def _counts_map(conn, company_ids: list[int]) -> dict:
    if not company_ids:
        return {}
    placeholders = ",".join("?" for _ in company_ids)
    rows = conn.execute(
        "SELECT company_id, COUNT(*) AS n FROM artifacts "
        f"WHERE company_id IN ({placeholders}) AND source != 'logo' "
        "GROUP BY company_id",
        company_ids,
    ).fetchall()
    return {r["company_id"]: r["n"] for r in rows}


def _hq_map(conn, company_ids: list[int]) -> dict:
    """Map company_id -> \"<city>, <country_code>\" of its Headquarters."""
    if not company_ids:
        return {}
    placeholders = ",".join("?" for _ in company_ids)
    rows = conn.execute(
        "SELECT company_id, city, country_code FROM locations "
        f"WHERE company_id IN ({placeholders}) AND type = 'Headquarters' "
        "ORDER BY id",
        company_ids,
    ).fetchall()
    result: dict = {}
    for r in rows:
        result.setdefault(r["company_id"], f"{r['city']}, {r['country_code']}")
    return result


def _logo_map(conn, company_ids: list[int]) -> dict:
    if not company_ids:
        return {}
    placeholders = ",".join("?" for _ in company_ids)
    rows = conn.execute(
        "SELECT company_id, id FROM artifacts "
        f"WHERE company_id IN ({placeholders}) AND source = 'logo' ORDER BY id",
        company_ids,
    ).fetchall()
    result: dict = {}
    for r in rows:
        result.setdefault(r["company_id"], f"/api/artifacts/{r['id']}/content")
    return result


def _company_item(row, counts, industry_map, hq_map, logo_map) -> dict:
    return {
        "id": row["id"],
        "name": row["name"],
        "industry": industry_map.get(row["industry_id"]),
        "hq_location": hq_map.get(row["id"]),
        "website": row["website"],
        "contact_email": row["contact_email"],
        "contact_phone": row["contact_phone"],
        "description": row["description"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
        "is_complete": company_is_complete(row),
        "artifacts_count": counts.get(row["id"], 0),
        "logo_url": logo_map.get(row["id"]),
    }


def _items_for(conn, company_ids: list[int]) -> dict:
    counts = _counts_map(conn, company_ids)
    industry_map = _industry_map(conn)
    hq_map = _hq_map(conn, company_ids)
    logo_map = _logo_map(conn, company_ids)
    return counts, industry_map, hq_map, logo_map


def _fetch_company_row(conn, company_id: int):
    row = conn.execute(
        "SELECT * FROM companies WHERE id = ?", (company_id,)
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Company not found")
    return row


def _validate_industry(conn, industry_id: int | None) -> None:
    if industry_id is None:
        return
    row = conn.execute(
        "SELECT id FROM industries WHERE id = ?", (industry_id,)
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=422, detail="Unknown industry_id")


@router.get("")
def list_companies(q: str | None = None, countries: str | None = None):
    sql = "SELECT c.* FROM companies c"
    where: list[str] = []
    params: list = []
    if q:
        where.append("c.name LIKE ? COLLATE NOCASE")
        params.append(f"%{q}%")
    codes = [c.strip() for c in countries.split(",")] if countries is not None else None
    codes = [c for c in codes if c] if codes is not None else None
    if codes:
        placeholders = ",".join("?" for _ in codes)
        where.append(
            "c.id IN (SELECT company_id FROM locations "
            f"WHERE country_code IN ({placeholders}))"
        )
        params.extend(codes)
    elif countries is not None:
        # Filter present but no valid codes: active filter matching nothing.
        where.append("1 = 0")
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY c.id ASC"
    with connection() as conn:
        rows = conn.execute(sql, params).fetchall()
        ids = [r["id"] for r in rows]
        counts, industry_map, hq_map, logo_map = _items_for(conn, ids)
        return [_company_item(r, counts, industry_map, hq_map, logo_map) for r in rows]


@router.post("", status_code=201)
def create_company(payload: CompanyIn):
    values = {f: getattr(payload, f) for f in _COMPANY_FIELDS}
    with connection() as conn:
        _validate_industry(conn, payload.industry_id)
        cur = conn.execute(
            "INSERT INTO companies (name, industry_id, website, contact_email, "
            "contact_phone, description, created_at, updated_at) "
            "VALUES (:name, :industry_id, :website, :contact_email, "
            ":contact_phone, :description, :created_at, :updated_at)",
            {**values, "created_at": utc_now(), "updated_at": utc_now()},
        )
        row = conn.execute(
            "SELECT * FROM companies WHERE id = ?", (cur.lastrowid,)
        ).fetchone()
        counts, industry_map, hq_map, logo_map = _items_for(conn, [row["id"]])
        return _company_item(row, counts, industry_map, hq_map, logo_map)


@router.get("/{company_id}")
def get_company(company_id: int):
    with connection() as conn:
        row = _fetch_company_row(conn, company_id)
        counts, industry_map, hq_map, logo_map = _items_for(conn, [company_id])
        data = _company_item(row, counts, industry_map, hq_map, logo_map)
        data["locations"] = [
            location_to_dict(l, l["country_name"])
            for l in conn.execute(
                "SELECT l.*, (SELECT name FROM countries c WHERE c.code = "
                "l.country_code) AS country_name FROM locations l "
                "WHERE l.company_id = ? ORDER BY l.id ASC",
                (company_id,),
            )
        ]
        data["references"] = [
            reference_to_dict(r)
            for r in conn.execute(
                "SELECT * FROM \"references\" WHERE company_id = ? ORDER BY id DESC",
                (company_id,),
            )
        ]
        data["news"] = [
            news_to_dict(r)
            for r in conn.execute(
                "SELECT * FROM news_articles WHERE company_id = ? ORDER BY id DESC",
                (company_id,),
            )
        ]
        data["artifacts"] = [
            artifact_to_dict(a)
            for a in conn.execute(
                "SELECT * FROM artifacts WHERE company_id = ? AND source != 'logo' "
                "ORDER BY id DESC",
                (company_id,),
            )
        ]
        return data


@router.put("/{company_id}")
def update_company(company_id: int, payload: CompanyIn):
    values = {f: getattr(payload, f) for f in _COMPANY_FIELDS}
    with connection() as conn:
        _fetch_company_row(conn, company_id)
        _validate_industry(conn, payload.industry_id)
        conn.execute(
            "UPDATE companies SET name = :name, industry_id = :industry_id, "
            "website = :website, contact_email = :contact_email, "
            "contact_phone = :contact_phone, description = :description, "
            "updated_at = :updated_at WHERE id = :id",
            {**values, "id": company_id, "updated_at": utc_now()},
        )
        row = conn.execute(
            "SELECT * FROM companies WHERE id = ?", (company_id,)
        ).fetchone()
        counts, industry_map, hq_map, logo_map = _items_for(conn, [company_id])
        return _company_item(row, counts, industry_map, hq_map, logo_map)


@router.delete("/{company_id}", status_code=204)
def delete_company(company_id: int):
    with connection() as conn:
        _fetch_company_row(conn, company_id)
        conn.execute("DELETE FROM companies WHERE id = ?", (company_id,))
    storage.delete_company_dir(company_id)
    return None
