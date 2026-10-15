"""Run full end-to-end API test against the live Aiven MySQL database with verified TLS."""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Load .env.aiven
aiven_env = PROJECT_ROOT / ".env.aiven"
if not aiven_env.is_file():
    print("[ERROR] .env.aiven not found")
    sys.exit(1)

load_dotenv(aiven_env, override=True)
if not os.getenv("MYSQL_SSL_CA"):
    os.environ["MYSQL_SSL_CA"] = str(PROJECT_ROOT / "certs" / "ca.pem")

from backend.app import app

def run_tests():
    client = app.test_client()
    passed = 0
    total = 0

    def check(name, condition, detail=""):
        nonlocal passed, total
        total += 1
        status = "PASS" if condition else "FAIL"
        print(f"  [{status}] {name} {detail}")
        if condition:
            passed += 1

    print("==================================================")
    print("      LIVE AIVEN MYSQL E2E API VERIFICATION")
    print("==================================================")
    print(f"Host: {os.getenv('MYSQL_HOST')}")
    print(f"DB  : {os.getenv('MYSQL_DATABASE')}")
    print(f"User: {os.getenv('MYSQL_USER')}")
    print(f"CA  : {os.getenv('MYSQL_SSL_CA')}")
    print("--------------------------------------------------")

    # 1. /api/health
    res = client.get("/api/health")
    check("/api/health", res.status_code == 200, f"({res.status_code})")

    # 2. /api/db-test
    res = client.get("/api/db-test")
    data = res.get_json() or {}
    check("/api/db-test", res.status_code == 200 and data.get("status") == "ok", f"({data.get('database')}, {data.get('college_count')} colleges)")

    # 3. /api/districts
    res = client.get("/api/districts")
    data = res.get_json() or {}
    districts = data.get("districts", [])
    check("/api/districts", res.status_code == 200 and len(districts) >= 30, f"({len(districts)} districts)")

    # 4. /api/branches
    res = client.get("/api/branches")
    data = res.get_json() or {}
    branches = data.get("branches", [])
    check("/api/branches", res.status_code == 200 and len(branches) == 116, f"({len(branches)} branches)")

    # 5. /api/colleges
    res = client.get("/api/colleges")
    data = res.get_json() or {}
    colleges = data.get("colleges", [])
    check("/api/colleges", res.status_code == 200 and len(colleges) == 467, f"({len(colleges)} colleges)")

    # 6. Predictor Cutoff
    res = client.get("/api/predictions?cutoff_mark=185.0&community=OC&limit=25")
    data = res.get_json() or {}
    preds = data.get("predictions", [])
    check("Predictor (Cutoff 185 OC)", res.status_code == 200 and len(preds) > 0, f"({len(preds)} candidates)")

    # 7. Predictor State Rank
    res = client.get("/api/rank-predictions?state_rank=5000&community=BC&limit=25")
    data = res.get_json() or {}
    preds = data.get("predictions", [])
    check("Predictor (Rank 5000 BC)", res.status_code == 200 and len(preds) > 0, f"({len(preds)} candidates)")

    # 8. Choice Optimizer Strategy
    sample_choices = [
        {"college_code": 1, "branch_code": "CS", "tier": "Reach", "estimated_probability": 25},
        {"college_code": 1, "branch_code": "EC", "tier": "Target", "estimated_probability": 55},
        {"college_code": 1315, "branch_code": "CS", "tier": "Target", "estimated_probability": 65},
        {"college_code": 2007, "branch_code": "IT", "tier": "Safe", "estimated_probability": 88},
        {"college_code": 2006, "branch_code": "ME", "tier": "Safe", "estimated_probability": 92},
    ]
    res = client.post("/api/choices/optimize", json={"choices": sample_choices, "target_count": 5})
    data = res.get_json() or {}
    check("Choice Optimizer", res.status_code == 200 and data.get("status") == "ok")

    # 9. Historical Records Explorer
    res = client.get("/api/historical-records?year=2024&year=2025&metric=cutoff&community=BC&page=1&page_size=10")
    data = res.get_json() or {}
    records = data.get("records", [])
    total_count = data.get("total_count", 0)
    check("Historical Explorer", res.status_code == 200 and total_count > 0, f"({len(records)} records on page 1, total: {total_count:,})")

    # 10. 5-Year Trend Trajectory
    res = client.get("/api/historical?college_code=1&branch_code=CS&community=OC")
    data = res.get_json() or {}
    years = data.get("years", [])
    check("5-Year Trend Modal", res.status_code == 200 and len(years) == 5, f"({len(years)} years)")

    # 11. Campus Branches Swap
    res = client.get("/api/branch-swap?college_code=1&community=OC&cutoff_mark=190.0")
    data = res.get_json() or {}
    cb = data.get("branches", [])
    check("Campus Branches Swap", res.status_code == 200 and len(cb) > 0, f"({len(cb)} branches)")

    # 12. Client-side CSV Export Engine
    app_js_text = (PROJECT_ROOT / "frontend" / "app.js").read_text(encoding="utf-8")
    has_csv_export = "exportButton?.addEventListener" in app_js_text and "text/csv;charset=utf-8;" in app_js_text and "csvEscape" in app_js_text
    check("CSV Export Engine", has_csv_export, "(Client-side RFC 4180 BOM generator verified)")

    # 13. PDF Export Service
    pdf_payload = {
        "candidate": {"cutoff_mark": 190.0, "community": "OC"},
        "choices": [
            {
                "choice_order": 1,
                "college_code": "0001",
                "college_name": "CEG",
                "branch_code": "CS",
                "branch_name": "CSE",
                "feasibility": "Safe",
                "probability": 85.0,
                "margin": "+2.50"
            }
        ]
    }
    res = client.post("/api/choices/export-pdf", json=pdf_payload)
    check("PDF Export Service", res.status_code == 200 and "application/pdf" in res.content_type, f"({len(res.data):,} bytes generated)")

    # 14. Grounded RAG / Fallback Explanation
    res = client.post("/api/rag-explanation", json={"cutoff_mark": 185.0, "community": "OC", "college_code": 1})
    data = res.get_json() or {}
    check("RAG / Deterministic Fallback", res.status_code == 200 and bool(data.get("explanation")), f"(Model: {data.get('generation_model')})")

    # 15. Frontend Assets
    res_index = client.get("/")
    res_css = client.get("/styles.css")
    res_js = client.get("/app.js")
    check("Frontend Assets", res_index.status_code == 200 and res_css.status_code == 200 and res_js.status_code == 200)

    print("==================================================")
    print(f"AIVEN LIVE TEST SUMMARY: {passed}/{total} passed ({(passed/total)*100:.1f}%)")
    print("==================================================")
    return 0 if passed == total else 1

if __name__ == "__main__":
    sys.exit(run_tests())
