"""Thin row-model helpers mapping DB rows to JSON-friendly dicts.

The public API shapes are defined here so routers and the PDF service share a
single source of truth. The on-disk ``stored_filename`` is intentionally never
exposed to clients.
"""

OPTIONAL_COMPANY_FIELDS = (
    "industry",
    "hq_location",
    "website",
    "contact_email",
    "contact_phone",
    "description",
)

ALL_COMPANY_FIELDS = ("name",) + OPTIONAL_COMPANY_FIELDS

ARTIFACT_FIELDS = (
    "id",
    "company_id",
    "original_name",
    "content_type",
    "size_bytes",
    "created_at",
    "source",
)


def company_is_complete(row) -> bool:
    """A company is complete when ``name`` and every optional field is
    non-empty. Derived, never stored."""
    return bool(row["name"]) and all(bool(row[f]) for f in OPTIONAL_COMPANY_FIELDS)


def company_to_dict(row, artifacts_count: int = 0) -> dict:
    data = {"id": row["id"]}
    data.update({f: row[f] for f in ALL_COMPANY_FIELDS})
    data["created_at"] = row["created_at"]
    data["updated_at"] = row["updated_at"]
    data["is_complete"] = company_is_complete(row)
    data["artifacts_count"] = artifacts_count
    return data


def artifact_to_dict(row) -> dict:
    data = {f: row[f] for f in ARTIFACT_FIELDS}
    data["download_url"] = f"/api/artifacts/{row['id']}/content"
    return data
