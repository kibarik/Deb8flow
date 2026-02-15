"""Unit tests for conclusion_types module.

Tests TypedDict definitions, enums, and validation functions.
"""

import unittest
from typing import get_type_hints

from src.types.conclusion_types import (
    ConclusionData,
    VerdictSummary,
    QAPair,
    TPMAnalysis,
    TPMWeakness,
    Recommendation,
    ConclusionMetadata,
    DebateType,
    WeaknessCategory,
    SeverityLevel,
    PriorityLevel,
    validate_qa_summary_count,
    validate_winner_role,
    validate_severity,
)


class TestEnums(unittest.TestCase):
    """Test enum definitions."""

    def test_debate_type_enum(self):
        """Test DebateType enum values."""
        self.assertEqual(DebateType.STANDARD.value, "standard")
        self.assertEqual(DebateType.DOCUMENT.value, "document")
        self.assertEqual(DebateType.COMMITTEE.value, "committee")

    def test_weakness_category_enum(self):
        """Test WeaknessCategory enum values."""
        self.assertEqual(WeaknessCategory.UNJUSTIFIED_ASSUMPTION.value, "unjustified_assumption")
        self.assertEqual(WeaknessCategory.UNCOVERED_RISK.value, "uncovered_risk")
        self.assertEqual(WeaknessCategory.WEAK_METRICS.value, "weak_metrics")
        self.assertEqual(WeaknessCategory.MISSING_EVIDENCE.value, "missing_evidence")
        self.assertEqual(WeaknessCategory.LOGICAL_FALLACY.value, "logical_fallacy")
        self.assertEqual(WeaknessCategory.UNCLEAR_VALUE_PROP.value, "unclear_value_prop")
        self.assertEqual(WeaknessCategory.INFEASIBLE_TIMELINE.value, "infeasible_timeline")
        self.assertEqual(WeaknessCategory.SELF_IDENTIFIED.value, "self_identified")

    def test_severity_level_enum(self):
        """Test SeverityLevel enum values."""
        self.assertEqual(SeverityLevel.HIGH.value, "high")
        self.assertEqual(SeverityLevel.MEDIUM.value, "medium")
        self.assertEqual(SeverityLevel.LOW.value, "low")

    def test_priority_level_enum(self):
        """Test PriorityLevel enum values."""
        self.assertEqual(PriorityLevel.HIGH.value, "high")
        self.assertEqual(PriorityLevel.MEDIUM.value, "medium")
        self.assertEqual(PriorityLevel.LOW.value, "low")

    def test_enums_are_str_subclasses(self):
        """Test that all enums are str subclasses for JSON compatibility."""
        self.assertIsInstance(DebateType.STANDARD, str)
        self.assertIsInstance(WeaknessCategory.UNJUSTIFIED_ASSUMPTION, str)
        self.assertIsInstance(SeverityLevel.HIGH, str)
        self.assertIsInstance(PriorityLevel.HIGH, str)


class TestVerdictSummary(unittest.TestCase):
    """Test VerdictSummary TypedDict."""

    def test_verdict_summary_type_hints(self):
        """Test that VerdictSummary has correct type hints."""
        hints = get_type_hints(VerdictSummary, include_extras=True)
        self.assertIn("winner", hints)
        self.assertIn("winner_position", hints)
        self.assertIn("justification", hints)
        self.assertIn("confidence", hints)

    def test_verdict_summary_instantiation(self):
        """Test that VerdictSummary can be instantiated."""
        verdict: VerdictSummary = {
            "winner": "TPM",
            "winner_position": "PRO",
            "justification": "TPM demonstrated stronger technical feasibility.",
            "confidence": 0.85,
        }
        self.assertEqual(verdict["winner"], "TPM")
        self.assertEqual(verdict["winner_position"], "PRO")
        self.assertEqual(verdict["confidence"], 0.85)

    def test_verdict_summary_optional_confidence(self):
        """Test that confidence is optional."""
        verdict: VerdictSummary = {
            "winner": "PRO",
            "winner_position": "PRO",
            "justification": "PRO position was more convincing.",
        }
        self.assertNotIn("confidence", verdict)


class TestQAPair(unittest.TestCase):
    """Test QAPair TypedDict."""

    def test_qa_pair_type_hints(self):
        """Test that QAPair has correct type hints."""
        hints = get_type_hints(QAPair, include_extras=True)
        self.assertIn("question", hints)
        self.assertIn("answer", hints)
        self.assertIn("stage", hints)
        self.assertIn("speaker", hints)
        self.assertIn("validated", hints)
        self.assertIn("priority", hints)

    def test_qa_pair_instantiation(self):
        """Test that QAPair can be instantiated."""
        qa: QAPair = {
            "question": "What is the timeline for implementation?",
            "answer": "The implementation can be completed in 6 months.",
            "stage": "opening",
            "speaker": "TPM",
            "validated": True,
            "priority": 3,
        }
        self.assertEqual(qa["question"], "What is the timeline for implementation?")
        self.assertEqual(qa["stage"], "opening")
        self.assertEqual(qa["priority"], 3)
        self.assertTrue(qa["validated"])


class TestTPMWeakness(unittest.TestCase):
    """Test TPMWeakness TypedDict."""

    def test_tpm_weakness_type_hints(self):
        """Test that TPMWeakness has correct type hints."""
        hints = get_type_hints(TPMWeakness, include_extras=True)
        self.assertIn("category", hints)
        self.assertIn("description", hints)
        self.assertIn("severity", hints)
        self.assertIn("source", hints)
        self.assertIn("context", hints)

    def test_tpm_weakness_instantiation(self):
        """Test that TPMWeakness can be instantiated."""
        weakness: TPMWeakness = {
            "category": "unjustified_assumption",
            "description": "Assumes development team can double velocity",
            "severity": "high",
            "source": "CPO",
            "context": "No historical data supports this claim",
        }
        self.assertEqual(weakness["category"], "unjustified_assumption")
        self.assertEqual(weakness["severity"], "high")
        self.assertEqual(weakness["source"], "CPO")

    def test_tpm_weakness_optional_context(self):
        """Test that context is optional."""
        weakness: TPMWeakness = {
            "category": "uncovered_risk",
            "description": "Missing risk analysis for market changes",
            "severity": "medium",
            "source": "CFO",
        }
        self.assertNotIn("context", weakness)


class TestTPMAnalysis(unittest.TestCase):
    """Test TPMAnalysis TypedDict."""

    def test_tpm_analysis_type_hints(self):
        """Test that TPMAnalysis has correct type hints."""
        hints = get_type_hints(TPMAnalysis, include_extras=True)
        self.assertIn("position_summary", hints)
        self.assertIn("weaknesses", hints)
        self.assertIn("recommended_improvements", hints)
        self.assertIn("victory_assessment", hints)

    def test_tpm_analysis_instantiation(self):
        """Test that TPMAnalysis can be instantiated."""
        analysis: TPMAnalysis = {
            "position_summary": "TPM argues for 6-month timeline with $100K budget.",
            "weaknesses": [],
            "recommended_improvements": ["Add historical velocity data"],
            "victory_assessment": "unclear",
        }
        self.assertEqual(analysis["victory_assessment"], "unclear")
        self.assertEqual(len(analysis["recommended_improvements"]), 1)


class TestRecommendation(unittest.TestCase):
    """Test Recommendation TypedDict."""

    def test_recommendation_type_hints(self):
        """Test that Recommendation has correct type hints."""
        hints = get_type_hints(Recommendation, include_extras=True)
        self.assertIn("agent_role", hints)
        self.assertIn("text", hints)
        self.assertIn("priority", hints)
        self.assertIn("category", hints)
        self.assertIn("actionable", hints)

    def test_recommendation_instantiation(self):
        """Test that Recommendation can be instantiated."""
        rec: Recommendation = {
            "agent_role": "CPO",
            "text": "От CPO: Validate timeline with engineering team",
            "priority": "high",
            "category": "planning",
            "actionable": True,
        }
        self.assertEqual(rec["agent_role"], "CPO")
        self.assertTrue(rec["actionable"])
        self.assertEqual(rec["priority"], "high")

    def test_recommendation_optional_fields(self):
        """Test that priority and category are optional."""
        rec: Recommendation = {
            "agent_role": "TPM",
            "text": "From TPM: Add buffer to timeline estimates",
            "actionable": False,
        }
        self.assertNotIn("priority", rec)
        self.assertNotIn("category", rec)


class TestConclusionMetadata(unittest.TestCase):
    """Test ConclusionMetadata TypedDict."""

    def test_conclusion_metadata_type_hints(self):
        """Test that ConclusionMetadata has correct type hints."""
        hints = get_type_hints(ConclusionMetadata, include_extras=True)
        self.assertIn("debate_type", hints)
        self.assertIn("run_id", hints)
        self.assertIn("generated_at", hints)
        self.assertIn("source_file", hints)
        self.assertIn("total_recommendations", hints)
        self.assertIn("tpm_victory", hints)
        self.assertIn("completion_status", hints)
        self.assertIn("error_message", hints)

    def test_conclusion_metadata_instantiation(self):
        """Test that ConclusionMetadata can be instantiated."""
        metadata: ConclusionMetadata = {
            "debate_type": "committee",
            "run_id": "committee-20250215-123456",
            "generated_at": "2025-02-15T12:34:56Z",
            "source_file": "/path/to/final_report.md",
            "total_recommendations": 5,
            "tpm_victory": False,
            "completion_status": "success",
            "error_message": None,
        }
        self.assertEqual(metadata["debate_type"], "committee")
        self.assertFalse(metadata["tpm_victory"])
        self.assertEqual(metadata["total_recommendations"], 5)

    def test_conclusion_metadata_optional_fields(self):
        """Test that source_file and error_message are optional."""
        metadata: ConclusionMetadata = {
            "debate_type": "standard",
            "run_id": "standard-20250215-789012",
            "generated_at": "2025-02-15T12:34:56Z",
            "total_recommendations": 3,
            "tpm_victory": True,
            "completion_status": "success",
        }
        self.assertNotIn("source_file", metadata)
        self.assertNotIn("error_message", metadata)


class TestConclusionData(unittest.TestCase):
    """Test ConclusionData TypedDict."""

    def test_conclusion_data_type_hints(self):
        """Test that ConclusionData has correct type hints."""
        hints = get_type_hints(ConclusionData, include_extras=True)
        self.assertIn("debate_question", hints)
        self.assertIn("verdict", hints)
        self.assertIn("qa_summary", hints)
        self.assertIn("tpm_analysis", hints)
        self.assertIn("recommendations", hints)
        self.assertIn("metadata", hints)

    def test_conclusion_data_instantiation(self):
        """Test that ConclusionData can be instantiated with valid data."""
        verdict: VerdictSummary = {
            "winner": "TPM",
            "winner_position": "PRO",
            "justification": "TPM demonstrated stronger technical feasibility.",
            "confidence": 0.85,
        }
        qa: QAPair = {
            "question": "What is the timeline?",
            "answer": "6 months",
            "stage": "opening",
            "speaker": "TPM",
            "validated": True,
            "priority": 1,
        }
        analysis: TPMAnalysis = {
            "position_summary": "TPM position",
            "weaknesses": [],
            "recommended_improvements": [],
            "victory_assessment": "won",
        }
        metadata: ConclusionMetadata = {
            "debate_type": "committee",
            "run_id": "test-123",
            "generated_at": "2025-02-15T12:34:56Z",
            "total_recommendations": 0,
            "tpm_victory": True,
            "completion_status": "success",
        }

        conclusion: ConclusionData = {
            "debate_question": "Should we adopt AI?",
            "verdict": verdict,
            "qa_summary": [qa],
            "tpm_analysis": analysis,
            "recommendations": [],
            "metadata": metadata,
        }
        self.assertEqual(conclusion["debate_question"], "Should we adopt AI?")
        self.assertEqual(len(conclusion["qa_summary"]), 1)
        self.assertEqual(conclusion["verdict"]["winner"], "TPM")


class TestValidationFunctions(unittest.TestCase):
    """Test validation functions."""

    def test_validate_qa_summary_count_valid_range(self):
        """Test validate_qa_summary_count with valid range."""
        self.assertTrue(validate_qa_summary_count(3))
        self.assertTrue(validate_qa_summary_count(5))
        self.assertTrue(validate_qa_summary_count(10))

    def test_validate_qa_summary_count_invalid_range(self):
        """Test validate_qa_summary_count with invalid range."""
        self.assertFalse(validate_qa_summary_count(0))
        self.assertFalse(validate_qa_summary_count(2))
        self.assertFalse(validate_qa_summary_count(11))
        self.assertFalse(validate_qa_summary_count(100))

    def test_validate_winner_role_valid_roles(self):
        """Test validate_winner_role with valid roles."""
        self.assertTrue(validate_winner_role("TPM"))
        self.assertTrue(validate_winner_role("PRO"))
        self.assertTrue(validate_winner_role("CON"))
        self.assertTrue(validate_winner_role("CPO"))
        self.assertTrue(validate_winner_role("CFO"))
        self.assertTrue(validate_winner_role("CTO"))
        self.assertTrue(validate_winner_role("BDM"))
        self.assertTrue(validate_winner_role("No clear winner"))

    def test_validate_winner_role_invalid_roles(self):
        """Test validate_winner_role with invalid roles."""
        self.assertFalse(validate_winner_role("Invalid"))
        self.assertFalse(validate_winner_role(""))
        self.assertFalse(validate_winner_role("Judge"))
        self.assertFalse(validate_winner_role("Moderator"))

    def test_validate_severity_valid_values(self):
        """Test validate_severity with valid values."""
        self.assertTrue(validate_severity("high"))
        self.assertTrue(validate_severity("medium"))
        self.assertTrue(validate_severity("low"))

    def test_validate_severity_invalid_values(self):
        """Test validate_severity with invalid values."""
        self.assertFalse(validate_severity("critical"))
        self.assertFalse(validate_severity("urgent"))
        self.assertFalse(validate_severity(""))
        self.assertFalse(validate_severity("HIGH"))  # Case sensitive


class TestFixtures(unittest.TestCase):
    """Test using fixtures for complex data structures."""

    @staticmethod
    def _sample_verdict_summary() -> VerdictSummary:
        """Fixture: sample VerdictSummary."""
        return {
            "winner": "TPM",
            "winner_position": "PRO",
            "justification": "TPM demonstrated stronger technical feasibility.",
            "confidence": 0.85,
        }

    @staticmethod
    def _sample_qa_pair() -> QAPair:
        """Fixture: sample QAPair."""
        return {
            "question": "What is the timeline for implementation?",
            "answer": "The implementation can be completed in 6 months.",
            "stage": "opening",
            "speaker": "TPM",
            "validated": True,
            "priority": 3,
        }

    @staticmethod
    def _sample_tpm_weakness() -> TPMWeakness:
        """Fixture: sample TPMWeakness."""
        return {
            "category": "unjustified_assumption",
            "description": "Assumes development team can double velocity",
            "severity": "high",
            "source": "CPO",
            "context": "No historical data supports this claim",
        }

    @staticmethod
    def _sample_tpm_analysis() -> TPMAnalysis:
        """Fixture: sample TPMAnalysis."""
        return {
            "position_summary": "TPM argues for 6-month timeline with $100K budget.",
            "weaknesses": [],
            "recommended_improvements": ["Add historical velocity data"],
            "victory_assessment": "unclear",
        }

    @staticmethod
    def _sample_recommendation() -> Recommendation:
        """Fixture: sample Recommendation."""
        return {
            "agent_role": "CPO",
            "text": "От CPO: Validate timeline with engineering team",
            "priority": "high",
            "category": "planning",
            "actionable": True,
        }

    @staticmethod
    def _sample_metadata() -> ConclusionMetadata:
        """Fixture: sample ConclusionMetadata."""
        return {
            "debate_type": "committee",
            "run_id": "committee-20250215-123456",
            "generated_at": "2025-02-15T12:34:56Z",
            "source_file": "/path/to/final_report.md",
            "total_recommendations": 5,
            "tpm_victory": False,
            "completion_status": "success",
            "error_message": None,
        }

    def test_fixtures_produce_valid_data(self):
        """Test that all fixtures produce valid data structures."""
        verdict = self._sample_verdict_summary()
        qa = self._sample_qa_pair()
        weakness = self._sample_tpm_weakness()
        analysis = self._sample_tpm_analysis()
        rec = self._sample_recommendation()
        metadata = self._sample_metadata()

        # Verify all fixtures can be accessed
        self.assertEqual(verdict["winner"], "TPM")
        self.assertEqual(qa["stage"], "opening")
        self.assertEqual(weakness["severity"], "high")
        self.assertEqual(analysis["victory_assessment"], "unclear")
        self.assertEqual(rec["agent_role"], "CPO")
        self.assertEqual(metadata["debate_type"], "committee")


if __name__ == "__main__":
    unittest.main()
