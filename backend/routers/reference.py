"""Reference data: the fixed standard country list (read-only).

No runtime country-management UI this sprint; the list is the curated seed list.
"""

from fastapi import APIRouter

from backend.db import connection

router = APIRouter(prefix="/countries", tags=["countries"])


@router.get("")
def list_countries():
    with connection() as conn:
        rows = conn.execute(
            "SELECT code, name FROM countries "
            "ORDER BY name COLLATE NOCASE, name"
        ).fetchall()
        return [{"code": r["code"], "name": r["name"]} for r in rows]
