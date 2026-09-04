"""Shared fixtures for the backend test suite.

The storage root is redirected to a session-scoped temp directory before any
backend module is imported (guarding against the real ``data/`` tree), and each
test then gets its own throwaway DB via a function-scoped ``client`` fixture.
The admin password is fixed per test so login is deterministic.
"""

import os
import tempfile
from pathlib import Path

import pytest

_SESSION_TMP = Path(tempfile.mkdtemp(prefix="company-hub-tests-"))
os.environ["COMPANY_HUB_DB"] = str(_SESSION_TMP / "company_hub.db")

from fastapi.testclient import TestClient  # noqa: E402

from backend import db as db_module  # noqa: E402
from backend.app import app  # noqa: E402
from backend.routers.auth import ADMIN_EMAIL  # noqa: E402
from backend.services import storage as storage_module  # noqa: E402

ADMIN_PASSWORD = "test-admin-password"


@pytest.fixture()
def admin_password() -> str:
    return ADMIN_PASSWORD


@pytest.fixture()
def client(tmp_path, monkeypatch, admin_password):
    db_file = tmp_path / "company_hub.db"
    monkeypatch.setattr(db_module, "DB_PATH", db_file)
    artifacts_dir = db_file.parent / "artifacts"
    monkeypatch.setattr(db_module, "ARTIFACTS_DIR", artifacts_dir)
    monkeypatch.setattr(storage_module, "ARTIFACTS_DIR", artifacts_dir)
    monkeypatch.setenv("COMPANY_HUB_ADMIN_PASSWORD", admin_password)
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def authed_client(client, admin_password):
    r = client.post(
        "/api/auth/login",
        json={"email": ADMIN_EMAIL, "password": admin_password},
    )
    assert r.status_code == 200
    return client