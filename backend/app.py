"""FastAPI application assembly.

Wire-up only: build the app, mount routers and the frontend static files, and
initialize runtime state on startup. No business logic lives here.

Every ``/api/`` route requires an authenticated session (the ``get_current_user``
dependency) except ``POST /api/auth/login``; logout is idempotent and does not
require a session. The frontend static files are served without auth — the SPA
itself renders the login view when unauthenticated.
"""

from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.staticfiles import StaticFiles

from backend.db import PROJECT_ROOT, init_db
from backend.routers import (
    artifacts,
    auth,
    companies,
    documents,
    industries,
    locations,
    news,
    reference,
    references,
)
from backend.routers.auth import bootstrap_admin, get_current_user

FRONTEND_DIR = PROJECT_ROOT / "frontend"


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    bootstrap_admin()
    yield


app = FastAPI(
    title="Company Hub",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(auth.router, prefix="/api")

_protected = [Depends(get_current_user)]
for router in (
    industries.router,
    reference.router,
    companies.router,
    locations.router,
    references.router,
    news.router,
    artifacts.router,
    documents.router,
):
    app.include_router(router, prefix="/api", dependencies=_protected)

if FRONTEND_DIR.is_dir():
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
