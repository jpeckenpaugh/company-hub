"""Runtime configuration: paths, environment overrides, and time helpers.

All paths are anchored to the repository root (the parent of the ``backend``
package) rather than the process working directory, so the app is robust
regardless of where it is launched from. Importing this module performs no I/O
beyond reading environment variables at import time.

Sprint 02: the persistence layer now lives under ``backend/db/`` and honors the
same environment overrides as the v0.1/Sprint 01 build (``COMPANY_HUB_DB`` for
the storage root, ``COMPANY_HUB_SESSION_TTL`` for the session lifetime).
"""

import os
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
FRONTEND_DIR = PROJECT_ROOT / "frontend"
DATA_DIR = PROJECT_ROOT / "data"

_OVERRIDE_DB = os.environ.get("COMPANY_HUB_DB")
if _OVERRIDE_DB:
    DB_PATH = Path(_OVERRIDE_DB)
    ARTIFACTS_DIR = DB_PATH.parent / "artifacts"
else:
    DB_PATH = DATA_DIR / "company_hub.db"
    ARTIFACTS_DIR = DATA_DIR / "artifacts"

ADMIN_EMAIL = "admin@localhost"

DEFAULT_SESSION_TTL = 7 * 24 * 60 * 60  # 604800 seconds (7 days)


def session_ttl_seconds() -> int:
    """The fixed absolute session lifetime in seconds.

    ``COMPANY_HUB_SESSION_TTL`` overrides the 7-day default; invalid/absent
    values fall back to the default. Non-positive values are rejected so a
    misconfigured variable never creates instant-expiry sessions.
    """
    raw = os.environ.get("COMPANY_HUB_SESSION_TTL")
    if raw:
        try:
            value = int(raw)
        except ValueError:
            return DEFAULT_SESSION_TTL
        if value > 0:
            return value
    return DEFAULT_SESSION_TTL


def utc_now() -> str:
    """Current UTC time as an ISO-8601 string with a ``Z`` suffix."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def ensure_dirs() -> None:
    """Create the runtime storage directories if absent."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)