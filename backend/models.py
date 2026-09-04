"""Thin row-model helpers mapping DB rows to JSON-friendly dicts.

The public API shapes are defined here so routers and the PDF service share a
single source of truth. The on-disk ``stored_filename`` is intentionally never
exposed to clients.

Sprint 01: company completeness now keys off ``industry_id`` plus the four
free-text contact/description fields; locations and logos do not count.
"""

TEXT_FIELDS_FOR_COMPLETENESS = (
    "website",
    "contact_email",
    "contact_phone",
    "description",
)

ARTIFACT_FIELDS = (
    "id",
    "company_id",
    "original_name",
    "content_type",
    "size_bytes",
    "created_at",
    "source",
)

LOCATION_FIELDS = (
    "id",
    "company_id",
    "label",
    "address",
    "city",
    "country_code",
    "type",
)

REFERENCE_FIELDS = (
    "id",
    "company_id",
    "title",
    "url",
    "description",
    "added_by",
    "created_at",
    "updated_at",
)

NEWS_FIELDS = (
    "id",
    "company_id",
    "title",
    "source",
    "url",
    "published_at",
    "summary",
    "created_at",
    "updated_at",
)


def company_is_complete(row) -> bool:
    """A company is complete when ``name`` is present, ``industry_id`` is set,
    and every text field is non-empty. Locations and logos do not count.
    Derived, never stored."""
    if not row["name"] or row["industry_id"] is None:
        return False
    return all(bool(row[f]) for f in TEXT_FIELDS_FOR_COMPLETENESS)


def artifact_to_dict(row) -> dict:
    data = {f: row[f] for f in ARTIFACT_FIELDS}
    data["download_url"] = f"/api/artifacts/{row['id']}/content"
    return data


def location_to_dict(row, country_name: str | None) -> dict:
    data = {f: row[f] for f in LOCATION_FIELDS}
    data["country_name"] = country_name
    return data


def reference_to_dict(row) -> dict:
    return {f: row[f] for f in REFERENCE_FIELDS}


def news_to_dict(row) -> dict:
    data = {f: row[f] for f in NEWS_FIELDS}
    data["is_scraped"] = bool(row["is_scraped"])
    return data
