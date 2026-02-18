"""
Conclusion generator for product committee.

This adapter generates executive summary with error categorization
and actionable recommendations.
"""

import logging
import re
from typing import List, Dict, Any, Optional

from ....shared.debate.domain.entities import DebateRoom
from ....shared.debate.domain.services import categorize_error
from ....shared.debate.domain.value_objects import Speaker


logger = logging.getLogger(__name__)


class ConclusionGenerator:
    """Generates executive summary conclusions for committee runs."""

    def generate_conclusion(
        self,
        question: str,
        rooms: List[DebateRoom],
        metadata: Dict[str, Any]
    ) -> str:
        """
        Generate a concise conclusion markdown summary.

        Args:
            question: Committee question
            rooms: All debate room results
            metadata: Run metadata

        Returns:
            Markdown conclusion content
        """
        lines = [
            f"# Conclusion",
            f"",
            f"**Generated:** {metadata.get('end_time', 'N/A')}",
            f"",
            f"---",
            f"",
            f"## Committee Question",
            f"",
            f"{question}",
            f"",
            f"---",
            f"",
            f"## Executive Summary",
            f"",
        ]

        # Count winners and results
        successful_rooms = [r for r in rooms if r.is_successful]
        failed_rooms = [r for r in rooms if r.status.value == "failed"]
        tpm_wins = sum(1 for r in successful_rooms if r.verdict and r.verdict.winner == Speaker.PRO)
        opponent_wins = len(successful_rooms) - tpm_wins

        lines.append(f"After {len(successful_rooms)} successful debate rooms:")
        lines.append(f"- **TPM victories:** {tpm_wins}/{len(successful_rooms)}")
        lines.append(f"- **Opponent victories:** {opponent_wins}/{len(successful_rooms)}")
        lines.append("")

        # If no successful rooms, provide error analysis
        if not successful_rooms and failed_rooms:
            lines.extend(self._generate_error_analysis(failed_rooms))
            return '\n'.join(lines)

        # Overall verdict
        if tpm_wins > opponent_wins:
            overall_verdict = "TPM (PRO) position prevails"
        elif opponent_wins > tpm_wins:
            overall_verdict = "Opponents (CON) positions prevail"
        else:
            overall_verdict = "No clear consensus"

        lines.extend([
            f"**Overall Verdict:** {overall_verdict}",
            f"",
            f"---",
            f"",
            f"## Room Results Summary",
            f""
        ])

        for room in rooms:
            if room.is_successful:
                winner = room.verdict.winner.value if room.verdict else "Unknown"
                explanation = room.verdict.explanation if room.verdict else ""
                first_sentence = self._extract_first_sentence(explanation)

                lines.extend([
                    f"### {room.room_id.value}",
                    f"**Winner:** {winner}",
                    f"**Summary:** {first_sentence}",
                    f""
                ])

        # Footer
        lines.extend([
            f"---",
            f"",
            f"*For detailed dialogue and analysis, see final_report.md*",
            f""
        ])

        return '\n'.join(lines)

    def _generate_error_analysis(self, failed_rooms: List[DebateRoom]) -> List[str]:
        """Generate detailed error analysis section for failed runs."""
        lines = [
            f"**Status:** All debate rooms failed to complete.",
            f"",
            f"---",
            f"",
            f"## Error Analysis",
            f""
        ]

        # Categorize errors
        error_patterns: Dict[str, List[str]] = {}
        for room in failed_rooms:
            if room.error:
                category = categorize_error(room.error)
                error_patterns.setdefault(category, []).append(room.room_id.value)

        for error_type, room_list in error_patterns.items():
            lines.append(f"### {error_type}")
            lines.append(f"Affected rooms: {', '.join(room_list)}")
            lines.append("")

            # Add specific recommendations based on error type
            lines.extend(self._get_error_recommendations(error_type))
            lines.append("")

        # Show sample errors for debugging
        lines.extend([
            f"### Sample Error Details",
            f""
        ])
        for room in failed_rooms[:2]:  # Show first 2 errors
            lines.extend([
                f"**{room.room_id.value}:**",
                f"```",
                room.error or "No error message",
                "```",
                ""
            ])

        # Next steps
        lines.extend([
            f"---",
            f"",
            f"## Next Steps",
            f"",
            "1. **Check logs above** for detailed error messages",
            "2. **Verify LLM configuration** - check API keys and endpoints",
            "3. **Test with single room first** - reduce concurrency to isolate issues",
            "4. **Check role prompt files** - ensure all `.txt` files in `prompts/roles/` exist",
            "5. **Review PRD document** - ensure it's readable and contains sufficient content",
            ""
        ])

        return lines

    def _get_error_recommendations(self, error_type: str) -> List[str]:
        """Get specific recommendations for an error type."""
        recommendations = {
            "Regex/Pattern Error": [
                "**Recommendation:** Check regular expressions in filename sanitization.",
                "- Ensure character ranges are properly formatted",
                "- Escape special characters like `-` when used literally",
                "- Test regex patterns: `python3 -c 'import re; re.test()'`"
            ],
            "Timeout": [
                "**Recommendation:** Debate rooms are taking too long to complete.",
                "- Check if LLM API is responding slowly",
                "- Consider increasing timeout in configuration",
                "- Reduce debate complexity or number of rounds"
            ],
            "JSON Parsing Error": [
                "**Recommendation:** LLM responses are not valid JSON.",
                "- Check LLM prompts are requesting proper JSON format",
                "- Ensure system prompt specifies JSON output only",
                "- Consider using structured output if available"
            ],
            "LLM/API Error": [
                "**Recommendation:** LLM API issues detected.",
                "- Check API key is valid and has sufficient quota",
                "- Verify network connectivity to LLM provider",
                "- Check service status page for outages"
            ],
            "Other Error": [
                "**Recommendation:** Unknown error - check logs for details.",
                "- Review full error stack trace",
                "- Check file permissions and disk space",
                "- Verify Python environment and dependencies"
            ]
        }
        return recommendations.get(error_type, ["**Recommendation:** Review error details and logs."])

    def _extract_first_sentence(self, text: str, max_length: int = 200) -> str:
        """Extract the first meaningful sentence from text."""
        if not text:
            return "No explanation provided"

        # Split by sentence terminators
        sentences = re.split(r'[.!?]', text)
        first_sentence = sentences[0].strip() if sentences else text

        if len(first_sentence) > max_length:
            first_sentence = first_sentence[:max_length] + "..."

        return first_sentence
