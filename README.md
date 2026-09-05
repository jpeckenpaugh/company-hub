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
  persisted through **async [SQLAlchemy](https://www.sqlalchemy.org/) 2.0**
  (`aiosqlite`) with versioned **[Alembic](https://alembic.sqlalchemy.org/)**
  migrations — serves the REST API and the frontend.
- **Frontend:** a static, client-side [Bootstrap](https://getbootstrap.com/) SPA
  (no build step) served by the FastAPI app at `/`.
- **Authentication:** the maintained [fastapi-users](https://fastapi-users.github.io/)
  library — email/password login with the stateful `DatabaseStrategy` (server-side
  session tokens with a defined lifetime) and an HttpOnly `session` cookie
  (`CookieTransport`).
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

Sprint 02 added:

- **Async ORM persistence** — the database layer was rebuilt on async
  SQLAlchemy 2.0 (`aiosqlite`); application code reads and writes through ORM
  models rather than hand-managed SQL. All existing non-auth API contracts and
  behaviors are unchanged.
- **Versioned schema migrations** — the schema is applied through Alembic
  versioned migrations (the Sprint 01 schema is the baseline; a Sprint 02
  revision adds the auth/schema deltas). Fresh databases reach the current
  schema by replaying the migration set in order.
- **Maintained authentication** — the hand-rolled Sprint 01 auth was replaced by
  fastapi-users. Sign-in/sign-out and the current-user endpoint use the same
  cookie-based experience as before, but login now returns `{access_token,
  token_type}` and `me` returns `{id, email, is_superuser}`.
- **Stable bootstrap admin** — the `admin@localhost` account now has a stable,
  persisted credential (created once, **not** re-randomized on every restart).
- **Self-service change-password** — a user can change their own password from a
  new `#/password` UI view (`POST /api/auth/change-password`).
- **Multiple user accounts** — additional accounts are created by a superuser
  through `POST /api/auth/users`; there is no self-service signup.
- **Defined session lifetime** — sessions have a fixed server-side lifetime
  (default 7 days, `COMPANY_HUB_SESSION_TTL` to override) enforced by the
  fastapi-users stateful `DatabaseStrategy`, with immediate server-side
  revocation on sign-out.
- **OAuth-ready account model (schema-only)** — an `oauth_accounts` table exists
  (Google-oriented) so external-identity-provider login can be added in a later
  sprint without a data-model change; no OAuth login routes exist yet.

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

**Login is required.** On first startup the backend creates the bootstrap admin
`admin@localhost` with a fresh, complex auto-generated password that is
**printed to the console**. Sign in with `admin@localhost` and that printed
password. The password is created once and **persisted** — it is **not**
re-randomized on subsequent restarts (the `COMPANY_HUB_ADMIN_PASSWORD`
environment override, used by the test suites, sets it deterministically
instead). The whole application (all `/api` routes) requires an authenticated
session, so you will be asked to log in on first use.

On first start the backend creates the SQLite database under `data/` and seeds
it with the standard data: six industries, the standard 83-entry country list,
and exactly six real companies — one of the biggest players in each seeded
industry. Each company is seeded with a Headquarters location, one or two
further real locations, two curated references (a Wikipedia article and its
official about/company-profile page), several genuine recent news articles
(hand-authored, not scraped), and a logo:

| Industry | Company | HQ |
|---|---|---|
| Manufacturing | Toyota Motor | Toyota City, JP |
| Technology | Samsung Electronics | Seoul, KR |
| Finance | HSBC | London, GB |
| Healthcare | Novartis | Basel, CH |
| Energy | Shell | London, GB |
| Retail | Carrefour | Paris, FR |

Seeded references use `added_by = admin@localhost` to mark them as
backend-seeded rather than user-added.

Seeding happens only when the `companies` table is empty; it never overwrites
user data. Runtime data (the database and stored artifact bytes) live under
`data/`, which is gitignored and never committed.

**If you are holding a database seeded before this build**, flush the gitignored
dev runtime state once so the richer seed (references, news, logos, and extra
locations) is created on the next start (seeding never runs on a non-empty
`companies` table):

```sh
./flush.sh
```

`flush.sh` removes `data/company_hub.db` and `data/artifacts`; the next
`./run.sh` seeds a fresh database from scratch. **Sprint 02** established the
Alembic migration baseline with a one-time flush of the dev state (scope item
n); from then on the current schema is reached by replaying the migration set in
order, and seeding still runs only on an empty `companies` table.

## API

The REST API lives under `/api`. Every route requires an authenticated session
except `POST /api/auth/login` (unauthenticated `/api` calls return `401`). It
includes:

- `POST /api/auth/login` — sign in with `{email, password}`; returns
  `200 {access_token, token_type:"bearer"}` plus an HttpOnly `session` cookie
- `GET /api/auth/me` — the current user `{id, email, is_superuser}`
- `POST /api/auth/logout` — sign out; revokes the session server-side (idempotent
  `204`)
- `POST /api/auth/change-password` — change the current user's own password
  (`{old_password, new_password}`, new password ≥ 8 chars)
- `POST /api/auth/users` — **superuser-only** account creation; no self-service
  signup route
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
with async SQLAlchemy persistence (`backend/db/` — engine, per-request session,
and seed), ORM models (`backend/models/`), Pydantic request schemas
(`backend/schemas.py`), row-to-JSON serializers (`backend/serializers.py`), and
routers for companies, artifacts, and document generation. A local-filesystem
object-storage service (`backend/services/storage.py`) stores bytes under
`data/artifacts/<company_id>/`, and a one-page PDF service
(`backend/services/pdf.py`) builds the company summary. The database stores
artifact metadata only; file bytes live on disk.

The frontend (`frontend/`) is a static Bootstrap SPA — an `index.html` shell, a
custom stylesheet, and eight ES-module JavaScript files (`app.js`, `api.js`,
`list.js`, `profile.js`, `form.js`, `login.js`, `industries.js`, `password.js`)
implementing hash-based routing, the list, profile, add/edit, artifact,
generate, login, industry-management, and change-password views. Bootstrap and
Bootstrap Icons are vendored locally, so the app has no runtime network/CDN
dependency. It is a strict API client with no client-side persistence: every
view re-fetches from the backend, so the UI always reflects current state.

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

The seed was later enriched with real content (`backend/data/seed.py`): each
seeded company now also carries one or two further real locations, two curated
references (Wikipedia + official about page, `added_by = admin@localhost`),
several genuine recent news articles (`is_scraped = 0`), and a committed raster
logo (`backend/data/logos/`) copied into artifact storage at seed time.

**Sprint 02** rebuilt the persistence layer on async SQLAlchemy 2.0 and replaced
the hand-rolled auth with fastapi-users. The backend now has a config module
(`backend/config.py`), an ORM model set (`backend/models/`, incl. `user`,
`access_token`, and the schema-only `oauth_account`), an async DB layer
(`backend/db/` — engine, per-request session, and seed), an auth package
(`backend/auth/` — DB adapters, `DatabaseStrategy` + `CookieTransport`, user
manager with the idempotent bootstrap-admin, and a custom auth-router assembly
for the JSON-login / idempotent-logout / `{id, email, is_superuser}`-`me`
contract), and a serializer layer (`backend/serializers.py`). Versioned Alembic
migrations (`backend/alembic/` — Sprint 01 schema baseline + a Sprint 02 auth
revision) run to `head` on startup. Routers are now async ORM calls; file I/O
and PDF generation run via `asyncio.to_thread` so they stay off the request
loop. The hand-rolled `backend/routers/auth.py` and `backend/db.py` were
removed (superseded). The frontend gained a `password.js` view and a `#/password`
route (self-service change-password) and re-fetches the current user via `me`
after login, since the login response is now `{access_token, token_type}`.

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
browser-automation checks. See `COMPARISON.md` for the v0.1 → Sprint 01
feature-set change summary.

The **Sprint 02** enhancement pass (persistence rebuilt on async SQLAlchemy
with Alembic versioned migrations, and hand-rolled auth replaced by the
maintained fastapi-users library) is **complete and verified**: PASS with 0
failures across 64 backend `pytest` checks, 36 CDP browser-automation checks
(incl. a self-service change-password UI flow), and 28 live `curl` checks
exercising the fastapi-users auth contract (login/me/logout, change-password,
superuser-only account creation, session expiry + server-side revocation, and a
non-auth API regression pass). The working tree is clean on `main` and up to
date with `origin`.

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
- **Sprint 02 (2026-09-05): PASS — 0 failures** — 64 backend `pytest` checks
  (16 auth: route gating, login/logout/me, change-password, multiple users,
  session expiry; plus all non-auth resources), 36 CDP headless-Chrome browser
  checks (incl. the new change-password UI flow), and 28 live `curl` checks
  against a running app exercising the fastapi-users auth contract
  (login/me/logout, change-password, superuser-only account creation, session
  expiry via a short-TTL throwaway server, server-side revocation, and a
  non-auth API regression pass), run against throwaway DBs so `data/` was
  untouched.

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
- **Sessions have no expiry (superseded).** Previously sessions persisted until
  logout or a database flush. **Added in Sprint 02:** sessions now have a
  defined server-side lifetime (default 7 days, `COMPANY_HUB_SESSION_TTL` to
  override) enforced by the fastapi-users stateful `DatabaseStrategy`, with
  immediate server-side revocation on sign-out.
- **No visual/pixel assertions.** Browser automation asserts behavior (DOM,
  rendering, flows) but not visual styling or PDF pixel rendering; screenshot/
  visual checks are a candidate future pass.
- **Admin-password test override is a documented seam.** The
  `COMPANY_HUB_ADMIN_PASSWORD` env override (used by the test suites) and
  `COMPANY_HUB_DB` are documented in `environment-notes.md`; the app's documented
  runtime path is the console-printed admin password, now created once and
  persisted (not re-randomized per restart). Documenting the override seam in
  `docs/architecture.md` is a candidate future pass.

**Sprint 02 additions:**

- **Fastapi-users contract deviations.** Login uses a JSON body
  (`{email, password}`) and returns `200 {access_token, token_type}` rather than
  the stock form-encoded flow; logout returns `204` even with no session
  (idempotent); `me` returns `{id, email, is_superuser}`. These are documented,
  deliberate deviations recorded by the Backend Engineer and verified as
  delivered.
- **`PATCH /api/auth/me` is declared but unused.** It is exposed for
  fastapi-users compatibility (password-only self-service); the SPA uses the
  dedicated `POST /api/auth/change-password` route instead, and no other profile
  fields are self-editable this sprint.
- **`oauth_accounts` is schema-only.** The OAuth-ready account table exists with
  zero rows and no OAuth login routes/SSO behavior; Google SSO is a future
  sprint.
- **Stable admin credential.** The bootstrap admin password is now created once
  and persisted across restarts (not re-randomized per startup as in Sprint 01);
  it is only re-generated if the admin account is deleted.

## Recommended next actions

- **Multi-field search.** Broaden company search beyond name-only (industry,
  location, etc.).
- **Streaming uploads.** Stream larger uploads to storage instead of reading them
  fully into memory.
- **PDF plaintext embedding.** Investigate embedding PDF text so it is
  greppable as plaintext regardless of host font availability.
- **Visual / screenshot checks.** Extend the browser suite to assert visual
  styling and PDF pixel rendering.
- **Automated scraping workflows.** Reference, news, and logo scraping per scope
  boundaries n/q are out of scope; the storage and application interfaces
  already exist, so automated workflows can write these records later.
- **Document the admin-password seam in `docs/architecture.md`.** Record the
  `COMPANY_HUB_ADMIN_PASSWORD` test override alongside the documented
  printed-password flow.

Sprint 02 / future:

- **Google-SSO login.** The `oauth_accounts` schema is in place (Google-oriented)
  with no OAuth routes yet; a later sprint can mount fastapi-users SSO with no
  data-model change.
- **Superuser admin UI.** Account creation exists via the superuser-only
  `POST /api/auth/users` API but there is no SPA admin view; a future pass could
  add a minimal user-management screen.
- **Document the `PATCH /api/auth/me` seam.** The route is implemented (password
  only) but unused by the SPA; record its availability/limits in
  `docs/architecture.md` for future use.

Completed since v0.1 (no longer open): **browser-automation verification** (now
a persistent CDP suite), **authentication** (added in Sprint 01, rebuilt on
fastapi-users in Sprint 02), and **session expiry / server-side session
lifetime** (added in Sprint 02).