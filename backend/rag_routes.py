"""
RAG API routes for CollegeConnect.

Flow:
1. Receive student input.
2. Retrieve the same candidate college/branch options
   used by the prediction workflow.
3. Retrieve their historical 2021-2025 evidence.
4. Send the structured evidence to Gemini.
5. Return a grounded explanation.
"""

import json

import pymysql
from flask import Blueprint, jsonify, request

from backend.db import get_db_connection
from backend.rag import generate_grounded_explanation


rag_bp = Blueprint("rag", __name__)


ALLOWED_COMMUNITIES = {
    "OC",
    "BC",
    "BCM",
    "MBC",
    "SC",
    "SCA",
    "ST"
}


@rag_bp.route("/api/rag-explanation", methods=["GET", "POST"])
def rag_explanation():
    """
    Generate a grounded explanation using the same
    filtered college/branch candidates as the prediction
    workflow.
    Supports both GET and POST requests.
    """

    conn = None

    try:
        # -------------------------------------------------
        # Read inputs from query parameters or JSON body
        # -------------------------------------------------
        body = request.get_json(silent=True) or {}

        cutoff_mark = request.args.get("cutoff_mark") if request.args.get("cutoff_mark") is not None else body.get("cutoff_mark")
        community = request.args.get("community") or body.get("community")
        district = request.args.get("district") or body.get("district")
        branch_code = request.args.get("branch_code") or body.get("branch_code")
        college_code = request.args.get("college_code") or body.get("college_code")

        limit_value = request.args.get("limit") or body.get("limit") or "8"


        # -------------------------------------------------
        # Validate cutoff
        # -------------------------------------------------

        if cutoff_mark is None:
            return jsonify({
                "status": "error",
                "message": "cutoff_mark is required"
            }), 400

        try:
            cutoff_mark = float(cutoff_mark)
        except ValueError:
            return jsonify({
                "status": "error",
                "message": "cutoff_mark must be a number"
            }), 400

        if cutoff_mark < 0 or cutoff_mark > 200:
            return jsonify({
                "status": "error",
                "message": "cutoff_mark must be between 0 and 200"
            }), 400

        # -------------------------------------------------
        # Validate community
        # -------------------------------------------------

        if not community:
            return jsonify({
                "status": "error",
                "message": "community is required"
            }), 400

        community = community.upper()

        if community not in ALLOWED_COMMUNITIES:
            return jsonify({
                "status": "error",
                "message": (
                    "Invalid community. "
                    "Allowed values: "
                    "OC, BC, BCM, MBC, SC, SCA, ST"
                )
            }), 400

        # -------------------------------------------------
        # Validate limit
        # -------------------------------------------------

        try:
            limit = int(limit_value)
        except ValueError:
            return jsonify({
                "status": "error",
                "message": "limit must be a whole number"
            }), 400

        if limit <= 0:
            return jsonify({
                "status": "error",
                "message": "limit must be greater than 0"
            }), 400

        limit = min(limit, 12)

        # -------------------------------------------------
        # Connect to database
        # -------------------------------------------------

        conn = get_db_connection()

        # -------------------------------------------------
        # Retrieve all relevant historical rows
        #
        # These are the same filters used by the prediction
        # workflow: community, quota, district, branch,
        # and years 2021-2025.
        # -------------------------------------------------

        query = """
            SELECT
                c.college_code,
                c.college_name,
                c.district,
                c.college_type,
                b.branch_code,
                b.branch_name,
                h.year,
                h.cutoff_mark,
                h.closing_rank,
                h.is_partial
            FROM historical_admissions h
            JOIN colleges c
                ON h.college_code = c.college_code
            JOIN branches b
                ON h.branch_code = b.branch_code
            WHERE h.community = %s
              AND h.quota = 'GENERAL'
              AND h.year BETWEEN 2021 AND 2025
        """

        params = [community]

        if district:
            query += " AND c.district = %s"
            params.append(district)

        if branch_code:
            query += " AND b.branch_code = %s"
            params.append(branch_code)

        if college_code:
            query += " AND c.college_code = %s"
            params.append(college_code)

        query += """
            ORDER BY
                c.college_code,
                b.branch_code,
                h.year
        """


        with conn.cursor() as cursor:
            cursor.execute(query, params)
            rows = cursor.fetchall()

        # -------------------------------------------------
        # Group historical rows by college + branch
        # -------------------------------------------------

        grouped = {}

        for row in rows:

            key = (
                row[0],
                row[4]
            )

            if key not in grouped:

                grouped[key] = {
                    "college_code": row[0],
                    "college_name": row[1],
                    "district": row[2],
                    "college_type": row[3],
                    "branch_code": row[4],
                    "branch_name": row[5],
                    "history": []
                }

            grouped[key]["history"].append({
                "year": row[6],
                "cutoff_mark": (
                    float(row[7])
                    if row[7] is not None
                    else None
                ),
                "closing_rank": (
                    int(row[8])
                    if row[8] is not None
                    else None
                ),
                "is_partial": bool(row[9])
            })

        # -------------------------------------------------
        # Build candidate summaries
        # -------------------------------------------------

        candidates = []

        for item in grouped.values():

            cutoff_records = [
                record
                for record in item["history"]
                if record["cutoff_mark"] is not None
            ]

            if not cutoff_records:
                continue

            matched_records = [
                record
                for record in cutoff_records
                if cutoff_mark >= record["cutoff_mark"]
            ]

            if not matched_records:
                continue

            matched_years = len(matched_records)

            available_years = len(
                cutoff_records
            )

            historical_fit_score = round(
                (
                    matched_years /
                    available_years
                ) * 100,
                2
            )

            latest_record = max(
                cutoff_records,
                key=lambda record: record["year"]
            )

            average_cutoff = round(
                sum(
                    record["cutoff_mark"]
                    for record in cutoff_records
                ) / available_years,
                3
            )

            minimum_cutoff = min(
                record["cutoff_mark"]
                for record in cutoff_records
            )

            maximum_cutoff = max(
                record["cutoff_mark"]
                for record in cutoff_records
            )

            # Change from earliest available cutoff
            # to latest available cutoff.
            cutoff_change = round(
                cutoff_records[-1]["cutoff_mark"]
                - cutoff_records[0]["cutoff_mark"],
                3
            )

            candidates.append({
                "college_code":
                    item["college_code"],

                "college_name":
                    item["college_name"],

                "district":
                    item["district"],

                "college_type":
                    item["college_type"],

                "branch_code":
                    item["branch_code"],

                "branch_name":
                    item["branch_name"],

                "historical_fit_score":
                    historical_fit_score,

                "matched_years":
                    matched_years,

                "available_years":
                    available_years,

                "latest_year":
                    latest_record["year"],

                "latest_cutoff":
                    latest_record["cutoff_mark"],

                "latest_closing_rank":
                    latest_record["closing_rank"],

                "average_cutoff":
                    average_cutoff,

                "minimum_cutoff":
                    minimum_cutoff,

                "maximum_cutoff":
                    maximum_cutoff,

                "cutoff_change":
                    cutoff_change,

                "historical_records":
                    item["history"]
            })

        # -------------------------------------------------
        # Sort exactly around useful historical evidence
        # -------------------------------------------------

        candidates.sort(
            key=lambda item: (
                -item["historical_fit_score"],
                -(item["latest_cutoff"] or 0),
                item["college_code"],
                item["branch_code"]
            )
        )

        # Keep a small, relevant RAG context.
        candidates = candidates[:limit]

        # -------------------------------------------------
        # No evidence
        # -------------------------------------------------

        if not candidates:

            return jsonify({
                "status": "ok",
                "retrieved_count": 0,
                "retrieved_evidence": [],
                "explanation": (
                    "No matching historical cutoff records "
                    "were found for the supplied inputs."
                )
            }), 200

        # -------------------------------------------------
        # Compact evidence for Gemini
        # -------------------------------------------------

        evidence = []

        for candidate in candidates:

            evidence.append({
                "college_code":
                    candidate["college_code"],

                "college_name":
                    candidate["college_name"],

                "district":
                    candidate["district"],

                "college_type":
                    candidate["college_type"],

                "branch_code":
                    candidate["branch_code"],

                "branch_name":
                    candidate["branch_name"],

                "historical_fit_score":
                    candidate["historical_fit_score"],

                "matched_years":
                    candidate["matched_years"],

                "available_years":
                    candidate["available_years"],

                "latest_year":
                    candidate["latest_year"],

                "latest_cutoff":
                    candidate["latest_cutoff"],

                "latest_closing_rank":
                    candidate["latest_closing_rank"],

                "average_cutoff":
                    candidate["average_cutoff"],

                "cutoff_change":
                    candidate["cutoff_change"],

                "historical_records":
                    candidate["historical_records"]
            })

        # -------------------------------------------------
        # Generate grounded explanation
        # -------------------------------------------------

        res = generate_grounded_explanation(
            cutoff_mark=cutoff_mark,
            community=community,
            retrieved_results=evidence,
            district=district,
            branch_code=branch_code,
            college_code=college_code,
        )

        if isinstance(res, tuple):
            explanation, model_name = res
        else:
            explanation, model_name = res, "Gemini"

        # -------------------------------------------------
        # Return RAG response
        # -------------------------------------------------

        return jsonify({
            "status": "ok",

            "input": {
                "cutoff_mark": cutoff_mark,
                "community": community,
                "district": district,
                "branch_code": branch_code,
                "college_code": college_code,
            },

            "retrieved_count":
                len(evidence),

            "retrieved_evidence":
                evidence,

            "generation_model":
                model_name,

            "explanation":
                explanation,


            "note": (
                "The explanation is generated from "
                "historical evidence retrieved from the "
                "CollegeConnect database. The historical-fit "
                "score is not a calibrated admission probability."
            )
        }), 200

    except pymysql.MySQLError as err:

        return jsonify({
            "status": "error",
            "message": (
                f"Database error: {str(err)}"
            )
        }), 500

    except Exception as err:

        return jsonify({
            "status": "error",
            "message": (
                f"RAG generation error: {str(err)}"
            )
        }), 500

    finally:

        if conn:
            conn.close()