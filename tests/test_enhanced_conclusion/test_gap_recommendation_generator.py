"""
Unit tests for GapRecommendationGenerator.

Tests verify:
- Critical gap identification from cross-role weaknesses
- Gap severity ranking by sources, strength, and judge emphasis
- Recommendation generation with problem→action→metric format
- Max 5 gaps and max 5 high-priority recommendations enforcement
- Evidence traceability for all recommendations
"""

import json
import pytest
from unittest.mock import Mock, patch, MagicMock

from src.analyzers.gap_recommendation_generator import GapRecommendationGenerator
from src.types.enhanced_conclusion_types import (
    IntermediateConclusionSchema,
    Verdict,
    RoleAnalysis,
    Weakness,
    EvidenceReference,
    CriticalGap,
    Recommendation,
)


# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
def gap_generator():
    """Create GapRecommendationGenerator instance."""
    return GapRecommendationGenerator(llm_config=None)


@pytest.fixture
def sample_intermediate_schema():
    """Sample intermediate conclusion schema."""
    # Create a valid Verdict with 120-150 words
    answer_words = " ".join(["word"] * 130)
    verdict = Verdict(
        answer=answer_words,
        confidence="Medium",
        rationale="Split decision with 3-1 outcome. Financial concerns were significant and require additional planning.",
        room_outcomes="PRO won 3/4 rooms"
    )

    role_analyses = [
        RoleAnalysis(
            role_name="CFO",
            strengths=[],
            weaknesses=[
                Weakness(
                    description="Financial model lacks conservative scenarios",
                    evidence=EvidenceReference(
                        room_id="TPM_vs_CFO",
                        speaker_role="CFO",
                        turn_index=2,
                        quote="The financial model is overly optimistic with no downside analysis."
                    )
                ),
                Weakness(
                    description="Insufficient detail on implementation costs",
                    evidence=EvidenceReference(
                        room_id="TPM_vs_CFO",
                        speaker_role="CFO",
                        turn_index=3,
                        quote="Implementation costs were not adequately detailed."
                    )
                )
            ]
        ),
        RoleAnalysis(
            role_name="CTO",
            strengths=[],
            weaknesses=[
                Weakness(
                    description="Technical architecture not adequately defined",
                    evidence=EvidenceReference(
                        room_id="TPM_vs_CTO",
                        speaker_role="CTO",
                        turn_index=4,
                        quote="The proposal lacks detailed technical architecture."
                    )
                ),
                Weakness(
                    description="Implementation timeline unrealistic",
                    evidence=EvidenceReference(
                        room_id="TPM_vs_CTO",
                        speaker_role="CTO",
                        turn_index=5,
                        quote="The proposed timeline does not account for technical complexity."
                    )
                )
            ]
        ),
        RoleAnalysis(
            role_name="CPO",
            strengths=[],
            weaknesses=[
                Weakness(
                    description="Integration challenges with existing systems",
                    evidence=EvidenceReference(
                        room_id="TPM_vs_CPO",
                        speaker_role="CPO",
                        turn_index=2,
                        quote="Integration with current systems was not adequately addressed."
                    )
                )
            ]
        )
    ]

    return IntermediateConclusionSchema(verdict=verdict, role_analyses=role_analyses)


@pytest.fixture
def sample_gaps_response():
    """Sample LLM response for gaps."""
    return json.dumps({
        "gaps": [
            {
                "title": "Incomplete Financial Analysis",
                "severity": "High",
                "description": "The financial model lacks conservative scenarios and detailed implementation costs, making it difficult to assess true ROI and risk.",
                "sources": ["CFO"],
                "evidence": [
                    {
                        "room_id": "TPM_vs_CFO",
                        "speaker_role": "CFO",
                        "turn_index": 2,
                        "quote": "The financial model is overly optimistic with no downside analysis."
                    }
                ]
            },
            {
                "title": "Technical Architecture Undefined",
                "severity": "High",
                "description": "The proposal lacks detailed technical architecture, including system components, data flow, and integration points.",
                "sources": ["CTO"],
                "evidence": [
                    {
                        "room_id": "TPM_vs_CTO",
                        "speaker_role": "CTO",
                        "turn_index": 4,
                        "quote": "The proposal lacks detailed technical architecture."
                    }
                ]
            },
            {
                "title": "Implementation Planning Gaps",
                "severity": "Medium",
                "description": "Timeline and implementation costs need more detail to be realistic.",
                "sources": ["CFO", "CTO"],
                "evidence": [
                    {
                        "room_id": "TPM_vs_CFO",
                        "speaker_role": "CFO",
                        "turn_index": 3,
                        "quote": "Implementation costs were not adequately detailed."
                    }
                ]
            }
        ]
    })


@pytest.fixture
def sample_recommendations_response():
    """Sample LLM response for recommendations."""
    return json.dumps({
        "recommendations": [
            {
                "priority": "High",
                "problem": "The PRD lacks a comprehensive financial analysis with conservative scenarios",
                "action": "Add a detailed 'Financial Analysis' section to the PRD with best-case, expected-case, and worst-case ROI scenarios",
                "metric": "PRD includes 3 financial scenarios with specific metrics for each (CAC, LTV, payback period)",
                "source_evidence": {
                    "room_id": "TPM_vs_CFO",
                    "speaker_role": "CFO",
                    "turn_index": 2,
                    "quote": "The financial model is overly optimistic with no downside analysis."
                }
            },
            {
                "priority": "High",
                "problem": "Technical architecture is not defined, making implementation impossible to plan",
                "action": "Create comprehensive technical architecture documentation including system diagrams, data flow, and API specifications",
                "metric": "Architecture document includes component diagram, data flow diagram, and API specification document",
                "source_evidence": {
                    "room_id": "TPM_vs_CTO",
                    "speaker_role": "CTO",
                    "turn_index": 4,
                    "quote": "The proposal lacks detailed technical architecture."
                }
            },
            {
                "priority": "Medium",
                "problem": "Implementation timeline appears optimistic given technical complexity",
                "action": "Revise implementation timeline with buffer for unexpected technical challenges",
                "metric": "Timeline includes 20% buffer for technical risks and phased rollout plan",
                "source_evidence": {
                    "room_id": "TPM_vs_CTO",
                    "speaker_role": "CTO",
                    "turn_index": 5,
                    "quote": "The proposed timeline does not account for technical complexity."
                }
            }
        ]
    })


# ============================================================================
# Test Gap Identification
# ============================================================================


class TestGapIdentification:
    """Test critical gap identification from role analyses."""

    def test_identify_gaps_from_weaknesses(
        self, gap_generator, sample_intermediate_schema, sample_gaps_response
    ):
        """Test identifying gaps from role analyses."""
        with patch.object(gap_generator, "_extract_gaps_with_llm", return_value=json.loads(sample_gaps_response)["gaps"]):
            gaps = gap_generator._identify_critical_gaps(sample_intermediate_schema)

        assert len(gaps) == 3
        assert all(isinstance(gap, CriticalGap) for gap in gaps)

    def test_empty_role_analyses_returns_empty_gaps(self, gap_generator):
        """Test role analyses with no weaknesses returns empty gaps."""
        # Create a valid Verdict with proper word count
        answer_words = " ".join(["word"] * 130)
        verdict = Verdict(
            answer=answer_words,
            confidence="High",
            rationale="This is a valid rationale that meets the minimum length requirement of fifty characters for testing purposes.",
            room_outcomes="Test outcomes"
        )
        # Create schema with one role analysis but no weaknesses
        schema = IntermediateConclusionSchema(
            verdict=verdict,
            role_analyses=[
                RoleAnalysis(role_name="TPM", strengths=[], weaknesses=[])
            ]
        )

        gaps = gap_generator._identify_critical_gaps(schema)
        assert len(gaps) == 0

    def test_role_analyses_with_no_weaknesses(self, gap_generator):
        """Test role analyses with no weaknesses."""
        # Create a valid Verdict with proper word count
        answer_words = " ".join(["word"] * 130)
        verdict = Verdict(
            answer=answer_words,
            confidence="High",
            rationale="This is a valid rationale that meets the minimum length requirement of fifty characters for testing purposes.",
            room_outcomes="Test outcomes"
        )
        schema = IntermediateConclusionSchema(
            verdict=verdict,
            role_analyses=[
                RoleAnalysis(role_name="TPM", strengths=[], weaknesses=[])
            ]
        )

        gaps = gap_generator._identify_critical_gaps(schema)
        assert len(gaps) == 0


# ============================================================================
# Test Gap Severity Ranking
# ============================================================================


class TestGapSeverityRanking:
    """Test gap severity ranking logic."""

    def test_rank_gaps_by_severity(self, gap_generator, sample_intermediate_schema):
        """Test ranking gaps by severity."""
        gaps = [
            {
                "title": "Single Source Low Detail",
                "severity": "Low",
                "description": "Short description",
                "sources": ["CFO"],
                "evidence": []
            },
            {
                "title": "Multiple Sources High Detail",
                "severity": "High",
                "description": "This is a very detailed description that explains the gap in significant detail with multiple aspects considered and thoroughly analyzed.",
                "sources": ["CFO", "CTO", "CPO"],
                "evidence": []
            },
            {
                "title": "Single Source Medium Detail",
                "severity": "Medium",
                "description": "This is a medium length description that is significantly longer than fifty characters to qualify for medium strength score.",
                "sources": ["CTO"],
                "evidence": []
            }
        ]

        ranked = gap_generator._rank_gaps_by_severity(gaps, sample_intermediate_schema.verdict)

        # Multi-source should rank first (3 sources * 3 strength * 1 = 9)
        assert ranked[0]["title"] == "Multiple Sources High Detail"
        # Medium detail should rank second (1 source * 2 strength * 1 = 2)
        assert ranked[1]["title"] == "Single Source Medium Detail"
        # Low detail should rank last (1 source * 1 strength * 1 = 1)
        assert ranked[2]["title"] == "Single Source Low Detail"

    def test_judge_emphasis_increases_severity(self, gap_generator):
        """Test that judge emphasis increases severity."""
        # Create a valid Verdict with proper word count and CFO mention
        answer_words = " ".join(["word"] * 130)
        verdict = Verdict(
            answer=answer_words,
            confidence="Medium",
            rationale="The CFO raised significant concerns about the financial model during the debate, indicating that more conservative scenarios are needed.",
            room_outcomes="PRO won 3/4 rooms"
        )

        gaps = [
            {
                "title": "Financial Gap (Mentioned by Judge)",
                "severity": "High",
                "description": "Detailed financial gap description with significant analysis.",
                "sources": ["CFO"],
                "evidence": []
            },
            {
                "title": "Technical Gap (Not Mentioned)",
                "severity": "High",
                "description": "Detailed technical gap description with significant analysis.",
                "sources": ["CTO"],
                "evidence": []
            }
        ]

        ranked = gap_generator._rank_gaps_by_severity(gaps, verdict)

        # CFO gap mentioned by judge should rank first
        assert ranked[0]["title"] == "Financial Gap (Mentioned by Judge)"
        assert ranked[1]["title"] == "Technical Gap (Not Mentioned)"


# ============================================================================
# Test Recommendation Generation
# ============================================================================


class TestRecommendationGeneration:
    """Test recommendation generation from gaps."""

    def test_generate_recommendations_from_gaps(
        self, gap_generator, sample_intermediate_schema, sample_recommendations_response
    ):
        """Test generating recommendations from gaps."""
        gaps = [
            CriticalGap(
                title="Test Gap",
                severity="High",
                description="This is a valid test description that meets the minimum length requirement of twenty characters.",
                sources=["CFO"],
                evidence=[
                    EvidenceReference(
                        room_id="TPM_vs_CFO",
                        speaker_role="CFO",
                        turn_index=1,
                        quote="This is a valid test quote that meets the minimum length requirement."
                    )
                ]
            )
        ]

        with patch.object(
            gap_generator, "_generate_recommendations_with_llm",
            return_value=json.loads(sample_recommendations_response)["recommendations"]
        ):
            recommendations = gap_generator._generate_recommendations(sample_intermediate_schema, gaps)

        assert len(recommendations) == 3
        assert all(isinstance(rec, Recommendation) for rec in recommendations)

    def test_empty_gaps_returns_empty_recommendations(self, gap_generator, sample_intermediate_schema):
        """Test empty gaps returns empty recommendations."""
        recommendations = gap_generator._generate_recommendations(sample_intermediate_schema, [])
        assert len(recommendations) == 0

    def test_max_five_high_priority_recommendations(self, gap_generator, sample_intermediate_schema):
        """Test that maximum 5 high-priority recommendations are returned."""
        # Create 7 high-priority recommendations
        recommendations_data = [
            {
                "priority": "High",
                "problem": f"Problem {i} that is long enough to meet validation requirements",
                "action": f"Action {i} that is long enough to meet validation requirements",
                "metric": f"Metric {i} for measuring success",
                "source_evidence": {
                    "room_id": "TPM_vs_CFO",
                    "speaker_role": "CFO",
                    "turn_index": 1,
                    "quote": "Test quote that is long enough to meet validation requirements"
                }
            }
            for i in range(7)
        ]

        # Provide a valid gap
        gaps = [
            CriticalGap(
                title="Test Gap",
                severity="High",
                description="This is a valid test description that meets the minimum length requirement.",
                sources=["CFO"],
                evidence=[
                    EvidenceReference(
                        room_id="TPM_vs_CFO",
                        speaker_role="CFO",
                        turn_index=1,
                        quote="This is a valid test quote that meets the minimum length requirement."
                    )
                ]
            )
        ]

        with patch.object(
            gap_generator, "_generate_recommendations_with_llm",
            return_value=recommendations_data
        ):
            recommendations = gap_generator._generate_recommendations(
                sample_intermediate_schema, gaps
            )

        # Should have exactly 5 high-priority recommendations
        high_priority = [r for r in recommendations if r.priority == "High"]
        assert len(high_priority) == 5
        assert len(recommendations) == 5  # Only high-priority ones


# ============================================================================
# Test Problem→Action→Metric Format
# ============================================================================


class TestProblemActionMetricFormat:
    """Test problem→action→metric format (FR-014)."""

    def test_all_recommendations_have_problem(self, gap_generator, sample_intermediate_schema):
        """Test all recommendations have problem field."""
        recommendations_data = [
            {
                "priority": "High",
                "problem": "The problem is clear",
                "action": "Take this action",
                "metric": "Measure by this metric",
                "source_evidence": {
                    "room_id": "TPM_vs_CFO",
                    "speaker_role": "CFO",
                    "turn_index": 1,
                    "quote": "Test"
                }
            }
        ]

        # Provide a valid gap
        gaps = [
            CriticalGap(
                title="Test Gap",
                severity="High",
                description="This is a valid test description that meets the minimum length requirement.",
                sources=["CFO"],
                evidence=[
                    EvidenceReference(
                        room_id="TPM_vs_CFO",
                        speaker_role="CFO",
                        turn_index=1,
                        quote="This is a valid test quote that meets the minimum length requirement."
                    )
                ]
            )
        ]

        with patch.object(
            gap_generator, "_generate_recommendations_with_llm",
            return_value=recommendations_data
        ):
            recommendations = gap_generator._generate_recommendations(
                sample_intermediate_schema, gaps
            )

        assert len(recommendations) == 1
        assert recommendations[0].problem == "The problem is clear"

    def test_all_recommendations_have_action(self, gap_generator, sample_intermediate_schema):
        """Test all recommendations have action field."""
        recommendations_data = [
            {
                "priority": "High",
                "problem": "Problem here",
                "action": "Execute this action",
                "metric": "Measure success",
                "source_evidence": {
                    "room_id": "TPM_vs_CFO",
                    "speaker_role": "CFO",
                    "turn_index": 1,
                    "quote": "Test"
                }
            }
        ]

        # Provide a valid gap
        gaps = [
            CriticalGap(
                title="Test Gap",
                severity="High",
                description="This is a valid test description that meets the minimum length requirement.",
                sources=["CFO"],
                evidence=[
                    EvidenceReference(
                        room_id="TPM_vs_CFO",
                        speaker_role="CFO",
                        turn_index=1,
                        quote="This is a valid test quote that meets the minimum length requirement."
                    )
                ]
            )
        ]

        with patch.object(
            gap_generator, "_generate_recommendations_with_llm",
            return_value=recommendations_data
        ):
            recommendations = gap_generator._generate_recommendations(
                sample_intermediate_schema, gaps
            )

        assert len(recommendations) == 1
        assert recommendations[0].action == "Execute this action"

    def test_all_recommendations_have_metric(self, gap_generator, sample_intermediate_schema):
        """Test all recommendations have metric field."""
        recommendations_data = [
            {
                "priority": "High",
                "problem": "Problem here",
                "action": "Action here",
                "metric": "Success metric defined",
                "source_evidence": {
                    "room_id": "TPM_vs_CFO",
                    "speaker_role": "CFO",
                    "turn_index": 1,
                    "quote": "Test"
                }
            }
        ]

        # Provide a valid gap
        gaps = [
            CriticalGap(
                title="Test Gap",
                severity="High",
                description="This is a valid test description that meets the minimum length requirement.",
                sources=["CFO"],
                evidence=[
                    EvidenceReference(
                        room_id="TPM_vs_CFO",
                        speaker_role="CFO",
                        turn_index=1,
                        quote="This is a valid test quote that meets the minimum length requirement."
                    )
                ]
            )
        ]

        with patch.object(
            gap_generator, "_generate_recommendations_with_llm",
            return_value=recommendations_data
        ):
            recommendations = gap_generator._generate_recommendations(
                sample_intermediate_schema, gaps
            )

        assert len(recommendations) == 1
        assert recommendations[0].metric == "Success metric defined"


# ============================================================================
# Test Evidence Traceability
# ============================================================================


class TestEvidenceTraceability:
    """Test evidence traceability for recommendations."""

    def test_all_recommendations_have_source_evidence(self, gap_generator, sample_intermediate_schema):
        """Test all recommendations have source_evidence."""
        recommendations_data = [
            {
                "priority": "High",
                "problem": "Problem here",
                "action": "Action here",
                "metric": "Metric here",
                "source_evidence": {
                    "room_id": "TPM_vs_CFO",
                    "speaker_role": "CFO",
                    "turn_index": 1,
                    "quote": "Supporting quote"
                }
            }
        ]

        # Provide a valid gap
        gaps = [
            CriticalGap(
                title="Test Gap",
                severity="High",
                description="This is a valid test description that meets the minimum length requirement.",
                sources=["CFO"],
                evidence=[
                    EvidenceReference(
                        room_id="TPM_vs_CFO",
                        speaker_role="CFO",
                        turn_index=1,
                        quote="This is a valid test quote that meets the minimum length requirement."
                    )
                ]
            )
        ]

        with patch.object(
            gap_generator, "_generate_recommendations_with_llm",
            return_value=recommendations_data
        ):
            recommendations = gap_generator._generate_recommendations(
                sample_intermediate_schema, gaps
            )

        assert len(recommendations) == 1
        assert hasattr(recommendations[0], "source_evidence")
        assert isinstance(recommendations[0].source_evidence, EvidenceReference)


# ============================================================================
# Test Response Parsing
# ============================================================================


class TestResponseParsing:
    """Test LLM response parsing."""

    def test_parse_gap_response_with_markdown(self, gap_generator):
        """Test parsing gap response with markdown wrapping."""
        response = '''```json
{
  "gaps": [
    {
      "title": "Test Gap",
      "severity": "High",
      "description": "Test description",
      "sources": ["CFO"],
      "evidence": []
    }
  ]
}
```'''
        gaps = gap_generator._parse_gap_response(response)
        assert len(gaps) == 1
        assert gaps[0]["title"] == "Test Gap"

    def test_parse_recommendation_response_with_markdown(self, gap_generator):
        """Test parsing recommendation response with markdown wrapping."""
        response = '''```json
{
  "recommendations": [
    {
      "priority": "High",
      "problem": "Test problem",
      "action": "Test action",
      "metric": "Test metric",
      "source_evidence": {
        "room_id": "TPM_vs_CFO",
        "speaker_role": "CFO",
        "turn_index": 1,
        "quote": "Test quote"
      }
    }
  ]
}
```'''
        recommendations = gap_generator._parse_recommendation_response(response)
        assert len(recommendations) == 1
        assert recommendations[0]["problem"] == "Test problem"

    def test_parse_invalid_json_returns_empty(self, gap_generator):
        """Test parsing invalid JSON returns empty list."""
        gaps = gap_generator._parse_gap_response("Not valid JSON")
        assert len(gaps) == 0

    def test_parse_response_missing_gaps_field(self, gap_generator):
        """Test parsing response without 'gaps' field."""
        response = '{"something_else": []}'
        gaps = gap_generator._parse_gap_response(response)
        assert len(gaps) == 0


# ============================================================================
# Test Integration
# ============================================================================


class TestIntegration:
    """Test GapRecommendationGenerator integration."""

    def test_extends_enhanced_analyzer(self):
        """Test that GapRecommendationGenerator extends EnhancedAnalyzer."""
        from src.analyzers.base_analyzer import EnhancedAnalyzer

        generator = GapRecommendationGenerator(llm_config=None)
        assert isinstance(generator, EnhancedAnalyzer)

    def test_call_returns_gaps_and_recommendations(
        self, gap_generator, sample_intermediate_schema
    ):
        """Test __call__ returns tuple of gaps and recommendations."""
        with patch.object(gap_generator, "_identify_critical_gaps", return_value=[]):
            with patch.object(gap_generator, "_generate_recommendations", return_value=[]):
                gaps, recommendations = gap_generator(sample_intermediate_schema)

        assert isinstance(gaps, list)
        assert isinstance(recommendations, list)


# ============================================================================
# Test Edge Cases
# ============================================================================


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_very_long_gap_title_truncated(self, gap_generator):
        """Test that very long gap titles are handled."""
        # Pydantic will validate max length
        gap_data = {
            "title": "x" * 150,  # Exceeds 100 char max
            "severity": "High",
            "description": "Valid description that is long enough",
            "sources": ["CFO"],
            "evidence": []
        }

        # This should raise validation error
        with pytest.raises(Exception):
            CriticalGap(**gap_data)

    def test_gap_description_too_short(self, gap_generator):
        """Test gap description too short raises error."""
        gap_data = {
            "title": "Valid title",
            "severity": "High",
            "description": "Too short",
            "sources": ["CFO"],
            "evidence": []
        }

        with pytest.raises(Exception):
            CriticalGap(**gap_data)

    def test_recommendation_problem_too_short(self, gap_generator):
        """Test recommendation problem too short raises error."""
        rec_data = {
            "priority": "High",
            "problem": "Short",
            "action": "Valid action description that is long enough",
            "metric": "Valid metric",
            "source_evidence": {
                "room_id": "TPM_vs_CFO",
                "speaker_role": "CFO",
                "turn_index": 1,
                "quote": "Valid quote that is long enough"
            }
        }

        with pytest.raises(Exception):
            Recommendation(**rec_data)

    def test_recommendation_metric_not_measurable(self, gap_generator):
        """Test recommendation with non-measurable metric."""
        # This is a content issue, not a validation issue
        # The metric "Improve quality" is not measurable but passes validation
        rec_data = {
            "priority": "High",
            "problem": "Valid problem statement that describes the issue",
            "action": "Valid action description that is specific",
            "metric": "Improve quality",  # Not measurable, but passes length validation
            "source_evidence": {
                "room_id": "TPM_vs_CFO",
                "speaker_role": "CFO",
                "turn_index": 1,
                "quote": "Valid quote that supports the recommendation"
            }
        }

        # Should pass validation (length check)
        rec = Recommendation(**rec_data)
        assert rec.metric == "Improve quality"
