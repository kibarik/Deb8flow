"""
Committee Report Extractor for parsing final_report.md.

This module extracts structured data from committee debate final_report.md,
including room sections, outcomes, and transcript data with turn indices.

Example:
    >>> from src.extractors.committee_report_extractor import CommitteeReportExtractor
    >>> extractor = CommitteeReportExtractor()
    >>> report_data = extractor.parse("path/to/final_report.md")
    >>> for room in report_data.rooms:
    ...     print(f"{room.room_id}: {room.winner}")
"""

import logging
import re
from pathlib import Path
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, field


__all__ = ["CommitteeReportExtractor", "CommitteeReportData", "RoomData", "TranscriptEntry"]


@dataclass
class TranscriptEntry:
    """A single entry in the debate transcript.

    Attributes:
        speaker: Speaker name (e.g., "PRO", "CON", or role name)
        stage: Debate stage (opening, rebuttal, counter, final_argument)
        content: The message content
        validated: Whether the fact-checker validated this message
        turn_index: Turn number in the debate (0-indexed)
    """
    speaker: str
    stage: str
    content: str
    validated: bool
    turn_index: int


@dataclass
class RoomData:
    """Structured data for a single debate room.

    Attributes:
        room_id: Room identifier (e.g., "TPM_vs_CPO")
        opponent_role: Opponent role (e.g., "CPO")
        winner: Winner of the debate (e.g., "TPM", "CFO")
        status: Room status (success, failed, skipped_missing_prompt)
        judge_rationale: Judge's explanation for the verdict
        key_takeaways: List of key takeaways from the room
        transcript: List of transcript entries with turn indices
        raw_content: Raw markdown content for this room
    """
    room_id: str
    opponent_role: str
    winner: str
    status: str
    judge_rationale: str
    key_takeaways: List[str] = field(default_factory=list)
    transcript: List[TranscriptEntry] = field(default_factory=list)
    raw_content: str = ""


@dataclass
class CommitteeReportData:
    """Structured data extracted from final_report.md.

    Attributes:
        run_id: Unique run identifier
        question: Committee question
        generated_at: Timestamp of report generation
        rooms: List of room data for each debate room
        tpm_reflection: TPM self-reflection content (if available)
        metadata: Additional metadata from the report
        raw_content: Raw markdown content of the entire report
    """
    run_id: str
    question: str
    generated_at: str
    rooms: List[RoomData]
    tpm_reflection: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    raw_content: str = ""


class CommitteeReportExtractor:
    """Extractor for parsing committee debate final_report.md files.

    Extracts structured data including:
    - Report metadata (run_id, question, timestamp)
    - Room sections (TPM_vs_CPO, TPM_vs_CFO, etc.)
    - Room outcomes (winner/loser)
    - Judge rationales
    - Transcript data with turn indices

    Example:
        >>> extractor = CommitteeReportExtractor()
        >>> report_data = extractor.parse("committee_output/RUN_123/final_report.md")
        >>> print(f"Question: {report_data.question}")
        >>> for room in report_data.rooms:
        ...     print(f"{room.room_id}: Winner={room.winner}")
    """

    # Standard committee room patterns
    ROOM_PATTERN = re.compile(r"^### (TPM_vs_(CPO|CFO|CTO|BDM))$", re.MULTILINE)

    def __init__(self):
        """Initialize the extractor with logger."""
        self.logger = logging.getLogger(self.__class__.__name__)

    def parse(self, report_path: str) -> CommitteeReportData:
        """Parse a final_report.md file into structured data.

        Args:
            report_path: Path to the final_report.md file

        Returns:
            CommitteeReportData with structured information from the report

        Raises:
            FileNotFoundError: If report file doesn't exist
            ValueError: If report format is invalid or required sections missing
        """
        self.logger.info(f"Parsing committee report: {report_path}")

        report_file = Path(report_path)
        if not report_file.exists():
            raise FileNotFoundError(f"Final report not found: {report_path}")

        # Read report content with UTF-8 encoding
        try:
            content = report_file.read_text(encoding="utf-8")
        except UnicodeDecodeError as e:
            raise ValueError(f"Failed to read report (encoding error): {e}")

        # Extract metadata
        run_id = self._extract_run_id(content)
        question = self._extract_question(content)
        generated_at = self._extract_timestamp(content)

        # Extract room data
        rooms = self._parse_room_sections(content)

        # Extract TPM reflection (if available)
        tpm_reflection = self._extract_tpm_reflection(content)

        # Build metadata dict
        metadata = {
            "source_file": str(report_path),
            "total_rooms": len(rooms),
            "successful_rooms": sum(1 for r in rooms if r.status == "success"),
        }

        self.logger.info(f"Extracted {len(rooms)} room sections from report")

        return CommitteeReportData(
            run_id=run_id,
            question=question,
            generated_at=generated_at,
            rooms=rooms,
            tpm_reflection=tpm_reflection,
            metadata=metadata,
            raw_content=content,
        )

    def _extract_run_id(self, content: str) -> str:
        """Extract run ID from report content.

        Args:
            content: Full report markdown content

        Returns:
            Run ID string or "unknown" if not found
        """
        # Try pattern: **Run ID:** VALUE
        pattern = re.compile(r"^\*\*Run ID:\*\*(.+)$", re.MULTILINE)
        match = pattern.search(content)
        if match:
            return match.group(1).strip()

        # Fallback: Run ID: VALUE
        fallback = re.compile(r"Run ID[:\*\*s]+(.+)$", re.MULTILINE)
        match = fallback.search(content)
        if match:
            return match.group(1).strip()

        return "unknown"

    def _extract_question(self, content: str) -> str:
        """Extract committee question from report.

        Args:
            content: Full report markdown content

        Returns:
            Committee question string

        Raises:
            ValueError: If question section not found
        """
        # Find Committee Question section
        pattern = re.compile(r"^## Committee Question\s*$", re.MULTILINE)
        match = pattern.search(content)
        if not match:
            raise ValueError("Missing required section: Committee Question")

        # Extract content until next section
        start_pos = match.end()
        next_section = re.search(r"^## ", content[start_pos:], re.MULTILINE)
        if next_section:
            end_pos = next_section.start() + start_pos
        else:
            end_pos = len(content)

        question_content = content[start_pos:end_pos].strip()
        return question_content

    def _extract_timestamp(self, content: str) -> str:
        """Extract timestamp from report.

        Args:
            content: Full report markdown content

        Returns:
            ISO timestamp string or current time if not found
        """
        # Try pattern: **Generated:** VALUE
        pattern = re.compile(r"^\*\*Generated:\*\*(.+)$", re.MULTILINE)
        match = pattern.search(content)
        if match:
            return match.group(1).strip()

        # Fallback to current time
        from datetime import datetime
        return datetime.utcnow().isoformat() + "Z"

    def _parse_room_sections(self, content: str) -> List[RoomData]:
        """Parse all room sections from the report.

        Args:
            content: Full report markdown content

        Returns:
            List of RoomData objects, one per debate room
        """
        rooms = []

        # Find Room-by-Room Analysis section
        room_section_pattern = re.compile(r"^## Room-by-Room Analysis\s*$", re.MULTILINE)
        room_section_match = room_section_pattern.search(content)
        if not room_section_match:
            self.logger.warning("Room-by-Room Analysis section not found")
            return rooms

        # Extract room section content
        start_pos = room_section_match.end()
        next_section = re.search(r"^## ", content[start_pos:], re.MULTILINE)
        if next_section:
            end_pos = next_section.start() + start_pos
        else:
            end_pos = len(content)

        room_section_content = content[start_pos:end_pos]

        # Find all room subsections
        for room_match in self.ROOM_PATTERN.finditer(room_section_content):
            room_id = room_match.group(1)
            opponent_role = room_match.group(2)

            # Extract room content
            room_start = room_match.end()
            next_room = self.ROOM_PATTERN.search(room_section_content[room_start:])
            if next_room:
                room_end = next_room.start() + room_start
            else:
                room_end = len(room_section_content)

            room_content = room_section_content[room_start:room_end]

            # Parse room data
            room_data = self._parse_room_data(room_id, opponent_role, room_content)
            rooms.append(room_data)

        return rooms

    def _parse_room_data(self, room_id: str, opponent_role: str, room_content: str) -> RoomData:
        """Parse data for a single room.

        Args:
            room_id: Room identifier (e.g., "TPM_vs_CPO")
            opponent_role: Opponent role (e.g., "CPO")
            room_content: Raw markdown content for this room

        Returns:
            RoomData object with parsed information
        """
        # Extract status
        status = self._extract_status(room_content)

        # Extract winner
        winner = self._extract_winner(room_content)

        # Extract judge rationale
        judge_rationale = self._extract_judge_rationale(room_content)

        # Extract key takeaways
        key_takeaways = self._extract_key_takeaways(room_content)

        # Extract transcript
        transcript = self._extract_transcript(room_content)

        return RoomData(
            room_id=room_id,
            opponent_role=opponent_role,
            winner=winner,
            status=status,
            judge_rationale=judge_rationale,
            key_takeaways=key_takeaways,
            transcript=transcript,
            raw_content=room_content,
        )

    def _extract_status(self, room_content: str) -> str:
        """Extract room status.

        Args:
            room_content: Room markdown content

        Returns:
            Status string (success, failed, or unknown)
        """
        pattern = re.compile(r"^\*\*Status:\*\*(.+)$", re.MULTILINE)
        match = pattern.search(room_content)
        if match:
            return match.group(1).strip().lower()
        return "unknown"

    def _extract_winner(self, room_content: str) -> str:
        """Extract winner from room content.

        Args:
            room_content: Room markdown content

        Returns:
            Winner name (e.g., "TPM", "CFO") or "Unknown"
        """
        # Try pattern: **Winner:** VALUE
        pattern = re.compile(r"^\*\*Winner:\*\*(.+)$", re.MULTILINE)
        match = pattern.search(room_content)
        if match:
            return match.group(1).strip()

        # Fallback: look for "TPM won" or "CFO won"
        fallback = re.search(r"(TPM|CPO|CFO|CTO|BDM)\s+won", room_content, re.IGNORECASE)
        if fallback:
            return fallback.group(1).upper()

        return "Unknown"

    def _extract_judge_rationale(self, room_content: str) -> str:
        """Extract judge's rationale from room content.

        Args:
            room_content: Room markdown content

        Returns:
            Judge rationale string or empty string if not found
        """
        # Try pattern: **Judge Explanation:** or **Judge Rationale:**
        pattern = re.compile(r"^\*\*Judge (Explanation|Rationale):\*\*(.+?)(?=^\*\*|$)", re.MULTILINE | re.DOTALL)
        match = pattern.search(room_content)
        if match:
            return match.group(2).strip()

        # Fallback: extract text after "Winner:" until next section
        winner_pattern = re.compile(r"^\*\*Winner:\*\*.+?$", re.MULTILINE)
        winner_match = winner_pattern.search(room_content)
        if winner_match:
            start = winner_match.end()
            # Extract until next bold section
            next_bold = re.search(r"^\*\*", room_content[start:], re.MULTILINE)
            if next_bold:
                end = next_bold.start() + start
            else:
                end = len(room_content)
            rationale = room_content[start:end].strip()
            return rationale

        return ""

    def _extract_key_takeaways(self, room_content: str) -> List[str]:
        """Extract key takeaways from room content.

        Args:
            room_content: Room markdown content

        Returns:
            List of takeaway strings
        """
        # Find Key Takeaways section
        pattern = re.compile(r"^\*\*Key Takeaways:\*\*", re.MULTILINE)
        match = pattern.search(room_content)
        if not match:
            return []

        # Extract bullet points after the heading
        start = match.end()
        # Extract until next section (about 500 chars max)
        section_content = room_content[start:start+500]

        # Extract bullet points
        bullet_pattern = re.compile(r"^- (.+)$", re.MULTILINE)
        bullets = bullet_pattern.findall(section_content)

        return bullets

    def _extract_transcript(self, room_content: str) -> List[TranscriptEntry]:
        """Extract transcript entries with turn indices.

        Args:
            room_content: Room markdown content

        Returns:
            List of TranscriptEntry objects with turn indices
        """
        transcript = []

        # Find Full Dialogue section
        dialogue_pattern = re.compile(r"^\*\*Full Dialogue:\*\*", re.MULTILINE)
        dialogue_match = dialogue_pattern.search(room_content)
        if not dialogue_match:
            return transcript

        # Extract dialogue content
        start = dialogue_match.end()
        # Find end of dialogue section (next section or end of content)
        # Look for markdown headers or horizontal rules
        next_section = re.search(r"^(---|\*\*[^:]+:\*\*|###\s)", room_content[start:], re.MULTILINE)
        if next_section:
            end = next_section.start() + start
        else:
            end = len(room_content)

        dialogue_content = room_content[start:end].strip()

        # Parse transcript entries
        # Pattern: **SPEAKER** (stage) [✓/✗]:
        # Followed by content on next line(s)
        # Note: The checkmark uses special Unicode characters (U+2713/U+2717)
        entry_pattern = re.compile(r"^\*\*(\w+)\*\*\s+\((\w+)\)\s+([✓✗])\:", re.MULTILINE)
        turn_index = 0

        for match in entry_pattern.finditer(dialogue_content):
            speaker = match.group(1)
            stage = match.group(2)
            validated_marker = match.group(3)

            validated = validated_marker == "✓"

            # Extract content from after the match until next entry or end
            content_start = match.end()
            next_match = entry_pattern.search(dialogue_content[content_start:])
            if next_match:
                content_end = next_match.start() + content_start
            else:
                content_end = len(dialogue_content)

            # Get content and clean it up
            content = dialogue_content[content_start:content_end].strip()
            content = re.sub(r"\n+", " ", content).strip()

            if content:  # Only add if there's content
                transcript.append(TranscriptEntry(
                    speaker=speaker,
                    stage=stage,
                    content=content,
                    validated=validated,
                    turn_index=turn_index,
                ))
                turn_index += 1

        return transcript

    def _extract_tpm_reflection(self, content: str) -> str:
        """Extract TPM self-reflection section.

        Args:
            content: Full report markdown content

        Returns:
            TPM reflection content or empty string if not found
        """
        # Find TPM Reflection section
        pattern = re.compile(r"^## TPM Reflection\s*$", re.MULTILINE)
        match = pattern.search(content)
        if not match:
            return ""

        # Extract reflection content
        start_pos = match.end()
        next_section = re.search(r"^## ", content[start_pos:], re.MULTILINE)
        if next_section:
            end_pos = next_section.start() + start_pos
        else:
            end_pos = len(content)

        return content[start_pos:end_pos].strip()
