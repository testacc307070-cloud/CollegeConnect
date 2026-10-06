# CollegeConnect — As-Built Project Guide

This document describes the implementation currently in the repository. It replaces the former proposed architecture and phase roadmap; completed behavior is described below, and no future feature is implied by the old plan.

## Product scope

The single-page application has three navigation menus: **Predictor**, **Choice Optimizer**, and **TNEA Historical Records**.

- **Predictor:** users choose Aggregate Cutoff Mark or TNEA State Rank, enter the corresponding value, and filter recommendations using the currently available community, location, branch, college, and tier controls. There is no Predictor quota-category selector.
- **Choice Optimizer:** submits candidate choices to the optimizer, presents the ordered list and risk mix, supports formatted copy, and exports CSV (browser-side) and PDF (backend).
- **TNEA Historical Records:** searches cutoff or closing-rank values for selected 2021–2025 years and communities; optional district, branch, and college filters are available. The response and table are grouped by Year → Community and paginated.
- **Predictor result actions:** show a five-year trend and same-campus branch alternatives.
- **Theme:** dark and light modes are available; the selection is persisted in local storage and applied early to avoid a visible theme flash.

Scores and tiers are historical estimates and do not guarantee an admission outcome.

## System architecture

```text
Browser (frontend/index.html, app.js, styles.css)
          │ JSON HTTP
          ▼
Flask app (backend/app.py + registered route blueprints)
          │ parameterized queries via PyMySQL
          ▼
MySQL 8.4 (collegeconnect)
```

The browser does not require a JavaScript build step or frontend dependencies. Flask serves the page and static assets. The database schema source is `database/schema.sql`; `scripts/load_database.py` ingests the bundled source CSV and invokes the tier classifier. Backend modules separate data access, scoring, cutoff/rank routes, historical records, explanation services, and PDF generation.

## Data and database

The bundled `data/integrated/tnea_integrated_master.csv` contains 16,174 offerings covering academic years 2021–2025. The loader normalizes these into 113,218 historical admission rows across seven communities. The current verification checks 467 colleges and 116 branches. The schema has three primary tables: `colleges`, `branches`, and `historical_admissions`.

Historical records are based on the General quota data. The Predictor UI does not expose a quota-category control. MySQL is required for the API and application data. Gemini explanations are optional; deterministic explanation fallback is part of the backend.

## Main backend surface

The current application provides health and lookup APIs; cutoff and state-rank prediction APIs; `/api/historical-records` for grouped and paginated historical results; trend and campus-branch APIs; choice optimization and PDF export APIs; and cutoff/rank explanation APIs. The browser creates choice-list CSV exports.

`GET /api/rank-matrix` remains a registered, tested backend endpoint for compatibility with existing code. It is not a current navigation menu or page and is not presented as a primary user feature.

## Development and verification

Setup, environment variables, launch steps, and test commands are maintained in [README.md](README.md). Automated checks are in `scripts/verify_system.py`, `scripts/verify_theme_system.py`, `scripts/test_scoring.py`, and `scripts/test_modal_and_exports.py`.

On October 6, 2026, the local end-to-end verifier passed 30/30 checks against the configured MySQL database. Theme checks, scoring checks, and modal/export checks also passed; modal/export checks were run with the Flask app already running. See [PROJECT_IMPLEMENTATION_REPORT.md](PROJECT_IMPLEMENTATION_REPORT.md) for the verification record.
