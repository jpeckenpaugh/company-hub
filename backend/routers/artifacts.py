"""Artifact upload / list / download / delete."""

from fastapi import APIRouter, HTTPException, UploadFile
from fastapi.responses import FileResponse

from backend.db import connection, utc_now
from backend.models import artifact_to_dict
from backend.services import storage

router = APIRouter(tags=["artifacts"])


def _fetch_company(conn, company_id: int):
    row = conn.execute(
        "SELECT id FROM companies WHERE id = ?", (company_id,)
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Company not found")
    return row


def _fetch_artifact(conn, artifact_id: int):
    row = conn.execute(
        "SELECT * FROM artifacts WHERE id = ?", (artifact_id,)
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Artifact not found")
    return row


@router.post("/companies/{company_id}/artifacts", status_code=201)
def upload_artifact(company_id: int, file: UploadFile):
    filename = file.filename or ""
    if not filename.strip():
        raise HTTPException(
            status_code=422, detail="A file part with a filename is required"
        )
    content = file.file.read()
    stored_filename = storage.new_stored_filename(filename)
    try:
        storage.save(company_id, stored_filename, content)
        with connection() as conn:
            _fetch_company(conn, company_id)
            cur = conn.execute(
                "INSERT INTO artifacts (company_id, original_name, "
                "stored_filename, content_type, size_bytes, created_at, source) "
                "VALUES (?, ?, ?, ?, ?, ?, 'upload')",
                (
                    company_id,
                    filename,
                    stored_filename,
                    file.content_type or "application/octet-stream",
                    len(content),
                    utc_now(),
                ),
            )
            row = conn.execute(
                "SELECT * FROM artifacts WHERE id = ?", (cur.lastrowid,)
            ).fetchone()
    except HTTPException:
        storage.delete(company_id, stored_filename)
        raise
    except Exception:
        storage.delete(company_id, stored_filename)
        raise
    return artifact_to_dict(row)


@router.get("/companies/{company_id}/artifacts")
def list_artifacts(company_id: int):
    with connection() as conn:
        _fetch_company(conn, company_id)
        rows = conn.execute(
            "SELECT * FROM artifacts WHERE company_id = ? ORDER BY id DESC",
            (company_id,),
        ).fetchall()
        return [artifact_to_dict(r) for r in rows]


@router.get("/artifacts/{artifact_id}/content")
def download_artifact(artifact_id: int):
    with connection() as conn:
        row = _fetch_artifact(conn, artifact_id)
        path = storage.read(row["company_id"], row["stored_filename"])
        if not path.is_file():
            raise HTTPException(status_code=404, detail="Artifact not found")
        return FileResponse(
            path,
            media_type=row["content_type"],
            filename=row["original_name"],
        )


@router.delete("/artifacts/{artifact_id}", status_code=204)
def delete_artifact(artifact_id: int):
    with connection() as conn:
        row = _fetch_artifact(conn, artifact_id)
        conn.execute("DELETE FROM artifacts WHERE id = ?", (artifact_id,))
    storage.delete(row["company_id"], row["stored_filename"])
    return None