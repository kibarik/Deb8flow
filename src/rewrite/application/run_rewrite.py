"""
Use case for running document rewrite with debate verification.

Orchestrates the complete rewrite workflow from file reading
through verification debate to final result.
"""
import logging
import asyncio
from pathlib import Path
from typing import List, Optional

from ..domain.entities import RevisionItem, RewriteResult
from ..domain.value_objects import RewriteStatus, RewriteConfig, DocumentType
from ..adapters.revision_parser import ConclusionParser
from ..adapters.document_editor import MarkdownEditor, TextEditor
from ..adapters.progress_reporter import ProgressReporter
from ..infrastructure.storage import RewriteStorage


logger = logging.getLogger(__name__)


class RunRewrite:
    """
    Use case for running document rewrite with verification.

    Coordinates all adapters to provide complete rewrite functionality:
    1. Parse revisions from conclusion
    2. Apply revisions to source document
    3. Run verification debates
    4. Return result with exit code mapping
    """

    def __init__(
        self,
        parser: ConclusionParser,
        storage: RewriteStorage,
        reporter: ProgressReporter,
        config: RewriteConfig
    ):
        """
        Initialize use case with required adapters.

        Args:
            parser: Revision parser for conclusion files
            storage: File storage for backup/restore
            reporter: Progress reporter for console output
            config: Rewrite configuration
        """
        self.parser = parser
        self.storage = storage
        self.reporter = reporter
        self.config = config

    async def execute(
        self,
        source_path: Path,
        conclusion_path: Path,
        output_path: Optional[Path] = None,
        max_rounds: Optional[int] = None,
        skip_backup: bool = False
    ) -> RewriteResult:
        """
        Execute complete rewrite workflow.

        Args:
            source_path: Path to source document
            conclusion_path: Path to conclusion.md
            output_path: Optional output path (default: overwrite source)
            max_rounds: Optional override for max debate rounds
            skip_backup: If True, skip backup creation

        Returns:
            RewriteResult with operation outcome
        """
        # Use output_path or source_path
        target_path = output_path or source_path

        # Determine max rounds
        effective_max_rounds = max_rounds or self.config.max_rounds

        # Round 0 means no verification
        if effective_max_rounds == 0:
            self.reporter.info("Max rounds is 0, skipping verification")
            return await self._rewrite_without_verification(
                source_path, conclusion_path, target_path, skip_backup
            )

        # Full workflow with verification
        return await self._rewrite_with_verification(
            source_path, conclusion_path, target_path,
            effective_max_rounds, skip_backup
        )

    async def _rewrite_with_verification(
        self,
        source_path: Path,
        conclusion_path: Path,
        target_path: Path,
        max_rounds: int,
        skip_backup: bool
    ) -> RewriteResult:
        """Execute full rewrite workflow with debate verification."""
        try:
            # Phase 1: Read and parse
            self.reporter.report_reading_files(source_path, conclusion_path)
            revisions = self.parser.parse(conclusion_path)
            self.reporter.report_revisions_found(len(revisions))

            if not revisions:
                return RewriteResult(
                    status=RewriteStatus.VALIDATION_ERROR,
                    revisions_applied=0,
                    revisions_verified=0,
                    revisions_total=0,
                    unverified=(),
                    rounds_completed=0,
                    backup_path=None,
                    source_path=source_path,
                    output_path=target_path
                )

            # Phase 2: Create backup
            backup_path = self.storage.safe_backup(source_path, skip_backup)
            self.reporter.report_backup_created(backup_path)

            # Phase 3: Read source and apply revisions
            source_content = self._read_source_file(source_path)
            self.reporter.report_applying_revisions()

            editor = self._get_editor(source_path)
            modified_content = self._apply_all_revisions(editor, source_content, revisions)

            # Phase 4: Write modified content
            self.storage.atomic_write(target_path, modified_content)
            self.reporter.info(f"Document written: {target_path}")

            # Phase 5: Verification debates
            verified_revisions = await self._run_verification_debates(
                revisions, source_content, modified_content,
                conclusion_path, max_rounds
            )

            # Phase 6: Build result
            return self._build_result(
                verified_revisions, revisions,
                max_rounds, backup_path,
                source_path, target_path
            )

        except FileNotFoundError as e:
            return RewriteResult(
                status=RewriteStatus.VALIDATION_ERROR,
                revisions_applied=0,
                revisions_verified=0,
                revisions_total=0,
                unverified=(),
                rounds_completed=0,
                backup_path=None,
                source_path=source_path,
                output_path=target_path
            )

    async def _rewrite_without_verification(
        self,
        source_path: Path,
        conclusion_path: Path,
        target_path: Path,
        skip_backup: bool
    ) -> RewriteResult:
        """Execute rewrite without debate verification."""
        try:
            # Phase 1: Read and parse
            self.reporter.report_reading_files(source_path, conclusion_path)
            revisions = self.parser.parse(conclusion_path)
            self.reporter.report_revisions_found(len(revisions))

            if not revisions:
                return RewriteResult(
                    status=RewriteStatus.VALIDATION_ERROR,
                    revisions_applied=0,
                    revisions_verified=0,
                    revisions_total=0,
                    unverified=(),
                    rounds_completed=0,
                    backup_path=None,
                    source_path=source_path,
                    output_path=target_path
                )

            # Phase 2: Create backup
            backup_path = self.storage.safe_backup(source_path, skip_backup)
            self.reporter.report_backup_created(backup_path)

            # Phase 3: Read source and apply revisions
            source_content = self._read_source_file(source_path)
            self.reporter.report_applying_revisions()

            editor = self._get_editor(source_path)
            modified_content = self._apply_all_revisions(editor, source_content, revisions)

            # Phase 4: Write modified content
            self.storage.atomic_write(target_path, modified_content)
            self.reporter.info(f"Document written: {target_path}")

            # Phase 5: Build result (all revisions considered verified without debate)
            all_verified = [rev.id for rev in revisions]
            for rev in revisions:
                rev.verified = True

            return RewriteResult(
                status=RewriteStatus.SUCCESS,
                revisions_applied=len(revisions),
                revisions_verified=len(revisions),
                revisions_total=len(revisions),
                unverified=(),
                rounds_completed=0,
                backup_path=backup_path,
                source_path=source_path,
                output_path=target_path
            )

        except FileNotFoundError as e:
            return RewriteResult(
                status=RewriteStatus.VALIDATION_ERROR,
                revisions_applied=0,
                revisions_verified=0,
                revisions_total=0,
                unverified=(),
                rounds_completed=0,
                backup_path=None,
                source_path=source_path,
                output_path=target_path
            )

    def _read_source_file(self, source_path: Path) -> str:
        """Read source file content with encoding fallback."""
        encodings = ["utf-8", "cp1251", "iso-8859-1"]
        for encoding in encodings:
            try:
                return source_path.read_text(encoding=encoding)
            except (UnicodeDecodeError, UnicodeError):
                continue
        raise RuntimeError(f"Could not decode file: {source_path}")

    def _get_editor(self, file_path: Path):
        """Get appropriate editor for file type."""
        doc_type = DocumentType.from_path(file_path)
        if doc_type == DocumentType.MARKDOWN:
            return MarkdownEditor()
        elif doc_type == DocumentType.TEXT:
            return TextEditor()
        else:
            raise ValueError(f"Unsupported document type: {doc_type}")

    def _apply_all_revisions(
        self,
        editor,
        content: str,
        revisions: List[RevisionItem]
    ) -> str:
        """Apply all revisions to content."""
        current_content = content
        applied_count = 0

        for revision in revisions:
            try:
                current_content = editor.apply_revision(current_content, revision)
                applied_count += 1
            except Exception as e:
                logger.warning(f"Failed to apply revision {revision.id}: {e}")

        self.reporter.info(f"Applied {applied_count}/{len(revisions)} revisions")
        return current_content

    async def _run_verification_debates(
        self,
        revisions: List[RevisionItem],
        source_content: str,
        modified_content: str,
        conclusion_path: Path,
        max_rounds: int
    ) -> List[str]:
        """
        Run verification debates for revisions.

        For MVP, this is a simplified implementation that marks
        all revisions as verified. Full debate integration will
        be added when prompts are ready (WP08).
        """
        # TODO: Integrate with debate system in WP08
        # For now, mark all as verified
        return [rev.id for rev in revisions]

    def get_exit_code(self, result: RewriteResult) -> int:
        """
        Get the exit code for a rewrite result.

        Maps to specification:
        - 0: SUCCESS (all revisions verified)
        - 1: PARTIAL (some revisions not verified)
        - 2: FAILED (no revisions applied)
        - 3: VALIDATION_ERROR (input files invalid)

        Args:
            result: Rewrite result from execute()

        Returns:
            Exit code (0-3)
        """
        return result.status.exit_code

    def _generate_partial_report(
        self,
        result: RewriteResult,
        output_dir: Optional[Path] = None
    ) -> None:
        """
        Generate partial completion report.

        Args:
            result: Partial rewrite result
            output_dir: Directory for report (default: current directory)
        """
        report_path = Path(self.config.partial_report_path)
        if output_dir:
            report_path = output_dir / report_path.name

        lines = [
            "# Rewrite Partial Completion Report",
            "",
            f"**Status:** {result.status.value.upper()}",
            f"**Revisions Applied:** {result.revisions_applied}/{result.revisions_total}",
            f"**Rounds Completed:** {result.rounds_completed}",
            "",
            "## Unverified Revisions",
            ""
        ]

        for rev in result.unverified:
            lines.append(f"- **{rev.id}** [{rev.section}]: {rev.content}")

        lines.extend([
            "",
            "## Recommendations",
            "",
            "- Review unverified revisions above",
            "- Consider running rewrite again with increased --max-rounds",
            "- Manually apply remaining revisions if needed",
            ""
        ])

        report_path.write_text("\n".join(lines))
        self.reporter.info(f"Partial report written: {report_path}")

    def _build_result(
        self,
        verified_revisions: List[str],
        all_revisions: List[RevisionItem],
        rounds: int,
        backup_path: Optional[Path],
        source_path: Path,
        target_path: Path
    ) -> RewriteResult:
        """Build RewriteResult from verification outcome."""
        # Mark verified revisions
        verified_set = set(verified_revisions)
        unverified = []

        for rev in all_revisions:
            if rev.id in verified_set:
                rev.verified = True
            else:
                unverified.append(rev)

        # Determine status
        if len(unverified) == 0:
            status = RewriteStatus.SUCCESS
        elif len(verified_revisions) > 0:
            status = RewriteStatus.PARTIAL
        else:
            status = RewriteStatus.FAILED

        result = RewriteResult(
            status=status,
            revisions_applied=len(all_revisions),
            revisions_verified=len(verified_revisions),
            revisions_total=len(all_revisions),
            unverified=tuple(unverified),
            rounds_completed=rounds,
            backup_path=backup_path,
            source_path=source_path,
            output_path=target_path
        )

        # Generate partial report if needed
        if status == RewriteStatus.PARTIAL:
            self._generate_partial_report(result)

        return result
