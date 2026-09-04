"""Synchronous PDF document generation for a company profile.

Generation requires a complete company (Sprint 01 rule: ``name``, an industry,
and the four contact/description text fields). Locations and a logo are not
required; a set logo is embedded when possible and otherwise omitted.
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from backend.db import connection, utc_now
from backend.models import artifact_to_dict, company_is_complete
from backend.services import pdf, storage

router = APIRouter(tags=["documents"])

_GENERATION_FAILURE = {
    "success": False,
    "message": "Not enough information to generate a document",
    "artifact": None,
}

_LOCATION_ORDER = (
    "CASE WHEN type = 'Headquarters' THEN 0 ELSE 1 END, id ASC"
)


def _company_locations(conn, company_id: int) -> list[dict]:
    rows = conn.execute(
        "SELECT label, city, country_code FROM locations "
        f"WHERE company_id = ? ORDER BY {_LOCATION_ORDER}",
        (company_id,),
    ).fetchall()
    return [
        {"label": r["label"], "city": r["city"], "country_code": r["country_code"]}
        for r in rows
    ]


def _logo_bytes(conn, company_id: int) -> bytes | None:
    row = conn.execute(
        "SELECT stored_filename FROM artifacts "
        "WHERE company_id = ? AND source = 'logo' ORDER BY id DESC LIMIT 1",
        (company_id,),
    ).fetchone()
    if row is None:
        return None
    path = storage.read(company_id, row["stored_filename"])
    if not path.is_file():
        return None
    return path.read_bytes()


@router.post("/companies/{company_id}/documents/generate", status_code=201)
def generate_document(company_id: int):
    with connection() as conn:
        row = conn.execute(
            "SELECT * FROM companies WHERE id = ?", (company_id,)
        ).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Company not found")
        if not company_is_complete(row):
            return JSONResponse(status_code=422, content=_GENERATION_FAILURE)

        industry = None
        if row["industry_id"] is not None:
            irow = conn.execute(
                "SELECT name FROM industries WHERE id = ?", (row["industry_id"],)
            ).fetchone()
            industry = irow["name"] if irow else None

        data = {
            "name": row["name"],
            "website": row["website"],
            "contact_email": row["contact_email"],
            "contact_phone": row["contact_phone"],
            "description": row["description"],
            "updated_at": row["updated_at"],
        }
        content = pdf.generate_summary(
            data,
            industry=industry,
            locations=_company_locations(conn, company_id),
            logo_bytes=_logo_bytes(conn, company_id),
        )
        stored_filename = storage.new_stored_filename("company-summary.pdf")
        storage.save(company_id, stored_filename, content)

        try:
            cur = conn.execute(
                "INSERT INTO artifacts (company_id, original_name, "
                "stored_filename, content_type, size_bytes, created_at, source) "
                "VALUES (?, ?, ?, ?, ?, ?, 'generated')",
                (
                    company_id,
                    f"{row['name']}-summary.pdf",
                    stored_filename,
                    "application/pdf",
                    len(content),
                    utc_now(),
                ),
            )
            artifact_row = conn.execute(
                "SELECT * FROM artifacts WHERE id = ?", (cur.lastrowid,)
            ).fetchone()
        except Exception:
            storage.delete(company_id, stored_filename)
            raise

    return JSONResponse(
        status_code=201,
        content={
            "success": True,
            "message": "Document generated",
            "artifact": artifact_to_dict(artifact_row),
        },
    )
