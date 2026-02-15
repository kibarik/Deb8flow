"""
Conclusion Writer Utility for markdown report generation.

This module provides utility functions for writing conclusion reports
as markdown files with proper formatting and UTF-8 encoding.
"""

import logging
import re
from pathlib import Path
from typing import Dict, Any, Optional, List

from src.types.conclusion_types import (
    ConclusionData,
    VerdictSummary,
    QAPair,
    TPMAnalysis,
    TPMWeakness,
    Recommendation,
    ConclusionMetadata,
)


__all__ = ["ConclusionWriter"]


class ConclusionWriter:
    """Utility class for writing conclusion reports as markdown.

    Provides methods for formatting and writing conclusion reports
    to markdown files with UTF-8 encoding.

    Attributes:
        logger: Logger instance for tracking operations
    """

    # Markdown formatting patterns
    SECTION_HEADER = re.compile(r"^(#+) (.+)$", re.MULTILINE)
    BOLD_PATTERN = re.compile(r"\*\*(.+?)\*\*", re.MULTILINE)

    def __init__(self):
        """Initialize conclusion writer with logger."""
        self.logger = logging.getLogger(self.__class__.__name__)

    def write(self, output_path: str, conclusion_data: ConclusionData,
                 parsed_conclusion: Optional[Dict[str, Any]] = None) -> str:
        """Write conclusion report to markdown file.

        Args:
            output_path: Path to output markdown file
            conclusion_data: Original conclusion data structure
            parsed_conclusion: Optional parsed conclusion from LLM response

        Returns:
            Path to generated markdown file

        Raises:
            ValueError: If output directory doesn't exist
            IOError: If file cannot be written
        """
        self.logger.info(f"Writing conclusion report to: {output_path}")

        # Ensure output directory exists
        output_file = Path(output_path)
        if not output_file.parent.exists():
            raise ValueError(f"Output directory does not exist: {output_file.parent}")

        # Use parsed conclusion if provided, otherwise use original
        data_to_write = parsed_conclusion if parsed_conclusion else conclusion_data

        # Generate markdown content
        markdown_content = self._format_conclusion_report(data_to_write)

        # Write file with UTF-8 encoding
        try:
            output_file.write_text(markdown_content, encoding="utf-8")
            self.logger.info(f"Successfully wrote conclusion report: {output_file}")
        except IOError as e:
            raise IOError(f"Failed to write conclusion report: {e}")

        return str(output_file)

    def _format_conclusion_report(self, data: ConclusionData) -> str:
        """Format conclusion data as markdown report.

        Args:
            data: ConclusionData structure

        Returns:
            Formatted markdown content
        """
        sections = []

        # Title and metadata
        sections.append(f"# Debate Conclusion Report")

        # Add horizontal rule
        sections.append("")
        sections.append(f"**Generated:** {data['metadata']['generated_at']}")

        # Debate Question
        sections.append("")
        sections.append("## Debate Question")
        sections.append("")
        sections.append(data['debate_question'])

        # Judge's Verdict
        sections.append("")
        sections.append("## Judge's Verdict")
        sections.append("")
        verdict = data['verdict']
        sections.append(f"**Winner:** {verdict['winner']} ({verdict['winner_position']})")
        sections.append(f"**Justification:** {verdict['justification']}")
        if verdict.get('confidence'):
            sections.append(f"**Confidence:** {verdict['confidence']:.2f}")

        # Key Question-Answer Pairs
        sections.append("")
        sections.append("## Key Question-Answer Pairs")
        sections.append("")
        qa_summary = data.get('qa_summary', [])
        for i, qa in enumerate(qa_summary[:10], 1):
            sections.append(f"### Q&A {i}")
            sections.append("")
            sections.append(f"**Question:** {qa['question']}")
            sections.append(f"**Answer:** {qa['answer']}")
            sections.append(f"**Stage:** {qa['stage']}")
            sections.append(f"**Speaker:** {qa['speaker']}")
            sections.append(f"**Validated:** {'Yes' if qa['validated'] else 'No'}")
            sections.append(f"**Priority:** {qa['priority']}")

        # TPM Position Analysis
        sections.append("")
        sections.append("## TPM Position Analysis")
        sections.append("")
        tpm_analysis = data.get('tpm_analysis', {})
        sections.append(f"### Position Summary")
        sections.append("")
        sections.append(tpm_analysis.get('position_summary', 'No position summary available'))

        # Identified Weaknesses
        weaknesses = tpm_analysis.get('weaknesses', [])
        if weaknesses:
            sections.append("")
            sections.append("### Identified Weaknesses")
            sections.append("")
            for i, weakness in enumerate(weaknesses, 1):
                sections.append(f"#### {i + 1}. {weakness['category']}")
                sections.append(f"- **Description:** {weakness['description']}")
                sections.append(f"- **Severity:** {weakness['severity']}")
                sections.append(f"- **Source:** {weakness['source']}")
                if weakness.get('context'):
                    sections.append(f"- **Context:** {weakness['context']}")

        # Recommended Improvements
        improvements = tpm_analysis.get('recommended_improvements', [])
        if improvements:
            sections.append("")
            sections.append("### Recommended Improvements")
            sections.append("")
            for i, improvement in enumerate(improvements, 1):
                sections.append(f"{i + 1}. {improvement}")

        # Victory Assessment
        sections.append("")
        sections.append("### Victory Assessment")
        sections.append("")
        victory_assessment = tpm_analysis.get('victory_assessment', 'unclear')
        sections.append(f"**Overall:** {victory_assessment.title() if isinstance(victory_assessment, str) else victory_assessment}")

        # Recommendations
        sections.append("")
        sections.append("## Recommendations")
        sections.append("")

        recommendations = data.get('recommendations', [])
        if recommendations:
            for i, rec in enumerate(recommendations, 1):
                role = rec.get('agent_role', 'Unknown')
                sections.append(f"### {i + 1}. От {role}:")
                sections.append("")
                sections.append(rec.get('text', 'No text provided'))
                sections.append("")

        # Add footer if no recommendations
        if not recommendations:
            sections.append("")
            sections.append("*Нет рекомендаций*")

        # Metadata section
        sections.append("")
        sections.append("---")
        sections.append("## Metadata")
        sections.append("")
        metadata = data.get('metadata', {})

        sections.append(f"- **Debate Type:** {metadata.get('debate_type', 'unknown')}")
        sections.append(f"- **Run ID:** {metadata.get('run_id', 'unknown')}")
        sections.append(f"- **TPM Victory:** {'Yes' if metadata.get('tpm_victory', False) else 'No'}")
        sections.append(f"- **Total Recommendations:** {metadata.get('total_recommendations', len(recommendations))}")
        sections.append(f"- **Completion Status:** {metadata.get('completion_status', 'unknown')}")

        if metadata.get('error_message'):
            sections.append(f"- **Error Message:** {metadata['error_message']}")

        # Join all sections
        return "\n".join(sections)

    def escape_markdown(self, text: str) -> str:
        """Escape special markdown characters to prevent formatting issues.

        Args:
            text: Text to escape

        Returns:
            Escaped text safe for markdown
        """
        # Escape asterisks (but not in bold sections)
        return text.replace("*", r"\*")

    def sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for safe filesystem usage.

        Args:
            filename: Original filename

        Returns:
            Sanitized filename safe for filesystem
        """
        # Remove or replace unsafe characters
        sanitized = re.sub(r"[^\w\s-.]", "", filename)
        sanitized = re.sub(r"\s+", "_", sanitized)
        sanitized = sanitized.strip("._")
        return sanitized if sanitized else "conclusion"
