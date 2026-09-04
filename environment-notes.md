# Environment Notes (Stage 4 — System Engineer)

## Target runtime

- **Python 3.12** (3.11+ acceptable). The environment assumes a 3.11+
  interpreter is already installed (`python3.12` preferred, falls back to
  `python3.11`); it is not bootstrapped by the scripts.
- **OS:** macOS / Linux, POSIX shells. `install.sh` and `run.sh` are Bash and
  are not expected to work on Windows.

## Provisioning

- `./install.sh` creates a project-local virtual environment at `.venv/`,
  upgrades pip, and installs the exact-pinned dependencies from
  `requirements.txt`.
- `./run.sh` starts the application with the provisioned environment:
  `uvicorn backend.app:app --host 127.0.0.1 --port 8000`.
- This entry-point contract (`backend.app:app`) is handed to the Architect
  (Stage 5) and Backend (Stage 6) stages; they must provide it.

## Dependencies and their role

| Package             | Role                                                              |
|---------------------|-------------------------------------------------------------------|
| `fastapi`           | Web/API framework for the backend                                 |
| `uvicorn`           | ASGI server used to run the app                                   |
| `python-multipart`  | Required by FastAPI for multipart file uploads (Brief 04)         |
| `fpdf2`             | Simple, clean PDF generation for derived documents (Brief 05)     |

## Storage

- **Database:** SQLite via the Python standard library — no external database
  server or driver dependency.
- **Object storage:** local filesystem. The local database and stored
  file/artifact objects live under `data/` (or wherever the Architect places
  them). `data/` is gitignored; nothing runtime-written should be committed.
- No external services (S3, database servers) are provisioned.

### Environment overrides

Two environment variables make the storage root and the admin bootstrap
deterministic, which the persistent test suites rely on:

- `COMPANY_HUB_DB` — if set, the SQLite database is created at that exact path
  and stored artifact bytes co-locate under `<dir of DB>/artifacts/`. When
  unset, the app uses the default `data/company_hub.db` + `data/artifacts/`.
- `COMPANY_HUB_ADMIN_PASSWORD` — if set, `bootstrap_admin` uses this as the
  admin password instead of generating a fresh random one on every startup.
  When unset, behavior is unchanged (a new random password is printed at boot).

## Testing

Dev-only test dependencies (nothing in `requirements.txt` is a test dependency):

```
.venv/bin/pip install -r requirements-dev.txt
```

The pinned dev deps are `pytest` (runner) and `httpx` (needed by FastAPI's
`TestClient`).

- **Backend suite** — persistent in-process pytest tests against throwaway
  temp databases (never touches `data/`):
  `.venv/bin/python -m pytest tests/backend -q`
- **Browser suite** — persistent CDP tests that drive a real headless Chrome:
  `node --test --test-concurrency=1 "tests/browser/*.test.mjs"` (requires a
  running uvicorn and Chrome on `--remote-debugging-port=9222`).
- **Everything** — `./tests/run.sh` runs both suites: it launches uvicorn with
  a throwaway DB under `tmp/` and headless Chrome, runs the browser tests, then
  tears both down. Logs land under `tmp/` (gitignored); the real `data/` is
  never touched.

The browser tests read `COMPANY_HUB_URL` (default `http://127.0.0.1:8000`) and
`COMPANY_HUB_ADMIN_PASSWORD` (default `test-admin-password`).

## Caveats

- `python-multipart` is required for FastAPI file uploads; do not remove it
  while Brief 04 is in scope.
- `fpdf2` was selected for PDF generation because it is lightweight,
  pure-Python, and has no system-level dependencies. Its role is limited to
  producing derived documents; exact format/contents remain an architecture
  (Stage 5) decision.
- `run.sh` currently expects the backend entry point to exist; running it
  before Stage 6 will fail at import time.

## Sprint 01 — manual dev-data flush (Stage 5 note)

This sprint rebuilds the data model (new tables: industries, countries, users,
sessions, locations, references, news_articles; `companies` drops `hq_location`
and the free-form `industry`). The v0.1 SQLite database is **not** migrated.
Per scope item u, flush the gitignored dev runtime state once before the first
run of the new build (performed by Stage 6):

```
rm -f data/company_hub.db && rm -rf data/artifacts
```

The app seeds only when the `companies` table is empty and never destroys data
on a normal restart. `data/` is gitignored, so no repository history is
affected.
