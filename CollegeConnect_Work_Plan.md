# CollegeConnect — Completed Work Checklist

This checklist describes the current implementation rather than the superseded phase proposal. Current setup and verification instructions are in [README.md](README.md).

## Product and interface

- [x] Three-menu single-page interface: Predictor, Choice Optimizer, and TNEA Historical Records.
- [x] Predictor supports Aggregate Cutoff Mark and TNEA State Rank methods.
- [x] Predictor filters by community, multiple districts and branches, and optional specific college; it has no quota-category or institutional-tier selector.
- [x] Historical explorer supports year/community selection, cutoff/rank metrics, searchable multi-select district/branch filters, optional specific college, pagination, and Year → Community grouped results.
- [x] Choice Optimizer supports balanced choice ordering, formatted copy, CSV export, and PDF export.
- [x] Predictor results include a five-year trend and same-campus branch alternatives.
- [x] Dark/light themes persist across visits.

## Data and services

- [x] Bundle the 2021–2025 TNEA source dataset and normalize it into MySQL tables.
- [x] Provide deterministic cutoff/rank prediction scoring and optional Gemini-backed explanations with fallback.
- [x] Provide database schema and local configuration template.
- [x] Provide database loading/tier classification scripts and Windows launcher scripts.

## Verification

- [x] End-to-end verification passed 30/30 checks on October 6, 2026.
- [x] Theme verification passed on October 6, 2026.
- [x] Scoring verification passed on October 6, 2026.
- [x] Trend, campus branch, optimizer, PDF, and CSV checks passed on October 6, 2026, with the Flask app running.

The registered `/api/rank-matrix` backend endpoint is retained and covered by the verifier, but it is not a menu/page in the current product. Do not interpret older phase-plan descriptions as current interface scope.
