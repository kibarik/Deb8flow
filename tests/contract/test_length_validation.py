"""
Contract tests for length limit validation (FR-030).

These tests enforce 60-second readability requirements:
- Verdict answer: 120-150 words
- Each role: 3-5 strengths, 3-5 weaknesses
- Max 5 critical gaps
- Max 5 high-priority recommendations
"""

import pytest
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from src.validators.enhanced_conclusion_validators import (
    ValidationResult,
    validate_length_limits,
)
from src.types.enhanced_conclusion_types import (
    EnhancedConclusion,
    Verdict,
    RoleAnalysis,
    CriticalGap,
    Recommendation,
    EvidenceReference,
)


class TestLengthValidation:
    """Contract tests for length limit validation."""

    @pytest.fixture
    def valid_verdict(self):
        """Create a valid verdict with 120-150 words."""
        # Create exactly 135 words (within range)
        words = " ".join(["word"] * 135)
        return Verdict(
            answer=words,
            confidence="Medium",
            rationale="Split decision with 3-1 outcome.",
            room_outcomes="PRO won 3/4 rooms"
        )

    @pytest.fixture
    def valid_role_analysis(self):
        """Create a valid role analysis with 3-5 strengths/weaknesses."""
        return RoleAnalysis(
            role_name="CFO",
            strengths=[
                {
                    "description": "Strong financial analysis skills",
                    "evidence": EvidenceReference(
                        room_id="TPM_vs_CFO",
                        speaker_role="CFO",
                        turn_index=1,
                        quote="Good financial model"
                    )
                },
                {
                    "description": "Thorough risk assessment",
                    "evidence": EvidenceReference(
                        room_id="TPM_vs_CFO",
                        speaker_role="CFO",
                        turn_index=2,
                        quote="Risk well analyzed"
                    )
                },
                {
                    "description": "Clear ROI projections",
                    "evidence": EvidenceReference(
                        room_id="TPM_vs_CFO",
                        speaker_role="CFO",
                        turn_index=3,
                        quote="ROI clearly defined"
                    )
                }
            ],
            weaknesses=[
                {
                    "description": "Conservative scenario missing",
                    "evidence": EvidenceReference(
                        room_id="TPM_vs_CFO",
                        speaker_role="CFO",
                        turn_index=2,
                        quote="Need more scenarios"
                    )
                },
                {
                    "description": "Implementation costs underestimated",
                    "evidence": EvidenceReference(
                        room_id="TPM_vs_CFO",
                        speaker_role="CFO",
                        turn_index=3,
                        quote="Costs too low"
                    )
                },
                {
                    "description": "Timeline too aggressive",
                    "evidence": EvidenceReference(
                        room_id="TPM_vs_CFO",
                        speaker_role="CFO",
                        turn_index=4,
                        quote="Timeline unrealistic"
                    )
                }
            ]
        )

    @pytest.fixture
    def valid_conclusion(self, valid_verdict, valid_role_analysis):
        """Create a valid enhanced conclusion."""
        return EnhancedConclusion(
            verdict=valid_verdict,
            role_analyses=[valid_role_analysis],
            critical_gaps=[
                CriticalGap(
                    title="Incomplete Financial Analysis",
                    severity="High",
                    description="The financial model lacks conservative scenarios.",
                    sources=["CFO"],
                    evidence=[
                        EvidenceReference(
                            room_id="TPM_vs_CFO",
                            speaker_role="CFO",
                            turn_index=2,
                            quote="Need more scenarios"
                        )
                    ]
                )
            ],
            recommendations=[
                Recommendation(
                    priority="High",
                    problem="The PRD lacks comprehensive financial analysis",
                    action="Add detailed Financial Analysis section",
                    metric="PRD includes complete financial analysis",
                    source_evidence=EvidenceReference(
                        room_id="TPM_vs_CFO",
                        speaker_role="CFO",
                        turn_index=2,
                        quote="Need more scenarios"
                    )
                )
            ]
        )

    def test_valid_conclusion_passes_length_validation(self, valid_conclusion):
        """Test that a valid enhanced conclusion passes length validation."""
        result = validate_length_limits(valid_conclusion)

        assert result.is_valid
        assert len(result.errors) == 0
        assert result.length_compliance == 100.0

    def test_verdict_answer_too_short_fails_validation(self):
        """Test that verdict answer < 120 words fails validation."""
        short_words = " ".join(["word"] * 100)  # 100 words (< 120)
        verdict = Verdict(
            answer=short_words,
            confidence="Medium",
            rationale="Split decision with 3-1 outcome. Financial concerns were significant and require additional planning based on the committee discussion and analysis of the PRD document content.",
            room_outcomes="PRO won"
        )

        conclusion = EnhancedConclusion(
            verdict=verdict,
            role_analyses=[],
            critical_gaps=[],
            recommendations=[]
        )

        result = validate_length_limits(conclusion)

        assert not result.is_valid
        assert any(e.field == "verdict.answer" for e in result.errors)
        assert "120-150 words" in result.errors[0].message

    def test_verdict_answer_too_long_fails_validation(self):
        """Test that verdict answer > 150 words fails validation."""
        long_words = " ".join(["word"] * 200)  # 200 words (> 150)
        verdict = Verdict(
            answer=long_words,
            confidence="Medium",
            rationale="Split decision with 3-1 outcome. Financial concerns were significant and require additional planning based on the committee discussion and analysis of the PRD document content.",
            room_outcomes="PRO won"
        )

        conclusion = EnhancedConclusion(
            verdict=verdict,
            role_analyses=[],
            critical_gaps=[],
            recommendations=[]
        )

        result = validate_length_limits(conclusion)

        assert not result.is_valid
        assert any(e.field == "verdict.answer" for e in result.errors)

    def test_verdict_answer_exactly_120_words_passes(self):
        """Test that verdict answer of exactly 120 words passes validation."""
        words = " ".join(["word"] * 120)
        verdict = Verdict(
            answer=words,
            confidence="Medium",
            rationale="Split decision with 3-1 outcome. Financial concerns were significant and require additional planning based on the committee discussion and analysis of the PRD document content.",
            room_outcomes="PRO won"
        )

        conclusion = EnhancedConclusion(
            verdict=verdict,
            role_analyses=[],
            critical_gaps=[],
            recommendations=[]
        )

        result = validate_length_limits(conclusion)

        assert result.is_valid

    def test_verdict_answer_exactly_150_words_passes(self):
        """Test that verdict answer of exactly 150 words passes validation."""
        words = " ".join(["word"] * 150)
        verdict = Verdict(
            answer=words,
            confidence="Medium",
            rationale="Split decision with 3-1 outcome. Financial concerns were significant and require additional planning based on the committee discussion and analysis of the PRD document content.",
            room_outcomes="PRO won"
        )

        conclusion = EnhancedConclusion(
            verdict=verdict,
            role_analyses=[],
            critical_gaps=[],
            recommendations=[]
        )

        result = validate_length_limits(conclusion)

        assert result.is_valid

    def test_role_strengths_too_few_fails_validation(self):
        """Test that < 3 strengths fails validation."""
        role_analysis = RoleAnalysis(
            role_name="CFO",
            strengths=[
                {
                    "description": "Strength 1",
                    "evidence": EvidenceReference(
                        room_id="TPM_vs_CFO",
                        speaker_role="CFO",
                        turn_index=1,
                        quote="Test"
                    )
                },
                {
                    "description": "Strength 2",
                    "evidence": EvidenceReference(
                        room_id="TPM_vs_CFO",
                        speaker_role="CFO",
                        turn_index=2,
                        quote="Test"
                    )
                }
            ],  # Only 2 strengths (< 3)
            weaknesses=[]
        )

        conclusion = EnhancedConclusion(
            verdict=Verdict(
                answer=" ".join(["word"] * 135),
                confidence="Medium",
                rationale="Split decision with 3-1 outcome. Financial concerns were significant and require additional planning based on the committee discussion and analysis of the PRD document content.",
                room_outcomes="PRO won"
            ),
            role_analyses=[role_analysis],
            critical_gaps=[],
            recommendations=[]
        )

        result = validate_length_limits(conclusion)

        assert not result.is_valid
        assert any(e.field == "strengths" for e in result.errors)

    def test_role_strengths_too_many_fails_validation(self):
        """Test that > 5 strengths fails validation."""
        strengths = []
        for i in range(6):  # 6 strengths (> 5)
            strengths.append({
                "description": f"Strength {i}",
                "evidence": EvidenceReference(
                    room_id="TPM_vs_CFO",
                    speaker_role="CFO",
                    turn_index=i,
                    quote=f"Test {i}"
                )
            })

        role_analysis = RoleAnalysis(
            role_name="CFO",
            strengths=strengths,
            weaknesses=[]
        )

        conclusion = EnhancedConclusion(
            verdict=Verdict(
                answer=" ".join(["word"] * 135),
                confidence="Medium",
                rationale="Split decision with 3-1 outcome. Financial concerns were significant and require additional planning based on the committee discussion and analysis of the PRD document content.",
                room_outcomes="PRO won"
            ),
            role_analyses=[role_analysis],
            critical_gaps=[],
            recommendations=[]
        )

        result = validate_length_limits(conclusion)

        assert not result.is_valid
        assert any(e.field == "strengths" for e in result.errors)

    def test_role_weaknesses_too_few_fails_validation(self):
        """Test that < 3 weaknesses fails validation."""
        role_analysis = RoleAnalysis(
            role_name="CFO",
            strengths=[],
            weaknesses=[
                {
                    "description": "Weakness 1",
                    "evidence": EvidenceReference(
                        room_id="TPM_vs_CFO",
                        speaker_role="CFO",
                        turn_index=1,
                        quote="Test"
                    )
                },
                {
                    "description": "Weakness 2",
                    "evidence": EvidenceReference(
                        room_id="TPM_vs_CFO",
                        speaker_role="CFO",
                        turn_index=2,
                        quote="Test"
                    )
                }
            ]  # Only 2 weaknesses (< 3)
        )

        conclusion = EnhancedConclusion(
            verdict=Verdict(
                answer=" ".join(["word"] * 135),
                confidence="Medium",
                rationale="Split decision with 3-1 outcome. Financial concerns were significant and require additional planning based on the committee discussion and analysis of the PRD document content.",
                room_outcomes="PRO won"
            ),
            role_analyses=[role_analysis],
            critical_gaps=[],
            recommendations=[]
        )

        result = validate_length_limits(conclusion)

        assert not result.is_valid
        assert any(e.field == "weaknesses" for e in result.errors)

    def test_role_weaknesses_too_many_fails_validation(self):
        """Test that > 5 weaknesses fails validation."""
        weaknesses = []
        for i in range(6):  # 6 weaknesses (> 5)
            weaknesses.append({
                "description": f"Weakness {i}",
                "evidence": EvidenceReference(
                    room_id="TPM_vs_CFO",
                    speaker_role="CFO",
                    turn_index=i,
                    quote=f"Test {i}"
                )
            })

        role_analysis = RoleAnalysis(
            role_name="CFO",
            strengths=[],
            weaknesses=weaknesses
        )

        conclusion = EnhancedConclusion(
            verdict=Verdict(
                answer=" ".join(["word"] * 135),
                confidence="Medium",
                rationale="Split decision with 3-1 outcome. Financial concerns were significant and require additional planning based on the committee discussion and analysis of the PRD document content.",
                room_outcomes="PRO won"
            ),
            role_analyses=[role_analysis],
            critical_gaps=[],
            recommendations=[]
        )

        result = validate_length_limits(conclusion)

        assert not result.is_valid
        assert any(e.field == "weaknesses" for e in result.errors)

    def test_critical_gaps_too_many_fails_validation(self):
        """Test that > 5 critical gaps fails validation."""
        gaps = []
        for i in range(6):  # 6 gaps (> 5)
            gaps.append(CriticalGap(
                title=f"Gap {i}",
                severity="High",
                description=f"Description {i}",
                sources=["CFO"],
                evidence=[]
            ))

        conclusion = EnhancedConclusion(
            verdict=Verdict(
                answer=" ".join(["word"] * 135),
                confidence="Medium",
                rationale="Split decision with 3-1 outcome. Financial concerns were significant and require additional planning based on the committee discussion and analysis of the PRD document content.",
                room_outcomes="PRO won"
            ),
            role_analyses=[],
            critical_gaps=gaps,
            recommendations=[]
        )

        result = validate_length_limits(conclusion)

        assert not result.is_valid
        assert any(e.field == "critical_gaps" for e in result.errors)

    def test_high_priority_recommendations_too_many_fails_validation(self):
        """Test that > 5 high-priority recommendations fails validation."""
        recommendations = []
        for i in range(6):  # 6 high-priority recommendations (> 5)
            recommendations.append(Recommendation(
                priority="High",
                problem=f"Problem number {i} that is descriptive enough",
                action=f"Action number {i} that is descriptive enough",
                metric=f"Metric number {i} that is measurable enough",
                source_evidence=EvidenceReference(
                    room_id="TPM_vs_CFO",
                    speaker_role="CFO",
                    turn_index=i,
                    quote=f"Test {i}"
                )
            ))

        conclusion = EnhancedConclusion(
            verdict=Verdict(
                answer=" ".join(["word"] * 135),
                confidence="Medium",
                rationale="Split decision with 3-1 outcome. Financial concerns were significant and require additional planning based on the committee discussion and analysis of the PRD document content.",
                room_outcomes="PRO won"
            ),
            role_analyses=[],
            critical_gaps=[],
            recommendations=recommendations
        )

        result = validate_length_limits(conclusion)

        assert not result.is_valid
        assert any(e.field == "recommendations" for e in result.errors)

    def test_exactly_5_critical_gaps_passes_validation(self):
        """Test that exactly 5 critical gaps passes validation."""
        gaps = []
        for i in range(5):
            gaps.append(CriticalGap(
                title=f"Gap {i}",
                severity="High",
                description=f"Description {i}",
                sources=["CFO"],
                evidence=[]
            ))

        conclusion = EnhancedConclusion(
            verdict=Verdict(
                answer=" ".join(["word"] * 135),
                confidence="Medium",
                rationale="Split decision with 3-1 outcome. Financial concerns were significant and require additional planning based on the committee discussion and analysis of the PRD document content.",
                room_outcomes="PRO won"
            ),
            role_analyses=[],
            critical_gaps=gaps,
            recommendations=[]
        )

        result = validate_length_limits(conclusion)

        assert result.is_valid

    def test_exactly_5_high_priority_recommendations_passes_validation(self):
        """Test that exactly 5 high-priority recommendations passes validation."""
        recommendations = []
        for i in range(5):
            recommendations.append(Recommendation(
                priority="High",
                problem=f"Problem number {i} that is descriptive enough",
                action=f"Action number {i} that is descriptive enough",
                metric=f"Metric number {i} that is measurable enough",
                source_evidence=EvidenceReference(
                    room_id="TPM_vs_CFO",
                    speaker_role="CFO",
                    turn_index=i,
                    quote=f"Test {i}"
                )
            ))

        conclusion = EnhancedConclusion(
            verdict=Verdict(
                answer=" ".join(["word"] * 135),
                confidence="Medium",
                rationale="Split decision with 3-1 outcome. Financial concerns were significant and require additional planning based on the committee discussion and analysis of the PRD document content.",
                room_outcomes="PRO won"
            ),
            role_analyses=[],
            critical_gaps=[],
            recommendations=recommendations
        )

        result = validate_length_limits(conclusion)

        assert result.is_valid

    def test_length_compliance_calculation(self):
        """Test that length compliance score is calculated correctly."""
        # Create a conclusion with violations
        role_analysis = RoleAnalysis(
            role_name="CFO",
            strengths=[
                {
                    "description": f"Strength {i}",
                    "evidence": EvidenceReference(
                        room_id="TPM_vs_CFO",
                        speaker_role="CFO",
                        turn_index=i,
                        quote=f"Test quote number {i} that is long enough"
                    )
                }
                for i in range(2)  # Only 2 strengths (< 3)
            ],
            weaknesses=[]
        )

        conclusion = EnhancedConclusion(
            verdict=Verdict(
                answer=" ".join(["word"] * 135),
                confidence="Medium",
                rationale="Split decision with 3-1 outcome. Financial concerns were significant and require additional planning based on the committee discussion and analysis of the PRD document content.",
                room_outcomes="PRO won"
            ),
            role_analyses=[role_analysis],
            critical_gaps=[],
            recommendations=[]
        )

        result = validate_length_limits(conclusion)

        # Should have errors and compliance < 100%
        assert len(result.errors) > 0
        assert result.length_compliance < 100.0
        assert not result.is_valid
