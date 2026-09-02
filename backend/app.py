"""FastAPI application assembly.

Wire-up only: build the app, mount routers and the frontend static files, and
initialize runtime state on startup. No business logic lives here.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from backend.db import PROJECT_ROOT, init_db
from backend.routers import artifacts, companies, documents

FRONTEND_DIR = PROJECT_ROOT / "frontend"


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="Company Hub",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(companies.router, prefix="/api")
app.include_router(artifacts.router, prefix="/api")
app.include_router(documents.router, prefix="/api")

if FRONTEND_DIR.is_dir():
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")