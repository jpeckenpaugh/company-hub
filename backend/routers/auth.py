"""Authentication: bootstrap admin, login/logout/me, and the auth dependency.

Credential storage is ``pbkdf2_sha256$<iterations>$<salt_hex>$<hash_hex>``.
Sessions are DB-backed rows keyed by an opaque cookie token; they survive
restarts and end only on logout or removal. No expiry this sprint.
"""

import hashlib
import hmac
import secrets
import sqlite3

from fastapi import APIRouter, Depends, HTTPException, Request, Response

from backend.db import connection, utc_now
from backend.schemas import LoginIn

router = APIRouter(prefix="/auth", tags=["auth"])

ADMIN_EMAIL = "admin@localhost"
_PBKDF2_ITERATIONS = 600_000
_COOKIE_NAME = "session"


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, _PBKDF2_ITERATIONS
    )
    return f"pbkdf2_sha256${_PBKDF2_ITERATIONS}${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        algorithm, iterations_s, salt_hex, hash_hex = stored.split("$")
        if algorithm != "pbkdf2_sha256":
            return False
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(hash_hex)
        iterations = int(iterations_s)
    except (ValueError, TypeError):
        return False
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, iterations
    )
    return hmac.compare_digest(digest, expected)


def bootstrap_admin() -> None:
    """Generate a fresh complex admin password, store its hash, and print the
    current password to the console. Runs on every startup; any previously
    displayed password becomes invalid after a restart."""
    password = secrets.token_urlsafe(24)
    with connection() as conn:
        conn.execute(
            "INSERT INTO users (email, password_hash, created_at) "
            "VALUES (?, ?, ?) "
            "ON CONFLICT(email) DO UPDATE SET password_hash = excluded.password_hash",
            (ADMIN_EMAIL, hash_password(password), utc_now()),
        )
    print(f"\nCompany Hub admin login -> email: {ADMIN_EMAIL}  password: {password}\n",
          flush=True)


def get_current_user(request: Request) -> sqlite3.Row:
    """Auth dependency: read the session cookie, resolve it to a user, else 401."""
    token = request.cookies.get(_COOKIE_NAME)
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    with connection() as conn:
        row = conn.execute(
            "SELECT u.id, u.email FROM sessions s "
            "JOIN users u ON u.id = s.user_id WHERE s.token = ?",
            (token,),
        ).fetchone()
    if row is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return row


@router.post("/login")
def login(payload: LoginIn, response: Response):
    email = payload.email.strip()
    with connection() as conn:
        user = conn.execute(
            "SELECT * FROM users WHERE email = ?", (email,)
        ).fetchone()
        if user is None or not verify_password(payload.password, user["password_hash"]):
            raise HTTPException(status_code=401, detail="Invalid email or password")
        token = secrets.token_urlsafe(32)
        conn.execute(
            "INSERT INTO sessions (token, user_id, created_at) VALUES (?, ?, ?)",
            (token, user["id"], utc_now()),
        )
    response.set_cookie(
        _COOKIE_NAME, token, path="/", httponly=True, samesite="lax"
    )
    return {"id": user["id"], "email": user["email"]}


@router.get("/me")
def me(current_user: sqlite3.Row = Depends(get_current_user)):
    return {"id": current_user["id"], "email": current_user["email"]}


@router.post("/logout", status_code=204)
def logout(request: Request, response: Response):
    token = request.cookies.get(_COOKIE_NAME)
    if token:
        with connection() as conn:
            conn.execute("DELETE FROM sessions WHERE token = ?", (token,))
    response.delete_cookie(_COOKIE_NAME, path="/")
    return None
