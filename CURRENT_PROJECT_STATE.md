# CollegeConnect — Current Project State

**Updated:** October 6, 2026

## Implemented interface

The current frontend has three menus:

- **Predictor:** switches between Aggregate Cutoff Mark and TNEA State Rank; filters by community, multiple districts, multiple branches, and an optional specific college. No Predictor quota-category field or institutional-tier filter is shown.
- **Choice Optimizer:** balances submitted options into Reach/Target/Safe choices; supports copy, CSV, and PDF.
- **TNEA Historical Records:** browses 2021–2025 cutoff marks or closing ranks. Multiple years, communities, districts, and branches can be selected; results are displayed in a Year → Community grouped table with pagination and an optional specific-college filter.

The Predictor additionally provides a five-year trend and Campus Branches alternatives. Dark and light themes are available and the chosen mode persists in local storage.

## Backend and data

- Flask application entry point: `backend/app.py`, local default `127.0.0.1:5000`.
- MySQL database: `collegeconnect`; schema: `database/schema.sql`.
- Tables: `colleges`, `branches`, `historical_admissions`.
- Bundled input: `data/integrated/tnea_integrated_master.csv` (16,174 source offerings, 2021–2025).
- Loader output expected by the end-to-end checks: 467 colleges, 116 branches, and 113,218 historical rows across the seven supported communities.
- Optional Gemini integration; deterministic explanation fallback available.
- Route modules include cutoff/rank predictions, historical records, explanations, and supporting legacy APIs. `GET /api/rank-matrix` remains registered and tested but has no current UI page/menu.

The provided historical data is General-quota data. The Predictor does not offer a quota-category selector.

## Verification performed

On October 6, 2026, using the local configured MySQL database:

- `scripts/verify_system.py`: **30/30 checks passed**.
- `scripts/verify_theme_system.py`: passed.
- `scripts/test_scoring.py`: passed.
- `scripts/test_modal_and_exports.py`: passed with Flask running, including trend, campus branch, optimizer, PDF, and CSV checks.

This records local test results; it does not claim a production deployment. Detailed commands are in [README.md](README.md), and the implementation/verification context is in [PROJECT_IMPLEMENTATION_REPORT.md](PROJECT_IMPLEMENTATION_REPORT.md).

## Running prerequisites

Use Python 3.11 and MySQL 8.4. Configure local credentials in an ignored `.env` copied from `.env.example`, start MySQL, run `python scripts/load_database.py`, then run `python backend/app.py`. On Windows, `start_mysql.bat` initializes a local ignored data directory on first launch. Full commands and the platform-specific launcher requirement are in [README.md](README.md).
