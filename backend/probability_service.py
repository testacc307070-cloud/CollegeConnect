"""
CollegeConnect Probability Service

Retrieves the five-year historical TNEA records for a community/quota
and attaches the relevant college-branch history to every candidate.

The deterministic scorer in scoring.py then calculates the probability.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any


try:

    from backend.scoring import (
        generate_probability_scores
    )

except ImportError:

    from scoring import (
        generate_probability_scores
    )


START_YEAR = 2021
END_YEAR = 2025


def candidate_key(
    candidate: dict,
) -> tuple[int, str]:

    return (

        int(
            candidate[
                "college_code"
            ]
        ),

        str(
            candidate[
                "branch_code"
            ]
        ),

    )


def attach_probability_scores(
    conn: Any,
    candidates: list[dict],
    community: str,
    student_input: dict,
    quota: str = "GENERAL",
) -> tuple[list[dict], str | None]:

    if not candidates:

        return (
            [],
            None,
        )


    # ------------------------------------------------------------------------
    # Fetch the full five-year history for the requested community/quota.
    # ------------------------------------------------------------------------

    try:

        with conn.cursor() as cursor:

            cursor.execute(
                """

                SELECT

                    college_code,

                    branch_code,

                    year,

                    cutoff_mark,

                    closing_rank,

                    is_partial

                FROM historical_admissions

                WHERE community = %s

                  AND quota = %s

                  AND year BETWEEN %s AND %s

                ORDER BY

                    college_code,

                    branch_code,

                    year;

                """,

                (
                    community,
                    quota,
                    START_YEAR,
                    END_YEAR,
                ),

            )

            rows = cursor.fetchall()


    except Exception as exc:

        return (

            candidates,

            f"Historical probability retrieval failed: {exc}",

        )


    # ------------------------------------------------------------------------
    # Build:

    # (college_code, branch_code)
    #
    # -> five-year records
    # ------------------------------------------------------------------------

    history_by_candidate = defaultdict(
        list
    )


    for row in rows:

        if hasattr(
            row,
            "keys",
        ):

            college_code = row[
                    "college_code"
                ]

            branch_code =    row[
                    "branch_code"
                ]

            history_by_candidate[
                (
                    int(
                        college_code
                    ),

                    str(
                        branch_code
                    ),
                )
            ].append({

                "year":
                    row[
                        "year"
                    ],

                "cutoff_mark":
                    row[
                        "cutoff_mark"
                    ],

                "closing_rank":
                    row[
                        "closing_rank"
                    ],

                "is_partial":
                    row[
                        "is_partial"
                    ],

            })


        else:

            (
                college_code,
                branch_code,
                year,
                cutoff_mark,
                closing_rank,
                is_partial,
            ) = row


            history_by_candidate[
                (
                    int(
                        college_code
                    ),

                    str(
                        branch_code
                    ),
                )
            ].append({

                "year":
                    year,

                "cutoff_mark":
                    cutoff_mark,

                "closing_rank":
                    closing_rank,

                "is_partial":
                    is_partial,

            })


    # ------------------------------------------------------------------------
    # Enrich ALL candidates.
    # ------------------------------------------------------------------------

    enriched = []


    for candidate in candidates:

        result =  dict(
                candidate
            )


        try:

            key =    candidate_key(
                    candidate
                )

        except (
            KeyError,
            TypeError,
            ValueError,
        ):

            key = (
                -1,
                "",
            )


        result[
            "historical_records"
        ] = history_by_candidate.get(
            key,
            [],
        )


        enriched.append(
            result
        )


    # ------------------------------------------------------------------------
    # Deterministic probability scoring.
    # ------------------------------------------------------------------------

    try:

        scored =  generate_probability_scores(

                student_input=
                    student_input,

                candidates=
                    enriched,

            )


    except Exception as exc:

        fallback = []


        for candidate in enriched:

            result =  dict(
                    candidate
                )


            result[
                "estimated_probability"
            ] = None


            result[
                "tier"
            ] = None


            result[
                "probability_reasoning"
            ] = None


            result.pop(
                "historical_records",
                None,
            )


            fallback.append(
                result
            )


        return (

            fallback,

            f"Probability scoring failed: {exc}",

        )


    # ------------------------------------------------------------------------
    # Dynamic resolution of latest values & trajectory across available years
    # ------------------------------------------------------------------------

    final_results = []

    for result in scored:

        cleaned = dict(result)
        hist = result.get("historical_records") or []

        valid_cutoffs = [
            r for r in hist
            if r.get("cutoff_mark") is not None
        ]

        valid_ranks = [
            r for r in hist
            if r.get("closing_rank") is not None
        ]

        if valid_cutoffs:
            valid_cutoffs.sort(key=lambda x: int(x["year"]))
            if cleaned.get("latest_cutoff") is None:
                cleaned["latest_cutoff"] = float(valid_cutoffs[-1]["cutoff_mark"])
            if (
                cleaned.get("latest_closing_rank") is None
                and valid_cutoffs[-1].get("closing_rank") is not None
            ):
                cleaned["latest_closing_rank"] = int(valid_cutoffs[-1]["closing_rank"])
            if cleaned.get("cutoff_change") is None and len(valid_cutoffs) >= 2:
                cleaned["cutoff_change"] = round(
                    float(valid_cutoffs[-1]["cutoff_mark"])
                    - float(valid_cutoffs[0]["cutoff_mark"]),
                    3
                )

        if valid_ranks:
            valid_ranks.sort(key=lambda x: int(x["year"]))
            if cleaned.get("latest_closing_rank") is None:
                cleaned["latest_closing_rank"] = int(valid_ranks[-1]["closing_rank"])
            if (
                cleaned.get("latest_cutoff") is None
                and valid_ranks[-1].get("cutoff_mark") is not None
            ):
                cleaned["latest_cutoff"] = float(valid_ranks[-1]["cutoff_mark"])
            if cleaned.get("rank_change") is None and len(valid_ranks) >= 2:
                cleaned["rank_change"] = (
                    int(valid_ranks[-1]["closing_rank"])
                    - int(valid_ranks[0]["closing_rank"])
                )

        cleaned.pop(
            "historical_records",
            None,
        )

        final_results.append(
            cleaned
        )

    return (
        final_results,
        None,
    )