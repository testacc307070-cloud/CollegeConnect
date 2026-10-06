# CollegeConnect

CollegeConnect is a Flask and MySQL web application for exploring Tamil Nadu Engineering Admissions (TNEA) historical outcomes and comparing college/branch choices. It uses 2021–2025 admission records to produce indicative cutoff- and rank-based predictions. Predictions are historical guidance, not admission guarantees.

## Current interface

The navigation has three menus:

1. **Predictor** — choose Aggregate Cutoff Mark or TNEA State Rank, then filter by community, multiple districts, multiple branches, and an optional specific college. There is no Predictor quota-category field or institutional-tier filter.
2. **Choice Optimizer** — build and balance a DoTE choice list, review the Reach/Target/Safe distribution, copy the formatted list, or export it as CSV or PDF.
3. **TNEA Historical Records** — query historical cutoff marks or closing ranks for selected years and communities, with searchable multi-select district and branch filters and an optional specific college. Results are grouped by **Year → Community** and paginated.

Additional Predictor result actions show a 2021–2025 trend chart and alternative branches at the same campus. The light/dark theme toggle saves the preference in browser local storage.

## Implementation overview

| Area | Current implementation |
|---|---|
| Frontend | Single-page HTML, vanilla JavaScript, and CSS in `frontend/`; no frontend package manager is required. |
| Backend | Flask application in `backend/app.py`, with prediction, historical-record, explanation, and supporting route modules. |
| Database | MySQL 8.4 with `colleges`, `branches`, and `historical_admissions` tables; DDL is in `database/schema.sql`. |
| Source data | `data/integrated/tnea_integrated_master.csv`: 16,174 source offerings from 2021–2025, expanded by the loader into 113,218 community-level fact rows. |
| Analysis | Deterministic scoring, cutoff/rank history, five-year trend data, campus branch alternatives, and college-tier classification. |
| Explanations | Google Gemini integration is optional; deterministic explanations are available when no Gemini API key is configured. |

The current dataset contains 467 colleges, 116 branches, and the seven communities OC, BC, BCM, MBC, SC, SCA, and ST. Historical records use the General quota baseline represented in the source data. The backend retains a quota-advisory response path covered by the system verifier; this does not represent a separate quota dataset or a Predictor quota selector.

## Requirements

- Windows 10/11 for the provided `.bat` MySQL launcher; install MySQL Server 8.4 at its standard Windows location (`C:\Program Files\MySQL\MySQL Server 8.4`). On other operating systems, install and start MySQL separately.
- Python 3.11.
- MySQL Server 8.4, reachable using the connection settings in `.env`.
- Node.js is optional and is used by the verification script to check JavaScript syntax.
- A Gemini API key is optional.

## Setup and run (Windows)

From PowerShell:

```powershell
git clone https://github.com/testacc307070-cloud/CollegeConnect.git
cd CollegeConnect
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Edit `.env` to match the local MySQL host, port, database, user, and password. Leave `GEMINI_API_KEY` blank to use deterministic explanations, or set it to a valid key to enable Gemini-backed explanations. Do not commit `.env`.

Start the local MySQL server in one terminal:

```powershell
.\start_mysql.bat
```

On first start, this script initializes `data\mysql_data` locally; that runtime directory is intentionally ignored by Git. A fresh data directory uses MySQL's `--initialize-insecure` option, so the local root account initially has a blank password. Keep this development database local and set `.env` to match any changes to the MySQL account. The launcher expects MySQL Server 8.4 at the standard path above. Alternatively, start an existing MySQL 8.4 service and skip the launcher.

In another terminal, with the project virtual environment active, load the schema and dataset, then start the Flask app:

```powershell
python scripts\load_database.py
python backend\app.py
```

The loader creates/populates the database and runs tier classification. The application is served at <http://127.0.0.1:5000/>.

## Verification

With MySQL initialized, loaded, and running:

```powershell
python scripts\verify_system.py
python scripts\verify_theme_system.py
python scripts\test_scoring.py
```

The end-to-end verifier exercises database integrity, prediction and history APIs, optimizer, explanation fallbacks, and frontend assets. The theme verifier checks the light/dark implementation. To run trend, campus-branch, optimizer, CSV, and PDF endpoint checks, start the Flask app first and run this script from a second terminal:

```powershell
python scripts\test_modal_and_exports.py
```

The export test creates `data\test_exported_choice_list.csv` and `.pdf`; these generated files are ignored by Git.

## API reference

The Flask service exposes JSON APIs including:

| Endpoint | Method | Purpose |
|---|---|---|
| `/api/health`, `/api/db-test` | GET | Application and database health checks. |
| `/api/districts`, `/api/branches`, `/api/tiers`, `/api/colleges` | GET | Populate filters and search colleges. |
| `/api/predictions` | GET | Aggregate-cutoff prediction results. |
| `/api/rank-predictions` | GET | State-rank prediction results. |
| `/api/historical-records` | GET | Year/community-grouped historical cutoff or rank records; supports repeated `year`, `community`, `district`, and `branch_code` parameters, optional `college_code`, and pagination. |
| `/api/historical`, `/api/historical-analysis` | GET | Historical outcome and trend data used by Predictor results. |
| `/api/branch-swap` | GET | Alternative branches at the selected campus. |
| `/api/choices/optimize` | GET/POST | Optimize a submitted choice list. |
| `/api/choices/export-pdf` | POST | Generate a PDF choice-list export. |
| `/api/rag-explanation`, `/api/rank-rag-explanation` | GET/POST | Cutoff- and rank-based explanations. |

Choice-list CSV export is generated in the browser; PDF export is handled by the backend. Additional registered compatibility endpoints include `/api/predict`, `/api/combined-predictions`, and `/api/combined-rag-explanation`. A legacy `GET /api/rank-matrix` endpoint remains registered and is covered by the backend verifier, but there is no Rank Matrix menu or page in the current interface.

## Repository map

```text
backend/             Flask app, API routes, database access, scoring, explanations, PDF service
backend/archive/     Archived predictor and choice-allocation implementations
data/integrated/     Required TNEA source dataset
database/            MySQL DDL schema
frontend/            Single-page UI, styles, and browser logic
scripts/             Data loader, tier classifier, tests, and verification tools
.env.example         Safe environment-variable template
requirements.txt     Python dependencies
run_app.bat          Windows Flask launcher
start_mysql.bat      Windows local MySQL launcher
```

For component detail, see [PROJECT_PLAN.md](PROJECT_PLAN.md), [CURRENT_PROJECT_STATE.md](CURRENT_PROJECT_STATE.md), [PROJECT_IMPLEMENTATION_REPORT.md](PROJECT_IMPLEMENTATION_REPORT.md), and [DATABASE_SCHEMA.md](DATABASE_SCHEMA.md).
