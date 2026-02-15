"""
Confidence Calculator for Enhanced Committee Conclusion.

This module implements the FR-029 confidence calculation formula:
- Unanimous (4-0 or 0-4) = High
- Split (3-1 or 1-3) = Medium
- Tie (2-2) = Low
- Contradictions reduce confidence by 1 level
"""

import re
from typing import List, Dict, Literal

ConfidenceLevel = Literal["High", "Medium", "Low"]


def calculate_confidence(
    room_outcomes: Dict[str, str], judge_rationales: List[str] = None
) -> ConfidenceLevel:
    """Calculate confidence level per FR-029 formula.

    Args:
        room_outcomes: Dictionary mapping room_id to winner (e.g., {"TPM_vs_CPO": "PRO"})
        judge_rationales: List of judge rationale texts for contradiction detection

    Returns:
        Confidence level: "High", "Medium", or "Low"

    Examples:
        >>> calculate_confidence({"TPM_vs_CPO": "PRO", "TPM_vs_CFO": "PRO", ...})
        "High"
        >>> calculate_confidence({"TPM_vs_CPO": "PRO", "TPM_vs_CFO": "CON", ...})
        "Medium"
    """
    if judge_rationales is None:
        judge_rationales = []

    # Count PRO and CON wins
    pro_wins = sum(1 for outcome in room_outcomes.values() if outcome == "PRO")
    con_wins = sum(1 for outcome in room_outcomes.values() if outcome == "CON")

    # Calculate base confidence
    base_confidence = _calculate_base_confidence(pro_wins, con_wins)

    # Check for contradictions in rationales
    has_contradictions = _detect_contradictions(judge_rationales)

    # Reduce confidence by 1 level if contradictions found
    final_confidence = _reduce_confidence(base_confidence, has_contradictions)

    return final_confidence


def _calculate_base_confidence(pro_wins: int, con_wins: int) -> ConfidenceLevel:
    """Calculate base confidence from PRO/CON win counts.

    Args:
        pro_wins: Number of rooms where PRO won
        con_wins: Number of rooms where CON won

    Returns:
        Base confidence level
    """
    total_rooms = pro_wins + con_wins

    # Handle edge cases
    if total_rooms == 0:
        return "Low"

    if total_rooms == 1:
        # Single room: use the outcome directly
        return "High" if pro_wins == 1 or con_wins == 1 else "Low"

    # FR-029 formula for multi-room debates
    if pro_wins == total_rooms or con_wins == total_rooms:
        # Unanimous decision (4-0 or 0-4)
        return "High"
    elif pro_wins == con_wins:
        # Tie decision (2-2)
        return "Low"
    else:
        # Split decision (3-1 or 1-3) - any non-unanimous, non-tie outcome
        return "Medium"


def _detect_contradictions(rationales: List[str]) -> bool:
    """Detect contradictions in judge rationales.

    Looks for:
    - Strong contradiction words: "contradicts", "inconsistent", "conflicting"
    - Multiple contrast words: "however", "but", "although", "yet" (2+ required)

    Args:
        rationales: List of judge rationale texts

    Returns:
        True if contradictions detected, False otherwise
    """
    if not rationales:
        return False

    # Combine all rationales into one text for analysis
    combined_text = " ".join(rationales).lower()

    # Strong contradiction indicators (immediate contradiction)
    strong_contradictions = ["contradicts", "inconsistent", "conflicting", "discrepancy"]
    has_strong_contradiction = any(
        word in combined_text for word in strong_contradictions
    )

    if has_strong_contradiction:
        return True

    # Contrast words (need 2+ to indicate contradiction)
    contrast_words = ["however", "but", "although", "yet", "nevertheless"]
    contrast_count = sum(combined_text.count(word) for word in contrast_words)

    return contrast_count >= 2


def _reduce_confidence(
    confidence: ConfidenceLevel, has_contradictions: bool
) -> ConfidenceLevel:
    """Reduce confidence by 1 level if contradictions found.

    Args:
        confidence: Current confidence level
        has_contradictions: Whether contradictions were detected

    Returns:
        Adjusted confidence level
    """
    if not has_contradictions:
        return confidence

    # Reduce by 1 level
    if confidence == "High":
        return "Medium"
    elif confidence == "Medium":
        return "Low"
    else:
        return "Low"  # Already at minimum
