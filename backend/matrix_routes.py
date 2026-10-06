from flask import Blueprint, jsonify, request
import pymysql

from backend.db import get_db_connection


matrix_bp = Blueprint("matrix", __name__)


ALLOWED_COMMUNITIES = {
    "OC",
    "BC",
    "BCM",
    "MBC",
    "SC",
    "SCA",
    "ST"
}


@matrix_bp.route("/api/rank-matrix", methods=["GET"])
def rank_matrix():
    """
    Return the latest available closing-rank information
    for college/branch combinations.

    Required:
    - community

    Optional:
    - district
    - branch_code
    - college_code
    - limit
    """

    conn = None

    try:
        community = request.args.get("community")
        district = request.args.get("district")
        branch_code = request.args.get("branch_code")
        college_code = request.args.get("college_code")

        limit_value = request.args.get("limit", "100")

        # ---------------------------------------------
        # Validate community
        # ---------------------------------------------

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

        # ---------------------------------------------
        # Validate limit
        # ---------------------------------------------

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

        limit = min(limit, 200)

        conn = get_db_connection()

        # ---------------------------------------------
        # Build query
        #
        # We select the latest year in which a closing
        # rank actually exists.
        # ---------------------------------------------

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
                h.closing_rank
            FROM historical_admissions h

            JOIN colleges c
                ON h.college_code = c.college_code

            JOIN branches b
                ON h.branch_code = b.branch_code

            WHERE h.community = %s
              AND h.quota = 'GENERAL'
              AND h.closing_rank IS NOT NULL

              AND h.year = (
                  SELECT MAX(h2.year)
                  FROM historical_admissions h2
                  WHERE h2.college_code = h.college_code
                    AND h2.branch_code = h.branch_code
                    AND h2.community = h.community
                    AND h2.quota = h.quota
                    AND h2.closing_rank IS NOT NULL
              )
        """

        params = [community]

        # ---------------------------------------------
        # Optional district filter
        # ---------------------------------------------

        if district:
            query += " AND c.district = %s"
            params.append(district)

        # ---------------------------------------------
        # Optional branch filter
        # ---------------------------------------------

        if branch_code:
            query += " AND b.branch_code = %s"
            params.append(branch_code)

        # ---------------------------------------------
        # Optional college filter
        # ---------------------------------------------

        if college_code:
            try:
                college_code_int = int(college_code)
                query += " AND c.college_code = %s"
                params.append(college_code_int)
            except ValueError:
                pass

        query += """
            ORDER BY
                h.closing_rank,
                c.college_code,
                b.branch_code
            LIMIT %s
        """

        params.append(limit)

        # ---------------------------------------------
        # Execute
        # ---------------------------------------------

        with conn.cursor() as cursor:
            cursor.execute(query, params)
            rows = cursor.fetchall()

        # ---------------------------------------------
        # Format response
        # ---------------------------------------------

        results = []

        for row in rows:

            results.append({
                "college_code": row[0],
                "college_name": row[1],
                "district": row[2],
                "college_type": row[3],
                "branch_code": row[4],
                "branch_name": row[5],
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
                )
            })

        return jsonify({
            "status": "ok",
            "count": len(results),

            "input": {
                "community": community,
                "district": district,
                "branch_code": branch_code,
                "college_code": college_code
            },

            "results": results,

            "note": (
                "Each row represents the latest available "
                "historical closing-rank record for the "
                "selected community."
            )
        }), 200

    except pymysql.MySQLError as err:

        return jsonify({
            "status": "error",
            "message": f"Database error: {str(err)}"
        }), 500

    except Exception as err:

        return jsonify({
            "status": "error",
            "message": f"An unexpected error occurred: {str(err)}"
        }), 500

    finally:

        if conn:
            conn.close()