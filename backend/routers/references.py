"""Company references sub-resource CRUD.

A reference belongs to exactly one company. ``added_by`` (the signed-in user's
email) and ``created_at`` are immutable; edits update only ``title``, ``url``,
``description``, and ``updated_at``.
"""

from fastapi import APIRouter, Depends, HTTPException

from backend.db import connection, utc_now
from backend.models import reference_to_dict
from backend.routers.auth import get_current_user
from backend.schemas import ReferenceIn

router = APIRouter(tags=["references"])

_EDITABLE_FIELDS = ("title", "url", "description")


def _fetch_company(conn, company_id: int):
    row = conn.execute(
        "SELECT id FROM companies WHERE id = ?", (company_id,)
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Company not found")
    return row


def _fetch_reference(conn, company_id: int, reference_id: int):
    row = conn.execute(
        "SELECT * FROM \"references\" WHERE id = ? AND company_id = ?",
        (reference_id, company_id),
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Reference not found")
    return row


@router.post("/companies/{company_id}/references", status_code=201)
def create_reference(
    company_id: int,
    payload: ReferenceIn,
    current_user=Depends(get_current_user),
):
    now = utc_now()
    with connection() as conn:
        _fetch_company(conn, company_id)
        cur = conn.execute(
            "INSERT INTO \"references\" (company_id, title, url, description, "
            "added_by, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                company_id,
                payload.title,
                payload.url,
                payload.description,
                current_user["email"],
                now,
                now,
            ),
        )
        row = conn.execute(
            "SELECT * FROM \"references\" WHERE id = ?", (cur.lastrowid,)
        ).fetchone()
        return reference_to_dict(row)


@router.put("/companies/{company_id}/references/{reference_id}")
def update_reference(
    company_id: int,
    reference_id: int,
    payload: ReferenceIn,
):
    with connection() as conn:
        _fetch_company(conn, company_id)
        _fetch_reference(conn, company_id, reference_id)
        values = {f: getattr(payload, f) for f in _EDITABLE_FIELDS}
        conn.execute(
            "UPDATE \"references\" SET title = :title, url = :url, "
            "description = :description, updated_at = :updated_at "
            "WHERE id = :id AND company_id = :company_id",
            {
                **values,
                "updated_at": utc_now(),
                "id": reference_id,
                "company_id": company_id,
            },
        )
        row = conn.execute(
            "SELECT * FROM \"references\" WHERE id = ?", (reference_id,)
        ).fetchone()
        return reference_to_dict(row)


@router.delete("/companies/{company_id}/references/{reference_id}", status_code=204)
def delete_reference(company_id: int, reference_id: int):
    with connection() as conn:
        _fetch_company(conn, company_id)
        _fetch_reference(conn, company_id, reference_id)
        conn.execute(
            "DELETE FROM \"references\" WHERE id = ? AND company_id = ?",
            (reference_id, company_id),
        )
    return None
