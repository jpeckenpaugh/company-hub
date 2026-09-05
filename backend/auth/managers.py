"""User manager and the stable admin bootstrap.

The manager validates passwords (minimum length, a backend-authored rule) and
parses integer user ids. ``bootstrap_admin`` creates the stable superuser
idempotently on startup: password from ``COMPANY_HUB_ADMIN_PASSWORD`` if set,
else a fresh complex password generated and printed once at creation. The
credential persists in the database and is never re-randomized on later
restarts (supersedes the Sprint 01 per-startup regeneration).
"""

import os
import secrets

from fastapi_users import exceptions
from fastapi_users.manager import BaseUserManager, IntegerIDMixin

from backend.auth.schemas import UserCreate
from backend.config import ADMIN_EMAIL, utc_now
from backend.db.engine import get_sessionmaker
from backend.models.user import User

MIN_PASSWORD_LENGTH = 8


class UserManager(IntegerIDMixin, BaseUserManager[User, int]):
    """Integer-PK user manager with a minimal password policy.

    ``reset_password_token_secret``/``verification_token_secret`` are required
    class attributes; neither the reset nor the verify router is mounted this
    sprint, so they are never exercised.
    """

    reset_password_token_secret = "company-hub-reset-password-secret"
    verification_token_secret = "company-hub-verify-token-secret"

    async def validate_password(self, password: str, user: UserCreate | User) -> None:
        if len(password) < MIN_PASSWORD_LENGTH:
            raise exceptions.InvalidPasswordException(
                reason=f"Password should be at least {MIN_PASSWORD_LENGTH} characters"
            )


async def bootstrap_admin() -> None:
    """Create ``admin@localhost`` if and only if it does not already exist."""
    from fastapi_users_db_sqlalchemy import SQLAlchemyUserDatabase

    async with get_sessionmaker()() as session:
        user_db = SQLAlchemyUserDatabase(session, User)
        existing = await user_db.get_by_email(ADMIN_EMAIL)
        if existing is not None:
            return

        from_env = bool(os.environ.get("COMPANY_HUB_ADMIN_PASSWORD"))
        password = os.environ.get("COMPANY_HUB_ADMIN_PASSWORD") or secrets.token_urlsafe(24)
        hashed = UserManager(user_db).password_helper.hash(password)
        await user_db.create(
            {
                "email": ADMIN_EMAIL,
                "hashed_password": hashed,
                "is_active": True,
                "is_superuser": True,
                "is_verified": True,
                "created_at": utc_now(),
            }
        )
        if not from_env:
            print(
                f"\nCompany Hub admin login -> email: {ADMIN_EMAIL}  password: {password}\n",
                flush=True,
            )