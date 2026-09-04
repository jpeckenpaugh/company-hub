"""Authentication: auth gates on every protected route, login/logout/me."""

from backend.routers.auth import ADMIN_EMAIL


def _protected_requests():
    return [
        ("GET", "/api/industries"),
        ("POST", "/api/industries", {"name": "X"}),
        ("PUT", "/api/industries/1", {"name": "X"}),
        ("GET", "/api/countries"),
        ("GET", "/api/companies"),
        ("POST", "/api/companies", {"name": "X"}),
        ("GET", "/api/companies/1"),
        ("PUT", "/api/companies/1", {"name": "X"}),
        ("DELETE", "/api/companies/1"),
        ("POST", "/api/companies/1/locations", {"label": "HQ", "city": "Paris", "country_code": "FR", "type": "Headquarters"}),
        ("PUT", "/api/companies/1/locations/1", {"label": "HQ", "city": "Paris", "country_code": "FR", "type": "Headquarters"}),
        ("DELETE", "/api/companies/1/locations/1"),
        ("POST", "/api/companies/1/references", {"title": "R", "url": "https://example.com"}),
        ("PUT", "/api/companies/1/references/1", {"title": "R", "url": "https://example.com"}),
        ("DELETE", "/api/companies/1/references/1"),
        ("POST", "/api/companies/1/news", {"title": "N", "source": "S", "url": "https://example.com", "published_at": "2026-01-01"}),
        ("PUT", "/api/companies/1/news/1", {"title": "N", "source": "S", "url": "https://example.com", "published_at": "2026-01-01"}),
        ("DELETE", "/api/companies/1/news/1"),
        ("POST", "/api/companies/1/artifacts"),
        ("GET", "/api/companies/1/artifacts"),
        ("GET", "/api/artifacts/1/content"),
        ("DELETE", "/api/artifacts/1"),
        ("POST", "/api/companies/1/logo"),
        ("DELETE", "/api/companies/1/logo"),
        ("POST", "/api/companies/1/documents/generate"),
    ]


def test_every_protected_route_401s_without_a_session(client):
    for method, url, *rest in _protected_requests():
        kwargs = {}
        if rest:
            if method == "POST" and url.endswith(("/artifacts", "/logo")):
                kwargs["files"] = {"file": ("notes.txt", b"hello", "text/plain")}
            else:
                kwargs["json"] = rest[0]
        r = client.request(method, url, **kwargs)
        assert r.status_code == 401, f"{method} {url} -> {r.status_code}"
        assert r.json() == {"detail": "Not authenticated"}, f"{method} {url}"


def test_login_wrong_password_401(client, admin_password):
    r = client.post(
        "/api/auth/login",
        json={"email": ADMIN_EMAIL, "password": "wrong-password"},
    )
    assert r.status_code == 401
    assert r.json() == {"detail": "Invalid email or password"}


def test_login_success_returns_user(client, admin_password):
    r = client.post(
        "/api/auth/login",
        json={"email": ADMIN_EMAIL, "password": admin_password},
    )
    assert r.status_code == 200
    assert r.json() == {"id": 1, "email": ADMIN_EMAIL}
    assert r.cookies.get("session")


def test_me_returns_current_user(client, admin_password):
    client.post(
        "/api/auth/login",
        json={"email": ADMIN_EMAIL, "password": admin_password},
    )
    r = client.get("/api/auth/me")
    assert r.status_code == 200
    assert r.json() == {"id": 1, "email": ADMIN_EMAIL}


def test_logout_is_idempotent(client, admin_password):
    client.post(
        "/api/auth/login",
        json={"email": ADMIN_EMAIL, "password": admin_password},
    )
    assert client.get("/api/companies").status_code == 200
    assert client.post("/api/auth/logout").status_code == 204
    assert client.get("/api/companies").status_code == 401
    assert client.post("/api/auth/logout").status_code == 204
    assert client.post("/api/auth/logout").status_code == 204