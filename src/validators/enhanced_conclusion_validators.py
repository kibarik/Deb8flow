"""
Enhanced Conclusion Validators for FR-030 and FR-031 compliance.

This module provides validation infrastructure for enhanced conclusion reports:
- FR-030: Length limits (60-second readability)
- FR-031: Evidence reference completeness
- SC-003: 95% recommendation traceability
- SC-007: 100% evidence compliance

Example:
    >>> from src.validators.enhanced_conclusion_validators import validate_enhanced_conclusion
    >>> from src.types.enhanced_conclusion_types import EnhancedConclusion
    >>> result = validate_enhanced_conclusion(enhanced_conclusion)
    >>> if result.is_valid:
    ...     print("All validations passed")
"""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field


__all__ = [
    "ValidationResult",
    "validate_enhanced_conclusion",
    "validate_evidence_references",
    "validate_length_limits",
    "validate_recommendation_format",
]


@dataclass
class ValidationError:
    """A single validation error.

    Attributes:
        category: Validation category (evidence, length, format)
        field: Field that failed validation
        message: Human-readable error message
        severity: Error severity (error, warning)
        location: Optional location string for context
    """
    category: str
    field: str
    message: str
    severity: str = "error"
    location: Optional[str] = None


@dataclass
class ValidationResult:
    """Result of enhanced conclusion validation.

    Attributes:
        is_valid: Whether all validations passed
        errors: List of validation errors
        warnings: List of validation warnings
        compliance_score: Overall compliance percentage (0-100)
        evidence_compliance: Evidence reference compliance percentage
        length_compliance: Length limit compliance percentage
    """
    is_valid: bool
    errors: List[ValidationError] = field(default_factory=list)
    warnings: List[ValidationError] = field(default_factory=list)
    compliance_score: float = 100.0
    evidence_compliance: float = 100.0
    length_compliance: float = 100.0

    def add_error(self, category: str, field: str, message: str, severity: str = "error", location: Optional[str] = None):
        """Add a validation error."""
        error = ValidationError(
            category=category,
            field=field,
            message=message,
            severity=severity,
            location=location
        )
        if severity == "error":
            self.errors.append(error)
        else:
            self.warnings.append(error)

    def calculate_compliance(self, total_evidence_refs: int = 0, total_length_checks: int = 0):
        """Calculate compliance scores.

        Args:
            total_evidence_refs: Total number of evidence references to validate
            total_length_checks: Total number of length checks to validate
        """
        # Evidence compliance (SC-007: 100% required)
        evidence_errors = sum(1 for e in self.errors if e.category == "evidence")
        if total_evidence_refs > 0:
            self.evidence_compliance = ((total_evidence_refs - evidence_errors) / total_evidence_refs) * 100
        else:
            self.evidence_compliance = 100.0 if evidence_errors == 0 else 0.0

        # Length compliance - use actual error count
        length_errors = sum(1 for e in self.errors if e.category == "length")
        # Calculate actual checks performed based on what was validated
        # If we have length_errors, we know at least that many checks were performed
        if length_errors > 0:
            # We know at least 'length_errors' checks were performed and failed
            # Assume at least that many checks total (conservative estimate)
            actual_length_checks = max(total_length_checks, length_errors)
            self.length_compliance = ((actual_length_checks - length_errors) / actual_length_checks) * 100
        elif total_length_checks > 0:
            self.length_compliance = 100.0  # No errors, full compliance
        else:
            self.length_compliance = 100.0 if length_errors == 0 else 0.0

        # Overall compliance
        total_checks = total_evidence_refs + total_length_checks
        total_errors = evidence_errors + length_errors
        if total_checks > 0:
            self.compliance_score = ((total_checks - total_errors) / total_checks) * 100
        else:
            self.compliance_score = 100.0 if len(self.errors) == 0 else 0.0

        # Update is_valid based on errors
        self.is_valid = len(self.errors) == 0


def validate_enhanced_conclusion(conclusion: Any) -> ValidationResult:
    """Validate all aspects of an enhanced conclusion.

    Args:
        conclusion: EnhancedConclusion object to validate

    Returns:
        ValidationResult with all validation errors and warnings
    """
    result = ValidationResult(is_valid=True)

    # Validate evidence references
    evidence_refs = _collect_all_evidence_references(conclusion)
    evidence_result = validate_evidence_references(evidence_refs)
    result.errors.extend(evidence_result.errors)
    result.warnings.extend(evidence_result.warnings)

    # Validate length limits
    length_result = validate_length_limits(conclusion)
    result.errors.extend(length_result.errors)
    result.warnings.extend(length_result.warnings)

    # Validate recommendation format
    format_result = validate_recommendation_format(conclusion)
    result.errors.extend(format_result.errors)
    result.warnings.extend(format_result.warnings)

    # Calculate compliance scores
    result.calculate_compliance(
        total_evidence_refs=len(evidence_refs),
        total_length_checks=_count_length_checks(conclusion)
    )

    return result


def validate_evidence_references(evidence_refs: List[Any]) -> ValidationResult:
    """Validate evidence reference completeness (FR-031, SC-007).

    Args:
        evidence_refs: List of EvidenceReference objects to validate

    Returns:
        ValidationResult with evidence reference validation errors
    """
    result = ValidationResult(is_valid=True)

    for i, ref in enumerate(evidence_refs):
        location = f"evidence_reference_{i}" if i > 0 else "evidence_reference"

        # Check required fields
        if not hasattr(ref, "room_id") or not ref.room_id:
            result.add_error("evidence", "room_id", "room_id is required", location=location)

        if not hasattr(ref, "speaker_role") or not ref.speaker_role:
            result.add_error("evidence", "speaker_role", "speaker_role is required", location=location)

        if not hasattr(ref, "turn_index") or ref.turn_index is None:
            result.add_error("evidence", "turn_index", "turn_index is required", location=location)
        elif hasattr(ref, "turn_index") and ref.turn_index < 0:
            result.add_error("evidence", "turn_index", "turn_index must be >= 0", location=location)

        if not hasattr(ref, "quote") or not ref.quote:
            result.add_error("evidence", "quote", "quote is required", location=location)
        elif hasattr(ref, "quote") and len(ref.quote) > 200:
            result.add_error(
                "evidence",
                "quote",
                f"quote must be <= 200 characters (got {len(ref.quote)})",
                location=location
            )

    # Calculate compliance score
    result.calculate_compliance(total_evidence_refs=len(evidence_refs), total_length_checks=0)
    return result


def validate_length_limits(conclusion: Any) -> ValidationResult:
    """Validate length limits for FR-030 (60-second readability).

    Args:
        conclusion: EnhancedConclusion object to validate

    Returns:
        ValidationResult with length limit validation errors
    """
    result = ValidationResult(is_valid=True)

    # Validate verdict answer word count (120-150 words)
    if hasattr(conclusion, "verdict") and conclusion.verdict:
        verdict = conclusion.verdict
        if hasattr(verdict, "answer"):
            word_count = len(verdict.answer.split())
            if word_count < 120:
                result.add_error(
                    "length",
                    "verdict.answer",
                    f"Verdict answer must be 120-150 words (got {word_count} words)",
                    location="verdict"
                )
            elif word_count > 150:
                result.add_error(
                    "length",
                    "verdict.answer",
                    f"Verdict answer must be 120-150 words (got {word_count} words)",
                    location="verdict"
                )

    # Validate role analyses (3-5 strengths, 3-5 weaknesses each)
    if hasattr(conclusion, "role_analyses"):
        for role_analysis in conclusion.role_analyses:
            role_name = getattr(role_analysis, "role_name", "unknown")

            if hasattr(role_analysis, "strengths"):
                strength_count = len(role_analysis.strengths)
                if strength_count < 3:
                    result.add_error(
                        "length",
                        "strengths",
                        f"{role_name}: Must have 3-5 strengths (got {strength_count})",
                        location=f"role_analysis.{role_name}"
                    )
                elif strength_count > 5:
                    result.add_error(
                        "length",
                        "strengths",
                        f"{role_name}: Must have 3-5 strengths (got {strength_count})",
                        location=f"role_analysis.{role_name}"
                    )

            if hasattr(role_analysis, "weaknesses"):
                weakness_count = len(role_analysis.weaknesses)
                if weakness_count < 3:
                    result.add_error(
                        "length",
                        "weaknesses",
                        f"{role_name}: Must have 3-5 weaknesses (got {weakness_count})",
                        location=f"role_analysis.{role_name}"
                    )
                elif weakness_count > 5:
                    result.add_error(
                        "length",
                        "weaknesses",
                        f"{role_name}: Must have 3-5 weaknesses (got {weakness_count})",
                        location=f"role_analysis.{role_name}"
                    )

    # Validate critical gaps (max 5)
    if hasattr(conclusion, "critical_gaps"):
        gap_count = len(conclusion.critical_gaps)
        if gap_count > 5:
            result.add_error(
                "length",
                "critical_gaps",
                f"Must have max 5 critical gaps (got {gap_count})",
                location="critical_gaps"
            )

    # Validate high-priority recommendations (max 5)
    if hasattr(conclusion, "recommendations"):
        high_priority_count = sum(1 for r in conclusion.recommendations if getattr(r, "priority", "") == "High")
        if high_priority_count > 5:
            result.add_error(
                "length",
                "recommendations",
                f"Must have max 5 high-priority recommendations (got {high_priority_count})",
                location="recommendations"
            )

    # Calculate compliance score
    result.calculate_compliance(total_evidence_refs=0, total_length_checks=_count_length_checks(conclusion))
    return result


def validate_recommendation_format(conclusion: Any) -> ValidationResult:
    """Validate recommendation format (problem → action → metric).

    Args:
        conclusion: EnhancedConclusion object to validate

    Returns:
        ValidationResult with recommendation format validation errors
    """
    result = ValidationResult(is_valid=True)

    if not hasattr(conclusion, "recommendations"):
        return result

    for i, rec in enumerate(conclusion.recommendations):
        location = f"recommendation_{i}" if i > 0 else "recommendation"

        # Check problem field
        if not hasattr(rec, "problem") or not rec.problem:
            result.add_error(
                "format",
                "problem",
                "problem field is required",
                location=location
            )
        elif hasattr(rec, "problem") and len(rec.problem) < 10:
            result.add_error(
                "format",
                "problem",
                "problem must be >= 10 characters",
                location=location
            )

        # Check action field
        if not hasattr(rec, "action") or not rec.action:
            result.add_error(
                "format",
                "action",
                "action field is required",
                location=location
            )
        elif hasattr(rec, "action") and len(rec.action) < 10:
            result.add_error(
                "format",
                "action",
                "action must be >= 10 characters",
                location=location
            )

        # Check metric field
        if not hasattr(rec, "metric") or not rec.metric:
            result.add_error(
                "format",
                "metric",
                "metric field is required",
                location=location
            )
        elif hasattr(rec, "metric"):
            metric = rec.metric
            # Check if metric is measurable (contains numbers or percentages)
            if not any(char.isdigit() for char in metric):
                result.add_warning(
                    "format",
                    "metric",
                    "metric should be measurable (include numbers or percentages)",
                    location=location
                )

    # Calculate compliance score
    result.calculate_compliance(total_evidence_refs=0, total_length_checks=0)
    return result


def _collect_all_evidence_references(conclusion: Any) -> List[Any]:
    """Collect all evidence references from an enhanced conclusion.

    Args:
        conclusion: EnhancedConclusion object

    Returns:
        List of all EvidenceReference objects
    """
    evidence_refs = []

    # Collect from role analyses
    if hasattr(conclusion, "role_analyses"):
        for role_analysis in conclusion.role_analyses:
            if hasattr(role_analysis, "strengths"):
                for strength in role_analysis.strengths:
                    if hasattr(strength, "evidence") and strength.evidence:
                        evidence_refs.append(strength.evidence)

            if hasattr(role_analysis, "weaknesses"):
                for weakness in role_analysis.weaknesses:
                    if hasattr(weakness, "evidence") and weakness.evidence:
                        evidence_refs.append(weakness.evidence)

    # Collect from critical gaps
    if hasattr(conclusion, "critical_gaps"):
        for gap in conclusion.critical_gaps:
            if hasattr(gap, "evidence"):
                for evidence in gap.evidence:
                    evidence_refs.append(evidence)

    # Collect from recommendations
    if hasattr(conclusion, "recommendations"):
        for rec in conclusion.recommendations:
            if hasattr(rec, "source_evidence") and rec.source_evidence:
                evidence_refs.append(rec.source_evidence)

    return evidence_refs


def _count_length_checks(conclusion: Any) -> int:
    """Count the total number of length checks to perform.

    Args:
        conclusion: EnhancedConclusion object

    Returns:
        Total number of length checks
    """
    checks = 0

    # Verdict answer check (1 check)
    checks += 1

    # Role analysis checks (2 per role: strengths + weaknesses)
    if hasattr(conclusion, "role_analyses"):
        checks += len(conclusion.role_analyses) * 2

    # Critical gaps check (1 check)
    checks += 1

    # High-priority recommendations check (1 check)
    checks += 1

    return checks
