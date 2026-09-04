"""Industry reference data: list, add, and rename (no delete this sprint).

Industries are controlled references: companies store ``industry_id`` and never
the label, so a rename resolves everywhere automatically. Duplicate detection is
case-insensitive at the application layer so the controlled vocabulary cannot
accumulate case-variant near-duplicates.
"""

from fastapi import APIRouter, HTTPException

from backend.db import connection, utc_now
from backend.schemas import IndustryIn

router = APIRouter(prefix="/industries", tags=["industries"])

_LIST_ORDER = "ORDER BY name COLLATE NOCASE, name"


def _fetch_industry(conn, industry_id: int):
    row = conn.execute(
        "SELECT id, name FROM industries WHERE id = ?", (industry_id,)
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Industry not found")
    return row


def _existing_id_named(conn, name: str) -> int | None:
    row = conn.execute(
        "SELECT id FROM industries WHERE name = ? COLLATE NOCASE", (name,)
    ).fetchone()
    return row["id"] if row else None


@router.get("")
def list_industries():
    with connection() as conn:
        rows = conn.execute(
            f"SELECT id, name FROM industries {_LIST_ORDER}"
        ).fetchall()
        return [{"id": r["id"], "name": r["name"]} for r in rows]


@router.post("", status_code=201)
def create_industry(payload: IndustryIn):
    name = payload.name
    with connection() as conn:
        if _existing_id_named(conn, name) is not None:
            raise HTTPException(status_code=409, detail="Industry already exists")
        cur = conn.execute(
            "INSERT INTO industries (name, created_at) VALUES (?, ?)",
            (name, utc_now()),
        )
        return {"id": cur.lastrowid, "name": name}


@router.put("/{industry_id}")
def rename_industry(industry_id: int, payload: IndustryIn):
    name = payload.name
    with connection() as conn:
        _fetch_industry(conn, industry_id)
        existing = _existing_id_named(conn, name)
        if existing is not None and existing != industry_id:
            raise HTTPException(status_code=409, detail="Industry already exists")
        conn.execute(
            "UPDATE industries SET name = ? WHERE id = ?", (name, industry_id)
        )
        return {"id": industry_id, "name": name}
