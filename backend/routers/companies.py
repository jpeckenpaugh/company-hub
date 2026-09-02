"""Company CRUD + profile payloads."""

from fastapi import APIRouter, HTTPException

from backend.db import connection, utc_now
from backend.models import artifact_to_dict, company_to_dict
from backend.schemas import CompanyIn
from backend.services import storage

router = APIRouter(prefix="/companies", tags=["companies"])

_COMPANY_FIELDS = (
    "name",
    "industry",
    "hq_location",
    "website",
    "contact_email",
    "contact_phone",
    "description",
)

_LIST_QUERY = """
SELECT c.*,
       (SELECT COUNT(*) FROM artifacts a WHERE a.company_id = c.id) AS artifacts_count
FROM companies c
"""


def _fetch_company_row(conn, company_id: int):
    row = conn.execute(
        "SELECT * FROM companies WHERE id = ?", (company_id,)
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Company not found")
    return row


def _company_list_item(row):
    return company_to_dict(row, artifacts_count=row["artifacts_count"])


@router.get("")
def list_companies(q: str | None = None):
    sql = _LIST_QUERY
    params: tuple = ()
    if q:
        sql += " WHERE c.name LIKE ? COLLATE NOCASE"
        params = (f"%{q}%",)
    sql += " ORDER BY c.id ASC"
    with connection() as conn:
        rows = conn.execute(sql, params).fetchall()
        return [_company_list_item(r) for r in rows]


@router.post("", status_code=201)
def create_company(payload: CompanyIn):
    values = {f: getattr(payload, f) for f in _COMPANY_FIELDS}
    with connection() as conn:
        cur = conn.execute(
            "INSERT INTO companies (name, industry, hq_location, website, "
            "contact_email, contact_phone, description, created_at, updated_at) "
            "VALUES (:name, :industry, :hq_location, :website, :contact_email, "
            ":contact_phone, :description, :created_at, :updated_at)",
            {**values, "created_at": utc_now(), "updated_at": utc_now()},
        )
        row = conn.execute(
            "SELECT c.*, (SELECT COUNT(*) FROM artifacts a "
            "WHERE a.company_id = c.id) AS artifacts_count "
            "FROM companies c WHERE c.id = ?",
            (cur.lastrowid,),
        ).fetchone()
        return _company_list_item(row)


@router.get("/{company_id}")
def get_company(company_id: int):
    with connection() as conn:
        row = _fetch_company_row(conn, company_id)
        count = conn.execute(
            "SELECT COUNT(*) AS n FROM artifacts WHERE company_id = ?",
            (company_id,),
        ).fetchone()["n"]
        artifacts = conn.execute(
            "SELECT * FROM artifacts WHERE company_id = ? ORDER BY id DESC",
            (company_id,),
        ).fetchall()
        data = company_to_dict(row, artifacts_count=count)
        data["artifacts"] = [artifact_to_dict(a) for a in artifacts]
        return data


@router.put("/{company_id}")
def update_company(company_id: int, payload: CompanyIn):
    values = {f: getattr(payload, f) for f in _COMPANY_FIELDS}
    with connection() as conn:
        _fetch_company_row(conn, company_id)
        conn.execute(
            "UPDATE companies SET name = :name, industry = :industry, "
            "hq_location = :hq_location, website = :website, "
            "contact_email = :contact_email, contact_phone = :contact_phone, "
            "description = :description, updated_at = :updated_at "
            "WHERE id = :id",
            {**values, "id": company_id, "updated_at": utc_now()},
        )
        row = conn.execute(
            "SELECT c.*, (SELECT COUNT(*) FROM artifacts a "
            "WHERE a.company_id = c.id) AS artifacts_count "
            "FROM companies c WHERE c.id = ?",
            (company_id,),
        ).fetchone()
        return _company_list_item(row)


@router.delete("/{company_id}", status_code=204)
def delete_company(company_id: int):
    with connection() as conn:
        _fetch_company_row(conn, company_id)
        conn.execute("DELETE FROM companies WHERE id = ?", (company_id,))
    storage.delete_company_dir(company_id)
    return None
