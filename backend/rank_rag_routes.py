"""
RAG API route for state-rank based analysis.

Flow:
1. Receive student state rank and community.
2. Retrieve relevant historical closing-rank evidence.
3. Send the evidence to Gemini.
4. Return a grounded explanation.
"""

import pymysql
from flask import Blueprint, jsonify, request

from backend.db import get_db_connection
from backend.rag import generate_rank_grounded_explanation


rank_rag_bp = Blueprint("rank_rag", __name__)


ALLOWED_COMMUNITIES = {
    "OC",
    "BC",
    "BCM",
    "MBC",
    "SC",
    "SCA",
    "ST"
}


@rank_rag_bp.route("/api/rank-rag-explanation", methods=["GET", "POST"])
def rank_rag_explanation():
    """
    Generate a grounded explanation for a student's
    state rank. Supports both GET and POST.
    """

    conn = None

    try:
        # -------------------------------------------------
        # Read inputs from query parameters or JSON body
        # -------------------------------------------------
        body = request.get_json(silent=True) or {}

        state_rank = request.args.get("state_rank") if request.args.get("state_rank") is not None else body.get("state_rank")
        community = request.args.get("community") or body.get("community")
        district = request.args.get("district") or body.get("district")
        branch_code = request.args.get("branch_code") or body.get("branch_code")
        college_code = request.args.get("college_code") or body.get("college_code")


        # -------------------------------------------------
        # Validate state rank
        # -------------------------------------------------

        if state_rank is None:
            return jsonify({
                "status": "error",
                "message": "state_rank is required"
            }), 400

        try:
            state_rank = int(state_rank)
        except ValueError:
            return jsonify({
                "status": "error",
                "message": "state_rank must be a whole number"
            }), 400

        if state_rank <= 0:
            return jsonify({
                "status": "error",
                "message": "state_rank must be greater than 0"
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
        # Database connection
        # -------------------------------------------------

        conn = get_db_connection()

        # -------------------------------------------------
        # Retrieve relevant historical records
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
                h.closing_rank,
                h.cutoff_mark,
                h.is_partial
            FROM historical_admissions h

            JOIN colleges c
                ON h.college_code = c.college_code

            JOIN branches b
                ON h.branch_code = b.branch_code

            WHERE h.community = %s
              AND h.quota = 'GENERAL'
              AND h.closing_rank IS NOT NULL
              AND h.year BETWEEN 2021 AND 2025
              AND h.closing_rank >= %s
        """

        params = [
            community,
            state_rank
        ]

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
                h.year DESC,
                h.closing_rank ASC
            LIMIT 20
        """


        with conn.cursor() as cursor:
            cursor.execute(query, params)
            rows = cursor.fetchall()

        # -------------------------------------------------
        # No evidence
        # -------------------------------------------------

        if not rows:
            return jsonify({
                "status": "ok",
                "retrieved_count": 0,
                "retrieved_evidence": [],
                "explanation": (
                    "No matching historical closing-rank "
                    "records were found for the supplied inputs."
                )
            }), 200

        # -------------------------------------------------
        # Build evidence
        # -------------------------------------------------

        evidence = []

        for row in rows:

            historical_rank = int(row[7])

            fit = (
                100
                if state_rank <= historical_rank
                else 0
            )

            evidence.append({

                "college_code":
                    row[0],

                "college_name":
                    row[1],

                "district":
                    row[2],

                "college_type":
                    row[3],

                "branch_code":
                    row[4],

                "branch_name":
                    row[5],

                "year":
                    row[6],

                "closing_rank":
                    historical_rank,

                "cutoff_mark":
                    (
                        float(row[8])
                        if row[8] is not None
                        else None
                    ),

                "historical_fit":
                    fit,

                "is_partial":
                    bool(row[9])

            })

        # -------------------------------------------------
        # Generate grounded explanation
        # -------------------------------------------------

        res = generate_rank_grounded_explanation(
            state_rank=state_rank,
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
        # Return
        # -------------------------------------------------

        return jsonify({

            "status": "ok",

            "input": {
                "state_rank": state_rank,
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
                "historical closing-rank evidence. "
                "Historical matching is not a guarantee "
                "of admission and is not a calibrated "
                "admission probability."
            )

        }), 200

    except pymysql.MySQLError as err:

        return jsonify({
            "status": "error",
            "message":
                f"Database error: {str(err)}"
        }), 500

    except Exception as err:

        return jsonify({
            "status": "error",
            "message":
                f"RAG generation error: {str(err)}"
        }), 500

    finally:

        if conn:
            conn.close()