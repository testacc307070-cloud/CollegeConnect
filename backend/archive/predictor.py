"""
Historical prediction foundation for CollegeConnect.

This module does NOT use machine learning yet.
It evaluates a student's cutoff mark or state rank
against historical admission records.
"""


def calculate_cutoff_fit(user_cutoff, historical_data):
    """
    Compare the student's cutoff mark against historical
    cutoff marks.

    A year is considered a historical match when:
        user_cutoff >= historical_cutoff

    Returns a dictionary containing the score and details.
    """

    valid_records = [
        record
        for record in historical_data
        if record.get("cutoff_mark") is not None
    ]

    if not valid_records:
        return {
            "score": None,
            "matched_years": 0,
            "available_years": 0,
            "details": [],
            "message": "No historical cutoff data available"
        }

    details = []
    matched_years = 0

    for record in valid_records:
        historical_cutoff = float(record["cutoff_mark"])
        year = record["year"]

        matched = user_cutoff >= historical_cutoff

        if matched:
            matched_years += 1

        details.append({
            "year": year,
            "historical_cutoff": historical_cutoff,
            "user_cutoff": float(user_cutoff),
            "difference": round(
                float(user_cutoff) - historical_cutoff,
                3
            ),
            "matched": matched
        })

    score = round(
        (matched_years / len(valid_records)) * 100,
        2
    )

    return {
        "score": score,
        "matched_years": matched_years,
        "available_years": len(valid_records),
        "details": details,
        "message": "Historical cutoff comparison completed"
    }


def calculate_rank_fit(user_rank, historical_data):
    """
    Compare the student's state rank against historical
    closing ranks.

    A year is considered a historical match when:
        user_rank <= historical_closing_rank

    A lower state rank is better because rank 1 is higher
    than rank 100, for example.
    """

    valid_records = [
        record
        for record in historical_data
        if record.get("closing_rank") is not None
    ]

    if not valid_records:
        return {
            "score": None,
            "matched_years": 0,
            "available_years": 0,
            "details": [],
            "message": "No historical closing-rank data available"
        }

    details = []
    matched_years = 0

    for record in valid_records:
        historical_rank = int(record["closing_rank"])
        year = record["year"]

        matched = user_rank <= historical_rank

        if matched:
            matched_years += 1

        details.append({
            "year": year,
            "historical_closing_rank": historical_rank,
            "user_rank": int(user_rank),
            "difference": historical_rank - int(user_rank),
            "matched": matched
        })

    score = round(
        (matched_years / len(valid_records)) * 100,
        2
    )

    return {
        "score": score,
        "matched_years": matched_years,
        "available_years": len(valid_records),
        "details": details,
        "message": "Historical rank comparison completed"
    }


def get_fit_label(score):
    """
    Convert a historical fit score into an explanatory label.

    These labels describe historical matching only.
    They are NOT admission probability categories.
    """

    if score is None:
        return "No historical evidence"

    if score == 100:
        return "Matched all available historical years"

    if score >= 80:
        return "Matched most historical years"

    if score >= 60:
        return "Mixed historical match"

    if score > 0:
        return "Matched some historical years"

    return "Did not match historical thresholds"


def generate_prediction(
    user_cutoff=None,
    user_rank=None,
    historical_data=None
):
    """
    Generate a historical-fit assessment.

    Either cutoff, rank, or both may be supplied.
    """

    if historical_data is None:
        historical_data = []

    result = {
        "input": {
            "cutoff_mark": user_cutoff,
            "state_rank": user_rank
        },
        "cutoff_analysis": None,
        "rank_analysis": None,
        "historical_fit_score": None,
        "historical_fit_label": "No historical evidence"
    }

    scores = []

    # ---------------------------------------------
    # Cutoff-based analysis
    # ---------------------------------------------

    if user_cutoff is not None:
        cutoff_result = calculate_cutoff_fit(
            float(user_cutoff),
            historical_data
        )

        result["cutoff_analysis"] = cutoff_result

        if cutoff_result["score"] is not None:
            scores.append(cutoff_result["score"])

    # ---------------------------------------------
    # Rank-based analysis
    # ---------------------------------------------

    if user_rank is not None:
        rank_result = calculate_rank_fit(
            int(user_rank),
            historical_data
        )

        result["rank_analysis"] = rank_result

        if rank_result["score"] is not None:
            scores.append(rank_result["score"])

    # ---------------------------------------------
    # Combined historical fit
    # ---------------------------------------------

    if scores:
        combined_score = round(
            sum(scores) / len(scores),
            2
        )

        result["historical_fit_score"] = combined_score
        result["historical_fit_label"] = get_fit_label(
            combined_score
        )

    return result