from typing import Any, Optional

import pymysql
from flask import Blueprint, jsonify, request

try:
    from backend.db import get_db_connection
    from backend.probability_service import attach_probability_scores
except ImportError:
    from db import get_db_connection
    from probability_service import attach_probability_scores


# ============================================================================
# BLUEPRINT
# ============================================================================

rank_bp = Blueprint(
    "rank_routes",
    __name__,
)


# ============================================================================
# CONSTANTS
# ============================================================================

VALID_COMMUNITIES = {
    "OC",
    "BC",
    "BCM",
    "MBC",
    "SC",
    "SCA",
    "ST",
}

DEFAULT_QUOTA = "GENERAL"

DEFAULT_RESULT_LIMIT = 30
MAX_RESULT_LIMIT = 30


def resolve_quota(user_quota: Optional[str]) -> tuple[str, str, Optional[str]]:
    """
    Resolves the user selected quota. Since historical counseling data is based on
    the primary GENERAL pool, 7.5% and special quotas query GENERAL as baseline while
    providing tailored guidance/notes.
    Returns (user_quota, db_quota, quota_note).
    """
    raw = (user_quota or "GENERAL").strip().upper()
    if raw in ("GOVT_7_5", "7.5_GOVT", "7.5%"):
        return raw, "GENERAL", "7.5% Government school preferential quota operates on dedicated DoTE counseling supplements; historical general cutoffs shown as reference baseline (actual 7.5% thresholds typically run 15–30 marks lower)."
    elif raw.startswith("SPECIAL"):
        return raw, "GENERAL", f"Special reservation quota ({raw}) operates through preliminary DoTE rounds; general cutoffs shown as baseline reference."
    return raw, raw, None


def safe_close(conn: Any) -> None:

    if conn is not None:

        try:
            conn.close()

        except Exception:
            pass


def normalize_optional_text(
    value: Optional[str],
) -> Optional[str]:

    if value is None:
        return None

    value = value.strip()

    return value if value else None


def parse_positive_int(
    value: Optional[str],
    field_name: str,
) -> int:

    if value is None:

        raise ValueError(
            f"{field_name} is required."
        )

    try:

        number = int(value)

    except (
        TypeError,
        ValueError,
    ):

        raise ValueError(
            f"{field_name} must be a valid integer."
        )

    if number <= 0:

        raise ValueError(
            f"{field_name} must be greater than zero."
        )

    return number


def parse_limit(
    value: Optional[str],
) -> int:

    if value is None:

        return DEFAULT_RESULT_LIMIT

    try:

        limit = int(value)

    except (
        TypeError,
        ValueError,
    ):

        raise ValueError(
            "limit must be a valid integer."
        )

    if limit <= 0:

        raise ValueError(
            "limit must be greater than zero."
        )

    return min(
        limit,
        MAX_RESULT_LIMIT,
    )


def validate_community(
    community: str,
) -> str:

    community = (
        community or ""
    ).strip().upper()

    if community not in VALID_COMMUNITIES:
        allowed = ", ".join(sorted(VALID_COMMUNITIES))
        raise ValueError(
            f"Invalid community '{community}'. Allowed values: {allowed}."
        )

    return community



def get_multiple_query_values(
    parameter_name: str,
) -> list[str]:

    values = request.args.getlist(
        parameter_name
    )

    output: list[str] = []

    for value in values:

        if value is None:
            continue

        for part in str(
            value
        ).split(","):

            part = part.strip()

            if part:

                output.append(
                    part
                )

    seen = set()

    unique_values = []

    for value in output:

        key = value.upper()

        if key in seen:

            continue

        seen.add(key)

        unique_values.append(
            value
        )

    return unique_values


def build_in_clause(
    values: list[Any],
) -> tuple[str, list[Any]]:

    placeholders = ", ".join(
        ["%s"] * len(values)
    )

    return placeholders, list(values)


def probability_value(
    candidate: dict,
) -> float:

    value = candidate.get(
        "estimated_probability"
    )

    if value is None:

        return -1.0

    try:

        return float(
            value
        )

    except (
        TypeError,
        ValueError,
    ):

        return -1.0


def select_display_candidates(
    results: list[dict],
    limit: int,
) -> list[dict]:

    if not results:

        return []

    if len(results) <= limit:

        selected = list(
            results
        )

    else:

        ranked = sorted(

            results,

            key=lambda item: (

                -probability_value(
                    item
                ),

                str(
                    item.get(
                        "college_name",
                        "",
                    )
                ),

                str(
                    item.get(
                        "branch_code",
                        "",
                    )
                ),

            ),

        )

        high_count = (
            limit // 3
        )

        middle_count = (
            limit // 3
        )

        low_count = (
            limit
            -
            high_count
            -
            middle_count
        )

        high = ranked[
            :high_count
        ]

        middle_start = max(
            0,
            (
                len(ranked)
                // 2
            )
            -
            (
                middle_count
                // 2
            ),
        )

        middle = ranked[
            middle_start:
            middle_start
            +
            middle_count
        ]

        low = (

            ranked[
                -low_count:
            ]

            if low_count > 0

            else []

        )

        selected = []

        seen = set()

        for candidate in (
            high
            +
            middle
            +
            low
        ):

            key = (

                str(
                    candidate.get(
                        "college_code",
                        "",
                    )
                ),

                str(
                    candidate.get(
                        "branch_code",
                        "",
                    )
                ),

            )

            if key in seen:

                continue

            seen.add(key)

            selected.append(
                candidate
            )

        if len(selected) < limit:

            for candidate in ranked:

                key = (

                    str(
                        candidate.get(
                            "college_code",
                            "",
                        )
                    ),

                    str(
                        candidate.get(
                            "branch_code",
                            "",
                        )
                    ),

                )

                if key in seen:

                    continue

                seen.add(key)

                selected.append(
                    candidate
                )

                if (
                    len(selected)
                    >= limit
                ):

                    break

    def tier_order(
        candidate: dict,
    ) -> int:

        tier = str(

            candidate.get(
                "tier",
                "",
            )

        ).title()

        return {

            "Reach": 0,

            "Target": 1,

            "Safe": 2,

        }.get(
            tier,
            1,
        )

    selected.sort(

        key=lambda item: (

            tier_order(item),

            -probability_value(
                item
            ),

            str(
                item.get(
                    "college_name",
                    "",
                )
            ),

        )

    )

    return selected[
        :limit
    ]


# ============================================================================
# RANK PREDICTIONS
# ============================================================================

@rank_bp.route(
    "/api/rank-predictions",
    methods=["GET"],
)
def rank_predictions():

    conn = None

    try:

        state_rank = parse_positive_int(

            request.args.get(
                "state_rank"
            ),

            "state_rank",

        )

        community = validate_community(

            request.args.get(
                "community",
                "OC",
            )

        )

        districts_filter = (
            get_multiple_query_values(
                "district"
            )
        )

        branches_filter = (
            get_multiple_query_values(
                "branch_code"
            )
        )

        college_code_value = (
            normalize_optional_text(

                request.args.get(
                    "college_code"
                )

            )
        )

        college_code = None

        if college_code_value:

            college_code = parse_positive_int(

                college_code_value,

                "college_code",

            )

        user_quota = request.args.get("quota", DEFAULT_QUOTA)
        quota, db_quota, quota_note = resolve_quota(user_quota)

        tier_filter = request.args.get("tier") or request.args.get("institutional_tier")
        if tier_filter:
            tier_filter = tier_filter.strip()

        limit = parse_limit(

            request.args.get(
                "limit"
            )

        )

        conn = get_db_connection()


        # --------------------------------------------------------------------
        # RETRIEVE COMPLETE FILTERED CANDIDATE SET
        # --------------------------------------------------------------------

        sql = """

            SELECT

                c.college_code,

                c.college_name,

                c.district,

                c.college_type,

                c.institutional_tier,

                h.branch_code,

                b.branch_name,

                ROUND(

                    (

                        SUM(

                            CASE

                                WHEN h.closing_rank IS NOT NULL

                                 AND %s <= h.closing_rank

                                THEN 1

                                ELSE 0

                            END

                        )

                        /

                        NULLIF(

                            COUNT(
                                h.closing_rank
                            ),

                            0

                        )

                    ) * 100,

                    1

                ) AS historical_fit_score,

                SUM(

                    CASE

                        WHEN h.closing_rank IS NOT NULL

                        THEN 1

                        ELSE 0

                    END

                ) AS available_years,

                SUM(

                    CASE

                        WHEN h.closing_rank IS NOT NULL

                         AND %s <= h.closing_rank

                        THEN 1

                        ELSE 0

                    END

                ) AS matched_years,

                MAX(

                    CASE

                        WHEN h.year = 2025

                        THEN h.closing_rank

                    END

                ) AS latest_closing_rank,

                MAX(

                    CASE

                        WHEN h.year = 2025

                        THEN h.cutoff_mark

                    END

                ) AS latest_cutoff,

                MAX(

                    CASE

                        WHEN h.year = 2021

                        THEN h.closing_rank

                    END

                ) AS earliest_closing_rank,

                (

                    CAST(

                        MAX(

                            CASE

                                WHEN h.year = 2025

                                THEN h.closing_rank

                            END

                        ) AS SIGNED

                    )

                    -

                    CAST(

                        MAX(

                            CASE

                                WHEN h.year = 2021

                                THEN h.closing_rank

                            END

                        ) AS SIGNED

                    )

                ) AS rank_change

            FROM historical_admissions h

            INNER JOIN colleges c

                ON c.college_code =
                   h.college_code

            INNER JOIN branches b

                ON b.branch_code =
                   h.branch_code

            WHERE h.community = %s

              AND h.quota = %s

        """

        params: list[Any] = [

            state_rank,

            state_rank,

            community,

            db_quota,

        ]


        if districts_filter:

            placeholders, values = (
                build_in_clause(
                    districts_filter
                )
            )

            sql += f"""

                AND c.district IN (

                    {placeholders}

                )

            """

            params.extend(
                values
            )


        if branches_filter:

            placeholders, values = (
                build_in_clause(
                    branches_filter
                )
            )

            sql += f"""

                AND h.branch_code IN (

                    {placeholders}

                )

            """

            params.extend(
                values
            )


        if college_code is not None:

            sql += """

                AND h.college_code = %s

            """

            params.append(
                college_code
            )


        if tier_filter and tier_filter.upper() != "ALL":

            sql += """

                AND c.institutional_tier = %s

            """

            params.append(
                tier_filter
            )


        sql += """

            GROUP BY

                c.college_code,

                c.college_name,

                c.district,

                c.college_type,

                c.institutional_tier,

                h.branch_code,

                b.branch_name

            HAVING COUNT(
                h.closing_rank
            ) > 0

            ORDER BY

                historical_fit_score DESC,

                c.college_name ASC;

        """


        with conn.cursor(
            pymysql.cursors.DictCursor
        ) as cursor:

            cursor.execute(
                sql,
                params,
            )

            all_results =list(
                    cursor.fetchall()
                )


        # --------------------------------------------------------------------
        # DETERMINISTIC PROBABILITY SCORING
        # --------------------------------------------------------------------

        student_input = {

            "cutoff_mark":
                None,

            "state_rank":
                state_rank,

            "community":
                community,

            "district":
                districts_filter,

            "branch_code":
                branches_filter,

        }


        scored_results, scoring_error = (
            attach_probability_scores(

                conn=conn,

                candidates=
                    all_results,

                community=
                    community,

                student_input=
                    student_input,

                quota=
                    db_quota,

            )
        )


        # --------------------------------------------------------------------
        # DISPLAY REPRESENTATIVE RESULTS
        # --------------------------------------------------------------------

        results =select_display_candidates(

                scored_results,

                limit,

            )


        # --------------------------------------------------------------------
        # COUNT DISPLAYED TIERS
        # --------------------------------------------------------------------

        result_counts = {

            "Reach": 0,

            "Target": 0,

            "Safe": 0,

        }


        for result in results:

            tier = str(

                result.get(
                    "tier",
                    "",
                )

            ).title()


            if tier in result_counts:

                result_counts[tier] += 1


        return jsonify({

            "status":
                "ok",

            "mode":
                "rank",

            "student_input": {

                "state_rank":
                    state_rank,

                "community":
                    community,

                "district":
                    districts_filter,

                "branch_code":
                    branches_filter,

                "college_code":
                    college_code,

                "quota":
                    quota,

                "quota_note":
                    quota_note,

                "tier":
                    tier_filter if (tier_filter and tier_filter.upper() != "ALL") else "ALL",

            },

            "candidate_pool_size":
                len(all_results),

            "scored_candidate_count":
                len(scored_results),

            "count":
                len(results),

            "result_counts":
                result_counts,

            "predictions":
                results,

            "probability_scoring": {

                "status": (

                    "completed"

                    if scoring_error is None

                    else "partial"

                ),

                "error":
                    scoring_error,

            },

        }), 200


    except ValueError as err:

        return jsonify({

            "status":
                "error",

            "message":
                str(err),

        }), 400


    except pymysql.MySQLError as err:

        return jsonify({

            "status":
                "error",

            "message":
                f"Database error: {err}",

        }), 500


    except Exception as err:

        return jsonify({

            "status":
                "error",

            "message":
                f"Unexpected error: {err}",

        }), 500


    finally:

        safe_close(conn)


# ============================================================================
# REGISTER
# ============================================================================

def register_rank_routes(
    app,
):

    app.register_blueprint(
        rank_bp
    )