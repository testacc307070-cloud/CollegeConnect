"""
RAG reasoning layer for CollegeConnect.

This module supports:
1. Cutoff-based grounded explanations.
2. State-rank-based grounded explanations.
3. Combined cutoff + rank grounded explanations.
4. Robust deterministic rule-based fallback when Gemini API is unconfigured or unavailable.
"""

import json
import logging
import os
from pathlib import Path

from dotenv import load_dotenv

logger = logging.getLogger("CollegeConnect.RAG")

# ---------------------------------------------------------
# Environment configuration
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

def get_gemini_config():
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip()
    if not model or model == "gemini-3.5-flash-lite":
        model = "gemini-2.5-flash"
    return api_key, model


def get_gemini_client():
    """
    Create a Gemini client using the API key stored in .env.
    """
    api_key, _ = get_gemini_config()
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not configured in .env")

    try:
        from google import genai
        return genai.Client(api_key=api_key)
    except Exception as exc:
        raise RuntimeError(f"Could not initialize Google GenAI client: {exc}")


# ---------------------------------------------------------
# Deterministic Fallback Generators (Zero Hallucination)
# ---------------------------------------------------------

def generate_fallback_cutoff_explanation(
    cutoff_mark: float,
    community: str,
    retrieved_results: list,
    district=None,
    branch_code=None,
    college_code=None,
) -> str:
    """
    Produce a grounded, deterministic analysis of historical TNEA cutoff evidence
    when Gemini API is unconfigured or unreachable.
    """
    if not retrieved_results:
        return (
            "### Summary:\n"
            f"No historical admissions data was found matching cutoff {cutoff_mark} for {community} quota.\n\n"
            "### Limitations:\n"
            "Try broadening your district or branch filters."
        )

    top_matches = retrieved_results[:5]
    lines = []

    lines.append("### Summary:")
    lines.append(
        f"Based on your aggregate cutoff mark of **{cutoff_mark:.2f}** under the **{community}** reservation category, "
        f"we evaluated {len(retrieved_results)} candidate college/branch options against official 2021–2025 TNEA allotment history."
    )
    if district:
        lines.append(f"Filtering applied for district: **{district}**.")
    if branch_code:
        lines.append(f"Filtering applied for branch: **{branch_code}**.")

    lines.append("\n### Historical Evidence:")
    for idx, c in enumerate(top_matches, start=1):
        c_name = c.get("college_name", f"College {c.get('college_code')}")
        b_name = c.get("branch_name", c.get("branch_code"))
        fit = c.get("historical_fit_score", 0)
        latest_cut = c.get("latest_cutoff")
        latest_yr = c.get("latest_year", 2025)
        cut_change = c.get("cutoff_change")

        diff_str = ""
        if latest_cut is not None:
            cushion = round(cutoff_mark - float(latest_cut), 2)
            cushion_sign = "+" if cushion >= 0 else ""
            diff_str = f" (Cushion: {cushion_sign}{cushion:.2f} marks vs {latest_yr} cutoff of {latest_cut})"

        trend_str = ""
        if cut_change is not None:
            trend_sign = "+" if cut_change > 0 else ""
            trend_str = f" | 5-Year Drift: {trend_sign}{cut_change:.2f}"

        lines.append(
            f"{idx}. **{c_name}** — *{b_name}*\n"
            f"   - Historical Match Rate: **{fit}%**{diff_str}{trend_str}"
        )

    lines.append("\n### How to Interpret:")
    lines.append(
        "- **Safe Options (≥80% match):** Your score comfortably exceeds recent closing cutoffs by +2.5 marks or more.\n"
        "- **Target Options (50%–79% match):** Your cutoff is competitive and falls within ±2.0 marks of historical averages.\n"
        "- **Reach Options (<50% match):** Ambitious options where past cutoffs were higher; recommended to include as aspirational choices in early DoTE rounds."
    )

    lines.append("\n### Limitations:")
    lines.append(
        "Historical cutoffs serve as empirical guidelines. Annual cutoff shifts are influenced by "
        "Class 12 board score distributions, total applicant counts, and seat matrix revisions for the current academic cycle."
    )

    return "\n".join(lines)


def generate_fallback_rank_explanation(
    state_rank: int,
    community: str,
    retrieved_results: list,
    district=None,
    branch_code=None,
    college_code=None,
) -> str:
    """
    Produce a grounded, deterministic analysis of historical TNEA state rank evidence
    when Gemini API is unconfigured or unreachable.
    """
    if not retrieved_results:
        return (
            "### Summary:\n"
            f"No historical closing rank data was found matching state rank {state_rank} for {community} quota.\n\n"
            "### Limitations:\n"
            "Try broadening your district or branch filters."
        )

    top_matches = retrieved_results[:5]
    lines = []

    lines.append("### Summary:")
    lines.append(
        f"With an overall TNEA State Rank of **{state_rank:,}** under the **{community}** reservation category, "
        f"a lower rank number represents higher admission priority. We evaluated {len(retrieved_results)} options "
        f"against historical closing ranks across 2021–2025."
    )

    lines.append("\n### Historical Evidence:")
    for idx, c in enumerate(top_matches, start=1):
        c_name = c.get("college_name", f"College {c.get('college_code')}")
        b_name = c.get("branch_name", c.get("branch_code"))
        fit = c.get("historical_fit_score", 0)
        latest_rank = c.get("latest_closing_rank")
        latest_yr = c.get("latest_year", 2025)

        rank_cushion = ""
        if latest_rank is not None:
            cushion = int(latest_rank) - state_rank
            if cushion >= 0:
                rank_cushion = f" (Ahead of {latest_yr} closing rank {latest_rank:,} by {cushion:,} positions)"
            else:
                rank_cushion = f" (Behind {latest_yr} closing rank {latest_rank:,} by {abs(cushion):,} positions)"

        lines.append(
            f"{idx}. **{c_name}** — *{b_name}*\n"
            f"   - Historical Match Rate: **{fit}%**{rank_cushion}"
        )

    lines.append("\n### How to Interpret:")
    lines.append(
        "- A candidate whose state rank is numerically lower than past closing ranks has a high historical admission probability.\n"
        "- Programs where your rank is slightly behind recent closing bounds can still be chosen as aspirational 'Reach' options."
    )

    lines.append("\n### Limitations:")
    lines.append(
        "Closing ranks fluctuate based on the community-wise applicant rank distribution and student preference trends across branches."
    )

    return "\n".join(lines)


# ---------------------------------------------------------
# Cutoff-based explanation (Gemini with Fallback)
# ---------------------------------------------------------

def generate_grounded_explanation(
    cutoff_mark,
    community,
    retrieved_results,
    district=None,
    branch_code=None,
    college_code=None,
):
    """
    Generate a grounded explanation from cutoff-based historical evidence.
    Attempts Google Gemini first; transparently falls back to deterministic rule-based output.
    Returns (explanation_text, model_name).
    """
    api_key, model_name = get_gemini_config()

    if not api_key:
        logger.info("GEMINI_API_KEY not configured. Serving deterministic rule-based explanation.")
        explanation = generate_fallback_cutoff_explanation(
            cutoff_mark, community, retrieved_results, district, branch_code, college_code
        )
        return explanation, "Deterministic Scorer (Offline Fallback)"

    try:
        client = get_gemini_client()
        evidence = retrieved_results[:12]
        evidence_json = json.dumps(evidence, indent=2, ensure_ascii=False)

        prompt = f"""You are the reasoning assistant for CollegeConnect, a Tamil Nadu Engineering Admissions (TNEA) prediction assistant.

Use ONLY the historical evidence supplied below. Do not invent any cutoff marks, colleges, or ranks.

Student aggregate cutoff: {cutoff_mark}
Community: {community}
District: {district if district else "All districts"}
Branch: {branch_code if branch_code else "All branches"}
College Code: {college_code if college_code else "All colleges"}

Retrieved historical evidence:
{evidence_json}

Instructions:
1. Use only the supplied evidence.
2. Do not claim guaranteed admission.
3. Compare student cutoff with historical values and trends.
4. Keep the response concise, informative, and formatted with these exact markdown headings:

### Summary:
### Historical Evidence:
### How to Interpret:
### Limitations:
"""
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
        )

        if response and response.text:
            return response.text, f"Google Gemini ({model_name})"
        raise RuntimeError("Empty response from Gemini")

    except Exception as exc:
        logger.warning(f"Gemini API invocation failed ({exc}). Using deterministic fallback.")
        explanation = generate_fallback_cutoff_explanation(
            cutoff_mark, community, retrieved_results, district, branch_code, college_code
        )
        return explanation, "Deterministic Scorer (Gemini Fallback)"


# ---------------------------------------------------------
# State-rank explanation (Gemini with Fallback)
# ---------------------------------------------------------

def generate_rank_grounded_explanation(
    state_rank,
    community,
    retrieved_results,
    district=None,
    branch_code=None,
    college_code=None,
):
    """
    Generate a grounded explanation from state-rank historical evidence.
    Attempts Google Gemini first; transparently falls back to deterministic rule-based output.
    Returns (explanation_text, model_name).
    """
    api_key, model_name = get_gemini_config()

    if not api_key:
        logger.info("GEMINI_API_KEY not configured. Serving deterministic rule-based explanation.")
        explanation = generate_fallback_rank_explanation(
            state_rank, community, retrieved_results, district, branch_code, college_code
        )
        return explanation, "Deterministic Scorer (Offline Fallback)"

    try:
        client = get_gemini_client()
        evidence = retrieved_results[:12]
        evidence_json = json.dumps(evidence, indent=2, ensure_ascii=False)

        prompt = f"""You are the reasoning assistant for CollegeConnect, a Tamil Nadu Engineering Admissions (TNEA) prediction assistant.

Use ONLY the historical evidence supplied below. Do not invent any figures.

Student TNEA state rank: {state_rank}
Community: {community}
District: {district if district else "All districts"}
Branch: {branch_code if branch_code else "All branches"}
College Code: {college_code if college_code else "All colleges"}

Retrieved historical evidence:
{evidence_json}

Instructions:
1. Lower state rank is better.
2. Compare student rank against historical closing ranks.
3. Keep response concise, informative, and formatted with these exact markdown headings:

### Summary:
### Historical Evidence:
### How to Interpret:
### Limitations:
"""
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
        )

        if response and response.text:
            return response.text, f"Google Gemini ({model_name})"
        raise RuntimeError("Empty response from Gemini")

    except Exception as exc:
        logger.warning(f"Gemini API invocation failed ({exc}). Using deterministic fallback.")
        explanation = generate_fallback_rank_explanation(
            state_rank, community, retrieved_results, district, branch_code, college_code
        )
        return explanation, "Deterministic Scorer (Gemini Fallback)"


# ---------------------------------------------------------
# Combined explanation (Cutoff + Rank)
# ---------------------------------------------------------

def generate_combined_grounded_explanation(
    cutoff_mark,
    state_rank,
    community,
    retrieved_results,
    district=None,
    branch_code=None,
    college_code=None,
):
    """
    Generate a grounded explanation when both cutoff and rank are supplied.
    """
    if cutoff_mark is not None:
        return generate_grounded_explanation(
            cutoff_mark=cutoff_mark,
            community=community,
            retrieved_results=retrieved_results,
            district=district,
            branch_code=branch_code,
            college_code=college_code,
        )
    return generate_rank_grounded_explanation(
        state_rank=state_rank,
        community=community,
        retrieved_results=retrieved_results,
        district=district,
        branch_code=branch_code,
        college_code=college_code,
    )