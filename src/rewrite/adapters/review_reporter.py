"""
Review reporter for generating review-agent.md files.

Produces human-readable diff-style reports of applied changes.
"""
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from ..domain.change_record import ChangeRecord
from ..domain.entities import RewriteResult


class ReviewReporter:
    """
    Generates review-agent.md file with change tracking.

    Creates a markdown file showing all changes made to the document
    in a "before/after" format for easy review.
    """

    DEFAULT_FILENAME = "review-agent.md"

    def __init__(self, output_dir: Optional[Path] = None):
        """
        Initialize review reporter.

        Args:
            output_dir: Directory for review file (default: current directory)
        """
        self.output_dir = output_dir or Path.cwd()

    def generate_report(
        self,
        changes: List[ChangeRecord],
        result: RewriteResult,
        source_path: Path,
        conclusion_path: Path
    ) -> Path:
        """
        Generate review-agent.md file with all changes.

        Args:
            changes: List of change records
            result: Rewrite operation result
            source_path: Original source file path
            conclusion_path: Conclusion file path

        Returns:
            Path to generated review file
        """
        report_path = self.output_dir / self.DEFAULT_FILENAME

        lines = self._generate_header(
            source_path, conclusion_path, result
        )

        lines.append("## Внесенные изменения")
        lines.append("")
        lines.append(f"Всего применено изменений: **{len(changes)}**")
        lines.append("")

        if not changes:
            lines.extend([
                "Нет изменений для отображения.",
                ""
            ])
        else:
            # Group by section
            sections = self._group_by_section(changes)

            for section_name, section_changes in sections.items():
                lines.append(f"### Секция: {section_name}")
                lines.append("")
                lines.append(f"Изменений: {len(section_changes)}")
                lines.append("")

                for change in section_changes:
                    lines.append(change.to_markdown())

        # Add footer
        lines.extend(self._generate_footer(result, conclusion_path))

        # Write file
        report_path.write_text("\n".join(lines), encoding="utf-8")

        return report_path

    def _generate_header(
        self,
        source_path: Path,
        conclusion_path: Path,
        result: RewriteResult
    ) -> List[str]:
        """Generate report header."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        return [
            "# Отчет о внесенных изменениях",
            "",
            f"**Дата:** {timestamp}",
            f"**Статус:** {result.status.value.upper()}",
            "",
            "## Файлы",
            "",
            f"- **Исходный файл:** `{source_path}`",
            f"- **Файл вывода:** `{result.output_path}`",
            f"- **Файл заключения:** `{conclusion_path}`",
            "",
            f"## Статистика",
            "",
            f"- **Всего ревизий:** {result.revisions_total}",
            f"- **Применено:** {result.revisions_applied}",
            f"- **Проверено:** {result.revisions_verified}",
            f"- **Раундов дебатов:** {result.rounds_completed}",
            ""
        ]

    def _group_by_section(
        self,
        changes: List[ChangeRecord]
    ) -> dict[str, List[ChangeRecord]]:
        """Group changes by section."""
        groups: dict[str, List[ChangeRecord]] = {}

        for change in changes:
            if change.section not in groups:
                groups[change.section] = []
            groups[change.section].append(change)

        return groups

    def _generate_footer(
        self,
        result: RewriteResult,
        conclusion_path: Path
    ) -> List[str]:
        """Generate report footer."""
        lines = [
            "",
            "## Примечания",
            ""
        ]

        if result.status.value == "partial":
            lines.extend([
                f"- ⚠️ Некоторые ревизии не были проверены",
                f"- Смотрите файл заключения для деталей: `{conclusion_path}`",
                ""
            ])

        if result.backup_path:
            lines.append(f"- Резервная копия сохранена: `{result.backup_path}`")

        lines.extend([
            "",
            "---",
            "",
            f"*Сгенерировано Deb8flow Rewrite System*"
        ])

        return lines
