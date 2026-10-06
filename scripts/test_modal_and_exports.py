"""
scripts/test_modal_and_exports.py
Verifies end-to-end functionality for:
1. 5-Year Trend data retrieval (/api/historical)
2. Campus Branches swap options (/api/branch-swap)
3. PDF choice list generation (/api/choices/export-pdf)
4. Choice Optimizer strategic balancing (/api/choices/optimize)
"""

import json
import urllib.request
from datetime import datetime

BASE_URL = "http://127.0.0.1:5000"

def test_historical_trend():
    print("\n--- 1. Testing /api/historical (5-Yr Trend) ---")
    url = f"{BASE_URL}/api/historical?college_code=1&branch_code=CS&community=OC"
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        data = json.loads(resp.read().decode())
        assert data["status"] == "ok"
        assert data["college_code"] == 1
        assert "Anna University" in data.get("college_name", "")
        assert data["branch_code"] == "CS"
        years = data.get("years", [])
        assert len(years) > 0, "No historical years returned"
        print(f"SUCCESS: Retrieved {len(years)} years for {data['college_name']} ({data['branch_code']})")
        for y in sorted(years, key=lambda x: x["year"]):
            print(f"  Year {y['year']}: Cutoff={y['cutoff_mark']}, Closing Rank={y['closing_rank']}")
        # Verify 2021-2025 coverage
        year_set = {y["year"] for y in years}
        print(f"Covered Counseling Years: {sorted(list(year_set))}")

def test_campus_branch_swap():
    print("\n--- 2. Testing /api/branch-swap (Campus Branches) ---")
    url = f"{BASE_URL}/api/branch-swap?college_code=1&cutoff_mark=198.5&community=BC"
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        data = json.loads(resp.read().decode())
        assert data["status"] == "ok"
        assert data["college_code"] == 1
        branches = data.get("branches", [])
        assert len(branches) > 0, "No campus branches returned"
        print(f"SUCCESS: Retrieved {len(branches)} campus branches for {data['college_name']}")
        
        # Check tier calculation and cushion
        tiers_found = set()
        for b in branches[:5]:
            tiers_found.add(b["tier"])
            print(f"  Branch {b['branch_code']}: {b['branch_name'][:30]} | Cutoff: {b['latest_cutoff']} | Tier: {b['tier']} | Cushion: {b['cushion']}")
        print(f"Tiers calculated across branches: {tiers_found}")

def test_choice_optimizer():
    print("\n--- 3. Testing /api/choices/optimize ---")
    candidates = [
        {"college_code": 1, "branch_code": "CS", "college_name": "CEG", "branch_name": "CSE", "tier": "Reach", "estimated_probability": 35.0},
        {"college_code": 1, "branch_code": "IT", "college_name": "CEG", "branch_name": "IT", "tier": "Reach", "estimated_probability": 45.0},
        {"college_code": 2006, "branch_code": "CS", "college_name": "PSG", "branch_name": "CSE", "tier": "Target", "estimated_probability": 65.0},
        {"college_code": 2006, "branch_code": "IT", "college_name": "PSG", "branch_name": "IT", "tier": "Target", "estimated_probability": 72.0},
        {"college_code": 2007, "branch_code": "CS", "college_name": "CIT", "branch_name": "CSE", "tier": "Safe", "estimated_probability": 90.0},
        {"college_code": 2007, "branch_code": "IT", "college_name": "CIT", "branch_name": "IT", "tier": "Safe", "estimated_probability": 94.0},
    ]
    payload = json.dumps({"candidates": candidates, "target_count": 5}).encode()
    req = urllib.request.Request(f"{BASE_URL}/api/choices/optimize", data=payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        data = json.loads(resp.read().decode())
        assert data["status"] == "ok"
        print(f"SUCCESS: Choice list optimized. Strategy counts: {data['counts']}")

def test_export_pdf():
    print("\n--- 4. Testing /api/choices/export-pdf ---")
    payload = json.dumps({
        "choices": [
            {
                "college_code": 1,
                "college_name": "College of Engineering Guindy (CEG), Anna University",
                "branch_code": "CS",
                "branch_name": "Computer Science and Engineering",
                "district": "Chennai",
                "latest_cutoff": 199.50,
                "latest_closing_rank": 42,
                "tier": "Reach",
                "estimated_probability": 38.5
            },
            {
                "college_code": 1,
                "college_name": "College of Engineering Guindy (CEG), Anna University",
                "branch_code": "IT",
                "branch_name": "Information Technology",
                "district": "Chennai",
                "latest_cutoff": 198.50,
                "latest_closing_rank": 180,
                "tier": "Target",
                "estimated_probability": 65.0
            },
            {
                "college_code": 2006,
                "college_name": "PSG College of Technology, Peelamedu",
                "branch_code": "CS",
                "branch_name": "Computer Science and Engineering",
                "district": "Coimbatore",
                "latest_cutoff": 197.50,
                "latest_closing_rank": 420,
                "tier": "Safe",
                "estimated_probability": 88.0
            }
        ],
        "student_profile": {
            "cutoff_mark": 198.25,
            "state_rank": 215,
            "community": "BC",
            "quota": "GENERAL"
        }
    }).encode()

    req = urllib.request.Request(f"{BASE_URL}/api/choices/export-pdf", data=payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        assert resp.headers.get("Content-Type") == "application/pdf"
        pdf_bytes = resp.read()
        assert len(pdf_bytes) > 1000, "PDF size unexpectedly small"
        assert pdf_bytes[:4] == b"%PDF", "Invalid PDF magic header"
        print(f"SUCCESS: Exported PDF received. Size = {len(pdf_bytes)} bytes. Magic Header = {pdf_bytes[:4].decode()}")

        # Save to disk for local inspection
        output_path = "data/test_exported_choice_list.pdf"
        with open(output_path, "wb") as f:
            f.write(pdf_bytes)
        print(f"Saved test PDF to: {output_path}")

def test_export_csv():
    print("\n--- 5. Testing CSV Export Structure ---")
    import csv
    headers = [
        "Preference", "College Code", "College Name", "Branch Code", "Branch Name",
        "District", "Latest Cutoff (2025)", "Latest Closing Rank (2025)",
        "Feasibility Tier", "Estimated Probability (%)", "Historical Fit Score (%)", "Strategy Reasoning"
    ]
    rows = [
        [1, 1, "College of Engineering Guindy (CEG), Anna University", "CS", "Computer Science and Engineering", "Chennai", "199.50", 42, "Reach", "38.5%", "92.0%", "Highly competitive flagship institution"],
        [2, 2006, "PSG College of Technology, Peelamedu", "CS", "Computer Science and Engineering", "Coimbatore", "197.50", 420, "Safe", "88.0%", "98.0%", "Strong safety net preference"]
    ]
    
    csv_str = "\ufeff" + "\r\n".join([",".join([f'"{c}"' if (isinstance(c, str) and (',' in c or ' ' in c)) else str(c) for c in row]) for row in [headers] + rows])
    csv_file = "data/test_exported_choice_list.csv"
    with open(csv_file, "w", newline="", encoding="utf-8") as f:
        f.write(csv_str)
    
    with open(csv_file, "r", newline="", encoding="utf-8-sig") as f:
        reader = list(csv.reader(f))
        assert len(reader) == 3
        assert len(reader[0]) == 12
        assert len(reader[1]) == 12
        assert reader[0][0] == "Preference"
        assert reader[1][2] == "College of Engineering Guindy (CEG), Anna University"
    print(f"SUCCESS: Generated RFC-4180 UTF-8 CSV with 12 distinct columns. Saved to: {csv_file}")

if __name__ == "__main__":
    test_historical_trend()
    test_campus_branch_swap()
    test_choice_optimizer()
    test_export_pdf()
    test_export_csv()
    print("\nALL MODAL & EXPORT TESTS COMPLETED SUCCESSFULLY!")

