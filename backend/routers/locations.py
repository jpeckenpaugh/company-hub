"""Locations sub-resource CRUD.

A company has zero or more locations. At most one Headquarters per company is
enforced with a clear ``422`` (the existing Headquarters is left unchanged); a
partial unique index provides defense in depth. Removing the Headquarters is
allowed, so a company may end up with zero locations.
"""

from fastapi import APIRouter, HTTPException

from backend.db import connection
from backend.models import location_to_dict
from backend.schemas import LocationIn

router = APIRouter(tags=["locations"])


def _fetch_company(conn, company_id: int):
    row = conn.execute(
        "SELECT id FROM companies WHERE id = ?", (company_id,)
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Company not found")
    return row


def _fetch_location(conn, company_id: int, location_id: int):
    row = conn.execute(
        "SELECT * FROM locations WHERE id = ? AND company_id = ?",
        (location_id, company_id),
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Location not found")
    return row


def _country_name(conn, country_code: str) -> str | None:
    row = conn.execute(
        "SELECT name FROM countries WHERE code = ?", (country_code,)
    ).fetchone()
    return row["name"] if row else None


def _validate_country(conn, country_code: str) -> None:
    row = conn.execute(
        "SELECT code FROM countries WHERE code = ?", (country_code,)
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=422, detail="Unknown country_code")


def _ensure_not_second_hq(conn, company_id: int, *, exclude_id: int | None = None) -> None:
    sql = "SELECT id FROM locations WHERE company_id = ? AND type = 'Headquarters'"
    params: list = [company_id]
    if exclude_id is not None:
        sql += " AND id != ?"
        params.append(exclude_id)
    row = conn.execute(sql, params).fetchone()
    if row is not None:
        raise HTTPException(
            status_code=422,
            detail="Company already has a Headquarters",
        )


def _location_payload(conn, row) -> dict:
    return location_to_dict(row, _country_name(conn, row["country_code"]))


@router.post("/companies/{company_id}/locations", status_code=201)
def create_location(company_id: int, payload: LocationIn):
    with connection() as conn:
        _fetch_company(conn, company_id)
        _validate_country(conn, payload.country_code)
        if payload.type == "Headquarters":
            _ensure_not_second_hq(conn, company_id)
        cur = conn.execute(
            "INSERT INTO locations (company_id, label, address, city, "
            "country_code, type) VALUES (?, ?, ?, ?, ?, ?)",
            (
                company_id,
                payload.label,
                payload.address,
                payload.city,
                payload.country_code,
                payload.type,
            ),
        )
        row = conn.execute(
            "SELECT * FROM locations WHERE id = ?", (cur.lastrowid,)
        ).fetchone()
        return _location_payload(conn, row)


@router.put("/companies/{company_id}/locations/{location_id}")
def update_location(company_id: int, location_id: int, payload: LocationIn):
    with connection() as conn:
        _fetch_company(conn, company_id)
        _fetch_location(conn, company_id, location_id)
        _validate_country(conn, payload.country_code)
        if payload.type == "Headquarters":
            _ensure_not_second_hq(conn, company_id, exclude_id=location_id)
        conn.execute(
            "UPDATE locations SET label = ?, address = ?, city = ?, "
            "country_code = ?, type = ? WHERE id = ? AND company_id = ?",
            (
                payload.label,
                payload.address,
                payload.city,
                payload.country_code,
                payload.type,
                location_id,
                company_id,
            ),
        )
        row = conn.execute(
            "SELECT * FROM locations WHERE id = ?", (location_id,)
        ).fetchone()
        return _location_payload(conn, row)


@router.delete("/companies/{company_id}/locations/{location_id}", status_code=204)
def delete_location(company_id: int, location_id: int):
    with connection() as conn:
        _fetch_company(conn, company_id)
        _fetch_location(conn, company_id, location_id)
        conn.execute(
            "DELETE FROM locations WHERE id = ? AND company_id = ?",
            (location_id, company_id),
        )
    return None
