# Verification Report — Company Hub

Stage 8 artifact. Evidence-backed pass/fail verification of the delivered
application (Stage 6 backend + Stage 7 frontend) against the approved
specifications: `concept.md`, `features/briefs/*.md`, and
`docs/architecture.md` (API contract).

- **Date:** 2026-09-02
- **Method:** live API verification via `curl` against `./run.sh` plus static
  review of frontend rendering logic (browser interaction is not automated in
  this environment). Logs and captured responses in `./tmp/verify/`.
- **Environment:** Python 3.12.14 venv (existing, reused); server started via
  `./run.sh` (`uvicorn backend.app:app --host 127.0.0.1 --port 8000`).
- **Result:** **PASS** — 0 failures. 2 checks pass with notes (documented human
  resolutions, not defects). See Limitations at the end.

---

## 1. Checklist derivation

Each check is observable and traceable to a specific requirement. Sources:
concept (`CON`), feature briefs (`B01`–`B05`), architecture/API contract (`API`,
`ENV`, `FE`). The checklist was derived by this stage from the approved
specifications; it was not provided by another role.

### 1.1 Environment & stack (concept.md, requirements.txt, architecture §1/§5)

| # | Check | Requirement | Result |
|---|-------|-------------|--------|
| ENV-1 | `install.sh` provisions a Python 3.11+ venv and installs the pinned deps (fastapi, uvicorn, python-multipart, fpdf2) | Stage 4 + `requirements.txt` | **PASS** |
| ENV-2 | `run.sh` starts the app via `uvicorn backend.app:app --host 127.0.0.1 --port 8000` | architecture §1 entry contract | **PASS** |
| ENV-3 | Runtime dirs `data/` and `data/artifacts/` created at startup | architecture §1 | **PASS** |
| ENV-4 | `data/` is gitignored; all runtime writes stay under `data/` | `.gitignore`, environment-notes | **PASS** |
| ENV-5 | Stack matches concept: FastAPI + SQLite backend, Bootstrap SPA frontend, object storage for files/artifacts, `fpdf2` PDFs | concept.md | **PASS** |

### 1.2 Company API (architecture §4)

| # | Check | Requirement | Result |
|---|-------|-------------|--------|
| API-1 | `GET /api/companies` → `200` JSON array; each item snake_case with `id`, `name`, six optional fields (null when missing), `created_at`, `updated_at`, derived `is_complete`, `artifacts_count` | §4 companies | **PASS** |
| API-2 | Seed data: small set of realistic companies present on first run | concept, §3 | **PASS** |
| API-3 | `GET /api/companies?q=` filters by case-insensitive name substring; no match → `[]` | §4 | **PASS** |
| API-4 | `POST /api/companies` → `201` created company incl. `id`, timestamps, `is_complete`, `artifacts_count` | §4 | **PASS** |
| API-5 | `POST` with missing or blank `name` → `422` | §4 | **PASS** |
| API-6 | `GET /api/companies/{id}` → `200` profile shape incl. `artifacts` array with `download_url` | §4 | **PASS** |
| API-7 | `GET /api/companies/{id}` unknown id → `404` with JSON detail | §4 | **PASS** |
| API-8 | `PUT /api/companies/{id}` → `200` full replace; `updated_at` refreshed; `created_at` unchanged | §4, §6 | **PASS** |
| API-9 | `PUT` blank `name` → `422`; `PUT` unknown id → `404` | §4 | **PASS** |
| API-10 | `PUT` response shape | §4 (see note 1) | **PASS-with-note** |
| API-11 | `DELETE /api/companies/{id}` → `204`; cascades to artifact rows and removes stored files | §3, §4 | **PASS** |
| API-12 | `DELETE` unknown id → `404` | §4 | **PASS** |
| API-13 | `is_complete` derived: false with only `name`, true when all seven fields non-empty | §3, B03 | **PASS** |

### 1.3 Artifact API / object storage (architecture §4, B04, concept)

| # | Check | Requirement | Result |
|---|-------|-------------|--------|
| API-14 | Upload → `201` artifact row with `source:"upload"`, `download_url`; bytes stored on disk under `data/artifacts/<company_id>/` (UUID `stored_filename`), metadata in DB only | §3, §4, B04 | **PASS** |
| API-15 | Upload to unknown company → `404`; missing file part → `422` | §4 | **PASS** |
| API-16 | `GET /api/companies/{id}/artifacts` lists newest-first, scoped to one company; other companies see none of its items | §3, §4, B04 | **PASS** |
| API-17 | `GET /api/artifacts/{id}/content` → `200` streams bytes with `Content-Disposition: attachment` and stored `content-type` | §4 | **PASS** |
| API-18 | Content download / delete of unknown artifact → `404` | §4 | **PASS** |
| API-19 | `DELETE /api/artifacts/{id}` → `204` removes DB row and on-disk bytes | §4, B04 | **PASS** |
| API-20 | Deleting a company removes its artifact rows and its storage folder | §3 (cascade) | **PASS** |

### 1.4 Document generation (architecture §4, B05, concept)

| # | Check | Requirement | Result |
|---|-------|-------------|--------|
| API-21 | Generate for complete company → `201` with `{success:true, message, artifact:{...source:"generated"}}`; valid PDF artifact appears in the profile | §4, B05 | **PASS** |
| API-22 | Generate for incomplete company → `422` with exact body `{success:false, message:"Not enough information to generate a document", artifact:null}` | §4 failure rule | **PASS** |
| API-23 | Generate for unknown company → `404` | §4 | **PASS** |
| API-24 | Regeneration creates a fresh artifact row from current data (bytes differ after edit); old documents remain | §4, B05 | **PASS** |
| API-25 | Generated PDF is a valid, simple summary of the company's structured fields | concept, B05, §7.3 | **PASS** |

### 1.5 Frontend static review (architecture §5, B01–B05)

Static review of `frontend/` rendering logic; the exact API calls each view
makes were exercised live via `curl` (see evidence).

| # | Check | Requirement | Result |
|---|-------|-------------|--------|
| FE-1 | SPA shell served by FastAPI at `/` (`index.html` + assets with correct MIME types) | §5 | **PASS** |
| FE-2 | List view: fetches `GET /api/companies`, renders name/industry/hq/artifact count/completeness badge, click-through to `#/companies/{id}`, live name search | B01, §5 | **PASS** |
| FE-3 | Profile view: fetches `GET /api/companies/{id}`, shows all structured fields, completeness indicator, related content with download/open, back-to-list | B02 | **PASS** |
| FE-4 | Add/edit form: all seven fields, name required, save/cancel; create via `POST`, edit via full-replace `PUT`; `422` rendered; no silent data loss | B03, §5 | **PASS** |
| FE-5 | Artifact UI on profile: upload, list, delete (with confirm), download | B04 | **PASS** |
| FE-6 | Generate action with inline success/failure feedback (incl. the `422` "not enough information" message) | B05 | **PASS** |
| FE-7 | No client-side persistence; every view re-fetches from the API so list and profile stay consistent | §6, B01 | **PASS** |
| FE-8 | All dynamically injected text escaped (single `esc()` helper) | security | **PASS** |
| FE-9 | All five JS modules pass `node --check` | — | **PASS** |
| FE-10 | No delete-company UI in the SPA | B03/B04 scope (see note 2) | **PASS-with-note** |
| FE-11 | Generate button always enabled, incl. incomplete companies | B05 (see note 3) | **PASS-with-note** |

---

## 2. Evidence

### 2.1 Environment / run

- `./run.sh` started the app; `GET /` → `200` and `/openapi.json` → `200`.
  OpenAPI lists all documented routes:
  `/api/artifacts/{artifact_id}`, `/api/artifacts/{artifact_id}/content`,
  `/api/companies`, `/api/companies/{company_id}`,
  `/api/companies/{company_id}/artifacts`,
  `/api/companies/{company_id}/documents/generate`.
- `data/` and `data/artifacts/` created at startup; `data/` is in `.gitignore`.

### 2.2 Company API

- `GET /api/companies` → `200`, 6 seeded companies. Sample item
  (`tmp/verify/a1-list.json`):
  ```json
  {
    "id": 1,
    "name": "Acme Manufacturing",
    "industry": "Manufacturing",
    "hq_location": "Berlin, DE",
    "website": "https://acme.example.com",
    "contact_email": "hello@acme.example.com",
    "contact_phone": "+49 30 1234 5678",
    "description": "Industrial components and precision machining for European OEMs.",
    "created_at": "2026-09-02T03:20:36Z",
    "updated_at": "2026-09-02T03:20:36Z",
    "is_complete": true,
    "artifacts_count": 0
  }
  ```
  Shape confirmed on every item: `id` present, snake_case keys, derived
  `is_complete`, `artifacts_count`.
- Search: `?q=lumen` → `["Lumen Financial"]`; `?q=ACME` → `["Acme Manufacturing"]`
  (case-insensitive); `?q=o` → 4 substring matches; `?q=xyz` → `[]`.
- `POST /api/companies` (`tmp/verify/c1-create.json`) → `201`, returned
  `{id, name, is_complete, artifacts_count}`. Missing `name` → `422`
  (`"Field required"`); blank `name` → `422` (`"name must not be empty"`).
- `GET /api/companies/1` (`tmp/verify/b1-profile.json`) → `200` profile with
  `artifacts: []`. `GET /api/companies/999` → `404 {"detail":"Company not found"}`.
- `PUT /api/companies/9` (`tmp/verify/c4-put.json`) → `200`; fields updated,
  `updated_at` changed. Blank name → `422`; unknown id → `404`.
- Completeness (`tmp/verify/d1-incomplete.json`): company created name-only →
  `is_complete:false`; after `PUT` filling all fields → `is_complete:true`.
- `DELETE /api/companies/9` → `204`; `DELETE /api/companies/999` → `404`.
- Cascade: company 1 holding 3 artifacts deleted → `204`; `artifacts` rows for
  company 1 → 0; `data/artifacts/1/` removed from disk.

### 2.3 Artifacts / object storage

- Upload (`tmp/verify/e1-upload.json`) → `201`:
  ```json
  {
    "id": 3, "company_id": 1, "original_name": "sample.txt",
    "content_type": "text/plain", "size_bytes": 31, "source": "upload",
    "download_url": "/api/artifacts/3/content"
  }
  ```
- DB holds metadata only (`stored_filename` = UUID `5c47f75f…f8.txt`,
  `size_bytes`, `source`); bytes live on disk at
  `data/artifacts/1/5c47f75ff1e44d55b84c4c2da4e685f8.txt`. Confirms the
  structured-vs-object separation in concept.md.
- Download → `200`, `Content-Type: text/plain`, `Content-Disposition: attachment;
  filename="sample.txt"`, body matches uploaded bytes.
- Scope: company 2 artifact list → `[]` after company 1 upload (0 items leak).
- Upload to unknown company → `404`; missing `file` part → `422`.
- Delete artifact → `204`; subsequent DB row count 0 and on-disk file removed.
- Unknown artifact content/delete → `404`.

### 2.4 Document generation

- Generate for complete company 1 (`tmp/verify/f1-gen.json`) → `201`:
  ```json
  {
    "success": true, "message": "Document generated",
    "artifact": {"id": 4, "company_id": 1,
      "original_name": "Acme Manufacturing-summary.pdf",
      "content_type": "application/pdf", "size_bytes": 38925,
      "source": "generated", "download_url": "/api/artifacts/4/content"}
  }
  ```
- Downloaded PDF starts with `%PDF-1.3` (valid), served as
  `application/pdf` with attachment disposition. The artifact appears in
  `GET /api/companies/1` → `.artifacts` with `source:"generated"`.
- Incomplete company → `422` with exact failure body
  `{"success":false,"message":"Not enough information to generate a document","artifact":null}`.
- Unknown company → `404`.
- Regeneration after editing the company produced a new artifact row (total 3)
  and new bytes (39121 vs 38925), reflecting the updated description.

### 2.5 Frontend static review

- `GET /` serves the SPA shell (`<title>Company Hub</title>`).
- All static assets serve `200` with correct MIME types (CSS, JS modules,
  Bootstrap, icons, woff2 font).
- `node --check` passes for all five JS modules (`api.js`, `app.js`, `form.js`,
  `list.js`, `profile.js`).
- `api.js` maps to the documented endpoints exactly: `GET/POST /api/companies`,
  `GET/PUT /api/companies/{id}`, `POST /api/companies/{id}/artifacts`,
  `DELETE /api/artifacts/{id}`, `POST /api/companies/{id}/documents/generate`,
  plus `download_url` for content. Every one of these calls was exercised live
  above with the documented status/body shapes.
- `app.js` routes views client-side via hash (`#/`, `#/companies`, `#/companies/{id}`,
  `#/companies/new`, `#/companies/{id}/edit`) and escapes all injected text.
- No client-side persistence: each view re-fetches on render, so the list and
  profile stay consistent with backend state (Briefs 01/02).

---

## 3. Failures

**None.** All checks pass. No requirement failures were observed.

## 4. Notes (pass-with-note items, all previously human-resolved)

1. **API-10 — `PUT` response shape.** The contract text (§4) says `PUT` returns
   "the updated company profile shape", but the backend returns the list-item
   shape (no `artifacts` array), identical to `POST`. This was an explicit human
   resolution recorded by the Backend Engineer in Stage 6 (`summaries/06-backend.md`):
   "`PUT` returns the list-item shape (no `artifacts` array), consistent with
   `POST`, per human resolution." The SPA only consumes `id`/fields from the
   `PUT` response, so behavior is correct. Recorded as a documented deviation,
   **not a failure.**
2. **FE-10 — No delete-company UI.** The SPA intentionally exposes no
   company-delete button; deletion is left to the API/automated workflows. This
   was an explicit human resolution recorded by the Frontend Engineer in Stage 7
   (`summaries/07-frontend.md`, Q2) and is within brief scope (B03/B04 require
   add/edit and artifact removal, not company removal). The `DELETE
   /api/companies/{id}` endpoint exists and works (API-11/12). **Not a failure.**
3. **FE-11 — Generate button always enabled.** The Generate action is enabled for
   all companies, including incomplete ones; the frontend renders the backend's
   `422` failure message inline when generation is not possible. This was an
   explicit human resolution recorded in Stage 7 (Q3) and satisfies Brief 05's
   "user is told when generation succeeds or fails". **Not a failure.**

## 5. Limitations

- **Frontend browser interaction was not exercised by an automation tool** in
  this environment. The frontend was verified by static review of rendering
  logic plus live exercise (via `curl`) of every API call the SPA makes, and
  confirmation that all assets serve with correct MIME types and that all JS
  passes a syntax check. Clicking/DOM behavior was not automated.
- Search is name-only per the architecture (`?q=` on `name`), as recorded in
  Stages 6 and 7.
- Generated PDFs embed text with a Unicode font when present on the host (here
  macOS Arial Unicode), so the company text is CID-encoded and not visible as
  plaintext in the file; the PDF is valid (`%PDF-1.3`) and reflects current
  company data (byte size changes after edits).
- Testing mutated the local `data/`; it was restored to the pristine 6-company
  seeded state (0 artifacts) after verification. `data/` is gitignored.