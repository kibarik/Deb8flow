# WP05: Report Generation System

**Work Package**: 017-product-committee-clean-architecture-refactoring / WP05
**Status**: TODO
**Dependencies**: WP04

## Overview

Extract report generation logic into modular adapter classes that implement the ReportGenerator port interface.

## Implementation Requirements

### 1. Final Report Generator (`src/committee/adapters/reports/final_report.py`)

```python
from typing import List, Dict, Any
from src.shared.debate.domain.entities import DebateRoom
from src.shared.debate.application.ports import ReportGenerator

class FinalReportGenerator:
    """Generates comprehensive final reports for committee sessions."""

    def generate_final_report(
        self,
        run_id: str,
        prd_path: str,
        question: str,
        rooms: List[DebateRoom],
        metadata: Dict[str, Any]
    ) -> str:
        """Generate comprehensive final report in markdown."""
        lines = [
            "# Product Committee Report",
            "",
            f"**Run ID:** {run_id}",
            f"**Generated:** {metadata.get('end_time', 'N/A')}",
            "",
            "---",
            "",
            "## Committee Question",
            "",
            f"{question}",
            "",
            "---",
            "",
            "## Executive Summary",
            ""
        ]

        # Count outcomes
        successful = [r for r in rooms if r.is_successful]
        failed = [r for r in rooms if r.status.value == "failed"]
        skipped = [r for r in rooms if r.status.value == "skipped"]

        lines.append(f"This report synthesizes debate results from {len(rooms)} committee rooms:")
        lines.append(f"- **Successful rooms:** {len(successful)}")
        lines.append(f"- **Failed rooms:** {len(failed)}")
        lines.append(f"- **Skipped rooms:** {len(skipped)}")
        lines.append("")

        # Room-by-room analysis
        lines.extend([
            "---",
            "",
            "## Room-by-Room Analysis",
            ""
        ])

        for room in rooms:
            lines.extend(self._format_room(room))

        # Metadata footer
        lines.extend([
            "---",
            "",
            "## Metadata",
            "",
            f"- **PRD:** {prd_path}",
            f"- **Model:** {metadata.get('model', 'default')}",
            f"- **Max retries:** {metadata.get('max_retries', 2)}",
            f"- **Start time:** {metadata.get('start_time', 'N/A')}",
            f"- **End time:** {metadata.get('end_time', 'N/A')}",
            ""
        ])

        return "\n".join(lines)

    def _format_room(self, room: DebateRoom) -> List[str]:
        """Format a single debate room for the report."""
        lines = [
            f"### {room.room_id.value}",
            "",
            f"**Status:** {room.status.value}",
            ""
        ]

        if room.is_successful:
            lines.extend([
                f"**Winner:** {room.verdict.winner.value if room.verdict else 'Unknown'}",
                "",
                f"**Judge Explanation:**",
                f"{room.verdict.explanation if room.verdict else 'N/A'}",
                "",
                f"**Key Takeaways:**",
                ""
            ])

            for takeaway in room.takeaways[:5]:
                lines.append(f"- {takeaway}")
            lines.append("")

            # Full dialogue
            if room.messages:
                lines.extend([
                    "**Full Dialogue:**",
                    ""
                ])
                for msg in room.messages:
                    validated_mark = " ✓" if msg.validated else " ✗"
                    lines.extend([
                        f"**{msg.speaker.value.upper()}** ({msg.stage}){validated_mark}:",
                        f"{msg.content}",
                        ""
                    ])

        elif room.status.value == "failed":
            lines.extend([
                f"**Error:** {room.error or 'Unknown error'}",
                ""
            ])
        else:
            lines.append("*Skipped: Role prompt file not found*\n")

        return lines
```

### 2. Conclusion Generator (`src/committee/adapters/reports/conclusion.py`)

```python
from typing import List, Dict, Any
from src.shared.debate.domain.entities import DebateRoom
from src.shared.debate.domain.services import categorize_error
from src.shared.debate.domain.value_objects import Speaker

class ConclusionGenerator:
    """Generates executive summary conclusions for committee sessions."""

    def generate_conclusion(
        self,
        question: str,
        rooms: List[DebateRoom],
        metadata: Dict[str, Any]
    ) -> str:
        """Generate executive summary conclusion."""
        lines = [
            "# Conclusion",
            "",
            f"**Generated:** {metadata.get('end_time', 'N/A')}",
            "",
            "---",
            "",
            "## Committee Question",
            "",
            f"{question}",
            "",
            "---",
            "",
            "## Executive Summary",
            ""
        ]

        successful = [r for r in rooms if r.is_successful]
        failed = [r for r in rooms if r.status.value == "failed"]

        # Handle all-failed case
        if not successful and failed:
            return self._generate_failure_conclusion(rooms, failed, metadata)

        # Normal conclusion
        tpm_wins = sum(1 for r in successful if r.verdict and r.verdict.winner == Speaker.PRO)
        opponent_wins = len(successful) - tpm_wins

        lines.append(f"After {len(successful)} successful debate rooms:")
        lines.append(f"- **TPM victories:** {tpm_wins}/{len(successful)}")
        lines.append(f"- **Opponent victories:** {opponent_wins}/{len(successful)}")
        lines.append("")

        # Overall verdict
        if tpm_wins > opponent_wins:
            overall_verdict = "TPM (PRO) position prevails"
        elif opponent_wins > tpm_wins:
            overall_verdict = "Opponents (CON) positions prevail"
        else:
            overall_verdict = "No clear consensus"

        lines.extend([
            f"**Overall Verdict:** {overall_verdict}",
            "",
            "---",
            "",
            "## Room Results Summary",
            ""
        ])

        for room in rooms:
            if room.is_successful:
                winner = room.verdict.winner.value if room.verdict else "Unknown"
                explanation = room.verdict.explanation if room.verdict else "No explanation"
                # Extract first sentence
                first_sentence = explanation.split('.')[0].strip() if explanation else "No explanation"
                if len(first_sentence) > 200:
                    first_sentence = first_sentence[:200] + "..."

                lines.extend([
                    f"### {room.room_id.value}",
                    f"**Winner:** {winner}",
                    f"**Summary:** {first_sentence}",
                    ""
                ])

        # Footer
        lines.extend([
            "---",
            "",
            "*For detailed dialogue and analysis, see final_report.md*",
            ""
        ])

        return "\n".join(lines)

    def _generate_failure_conclusion(
        self,
        rooms: List[DebateRoom],
        failed_rooms: List[DebateRoom],
        metadata: Dict[str, Any]
    ) -> str:
        """Generate conclusion when all rooms failed."""
        lines = [
            "**Status:** All debate rooms failed to complete.",
            "",
            "---",
            "",
            "## Error Analysis",
            ""
        ]

        # Categorize errors
        error_patterns = {}
        for room in failed_rooms:
            if room.error:
                error_type = categorize_error(room.error)
                error_patterns.setdefault(error_type, []).append(room.room_id.value)

        for error_type, room_list in error_patterns.items():
            lines.extend([
                f"### {error_type}",
                f"Affected rooms: {', '.join(room_list)}",
                ""
            ])

            # Add recommendations
            lines.extend(self._get_error_recommendations(error_type))
            lines.append("")

        # Sample errors
        lines.extend([
            "### Sample Error Details",
            ""
        ])

        for room in failed_rooms[:2]:
            lines.extend([
                f"**{room.room_id.value}:**",
                "```",
                room.error or "No error message",
                "```",
                ""
            ])

        # Next steps
        lines.extend([
            "---",
            "",
            "## Next Steps",
            "",
            "1. **Check logs above** for detailed error messages",
            "2. **Verify LLM configuration** - check API keys and endpoints",
            "3. **Test with single room first** - use `--max-concurrency 1`",
            "4. **Check role prompt files** - ensure all `.txt` files in `prompts/roles/` exist",
            "5. **Review PRD document** - ensure it's readable and contains sufficient content",
            ""
        ])

        return "\n".join(lines)

    def _get_error_recommendations(self, error_type: str) -> List[str]:
        """Get recommendations for specific error types."""
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
            ]
        }

        return recommendations.get(error_type, [
            "**Recommendation:** Unknown error - check logs for details.",
            f"- Error message: {error_type}"
        ])
```

### 3. Unified Report Generator Adapter

Create adapter that implements the port:

```python
# src/committee/adapters/reports/__init__.py
from .final_report import FinalReportGenerator
from .conclusion import ConclusionGenerator

class CommitteeReportGenerator:
    """Implements ReportGenerator port for committee reports."""

    def __init__(self):
        self.final_generator = FinalReportGenerator()
        self.conclusion_generator = ConclusionGenerator()

    def generate_final_report(
        self,
        run_id: str,
        prd_path: str,
        question: str,
        rooms: List,
        metadata: Dict[str, Any]
    ) -> str:
        return self.final_generator.generate_final_report(
            run_id, prd_path, question, rooms, metadata
        )

    def generate_conclusion(
        self,
        question: str,
        rooms: List,
        metadata: Dict[str, Any]
    ) -> str:
        return self.conclusion_generator.generate_conclusion(
            question, rooms, metadata
        )

    def generate_intermediate_report(
        self,
        run_id: str,
        question: str,
        rooms: List,
        metadata: Dict[str, Any]
    ) -> str:
        # Use same format as final report for intermediate
        return self.final_generator.generate_final_report(
            run_id, "", question, rooms, metadata
        )
```

## Snapshot Testing

```python
# tests/snapshots/test_committee_reports/
# Use syrupy for snapshot testing

def test_final_report_snapshot(snapshot):
    from src.committee.adapters.reports import FinalReportGenerator

    generator = FinalReportGenerator()
    result = generator.generate_final_report(
        run_id="test_run",
        prd_path="test.txt",
        question="Test question",
        rooms=test_rooms,
        metadata=test_metadata
    )

    assert snapshot == result

def test_conclusion_snapshot(snapshot):
    from src.committee.adapters.reports import ConclusionGenerator

    generator = ConclusionGenerator()
    result = generator.generate_conclusion(
        question="Test question",
        rooms=test_rooms,
        metadata=test_metadata
    )

    assert snapshot == result
```

## Acceptance Criteria

- [ ] Report generators produce identical output to current implementation
- [ ] Snapshot tests pass for all report types
- [ ] Error categorization matches spec (Regex, Timeout, JSON, LLM/API)
- [ ] Reports handle partial failures gracefully
- [ ] All-room-failure case generates specific recommendations
- [ ] ReportGenerator port interface implemented correctly

## Files to Create

1. `src/committee/adapters/__init__.py`
2. `src/committee/adapters/reports/__init__.py`
3. `src/committee/adapters/reports/final_report.py`
4. `src/committee/adapters/reports/conclusion.py`
5. `tests/snapshots/test_committee_reports/test_final_report.md`
6. `tests/snapshots/test_committee_reports/test_conclusion.md`
7. `tests/unit/committee/adapters/reports/test_generators.py`

## Notes

- Match exact output format of current `product_committee.py`
- Use snapshot tests to ensure identical output
- Handle all edge cases (no successful rooms, all failed, partial failures)
- Error categorization: Regex, Timeout, JSON, LLM/API, Other

## Next Steps

After completing this work package:
1. Run `pytest tests/snapshots/test_committee_reports/ --snapshot-update` to generate initial snapshots
2. Run `pytest tests/snapshots/test_committee_reports/` to verify they match
3. Compare output with current `product_committee.py` to ensure exact match
4. Commit changes with message "feat: implement report generation system (WP05)"
5. Move to WP06 (CLI Argument Parsing and Validation)
