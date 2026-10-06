#!/usr/bin/env python3
"""
scripts/classify_tiers.py
Classifies colleges into Institutional Tiers (Tier-1, Tier-2, Tier-3)
based on historical admissions cutoffs across 2021-2025.
"""

import os
import sys
from pathlib import Path
import pymysql

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.db import get_db_connection, safe_close

def classify_and_update_tiers():
    conn = get_db_connection()
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            # Calculate overall average and maximum cutoffs per college
            cursor.execute("""
                SELECT 
                    c.college_code,
                    c.college_name,
                    c.district,
                    AVG(h.cutoff_mark) as overall_avg,
                    MAX(h.cutoff_mark) as max_cutoff,
                    COUNT(h.cutoff_mark) as record_count
                FROM colleges c
                LEFT JOIN historical_admissions h 
                    ON h.college_code = c.college_code
                GROUP BY c.college_code, c.college_name, c.district;
            """)
            colleges = cursor.fetchall()
            print(f"Loaded {len(colleges)} colleges for tier classification.")

            tier_counts = {"Tier-1": 0, "Tier-2": 0, "Tier-3": 0}
            updates = []

            for col in colleges:
                avg = float(col["overall_avg"]) if col["overall_avg"] is not None else 0.0
                mx = float(col["max_cutoff"]) if col["max_cutoff"] is not None else 0.0
                code = col["college_code"]

                # Premier institutions: top cutoffs or flagship universities
                if avg >= 148.0 or mx >= 193.0 or code in (1, 2, 3, 4, 1315, 2005, 2006, 2007, 2377, 5008):
                    tier = "Tier-1"
                elif avg >= 115.0 or mx >= 165.0:
                    tier = "Tier-2"
                else:
                    tier = "Tier-3"

                tier_counts[tier] += 1
                updates.append((tier, code))

            cursor.executemany(
                "UPDATE colleges SET institutional_tier = %s WHERE college_code = %s",
                updates
            )
            conn.commit()

            print("\nTier classification summary:")
            for tier, count in tier_counts.items():
                print(f"  {tier}: {count} colleges ({round(count / len(colleges) * 100, 1)}%)")

            # Verify no NULLs remaining
            cursor.execute("SELECT COUNT(*) as null_count FROM colleges WHERE institutional_tier IS NULL")
            null_res = cursor.fetchone()
            print(f"Remaining NULL institutional_tier: {null_res['null_count']}")

    finally:
        safe_close(conn)

if __name__ == "__main__":
    classify_and_update_tiers()
