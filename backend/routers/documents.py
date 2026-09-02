"""Synchronous PDF document generation for a company profile."""

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from backend.db import connection, utc_now
from backend.models import ALL_COMPANY_FIELDS, artifact_to_dict, company_is_complete
from backend.services import pdf, storage

router = APIRouter(tags=["documents"])

_GENERATION_FAILURE = {
    "success": False,
    "message": "Not enough information to generate a document",
    "artifact": None,
}


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

        data = {f: row[f] for f in ALL_COMPANY_FIELDS}
        data["created_at"] = row["created_at"]
        data["updated_at"] = row["updated_at"]

        content = pdf.generate_summary(data)
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