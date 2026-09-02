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

## Caveats

- `python-multipart` is required for FastAPI file uploads; do not remove it
  while Brief 04 is in scope.
- `fpdf2` was selected for PDF generation because it is lightweight,
  pure-Python, and has no system-level dependencies. Its role is limited to
  producing derived documents; exact format/contents remain an architecture
  (Stage 5) decision.
- `run.sh` currently expects the backend entry point to exist; running it
  before Stage 6 will fail at import time.
