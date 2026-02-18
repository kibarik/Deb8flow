"""
Final report generator for product committee.

This adapter generates comprehensive markdown reports synthesizing
all debate room results, including dialogue excerpts and metadata.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from ....shared.debate.domain.entities import DebateRoom
from ....shared.debate.domain.value_objects import Speaker


logger = logging.getLogger(__name__)


class FinalReportGenerator:
    """Generates comprehensive markdown committee reports."""

    def generate_final_report(
        self,
        run_id: str,
        prd_path: str,
        question: str,
        rooms: List[DebateRoom],
        metadata: Dict[str, Any]
    ) -> str:
        """
        Generate final markdown committee report.

        Args:
            run_id: Run identifier
            prd_path: Path to PRD document
            question: Committee question
            rooms: All debate room results
            metadata: Run metadata with end_time, model, etc.

        Returns:
            Markdown report content
        """
        lines = [
            f"# Product Committee Report",
            f"",
            f"**Run ID:** {run_id}",
            f"**Generated:** {metadata.get('end_time', datetime.utcnow().isoformat())}",
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

        # Count room statuses
        successful = [r for r in rooms if r.is_successful]
        failed = [r for r in rooms if r.status.value == "failed"]
        skipped = [r for r in rooms if r.status.value == "skipped_missing_prompt"]

        lines.append(f"This report synthesizes debate results from {len(rooms)} committee rooms:")
        lines.append(f"- **Successful rooms:** {len(successful)}")
        lines.append(f"- **Failed rooms:** {len(failed)}")
        lines.append(f"- **Skipped rooms:** {len(skipped)} (missing role prompts)")
        lines.append("")

        # Room-by-room analysis
        lines.extend([
            f"---",
            f"",
            f"## Room-by-Room Analysis",
            f""
        ])

        for room in rooms:
            lines.extend(self._format_room_section(room))

        # TPM Reflection section (placeholder for future implementation)
        lines.extend([
            f"---",
            f"",
            f"## TPM Reflection",
            f"",
            f"*Reflection feature is currently disabled*",
            f""
        ])

        # Metadata footer
        lines.extend([
            f"---",
            f"",
            f"## Metadata",
            f"",
            f"- **PRD:** {prd_path}",
            f"- **Roles directory:** {metadata.get('roles_dir', 'N/A')}",
            f"- **Model:** {metadata.get('model', 'default')}",
            f"- **Max retries:** {metadata.get('max_retries', 2)}",
            f"- **Start time:** {metadata.get('start_time', 'N/A')}",
            f"- **End time:** {metadata.get('end_time', 'N/A')}",
            ""
        ])

        return '\n'.join(lines)

    def _format_room_section(self, room: DebateRoom) -> List[str]:
        """Format a single room's section in the report."""
        lines = [
            f"### {room.room_id.value}",
            f"",
            f"**Status:** {room.status.value}",
            f""
        ]

        if room.is_successful:
            lines.extend([
                f"**Participants:** TPM (PRO) vs {room.con_participant} (CON)",
                f"",
                f"**Winner:** {room.verdict.winner.value if room.verdict else 'Unknown'}",
                f"",
                f"**Judge Explanation:**",
                f"{room.verdict.explanation if room.verdict else 'N/A'}",
                f"",
                f"**Key Takeaways:**",
                f""
            ])

            if room.takeaways:
                for takeaway in room.takeaways:
                    lines.append(f"- {takeaway}")
                lines.append("")
            else:
                lines.append("*No takeaways extracted*\n")

            # Add dialogue excerpt if available
            if room.messages:
                lines.extend([
                    f"**Dialogue Excerpt:**",
                    f""
                ])
                for msg in room.messages[:10]:  # First 10 messages
                    speaker = msg.speaker.value
                    content = msg.content
                    stage = msg.stage
                    validated = " ✓" if msg.validated else " ✗"

                    lines.extend([
                        f"**{speaker.upper()}** ({stage}){validated}:",
                        f"{content[:200]}{'...' if len(content) > 200 else ''}",
                        f""
                    ])

                if len(room.messages) > 10:
                    lines.append(f"*... and {len(room.messages) - 10} more messages*\n")

        elif room.status.value == "failed":
            lines.extend([
                f"**Error:** {room.error or 'Unknown error'}",
                f""
            ])
        else:
            lines.append("*Skipped: Role prompt file not found*\n")

        return lines

    def generate_intermediate_report(
        self,
        run_id: str,
        completed_rooms: List[DebateRoom],
        total_rooms: int
    ) -> str:
        """
        Generate intermediate progress report during execution.

        Args:
            run_id: Run identifier
            completed_rooms: Rooms completed so far
            total_rooms: Total number of rooms to execute

        Returns:
            Markdown progress report
        """
        successful = sum(1 for r in completed_rooms if r.is_successful)
        failed = sum(1 for r in completed_rooms if r.status.value == "failed")

        lines = [
            f"# Committee Progress Report",
            f"",
            f"**Run ID:** {run_id}",
            f"**Progress:** {len(completed_rooms)}/{total_rooms} rooms completed",
            f"",
            f"---",
            f"",
            f"## Summary",
            f"",
            f"- **Successful:** {successful}",
            f"- **Failed:** {failed}",
            f"- **In progress:** {total_rooms - len(completed_rooms)}",
            f"",
            f"## Completed Rooms",
            f""
        ]

        for room in completed_rooms:
            status_icon = "✓" if room.is_successful else "✗"
            winner = room.verdict.winner.value if room.verdict else "Unknown"
            lines.append(f"- {status_icon} **{room.room_id.value}**: {room.status.value} (Winner: {winner})")

        lines.append("")

        return '\n'.join(lines)
