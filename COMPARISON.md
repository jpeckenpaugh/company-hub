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