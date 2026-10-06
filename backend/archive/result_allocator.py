"""
CollegeConnect Result Allocator

Final student-facing categories are based on probability thresholds.

Probability ranges:

    Safe   : 85 - 100
    Target : 60 - 84.9
    Reach  : 0 - 59.9

The user's result preferences control how many results are displayed
from each category, but the system never changes a candidate's tier
just to fill a requested number.
"""

from typing import Optional


# ============================================================================
# PROBABILITY THRESHOLDS
# ============================================================================

SAFE_MIN = 85.0
TARGET_MIN = 60.0


# ============================================================================
# HELPERS
# ============================================================================

def get_probability(
    candidate: dict,
) -> Optional[float]:
    """
    Safely read the Gemini estimated probability.
    """

    value = candidate.get(
        "estimated_probability"
    )

    if value is None:
        return None

    try:

        probability = float(
            value
        )

    except (
        TypeError,
        ValueError,
    ):

        return None

    return max(
        0.0,
        min(
            100.0,
            probability,
        ),
    )


def candidate_key(
    candidate: dict,
) -> tuple[str, str]:
    """
    Unique college + branch identifier.
    """

    return (
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


def determine_tier(
    probability: Optional[float],
) -> str:
    """
    Assign the final CollegeConnect tier.

    This is based ONLY on estimated probability.
    """

    if probability is None:
        return "Target"

    if probability >= SAFE_MIN:
        return "Safe"

    if probability >= TARGET_MIN:
        return "Target"

    return "Reach"


# ============================================================================
# MAIN ALLOCATION
# ============================================================================

def allocate_probability_mix(
    scored_results: list[dict],
    preferences: dict,
) -> tuple[list[dict], dict]:
    """
    Create the final student-facing result set.

    Example:

        Total  = 30
        Reach  = 6
        Target = 12
        Safe   = 12

    These are DISPLAY LIMITS.

    The candidate's actual tier is always determined from probability:

        85-100  -> Safe
        60-84   -> Target
        0-59    -> Reach

    Therefore:

        90% can NEVER become Reach.

    """

    requested_total = int(
        preferences.get(
            "result_total",
            30,
        )
    )

    requested_reach = int(
        preferences.get(
            "reach_count",
            6,
        )
    )

    requested_target = int(
        preferences.get(
            "target_count",
            12,
        )
    )

    requested_safe = int(
        preferences.get(
            "safe_count",
            12,
        )
    )

    # ------------------------------------------------------------------------
    # Remove duplicate college + branch pairs.
    # ------------------------------------------------------------------------

    unique_candidates = []

    seen = set()

    for candidate in scored_results:

        key = candidate_key(
            candidate
        )

        if key in seen:
            continue

        seen.add(
            key
        )

        unique_candidates.append(
            dict(candidate)
        )

    # ------------------------------------------------------------------------
    # Assign tier from probability.
    # ------------------------------------------------------------------------

    groups = {
        "Reach": [],
        "Target": [],
        "Safe": [],
    }

    for candidate in unique_candidates:

        probability = get_probability(
            candidate
        )

        final_tier = determine_tier(
            probability
        )

        # Preserve Gemini's original tier for debugging/transparency.
        candidate["model_tier"] = (
            candidate.get(
                "tier"
            )
        )

        candidate["tier"] = (
            final_tier
        )

        groups[
            final_tier
        ].append(
            candidate
        )

    # ------------------------------------------------------------------------
    # Sort candidates inside each group.
    #
    # Reach:
    #     highest probability first so the strongest Reach choices appear.
    #
    # Target:
    #     highest probability first.
    #
    # Safe:
    #     highest probability first.
    # ------------------------------------------------------------------------

    for tier in groups:

        groups[tier].sort(
            key=lambda candidate:
                (
                    get_probability(
                        candidate
                    )
                    if get_probability(
                        candidate
                    ) is not None
                    else -1.0
                ),

            reverse=True,
        )

    # ------------------------------------------------------------------------
    # Take only as many as the user requested from each actual category.
    # ------------------------------------------------------------------------

    selected_reach = groups[
        "Reach"
    ][:requested_reach]

    selected_target = groups[
        "Target"
    ][:requested_target]

    selected_safe = groups[
        "Safe"
    ][:requested_safe]

    # ------------------------------------------------------------------------
    # We now have true categories.
    #
    # Do NOT relabel candidates from another tier just to fill a gap.
    # ------------------------------------------------------------------------

    result = (

        selected_reach

        +

        selected_target

        +

        selected_safe

    )

    # ------------------------------------------------------------------------
    # If the requested total is smaller than the sum of category limits,
    # trim from the end while preserving Reach -> Target -> Safe display
    # order.
    # ------------------------------------------------------------------------

    result = result[
        :requested_total
    ]

    # ------------------------------------------------------------------------
    # Actual counts.
    # ------------------------------------------------------------------------

    actual = {

        "Reach":
            len(selected_reach),

        "Target":
            len(selected_target),

        "Safe":
            len(selected_safe),

    }

    # ------------------------------------------------------------------------
    # Shortfalls.
    #
    # A shortfall is completely legitimate:
    #
    # requested Reach = 6
    # available Reach = 2
    #
    # We show 2, not four fake Reach results.
    # ------------------------------------------------------------------------

    shortfalls = {

        "Reach":
            max(
                0,
                requested_reach
                -
                actual["Reach"],
            ),

        "Target":
            max(
                0,
                requested_target
                -
                actual["Target"],
            ),

        "Safe":
            max(
                0,
                requested_safe
                -
                actual["Safe"],
            ),

    }

    # ------------------------------------------------------------------------
    # Total actually displayed.
    # ------------------------------------------------------------------------

    actual_total = (
        len(result)
    )

    # ------------------------------------------------------------------------
    # Metadata returned to frontend.
    # ------------------------------------------------------------------------

    metadata = {

        "requested": {

            "Reach":
                requested_reach,

            "Target":
                requested_target,

            "Safe":
                requested_safe,

        },

        "actual": {

            "Reach":
                actual["Reach"],

            "Target":
                actual["Target"],

            "Safe":
                actual["Safe"],

            "Total":
                actual_total,

        },

        "shortfalls":
            shortfalls,

        "thresholds": {

            "Safe":
                f"{SAFE_MIN:.0f}-100%",

            "Target":
                f"{TARGET_MIN:.0f}-{SAFE_MIN - 0.1:.1f}%",

            "Reach":
                f"0-{TARGET_MIN - 0.1:.1f}%",

        },

    }

    return result, metadata