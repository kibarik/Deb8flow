"""
Enhanced Conclusion Writer for Committee Debates.

This module formats and writes the enhanced conclusion report to markdown,
following the specification structure and supporting UTF-8 encoding.
"""

import logging
from pathlib import Path
from typing import Optional

from src.types.enhanced_conclusion_types import EnhancedConclusion


class EnhancedConclusionWriter:
    """Write enhanced conclusion reports to markdown format.

    Takes an EnhancedConclusion object and formats it into markdown
    following the specification structure with UTF-8 encoding support.

    Example:
        >>> writer = EnhancedConclusionWriter()
        >>> writer.write(conclusion, output_path)
        >>> # Writes enhanced_conclusion_types.EnhancedConclusion to markdown
    """

    def __init__(self):
        """Initialize EnhancedConclusionWriter."""
        self.logger = logging.getLogger(self.__class__.__name__)

    def write(
        self,
        conclusion: EnhancedConclusion,
        output_path: Path,
        run_id: Optional[str] = None
    ) -> Path:
        """Write enhanced conclusion to markdown file.

        Args:
            conclusion: EnhancedConclusion object to write
            output_path: Directory to write the conclusion file
            run_id: Optional run ID for the filename

        Returns:
            Path to the written conclusion file
        """
        self.logger.info(f"Writing enhanced conclusion to {output_path}")

        # Generate filename
        if run_id:
            filename = f"enhanced_conclusion_{run_id}.md"
        else:
            filename = "enhanced_conclusion.md"

        output_file = output_path / filename

        # Generate markdown content
        markdown_content = self._format_markdown(conclusion)

        # Write to file with UTF-8 encoding
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(markdown_content)

        self.logger.info(f"Enhanced conclusion written to {output_file}")
        return output_file

    def _format_markdown(self, conclusion: EnhancedConclusion) -> str:
        """Format enhanced conclusion as markdown.

        Args:
            conclusion: EnhancedConclusion object to format

        Returns:
            Formatted markdown string
        """
        lines = []

        # Header
        lines.append("# Enhanced Committee Conclusion Report")
        lines.append("")

        # Verdict Section
        lines.append("## Verdict")
        lines.append("")
        lines.append(f"**Answer:** {conclusion.verdict.answer}")
        lines.append("")
        lines.append(f"**Confidence:** {conclusion.verdict.confidence}")
        lines.append("")
        lines.append(f"**Room Outcomes:** {conclusion.verdict.room_outcomes}")
        lines.append("")
        lines.append(f"**Rationale:** {conclusion.verdict.rationale}")
        lines.append("")

        # Role Analysis Section
        lines.append("## Role-Based Analysis")
        lines.append("")

        for role_analysis in conclusion.role_analyses:
            lines.append(f"### {role_analysis.role_name}")
            lines.append("")

            if role_analysis.strengths:
                lines.append("**Strengths:**")
                lines.append("")
                for strength in role_analysis.strengths:
                    lines.append(f"- {strength.description}")
                    lines.append(f"  - *Source:* {strength.evidence.room_id}, {strength.evidence.speaker_role} (Turn {strength.evidence.turn_index})")
                    lines.append(f"  - *Evidence:* \"{strength.evidence.quote}\"")
                    lines.append("")
            else:
                lines.append("**Strengths:** None")
                lines.append("")

            if role_analysis.weaknesses:
                lines.append("**Weaknesses:**")
                lines.append("")
                for weakness in role_analysis.weaknesses:
                    lines.append(f"- {weakness.description}")
                    lines.append(f"  - *Source:* {weakness.evidence.room_id}, {weakness.evidence.speaker_role} (Turn {weakness.evidence.turn_index})")
                    lines.append(f"  - *Evidence:* \"{weakness.evidence.quote}\"")
                    lines.append("")
            else:
                lines.append("**Weaknesses:** None")
                lines.append("")

        # Critical Gaps Section
        lines.append("## Critical Gaps")
        lines.append("")

        if conclusion.critical_gaps:
            for gap in conclusion.critical_gaps:
                lines.append(f"### {gap.title} ({gap.severity})")
                lines.append("")
                lines.append(gap.description)
                lines.append("")
                lines.append(f"**Sources:** {', '.join(gap.sources)}")
                lines.append("")
                if gap.evidence:
                    lines.append("**Evidence:**")
                    for evidence in gap.evidence:
                        lines.append(f"- {evidence.room_id}, {evidence.speaker_role} (Turn {evidence.turn_index})")
                        lines.append(f"  > \"{evidence.quote}\"")
                    lines.append("")
        else:
            lines.append("No critical gaps identified.")
            lines.append("")

        # Recommendations Section
        lines.append("## Recommendations")
        lines.append("")

        if conclusion.recommendations:
            # Group by priority
            high_priority = [r for r in conclusion.recommendations if r.priority == "High"]
            medium_priority = [r for r in conclusion.recommendations if r.priority == "Medium"]
            low_priority = [r for r in conclusion.recommendations if r.priority == "Low"]

            if high_priority:
                lines.append("### High Priority")
                lines.append("")
                for rec in high_priority:
                    lines.append(f"**Problem:** {rec.problem}")
                    lines.append("")
                    lines.append(f"**Action:** {rec.action}")
                    lines.append("")
                    lines.append(f"**Metric:** {rec.metric}")
                    lines.append("")
                    lines.append(f"*Source: {rec.source_evidence.room_id}, {rec.source_evidence.speaker_role} (Turn {rec.source_evidence.turn_index})*")
                    lines.append("")

            if medium_priority:
                lines.append("### Medium Priority")
                lines.append("")
                for rec in medium_priority:
                    lines.append(f"**Problem:** {rec.problem}")
                    lines.append("")
                    lines.append(f"**Action:** {rec.action}")
                    lines.append("")
                    lines.append(f"**Metric:** {rec.metric}")
                    lines.append("")

            if low_priority:
                lines.append("### Low Priority")
                lines.append("")
                for rec in low_priority:
                    lines.append(f"**Problem:** {rec.problem}")
                    lines.append("")
                    lines.append(f"**Action:** {rec.action}")
                    lines.append("")
                    lines.append(f"**Metric:** {rec.metric}")
                    lines.append("")
        else:
            lines.append("No recommendations generated.")
            lines.append("")

        return "\n".join(lines)

    def format_to_string(self, conclusion: EnhancedConclusion) -> str:
        """Format enhanced conclusion to markdown string.

        Args:
            conclusion: EnhancedConclusion object to format

        Returns:
            Formatted markdown string
        """
        return self._format_markdown(conclusion)
