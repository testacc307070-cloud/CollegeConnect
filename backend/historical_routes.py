"""
Historical Admissions Explorer Routes for CollegeConnect.
Provides parameterized multi-year, multi-community cutoff and closing-rank
historical queries with Year -> Community pivoting and full pagination.
"""

import logging
from flask import Blueprint, jsonify, request
import pymysql.cursors

from backend.db import get_db_connection

logger = logging.getLogger("collegeconnect.historical")

historical_bp = Blueprint("historical_records", __name__)

ALL_VALID_YEARS = [2021, 2022, 2023, 2024, 2025]
ALL_VALID_COMMUNITIES = ["OC", "BC", "BCM", "MBC", "SC", "SCA", "ST"]


@historical_bp.route("/api/historical-records", methods=["GET"])
def get_historical_records():
    """
    Search multi-year historical cutoff and closing-rank records with
    grouped Year -> Community matrix structure.

    Query Parameters:
      - years: comma-separated or multiple keys, e.g. '2021,2023,2025' or '2021'
      - metric: 'cutoff' (default) or 'rank'
      - communities: comma-separated or multiple keys, e.g. 'BC,MBC,OC' (optional)
      - district: string (optional)
      - branch_code: string (optional)
      - college_code: int (optional)
      - page: int (default: 1)
      - page_size: int (default: 25, max: 100)
    """
    conn = None
    try:
        # 1. Parse & validate Years (Multi-select, 2021-2025)
        raw_years = request.args.getlist("year")
        if not raw_years:
            raw_years = request.args.getlist("years")
        if not raw_years and "years" in request.args:
            raw_years = request.args.get("years", "").split(",")
        elif not raw_years and "year" in request.args:
            raw_years = request.args.get("year", "").split(",")

        parsed_years = []
        for y_item in raw_years:
            for part in str(y_item).split(","):
                part_clean = part.strip()
                if part_clean.isdigit():
                    yr = int(part_clean)
                    if yr in ALL_VALID_YEARS and yr not in parsed_years:
                        parsed_years.append(yr)

        if not parsed_years:
            parsed_years = list(ALL_VALID_YEARS)
        else:
            parsed_years.sort()

        # 2. Parse & validate Metric (Cutoff vs Closing Rank)
        metric = request.args.get("metric", "cutoff").strip().lower()
        if metric not in ("cutoff", "rank"):
            metric = "cutoff"

        # 3. Parse & validate Communities (Multi-select, Optional)
        raw_comms = request.args.getlist("communities")
        if not raw_comms and "communities" in request.args:
            raw_comms = request.args.get("communities", "").split(",")

        # Also support singular 'community'
        if not raw_comms and "community" in request.args:
            raw_comms = request.args.getlist("community")
            if not raw_comms:
                raw_comms = request.args.get("community", "").split(",")

        parsed_comms = []
        for c_item in raw_comms:
            for part in str(c_item).split(","):
                c_clean = part.strip().upper()
                if c_clean in ALL_VALID_COMMUNITIES and c_clean not in parsed_comms:
                    parsed_comms.append(c_clean)

        # If no community is selected, show all available standard communities in order
        if not parsed_comms:
            parsed_comms = list(ALL_VALID_COMMUNITIES)
        else:
            # Keep consistent standard order
            parsed_comms.sort(key=lambda c: ALL_VALID_COMMUNITIES.index(c))

        # 4. Optional single filters
        district = request.args.get("district", "").strip() or None
        branch_code = request.args.get("branch_code", "").strip() or None
        if not branch_code:
            branch_code = request.args.get("branch", "").strip() or None

        college_code_raw = request.args.get("college_code", "").strip()
        college_code = int(college_code_raw) if college_code_raw.isdigit() else None

        # 5. Pagination parameters
        try:
            page = max(1, int(request.args.get("page", 1)))
        except (ValueError, TypeError):
            page = 1

        try:
            page_size = min(100, max(1, int(request.args.get("page_size", 25))))
        except (ValueError, TypeError):
            page_size = 25

        offset = (page - 1) * page_size

        # 6. Build parameterized SQL queries
        conn = get_db_connection()
        with conn.cursor(pymysql.cursors.DictCursor) as cur:
            # Base conditions for matching college-branch pairs
            where_conditions = ["h.quota = %s"]
            base_params = ["GENERAL"]

            where_conditions.append(
                "h.year IN (" + ",".join(["%s"] * len(parsed_years)) + ")"
            )
            base_params.extend(parsed_years)

            where_conditions.append(
                "h.community IN (" + ",".join(["%s"] * len(parsed_comms)) + ")"
            )
            base_params.extend(parsed_comms)

            if district:
                where_conditions.append("c.district = %s")
                base_params.append(district)

            if branch_code:
                where_conditions.append("h.branch_code = %s")
                base_params.append(branch_code)

            if college_code:
                where_conditions.append("h.college_code = %s")
                base_params.append(college_code)

            where_sql = " AND ".join(where_conditions)

            # Count total distinct (college_code, branch_code) combinations
            count_sql = f"""
                SELECT COUNT(DISTINCT h.college_code, h.branch_code) AS total
                FROM historical_admissions h
                JOIN colleges c ON c.college_code = h.college_code
                JOIN branches b ON b.branch_code = h.branch_code
                WHERE {where_sql}
            """
            cur.execute(count_sql, base_params)
            count_row = cur.fetchone()
            total_records = count_row["total"] if count_row else 0

            total_pages = (total_records + page_size - 1) // page_size if total_records > 0 else 1

            rows = []
            if total_records > 0 and offset < total_records:
                # Fetch distinct pairs for current page
                pairs_sql = f"""
                    SELECT DISTINCT
                        c.college_code,
                        c.college_name,
                        c.district,
                        b.branch_code,
                        b.branch_name
                    FROM historical_admissions h
                    JOIN colleges c ON c.college_code = h.college_code
                    JOIN branches b ON b.branch_code = h.branch_code
                    WHERE {where_sql}
                    ORDER BY c.college_name ASC, b.branch_name ASC
                    LIMIT %s OFFSET %s
                """
                cur.execute(pairs_sql, base_params + [page_size, offset])
                pairs = cur.fetchall()

                if pairs:
                    pair_keys = [(p["college_code"], p["branch_code"]) for p in pairs]
                    pairs_clause = ",".join(["(%s, %s)"] * len(pair_keys))
                    flat_pairs = [item for pair in pair_keys for item in pair]

                    # Retrieve matching metric records
                    data_params = flat_pairs + ["GENERAL"] + parsed_years + parsed_comms
                    data_sql = f"""
                        SELECT
                            college_code,
                            branch_code,
                            year,
                            community,
                            cutoff_mark,
                            closing_rank
                        FROM historical_admissions
                        WHERE (college_code, branch_code) IN ({pairs_clause})
                          AND quota = %s
                          AND year IN ({','.join(['%s'] * len(parsed_years))})
                          AND community IN ({','.join(['%s'] * len(parsed_comms))})
                    """
                    cur.execute(data_sql, data_params)
                    metric_records = cur.fetchall()

                    # Index metrics by (college_code, branch_code) -> year -> community
                    data_index = {}
                    for rec in metric_records:
                        k = (rec["college_code"], rec["branch_code"])
                        if k not in data_index:
                            data_index[k] = {}
                        yr = rec["year"]
                        comm = rec["community"]
                        if yr not in data_index[k]:
                            data_index[k][yr] = {}

                        if metric == "cutoff":
                            val = float(rec["cutoff_mark"]) if rec["cutoff_mark"] is not None else None
                        else:
                            val = int(rec["closing_rank"]) if rec["closing_rank"] is not None else None

                        data_index[k][yr][comm] = val

                    # Assemble final structured response rows
                    for p in pairs:
                        k = (p["college_code"], p["branch_code"])
                        p_metrics = data_index.get(k, {})

                        # Structure metrics by Year -> Community
                        year_data = {}
                        for yr in parsed_years:
                            year_data[str(yr)] = {}
                            for comm in parsed_comms:
                                year_data[str(yr)][comm] = p_metrics.get(yr, {}).get(comm, None)

                        rows.append({
                            "college_code": p["college_code"],
                            "college_name": p["college_name"],
                            "district": p["district"],
                            "branch_code": p["branch_code"],
                            "branch_name": p["branch_name"],
                            "metrics": year_data
                        })

        return jsonify({
            "status": "ok",
            "metric": metric,
            "years": parsed_years,
            "communities": parsed_comms,
            "total_records": total_records,
            "total_count": total_records,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
            "rows": rows,
            "records": rows
        })

    except Exception as exc:
        logger.exception(f"Error querying historical records: {exc}")
        return jsonify({
            "status": "error",
            "message": f"Could not retrieve historical records: {str(exc)}"
        }), 500
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass
