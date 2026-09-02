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
│       └── seed.py                # seed companies (structured data only)
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

On first startup (empty `companies` table), `backend/data/seed.py` inserts a
small set of realistic companies (see `concept.md`: a small set of realistic
firms). Seed data includes structured fields only — no artifacts are seeded.
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
