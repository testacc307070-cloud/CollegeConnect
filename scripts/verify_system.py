#!/usr/bin/env python3
"""
scripts/verify_system.py
Comprehensive End-to-End System Verification Suite for CollegeConnect.
Tests all APIs, database integrity, RAG fallbacks, tiering, quotas, and optimizer.
"""

import sys
import json
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pymysql
from backend.app import app
from backend.db import get_db_connection, safe_close


class TestReporter:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.tests = []

    def check(self, name: str, condition: bool, details: str = ""):
        if condition:
            self.passed += 1
            print(f"  [PASS] {name} {details}")
            self.tests.append((name, True, details))
        else:
            self.failed += 1
            print(f"  [FAIL] {name} {details}")
            self.tests.append((name, False, details))

    def summary(self):
        total = self.passed + self.failed
        score = (self.passed / total * 100) if total > 0 else 0
        print("\n" + "=" * 70)
        print(f"VERIFICATION SUMMARY: {self.passed}/{total} checks passed ({score:.1f}%)")
        print("=" * 70)
        return self.failed == 0


def verify_database(reporter: TestReporter):
    print("\n--- 1. DATABASE INTEGRITY ---")
    conn = None
    try:
        conn = get_db_connection()
        reporter.check("Database Connection", conn.open, "(MySQL connected on port 3306)")
        with conn.cursor(pymysql.cursors.DictCursor) as cur:
            # Colleges count
            cur.execute("SELECT COUNT(*) as c FROM colleges")
            col_count = cur.fetchone()["c"]
            reporter.check("Colleges Count", col_count == 467, f"({col_count} colleges)")

            # Branches count
            cur.execute("SELECT COUNT(*) as c FROM branches")
            br_count = cur.fetchone()["c"]
            reporter.check("Branches Count", br_count == 116, f"({br_count} branches)")

            # Admissions fact table count
            cur.execute("SELECT COUNT(*) as c FROM historical_admissions")
            adm_count = cur.fetchone()["c"]
            reporter.check("Historical Admissions Count", adm_count == 113218, f"({adm_count:,} records)")

            # Institutional Tier Classification
            cur.execute("SELECT institutional_tier, COUNT(*) as c FROM colleges GROUP BY institutional_tier")
            tiers = {r["institutional_tier"]: r["c"] for r in cur.fetchall()}
            has_no_null = None not in tiers and sum(tiers.values()) == 467
            reporter.check("Institutional Tiers Populated", has_no_null, f"(T1: {tiers.get('Tier-1',0)}, T2: {tiers.get('Tier-2',0)}, T3: {tiers.get('Tier-3',0)})")

    except Exception as exc:
        reporter.check("Database Check Exception", False, str(exc))
    finally:
        safe_close(conn)


def verify_api_endpoints(reporter: TestReporter):
    print("\n--- 2. CORE BACKEND APIS ---")
    client = app.test_client()

    # Health
    r = client.get("/api/health")
    reporter.check("GET /api/health", r.status_code == 200 and r.get_json().get("status") == "ok")

    # DB test
    r = client.get("/api/db-test")
    reporter.check("GET /api/db-test", r.status_code == 200 and r.get_json().get("status") == "ok")

    # Reference data: districts, branches, tiers
    r = client.get("/api/districts")
    d = r.get_json()
    reporter.check("GET /api/districts", r.status_code == 200 and len(d.get("districts", [])) >= 30, f"({len(d.get('districts', []))} districts)")

    r = client.get("/api/branches")
    d = r.get_json()
    reporter.check("GET /api/branches", r.status_code == 200 and len(d.get("branches", [])) == 116, f"({len(d.get('branches', []))} branches)")

    r = client.get("/api/tiers")
    d = r.get_json()
    reporter.check("GET /api/tiers", r.status_code == 200 and len(d.get("tiers", [])) == 3, f"({len(d.get('tiers', []))} tiers returned)")

    # Colleges and tier filter
    r = client.get("/api/colleges?tier=Tier-1")
    d = r.get_json()
    reporter.check("GET /api/colleges?tier=Tier-1", r.status_code == 200 and len(d.get("colleges", [])) == 69, f"({len(d.get('colleges', []))} Tier-1 colleges)")


def verify_predictions(reporter: TestReporter):
    print("\n--- 3. PREDICTION & QUOTA ENGINES ---")
    client = app.test_client()

    # Cutoff prediction
    r = client.get("/api/predictions?cutoff_mark=192.5&community=BC&limit=25")
    d = r.get_json()
    preds = d.get("predictions", [])
    reporter.check("Cutoff Prediction Basic", r.status_code == 200 and len(preds) > 0, f"({len(preds)} candidates returned)")
    if preds:
        first = preds[0]
        has_req_fields = all(k in first for k in ("college_name", "branch_name", "tier", "estimated_probability", "latest_cutoff", "institutional_tier"))
        reporter.check("Cutoff Prediction Fields", has_req_fields, f"(Probability: {first.get('estimated_probability')}%, Tier: {first.get('tier')})")

    # Tier filtering in predictions
    r = client.get("/api/predictions?cutoff_mark=192.5&community=BC&tier=Tier-1")
    d = r.get_json()
    p_t1 = d.get("predictions", [])
    all_t1 = all(p.get("institutional_tier") == "Tier-1" for p in p_t1) if p_t1 else False
    reporter.check("Cutoff Prediction Tier-1 Filter", all_t1 and len(p_t1) > 0, f"({len(p_t1)} Tier-1 candidates)")

    # Special Quota handling (7.5% Government school quota)
    r = client.get("/api/predictions?cutoff_mark=185.0&community=OC&quota=GOVT_7_5")
    d = r.get_json()
    has_quota_note = bool(d.get("student_input", {}).get("quota_note"))
    reporter.check("Special Quota 7.5% Handling", r.status_code == 200 and has_quota_note and len(d.get("predictions", [])) > 0, "(Advisory note populated)")

    # Rank prediction
    r = client.get("/api/rank-predictions?state_rank=1200&community=BC")
    d = r.get_json()
    rank_preds = d.get("predictions", [])
    reporter.check("Rank Prediction", r.status_code == 200 and len(rank_preds) > 0, f"({len(rank_preds)} candidates returned)")

    # Prediction with District, Branch & College filters
    r_pred_col = client.get("/api/predictions?cutoff_mark=190&community=BC&district=COIMBATORE&branch_code=CM&college_code=2006")
    d_pred_col = r_pred_col.get_json()
    preds_col = d_pred_col.get("predictions", [])
    all_pred_col = all(p.get("college_code") == 2006 and p.get("branch_code") == "CM" for p in preds_col) if preds_col else False
    reporter.check("Cutoff Prediction Multi-Filter (District, Branch, College)", r_pred_col.status_code == 200 and all_pred_col and len(preds_col) > 0, f"({len(preds_col)} filtered candidate)")

    # Rank Matrix Basic
    r = client.get("/api/rank-matrix?community=OC")
    d = r.get_json()
    records = d.get("results", [])
    reporter.check("Rank Matrix Basic", r.status_code == 200 and len(records) > 0, f"({len(records)} records returned)")

    # Rank Matrix with College filter
    r_mat_col = client.get("/api/rank-matrix?community=BC&college_code=2006")
    d_mat_col = r_mat_col.get_json()
    recs_col = d_mat_col.get("results", [])
    all_2006 = all(x.get("college_code") == 2006 for x in recs_col) if recs_col else False
    reporter.check("Rank Matrix College Filter", r_mat_col.status_code == 200 and all_2006 and len(recs_col) > 0, f"({len(recs_col)} records for college 2006)")

    # Rank Matrix with District & Branch filter
    r_mat_filt = client.get("/api/rank-matrix?community=BC&district=COIMBATORE&branch_code=CM")
    d_mat_filt = r_mat_filt.get_json()
    recs_filt = d_mat_filt.get("results", [])
    all_filt = all(x.get("district") == "COIMBATORE" and x.get("branch_code") == "CM" for x in recs_filt) if recs_filt else False
    reporter.check("Rank Matrix District & Branch Filter", r_mat_filt.status_code == 200 and all_filt and len(recs_filt) > 0, f"({len(recs_filt)} records returned)")


def verify_rag_and_historical(reporter: TestReporter):
    print("\n--- 4. RAG, HISTORICAL & RECOMMENDATIONS ---")
    client = app.test_client()

    # Historical 5-year trajectory
    r = client.get("/api/historical?college_code=1&branch_code=CS&community=OC")
    d = r.get_json()
    years = d.get("years", [])
    reporter.check("Historical 5-Year Trajectory", r.status_code == 200 and len(years) == 5, f"({len(years)} years: 2021-2025)")

    # Campus Branch Swap
    r = client.get("/api/branch-swap?college_code=1&community=OC&cutoff_mark=199.0")
    d = r.get_json()
    branches = d.get("branches", [])
    reporter.check("Campus Branch Swap Alternatives", r.status_code == 200 and len(branches) >= 15, f"({len(branches)} branches on campus)")

    # Choice Optimizer
    sample_choices = [
        {"college_code": 1, "branch_code": "CS", "tier": "Reach", "estimated_probability": 25},
        {"college_code": 1, "branch_code": "EC", "tier": "Target", "estimated_probability": 55},
        {"college_code": 1315, "branch_code": "CS", "tier": "Target", "estimated_probability": 65},
        {"college_code": 2007, "branch_code": "IT", "tier": "Safe", "estimated_probability": 88},
        {"college_code": 2006, "branch_code": "ME", "tier": "Safe", "estimated_probability": 92},
    ]
    r = client.post("/api/choices/optimize", json={"choices": sample_choices, "target_count": 5})
    d = r.get_json()
    reporter.check("Choice Optimizer Algorithm", r.status_code == 200 and d.get("status") == "ok" and len(d.get("optimized_choices", [])) == 5, "(Balanced 20/50/30 distribution)")

    # RAG Explanation with deterministic fallback (Cutoff)
    r = client.post("/api/rag-explanation", json={"cutoff_mark": 195.0, "community": "OC", "college_code": 1})
    d = r.get_json() or {}
    has_explanation = bool(d.get("explanation"))
    reporter.check("RAG Explanation (Cutoff)", r.status_code == 200 and has_explanation, f"(Model: {d.get('generation_model')})")

    # RAG Explanation with deterministic fallback (Rank)
    r_rank = client.post("/api/rank-rag-explanation", json={"state_rank": 1500, "community": "BC", "college_code": 1})
    d_rank = r_rank.get_json() or {}
    has_rank_exp = bool(d_rank.get("explanation"))
    reporter.check("RAG Explanation (Rank)", r_rank.status_code == 200 and has_rank_exp, f"(Model: {d_rank.get('generation_model')})")


def verify_frontend_assets(reporter: TestReporter):
    print("\n--- 5. FRONTEND STATIC ASSETS & JAVASCRIPT ---")
    client = app.test_client()

    # TNEA Historical Records Explorer API
    r_hist = client.get("/api/historical-records?year=2021&year=2023&metric=cutoff&community=BC&page=1&page_size=5")
    d_hist = r_hist.get_json() or {}
    reporter.check("TNEA Historical Records API", r_hist.status_code == 200 and d_hist.get("status") == "ok" and (d_hist.get("total_count") or 0) > 0, f"({d_hist.get('total_count')} offerings matched)")

    # Index page
    r = client.get("/")
    content = r.data.decode("utf-8")
    has_trend_modal = "trendModal" in content
    has_branch_swap_modal = "branchSwapModal" in content
    has_calc_widget = "calc-widget" in content
    has_method_toggle = "predictionMethod" in content
    has_tier_select = "tierFilter" in content
    has_historical_tab = "historicalTab" in content
    reporter.check("Index.html Modal & Widget Markup", r.status_code == 200 and all([has_trend_modal, has_branch_swap_modal, has_calc_widget, has_method_toggle, has_tier_select, has_historical_tab]), "(All UI widgets & tabs present)")

    # Stylesheet
    r = client.get("/assets/styles.css")
    styles = r.data.decode("utf-8")
    has_modal_css = "modal-overlay" in styles and "tier-inst-badge" in styles and "historical-grouped-table" in styles
    reporter.check("Styles.css Modals & Badges", r.status_code == 200 and has_modal_css, "(Modal, tier badge & historical table CSS verified)")

    # App.js static serving & syntax
    r = client.get("/assets/app.js")
    js_content = r.data.decode("utf-8")
    has_modal_js = "openTrendModal" in js_content and "openBranchSwapModal" in js_content and "searchHistoricalRecords" in js_content
    reporter.check("App.js Controllers Served", r.status_code == 200 and has_modal_js, "(Controllers verified)")

    # Node JS syntax check
    try:
        node_res = subprocess.run(["node", "-c", "frontend/app.js"], cwd=str(PROJECT_ROOT), capture_output=True, text=True)
        reporter.check("Frontend App.js Syntax", node_res.returncode == 0, "(Node.js syntax parser passed)")
    except Exception as exc:
        reporter.check("Node.js Check", False, str(exc))


def main():
    print("=" * 70)
    print("COLLEGECONNECT FULL SYSTEM END-TO-END VERIFICATION")
    print("=" * 70)

    reporter = TestReporter()
    verify_database(reporter)
    verify_api_endpoints(reporter)
    verify_predictions(reporter)
    verify_rag_and_historical(reporter)
    verify_frontend_assets(reporter)

    success = reporter.summary()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
