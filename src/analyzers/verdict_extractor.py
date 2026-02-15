"""
Verdict Extractor for Enhanced Conclusion Pipeline.

This module extracts the verdict from committee debate final_report.md
with confidence level calculation per FR-029.

FR-029 Confidence Formula:
- Unanimous (4-0 or 0-4) = High
- Split (3-1 or 1-3) = Medium
- Tie (2-2) = Low
- Strong contradictions reduce by 1 level

Example:
    >>> from src.analyzers.verdict_extractor import VerdictExtractor
    >>> extractor = VerdictExtractor(llm_config)
    >>> verdict = extractor.extract(final_report_text)
"""

import re
import logging
from typing import Dict, Any, List

from src.analyzers.base_analyzer import EnhancedAnalyzer
from src.types.enhanced_conclusion_types import Verdict


__all__ = ["VerdictExtractor"]


class VerdictExtractor(EnhancedAnalyzer):
    """Extract verdict from committee debate final_report.md.

    Parses room outcomes and calculates confidence level per FR-029:
    - Unanimous (4-0 or 0-4) = High
    - Split (3-1 or 1-3) = Medium
    - Tie (2-2) = Low
    - Strong contradictions reduce by 1 level

    Attributes:
        logger: Logger instance for tracking extraction progress

    Example:
        >>> extractor = VerdictExtractor(llm_config)
        >>> verdict = extractor(final_report_text)
    """

    def __init__(self, llm_config=None):
        """Initialize the verdict extractor.

        Args:
            llm_config: LLM configuration (inherited from EnhancedAnalyzer)
        """
        super().__init__(llm_config)
        self.logger = logging.getLogger(self.__class__.__name__)

    def __call__(self, final_report_text: str) -> Verdict:
        """Extract verdict with confidence calculation.

        Args:
            final_report_text: Full text of final_report.md

        Returns:
            Verdict object with answer, confidence, rationale, room_outcomes

        Raises:
            ValueError: If required fields cannot be extracted
        """
        self.logger.info("Extracting verdict from final_report.md")

        # Extract room outcomes
        room_outcomes = self._extract_room_outcomes(final_report_text)

        # Extract judge rationales
        judge_rationales = self._extract_judge_rationales(final_report_text)

        # Calculate confidence
        confidence = self._calculate_confidence(room_outcomes, judge_rationales)

        # Generate verdict answer using LLM
        verdict_data = self._generate_verdict_answer(
            final_report_text, room_outcomes, confidence
        )

        return Verdict(**verdict_data)

    def _extract_room_outcomes(self, final_report_text: str) -> Dict[str, str]:
        """Extract winner for each room from final_report.md.

        Args:
            final_report_text: Full text of final_report.md

        Returns:
            Dict mapping room_id to winner (e.g., {"TPM_vs_CPO": "CON"})
        """
        room_outcomes = {}

        # Pattern to match room headers
        # Example: "## TPM vs CPO" or "## Room 1: TPM vs CPO"
        room_pattern = r'##\s*(?:Room\s+\d+:\s*)?(TPM\s+vs\s+(CPO|CFO|CTO|BDM))'

        # Find all room sections
        rooms = re.finditer(room_pattern, final_report_text, re.IGNORECASE)

        for match in rooms:
            room_name = match.group(1).replace(" ", "_")  # "TPM_vs_CPO"
            room_start = match.end()

            # Find next room header or end of document
            next_room = re.search(room_pattern, final_report_text[room_start:], re.IGNORECASE)
            room_end = room_start + next_room.start() if next_room else len(final_report_text)

            room_section = final_report_text[room_start:room_end]

            # Extract winner from room section
            winner = self._extract_winner_from_room(room_section)
            room_outcomes[room_name] = winner

        self.logger.info(f"Extracted {len(room_outcomes)} room outcomes: {room_outcomes}")
        return room_outcomes

    def _extract_winner_from_room(self, room_section: str) -> str:
        """Extract winner from a single room section.

        Looks for patterns like:
        - "Winner: CON" or "Победитель: CON"
        - "The judge rules in favor of CON"
        - "Verdict: CON wins"

        Args:
            room_section: Room section text from final_report.md

        Returns:
            Winner role name (PRO, CON, etc.) or "UNCLEAR" if cannot determine
        """
        # Try explicit "Winner:" pattern
        winner_pattern = r'(?:Winner|Победитель)\s*:\s*(PRO|CON|TPM|CPO|CFO|CTO|BDM)'
        match = re.search(winner_pattern, room_section, re.IGNORECASE)
        if match:
            return match.group(1).upper()

        # Try "rules in favor of" pattern
        favor_pattern = r'rules?\s+in\s+favor\s+of\s+(PRO|CON)'
        match = re.search(favor_pattern, room_section, re.IGNORECASE)
        if match:
            return match.group(1).upper()

        # Try "Verdict:" pattern
        verdict_pattern = r'Verdict\s*:?\s*(?:\w+\s+)?(?:wins?|victorious)\s*\((PRO|CON)\)'
        match = re.search(verdict_pattern, room_section, re.IGNORECASE)
        if match:
            return match.group(1).upper()

        # Default: log warning and return "UNCLEAR"
        self.logger.warning("Could not determine winner from room section")
        return "UNCLEAR"

    def _calculate_confidence(
        self,
        room_outcomes: Dict[str, str],
        judge_rationales: List[str]
    ) -> str:
        """Calculate confidence level per FR-029.

        Formula:
        - Unanimous (4-0 or 0-4) = High
        - Split (3-1 or 1-3) = Medium
        - Tie (2-2) = Low
        - Strong contradictions reduce by 1 level

        Args:
            room_outcomes: Dict mapping room_id to winner
            judge_rationales: List of judge rationale texts

        Returns:
            "High", "Medium", or "Low"
        """
        if not room_outcomes:
            return "Low"

        # Count PRO vs CON wins
        pro_wins = sum(1 for winner in room_outcomes.values() if winner == "PRO")
        con_wins = sum(1 for winner in room_outcomes.values() if winner == "CON")
        total_rooms = len(room_outcomes)

        # For committee debates, TPM is always PRO position
        # So we count TPM wins as PRO wins
        tpm_wins = pro_wins

        # Calculate base confidence
        if total_rooms == 0:
            base_confidence = "Low"
        elif tpm_wins == total_rooms or tpm_wins == 0:
            # Unanimous (4-0 or 0-4)
            base_confidence = "High"
        elif abs(tpm_wins - total_rooms / 2) <= 0.5:
            # Tie (2-2)
            base_confidence = "Low"
        else:
            # Split (3-1 or 1-3)
            base_confidence = "Medium"

        # Check for contradictions and reduce confidence
        has_contradictions = self._detect_contradictions(judge_rationales)

        if has_contradictions:
            if base_confidence == "High":
                return "Medium"
            elif base_confidence == "Medium":
                return "Low"

        return base_confidence

    def _extract_judge_rationales(self, final_report_text: str) -> List[str]:
        """Extract judge rationales from final_report.md.

        Looks for sections containing judge explanations/verdicts.

        Args:
            final_report_text: Full text of final_report.md

        Returns:
            List of judge rationale texts
        """
        rationales = []

        # Pattern to match judge verdict sections
        # Example: "### Judge's Verdict" or "### Verdict"
        verdict_pattern = r'###\s*(?:Judge[\'s]?\s+)?Verdict'

        # Find all verdict sections
        verdicts = re.finditer(verdict_pattern, final_report_text, re.IGNORECASE)

        for match in verdicts:
            verdict_start = match.end()

            # Find next section header or end of document
            next_section = re.search(r'^#+\s', final_report_text[verdict_start:], re.MULTILINE)
            verdict_end = verdict_start + next_section.start() if next_section else len(final_report_text)

            verdict_section = final_report_text[verdict_start:verdict_end].strip()

            if verdict_section:
                rationales.append(verdict_section)

        self.logger.info(f"Extracted {len(rationales)} judge rationales")
        return rationales

    def _detect_contradictions(self, rationales: List[str]) -> bool:
        """Detect if judge rationales contain strong contradictions.

        Looks for contradiction indicators like:
        - "however", "but", "although" (contrast)
        - "contradicts", "inconsistent", "conflicting" (explicit contradiction)
        - "on the other hand", "conversely" (opposing views)

        Args:
            rationales: List of judge rationale texts

        Returns:
            True if contradictions detected, False otherwise
        """
        if not rationales:
            return False

        # Combine all rationales
        combined = " ".join(rationales).lower()

        # Contradiction keywords
        strong_contradictions = ["contradicts", "inconsistent", "conflicting"]
        contrast_words = ["however", "but", "although", "conversely", "on the other hand"]

        # Count strong contradictions
        strong_count = sum(1 for word in strong_contradictions if word in combined)

        # Count contrast words (but require 2+ to avoid false positives)
        contrast_count = sum(1 for word in contrast_words if word in combined)

        # Return True if strong contradictions OR 2+ contrast words
        return strong_count >= 1 or contrast_count >= 2

    def _generate_verdict_answer(
        self,
        final_report_text: str,
        room_outcomes: Dict[str, str],
        confidence: str
    ) -> Dict[str, Any]:
        """Generate verdict answer using LLM.

        Args:
            final_report_text: Full text of final_report.md
            room_outcomes: Dict of room outcomes
            confidence: Calculated confidence level

        Returns:
            Dict with answer, confidence, rationale, room_outcomes
        """
        # Load prompt template
        prompt_template = self._load_prompt('verdict_extraction_prompt.md')

        # Format room outcomes summary
        room_outcomes_summary = self._format_room_outcomes(room_outcomes)

        # Format prompt with variables
        formatted_prompt = self._format_prompt(
            prompt_template,
            final_report_text=final_report_text,
            room_outcomes_summary=room_outcomes_summary,
            confidence_level=confidence
        )

        # Invoke LLM with retry
        llm_response = self._invoke_with_retry(
            self._create_structured_chain(formatted_prompt, Verdict),
            {"input": formatted_prompt}
        )

        # Convert to dict if it's a Pydantic model
        if hasattr(llm_response, 'model_dump'):
            return llm_response.model_dump()
        elif isinstance(llm_response, dict):
            return llm_response
        else:
            raise ValueError(f"Unexpected LLM response type: {type(llm_response)}")

    def _format_room_outcomes(self, room_outcomes: Dict[str, str]) -> str:
        """Format room outcomes as summary string.

        Args:
            room_outcomes: Dict mapping room_id to winner

        Returns:
            Formatted summary string
        """
        if not room_outcomes:
            return "No room outcomes found"

        # Count PRO and CON wins
        pro_wins = sum(1 for winner in room_outcomes.values() if winner == "PRO")
        con_wins = sum(1 for winner in room_outcomes.values() if winner == "CON")

        # Format summary
        if pro_wins > con_wins:
            return f"PRO won {pro_wins}/{len(room_outcomes)} rooms"
        elif con_wins > pro_wins:
            return f"CON won {con_wins}/{len(room_outcomes)} rooms"
        else:
            return f"Tie ({pro_wins}-{con_wins})"
