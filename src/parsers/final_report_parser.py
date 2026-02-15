import logging
import re
from pathlib import Path
from typing import Optional, Dict, List

from src.types.conclusion_types import (
    ConclusionData,
    VerdictSummary,
    QAPair,
    TPMAnalysis,
    TPMWeakness,
    Recommendation,
    ConclusionMetadata,
    DebateType,
)


__all__ = ["FinalReportParser"]


class FinalReportParser:
    """Parser for committee debate final_report.md files."""

    def __init__(self):
        """Initialize the parser with logger."""
        self.logger = logging.getLogger(self.__class__.__name__)

    def parse(self, report_path: str) -> ConclusionData:
        """Parse a final_report.md file into ConclusionData."""
        report_file = Path(report_path)

        if not report_file.exists():
            raise FileNotFoundError(f"Final report not found: {report_path}")

        try:
            content = report_file.read_text(encoding="utf-8")
        except UnicodeDecodeError as e:
            raise ValueError(f"Failed to read report: {e}")

        sections = self._extract_sections(content)

        debate_question = self._parse_question(sections)
        verdict = self._parse_verdict(sections)
        qa_summary = self._parse_qa_summary(sections)
        tpm_analysis = self._parse_tpm_analysis(sections)
        recommendations = self._parse_recommendations(sections)
        metadata = self._parse_metadata(sections, report_path)

        return ConclusionData(
            debate_question=debate_question,
            verdict=verdict,
            qa_summary=qa_summary,
            tpm_analysis=tpm_analysis,
            recommendations=recommendations,
            metadata=metadata,
        )

    def _extract_sections(self, content: str) -> Dict[str, str]:
        """Extract sections from markdown content using regex."""
        sections = {}
        pattern = re.compile(r"^## (.+)$", re.MULTILINE)
        matches = list(pattern.finditer(content))

        for i, match in enumerate(matches):
            section_name = match.group(1).strip()
            start_pos = match.end() + 1

            if i + 1 < len(matches):
                end_pos = matches[i + 1].start()
            else:
                end_pos = len(content)

            section_content = content[start_pos:end_pos].strip()
            sections[section_name] = section_content

        return sections

    def _parse_question(self, sections: Dict[str, str]) -> str:
        """Extract debate question from Committee Question section."""
        section = sections.get("Committee Question")
        if not section:
            raise ValueError("Missing required section: Committee Question")

        lines = section.split('\n')
        for line in lines:
            stripped = line.strip()
            if stripped:
                return stripped
        return section.strip()

    def _parse_verdict(self, sections: Dict[str, str]) -> VerdictSummary:
        """Extract verdict from room results."""
        room_section = sections.get("Room-by-Room Analysis", "")

        status_pattern = re.compile(r"^\*\*Status:\*\*(.+)$", re.MULTILINE)
        winner_pattern = re.compile(r"^\*\*Winner:\*\*(.+)$", re.MULTILINE)

        status_match = status_pattern.search(room_section)
        winner_match = winner_pattern.search(room_section)

        winner = winner_match.group(1).strip() if winner_match else "No clear winner"

        if status_match:
            justification = status_match.group(1).strip()
        else:
            justification = "No explanation available"

        winner_position = self._determine_position(winner)

        return VerdictSummary(
            winner=winner,
            winner_position=winner_position,
            justification=justification,
            confidence=None,
        )

    def _determine_position(self, role: str) -> str:
        """Determine if role is PRO or CON position."""
        pro_roles = {"TPM", "BDM", "PRO"}
        return "PRO" if role in pro_roles else "CON"

    def _parse_qa_summary(self, sections: Dict[str, str]) -> List[QAPair]:
        """Extract Q&A pairs from room results."""
        room_section = sections.get("Room-by-Room Analysis", "")
        qa_pairs: List[QAPair] = []
        room_pattern = re.compile(r"^### TPM_vs_(\w+)$", re.MULTILINE)

        for room_match in room_pattern.finditer(room_section):
            role = room_match.group(1)
            room_start = room_match.end()
            next_room = room_pattern.search(room_section[room_start:])
            room_end = next_room.start() + room_start if next_room else len(room_section)
            room_content = room_section[room_start:room_end]

            takeaway_pattern = re.compile(r"^\*\*Key Takeaways:\*\*", re.MULTILINE)
            takeaway_match = takeaway_pattern.search(room_content)

            if takeaway_match:
                takeaway_start = takeaway_match.end()
                takeaway_content = room_content[takeaway_start:]
                bullet_pattern = re.compile(r"^- (.+)$", re.MULTILINE)
                bullets = bullet_pattern.findall(takeaway_content)

                for i, bullet in enumerate(bullets[:10]):
                    qa_pairs.append(QAPair(
                        question=f"Key takeaway {i + 1} from TPM_vs_{role}",
                        answer=bullet,
                        stage="verdict",
                        speaker=role,
                        validated=True,
                        priority=i + 1,
                    ))

        if len(qa_pairs) < 3:
            self.logger.warning(f"Only {len(qa_pairs)} Q&A pairs found, expected 3-10")

        return qa_pairs[:10]

    def _parse_tpm_analysis(self, sections: Dict[str, str]) -> TPMAnalysis:
        """Extract TPM analysis from TPM Reflection section."""
        reflection_section = sections.get("TPM Reflection", "")

        position_summary = self._extract_subsection(reflection_section, "Learned Insights")

        weaknesses: List[TPMWeakness] = []
        insights = self._extract_subsection(reflection_section, "Learned Insights")

        if "weakness" in insights.lower() or "gap" in insights.lower():
            weaknesses.append(TPMWeakness(
                category="self_identified",
                description="Self-identified weakness from reflection",
                severity="medium",
                source="TPM",
                context=None,
            ))

        assessment_section = self._extract_subsection(reflection_section, "Potential Assessment")
        victory_assessment = self._parse_victory_assessment(assessment_section)

        recommended_improvements = self._extract_improvements(reflection_section)

        return TPMAnalysis(
            position_summary=position_summary or "TPM position analysis not available",
            weaknesses=weaknesses,
            recommended_improvements=recommended_improvements,
            victory_assessment=victory_assessment,
        )

    def _parse_victory_assessment(self, assessment_text: str) -> str:
        """Parse victory assessment from assessment section."""
        assessment_lower = assessment_text.lower()
        overall_pattern = re.compile(r"^\*\*Overall:\*\*(.+)$", re.MULTILINE)
        overall_match = overall_pattern.search(assessment_text)

        if overall_match:
            overall = overall_match.group(1).strip().lower()
            if "won" in overall or "success" in overall:
                return "won"
            elif "lost" in overall or "fail" in overall:
                return "lost"

        return "unclear"

    def _extract_improvements(self, reflection_section: str) -> List[str]:
        """Extract recommended improvements from reflection."""
        recommendations_section = self._extract_subsection(reflection_section, "Recommendations")

        if not recommendations_section:
            return []

        recommendations = re.findall(r"^\d+\. (.+)$", recommendations_section, re.MULTILINE)
        return recommendations

    def _parse_recommendations(self, sections: Dict[str, str]) -> List[Recommendation]:
        """Extract recommendations from various sections."""
        recommendations: List[Recommendation] = []

        reflection_section = sections.get("TPM Reflection", "")
        for i, rec_text in enumerate(self._extract_improvements(reflection_section)):
            recommendations.append(Recommendation(
                agent_role="TPM",
                text=rec_text,
                priority="high" if i < 2 else "medium",
                category="improvement",
                actionable=True,
            ))

        return recommendations

    def _parse_metadata(self, sections: Dict[str, str], report_path: str) -> ConclusionMetadata:
        """Extract metadata from Metadata section and file info."""
        metadata_section = sections.get("Metadata", "")

        run_id = self._extract_run_id(metadata_section)
        generated_at = self._extract_timestamp(metadata_section)
        debate_type = DebateType.COMMITTEE.value

        return ConclusionMetadata(
            debate_type=debate_type,
            run_id=run_id,
            generated_at=generated_at,
            source_file=report_path,
            total_recommendations=0,
            tpm_victory=False,
            completion_status="success",
            error_message=None,
        )

    def _extract_run_id(self, metadata_section: str) -> str:
        """Extract run ID from metadata section."""
        run_id_pattern = re.compile(r"^\*\*Run ID:\*\*(.+)$", re.MULTILINE)
        run_id_match = run_id_pattern.search(metadata_section)

        if run_id_match:
            return run_id_match.group(1).strip()

        fallback_pattern = re.compile(r"Run ID[:\*\*s+(.+)$", re.MULTILINE)
        fallback_match = fallback_pattern.search(metadata_section)

        if fallback_match:
            return fallback_match.group(1).strip()

        return "unknown"

    def _extract_timestamp(self, metadata_section: str) -> str:
        """Extract timestamp from metadata section."""
        generated_pattern = re.compile(r"^\*\*Generated:\*\*(.+)$", re.MULTILINE)
        generated_match = generated_pattern.search(metadata_section)

        if generated_match:
            return generated_match.group(1).strip()

        from datetime import datetime
        return datetime.utcnow().isoformat() + "Z"

    def _extract_subsection(self, section_content: str, subsection_title: str) -> str:
        """Extract a subsection by title from section content."""
        pattern = re.compile(rf"^### {re.escape(subsection_title)}$", re.MULTILINE)
        match = pattern.search(section_content)

        if not match:
            return ""

        start_pos = match.end()
        next_pattern = re.compile(r"^### ", section_content[start_pos:], re.MULTILINE)
        next_match = next_pattern.search(section_content[start_pos:])
        end_pos = next_match.start() + start_pos if next_match else len(section_content)

        return section_content[start_pos:end_pos].strip()
