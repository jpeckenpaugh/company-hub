# Company Hub — v0.1 vs Sprint 01

Concise feature-set comparison between the v0.1 build and the Sprint 01
enhancement pass. Full details: `README.md`, `docs/architecture.md` (§8),
`docs/verification-report.md` (Sprint 01 section).

## Feature-set changes

| Area | v0.1 | Sprint 01 |
|---|---|---|
| **Authentication** | None | Email/password login required app-wide; bootstrap `admin@localhost` with a console-printed auto-generated password; DB-backed HttpOnly session cookie |
| **Industry** | Free-form text field | Controlled value from a seeded six-item standard list; add/rename via a management UI (no delete); renames propagate to companies |
| **Headquarters** | Single free-form `hq_location` field | Zero or more locations (label, city, address, country from a standard 83-entry list, type); at most one Headquarters; HQ derived as "City, CC" |
| **Country filter** | None | Companies list filters by country (multi-select, OR), combinable with name search |
| **References** | None | Per-company curated resource links (title, URL, description, added-by, timestamps) |
| **News** | None | Per-company news articles (title, source, URL, publication date, summary) with a scraped-status flag for automated workflows |
| **Logos** | None | One designated logo per company; upload/replace/remove from the UI; shown on profile and list; embedded in generated PDFs when possible |
| **Company completeness** | All seven fields non-empty | Redefined: name + industry + website/email/phone/description (locations and logos do not count) |
| **Seed data** | Small set of fictitious companies | Six real companies (Toyota, Samsung, HSBC, Novartis, Shell, Carrefour) — one of the biggest players per seeded industry. Each is seeded with a Headquarters plus further real locations, two references (Wikipedia + official about page), several genuine recent news articles, and a committed raster logo |
| **API auth** | All `/api` routes public | All `/api` routes require a session except `POST /api/auth/login`; content endpoints gated too |
| **Browser verification** | Static review + live curl only | Persistent CDP headless-Chrome suite (34 checks) covering login, filters, editors, and logo flows |

## Unchanged (no regression)

- Browse/search-by-name list, company profile, add/edit, artifact
  upload/download/delete, and PDF generation flows all still work (now
  auth-gated).
- Stack (FastAPI + SQLite, Bootstrap SPA, local object storage, fpdf2) and the
  setup/run flow are unchanged.
- Seeding never overwrites user data; the Sprint 01 data-model rebuild was a
  one-time, sanctioned flush of gitignored dev state (scope item u).

## Verification summary

- **v0.1:** PASS — 0 failures, 34 checks (static review + live curl).
- **Sprint 01:** PASS — 0 failures, 93 live curl + 51 backend pytest + 34
  browser checks.

See `docs/verification-report.md` for the evidence-backed detail.

---

# Company Hub — Sprint 01 vs Sprint 02

Concise comparison of the changes introduced by the Sprint 02 enhancement pass.
Full details: `README.md`, `docs/architecture.md` (§9),
`docs/verification-report.md` (Sprint 02 section).

## Feature-set changes

| Area | Sprint 01 | Sprint 02 |
|---|---|---|
| **Persistence** | Hand-written `sqlite3` SQL (`backend/db.py`) | Async SQLAlchemy 2.0 ORM (`backend/models/`, `backend/db/`) with versioned Alembic migrations (`backend/alembic/`); non-auth contracts byte-for-byte unchanged |
| **Authentication** | Hand-rolled PBKDF2 + DB session cookies (`backend/routers/auth.py`) | Maintained fastapi-users (`DatabaseStrategy` + `CookieTransport`); JSON login body returning `{access_token, token_type}`; `me` = `{id, email, is_superuser}` |
| **Bootstrap admin** | Per-startup auto-generated, re-randomized password | Stable account; password created once and persisted (`COMPANY_HUB_ADMIN_PASSWORD` override or generated-and-printed); not re-randomized |
| **Password change** | None | Self-service `POST /api/auth/change-password` with a `#/password` UI view (new ≥ 8-char policy) |
| **User accounts** | Single admin only | Multiple accounts via superuser-only `POST /api/auth/users`; no self-service signup |
| **Session lifetime** | Sessions persisted until logout/flush (no expiry) | Defined server-side lifetime (default 7 days, `COMPANY_HUB_SESSION_TTL`) with immediate server-side revocation |
| **OAuth readiness** | None | Schema-only `oauth_accounts` table (Google-oriented); no OAuth routes yet |
| **Login response** | `200 {id, email}` | `200 {access_token, token_type:"bearer"}` + HttpOnly `session` cookie |

## Unchanged (no regression)

- All non-auth API contracts, responses, and semantics (browse/search, profile,
  add/edit, locations/references/news, logo, artifacts/object storage, document
  generation) are unchanged.
- Seed content and seeding rules are unchanged; seeding still runs only on an
  empty `companies` table.
- The cookie-based sign-in experience and the login screen for unauthenticated
  users are preserved.
- The Sprint 02 data-model change was a one-time, sanctioned flush of gitignored
  dev state to establish the migration baseline (scope item n).

## Verification summary

- **Sprint 01:** PASS — 0 failures, 93 live curl + 51 backend pytest + 34
  browser checks.
- **Sprint 02:** PASS — 0 failures, 64 backend pytest + 36 CDP browser + 28 live
  curl checks.

See `docs/verification-report.md` for the evidence-backed detail.