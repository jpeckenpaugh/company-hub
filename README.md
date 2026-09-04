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
- **Authentication:** email/password login with PBKDF2-HMAC-SHA256 password
  hashing and database-backed, HttpOnly `session` cookies.
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

Sprint 01 added:

- **Sign-in required** — email/password login; the whole app requires an
  authenticated session. A bootstrap `admin@localhost` user is created on
  startup with a fresh, complex auto-generated password printed to the console
  (no signup flow).
- **Standardized industries** — industry is a controlled value chosen from a
  seeded six-item standard list (added in Sprint 01, replacing the free-form
  field). A management view can add and rename industries; renames propagate to
  companies automatically.
- **Standardized countries and locations** — a company can have zero or more
  locations (label, city, optional address/region, country from a standard
  83-entry country list, type), replacing the single free-form headquarters
  field. A company may have at most one Headquarters; the derived HQ is shown as
  "City, CC" (e.g. Shell's is "London, GB").
- **Country filter** — the companies list can be filtered by country
  (multi-select), combined with the existing name search.
- **References** — a per-company place for curated resource links (title, URL,
  description, who added it and when).
- **News** — a per-company place for news articles (title, source, URL,
  publication date, summary) with a scraped-status flag for automated
  workflows.
- **Logos** — a company can have one designated logo, uploaded from the UI,
  shown on the profile and as a list thumbnail, and embedded in generated PDFs
  when possible.

Company completeness was redefined in Sprint 01: name + industry + the four
contact/description fields (locations and logos do not count).

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

**Login is required.** On startup the backend creates the bootstrap admin
`admin@localhost` with a fresh, complex auto-generated password that is
**printed to the console**. Sign in with `admin@localhost` and that printed
password. The whole application (all `/api` routes) requires an authenticated
session, so you will be asked to log in on first use.

On first start the backend creates the SQLite database under `data/` and seeds
it with the standard data: six industries, the standard 83-entry country list,
and exactly six real companies — one of the biggest players in each seeded
industry, each carrying one Headquarters location:

| Industry | Company | HQ |
|---|---|---|
| Manufacturing | Toyota Motor | Toyota City, JP |
| Technology | Samsung Electronics | Seoul, KR |
| Finance | HSBC | London, GB |
| Healthcare | Novartis | Basel, CH |
| Energy | Shell | London, GB |
| Retail | Carrefour | Paris, FR |

Seeding happens only when the `companies` table is empty; it never overwrites
user data. Runtime data (the database and stored artifact bytes) live under
`data/`, which is gitignored and never committed.

**If you are holding a v0.1 database**, flush the gitignored dev runtime state
once before the first run of this build (the data model was rebuilt in
Sprint 01 and the v0.1 DB is not migrated):

```sh
rm -f data/company_hub.db && rm -rf data/artifacts
```

## API

The REST API lives under `/api`. Every route requires an authenticated session
except `POST /api/auth/login` (unauthenticated `/api` calls return `401`). It
includes:

- `POST /api/auth/login`, `GET /api/auth/me`, `POST /api/auth/logout` — session
  management
- `GET /api/companies` — list (with optional `?q=` name search and `?countries=`
  multi-country filter)
- `POST /api/companies` — create a company
- `GET /api/companies/{id}` — company profile (with its locations, references,
  news, and artifacts)
- `PUT /api/companies/{id}` — full-replace update
- `DELETE /api/companies/{id}` — delete a company (cascades to its artifacts)
- `GET /api/companies/{id}/locations`, `POST`, `PUT /api/companies/{id}/locations/{location_id}`,
  `DELETE` — manage a company's locations
- `GET /api/companies/{id}/references`, `POST`, `PUT`/`DELETE` per reference —
  manage references
- `GET /api/companies/{id}/news`, `POST`, `PUT`/`DELETE` per article — manage news
- `POST /api/companies/{id}/logo`, `DELETE /api/companies/{id}/logo` — set/remove
  the company logo
- `GET /api/industries`, `POST`, `PUT /api/industries/{id}` — manage the
  industry list (add/rename)
- `GET /api/countries` — the standard country list (read-only)
- `POST /api/companies/{id}/artifacts` — upload an artifact
- `GET /api/companies/{id}/artifacts` — list a company's artifacts (logos excluded)
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

**Sprint 01** extended both sides. The backend gained auth (`backend/routers/auth.py`:
PBKDF2 hashing, DB-backed HttpOnly session cookie, `login`/`me`/`logout`, every
`/api` route gated), controlled industries (`industries.py`), the standard
country list (`reference.py`), locations (`locations.py`), references
(`references.py`), news (`news.py`), and logo upload/remove on the companies
router. The companies contract now exposes a nested `industry`, a derived
`hq_location` ("City, CC"), `logo_url`, a logo-exclusive `artifacts_count`, and
the multi-country filter; completeness was redefined; the seed was replaced
with the six real companies (one HQ each); and PDF generation embeds the logo
when its bytes are embeddable. The frontend gained `login.js` and
`industries.js` plus updates to `app.js`, `api.js`, `list.js`, `profile.js`,
and `form.js` for the login gate, industry management, the country multi-select
filter, locations/references/news editors on the profile, logo
upload/replace/remove, and the new payload rendering.

## Testing

Dev-only test dependencies (nothing in `requirements.txt` is a test dependency):

```sh
.venv/bin/pip install -r requirements-dev.txt
```

- **Backend suite** — persistent in-process pytest tests against throwaway
  temp databases (never touches `data/`):
  `python -m pytest tests/backend -q`
- **Everything (backend + browser)** — `./tests/run.sh` launches uvicorn with a
  throwaway DB and headless Chrome, runs the CDP browser tests, then tears both
  down. Logs land under `tmp/` (gitignored).

See `environment-notes.md` for the full environment details, including the
`COMPANY_HUB_DB` / `COMPANY_HUB_ADMIN_PASSWORD` overrides the test suites rely
on.

## Current status

**Complete and verified.** The v0.1 application (Stage 6 backend + Stage 7
frontend) passed verification with zero failures. The only Stage 7 blocker — the
backend's company responses initially omitting the `id` field — was fixed in a
follow-up patch and confirmed across every company endpoint.

The **Sprint 01** enhancement pass (authentication, standardized industries,
standardized countries and locations, country filter, references, news, logos,
and the real-company seed) is likewise **complete and verified**: PASS with 0
failures across 93 live `curl` checks, 51 backend `pytest` checks, and 34 CDP
browser-automation checks. The working tree is clean on `main` and up to date
with `origin`. See `COMPARISON.md` for the v0.1 → Sprint 01 feature-set change
summary.

## Verification results

Verification (Stage 8) ran the app via `./run.sh` and exercised the full API
surface live, plus static review of the frontend rendering logic. See
`docs/verification-report.md` for the full evidence-backed report.

- **v0.1 (2026-09-02): PASS — 0 failures** across 34 checks in five groups
  (environment and stack, company API, artifact API / object storage, document
  generation, and frontend static review).
- **Sprint 01 (2026-09-04): PASS — 0 failures** — 93 live `curl` checks
  (auth-gated API incl. industries/countries/locations/references/news/logos/
  documents, run against a throwaway DB using the real printed-password login),
  51 backend `pytest` checks, and 34 CDP headless-Chrome browser checks, plus
  static frontend review (all seven JS modules pass `node --check`).

Three v0.1 checks pass with notes; these are documented human resolutions from
earlier stages, not defects (see Known issues below).

## Known issues and limitations

These are documented limitations and previously resolved human decisions,
recorded as delivered and **not** treated as defects. Two v0.1 items are
superseded by Sprint 01 and retained as supersession notes:

- **No automated browser interaction (superseded).** v0.1's frontend was
  verified by static review of its rendering logic plus live exercise (via
  `curl`) of every API call the SPA makes, and by confirming all assets serve
  with correct MIME types and all JS passes a syntax check. Click-through, form
  fill, and toast rendering were not exercised by a browser-automation tool.
  **Added in Sprint 01:** the repo now ships a persistent CDP browser suite
  (`tests/browser`, run via `tests/run.sh`) that drives real headless Chrome
  through login, country filtering, industry management, location/reference/news
  add/edit/remove, and logo flows.
- **No authentication (superseded).** There was no auth in the v0.1 scope; the
  app was intended as an internal lightweight backbone. **Added in Sprint 01:**
  email/password login with a bootstrap admin; the whole app now requires an
  authenticated session.

Remaining items:

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
- **Uploads are read fully into memory** before being written to storage —
  acceptable for the lightweight backbone, but a streaming path may be needed for
  larger files.
- **SQLite autoincrement sequence is not reset when the seeded database is
  restored**; new ids continue after the highest ever used. Ids remain stable and
  monotonic, so this is cosmetic.
- **Sessions have no expiry.** Sessions persist until logout or a database flush;
  there is no idle/session timeout this sprint (acceptable for a single-user dev
  tool). A timeout is a candidate future pass.
- **No visual/pixel assertions.** Browser automation asserts behavior (DOM,
  rendering, flows) but not visual styling or PDF pixel rendering; screenshot/
  visual checks are a candidate future pass.
- **Admin-password test override is a documented seam.** The
  `COMPANY_HUB_ADMIN_PASSWORD` env override (used by the test suites) and
  `COMPANY_HUB_DB` are documented in `environment-notes.md`; the app's documented
  runtime path is the console-printed admin password. Documenting the override
  seam in `docs/architecture.md` is a candidate future pass.

## Recommended next actions

- **Multi-field search.** Broaden company search beyond name-only (industry,
  location, etc.).
- **Streaming uploads.** Stream larger uploads to storage instead of reading them
  fully into memory.
- **PDF plaintext embedding.** Investigate embedding PDF text so it is
  greppable as plaintext regardless of host font availability.
- **Session expiry / timeout.** Add an idle or absolute session timeout; the
  current sessions persist until logout or a DB flush.
- **Visual / screenshot checks.** Extend the browser suite to assert visual
  styling and PDF pixel rendering.
- **Automated scraping workflows.** Reference, news, and logo scraping per scope
  boundaries n/q are out of scope; the storage and application interfaces
  already exist, so automated workflows can write these records later.
- **Document the admin-password seam in `docs/architecture.md`.** Record the
  `COMPANY_HUB_ADMIN_PASSWORD` test override alongside the documented
  printed-password flow.

Completed since v0.1 (no longer open): **browser-automation verification** (now
a persistent CDP suite) and **authentication** (added in Sprint 01).