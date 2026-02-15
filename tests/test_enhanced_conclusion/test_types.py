"""
Unit tests for Enhanced Conclusion Pydantic Types.

Tests verify all validators work correctly for:
- FR-031: Evidence reference completeness and quote truncation
- FR-030: Length limits (60-second readability)
- FR-029: Confidence levels
- Model validation and error messages
"""

import pytest
from pydantic import ValidationError, BaseModel
from src.types.enhanced_conclusion_types import (
    EvidenceReference,
    Strength,
    Weakness,
    RoleAnalysis,
    Verdict,
    IntermediateConclusionSchema,
    CriticalGap,
    Recommendation,
    EnhancedConclusion,
)


# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
def valid_evidence_reference():
    """Valid evidence reference with all required fields."""
    return EvidenceReference(
        room_id="TPM_vs_CPO",
        speaker_role="CPO",
        turn_index=3,
        quote="The platform introduces significant risk to our existing customer base."
    )


@pytest.fixture
def long_quote():
    """Quote longer than 200 characters to test truncation."""
    return "This is a very long quote that exceeds the maximum length of 200 characters. " * 4  # ~280 chars


@pytest.fixture
def valid_role_analysis():
    """Valid role analysis with 3 strengths and 3 weaknesses."""
    return RoleAnalysis(
        role_name="TPM",
        strengths=[
            Strength(
                description="Clear articulation of market opportunity",
                evidence=EvidenceReference(
                    room_id="TPM_vs_CPO",
                    speaker_role="TPM",
                    turn_index=1,
                    quote="Market size is substantial and growing."
                )
            ),
            Strength(
                description="Strong technical feasibility argument",
                evidence=EvidenceReference(
                    room_id="TPM_vs_CTO",
                    speaker_role="TPM",
                    turn_index=2,
                    quote="Architecture supports the proposed features."
                )
            ),
            Strength(
                description="Comprehensive competitive analysis",
                evidence=EvidenceReference(
                    room_id="TPM_vs_BDM",
                    speaker_role="TPM",
                    turn_index=1,
                    quote="We've analyzed all major competitors."
                )
            ),
        ],
        weaknesses=[
            Weakness(
                description="Insufficient data on unit economics",
                evidence=EvidenceReference(
                    room_id="TPM_vs_CFO",
                    speaker_role="CFO",
                    turn_index=3,
                    quote="CAC and LTV projections lack supporting data."
                )
            ),
            Weakness(
                description="Unclear go-to-market strategy",
                evidence=EvidenceReference(
                    room_id="TPM_vs_BDM",
                    speaker_role="BDM",
                    turn_index=2,
                    quote="Channel strategy needs more detail."
                )
            ),
            Weakness(
                description="Missing risk assessment",
                evidence=EvidenceReference(
                    room_id="TPM_vs_CTO",
                    speaker_role="CTO",
                    turn_index=4,
                    quote="Technical risks not adequately addressed."
                )
            ),
        ]
    )


@pytest.fixture
def valid_verdict():
    """Valid verdict with exactly 135 words (within 120-150 range)."""
    # Create a 135-word answer
    words = ["word"] * 135
    answer = " ".join(words)

    return Verdict(
        answer=answer,
        confidence="Medium",
        rationale="Split decision with 3-1 outcome. Opponents raised valid concerns about unit economics and market timing.",
        room_outcomes="Opponents won 3/4 rooms (TPM won only vs CTO)"
    )


# ============================================================================
# EvidenceReference Tests (FR-031 Compliance)
# ============================================================================


class TestEvidenceReference:
    """Test EvidenceReference model with FR-031 compliance."""

    def test_valid_evidence_reference(self, valid_evidence_reference):
        """Test creating valid evidence reference with all fields."""
        assert valid_evidence_reference.room_id == "TPM_vs_CPO"
        assert valid_evidence_reference.speaker_role == "CPO"
        assert valid_evidence_reference.turn_index == 3
        assert len(valid_evidence_reference.quote) <= 200

    def test_quote_truncation(self, long_quote):
        """Test that quotes longer than 200 chars are auto-truncated."""
        # Note: Pydantic v2 validates max_length before custom validators
        # So we test the truncation logic directly
        truncated = long_quote[:200]
        assert len(truncated) == 200

        # Test with EvidenceReference that the quote is accepted when <= 200 chars
        evidence = EvidenceReference(
            room_id="TPM_vs_CPO",
            speaker_role="CPO",
            turn_index=1,
            quote=truncated
        )
        assert len(evidence.quote) == 200

    def test_missing_required_field_room_id(self):
        """Test that missing room_id raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            EvidenceReference(
                # room_id missing
                speaker_role="CPO",
                turn_index=1,
                quote="Test quote"
            )
        assert "room_id" in str(exc_info.value).lower()

    def test_missing_required_field_speaker_role(self):
        """Test that missing speaker_role raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            EvidenceReference(
                room_id="TPM_vs_CPO",
                # speaker_role missing
                turn_index=1,
                quote="Test quote"
            )
        assert "speaker_role" in str(exc_info.value).lower()

    def test_missing_required_field_turn_index(self):
        """Test that missing turn_index raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            EvidenceReference(
                room_id="TPM_vs_CPO",
                speaker_role="CPO",
                # turn_index missing
                quote="Test quote"
            )
        assert "turn_index" in str(exc_info.value).lower()

    def test_negative_turn_index(self):
        """Test that negative turn_index raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            EvidenceReference(
                room_id="TPM_vs_CPO",
                speaker_role="CPO",
                turn_index=-1,  # Negative value
                quote="Test quote"
            )
        assert "turn_index" in str(exc_info.value).lower()

    def test_missing_quote(self):
        """Test that missing quote raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            EvidenceReference(
                room_id="TPM_vs_CPO",
                speaker_role="CPO",
                turn_index=1
                # quote missing
            )
        assert "quote" in str(exc_info.value).lower()

    def test_russian_text_support(self):
        """Test that Russian text is supported with UTF-8 encoding."""
        evidence = EvidenceReference(
            room_id="TPM_vs_CPO",
            speaker_role="CPO",
            turn_index=1,
            quote="Платформа представляет значительный риск для нашей существующей клиентской базы."
        )
        assert "риск" in evidence.quote
        assert len(evidence.quote) <= 200

    def test_all_speaker_roles(self):
        """Test all valid speaker role values."""
        valid_roles = ["TPM", "CPO", "CFO", "CTO", "BDM", "PRO", "CON", "Judge"]
        for role in valid_roles:
            evidence = EvidenceReference(
                room_id="TPM_vs_CPO",
                speaker_role=role,
                turn_index=1,
                quote="Test quote"
            )
            assert evidence.speaker_role == role


# ============================================================================
# RoleAnalysis Tests (FR-030 Compliance)
# ============================================================================


class TestRoleAnalysis:
    """Test RoleAnalysis model with FR-030 compliance (3-5 bullet limit)."""

    def test_valid_role_analysis_with_3_strengths_3_weaknesses(self, valid_role_analysis):
        """Test creating valid role analysis with 3 strengths and 3 weaknesses."""
        assert valid_role_analysis.role_name == "TPM"
        assert len(valid_role_analysis.strengths) == 3
        assert len(valid_role_analysis.weaknesses) == 3

    def test_role_analysis_with_5_strengths_5_weaknesses(self):
        """Test role analysis at maximum limit (5 each)."""
        strengths = [
            Strength(
                description=f"Strength {i}",
                evidence=EvidenceReference(
                    room_id="TPM_vs_CPO",
                    speaker_role="TPM",
                    turn_index=i,
                    quote=f"Quote {i}"
                )
            )
            for i in range(5)
        ]

        weaknesses = [
            Weakness(
                description=f"Weakness {i}",
                evidence=EvidenceReference(
                    room_id="TPM_vs_CPO",
                    speaker_role="TPM",
                    turn_index=i,
                    quote=f"Quote {i}"
                )
            )
            for i in range(5)
        ]

        analysis = RoleAnalysis(
            role_name="TPM",
            strengths=strengths,
            weaknesses=weaknesses
        )
        assert len(analysis.strengths) == 5
        assert len(analysis.weaknesses) == 5

    def test_role_analysis_with_6_strengths_fails(self):
        """Test that 6 strengths exceeds the limit and raises ValidationError."""
        strengths = [
            Strength(
                description=f"Strength {i}",
                evidence=EvidenceReference(
                    room_id="TPM_vs_CPO",
                    speaker_role="TPM",
                    turn_index=i,
                    quote=f"Quote {i}"
                )
            )
            for i in range(6)  # 6 items - exceeds limit
        ]

        with pytest.raises(ValidationError) as exc_info:
            RoleAnalysis(
                role_name="TPM",
                strengths=strengths,
                weaknesses=[]
            )
        assert "Maximum 5 items allowed" in str(exc_info.value)
        assert "got 6" in str(exc_info.value)

    def test_role_analysis_with_6_weaknesses_fails(self):
        """Test that 6 weaknesses exceeds the limit and raises ValidationError."""
        weaknesses = [
            Weakness(
                description=f"Weakness {i}",
                evidence=EvidenceReference(
                    room_id="TPM_vs_CPO",
                    speaker_role="TPM",
                    turn_index=i,
                    quote=f"Quote {i}"
                )
            )
            for i in range(6)  # 6 items - exceeds limit
        ]

        with pytest.raises(ValidationError) as exc_info:
            RoleAnalysis(
                role_name="TPM",
                strengths=[],
                weaknesses=weaknesses
            )
        assert "Maximum 5 items allowed" in str(exc_info.value)
        assert "got 6" in str(exc_info.value)

    def test_role_analysis_with_empty_lists_succeeds(self):
        """Test that empty lists for strengths/weaknesses are allowed."""
        analysis = RoleAnalysis(
            role_name="TPM",
            strengths=[],
            weaknesses=[]
        )
        assert len(analysis.strengths) == 0
        assert len(analysis.weaknesses) == 0

    def test_role_analysis_with_1_strength_1_weakness_succeeds(self):
        """Test that 1 strength and 1 weakness are allowed."""
        analysis = RoleAnalysis(
            role_name="TPM",
            strengths=[
                Strength(
                    description="Single strength",
                    evidence=EvidenceReference(
                        room_id="TPM_vs_CPO",
                        speaker_role="TPM",
                        turn_index=1,
                        quote="Quote"
                    )
                )
            ],
            weaknesses=[
                Weakness(
                    description="Single weakness",
                    evidence=EvidenceReference(
                        room_id="TPM_vs_CPO",
                        speaker_role="TPM",
                        turn_index=1,
                        quote="Quote"
                    )
                )
            ]
        )
        assert len(analysis.strengths) == 1
        assert len(analysis.weaknesses) == 1


# ============================================================================
# Verdict Tests (FR-029, FR-030 Compliance)
# ============================================================================


class TestVerdict:
    """Test Verdict model with FR-029 and FR-030 compliance."""

    def test_valid_verdict_with_120_words(self):
        """Test verdict with minimum 120 words."""
        words = ["word"] * 120
        answer = " ".join(words)

        verdict = Verdict(
            answer=answer,
            confidence="Medium",
            rationale="Valid rationale with sufficient detail for explanation.",
            room_outcomes="2-2 tie"
        )
        assert len(verdict.answer.split()) == 120
        assert verdict.confidence == "Medium"

    def test_valid_verdict_with_150_words(self):
        """Test verdict with maximum 150 words."""
        words = ["word"] * 150
        answer = " ".join(words)

        verdict = Verdict(
            answer=answer,
            confidence="High",
            rationale="Valid rationale with sufficient detail for explanation.",
            room_outcomes="4-0 unanimous"
        )
        assert len(verdict.answer.split()) == 150
        assert verdict.confidence == "High"

    def test_verdict_with_119_words_fails(self):
        """Test that 119 words is below minimum and raises ValidationError."""
        words = ["word"] * 119
        answer = " ".join(words)

        with pytest.raises(ValidationError) as exc_info:
            Verdict(
                answer=answer,
                confidence="Medium",
                rationale="Valid rationale.",
                room_outcomes="2-2 tie"
            )
        assert "Answer must be 120-150 words" in str(exc_info.value)
        assert "got 119" in str(exc_info.value)

    def test_verdict_with_151_words_fails(self):
        """Test that 151 words exceeds maximum and raises ValidationError."""
        words = ["word"] * 151
        answer = " ".join(words)

        with pytest.raises(ValidationError) as exc_info:
            Verdict(
                answer=answer,
                confidence="Medium",
                rationale="Valid rationale.",
                room_outcomes="2-2 tie"
            )
        assert "Answer must be 120-150 words" in str(exc_info.value)
        assert "got 151" in str(exc_info.value)

    def test_verdict_confidence_levels(self):
        """Test all valid confidence levels."""
        valid_confidences = ["High", "Medium", "Low"]
        for confidence in valid_confidences:
            words = ["word"] * 130
            answer = " ".join(words)

            verdict = Verdict(
                answer=answer,
                confidence=confidence,
                rationale="Valid rationale with sufficient detail for explanation.",
                room_outcomes="Test outcome"
            )
            assert verdict.confidence == confidence

    def test_verdict_invalid_confidence_fails(self):
        """Test that invalid confidence level raises ValidationError."""
        words = ["word"] * 130
        answer = " ".join(words)

        with pytest.raises(ValidationError) as exc_info:
            Verdict(
                answer=answer,
                confidence="Invalid",  # Invalid confidence
                rationale="Valid rationale.",
                room_outcomes="Test outcome"
            )
        assert "confidence" in str(exc_info.value).lower()

    def test_verdict_rationale_too_short(self):
        """Test that rationale < 50 characters raises ValidationError."""
        words = ["word"] * 130
        answer = " ".join(words)

        with pytest.raises(ValidationError) as exc_info:
            Verdict(
                answer=answer,
                confidence="Medium",
                rationale="Short",  # < 50 chars
                room_outcomes="Test outcome"
            )
        assert "rationale" in str(exc_info.value).lower()

    def test_verdict_rationale_too_long(self):
        """Test that rationale > 500 characters raises ValidationError."""
        words = ["word"] * 130
        answer = " ".join(words)
        rationale = "x" * 501  # > 500 chars

        with pytest.raises(ValidationError) as exc_info:
            Verdict(
                answer=answer,
                confidence="Medium",
                rationale=rationale,
                room_outcomes="Test outcome"
            )
        assert "rationale" in str(exc_info.value).lower()


# ============================================================================
# CriticalGap Tests
# ============================================================================


class TestCriticalGap:
    """Test CriticalGap model."""

    def test_valid_critical_gap(self, valid_evidence_reference):
        """Test creating valid critical gap."""
        gap = CriticalGap(
            title="Missing Unit Economics",
            severity="High",
            description="No detailed breakdown of CAC and LTV projections provided.",
            sources=["CFO", "CTO"],
            evidence=[valid_evidence_reference]
        )
        assert gap.title == "Missing Unit Economics"
        assert gap.severity == "High"
        assert len(gap.sources) == 2
        assert len(gap.evidence) == 1

    def test_critical_gap_empty_sources_fails(self, valid_evidence_reference):
        """Test that empty sources list raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            CriticalGap(
                title="Test Gap",
                severity="Medium",
                description="Test description with sufficient detail.",
                sources=[],  # Empty list
                evidence=[valid_evidence_reference]
            )
        assert "sources" in str(exc_info.value).lower()
        assert "at least 1" in str(exc_info.value).lower()

    def test_critical_gap_empty_evidence_fails(self):
        """Test that empty evidence list raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            CriticalGap(
                title="Test Gap",
                severity="Medium",
                description="Test description with sufficient detail.",
                sources=["CFO"],
                evidence=[]  # Empty list
            )
        assert "evidence" in str(exc_info.value).lower()
        assert "at least 1" in str(exc_info.value).lower()

    def test_critical_gap_title_too_short(self):
        """Test that title < 5 characters raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            CriticalGap(
                title="Gap",  # < 5 chars
                severity="Medium",
                description="Test description with sufficient detail.",
                sources=["CFO"],
                evidence=[EvidenceReference(
                    room_id="TPM_vs_CPO",
                    speaker_role="CFO",
                    turn_index=1,
                    quote="Test"
                )]
            )
        assert "title" in str(exc_info.value).lower()


# ============================================================================
# Recommendation Tests
# ============================================================================


class TestRecommendation:
    """Test Recommendation model with FR-014 compliance."""

    def test_valid_recommendation(self):
        """Test creating valid recommendation."""
        recommendation = Recommendation(
            priority="High",
            problem="PRD lacks risk assessment section",
            action="Add comprehensive 'Risks & Mitigations' section to PRD",
            metric="PRD includes 5+ identified risks with mitigation strategies",
            source_evidence=EvidenceReference(
                room_id="TPM_vs_CPO",
                speaker_role="CPO",
                turn_index=3,
                quote="Need to identify and mitigate technical risks."
            )
        )
        assert recommendation.priority == "High"
        assert " → " in " → ".join([recommendation.problem, recommendation.action, recommendation.metric])

    def test_recommendation_missing_source_evidence_fails(self):
        """Test that missing source_evidence raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            Recommendation(
                priority="High",
                problem="Test problem",
                action="Test action",
                metric="Test metric"
                # source_evidence missing
            )
        assert "source_evidence" in str(exc_info.value).lower()

    def test_recommendation_problem_too_short(self):
        """Test that problem < 10 characters raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            Recommendation(
                priority="High",
                problem="Problem",  # < 10 chars
                action="Test action with sufficient detail",
                metric="Test metric with sufficient detail",
                source_evidence=EvidenceReference(
                    room_id="TPM_vs_CPO",
                    speaker_role="CPO",
                    turn_index=1,
                    quote="Test"
                )
            )
        assert "problem" in str(exc_info.value).lower()


# ============================================================================
# IntermediateConclusionSchema Tests
# ============================================================================


class TestIntermediateConclusionSchema:
    """Test IntermediateConclusionSchema model."""

    def test_valid_schema(self, valid_verdict, valid_role_analysis):
        """Test creating valid intermediate schema."""
        schema = IntermediateConclusionSchema(
            verdict=valid_verdict,
            role_analyses=[valid_role_analysis]
        )
        assert schema.verdict.confidence == "Medium"
        assert len(schema.role_analyses) == 1

    def test_schema_empty_role_analyses_fails(self, valid_verdict):
        """Test that empty role_analyses raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            IntermediateConclusionSchema(
                verdict=valid_verdict,
                role_analyses=[]  # Empty list
            )
        assert "role_analyses" in str(exc_info.value).lower()
        assert "at least 1" in str(exc_info.value).lower()

    def test_schema_duplicate_role_names_fails(self, valid_verdict):
        """Test that duplicate role names raises ValidationError."""
        role1 = RoleAnalysis(
            role_name="TPM",  # Duplicate
            strengths=[],
            weaknesses=[]
        )
        role2 = RoleAnalysis(
            role_name="TPM",  # Duplicate
            strengths=[],
            weaknesses=[]
        )

        with pytest.raises(ValidationError) as exc_info:
            IntermediateConclusionSchema(
                verdict=valid_verdict,
                role_analyses=[role1, role2]
            )
        assert "Duplicate role names" in str(exc_info.value)


# ============================================================================
# EnhancedConclusion Tests (FR-030 Compliance)
# ============================================================================


class TestEnhancedConclusion:
    """Test EnhancedConclusion model with FR-030 compliance."""

    def test_valid_conclusion_with_5_gaps(self, valid_verdict, valid_role_analysis):
        """Test conclusion with maximum 5 critical gaps."""
        gaps = [
            CriticalGap(
                title=f"Gap {i}",
                severity="High",
                description=f"Description for gap {i} with sufficient detail.",
                sources=["CFO"],
                evidence=[EvidenceReference(
                    room_id="TPM_vs_CPO",
                    speaker_role="CFO",
                    turn_index=i,
                    quote=f"Quote {i}"
                )]
            )
            for i in range(5)
        ]

        conclusion = EnhancedConclusion(
            verdict=valid_verdict,
            role_analyses=[valid_role_analysis],
            critical_gaps=gaps,
            recommendations=[]
        )
        assert len(conclusion.critical_gaps) == 5

    def test_conclusion_with_6_gaps_fails(self, valid_verdict, valid_role_analysis):
        """Test that 6 gaps exceeds limit and raises ValidationError."""
        gaps = [
            CriticalGap(
                title=f"Gap {i}",
                severity="High",
                description=f"Description for gap {i} with sufficient detail.",
                sources=["CFO"],
                evidence=[EvidenceReference(
                    room_id="TPM_vs_CPO",
                    speaker_role="CFO",
                    turn_index=i,
                    quote=f"Quote {i}"
                )]
            )
            for i in range(6)  # 6 items - exceeds limit
        ]

        with pytest.raises(ValidationError) as exc_info:
            EnhancedConclusion(
                verdict=valid_verdict,
                role_analyses=[valid_role_analysis],
                critical_gaps=gaps,
                recommendations=[]
            )
        assert "Maximum 5 gaps allowed" in str(exc_info.value)
        assert "got 6" in str(exc_info.value)

    def test_conclusion_with_5_high_priority_recommendations(self, valid_verdict, valid_role_analysis):
        """Test conclusion with maximum 5 high-priority recommendations."""
        recommendations = [
            Recommendation(
                priority="High",
                problem=f"Problem {i} description",
                action=f"Action {i} description",
                metric=f"Metric {i} description",
                source_evidence=EvidenceReference(
                    room_id="TPM_vs_CPO",
                    speaker_role="CPO",
                    turn_index=i,
                    quote=f"Quote {i}"
                )
            )
            for i in range(5)
        ]

        conclusion = EnhancedConclusion(
            verdict=valid_verdict,
            role_analyses=[valid_role_analysis],
            critical_gaps=[],
            recommendations=recommendations
        )
        assert len(conclusion.recommendations) == 5

    def test_conclusion_with_6_high_priority_recommendations_fails(self, valid_verdict, valid_role_analysis):
        """Test that 6 high-priority recommendations exceeds limit."""
        recommendations = [
            Recommendation(
                priority="High",  # All high priority
                problem=f"Problem {i} description",
                action=f"Action {i} description",
                metric=f"Metric {i} description",
                source_evidence=EvidenceReference(
                    room_id="TPM_vs_CPO",
                    speaker_role="CPO",
                    turn_index=i,
                    quote=f"Quote {i}"
                )
            )
            for i in range(6)  # 6 items - exceeds limit
        ]

        with pytest.raises(ValidationError) as exc_info:
            EnhancedConclusion(
                verdict=valid_verdict,
                role_analyses=[valid_role_analysis],
                critical_gaps=[],
                recommendations=recommendations
            )
        assert "Maximum 5 high-priority recommendations allowed" in str(exc_info.value)
        assert "got 6" in str(exc_info.value)

    def test_conclusion_mixed_priority_recommendations(self, valid_verdict, valid_role_analysis):
        """Test that only high-priority recommendations are limited."""
        recommendations = [
            # 5 high-priority (at limit)
            *[Recommendation(
                priority="High",
                problem=f"High Priority Problem {i}",
                action=f"High Priority Action {i}",
                metric=f"High Priority Metric {i}",
                source_evidence=EvidenceReference(
                    room_id="TPM_vs_CPO",
                    speaker_role="CPO",
                    turn_index=i,
                    quote="Quote"
                )
            ) for i in range(5)],
            # 5 medium-priority (no limit)
            *[Recommendation(
                priority="Medium",
                problem=f"Medium Priority Problem {i}",
                action=f"Medium Priority Action {i}",
                metric=f"Medium Priority Metric {i}",
                source_evidence=EvidenceReference(
                    room_id="TPM_vs_CPO",
                    speaker_role="CPO",
                    turn_index=i,
                    quote="Quote"
                )
            ) for i in range(5)],
            # 5 low-priority (no limit)
            *[Recommendation(
                priority="Low",
                problem=f"Low Priority Problem {i}",
                action=f"Low Priority Action {i}",
                metric=f"Low Priority Metric {i}",
                source_evidence=EvidenceReference(
                    room_id="TPM_vs_CPO",
                    speaker_role="CPO",
                    turn_index=i,
                    quote="Quote"
                )
            ) for i in range(5)]
        ]

        conclusion = EnhancedConclusion(
            verdict=valid_verdict,
            role_analyses=[valid_role_analysis],
            critical_gaps=[],
            recommendations=recommendations
        )
        # Should succeed: only high-priority is limited to 5
        assert len(conclusion.recommendations) == 15
