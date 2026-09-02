# Company Hub

A simple internal web app for a small, globally distributed firm to view and
maintain information about the companies it works with. Company Hub is intended
as a lightweight backbone for other internal workflows — a consistent place to
browse company information, view and edit company profiles, and store or
generate documents associated with a company — rather than a comprehensive CRM
or firm-wide system of record.

The application distinguishes between structured company information (stored in
a relational database) and files or generated artifacts associated with those
companies (handled through a simple object-storage capability). As an initial
example, it can generate a simple, clean PDF summary of a company's profile and
make that document available from the profile.

## Stack

- **Backend:** [FastAPI](https://fastapi.tiangolo.com/) with [SQLite](https://www.sqlite.org/)
  (via the Python standard library) — serves the REST API and the frontend.
- **Frontend:** a static, client-side [Bootstrap](https://getbootstrap.com/) SPA
  (no build step) served by the FastAPI app at `/`.
- **Object storage:** local filesystem under `data/artifacts/` — file bytes are
  kept on disk; the database stores artifact metadata only.
- **Document generation:** [fpdf2](https://py-pdf.github.io/fpdf2/) for the
  one-page PDF company summary.

Target Python 3.11+ (developed on 3.12).

## Features

- **Browse companies** — a single, central list with searchable names, compact
  scannable details, and click-through to a company profile.
- **View company profiles** — all structured information for one company plus
  its related files and generated documents in one place.
- **Maintain company information** — add and edit a company's structured
  details with save/cancel; incomplete records are flagged as such.
- **Manage files and artifacts** — upload, list, download, and remove files or
  artifacts associated with a company.
- **Generate documents** — generate a simple, clean PDF summary from a company
  profile; it is stored as an artifact and exposed from the profile.

## Requirements

- A Python 3.11+ interpreter named `python3.12` or `python3.11` on `PATH`
  (the install script does not bootstrap a runtime).
- No external database or object-storage service is required.

## Setup

```sh
./install.sh
```

`install.sh` creates a project-local virtual environment (`.venv/`) and installs
the pinned dependencies from `requirements.txt`.

## Run

```sh
./run.sh
```

`run.sh` starts the app with `uvicorn backend.app:app` on
`http://127.0.0.1:8000`. Open that URL in a browser.

On first start the backend creates the SQLite database under `data/` and seeds
it with a small set of realistic companies. Runtime data (the database and
stored artifact bytes) live under `data/`, which is gitignored and never
committed.

## API

The REST API lives under `/api` and includes:

- `GET /api/companies` — list (with optional `?q=` name search)
- `POST /api/companies` — create a company
- `GET /api/companies/{id}` — company profile (with its artifacts)
- `PUT /api/companies/{id}` — full-replace update
- `DELETE /api/companies/{id}` — delete a company (cascades to its artifacts)
- `POST /api/companies/{id}/artifacts` — upload an artifact
- `GET /api/companies/{id}/artifacts` — list a company's artifacts
- `GET /api/artifacts/{id}/content` — download an artifact
- `DELETE /api/artifacts/{id}` — remove an artifact
- `POST /api/companies/{id}/documents/generate` — generate a PDF summary

Interactive API docs are available at `/docs` (OpenAPI).

## Implementation summary

The backend (`backend/`) is a FastAPI application assembled in `backend/app.py`,
with SQLite persistence (`backend/db.py`), row-to-JSON models
(`backend/models.py`), Pydantic request schemas (`backend/schemas.py`), and
routers for companies, artifacts, and document generation. A local-filesystem
object-storage service (`backend/services/storage.py`) stores bytes under
`data/artifacts/<company_id>/`, and a one-page PDF service
(`backend/services/pdf.py`) builds the company summary. The database stores
artifact metadata only; file bytes live on disk.

The frontend (`frontend/`) is a static Bootstrap SPA — an `index.html` shell, a
custom stylesheet, and five ES-module JavaScript files (`app.js`, `api.js`,
`list.js`, `profile.js`, `form.js`) implementing hash-based routing, the list,
profile, add/edit, artifact, and generate views. Bootstrap and Bootstrap Icons
are vendored locally, so the app has no runtime network/CDN dependency. It is a
strict API client with no client-side persistence: every view re-fetches from
the backend, so the UI always reflects current state.

## Current status

**Complete and verified.** The delivered application (Stage 6 backend + Stage 7
frontend) passed verification with zero failures. The only Stage 7 blocker — the
backend's company responses initially omitting the `id` field — was fixed in a
follow-up patch and confirmed across every company endpoint. The working tree is
clean on `main` and up to date with `origin`.

## Verification results

Verification (Stage 8) ran the app via `./run.sh` and exercised the full API
surface live, plus static review of the frontend rendering logic. See
`docs/verification-report.md` for the full evidence-backed report.

- **Result: PASS — 0 failures** across 34 checks in five groups (environment and
  stack, company API, artifact API / object storage, document generation, and
  frontend static review).
- Three checks pass with notes; these are documented human resolutions from
  earlier stages, not defects (see Known issues below).

## Known issues and limitations

These are documented limitations and previously resolved human decisions,
recorded as delivered and **not** treated as defects:

- **No automated browser interaction.** The frontend was verified by static
  review of its rendering logic plus live exercise (via `curl`) of every API call
  the SPA makes, and by confirming all assets serve with correct MIME types and
  all JS passes a syntax check. Click-through, form fill, and toast rendering
  were not exercised by a browser-automation tool.
- **Search is name-only.** List search is a case-insensitive substring match on
  the company `name` field only (an architecture decision).
- **Generated PDF text is CID-encoded on hosts with a Unicode font.** On macOS
  the summary is rendered with Arial Unicode, so the text is embedded in a way
  that is not human-greppable as plaintext; the file is still a valid `%PDF-1.3`
  and reflects current company data.
- **No delete-company UI in the SPA.** Company deletion is available through the
  API (and intended for automated workflows) but the SPA does not expose a
  delete button. Artifact delete is available from the profile.
- **`PUT` returns the list-item shape.** The update endpoint returns the same
  shape as `POST` (without the `artifacts` array), per an explicit human
  resolution; the SPA only consumes the fields it needs from the response.
- **Generate is enabled for incomplete companies.** The button is always active;
  generating for an incomplete company returns a `422` and the frontend renders
  the backend's failure message inline.
- **No authentication.** There is no auth in the initial scope; the app is
  intended as an internal lightweight backbone.
- **Uploads are read fully into memory** before being written to storage —
  acceptable for the lightweight backbone, but a streaming path may be needed for
  larger files.
- **SQLite autoincrement sequence is not reset when the seeded database is
  restored**; new ids continue after the highest ever used. Ids remain stable and
  monotonic, so this is cosmetic.

## Recommended next actions

- **Browser-automation verification.** Add a browser automation tool (e.g.,
  Playwright/Selenium) to exercise click-through, form fill, and toast rendering
  end-to-end, closing the current static-review limitation.
- **Multi-field search.** Broaden company search beyond name-only (industry,
  location, etc.).
- **Streaming uploads.** Stream larger uploads to storage instead of reading them
  fully into memory.
- **Authentication.** Add auth for the internal backbone as a future pass.
- **PDF plaintext embedding.** Investigate embedding PDF text so it is
  greppable as plaintext regardless of host font availability.
