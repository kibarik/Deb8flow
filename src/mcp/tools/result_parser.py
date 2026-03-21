"""
Result Parser for LLM Debate Output.

Parses structured entities (WeakPoint, Recommendation, UnclearSection)
from raw LLM debate output with robust error handling.

Based on: TASK-14 requirements
"""

import json
import logging
import re
from dataclasses import dataclass, field
from typing import Any, Optional, Union

# Import models from TASK-10
from src.mcp.models import (
    Recommendation,
    UnclearSection,
    WeakPoint,
)


# =============================================================================
# ENUM TYPES (compatibility layer for current string-based models)
# =============================================================================

class ActionType:
    """Action type for recommendations."""
    ADD = "add"
    CLARIFY = "clarify"
    REMOVE = "remove"
    RESTRUCTURE = "restructure"
    SPLIT = "split"
    MERGE = "merge"


class Priority:
    """Priority level."""
    MUST = "must"
    SHOULD = "should"
    COULD = "could"


class Severity:
    """Severity level."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class WeakPointCategory:
    """Category of weak point."""
    COMPLETENESS = "completeness"
    CLARITY = "clarity"
    CONSISTENCY = "consistency"
    TESTABILITY = "testability"
    SECURITY = "security"
    SCALABILITY = "scalability"
    PERFORMANCE = "performance"


logger = logging.getLogger(__name__)


# =============================================================================
# CONSTANTS
# =============================================================================

# Maximum lengths for content fields
MAX_EVIDENCE_LENGTH = 1000
MAX_SNIPPET_LENGTH = 500
MAX_DESCRIPTION_LENGTH = 2000

# Default confidence scores
DEFAULT_CONFIDENCE = 0.8
MIN_CONFIDENCE = 0.1
MAX_CONFIDENCE = 1.0

# ID format patterns
WP_ID_PATTERN = re.compile(r"WP-\d{3}")
REC_ID_PATTERN = re.compile(r"REC-\d{3}")
UNS_ID_PATTERN = re.compile(r"UNS-\d{3}")


# =============================================================================
# PARSED RESULT DATACLASS
# =============================================================================

@dataclass
class ParsedDebateResult:
    """
    Container for parsed debate results.

    Attributes:
        weak_points: List of parsed WeakPoint objects
        recommendations: List of parsed Recommendation objects
        unclear_sections: List of parsed UnclearSection objects
        parse_errors: List of non-fatal parsing errors encountered
    """

    weak_points: list[WeakPoint] = field(default_factory=list)
    recommendations: list[Recommendation] = field(default_factory=list)
    unclear_sections: list[UnclearSection] = field(default_factory=list)
    parse_errors: list[str] = field(default_factory=list)

    def is_empty(self) -> bool:
        """Check if no entities were parsed."""
        return (
            not self.weak_points
            and not self.recommendations
            and not self.unclear_sections
        )

    def total_entities(self) -> int:
        """Get total count of parsed entities."""
        return (
            len(self.weak_points)
            + len(self.recommendations)
            + len(self.unclear_sections)
        )


# =============================================================================
# CONFIDENCE EXTRACTION
# =============================================================================

def extract_confidence(text: str) -> float:
    """
    Extract confidence score from text.

    Looks for patterns like:
    - "confidence: 0.85"
    - "confidence score: 85%"
    - "85% confident"
    - "high confidence" / "medium confidence" / "low confidence"

    Args:
        text: Text to search for confidence indicators

    Returns:
        Confidence score between 0.1 and 1.0
    """
    text_lower = text.lower()

    # Pattern 1: Explicit decimal confidence (0.0 - 1.0)
    decimal_match = re.search(
        r"confidence[:\s]+(?:score[:\s]*)?([0-9]*\.?[0-9]+)",
        text_lower
    )
    if decimal_match:
        try:
            value = float(decimal_match.group(1))
            # Handle values that might be percentages (e.g., 85 instead of 0.85)
            if value > 1.0:
                value = value / 100.0
            return max(MIN_CONFIDENCE, min(MAX_CONFIDENCE, value))
        except ValueError:
            pass

    # Pattern 2: Percentage confidence (85%)
    percent_match = re.search(r"([0-9]+)%\s*(?:confident|confidence)", text_lower)
    if percent_match:
        try:
            value = float(percent_match.group(1)) / 100.0
            return max(MIN_CONFIDENCE, min(MAX_CONFIDENCE, value))
        except ValueError:
            pass

    # Pattern 3: Qualitative confidence (check more specific first)
    if "extremely confident" in text_lower or "very high confidence" in text_lower:
        return 0.95
    if "very uncertain" in text_lower or "very low confidence" in text_lower:
        return 0.20
    if "very confident" in text_lower or "high confidence" in text_lower:
        return 0.85
    if "somewhat uncertain" in text_lower or "low confidence" in text_lower:
        return 0.40
    if "moderately confident" in text_lower or "medium confidence" in text_lower:
        return 0.65

    return DEFAULT_CONFIDENCE


def extract_evidence_snippet(text: str, max_length: int = MAX_EVIDENCE_LENGTH) -> str:
    """
    Extract an evidence snippet from text.

    Looks for quoted text or key phrases and truncates to max_length.

    Args:
        text: Text to extract evidence from
        max_length: Maximum length of snippet

    Returns:
        Evidence snippet (truncated if needed)
    """
    # Look for quoted text
    quote_match = re.search(r'"([^"]+)"', text)
    if quote_match:
        snippet = quote_match.group(1)
        if len(snippet) <= max_length:
            return snippet

    # Look for "evidence:" prefix
    evidence_match = re.search(
        r"(?:evidence|quote|reference|source)[:\s]+(.+?)(?:\n\n|\n[A-Z]|\Z)",
        text,
        re.DOTALL | re.IGNORECASE
    )
    if evidence_match:
        snippet = evidence_match.group(1).strip()
        if len(snippet) <= max_length:
            return snippet

    # Fall back to first non-empty paragraph
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    if paragraphs:
        snippet = paragraphs[0]
        if len(snippet) > max_length:
            return snippet[:max_length - 3] + "..."
        return snippet

    # Last resort: truncate the whole text
    if len(text) > max_length:
        return text[:max_length - 3] + "..."
    return text


# =============================================================================
# SEVERITY AND CATEGORY EXTRACTION
# =============================================================================

def extract_severity(text: str) -> Severity:
    """
    Extract severity level from text.

    Args:
        text: Text to search for severity indicators

    Returns:
        Severity enum value
    """
    text_lower = text.lower()

    # High severity indicators
    high_indicators = [
        "critical", "severe", "high severity", "high priority",
        "blocking", "blocker", "major issue", "urgent"
    ]
    if any(indicator in text_lower for indicator in high_indicators):
        return Severity.HIGH

    # Low severity indicators
    low_indicators = [
        "minor", "low severity", "low priority", "trivial",
        "nice to have", "small issue", "cosmetic"
    ]
    if any(indicator in text_lower for indicator in low_indicators):
        return Severity.LOW

    return Severity.MEDIUM


def extract_category(text: str) -> WeakPointCategory:
    """
    Extract weak point category from text.

    Args:
        text: Text to search for category indicators

    Returns:
        WeakPointCategory enum value
    """
    text_lower = text.lower()

    # Category keyword mappings
    category_keywords = {
        WeakPointCategory.COMPLETENESS: [
            "missing", "incomplete", "lacking", "not specified",
            "no information", "absent", "omitted"
        ],
        WeakPointCategory.CLARITY: [
            "unclear", "ambiguous", "confusing", "vague",
            "imprecise", "not clear", "hard to understand"
        ],
        WeakPointCategory.CONSISTENCY: [
            "inconsistent", "contradiction", "conflicts with",
            "contradictory", "doesn't match", "discrepancy"
        ],
        WeakPointCategory.TESTABILITY: [
            "untestable", "cannot be verified", "not verifiable",
            "how to test", "verification needed", "testing concern"
        ],
        WeakPointCategory.SECURITY: [
            "security", "vulnerability", "exploit", "authentication",
            "authorization", "injection", "xss", "csrf"
        ],
        WeakPointCategory.SCALABILITY: [
            "scalability", "scale", "performance at scale",
            "load handling", "throughput", "bottleneck"
        ],
    }

    # Check each category's keywords
    for category, keywords in category_keywords.items():
        if any(keyword in text_lower for keyword in keywords):
            return category

    return WeakPointCategory.CLARITY  # Default


def extract_action_type(text: str) -> ActionType:
    """
    Extract action type for recommendation from text.

    Args:
        text: Text to search for action indicators

    Returns:
        ActionType enum value
    """
    text_lower = text.lower()

    # Action keyword mappings
    action_keywords = {
        ActionType.ADD: [
            "add", "include", "create", "introduce", "insert",
            "append", "new section", "additional"
        ],
        ActionType.CLARIFY: [
            "clarify", "explain", "elaborate", "specify",
            "make clear", "define more clearly", "detail"
        ],
        ActionType.REMOVE: [
            "remove", "delete", "eliminate", "cut",
            "exclude", "drop", "omit"
        ],
        ActionType.RESTRUCTURE: [
            "restructure", "reorganize", "rearrange",
            "change order", "reorder", "restructure"
        ],
        ActionType.SPLIT: [
            "split", "divide", "separate", "break into",
            "break down", "split into sections"
        ],
        ActionType.MERGE: [
            "merge", "combine", "consolidate", "join",
            "unify", "integrate sections"
        ],
    }

    # Check each action's keywords
    for action, keywords in action_keywords.items():
        if any(keyword in text_lower for keyword in keywords):
            return action

    return ActionType.CLARIFY  # Default


def extract_priority(text: str) -> Priority:
    """
    Extract priority level from text.

    Args:
        text: Text to search for priority indicators

    Returns:
        Priority enum value
    """
    text_lower = text.lower()

    # Must priority indicators
    must_indicators = [
        "must", "required", "critical", "mandatory",
        "essential", "blocking", "blocker"
    ]
    if any(indicator in text_lower for indicator in must_indicators):
        return Priority.MUST

    # Could priority indicators
    could_indicators = [
        "could", "optional", "nice to have", "if time permits",
        "consider", "may want to", "suggested"
    ]
    if any(indicator in text_lower for indicator in could_indicators):
        return Priority.COULD

    return Priority.SHOULD  # Default


# =============================================================================
# SECTION EXTRACTION
# =============================================================================

def extract_section_reference(text: str) -> str:
    """
    Extract section reference from text.

    Looks for patterns like:
    - "section 2.1"
    - "Section 3.4.1"
    - "API-001"
    - "in the Authentication section"

    Args:
        text: Text to search for section references

    Returns:
        Section identifier or "general" if not found
    """
    # Pattern: "section X.Y" or "Section X.Y.Z"
    section_match = re.search(
        r"(?:section|sec\.?)\s*(\d+(?:\.\d+)*)",
        text,
        re.IGNORECASE
    )
    if section_match:
        return section_match.group(1)

    # Pattern: Identifier like "API-001", "AUTH-123"
    id_match = re.search(r"\b([A-Z]{2,}-\d{3})\b", text)
    if id_match:
        return id_match.group(1)

    # Pattern: Named section like "Authentication section"
    named_match = re.search(
        r"(?:in\s+(?:the\s+)?|under\s+)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+section",
        text
    )
    if named_match:
        return named_match.group(1)

    return "general"


# =============================================================================
# JSON PARSING HELPERS
# =============================================================================

def try_parse_json(text: str) -> Optional[Union[dict, list]]:
    """
    Attempt to parse JSON from text, with fallback extraction.

    Args:
        text: Text that may contain JSON

    Returns:
        Parsed JSON object or None
    """
    # Try direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try to extract JSON from text
    # Look for JSON objects
    json_obj_match = re.search(r"\{[\s\S]*\}", text)
    if json_obj_match:
        try:
            return json.loads(json_obj_match.group(0))
        except json.JSONDecodeError:
            pass

    # Look for JSON arrays
    json_arr_match = re.search(r"\[[\s\S]*\]", text)
    if json_arr_match:
        try:
            return json.loads(json_arr_match.group(0))
        except json.JSONDecodeError:
            pass

    return None


def safe_get(data: Optional[dict], *keys, default=None) -> Any:
    """
    Safely get value from dictionary using first matching key.

    Unlike nested traversal, this tries each key at the top level
    and returns the value of the first key that exists.

    Args:
        data: Dictionary to get value from
        *keys: Keys to try (returns first match)
        default: Default value if no key found

    Returns:
        Value at first matching key or default
    """
    if data is None:
        return default

    if not isinstance(data, dict):
        return default

    # Try each key at the top level
    for key in keys:
        if key in data:
            return data[key]

    return default


# =============================================================================
# WEAK POINT PARSING
# =============================================================================

def parse_weak_point_from_dict(
    data: dict,
    id_counter: int,
    errors: list[str]
) -> Optional[WeakPoint]:
    """
    Parse a WeakPoint from a dictionary.

    Args:
        data: Dictionary with weak point data
        id_counter: Counter for auto-generating ID
        errors: List to append parsing errors to

    Returns:
        WeakPoint object or None if parsing failed
    """
    try:
        # Generate or use provided ID
        wp_id = data.get("id", f"WP-{id_counter:03d}")
        if not WP_ID_PATTERN.match(wp_id):
            wp_id = f"WP-{id_counter:03d}"

        # Extract required fields with fallbacks
        description = safe_get(data, "description", "issue", "problem", default="")
        if not description:
            description = safe_get(data, "text", "content", default="No description provided")

        # Truncate long descriptions
        if len(description) > MAX_DESCRIPTION_LENGTH:
            description = description[:MAX_DESCRIPTION_LENGTH - 3] + "..."

        section = safe_get(data, "section", "location", default="general")
        recommendation = safe_get(data, "recommendation", "suggestion", "fix", default="Review and address the identified concern")

        # Extract or infer category
        category_str = safe_get(data, "category", default="")
        if category_str:
            try:
                category = WeakPointCategory(category_str.lower())
            except ValueError:
                category = extract_category(description)
        else:
            category = extract_category(description)

        # Extract or infer severity
        severity_str = safe_get(data, "severity", default="")
        if severity_str:
            try:
                severity = Severity(severity_str.lower())
            except ValueError:
                severity = extract_severity(description)
        else:
            severity = extract_severity(description)

        # Extract evidence and confidence
        evidence = safe_get(data, "evidence", "quote", default="")
        if not evidence:
            evidence = extract_evidence_snippet(description)

        confidence = safe_get(data, "confidence", default=None)
        if confidence is not None:
            try:
                confidence = float(confidence)
                confidence = max(MIN_CONFIDENCE, min(MAX_CONFIDENCE, confidence))
            except (ValueError, TypeError):
                confidence = extract_confidence(description)
        else:
            confidence = extract_confidence(description)

        return WeakPoint(
            section=str(section),
            severity=severity.value if hasattr(severity, 'value') else str(severity),
            description=description,
            recommendation=recommendation
        )

    except Exception as e:
        errors.append(f"Failed to parse weak point: {str(e)}")
        logger.warning(f"Failed to parse weak point: {e}")
        return None


def parse_weak_points_from_text(
    text: str,
    max_count: int = 15,
    errors: Optional[list[str]] = None
) -> list[WeakPoint]:
    """
    Parse weak points from text using pattern matching.

    Looks for structured patterns and natural language indicators.

    Args:
        text: Text to parse
        max_count: Maximum number of weak points to extract
        errors: List to append parsing errors to

    Returns:
        List of WeakPoint objects
    """
    if errors is None:
        errors = []

    weak_points = []

    # Try JSON parsing first
    json_data = try_parse_json(text)
    if json_data:
        if isinstance(json_data, dict):
            wp_list = safe_get(json_data, "weak_points", "weakPoints", "issues", default=[])
        elif isinstance(json_data, list):
            wp_list = json_data
        else:
            wp_list = []

        if wp_list:
            for i, wp_data in enumerate(wp_list[:max_count], 1):
                if isinstance(wp_data, dict):
                    wp = parse_weak_point_from_dict(wp_data, i, errors)
                    if wp:
                        weak_points.append(wp)
            return weak_points

    # Pattern-based extraction from text
    # Look for numbered issues or bullet points with weakness indicators

    # Pattern 1: Numbered weak points
    numbered_pattern = re.compile(
        r"(?:weakness|issue|problem|concern)[:\s]*"
        r"(\d+)[.\)]\s*"
        r"(.+?)(?=(?:weakness|issue|problem|concern)[:\s]*\d+[.\)]|\Z)",
        re.DOTALL | re.IGNORECASE
    )

    for match in numbered_pattern.finditer(text):
        if len(weak_points) >= max_count:
            break

        content = match.group(2).strip()
        if len(content) < 10:
            continue

        wp_id = f"WP-{len(weak_points) + 1:03d}"
        weak_points.append(WeakPoint(
            section=extract_section_reference(content),
            severity=extract_severity(content).value if hasattr(extract_severity(content), 'value') else str(extract_severity(content)),
            description=content[:MAX_DESCRIPTION_LENGTH],
            recommendation="Review and address the identified concern"
        ))

    # Pattern 2: Bullet points with issue indicators
    if len(weak_points) < max_count:
        bullet_pattern = re.compile(
            r"[-*]\s*"
            r"(.+?(?:issue|problem|weakness|concern|gap|missing|unclear|ambiguous).+?)"
            r"(?=\n[-*]|\n\n|\Z)",
            re.DOTALL | re.IGNORECASE
        )

        for match in bullet_pattern.finditer(text):
            if len(weak_points) >= max_count:
                break

            content = match.group(1).strip()
            if len(content) < 10:
                continue

            wp_id = f"WP-{len(weak_points) + 1:03d}"
            weak_points.append(WeakPoint(
                section=extract_section_reference(content),
                severity=extract_severity(content).value if hasattr(extract_severity(content), 'value') else str(extract_severity(content)),
                description=content[:MAX_DESCRIPTION_LENGTH],
                recommendation="Review and address the identified concern"
            ))

    return weak_points


# =============================================================================
# RECOMMENDATION PARSING
# =============================================================================

def parse_recommendation_from_dict(
    data: dict,
    id_counter: int,
    errors: list[str]
) -> Optional[Recommendation]:
    """
    Parse a Recommendation from a dictionary.

    Args:
        data: Dictionary with recommendation data
        id_counter: Counter for auto-generating ID
        errors: List to append parsing errors to

    Returns:
        Recommendation object or None if parsing failed
    """
    try:
        # Generate or use provided ID
        rec_id = data.get("id", f"REC-{id_counter:03d}")
        if not REC_ID_PATTERN.match(rec_id):
            rec_id = f"REC-{id_counter:03d}"

        # Extract required fields with fallbacks
        description = safe_get(
            data, "description", "action", "recommendation",
            default="No description provided"
        )
        if len(description) > MAX_DESCRIPTION_LENGTH:
            description = description[:MAX_DESCRIPTION_LENGTH - 3] + "..."

        section = safe_get(data, "section", "location", default="general")
        rationale = safe_get(
            data, "rationale", "reason", "why", "justification",
            default="Based on analysis findings"
        )

        # Extract or infer action type
        action_str = safe_get(data, "action", "type", default="")
        if action_str:
            try:
                action = ActionType(action_str.lower())
            except ValueError:
                action = extract_action_type(description)
        else:
            action = extract_action_type(description)

        # Extract or infer priority
        priority_str = safe_get(data, "priority", default="")
        if priority_str:
            try:
                priority = Priority(priority_str.lower())
            except ValueError:
                priority = extract_priority(description)
        else:
            priority = extract_priority(description)

        return Recommendation(
            section=str(section),
            priority=priority.value if hasattr(priority, 'value') else str(priority),
            action=description,
            rationale=rationale
        )

    except Exception as e:
        errors.append(f"Failed to parse recommendation: {str(e)}")
        logger.warning(f"Failed to parse recommendation: {e}")
        return None


def parse_recommendations_from_text(
    text: str,
    max_count: int = 10,
    errors: Optional[list[str]] = None
) -> list[Recommendation]:
    """
    Parse recommendations from text using pattern matching.

    Args:
        text: Text to parse
        max_count: Maximum number of recommendations to extract
        errors: List to append parsing errors to

    Returns:
        List of Recommendation objects
    """
    if errors is None:
        errors = []

    recommendations = []

    # Try JSON parsing first
    json_data = try_parse_json(text)
    if json_data:
        if isinstance(json_data, dict):
            rec_list = safe_get(
                json_data, "recommendations", "suggestions", "actions",
                default=[]
            )
        elif isinstance(json_data, list):
            rec_list = json_data
        else:
            rec_list = []

        if rec_list:
            for i, rec_data in enumerate(rec_list[:max_count], 1):
                if isinstance(rec_data, dict):
                    rec = parse_recommendation_from_dict(rec_data, i, errors)
                    if rec:
                        recommendations.append(rec)
            return recommendations

    # Pattern-based extraction
    # Look for "recommend", "should", "suggest" patterns

    # Pattern 1: Explicit recommendations
    rec_pattern = re.compile(
        r"(?:recommendation|suggest|should)[:\s]*"
        r"(\d+)[.\)]?\s*"
        r"(.+?)(?=(?:recommendation|suggest|should)[:\s]*\d+[.\)]?|\Z)",
        re.DOTALL | re.IGNORECASE
    )

    for match in rec_pattern.finditer(text):
        if len(recommendations) >= max_count:
            break

        content = match.group(2).strip()
        if len(content) < 10:
            continue

        rec_id = f"REC-{len(recommendations) + 1:03d}"
        recommendations.append(Recommendation(
            section=extract_section_reference(content),
            priority=extract_priority(content).value if hasattr(extract_priority(content), 'value') else str(extract_priority(content)),
            action=content[:MAX_DESCRIPTION_LENGTH],
            rationale="Based on analysis findings"
        ))

    # Pattern 2: Bullet points with recommendation indicators
    if len(recommendations) < max_count:
        bullet_pattern = re.compile(
            r"[-*]\s*"
            r"(.+?(?:recommend|suggest|should|consider|add|include|clarify).+?)"
            r"(?=\n[-*]|\n\n|\Z)",
            re.DOTALL | re.IGNORECASE
        )

        for match in bullet_pattern.finditer(text):
            if len(recommendations) >= max_count:
                break

            content = match.group(1).strip()
            if len(content) < 10:
                continue

            rec_id = f"REC-{len(recommendations) + 1:03d}"
            recommendations.append(Recommendation(
                section=extract_section_reference(content),
                priority=extract_priority(content).value if hasattr(extract_priority(content), 'value') else str(extract_priority(content)),
                action=content[:MAX_DESCRIPTION_LENGTH],
                rationale="Based on analysis findings"
            ))

    return recommendations


# =============================================================================
# UNCLEAR SECTION PARSING
# =============================================================================

def parse_unclear_section_from_dict(
    data: dict,
    id_counter: int,
    errors: list[str]
) -> Optional[UnclearSection]:
    """
    Parse an UnclearSection from a dictionary.

    Args:
        data: Dictionary with unclear section data
        id_counter: Counter for auto-generating ID
        errors: List to append parsing errors to

    Returns:
        UnclearSection object or None if parsing failed
    """
    try:
        # Generate or use provided ID
        uns_id = data.get("id", f"UNS-{id_counter:03d}")
        if not UNS_ID_PATTERN.match(uns_id):
            uns_id = f"UNS-{id_counter:03d}"

        # Extract required fields with fallbacks
        content_snippet = safe_get(
            data, "content_snippet", "snippet", "content", "text",
            default=""
        )
        if not content_snippet:
            content_snippet = "Content needs clarification"

        # Enforce max length
        if len(content_snippet) > MAX_SNIPPET_LENGTH:
            content_snippet = content_snippet[:MAX_SNIPPET_LENGTH - 3] + "..."

        section = safe_get(data, "section", "location", default="general")
        question = safe_get(
            data, "question", "clarification_needed", "what_is_unclear",
            default="This section needs clarification"
        )
        impact = safe_get(
            data, "impact", "consequence", "why_matters",
            default="May lead to implementation issues"
        )

        return UnclearSection(
            section=str(section),
            issue=question,
            suggested_clarification=impact
        )

    except Exception as e:
        errors.append(f"Failed to parse unclear section: {str(e)}")
        logger.warning(f"Failed to parse unclear section: {e}")
        return None


def parse_unclear_sections_from_text(
    text: str,
    max_count: int = 10,
    errors: Optional[list[str]] = None
) -> list[UnclearSection]:
    """
    Parse unclear sections from text using pattern matching.

    Args:
        text: Text to parse
        max_count: Maximum number of unclear sections to extract
        errors: List to append parsing errors to

    Returns:
        List of UnclearSection objects
    """
    if errors is None:
        errors = []

    unclear_sections = []

    # Try JSON parsing first
    json_data = try_parse_json(text)
    if json_data:
        if isinstance(json_data, dict):
            uns_list = safe_get(
                json_data, "unclear_sections", "unclearSections",
                "ambiguities", default=[]
            )
        elif isinstance(json_data, list):
            uns_list = json_data
        else:
            uns_list = []

        if uns_list:
            for i, uns_data in enumerate(uns_list[:max_count], 1):
                if isinstance(uns_data, dict):
                    uns = parse_unclear_section_from_dict(uns_data, i, errors)
                    if uns:
                        unclear_sections.append(uns)
            return unclear_sections

    # Pattern-based extraction
    # Look for unclear/ambiguous indicators

    # Pattern 1: Explicit unclear sections
    unclear_pattern = re.compile(
        r"(?:unclear|ambiguous|confusing|needs clarification)[:\s]*"
        r"(\d+)?[.\)]?\s*"
        r"(.+?)(?=(?:unclear|ambiguous|confusing|needs clarification)[:\s]*(?:\d+)?[.\)]?|\Z)",
        re.DOTALL | re.IGNORECASE
    )

    for match in unclear_pattern.finditer(text):
        if len(unclear_sections) >= max_count:
            break

        content = match.group(2).strip()
        if len(content) < 5:
            continue

        uns_id = f"UNS-{len(unclear_sections) + 1:03d}"
        snippet = content[:MAX_SNIPPET_LENGTH]

        unclear_sections.append(UnclearSection(
            section=extract_section_reference(content),
            issue="This section needs clarification",
            suggested_clarification="May lead to implementation issues"
        ))

    # Pattern 2: Questions indicating unclear sections
    if len(unclear_sections) < max_count:
        question_pattern = re.compile(
            r"[-*]?\s*(?:question|q)[:\s]*"
            r"(.+?\?)"
            r"(?=\n[-*]|\n\n|\Z)",
            re.DOTALL | re.IGNORECASE
        )

        for match in question_pattern.finditer(text):
            if len(unclear_sections) >= max_count:
                break

            question = match.group(1).strip()
            if len(question) < 5:
                continue

            uns_id = f"UNS-{len(unclear_sections) + 1:03d}"

            unclear_sections.append(UnclearSection(
                section="general",
                issue=question,
                suggested_clarification="Needs stakeholder input"
            ))

    return unclear_sections


# =============================================================================
# DIALOGUE PARSING
# =============================================================================

def parse_dialogue_message(
    message: dict,
    wp_counter: int,
    rec_counter: int,
    uns_counter: int,
    config: Optional[dict] = None,
    errors: Optional[list[str]] = None
) -> tuple[list[WeakPoint], list[Recommendation], list[UnclearSection], int, int, int]:
    """
    Parse a single dialogue message for entities.

    Args:
        message: Dialogue message dict with 'speaker', 'content', 'stage'
        wp_counter: Current weak point counter
        rec_counter: Current recommendation counter
        uns_counter: Current unclear section counter
        config: Optional configuration for limits
        errors: List to append parsing errors to

    Returns:
        Tuple of (weak_points, recommendations, unclear_sections,
                  new_wp_counter, new_rec_counter, new_uns_counter)
    """
    if errors is None:
        errors = []

    config = config or {}
    limits = config.get("analysis", {}).get("limits", {})
    max_wp = limits.get("weak_points_max", 15)
    max_rec = limits.get("recommendations_max", 10)
    max_uns = limits.get("unclear_sections_max", 10)

    content = message.get("content", "")
    speaker = message.get("speaker", "")
    stage = message.get("stage", "")
    content_lower = content.lower()

    weak_points = []
    recommendations = []
    unclear_sections = []

    # CON speakers typically identify weaknesses
    if speaker in ["CON", "DevLead", "QA", "Security"]:
        # Look for weakness indicators
        weakness_indicators = [
            "weakness", "issue", "problem", "concern", "gap",
            "missing", "unclear", "ambiguous", "untestable"
        ]

        if any(indicator in content_lower for indicator in weakness_indicators):
            if wp_counter <= max_wp:
                wp = WeakPoint(
                    section=extract_section_reference(content),
                    severity=extract_severity(content).value if hasattr(extract_severity(content), 'value') else str(extract_severity(content)),
                    description=f"Issue identified in {stage}",
                    recommendation="Review and address the identified concern"
                )
                weak_points.append(wp)
                wp_counter += 1

    # Look for recommendation indicators from any speaker
    rec_indicators = ["recommend", "suggest", "should", "consider"]
    if any(indicator in content_lower for indicator in rec_indicators):
        if rec_counter <= max_rec:
            rec = Recommendation(
                section=extract_section_reference(content),
                priority=extract_priority(content).value if hasattr(extract_priority(content), 'value') else str(extract_priority(content)),
                action=f"Recommendation from {speaker}",
                rationale="Based on debate analysis"
            )
            recommendations.append(rec)
            rec_counter += 1

    # Look for unclear/ambiguous indicators
    if "unclear" in content_lower or "ambiguous" in content_lower:
        if uns_counter <= max_uns:
            uns = UnclearSection(
                section=extract_section_reference(content),
                issue="This section needs clarification",
                suggested_clarification="May lead to implementation issues"
            )
            unclear_sections.append(uns)
            uns_counter += 1

    return (
        weak_points,
        recommendations,
        unclear_sections,
        wp_counter,
        rec_counter,
        uns_counter,
    )


# =============================================================================
# MAIN PARSER FUNCTIONS
# =============================================================================

def parse_debate_output(
    output: Union[str, list[dict]],
    config: Optional[dict] = None
) -> ParsedDebateResult:
    """
    Main entry point for parsing LLM debate output.

    Handles both raw text output and structured dialogue lists.
    Gracefully handles partial/malformed output and returns
    empty lists (not errors) for missing sections.

    Args:
        output: LLM output (text or list of dialogue messages)
        config: Optional configuration for parsing limits

    Returns:
        ParsedDebateResult with all parsed entities
    """
    result = ParsedDebateResult()

    # Handle empty/None input
    if not output:
        return result

    config = config or {}

    # Handle string input
    if isinstance(output, str):
        if not output.strip():
            return result

        result.weak_points = parse_weak_points_from_text(
            output,
            config.get("analysis", {}).get("limits", {}).get("weak_points_max", 15),
            result.parse_errors
        )
        result.recommendations = parse_recommendations_from_text(
            output,
            config.get("analysis", {}).get("limits", {}).get("recommendations_max", 10),
            result.parse_errors
        )
        result.unclear_sections = parse_unclear_sections_from_text(
            output,
            config.get("analysis", {}).get("limits", {}).get("unclear_sections_max", 10),
            result.parse_errors
        )
        return result

    # Handle dialogue list input
    if isinstance(output, list):
        wp_counter = 1
        rec_counter = 1
        uns_counter = 1

        for message in output:
            if not isinstance(message, dict):
                result.parse_errors.append(f"Skipping non-dict message: {type(message)}")
                continue

            wps, recs, unss, wp_counter, rec_counter, uns_counter = parse_dialogue_message(
                message,
                wp_counter,
                rec_counter,
                uns_counter,
                config,
                result.parse_errors
            )

            result.weak_points.extend(wps)
            result.recommendations.extend(recs)
            result.unclear_sections.extend(unss)

        return result

    # Unknown input type
    result.parse_errors.append(f"Unknown output type: {type(output)}")
    return result


def parse_debate_output_safe(
    output: Union[str, list[dict], None],
    config: Optional[dict] = None
) -> ParsedDebateResult:
    """
    Safe wrapper that never raises exceptions.

    Always returns a valid ParsedDebateResult, even on complete failure.

    Args:
        output: LLM output (any type)
        config: Optional configuration

    Returns:
        ParsedDebateResult (empty if parsing fails completely)
    """
    try:
        return parse_debate_output(output, config)
    except Exception as e:
        logger.error(f"Safe parse failed: {e}")
        result = ParsedDebateResult()
        result.parse_errors.append(f"Parser exception: {str(e)}")
        return result


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Main functions
    "parse_debate_output",
    "parse_debate_output_safe",
    "ParsedDebateResult",
    # Weak point parsing
    "parse_weak_points_from_text",
    "parse_weak_point_from_dict",
    # Recommendation parsing
    "parse_recommendations_from_text",
    "parse_recommendation_from_dict",
    # Unclear section parsing
    "parse_unclear_sections_from_text",
    "parse_unclear_section_from_dict",
    # Extraction helpers
    "extract_confidence",
    "extract_evidence_snippet",
    "extract_severity",
    "extract_category",
    "extract_action_type",
    "extract_priority",
    "extract_section_reference",
    # JSON helpers
    "try_parse_json",
    "safe_get",
]
