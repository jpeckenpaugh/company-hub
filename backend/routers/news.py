"""Company news sub-resource CRUD.

UI-created records always have ``is_scraped = false``; the API accepts the flag
so automated workflows may set it true later. On ``PUT`` an omitted
``is_scraped`` preserves the current value.
"""

from fastapi import APIRouter, HTTPException

from backend.db import connection, utc_now
from backend.models import news_to_dict
from backend.schemas import NewsIn

router = APIRouter(tags=["news"])

_EDITABLE_FIELDS = ("title", "source", "url", "published_at", "summary")


def _fetch_company(conn, company_id: int):
    row = conn.execute(
        "SELECT id FROM companies WHERE id = ?", (company_id,)
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Company not found")
    return row


def _fetch_news(conn, company_id: int, news_id: int):
    row = conn.execute(
        "SELECT * FROM news_articles WHERE id = ? AND company_id = ?",
        (news_id, company_id),
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="News article not found")
    return row


def _scraped_flag(payload: NewsIn, current: int | None = None) -> int:
    if payload.is_scraped is not None:
        return int(payload.is_scraped)
    return int(bool(current)) if current is not None else 0


@router.post("/companies/{company_id}/news", status_code=201)
def create_news(company_id: int, payload: NewsIn):
    now = utc_now()
    with connection() as conn:
        _fetch_company(conn, company_id)
        cur = conn.execute(
            "INSERT INTO news_articles (company_id, title, source, url, "
            "published_at, summary, is_scraped, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                company_id,
                payload.title,
                payload.source,
                payload.url,
                payload.published_at,
                payload.summary,
                _scraped_flag(payload),
                now,
                now,
            ),
        )
        row = conn.execute(
            "SELECT * FROM news_articles WHERE id = ?", (cur.lastrowid,)
        ).fetchone()
        return news_to_dict(row)


@router.put("/companies/{company_id}/news/{news_id}")
def update_news(company_id: int, news_id: int, payload: NewsIn):
    with connection() as conn:
        _fetch_company(conn, company_id)
        existing = _fetch_news(conn, company_id, news_id)
        values = {f: getattr(payload, f) for f in _EDITABLE_FIELDS}
        conn.execute(
            "UPDATE news_articles SET title = :title, source = :source, "
            "url = :url, published_at = :published_at, summary = :summary, "
            "is_scraped = :is_scraped, updated_at = :updated_at "
            "WHERE id = :id AND company_id = :company_id",
            {
                **values,
                "is_scraped": _scraped_flag(payload, existing["is_scraped"]),
                "updated_at": utc_now(),
                "id": news_id,
                "company_id": company_id,
            },
        )
        row = conn.execute(
            "SELECT * FROM news_articles WHERE id = ?", (news_id,)
        ).fetchone()
        return news_to_dict(row)


@router.delete("/companies/{company_id}/news/{news_id}", status_code=204)
def delete_news(company_id: int, news_id: int):
    with connection() as conn:
        _fetch_company(conn, company_id)
        _fetch_news(conn, company_id, news_id)
        conn.execute(
            "DELETE FROM news_articles WHERE id = ? AND company_id = ?",
            (news_id, company_id),
        )
    return None
