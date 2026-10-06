"""
Direct test for the CollegeConnect RAG probability scoring module.

This test checks that Gemini returns:
    - candidate_id
    - estimated_probability
    - tier
    - reasoning

No confidence field is used.
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.scoring import generate_probability_scores


def main():
    # ------------------------------------------------------------------
    # Example student input
    # ------------------------------------------------------------------

    student_input = {
        "cutoff_mark": 195.0,
        "state_rank": None,
        "community": "BC",
        "district": "CHENNAI",
        "branch_code": "CS",
    }

    # ------------------------------------------------------------------
    # Example retrieved historical candidate
    # ------------------------------------------------------------------

    candidates = [
        {
            "candidate_id": "1450_CS",

            "college_code": 1450,

            "college_name": (
                "Loyola-ICAM College of Engineering and Technology "
                "(Autonomous), Loyola College Campus, Chennai-600034."
            ),

            "district": "CHENNAI",

            "branch_code": "CS",

            "branch_name": (
                "Computer Science and Engineering"
            ),

            "historical_records": [
                {
                    "year": 2021,
                    "cutoff_mark": 184.5,
                    "closing_rank": 16562,
                },
                {
                    "year": 2022,
                    "cutoff_mark": 185.0,
                    "closing_rank": 15200,
                },
                {
                    "year": 2023,
                    "cutoff_mark": 186.5,
                    "closing_rank": 13800,
                },
                {
                    "year": 2024,
                    "cutoff_mark": 190.5,
                    "closing_rank": 8200,
                },
                {
                    "year": 2025,
                    "cutoff_mark": 188.5,
                    "closing_rank": 6176,
                },
            ],
        }
    ]

    # ------------------------------------------------------------------
    # Generate RAG probability score
    # ------------------------------------------------------------------

    results = generate_probability_scores(
        student_input=student_input,
        candidates=candidates,
    )

    # ------------------------------------------------------------------
    # Display results
    # ------------------------------------------------------------------

    print()
    print("SCORING RESULT")
    print("=" * 60)

    if not results:
        print("No scoring result was returned.")
        return

    for result in results:

        print(
            f"Candidate: "
            f"{result.get('candidate_id', 'Unknown')}"
        )

        print(
            f"Probability: "
            f"{result.get('estimated_probability')}%"
        )

        print(
            f"Tier: "
            f"{result.get('tier', 'Unknown')}"
        )

        print(
            "Reasoning: "
            f"{result.get('probability_reasoning') or result.get('reasoning', 'No reasoning returned')}"
        )

        print("-" * 60)

    print()
    print("TEST COMPLETED SUCCESSFULLY")
    print()
    

if __name__ == "__main__":
    main()