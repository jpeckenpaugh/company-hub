# Architecture Specification — Company Hub

Stage 5 artifact. Defines the technical shape of the application so that the
Backend (Stage 6) and Frontend (Stage 7) engineers can implement independently
and in parallel. This is reference documentation, not code.

- **Product:** Company Hub (see `concept.md`).
- **Feature briefs:** `features/briefs/01-browse-companies.md` through
  `features/briefs/05-generate-documents-from-profiles.md`.
- **Environment:** `requirements.txt` and `environment-notes.md` (Stage 4).
- **Stack:** FastAPI + SQLite (stdlib `sqlite3`) backend; Bootstrap-based SPA
  frontend served as static files by the backend; local-filesystem object
  storage for files and generated artifacts; `fpdf2` for PDF generation.
- **Entry point contract:** `uvicorn backend.app:app --host 127.0.0.1 --port 8000`
  (`run.sh`). The backend package must be importable as `backend` with the ASGI
  app named `app`. This contract is preserved by every module layout decision
  below.

---

## 1. Project / File Structure

```
.
├── backend/                       # FastAPI application (Stage 6)
│   ├── __init__.py
│   ├── app.py                     # creates FastAPI app, mounts routers + static
│   ├── db.py                      # SQLite connection + schema init + seed
│   ├── models.py                  # row-model helpers / dataclasses
│   ├── schemas.py                 # Pydantic request/response models
│   ├── routers/
│   │   ├── __init__.py
│   │   └── companies.py           # company CRUD + profile payloads
│   │   └── artifacts.py           # artifact upload/list/download/delete
│   │   └── documents.py           # PDF generation
│   ├── services/
│   │   ├── __init__.py
│   │   ├── storage.py             # object storage (file bytes) + path mapping
│   │   └── pdf.py                 # PDF summary generation (fpdf2)
│   └── data/
│       ├── seed.py                # seed content + seed-on-empty logic
│       └── logos/                 # committed raster logo bytes (one per company)
├── frontend/                      # Bootstrap SPA (Stage 7)
│   ├── index.html                 # entry page; mounts the SPA
│   ├── css/style.css              # custom styles over Bootstrap
│   └── js/
│       ├── api.js                 # fetch wrapper for the REST API
│       ├── list.js                # browse/list view + routing
│       ├── profile.js             # profile view + artifact/document actions
│       └── form.js                # add/edit company form
├── data/                          # runtime storage (gitignored, auto-created)
│   ├── company_hub.db             # SQLite database
│   └── artifacts/                 # object storage (files, generated PDFs)
│       └── <company_id>/          # one folder per company
│           └── <stored filename>  # stored bytes, unique per item
├── docs/
│   └── architecture.md            # this file
├── summaries/
│   └── 05-architecture.md         # stage summary
├── requirements.txt               # Stage 4
├── install.sh                     # Stage 4
├── run.sh                         # Stage 4 (backend.app:app contract)
├── environment-notes.md           # Stage 4
└── tmp/                           # scratch/logs (gitignored)
```

### Runtime directory creation

The backend creates runtime directories on startup if absent: `data/` and
`data/artifacts/`. The SQLite file `data/company_hub.db` is created (and the
schema initialized) on first startup. All runtime writes stay under `data/`,
which is gitignored.

---

## 2. Module Boundaries

| Module | Responsibility | Owns |
|--------|----------------|------|
| `backend/app.py` | Wire-up only: build app, mount routers and static frontend, create runtime dirs. No business logic. | app lifecycle |
| `backend/db.py` | Connection, schema DDL, schema initialization, and seed-on-empty. No request logic. | `companies`, `artifacts` tables |
| `backend/schemas.py` | Pydantic models — request/response shapes. | request/response contract |
| `backend/models.py` | Thin row/dataclass helpers mapping DB rows to JSON-friendly values. | row mapping |
| `backend/routers/*` | HTTP routes: parse input, call services/db, return responses. No raw SQL, no file bytes handling. | HTTP surface |
| `backend/services/storage.py` | Object storage: store/retrieve/delete bytes under `data/artifacts/<company_id>/`; metadata passed back. No HTTP. | artifact bytes + paths |
| `backend/services/pdf.py` | Generate the simple clean one-page PDF summary from a company's structured fields. No HTTP, no DB. | PDF bytes |
| `frontend/*` | Bootstrap SPA: list, profile, forms, API calls, artifact/document actions. Consumes only the documented API. | UI |

Backend responsibilities: all API routes, data persistence, schema/seed,
object storage, PDF generation, serving the frontend static files.

Frontend responsibilities: rendering the company list, company profile, add/edit
form, artifact upload/delete UI, document generation action, and surfacing
completeness state. No business data is stored client-side; the SPA is a pure
API client. Routing between views is handled client-side (hash-based or simple
JS show/hide); the backend does not render pages.

---

## 3. Data Model & SQLite Schema

Two tables. Object bytes are **not** stored in the database; the `artifacts`
table stores only the metadata row for a stored object, and the bytes live under
`data/artifacts/<company_id>/`.

### `companies`

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | INTEGER | `PRIMARY KEY AUTOINCREMENT` | stable identifier |
| `name` | TEXT | `NOT NULL` | required; used for identification |
| `industry` | TEXT | nullable | structured detail |
| `hq_location` | TEXT | nullable | headquarter city / country |
| `website` | TEXT | nullable | company URL |
| `contact_email` | TEXT | nullable | primary contact email |
| `contact_phone` | TEXT | nullable | primary contact phone |
| `description` | TEXT | nullable | free-text summary |
| `created_at` | TEXT | `NOT NULL` | ISO-8601 UTC timestamp |
| `updated_at` | TEXT | `NOT NULL` | ISO-8601 UTC timestamp |

Required fields: `name`. A company is **complete** when `name` is present and
every one of the structured fields (`industry`, `hq_location`, `website`,
`contact_email`, `contact_phone`, `description`) is non-empty. Completeness is
derived, never stored.

### `artifacts`

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | INTEGER | `PRIMARY KEY AUTOINCREMENT` | stable identifier |
| `company_id` | INTEGER | `NOT NULL`, `FOREIGN KEY -> companies.id`, `ON DELETE CASCADE` | owner |
| `original_name` | TEXT | `NOT NULL` | user-visible filename |
| `stored_filename` | TEXT | `NOT NULL` | filesystem name on disk; unique via UUID |
| `content_type` | TEXT | `NOT NULL` | MIME type |
| `size_bytes` | INTEGER | `NOT NULL` | byte size |
| `created_at` | TEXT | `NOT NULL` | ISO-8601 UTC timestamp |
| `source` | TEXT | `NOT NULL` | `upload` or `generated` |

- Every artifact belongs to exactly one company (`company_id`); access control
  is enforced by always querying/listing/scoping through `company_id`.
- `stored_filename` is a server-generated UUID (with original extension), so
  the on-disk name is always unique and never collides across companies or
  re-uploads.
- Deleting a company cascades to its artifact rows; the storage service removes
  the corresponding files under `data/artifacts/<company_id>/`.

### Seed data

On first startup (empty `companies` table), `backend/data/seed.py` inserts the
six real companies plus per-company locations, references, news, and logos (see
§8.1.5). Seed data includes structured fields and committed raster logos copied
into artifact storage — no generated artifacts are seeded.
Seeding happens only when the `companies` table is empty; it never overwrites
user-entered data.

---

## 4. API Contracts

Base path: all routes are served under `/api/`. Frontend static files are
served at `/` by FastAPI's `StaticFiles`.

### Company resources

#### `GET /api/companies`

List all companies. Supports optional search filtering: `?q=<text>` filters by
case-insensitive substring match on `name`.

Response `200` — JSON array, each item:

```json
{
  "id": 1,
  "name": "Acme Corp",
  "industry": "Manufacturing",
  "hq_location": "Berlin, DE",
  "website": "https://acme.example",
  "contact_email": "hello@acme.example",
  "contact_phone": "+49 30 1234 5678",
  "description": "Industrial components.",
  "created_at": "2026-09-01T00:00:00Z",
  "updated_at": "2026-09-01T00:00:00Z",
  "is_complete": true,
  "artifacts_count": 2
}
```

Fields are serialized in snake_case; missing optional fields are `null`.
`is_complete` is derived (see §3). `artifacts_count` is the number of stored
items for the company.

#### `POST /api/companies`

Create a company.

Request body (all optional except `name`):

```json
{
  "name": "Acme Corp",
  "industry": "Manufacturing",
  "hq_location": "Berlin, DE",
  "website": "https://acme.example",
  "contact_email": "hello@acme.example",
  "contact_phone": "+49 30 1234 5678",
  "description": "Industrial components."
}
```

Response `201` — the created company in the same shape as `GET /api/companies`
items (including `id`, timestamps, `is_complete`, `artifacts_count`).

Errors:
- `422` — validation: `name` missing or empty.

#### `GET /api/companies/{id}`

Get one company profile.

Response `200` — company shape above, plus an `artifacts` array:

```json
{
  "id": 1,
  "name": "Acme Corp",
  "industry": "Manufacturing",
  "hq_location": "Berlin, DE",
  "website": "https://acme.example",
  "contact_email": "hello@acme.example",
  "contact_phone": "+49 30 1234 5678",
  "description": "Industrial components.",
  "created_at": "2026-09-01T00:00:00Z",
  "updated_at": "2026-09-01T00:00:00Z",
  "is_complete": true,
  "artifacts_count": 2,
  "artifacts": [
    {
      "id": 3,
      "company_id": 1,
      "original_name": "report.pdf",
      "content_type": "application/pdf",
      "size_bytes": 4096,
      "created_at": "2026-09-01T01:00:00Z",
      "source": "generated",
      "download_url": "/api/artifacts/3/content"
    }
  ]
}
```

Errors:
- `404` — company does not exist.

#### `PUT /api/companies/{id}`

Full update of a company's structured information. Request body has the same
shape as `POST /api/companies` (all fields, including `name`).

Response `200` — the updated company profile shape.
Errors:
- `404` — company does not exist.
- `422` — validation: `name` missing or empty.

Rationale: the SPA always edits the full set of structured fields from the
profile form, so a full replace is simpler and matches the UI. The briefs
require save/cancel and no silent data loss; the form submits the complete
current field set and there is no partial-update path.

#### `DELETE /api/companies/{id}`

Delete a company and its artifacts (DB cascade + storage cleanup).

Response `204` — no body.
Errors:
- `404` — company does not exist.

### Artifact resources

#### `POST /api/companies/{company_id}/artifacts`

Upload a file/artifact and associate it with a company. `multipart/form-data`:
one file part named `file` (the artifact). `python-multipart` (pinned in
`requirements.txt`) is required for this.

Response `201` — the artifact row shape (as in the profile `artifacts` array,
including `source: "upload"` and `download_url`).
Errors:
- `404` — company does not exist.
- `422` — missing file part or empty filename.

#### `GET /api/companies/{company_id}/artifacts`

List a company's stored items. Returns a JSON array of artifact rows (same shape
as the profile `artifacts` array), newest first.
Errors:
- `404` — company does not exist.

#### `GET /api/artifacts/{artifact_id}/content`

Open or download a stored artifact. Streams the stored bytes with
`Content-Disposition: attachment; filename="<original_name>"`.

Response `200` — file bytes (the stored `content_type`).
Errors:
- `404` — artifact does not exist.

#### `DELETE /api/artifacts/{artifact_id}`

Remove a stored artifact (bytes + DB row). Enables the "remove file/artifact"
behavior.
Response `204` — no body.
Errors:
- `404` — artifact does not exist.

### Document generation

#### `POST /api/companies/{company_id}/documents/generate`

Request generation of a derived summary PDF from the company's current
structured information. The endpoint is synchronous (simple, immediate).

Response `201` — a JSON body:

```json
{
  "success": true,
  "message": "Document generated",
  "artifact": { ... artifact row shape, source: "generated" ... }
}
```

On failure (e.g., not enough information to produce a meaningful document),
response `422` with a JSON body:

```json
{
  "success": false,
  "message": "Not enough information to generate a document",
  "artifact": null
}
```

Errors:
- `404` — company does not exist.
- `422` — generation failed due to insufficient data (company not complete).

**Failure rule:** generation requires the company to be **complete** (see §3).
An incomplete company cannot produce a meaningful summary; the frontend
surfaces the failure message to the user. Re-generation is always allowed and
produces a fresh PDF from the current data; each generation creates a new
artifact row, so old documents remain available (and removable).

### Response/error conventions

- JSON, snake_case keys.
- Unknown company/artifact → `404` with a short JSON detail message.
- Validation errors → FastAPI default `422`.
- Success states: `200`/`201`/`204` as noted. There is no auth in the initial
  scope (internal lightweight backbone).

---

## 5. Backend / Frontend Responsibilities

### Backend (Stage 6)

- Implement `backend/app.py` (ASGI app `app`), all routers, schema DDL +
  initialization, and seed-on-empty.
- Persist and query company/artifact metadata via SQLite (stdlib `sqlite3`).
- Own object storage: write/read/delete bytes under
  `data/artifacts/<company_id>/` using `stored_filename` UUIDs.
- Generate PDFs with `fpdf2` (`backend/services/pdf.py`), a single clean,
  one-page summary of the company's structured fields.
- Serve the SPA: mount `frontend/` as `StaticFiles` at `/` (with HTML fallback
  to `index.html`).
- Create `data/` and `data/artifacts/` at startup.

### Frontend (Stage 7)

- Bootstrap-based SPA in `frontend/` (a static bundle served by FastAPI).
- Views: **List** (browse + search + click-through), **Profile** (structured
  details + related content + completeness indicator + actions),
  **Add/Edit form** (save/cancel), **Artifact list/upload/delete**,
  **Generate document** action with success/failure feedback.
- Consumes only the documented API. No data persistence client-side; views are
  refreshed/re-rendered from API responses so the list stays consistent with
  the profile and vice versa.

---

## 6. Component Interactions & State Flow

```
Browser (Bootstrap SPA)
   │  fetch() → /api/...
   ▼
FastAPI routers (companies / artifacts / documents)
   │  ├─→ schemas (validation)
   │  ├─→ services/pdf.py (fpdf2) ──→ bytes → storage
   │  ├─→ services/storage.py ──→ data/artifacts/<company_id>/...
   │  └─→ db.py (sqlite3) ──→ data/company_hub.db
   │
   └─ StaticFiles: / → frontend/index.html + assets
```

**State flow:** The SPA holds no authoritative state; every view change fetches
from the API. Adding/editing a company via the form → `POST`/`PUT` → the list
and profile re-fetch and reflect the change. Uploading/removing an artifact or
generating a document → `POST`/`DELETE` → profile re-fetches and shows the new
set of stored items. Because all reads go through the same API, the list stays
consistent with the company records (Brief 01), and the profile always reflects
current structured info and related content (Brief 02).

**Lifecycle (backend):** startup creates runtime dirs, opens/creates the SQLite
DB, applies schema DDL, and seeds realistic companies when empty. Each request
opens a short-lived DB connection; writes are committed per request.
`updated_at` is refreshed on every company update; `created_at` is set once.
Artifact upload and document generation write bytes to storage first, then
insert the metadata row; on row-insert failure the stored file is removed to
avoid orphans.

---

## 7. Open Design Decisions / Contract Notes (for downstream engineers)

1. **Company field set & completeness (fixed here):** `name` required; the six
   optional fields as in §3. Completeness = all seven fields non-empty, exposed
   as `is_complete`. Brief 03 left the field set to the architecture; this is
   that decision.
2. **Update semantics:** full `PUT` replace only (matches the edit-form UI); no
   `PATCH`. Backend should implement `PUT` as a full replace of all structured
   fields.
3. **PDF format:** one-page, clean summary derived from the structured fields,
   via `fpdf2`. No branding/template requirements. Exact layout is a backend
   implementation detail.
4. **Generation failure rule:** generation is only meaningful for complete
   companies; incomplete → `422` with the JSON body in §4. The frontend must
   render the failure message.
5. **Object storage:** local filesystem under `data/artifacts/<company_id>/`;
   DB holds metadata only. `stored_filename` = UUID + original extension.
6. **Entry point:** honor `backend.app:app` exactly for `run.sh`.
7. **No auth:** out of scope for the initial internal backbone.
8. **IDs/timestamps:** integer autoincrement IDs; ISO-8601 UTC timestamps
   (e.g., `2026-09-01T00:00:00Z`).

---

## 8. Sprint 01 Enhancements — Architecture Additions

This section extends the v0.1 specification above (§1–§7) with the deltas
required by the Sprint 01 scope (`enhancements/scope.md` items a–u; briefs
`features/briefs/01-…-09-…`). It supersedes the earlier "no auth" statements
(§4 "Response/error conventions", §7 item 7), the §3 `companies` schema, the
§3 completeness rule, and the §3 seed definition. Everything else in §1–§7
remains in force and is unchanged by this pass.

### 8.1 Data Model & SQLite Schema Changes

#### 8.1.1 `companies` (modified)

| Column | Change |
|--------|--------|
| `industry` | **Removed.** Replaced by `industry_id` (below). Free-form industry text is no longer stored. |
| `industry_id` | **Added.** INTEGER, nullable, `FOREIGN KEY -> industries(id)`. The controlled industry value; `NULL` = no industry. |
| `hq_location` | **Removed.** The single free-form headquarters field no longer exists; headquarters information now comes from `locations`. |

All other `companies` columns (`id`, `name`, `website`, `contact_email`,
`contact_phone`, `description`, `created_at`, `updated_at`) are unchanged.

#### 8.1.2 New tables

##### `industries`

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | INTEGER | `PRIMARY KEY AUTOINCREMENT` | stable identifier |
| `name` | TEXT | `NOT NULL UNIQUE` | controlled label; unique so renaming to an existing name is rejected |
| `created_at` | TEXT | `NOT NULL` | ISO-8601 UTC |

- No delete operation exists (scope/brief: add and rename only).
- Renaming an industry = `UPDATE industries SET name = ...`; every company
  referencing it resolves the new label automatically (companies store
  `industry_id`, never the label), so no company is left with a stale name.
- Add and rename reject a name that already exists (`409`, see §8.2.2).

##### `countries`

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | INTEGER | `PRIMARY KEY AUTOINCREMENT` | stable identifier |
| `code` | TEXT | `NOT NULL UNIQUE` | ISO 3166-1 alpha-2 code (e.g. `GB`, `JP`) |
| `name` | TEXT | `NOT NULL UNIQUE` | English country name |
| `created_at` | TEXT | `NOT NULL` | ISO-8601 UTC |

- Fixed, seeded standard list; **no runtime country-management UI** this sprint
  (unlike industries).
- Content: a curated ~50–100 entry list of major economies (including all G20
  members) plus the seed countries, each with an ISO alpha-2 `code` and an
  English `name`, sorted by name. The exact entry set is a Stage 6 seed detail;
  it **must include** `JP`, `KR`, `GB`, `CH`, `FR` (the seed companies'
  countries).
- **Note on "UK":** the scope/briefs refer to the United Kingdom as "UK". Its
  ISO 3166-1 alpha-2 code is `GB`; the standard list therefore stores
  `code = "GB"`, `name = "United Kingdom"`. Seed/UI references to "UK" map to
  this record.

##### `users`

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | INTEGER | `PRIMARY KEY AUTOINCREMENT` | stable identifier |
| `email` | TEXT | `NOT NULL UNIQUE` | login identity; the only user is `admin@localhost` |
| `password_hash` | TEXT | `NOT NULL` | PBKDF2-HMAC-SHA256 hash string (see §8.2.1) |
| `created_at` | TEXT | `NOT NULL` | ISO-8601 UTC |

##### `sessions`

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | INTEGER | `PRIMARY KEY AUTOINCREMENT` | stable identifier |
| `token` | TEXT | `NOT NULL UNIQUE` | opaque random token; the cookie value |
| `user_id` | INTEGER | `NOT NULL`, `FOREIGN KEY -> users.id`, `ON DELETE CASCADE` | owner |
| `created_at` | TEXT | `NOT NULL` | ISO-8601 UTC |

- DB-backed sessions survive a server restart; a session ends on logout or when
  its row is removed. No expiry this sprint.
- The bootstrap admin is **not** seed-on-empty: on **every** startup the app
  generates a fresh complex password (`secrets.token_urlsafe`), overwrites the
  stored hash for `admin@localhost`, and prints the current password to the
  console (scope item b). Any previously displayed password becomes invalid
  after a restart.

##### `locations`

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | INTEGER | `PRIMARY KEY AUTOINCREMENT` | stable identifier |
| `company_id` | INTEGER | `NOT NULL`, `FOREIGN KEY -> companies.id`, `ON DELETE CASCADE` | owner |
| `label` | TEXT | `NOT NULL` | e.g. "Global HQ" |
| `address` | TEXT | nullable | optional address/region |
| `city` | TEXT | `NOT NULL` | |
| `country_code` | TEXT | `NOT NULL`, `FOREIGN KEY -> countries.code` | from the standard list |
| `type` | TEXT | `NOT NULL`, `CHECK (type IN ('Headquarters','Office','Plant','Other'))` | exactly one of the four |

- A company has zero or more locations; the free-form `companies.hq_location`
  is replaced entirely.
- **At most one Headquarters per company**, enforced by application-level
  validation returning a clear `422` (the existing Headquarters is left
  unchanged — no auto-demotion) and, for defense in depth, a partial unique
  index: `CREATE UNIQUE INDEX idx_locations_one_hq ON locations(company_id)
  WHERE type = 'Headquarters'`.
- A company may end up with zero locations; removing an HQ is allowed.
- No timestamps: locations are ordered by `id` for display.

##### `references`

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | INTEGER | `PRIMARY KEY AUTOINCREMENT` | stable identifier |
| `company_id` | INTEGER | `NOT NULL`, `FOREIGN KEY -> companies.id`, `ON DELETE CASCADE` | owner |
| `title` | TEXT | `NOT NULL` | |
| `url` | TEXT | `NOT NULL` | openable link |
| `description` | TEXT | nullable | |
| `added_by` | TEXT | `NOT NULL` | email snapshot of the signed-in user who added it |
| `created_at` | TEXT | `NOT NULL` | immutable once set |
| `updated_at` | TEXT | `NOT NULL` | refreshed on edit |

- `added_by` and `created_at` are immutable; edits update only `title`, `url`,
  `description`, and `updated_at`.
- Every reference belongs to exactly one company and is shown only there.

##### `news_articles`

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | INTEGER | `PRIMARY KEY AUTOINCREMENT` | stable identifier |
| `company_id` | INTEGER | `NOT NULL`, `FOREIGN KEY -> companies.id`, `ON DELETE CASCADE` | owner |
| `title` | TEXT | `NOT NULL` | |
| `source` | TEXT | `NOT NULL` | |
| `url` | TEXT | `NOT NULL` | openable link |
| `published_at` | TEXT | `NOT NULL` | publication date, date-only `YYYY-MM-DD` |
| `summary` | TEXT | nullable | summary/snippet |
| `is_scraped` | INTEGER | `NOT NULL DEFAULT 0` | `0`/`1`; `true` only for records written by automated workflows |
| `created_at` | TEXT | `NOT NULL` | ISO-8601 UTC |
| `updated_at` | TEXT | `NOT NULL` | refreshed on edit |

- UI-created records always have `is_scraped = false`; the API accepts the flag
  so automated workflows can set `true` later (scope item n).

#### 8.1.3 `artifacts` (modified)

- `source` now accepts three values: `upload` and `generated` (v0.1) plus
  `logo` (new). Logos are stored objects like any other artifact: bytes under
  `data/artifacts/<company_id>/`, a metadata row in `artifacts`, and a
  `download_url` via the existing content endpoint.
- At most one logo per company, enforced by a partial unique index:
  `CREATE UNIQUE INDEX idx_artifacts_one_logo ON artifacts(company_id)
  WHERE source = 'logo'`. Replacing a logo deletes the previous `logo` row (and
  its bytes) then inserts the new one within a single transaction.
- The generic "Files & artifacts" list (`GET /api/companies/{id}` `artifacts`
  array, `GET /api/companies/{company_id}/artifacts`, and `artifacts_count`)
  **excludes** `source = 'logo'` rows; the logo is surfaced separately via
  `logo_url` on company payloads.

#### 8.1.4 Completeness (redefined)

A company is **complete** when `name` is present and non-empty, `industry_id`
is not null, and every one of `website`, `contact_email`, `contact_phone`,
`description` is non-empty. **Locations are not counted** (zero-location
companies are legitimate) and **a logo is not counted** (scope item p).
Completeness remains derived, never stored.

#### 8.1.5 Seed data (redefined)

On a fresh/empty database the app seeds:

- The six standard industries: Manufacturing, Technology, Finance, Healthcare,
  Energy, Retail (the complete seeded list; only the industry-management UI
  extends it).
- The standard country list (§8.1.2).
- Exactly six companies, each with `name`, `industry_id`, `website`,
  `contact_email`, `contact_phone`, `description`, and exactly one Headquarters
  location (label, city, `country_code` from the list, type `Headquarters`):

  | Company | Industry | HQ city | Country |
  |---------|----------|---------|---------|
  | Toyota Motor | Manufacturing | Toyota City | JP |
  | Samsung Electronics | Technology | Seoul | KR |
  | HSBC | Finance | London | GB |
  | Novartis | Healthcare | Basel | CH |
  | Shell | Energy | London | GB |
  | Carrefour | Retail | Paris | FR |

  (Shell's HQ is London, UK → `GB`, per the §8.1.2 note.)

- Real supporting content per company, keyed by name in `seed.py`:
  - One or two further real locations (Office/Plant; deliberately no GB/FR
    offices on non-GB/FR companies so the country filter stays stable).
  - Two references each: a Wikipedia article and an official
    about/company-profile page, with `added_by = admin@localhost`.
  - Three to five genuine recent news articles with `is_scraped = 0`
    (hand-authored, not scraped).
  - One logo each: raster PNG bytes committed under `backend/data/logos/` and
    copied into artifact storage at seed time as an artifacts row with
    `source = 'logo'` (so the seeded logos render in the UI and embed in
    generated PDFs).
- Seeding happens only when the `companies` table is empty; it never overwrites
  user-entered data. The bootstrap admin user is the one exception to
  seed-on-empty: it is upserted with a fresh password on **every** startup
  (§8.1.2 `users`).

**Manual dev-data flush (Sprint 01).** This sprint changes the schema
(`companies` loses `industry` and `hq_location`; new tables are added), and the
v0.1 SQLite database is **not** migrated. Per scope item u, the operator flushes
the gitignored dev runtime state **once** before the first run of the new build
(performed by Stage 6), then the app seeds from scratch:

```
rm -f data/company_hub.db && rm -rf data/artifacts
```

A later pass enriched the seed with references, news, locations, and logos; any
database seeded before that pass must be flushed the same way to pick up the new
seed content (seeding never runs on a non-empty `companies` table). `./flush.sh`
wraps the flush.

The app never deletes data on a normal restart and seeds only when empty.

---

### 8.2 API Contract Changes

Base path and static-file serving are unchanged (§4). **All `/api/` routes now
require an authenticated session** (scope item a) except `POST /api/auth/login`.
An unauthenticated request to any other `/api/` route returns `401`
`{"detail": "Not authenticated"}`. The frontend is served without auth; the SPA
itself renders the login view when unauthenticated (§8.5, §8.6).

#### 8.2.1 Authentication

- **Credential storage:** `users.password_hash` holds
  `pbkdf2_sha256$<iterations>$<salt_hex>$<hash_hex>` using
  `hashlib.pbkdf2_hmac("sha256", ...)`, a 16-byte random salt, and 600,000
  iterations.
- **Session cookie:** on successful login the backend creates a `sessions` row
  with an opaque `secrets.token_urlsafe` token and sets an HttpOnly cookie
  `session=<token>` (`Path=/`, `SameSite=Lax`; not `Secure`, because the dev
  server is plain http on localhost). Sessions are DB-backed and survive
  restarts.
- **Auth dependency:** every protected route reads the `session` cookie, looks
  up the session row and its user, and returns `401` when absent/invalid.

##### `POST /api/auth/login`

Public. Request body:

```json
{ "email": "admin@localhost", "password": "<printed at startup>" }
```

- `200` — on success: `{ "id": 1, "email": "admin@localhost" }`; sets the
  `session` cookie.
- `401` — unknown email or wrong password: `{ "detail": "Invalid email or password" }`.

##### `GET /api/auth/me`

- `200` — current session user: `{ "id": 1, "email": "admin@localhost" }`.
- `401` — no valid session.

##### `POST /api/auth/logout`

- `204` — deletes the session row and clears the cookie. Idempotent: a missing
  session still returns `204`.

#### 8.2.2 Reference data

##### `GET /api/industries`

- `200` — array of `{ "id": 1, "name": "Manufacturing" }`, sorted by name. Used
  by the company add/edit form and the industry-management view.

##### `POST /api/industries`

Request: `{ "name": "Aerospace" }` (required, non-empty).
- `201` — `{ "id": 7, "name": "Aerospace" }`.
- `422` — empty/blank name.
- `409` — name already exists: `{ "detail": "Industry already exists" }`.

##### `PUT /api/industries/{id}`

Rename. Request: `{ "name": "Aerospace & Defense" }`.
- `200` — `{ "id": 7, "name": "Aerospace & Defense" }`. Companies using this
  industry resolve the new label automatically (they store `industry_id`).
- `404` — industry does not exist.
- `409` — the new name is already used by another industry.
- No `DELETE` exists (out of scope).

##### `GET /api/countries`

- `200` — array of `{ "code": "GB", "name": "United Kingdom" }`, sorted by name.
  Used by the location editor and the list country filter.

#### 8.2.3 Companies (modified)

Company payload shape (list items and profile):

```json
{
  "id": 1,
  "name": "Toyota Motor",
  "industry": { "id": 1, "name": "Manufacturing" },
  "hq_location": "Toyota City, JP",
  "website": "https://...",
  "contact_email": "...",
  "contact_phone": "...",
  "description": "...",
  "created_at": "2026-09-04T00:00:00Z",
  "updated_at": "2026-09-04T00:00:00Z",
  "is_complete": true,
  "artifacts_count": 0,
  "logo_url": null
}
```

- `industry`: nested `{ id, name }`, or `null` when unset. Renames propagate
  automatically (the label is resolved at read time).
- `hq_location`: **derived**, never stored — `"<city>, <country_code>"` of the
  company's Headquarters location, or `null` when it has none. Replaces the
  v0.1 free-form `hq_location` field in all payloads.
- `logo_url`: URL of the logo object (`/api/artifacts/<id>/content`), or `null`
  when none. Listed to enable logo display in the list/profile.
- `artifacts_count`: counts non-logo artifacts only (`upload` + `generated`).

##### `GET /api/companies`

List, now with optional multi-country filtering in addition to the existing
name search:

- `?q=<text>` — unchanged (§4): case-insensitive name substring match.
- `?countries=GB,FR` — comma-separated ISO alpha-2 codes. **OR** semantics: the
  company is included when **any** of its locations has a `country_code` in the
  selected set; each company appears once (DISTINCT). Companies with no
  locations are excluded whenever this filter is active.
- Both filters combine with AND (`?q=shell&countries=GB,FR`).
- Unknown/empty codes in `countries` simply match nothing.
- Response `200` — array of company list items (shape above, no `locations`
  array). Ordered by `id` ascending as before.

##### `POST /api/companies` and `PUT /api/companies/{id}`

Request body (all optional except `name`):

```json
{
  "name": "Acme Corp",
  "industry_id": 1,
  "website": "https://acme.example",
  "contact_email": "hello@acme.example",
  "contact_phone": "+49 30 1234 5678",
  "description": "Industrial components."
}
```

- `industry_id`: optional integer; must reference an existing industry (`422`
  otherwise). `null`/absent = no industry.
- **Locations are not part of these payloads.** They are managed exclusively
  through the locations sub-resource (§8.2.4). `PUT` remains a full replace of
  the structured fields above only.
- Responses `201` / `200` with the company shape. Errors: `404` (PUT of an
  unknown company), `422` (`name` missing/empty, unknown `industry_id`).

##### `GET /api/companies/{id}`

Profile. Returns the company shape plus:

```json
{
  "...company fields (incl. logo_url)...",
  "locations": [
    { "id": 1, "company_id": 1, "label": "Global HQ", "address": "1 Motomachi",
      "city": "Toyota City", "country_code": "JP", "country_name": "Japan", "type": "Headquarters" }
  ],
  "references": [
    { "id": 1, "company_id": 1, "title": "...", "url": "https://...",
      "description": "...", "added_by": "admin@localhost",
      "created_at": "...", "updated_at": "..." }
  ],
  "news": [
    { "id": 1, "company_id": 1, "title": "...", "source": "...", "url": "https://...",
      "published_at": "2026-08-01", "summary": "...", "is_scraped": false,
      "created_at": "...", "updated_at": "..." }
  ],
  "artifacts": [ "...non-logo artifact rows (§4), source 'upload' or 'generated'..." ]
}
```

- `locations` ordered by `id` ascending; `references` and `news` ordered by
  `id` descending (newest first); `artifacts` as in §4 except logos are
  excluded.
- Errors: `404` — company does not exist.

##### `DELETE /api/companies/{id}`

Unchanged (§4): deletes the company and cascades to its locations, references,
news, and artifact rows; the storage service removes the company's
`data/artifacts/<company_id>/` directory (including any logo bytes).

#### 8.2.4 Locations sub-resource

##### `POST /api/companies/{company_id}/locations`

Request:

```json
{ "label": "Global HQ", "address": "1 Main St", "city": "London", "country_code": "GB", "type": "Headquarters" }
```

(`address` optional; `label`, `city`, `country_code`, `type` required.)

- `201` — location payload (see §8.2.3 shape, with `country_name`).
- `404` — company does not exist.
- `422` — missing/empty required field; unknown `country_code`; invalid `type`;
  or adding a second Headquarters (the existing Headquarters is left unchanged).

##### `PUT /api/companies/{company_id}/locations/{location_id}`

Full replace of `label`, `address`, `city`, `country_code`, `type`.
- `200` — updated location payload.
- `404` — company or location not found (a location never belongs to a company
  other than the path's `company_id`).
- `422` — same validation as `POST`, including "second Headquarters" if this
  edit would make it a Headquarters while another location already is one.

##### `DELETE /api/companies/{company_id}/locations/{location_id}`

- `204` — removed (removing the Headquarters is allowed; the company may end up
  with zero locations).
- `404` — company or location not found.

#### 8.2.5 References sub-resource

##### `POST /api/companies/{company_id}/references`

Request: `{ "title": "...", "url": "https://...", "description": "..." }`
(`title` and `url` required; `description` optional). `added_by` is set from
the signed-in session user's email; `created_at`/`updated_at` are set
server-side.

- `201` — reference payload (§8.2.3 shape).
- `404` — company does not exist.
- `422` — missing/empty `title` or `url`.

##### `PUT /api/companies/{company_id}/references/{reference_id}`

Request: `{ "title", "url", "description" }` (full replace of editable fields).
Preserves `added_by` and `created_at`; refreshes `updated_at`.
- `200` — updated reference payload.
- `404` — company or reference not found.

##### `DELETE /api/companies/{company_id}/references/{reference_id}`

- `204` — removed.
- `404` — company or reference not found.

#### 8.2.6 News sub-resource

##### `POST /api/companies/{company_id}/news`

Request:

```json
{
  "title": "...", "source": "...", "url": "https://...",
  "published_at": "2026-08-01", "summary": "...", "is_scraped": false
}
```

(`title`, `source`, `url`, `published_at` required; `summary` optional;
`is_scraped` optional, defaults `false` — the UI never sets it, automated
workflows may set `true`.)

- `201` — news payload (§8.2.3 shape).
- `404` — company does not exist.
- `422` — missing/empty required field or malformed `published_at`.

##### `PUT /api/companies/{company_id}/news/{news_id}`

Request: same fields as `POST`; `is_scraped` optional — when omitted, the
current value is preserved.
- `200` — updated news payload (`updated_at` refreshed; `created_at` and
  `is_scraped` semantics preserved per brief).
- `404` — company or news record not found.
- `422` — invalid fields.

##### `DELETE /api/companies/{company_id}/news/{news_id}`

- `204` — removed.
- `404` — company or news record not found.

#### 8.2.7 Logos

##### `POST /api/companies/{company_id}/logo`

`multipart/form-data`, one file part named `file` (same upload mechanism as the
§4 artifact upload).
- Replaces any existing logo: the previous `source = 'logo'` artifact row and
  its bytes are deleted, then the new bytes are stored and a new logo row is
  inserted (single transaction).
- `201` — the logo artifact row (§4 artifact-row shape, `source: "logo"`,
  `download_url`). The company's `logo_url` points here.
- `404` — company does not exist.
- `415` — uploaded content-type is not an image (`image/*`):
  `{ "detail": "Logo must be an image" }`.
- `422` — missing file part or empty filename.

##### `DELETE /api/companies/{company_id}/logo`

- `204` — logo removed (row + bytes).
- `404` — no logo is set for the company.

##### Generic artifact endpoints

`GET /api/companies/{company_id}/artifacts`, `GET /api/artifacts/{id}/content`,
and `DELETE /api/artifacts/{id}` are unchanged (§4) except that the list
endpoint excludes `source = 'logo'` rows. The generic `DELETE` on a logo row is
equivalent to removing the logo.

#### 8.2.8 Document generation (modified)

`POST /api/companies/{company_id}/documents/generate` — unchanged contract
(synchronous, `201`/`422`, response body shape per §4), with these content
changes:

- **Completeness gate:** uses the new completeness rule (§8.1.4).
- **Content:** the summary now presents `name`, `industry` (label), locations
  (Headquarters first, then the rest, e.g. "Global HQ — Toyota City, JP"),
  `website`, `contact_email`, `contact_phone`, `description` — replacing the
  removed free-form `hq_location`.
- **Logo:** when the company has a logo, its bytes are embedded in the PDF
  (fpdf2 image). A missing logo is simply omitted; generation must not fail on
  its absence.

---

### 8.3 Project / File Structure Additions

New/changed files beyond the §1 tree:

```
backend/
├── routers/
│   ├── auth.py            # login / logout / me + session dependency (new)
│   ├── industries.py      # industry list/add/rename (new)
│   ├── reference.py       # GET /api/countries (new)
│   ├── locations.py       # locations sub-resource CRUD (new)
│   ├── references.py      # references sub-resource CRUD (new)
│   ├── news.py            # news sub-resource CRUD (new)
│   └── artifacts.py       # extended: POST/DELETE /api/companies/{id}/logo
├── db.py                  # extended schema (new tables), seed calls
├── schemas.py             # new Pydantic request models
├── models.py              # new row→dict helpers, new completeness rule
├── data/seed.py           # redefined seed (real companies + industries + countries)
└── services/pdf.py        # updated summary fields + logo embedding
frontend/
├── js/
│   ├── login.js           # login view + session gate (new)
│   ├── industries.js      # industry-management view (new)
│   ├── api.js             # extended endpoints (extended)
│   ├── app.js             # auth bootstrapping, logout, nav (extended)
│   ├── list.js            # country filter, logo thumbnails (extended)
│   ├── profile.js         # locations, references, news, logo sections (extended)
│   └── form.js            # industry dropdown, locations editor (extended)
└── index.html             # nav: Industries, logout (extended)
```

### 8.4 Module Boundary Changes

| Module | Change |
|--------|--------|
| `backend/routers/auth.py` | Owns login/logout/me and the `get_current_user` dependency. No business data. |
| `backend/routers/industries.py` | Owns industry list/add/rename (no delete) over the `industries` table. |
| `backend/routers/reference.py` | Owns the countries reference list (read-only). |
| `backend/routers/locations.py` | Owns location CRUD incl. HQ-uniqueness validation. |
| `backend/routers/references.py`, `news.py` | Own their sub-resource CRUD; `added_by` comes from the session. |
| `backend/routers/artifacts.py` | Adds the logo upload/replace/remove endpoints (reuses storage). |
| `backend/services/pdf.py` | Reads the locations/logos it is given; still no HTTP/DB. |
| `backend/data/seed.py` | Seeds industries + countries + six real companies with one HQ each, plus per-company locations, references, news, and logos. |
| `frontend/*` | Adds login gate, industry management, locations editor, references/news sections, logo UI, country filter. |

Ownership rules from §2 (routers do no raw SQL/file-bytes handling; storage owns
bytes; schemas own the contract) are unchanged.

### 8.5 Backend / Frontend Responsibility Changes

**Backend (new):** implement authentication (bootstrap admin, PBKDF2 hashing,
DB-backed session cookie, 401-gating every `/api/` route except login);
industries and countries reference data; locations, references, and news
sub-resource CRUD; logo upload/replace/remove via the existing storage; the
redefined seed; the redefined completeness rule; and the updated PDF generation
(new fields + logo).

**Frontend (new):** on load call `GET /api/auth/me`; when `401`, render the
login view and gate all other views behind an authenticated session. Treat a
`401` from any API call as a return to the login view. Add a logout action. Add:
an industry-management view (add/rename); an industry dropdown (not free-text)
and a locations editor in the add/edit form; a multi-select country filter on
the list; locations/references/news sections with add/edit/remove on the
profile; and logo upload/replace/remove controls plus logo display on the list
and profile. Replace all free-form `hq_location` display with the derived
`hq_location` / locations data. The SPA remains a pure API client with no
authoritative client-side state.

### 8.6 Component Interactions & State Flow

```
Browser (SPA)
   │  boot → GET /api/auth/me
   │    401 ────────────────► login view
   │    200 ─► main views (all data via authenticated /api calls)
   │  any /api call → 401  ─► return to login view
   ▼
FastAPI routers (auth / industries / reference / locations / references / news
                / artifacts(+logo) / companies / documents)
   │  ├─ auth dependency: session cookie → sessions → users (else 401)
   │  ├─ services/pdf.py (fpdf2) ──► bytes (+ logo bytes when set) → storage
   │  ├─ services/storage.py ──► data/artifacts/<company_id>/...
   │  └─ db.py (sqlite3) ──► data/company_hub.db
```

**State flow additions:** The SPA holds no session state itself; on boot it asks
`/api/auth/me` and renders the login view or the app accordingly. Editing a
company's industry or a location's country re-fetches the list/profile, which
resolve the controlled labels (`industry.name`, `country_name`) at read time — a
rename in the industry-management view is reflected everywhere on the next
fetch. The country filter re-issues `GET /api/companies?countries=...`; clearing
it restores the full list. The add/edit form manages locations through the
locations sub-resource; profile edits to references/news/logos hit their
sub-resources and re-fetch the profile. Generation embeds the current logo
bytes; regenerating after a logo change reflects the new logo.

### 8.7 Explicitly Unchanged / Out of Scope

- v0.1 browse/search-by-name, profile view, artifact upload/list/download/delete
  (non-logo), and the document-generation flow (except the content/completeness/
  logo changes above) are unchanged.
- No signup, roles/permissions, password reset, or multi-user administration
  (scope item c). `admin@localhost` is the only user.
- No country-management UI (fixed list only). No industry delete (add/rename only).
- No scraping of news, references, or logos (items n, q).
- No JWT/OAuth/external auth; cookie sessions only.
- Entry point `backend.app:app`, `run.sh`, Python version, dependency set, and
  the `data/` storage layout are unchanged (Stage 4: no environment changes).
- The completeness rule and seed definition are intentionally changed per
  §8.1.4/§8.1.5 (items s, t, u) — in-scope, not regressions.

### 8.8 Open Design Decisions / Contract Notes (Sprint 01)

1. **UK vs GB:** scope/briefs say "UK"; the standard list uses the ISO code
   `GB` (name "United Kingdom"). All references to the seed country map to `GB`.
2. **Admin password regeneration:** a fresh complex password is generated,
   hashed, and printed on **every** startup; previously displayed passwords
   become invalid after a restart.
3. **Session lifetime:** sessions have no expiry this sprint and survive
   restarts; they end on logout (or the DB flush).
4. **Logo exclusivity:** the generic Files/artifacts list and `artifacts_count`
   exclude `source = 'logo'` rows; logos are surfaced via `logo_url`.
5. **Country filter:** comma-separated `?countries=` codes, OR semantics,
   DISTINCT results, companies with no locations excluded while active.
6. **Company payloads:** `hq_location` is now derived from the Headquarters
   location and is never stored; locations live only in the `locations` table.
7. **Manual dev-DB flush** (scope item u) is a documented operator action, not
   app startup behavior (§8.1.5).
