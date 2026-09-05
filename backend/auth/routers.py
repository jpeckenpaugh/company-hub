"""Custom assembly of the fastapi-users auth routes under ``/api/auth``.

The stock ``get_auth_router`` is not used directly because the contract deviates
from it in three ways, per architecture §9.2.1:

- **JSON login body** ``{email, password}`` (stock fastapi-users login is
  form-encoded via ``OAuth2PasswordRequestForm``);
- **idempotent logout** — ``204`` even with no session (the stock router
  returns ``401`` without a token);
- **``me`` payload** ``{id, email, is_superuser}``.

The routes below are assembled from the same fastapi-users components
(``UserManager.authenticate``, the ``DatabaseStrategy``, and the
``CookieTransport``), so the auth machinery is the maintained library's.

Routes: ``POST /login``, ``POST /logout``, ``GET /me``, ``PATCH /me``,
``POST /change-password`` (self-service), and ``POST /users``
(superuser-only account creation). The register router is not mounted (no
self-service signup).
"""

from types import SimpleNamespace

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse
from fastapi_users import exceptions
from fastapi_users.authentication.strategy.db import DatabaseStrategy
from fastapi_users.authentication.transport.bearer import BearerResponse
from fastapi_users.authentication.transport.cookie import CookieTransport
from fastapi_users.manager import BaseUserManager

from backend.auth.dependencies import get_current_superuser, get_current_user
from backend.auth.db import get_user_manager
from backend.auth.schemas import (
    ChangePasswordIn,
    LoginIn,
    UserCreate,
    UserRead,
    UserUpdate,
)
from backend.auth.strategies import get_cookie_transport, get_database_strategy
from backend.models.user import User

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=BearerResponse)
async def login(
    payload: LoginIn,
    request: Request,
    user_manager: BaseUserManager = Depends(get_user_manager),
    strategy: DatabaseStrategy = Depends(get_database_strategy),
    transport: CookieTransport = Depends(get_cookie_transport),
):
    user = await user_manager.authenticate(
        SimpleNamespace(username=payload.email, password=payload.password)
    )
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="LOGIN_BAD_CREDENTIALS",
        )
    token = await strategy.write_token(user)
    response = JSONResponse(BearerResponse(access_token=token, token_type="bearer").model_dump())
    response.set_cookie(
        transport.cookie_name,
        token,
        max_age=transport.cookie_max_age,
        path=transport.cookie_path,
        domain=transport.cookie_domain,
        secure=transport.cookie_secure,
        httponly=transport.cookie_httponly,
        samesite=transport.cookie_samesite,
    )
    await user_manager.on_after_login(user, request, response)
    return response


@router.post("/logout", status_code=204)
async def logout(
    request: Request,
    user_manager: BaseUserManager = Depends(get_user_manager),
    strategy: DatabaseStrategy = Depends(get_database_strategy),
    transport: CookieTransport = Depends(get_cookie_transport),
):
    token = request.cookies.get(transport.cookie_name)
    if token:
        await strategy.destroy_token(token, None)
    response = Response(status_code=204)
    response.delete_cookie(transport.cookie_name, path=transport.cookie_path)
    return response


@router.get("/me", response_model=UserRead)
async def me(user: User = Depends(get_current_user)):
    return user


@router.patch("/me", response_model=UserRead)
async def update_me(
    payload: UserUpdate,
    request: Request,
    user: User = Depends(get_current_user),
    user_manager: BaseUserManager = Depends(get_user_manager),
):
    try:
        updated = await user_manager.update(payload, user, safe=True, request=request)
    except exceptions.InvalidPasswordException:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid password")
    return updated


@router.post("/change-password")
async def change_password(
    payload: ChangePasswordIn,
    request: Request,
    user: User = Depends(get_current_user),
    user_manager: BaseUserManager = Depends(get_user_manager),
):
    verified, _ = user_manager.password_helper.verify_and_update(
        payload.old_password, user.hashed_password
    )
    if not verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="INVALID_PASSWORD"
        )
    try:
        await user_manager.update(
            UserUpdate(password=payload.new_password), user, safe=True, request=request
        )
    except exceptions.InvalidPasswordException:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid password")
    return {"status": "ok"}


@router.post("/users", status_code=201, response_model=UserRead)
async def create_user(
    payload: UserCreate,
    request: Request,
    user: User = Depends(get_current_superuser),
    user_manager: BaseUserManager = Depends(get_user_manager),
):
    try:
        created = await user_manager.create(payload, safe=False, request=request)
    except exceptions.UserAlreadyExists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="REGISTER_USER_ALREADY_EXISTS",
        )
    except exceptions.InvalidPasswordException:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid password")
    return created