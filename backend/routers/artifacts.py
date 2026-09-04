"""Artifact upload / list / download / delete, plus logo upload/replace/remove.

Logos are stored objects like any other artifact (bytes under
``data/artifacts/<company_id>/`` plus a metadata row with ``source = 'logo'``)
but are surfaced separately via ``logo_url`` and excluded from the generic
Files & artifacts list. At most one logo per company is enforced by a partial
unique index; replacing one deletes the previous row (and its bytes) before
inserting the new row within a single transaction.
"""

from fastapi import APIRouter, HTTPException, UploadFile

from backend.services import storage
from fastapi.responses import FileResponse

from backend.db import connection, utc_now
from backend.models import artifact_to_dict

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


def _require_filename(file: UploadFile) -> None:
    if not (file.filename or "").strip():
        raise HTTPException(
            status_code=422, detail="A file part with a filename is required"
        )


def _insert_artifact_row(
    conn, company_id: int, original_name: str, stored_filename: str,
    content_type: str, content: bytes, source: str,
):
    cur = conn.execute(
        "INSERT INTO artifacts (company_id, original_name, stored_filename, "
        "content_type, size_bytes, created_at, source) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (
            company_id,
            original_name,
            stored_filename,
            content_type,
            len(content),
            utc_now(),
            source,
        ),
    )
    return conn.execute(
        "SELECT * FROM artifacts WHERE id = ?", (cur.lastrowid,)
    ).fetchone()


@router.post("/companies/{company_id}/artifacts", status_code=201)
def upload_artifact(company_id: int, file: UploadFile):
    _require_filename(file)
    content = file.file.read()
    stored_filename = storage.new_stored_filename(file.filename or "")
    storage.save(company_id, stored_filename, content)
    try:
        with connection() as conn:
            _fetch_company(conn, company_id)
            row = _insert_artifact_row(
                conn,
                company_id,
                file.filename,
                stored_filename,
                file.content_type or "application/octet-stream",
                content,
                "upload",
            )
    except Exception:
        storage.delete(company_id, stored_filename)
        raise
    return artifact_to_dict(row)


@router.get("/companies/{company_id}/artifacts")
def list_artifacts(company_id: int):
    with connection() as conn:
        _fetch_company(conn, company_id)
        rows = conn.execute(
            "SELECT * FROM artifacts WHERE company_id = ? AND source != 'logo' "
            "ORDER BY id DESC",
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


@router.post("/companies/{company_id}/logo", status_code=201)
def upload_logo(company_id: int, file: UploadFile):
    _require_filename(file)
    if not (file.content_type or "").startswith("image/"):
        raise HTTPException(status_code=415, detail="Logo must be an image")
    with connection() as conn:
        _fetch_company(conn, company_id)
    content = file.file.read()
    stored_filename = storage.new_stored_filename(file.filename or "")
    storage.save(company_id, stored_filename, content)
    old_row = None
    try:
        with connection() as conn:
            _fetch_company(conn, company_id)
            old_row = conn.execute(
                "SELECT * FROM artifacts WHERE company_id = ? AND source = 'logo' "
                "ORDER BY id DESC LIMIT 1",
                (company_id,),
            ).fetchone()
            conn.execute(
                "DELETE FROM artifacts WHERE company_id = ? AND source = 'logo'",
                (company_id,),
            )
            row = _insert_artifact_row(
                conn,
                company_id,
                file.filename,
                stored_filename,
                file.content_type or "application/octet-stream",
                content,
                "logo",
            )
    except Exception:
        storage.delete(company_id, stored_filename)
        raise
    if old_row is not None:
        storage.delete(company_id, old_row["stored_filename"])
    return artifact_to_dict(row)


@router.delete("/companies/{company_id}/logo", status_code=204)
def delete_logo(company_id: int):
    with connection() as conn:
        row = conn.execute(
            "SELECT * FROM artifacts WHERE company_id = ? AND source = 'logo' "
            "ORDER BY id DESC LIMIT 1",
            (company_id,),
        ).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Logo not found")
        conn.execute("DELETE FROM artifacts WHERE id = ?", (row["id"],))
    storage.delete(company_id, row["stored_filename"])
    return None
