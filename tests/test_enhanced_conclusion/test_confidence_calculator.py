"""
Unit tests for Confidence Calculator.

Tests verify:
- FR-029 confidence calculation formula
- Room outcome counting (PRO vs CON wins)
- Contradiction detection in judge rationales
- Confidence level reduction with contradictions
- Edge cases (0 rooms, 1 room, empty outcomes)
"""

import pytest

from src.utils.confidence_calculator import (
    calculate_confidence,
    _calculate_base_confidence,
    _detect_contradictions,
    _reduce_confidence,
)


# ============================================================================
# Test Base Confidence Calculation (FR-029 Formula)
# ============================================================================


class TestBaseConfidenceCalculation:
    """Test base confidence calculation per FR-029 formula."""

    def test_unanimous_pro_victory_4_0(self):
        """Test unanimous PRO victory (4-0) = High."""
        outcomes = {
            "TPM_vs_CPO": "PRO",
            "TPM_vs_CFO": "PRO",
            "TPM_vs_CTO": "PRO",
            "TPM_vs_BDM": "PRO",
        }
        confidence = calculate_confidence(outcomes)
        assert confidence == "High"

    def test_unanimous_con_victory_0_4(self):
        """Test unanimous CON victory (0-4) = High."""
        outcomes = {
            "TPM_vs_CPO": "CON",
            "TPM_vs_CFO": "CON",
            "TPM_vs_CTO": "CON",
            "TPM_vs_BDM": "CON",
        }
        confidence = calculate_confidence(outcomes)
        assert confidence == "High"

    def test_split_decision_pro_wins_3_1(self):
        """Test split decision (3-1) = Medium."""
        outcomes = {
            "TPM_vs_CPO": "PRO",
            "TPM_vs_CFO": "CON",
            "TPM_vs_CTO": "PRO",
            "TPM_vs_BDM": "PRO",
        }
        confidence = calculate_confidence(outcomes)
        assert confidence == "Medium"

    def test_split_decision_con_wins_1_3(self):
        """Test split decision (1-3) = Medium."""
        outcomes = {
            "TPM_vs_CPO": "CON",
            "TPM_vs_CFO": "CON",
            "TPM_vs_CTO": "CON",
            "TPM_vs_BDM": "PRO",
        }
        confidence = calculate_confidence(outcomes)
        assert confidence == "Medium"

    def test_tie_decision_2_2(self):
        """Test tie decision (2-2) = Low."""
        outcomes = {
            "TPM_vs_CPO": "PRO",
            "TPM_vs_CFO": "CON",
            "TPM_vs_CTO": "CON",
            "TPM_vs_BDM": "PRO",
        }
        confidence = calculate_confidence(outcomes)
        assert confidence == "Low"


# ============================================================================
# Test Edge Cases
# ============================================================================


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_outcomes(self):
        """Test empty outcomes returns Low."""
        confidence = calculate_confidence({})
        assert confidence == "Low"

    def test_single_room_pro_wins(self):
        """Test single room with PRO winner = High."""
        outcomes = {"TPM_vs_CPO": "PRO"}
        confidence = calculate_confidence(outcomes)
        assert confidence == "High"

    def test_single_room_con_wins(self):
        """Test single room with CON winner = High."""
        outcomes = {"TPM_vs_CFO": "CON"}
        confidence = calculate_confidence(outcomes)
        assert confidence == "High"

    def test_three_rooms_unanimous(self):
        """Test 3 rooms unanimous = High."""
        outcomes = {"TPM_vs_CPO": "PRO", "TPM_vs_CFO": "PRO", "TPM_vs_CTO": "PRO"}
        confidence = calculate_confidence(outcomes)
        assert confidence == "High"

    def test_three_rooms_split(self):
        """Test 3 rooms split (2-1) = Medium."""
        outcomes = {"TPM_vs_CPO": "PRO", "TPM_vs_CFO": "CON", "TPM_vs_CTO": "PRO"}
        confidence = calculate_confidence(outcomes)
        assert confidence == "Medium"

    def test_unclear_winner_in_room(self):
        """Test room with unclear winner (not PRO or CON)."""
        outcomes = {
            "TPM_vs_CPO": "PRO",
            "TPM_vs_CFO": "UNCLEAR",
            "TPM_vs_CTO": "PRO",
            "TPM_vs_BDM": "PRO",
        }
        # UNCLEAR doesn't count as win, so this is 3-0 = High
        confidence = calculate_confidence(outcomes)
        assert confidence == "High"


# ============================================================================
# Test Contradiction Detection
# ============================================================================


class TestContradictionDetection:
    """Test contradiction detection in judge rationales."""

    def test_no_contradictions(self):
        """Test rationales with no contradictions."""
        rationales = [
            "The judge found strong arguments on both sides.",
            "Consensus was reached on key points.",
        ]
        has_contradictions = _detect_contradictions(rationales)
        assert has_contradictions is False

    def test_strong_contradiction_contradicts(self):
        """Test strong contradiction word 'contradicts'."""
        rationales = [
            "The judge's analysis contradicts the earlier findings.",
            "This creates uncertainty in the conclusion.",
        ]
        has_contradictions = _detect_contradictions(rationales)
        assert has_contradictions is True

    def test_strong_contradiction_inconsistent(self):
        """Test strong contradiction word 'inconsistent'."""
        rationales = [
            "The analysis was inconsistent with previous findings.",
            "This discrepancy raises concerns.",
        ]
        has_contradictions = _detect_contradictions(rationales)
        assert has_contradictions is True

    def test_strong_contradiction_conflicting(self):
        """Test strong contradiction word 'conflicting'."""
        rationales = [
            "Conflicting opinions were expressed by the judges.",
            "The evidence is unclear.",
        ]
        has_contradictions = _detect_contradictions(rationales)
        assert has_contradictions is True

    def test_multiple_contrast_words_triggers_contradiction(self):
        """Test multiple contrast words trigger contradiction."""
        rationales = [
            "The arguments were strong but the concerns were valid.",
            "However, the financial model needs revision.",
        ]
        has_contradictions = _detect_contradictions(rationales)
        assert has_contradictions is True  # "but" + "however" = 2

    def test_single_contrast_word_no_contradiction(self):
        """Test single contrast word doesn't trigger contradiction."""
        rationales = ["The proposal has merits but needs refinement."]
        has_contradictions = _detect_contradictions(rationales)
        assert has_contradictions is False  # Only 1 contrast word

    def test_empty_rationales(self):
        """Test empty rationales list."""
        has_contradictions = _detect_contradictions([])
        assert has_contradictions is False

    def test_none_rationales(self):
        """Test None rationales (handled in calculate_confidence)."""
        confidence = calculate_confidence({"TPM_vs_CPO": "PRO"}, None)
        assert confidence == "High"

    def test_case_insensitive_detection(self):
        """Test case-insensitive contradiction detection."""
        rationales = [
            "The analysis CONTRADICTS previous findings.",
            "However, concerns remain.",
        ]
        has_contradictions = _detect_contradictions(rationales)
        assert has_contradictions is True


# ============================================================================
# Test Confidence Level Reduction
# ============================================================================


class TestConfidenceLevelReduction:
    """Test confidence level reduction with contradictions."""

    def test_high_reduced_to_medium_with_contradictions(self):
        """Test High reduced to Medium when contradictions found."""
        outcomes = {
            "TPM_vs_CPO": "PRO",
            "TPM_vs_CFO": "PRO",
            "TPM_vs_CTO": "PRO",
            "TPM_vs_BDM": "PRO",
        }
        rationales = [
            "The arguments were strong but the concerns were valid.",
            "However, significant issues remain unresolved.",
        ]
        confidence = calculate_confidence(outcomes, rationales)
        assert confidence == "Medium"  # High reduced to Medium

    def test_medium_reduced_to_low_with_contradictions(self):
        """Test Medium reduced to Low when contradictions found."""
        outcomes = {
            "TPM_vs_CPO": "PRO",
            "TPM_vs_CFO": "CON",
            "TPM_vs_CTO": "PRO",
            "TPM_vs_BDM": "PRO",
        }
        rationales = [
            "The proposal has merit but needs work.",
            "However, the risks are significant.",
        ]
        confidence = calculate_confidence(outcomes, rationales)
        assert confidence == "Low"  # Medium reduced to Low

    def test_low_stays_low_with_contradictions(self):
        """Test Low stays Low (already at minimum)."""
        outcomes = {
            "TPM_vs_CPO": "PRO",
            "TPM_vs_CFO": "CON",
            "TPM_vs_CTO": "CON",
            "TPM_vs_BDM": "PRO",
        }
        rationales = ["Conflicting views were expressed."]
        confidence = calculate_confidence(outcomes, rationales)
        assert confidence == "Low"  # Already at minimum

    def test_no_reduction_without_contradictions(self):
        """Test no reduction when no contradictions found."""
        outcomes = {
            "TPM_vs_CPO": "PRO",
            "TPM_vs_CFO": "PRO",
            "TPM_vs_CTO": "PRO",
            "TPM_vs_BDM": "PRO",
        }
        rationales = ["The judge found strong arguments for PRO."]
        confidence = calculate_confidence(outcomes, rationales)
        assert confidence == "High"  # No reduction


# ============================================================================
# Test _reduce_confidence Helper
# ============================================================================


class TestReduceConfidenceHelper:
    """Test _reduce_confidence helper function."""

    def test_reduce_high_to_medium(self):
        """Test reducing High to Medium."""
        result = _reduce_confidence("High", has_contradictions=True)
        assert result == "Medium"

    def test_reduce_medium_to_low(self):
        """Test reducing Medium to Low."""
        result = _reduce_confidence("Medium", has_contradictions=True)
        assert result == "Low"

    def test_reduce_low_stays_low(self):
        """Test reducing Low stays Low (minimum)."""
        result = _reduce_confidence("Low", has_contradictions=True)
        assert result == "Low"

    def test_no_reduction_when_false(self):
        """Test no reduction when has_contradictions is False."""
        assert _reduce_confidence("High", False) == "High"
        assert _reduce_confidence("Medium", False) == "Medium"
        assert _reduce_confidence("Low", False) == "Low"


# ============================================================================
# Test _calculate_base_confidence Helper
# ============================================================================


class TestCalculateBaseConfidenceHelper:
    """Test _calculate_base_confidence helper function."""

    def test_unanimous_pro(self):
        """Test unanimous PRO returns High."""
        result = _calculate_base_confidence(4, 0)
        assert result == "High"

    def test_unanimous_con(self):
        """Test unanimous CON returns High."""
        result = _calculate_base_confidence(0, 4)
        assert result == "High"

    def test_split_pro(self):
        """Test split PRO returns Medium."""
        result = _calculate_base_confidence(3, 1)
        assert result == "Medium"

    def test_split_con(self):
        """Test split CON returns Medium."""
        result = _calculate_base_confidence(1, 3)
        assert result == "Medium"

    def test_tie(self):
        """Test tie returns Low."""
        result = _calculate_base_confidence(2, 2)
        assert result == "Low"

    def test_zero_rooms(self):
        """Test zero rooms returns Low."""
        result = _calculate_base_confidence(0, 0)
        assert result == "Low"

    def test_single_room_pro(self):
        """Test single room PRO returns High."""
        result = _calculate_base_confidence(1, 0)
        assert result == "High"

    def test_single_room_con(self):
        """Test single room CON returns High."""
        result = _calculate_base_confidence(0, 1)
        assert result == "High"


# ============================================================================
# Test Integration Scenarios
# ============================================================================


class TestIntegrationScenarios:
    """Test realistic integration scenarios."""

    def test_complete_unanimous_scenario(self):
        """Test complete unanimous scenario with rationales."""
        outcomes = {
            "TPM_vs_CPO": "PRO",
            "TPM_vs_CFO": "PRO",
            "TPM_vs_CTO": "PRO",
            "TPM_vs_BDM": "PRO",
        }
        rationales = [
            "The judge found PRO's technical arguments compelling.",
            "Financial concerns were addressed adequately.",
            "Market opportunity was clearly demonstrated.",
            "Competitive advantage was established.",
        ]
        confidence = calculate_confidence(outcomes, rationales)
        assert confidence == "High"

    def test_complete_split_scenario_with_contradictions(self):
        """Test complete split scenario with contradictions."""
        outcomes = {
            "TPM_vs_CPO": "PRO",
            "TPM_vs_CFO": "CON",
            "TPM_vs_CTO": "PRO",
            "TPM_vs_BDM": "PRO",
        }
        rationales = [
            "The technical case was strong but financial concerns are significant.",
            "However, the ROI projection remains optimistic.",
        ]
        confidence = calculate_confidence(outcomes, rationales)
        assert confidence == "Low"  # Medium reduced to Low

    def test_complete_tie_scenario(self):
        """Test complete tie scenario."""
        outcomes = {
            "TPM_vs_CPO": "PRO",
            "TPM_vs_CFO": "CON",
            "TPM_vs_CTO": "CON",
            "TPM_vs_BDM": "PRO",
        }
        rationales = ["The committee reached a split decision."]
        confidence = calculate_confidence(outcomes, rationales)
        assert confidence == "Low"
