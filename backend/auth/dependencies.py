"""Auth gate dependencies backed by the fastapi-users components.

Every protected ``/api/`` route resolves the ``session`` cookie through the
``DatabaseStrategy`` (``access_tokens`` → ``users``); a missing/invalid/expired
session yields the contracted ``401 {"detail": "Not authenticated"}``. The
superuser variant adds the contracted ``403 {"detail": "Not enough
permissions"}`` for authenticated non-superusers.
"""

from fastapi import Depends, HTTPException, status
from fastapi_users.authentication.strategy.db import DatabaseStrategy
from fastapi_users.manager import BaseUserManager

from backend.auth.db import get_user_manager
from backend.auth.strategies import cookie_scheme, get_database_strategy
from backend.models.user import User


async def get_current_user(
    token: str | None = Depends(cookie_scheme),
    user_manager: BaseUserManager = Depends(get_user_manager),
    strategy: DatabaseStrategy = Depends(get_database_strategy),
) -> User:
    if token is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    user = await strategy.read_token(token, user_manager)
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return user


async def get_current_superuser(user: User = Depends(get_current_user)) -> User:
    if not user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions"
        )
    return user