"""
Role Analyzer for Enhanced Committee Conclusion.

This module extracts role-based analysis from committee debate final_report.md,
identifying strengths and weaknesses for each participating role with complete
evidence references per FR-031.
"""

import json
import logging
import re
from typing import List, Dict, Any

from src.analyzers.base_analyzer import EnhancedAnalyzer
from src.types.enhanced_conclusion_types import (
    RoleAnalysis,
    EvidenceReference,
    Strength,
    Weakness,
)


class RoleAnalyzer(EnhancedAnalyzer):
    """Extract role-based analysis from committee debate final_report.md.

    For each role (TPM, CPO, CFO, CTO, BDM):
    - Extract 3-5 strengths with supporting evidence
    - Extract 3-5 weaknesses with supporting evidence
    - Each strength/weakness must have complete evidence reference (FR-031)

    Example:
        >>> analyzer = RoleAnalyzer(llm_config=None)
        >>> role_analyses = analyzer(final_report_text)
        >>> for analysis in role_analyses:
        ...     print(f"{analysis.role_name}: {len(analysis.strengths)} strengths")
    """

    def __init__(self, llm_config=None):
        """Initialize RoleAnalyzer.

        Args:
            llm_config: LLM configuration (optional, uses default if None)
        """
        super().__init__(llm_config)
        self.logger = logging.getLogger(self.__class__.__name__)

        # Standard committee roles
        self._committee_roles = {"TPM", "CPO", "CFO", "CTO", "BDM"}

    def __call__(self, final_report_text: str) -> List[RoleAnalysis]:
        """Extract role-based analysis from final_report.md.

        Args:
            final_report_text: Full text of final_report.md

        Returns:
            List of RoleAnalysis objects (one per participating role)
        """
        self.logger.info("Extracting role-based analysis from final_report.md")

        # Identify participating roles
        participating_roles = self._identify_participating_roles(final_report_text)

        # Extract role analyses
        role_analyses = []
        for role in participating_roles:
            analysis = self._extract_role_analysis(final_report_text, role)
            role_analyses.append(analysis)

        self.logger.info(f"Extracted {len(role_analyses)} role analyses")
        return role_analyses

    def _identify_participating_roles(self, final_report_text: str) -> List[str]:
        """Identify all roles participating in the debate.

        Args:
            final_report_text: Full text of final_report.md

        Returns:
            List of role names (e.g., ["TPM", "CPO", "CFO", "CTO", "BDM"])
        """
        # Find all mentioned roles in room headers
        # Pattern returns tuple of captured groups
        room_pattern = r'##\s*(?:Room\s+\d+:\s*)?TPM\s+vs\s+(CPO|CFO|CTO|BDM)'
        matches = re.findall(room_pattern, final_report_text, re.IGNORECASE)

        # Extract mentioned roles
        mentioned_roles = {"TPM"}  # TPM is always in committee debates
        for opponent in matches:
            # matches is a list of strings (the second group)
            mentioned_roles.add(opponent.upper())

        # Return only standard committee roles that were mentioned
        participating = [role for role in self._committee_roles if role in mentioned_roles]

        self.logger.info(f"Identified participating roles: {participating}")
        return participating

    def _extract_role_analysis(
        self, final_report_text: str, role: str
    ) -> RoleAnalysis:
        """Extract analysis for a single role.

        Args:
            final_report_text: Full text of final_report.md
            role: Role name to analyze (e.g., "TPM", "CPO")

        Returns:
            RoleAnalysis object with strengths and weaknesses
        """
        # Load prompt template
        prompt_template = self._load_prompt("role_analysis_prompt.md")

        # Format prompt with role and final_report_text
        formatted_prompt = self._format_prompt(
            prompt_template, role=role, final_report_text=final_report_text
        )

        # Invoke LLM with retry
        llm_response = self._invoke_with_retry(
            self._create_text_chain(), {"input": formatted_prompt}
        )

        # Parse response
        analysis_data = self._parse_role_analysis_response(llm_response, role)

        # Create RoleAnalysis object (validates 3-5 limit)
        return RoleAnalysis(**analysis_data)

    def _parse_role_analysis_response(
        self, response: str, role: str
    ) -> Dict[str, Any]:
        """Parse LLM response into RoleAnalysis data.

        Args:
            response: JSON response from LLM
            role: Role name for this analysis

        Returns:
            Dict with role_name, strengths, weaknesses
        """
        # Clean response (remove markdown code blocks)
        cleaned = response.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            cleaned = "\n".join(lines).strip()

        # Parse JSON
        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse role analysis response: {e}")
            raise ValueError(f"Invalid JSON from LLM: {e}")

        # Validate structure
        if "strengths" not in data or "weaknesses" not in data:
            raise ValueError("Missing required fields in LLM response")

        # Convert to proper format
        strengths = [
            Strength(
                description=s["description"],
                evidence=EvidenceReference(**s["evidence"]),
            )
            for s in data["strengths"][:5]
        ]

        weaknesses = [
            Weakness(
                description=w["description"],
                evidence=EvidenceReference(**w["evidence"]),
            )
            for w in data["weaknesses"][:5]
        ]

        return {"role_name": role, "strengths": strengths, "weaknesses": weaknesses}

    def _extract_evidence_reference(
        self, final_report_text: str, role: str, quote_text: str
    ) -> EvidenceReference:
        """Extract complete evidence reference for a quote.

        Args:
            final_report_text: Full text of final_report.md
            role: Role being analyzed
            quote_text: Quote to locate in final_report

        Returns:
            EvidenceReference with room_id, speaker_role, turn_index, quote
        """
        # Find the quote in final_report_text
        # This is a simplified implementation - production would use more sophisticated matching

        # Try to find the room containing this quote
        room_id = self._find_room_for_quote(final_report_text, quote_text)

        # Try to identify the speaker
        speaker_role = self._identify_speaker_for_quote(
            final_report_text, quote_text, role
        )

        # Estimate turn index (simplified)
        turn_index = self._estimate_turn_index(final_report_text, quote_text)

        # Truncate quote to 200 chars
        truncated_quote = quote_text[:200] if len(quote_text) > 200 else quote_text

        return EvidenceReference(
            room_id=room_id, speaker_role=speaker_role, turn_index=turn_index, quote=truncated_quote
        )

    def _find_room_for_quote(self, final_report_text: str, quote: str) -> str:
        """Find which room contains a given quote.

        Args:
            final_report_text: Full text of final_report.md
            quote: Quote to locate

        Returns:
            Room ID (e.g., "TPM_vs_CPO")
        """
        # Split into room sections
        room_pattern = r"##\s*(TPM\s+vs\s+(CPO|CFO|CTO|BDM))"
        rooms = list(re.finditer(room_pattern, final_report_text, re.IGNORECASE))

        for i, match in enumerate(rooms):
            room_start = match.end()
            room_name = match.group(1).replace(" ", "_")

            # Find next room or end of document
            next_room = rooms[i + 1] if i + 1 < len(rooms) else None
            room_end = next_room.start() if next_room else len(final_report_text)

            room_section = final_report_text[room_start:room_end]

            # Check if quote is in this room
            if quote[:50] in room_section:
                return room_name

        # Default: return "UNKNOWN"
        return "UNKNOWN"

    def _identify_speaker_for_quote(
        self, final_report_text: str, quote: str, context_role: str
    ) -> str:
        """Identify speaker for a quote.

        Args:
            final_report_text: Full text of final_report.md
            quote: Quote to analyze
            context_role: Role being analyzed

        Returns:
            Speaker role name
        """
        # Simplified: use context role as default
        # In production, would parse speaker labels from transcript
        return context_role

    def _estimate_turn_index(self, final_report_text: str, quote: str) -> int:
        """Estimate turn index for a quote.

        Args:
            final_report_text: Full text of final_report.md
            quote: Quote to analyze

        Returns:
            Estimated turn index (non-negative integer)
        """
        # Simplified: count occurrence position
        # In production, would parse actual turn numbers from transcript
        position = final_report_text.find(quote[:50])
        if position == -1:
            return 0

        # Rough estimate: assume ~500 chars per turn
        return max(0, position // 500)
