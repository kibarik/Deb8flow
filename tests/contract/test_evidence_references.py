"""
Contract tests for evidence reference validation (FR-031, SC-007).

These tests enforce 100% evidence compliance requirement:
- All evidence references must have complete fields
- room_id, speaker_role, turn_index, quote all required
- Quote must be <= 200 characters
"""

import pytest
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from src.validators.enhanced_conclusion_validators import (
    ValidationResult,
    validate_evidence_references,
)
from src.types.enhanced_conclusion_types import EvidenceReference


class TestEvidenceReferenceValidation:
    """Contract tests for evidence reference validation."""

    def test_complete_evidence_reference_passes_validation(self):
        """Test that a complete evidence reference passes validation."""
        evidence_ref = EvidenceReference(
            room_id="TPM_vs_CFO",
            speaker_role="CFO",
            turn_index=2,
            quote="The financial model is overly optimistic."
        )

        result = validate_evidence_references([evidence_ref])

        assert result.is_valid
        assert len(result.errors) == 0
        assert result.evidence_compliance == 100.0

    def test_missing_room_id_fails_validation(self):
        """Test that missing room_id fails validation."""
        # Create a reference-like object without room_id
        class IncompleteRef:
            def __init__(self):
                self.speaker_role = "CFO"
                self.turn_index = 2
                self.quote = "Test quote"

        evidence_ref = IncompleteRef()
        result = validate_evidence_references([evidence_ref])

        assert not result.is_valid
        assert any(e.field == "room_id" for e in result.errors)

    def test_missing_speaker_role_fails_validation(self):
        """Test that missing speaker_role fails validation."""
        class IncompleteRef:
            def __init__(self):
                self.room_id = "TPM_vs_CFO"
                self.turn_index = 2
                self.quote = "Test quote"

        evidence_ref = IncompleteRef()
        result = validate_evidence_references([evidence_ref])

        assert not result.is_valid
        assert any(e.field == "speaker_role" for e in result.errors)

    def test_missing_turn_index_fails_validation(self):
        """Test that missing turn_index fails validation."""
        class IncompleteRef:
            def __init__(self):
                self.room_id = "TPM_vs_CFO"
                self.speaker_role = "CFO"
                self.quote = "Test quote"

        evidence_ref = IncompleteRef()
        result = validate_evidence_references([evidence_ref])

        assert not result.is_valid
        assert any(e.field == "turn_index" for e in result.errors)

    def test_negative_turn_index_fails_validation(self):
        """Test that negative turn_index fails validation at Pydantic level."""
        # Pydantic model already validates turn_index >= 0
        # This test documents that behavior
        import pytest
        with pytest.raises(Exception):  # Pydantic ValidationError
            EvidenceReference(
                room_id="TPM_vs_CFO",
                speaker_role="CFO",
                turn_index=-1,
                quote="Test quote"
            )

    def test_missing_quote_fails_validation(self):
        """Test that missing quote fails validation."""
        class IncompleteRef:
            def __init__(self):
                self.room_id = "TPM_vs_CFO"
                self.speaker_role = "CFO"
                self.turn_index = 2

        evidence_ref = IncompleteRef()
        result = validate_evidence_references([evidence_ref])

        assert not result.is_valid
        assert any(e.field == "quote" for e in result.errors)

    def test_quote_over_200_chars_is_auto_truncated(self):
        """Test that quote over 200 characters is auto-truncated by Pydantic."""
        long_quote = "This is a very long quote that exceeds the maximum allowed length of 200 characters. " * 3

        evidence_ref = EvidenceReference(
            room_id="TPM_vs_CFO",
            speaker_role="CFO",
            turn_index=2,
            quote=long_quote
        )

        # Pydantic auto-truncates to 200 chars, so validator should pass
        assert len(evidence_ref.quote) <= 200

        result = validate_evidence_references([evidence_ref])
        assert result.is_valid  # Should pass since quote was truncated

    def test_empty_quote_fails_validation(self):
        """Test that empty quote fails validation at Pydantic level."""
        # Pydantic model may or may not allow empty string
        # Test the validator behavior with empty quote
        evidence_ref = EvidenceReference(
            room_id="TPM_vs_CFO",
            speaker_role="CFO",
            turn_index=2,
            quote=""
        )

        result = validate_evidence_references([evidence_ref])

        # Validator checks for empty quote
        assert not result.is_valid
        assert any(e.field == "quote" for e in result.errors)

    def test_multiple_evidence_references_all_validated(self):
        """Test that all evidence references are validated."""
        evidence_refs = [
            EvidenceReference(
                room_id="TPM_vs_CFO",
                speaker_role="CFO",
                turn_index=2,
                quote="Financial model lacks conservative scenarios."
            ),
            EvidenceReference(
                room_id="TPM_vs_CTO",
                speaker_role="CTO",
                turn_index=1,
                quote="Technical approach is sound."
            ),
            EvidenceReference(
                room_id="TPM_vs_BDM",
                speaker_role="BDM",
                turn_index=3,
                quote="Market timing is favorable."
            ),
        ]

        result = validate_evidence_references(evidence_refs)

        assert result.is_valid
        assert len(result.errors) == 0
        assert result.evidence_compliance == 100.0

    def test_multiple_evidence_references_one_invalid_fails_all(self):
        """Test that one invalid evidence reference causes validation failure."""
        evidence_refs = [
            EvidenceReference(
                room_id="TPM_vs_CFO",
                speaker_role="CFO",
                turn_index=2,
                quote="Financial model lacks conservative scenarios."
            ),
        ]

        # Add an incomplete reference using a simple class
        class IncompleteRef:
            def __init__(self):
                self.room_id = "TPM_vs_CTO"
                self.speaker_role = "CTO"
                self.turn_index = 1
                self.quote = ""  # Invalid: empty quote

        evidence_refs.append(IncompleteRef())

        result = validate_evidence_references(evidence_refs)

        assert not result.is_valid
        assert result.evidence_compliance < 100.0

    def test_100_percent_compliance_required(self):
        """Test that 100% evidence compliance is enforced (SC-007)."""
        # Create 10 evidence references, 1 invalid
        evidence_refs = []
        for i in range(10):
            if i == 5:
                # Invalid reference - use simple class
                class IncompleteRef:
                    def __init__(self, idx):
                        self.room_id = "TPM_vs_CFO"
                        self.speaker_role = "CFO"
                        self.turn_index = 2
                        self.quote = ""  # Empty quote

                evidence_refs.append(IncompleteRef(i))
            else:
                evidence_refs.append(EvidenceReference(
                    room_id=f"TPM_vs_ROLE{i}",
                    speaker_role=f"ROLE{i}",
                    turn_index=i,
                    quote=f"Quote {i}"
                ))

        result = validate_evidence_references(evidence_refs)

        # Should fail because not 100% compliant
        assert not result.is_valid
        assert result.evidence_compliance == 90.0  # 9/10 = 90%

    def test_compliance_score_calculation(self):
        """Test that compliance score is calculated correctly."""
        evidence_refs = []
        for i in range(5):
            evidence_refs.append(EvidenceReference(
                room_id="TPM_vs_CFO",
                speaker_role="CFO",
                turn_index=2,
                quote=f"Quote {i}"
            ))

        result = validate_evidence_references(evidence_refs)

        assert result.evidence_compliance == 100.0
        assert result.compliance_score == 100.0

    def test_evidence_reference_validation_result_structure(self):
        """Test that ValidationResult has correct structure."""
        result = ValidationResult(is_valid=True)

        assert hasattr(result, "is_valid")
        assert hasattr(result, "errors")
        assert hasattr(result, "warnings")
        assert hasattr(result, "compliance_score")
        assert hasattr(result, "evidence_compliance")
        assert hasattr(result, "length_compliance")
