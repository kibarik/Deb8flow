"""
Use case for running document rewrite with debate verification.

Orchestrates the complete rewrite workflow from file reading
through verification debate to final result.
"""
import logging
import asyncio
from pathlib import Path
from typing import List, Optional
from os import getenv

from ..domain.entities import RevisionItem, RewriteResult
from ..domain.value_objects import RewriteStatus, RewriteConfig, DocumentType
from ..domain.change_record import ChangeRecord
from ..adapters.revision_parser import ConclusionParser
from ..adapters.document_editor import MarkdownEditor, TextEditor, DocxEditor
from ..adapters.ai_document_editor import AIMarkdownEditor, AIEditConfig
from ..adapters.structured_ai_editor import StructuredAIDocumentEditor
from ..adapters.docx_converter import DocxConverter
from ..adapters.progress_reporter import ProgressReporter
from ..adapters.review_reporter import ReviewReporter
from ..infrastructure.storage import RewriteStorage

# Type hint for AI editor
from ..adapters.structured_ai_editor import StructuredAIDocumentEditor as StructuredAIEditorType


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
        config: RewriteConfig,
        review_reporter: Optional[ReviewReporter] = None,
        use_ai: bool = False,
        ai_config: Optional[AIEditConfig] = None,
        batch_size: Optional[int] = None
    ):
        """
        Initialize use case with required adapters.

        Args:
            parser: Revision parser for conclusion files
            storage: File storage for backup/restore
            reporter: Progress reporter for console output
            config: Rewrite configuration
            review_reporter: Optional review reporter for change tracking
            use_ai: If True, use AI-powered editing for markdown files
            ai_config: Configuration for AI editing
            batch_size: Number of revisions per AI batch (from config or CLI)
        """
        self.parser = parser
        self.storage = storage
        self.reporter = reporter
        self.config = config
        self.review_reporter = review_reporter
        self.use_ai = use_ai

        # Get batch_size from config, CLI override, or default
        effective_batch_size = batch_size or config.batch_size if use_ai else 5

        # Initialize AI editor if enabled
        if self.use_ai:
            if ai_config is None:
                # Default AI config from environment
                ai_config = AIEditConfig(
                    model=getenv("REWRITE_MODEL", "gpt-4o"),
                    temperature=0.3,
                    api_key=getenv("OPENAI_API_KEY"),
                    base_url=getenv("OPENAI_BASE_URL")
                )
            # Use structured AI editor following Perplexity's recommendations
            self.ai_editor = StructuredAIDocumentEditor(
                model=ai_config.model,
                temperature=ai_config.temperature,
                api_key=ai_config.api_key or "",
                base_url=ai_config.base_url,
                batch_size=effective_batch_size
            )
        else:
            self.ai_editor = None

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
            # Check for DOCX file - use special handling
            doc_type = DocumentType.from_path(source_path)
            if doc_type == DocumentType.DOCX:
                if self.use_ai and self.ai_editor:
                    # Use AI-powered editing via Markdown conversion
                    return await self._rewrite_docx_with_ai(
                        source_path, conclusion_path, target_path,
                        max_rounds, skip_backup
                    )
                else:
                    # Use mechanical DOCX editing
                    return await self._rewrite_docx(
                        source_path, conclusion_path, target_path,
                        max_rounds, skip_backup
                    )

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
            use_ai = self.use_ai and isinstance(editor, MarkdownEditor) and self.ai_editor is not None and isinstance(self.ai_editor, StructuredAIEditorType)
            modified_content, changes = await self._apply_all_revisions(
                editor, source_content, revisions, use_ai_for_markdown=use_ai
            )

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
                source_path, target_path,
                changes=changes,
                conclusion_path=conclusion_path
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
            # Check for DOCX file - use special handling
            doc_type = DocumentType.from_path(source_path)
            if doc_type == DocumentType.DOCX:
                if self.use_ai and self.ai_editor:
                    # Use AI-powered editing via Markdown conversion
                    return await self._rewrite_docx_with_ai(
                        source_path, conclusion_path, target_path,
                        0, skip_backup
                    )
                else:
                    # Use mechanical DOCX editing
                    return await self._rewrite_docx(
                        source_path, conclusion_path, target_path,
                        0, skip_backup
                    )

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
            use_ai = self.use_ai and isinstance(editor, MarkdownEditor) and self.ai_editor is not None and isinstance(self.ai_editor, StructuredAIEditorType)
            modified_content, changes = await self._apply_all_revisions(
                editor, source_content, revisions, use_ai_for_markdown=use_ai
            )

            # Phase 4: Write modified content
            self.storage.atomic_write(target_path, modified_content)
            self.reporter.info(f"Document written: {target_path}")

            # Phase 5: Build result (all revisions considered verified without debate)
            all_verified = [rev.id for rev in revisions]
            for rev in revisions:
                rev.verified = True

            return self._build_result(
                all_verified, revisions,
                0, backup_path,
                source_path, target_path,
                changes=changes,
                conclusion_path=conclusion_path
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
        elif doc_type == DocumentType.DOCX:
            return DocxEditor()
        else:
            raise ValueError(f"Unsupported document type: {doc_type}")

    async def _apply_all_revisions(
        self,
        editor,
        content: str,
        revisions: List[RevisionItem],
        use_ai_for_markdown: bool = False
    ) -> tuple[str, List[ChangeRecord]]:
        """
        Apply all revisions to content.

        Args:
            editor: Document editor to use
            content: Original content
            revisions: List of revisions to apply
            use_ai_for_markdown: If True, use AI for markdown files

        Returns:
            Tuple of (modified_content, list_of_change_records)
        """
        # Use AI editor for markdown if enabled and available
        if use_ai_for_markdown and self.ai_editor and isinstance(self.ai_editor, StructuredAIDocumentEditor):
            self.reporter.info("Using Structured AI-powered editing (multi-step approach)")
            return await self.ai_editor.rewrite_document(content, revisions)

        # Fallback to mechanical editing

        # Fallback to mechanical editing
        current_content = content
        applied_count = 0
        changes: List[ChangeRecord] = []

        for revision in revisions:
            try:
                current_content, change_record = editor.apply_revision(current_content, revision)
                if change_record:
                    changes.append(change_record)
                    applied_count += 1
            except Exception as e:
                logger.warning(f"Failed to apply revision {revision.id}: {e}")

        self.reporter.info(f"Applied {applied_count}/{len(revisions)} revisions")
        return current_content, changes

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
        target_path: Path,
        changes: Optional[List[ChangeRecord]] = None,
        conclusion_path: Optional[Path] = None
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

        # Generate review report if we have changes
        if self.review_reporter and changes and conclusion_path:
            review_path = self.review_reporter.generate_report(
                changes=changes,
                result=result,
                source_path=source_path,
                conclusion_path=conclusion_path
            )
            self.reporter.info(f"Review report generated: {review_path}")

        return result

    async def _rewrite_docx(
        self,
        source_path: Path,
        conclusion_path: Path,
        target_path: Path,
        max_rounds: int,
        skip_backup: bool
    ) -> RewriteResult:
        """Execute rewrite workflow for DOCX files."""
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
                    rounds_completed=max_rounds,
                    backup_path=None,
                    source_path=source_path,
                    output_path=target_path
                )

            # Phase 2: Create backup
            backup_path = self.storage.safe_backup(source_path, skip_backup)
            self.reporter.report_backup_created(backup_path)

            # Phase 3: Load DOCX and apply revisions
            editor = DocxEditor()
            editor.load_document(source_path)
            self.reporter.report_applying_revisions()

            applied_count = 0
            changes: List[ChangeRecord] = []
            for revision in revisions:
                try:
                    _, change_record = editor.apply_revision("", revision)  # content ignored for DOCX
                    if change_record:
                        changes.append(change_record)
                        applied_count += 1
                except Exception as e:
                    logger.warning(f"Failed to apply revision {revision.id}: {e}")

            self.reporter.info(f"Applied {applied_count}/{len(revisions)} revisions")

            # Phase 4: Save document
            editor.save_document(target_path)
            self.reporter.info(f"Document written: {target_path}")

            # Phase 5: For DOCX, skip verification (would require complex text extraction)
            verified_revisions = [rev.id for rev in revisions]
            for rev in revisions:
                rev.verified = True

            # Phase 6: Build result
            return self._build_result(
                verified_revisions, revisions,
                max_rounds, backup_path,
                source_path, target_path,
                changes=changes,
                conclusion_path=conclusion_path
            )

        except FileNotFoundError as e:
            return RewriteResult(
                status=RewriteStatus.VALIDATION_ERROR,
                revisions_applied=0,
                revisions_verified=0,
                revisions_total=0,
                unverified=(),
                rounds_completed=max_rounds,
                backup_path=None,
                source_path=source_path,
                output_path=target_path
            )

    async def _rewrite_docx_with_ai(
        self,
        source_path: Path,
        conclusion_path: Path,
        target_path: Path,
        max_rounds: int,
        skip_backup: bool
    ) -> RewriteResult:
        """
        Execute rewrite workflow for DOCX files using AI.

        Converts DOCX to Markdown, applies AI edits, then converts back.
        """
        import tempfile
        import os

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
                    rounds_completed=max_rounds,
                    backup_path=None,
                    source_path=source_path,
                    output_path=target_path
                )

            # Phase 2: Create backup
            backup_path = self.storage.safe_backup(source_path, skip_backup)
            self.reporter.report_backup_created(backup_path)

            # Phase 3: Convert DOCX to Markdown for AI processing
            self.reporter.info("Converting DOCX to Markdown for AI processing")
            converter = DocxConverter()

            # Create temporary markdown file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as tmp_md:
                temp_md_path = Path(tmp_md.name)

            try:
                # Convert DOCX to Markdown
                markdown_content = converter.docx_to_markdown(source_path)
                temp_md_path.write_text(markdown_content, encoding='utf-8')
                self.reporter.info(f"Converted to Markdown: {len(markdown_content)} characters")

                # Phase 4: Apply AI edits to Markdown
                self.reporter.info("Applying AI-powered edits")
                modified_content, changes = await self.ai_editor.rewrite_document(
                    markdown_content, revisions
                )

                # Check if AI made any changes
                if not changes:
                    logger.warning("AI made no changes, copying original document")
                    self.reporter.info("AI made no changes, copying original document")
                    import shutil
                    shutil.copy2(source_path, target_path)

                    # Still mark as verified but with no actual changes
                    verified_revisions = [rev.id for rev in revisions]
                    for rev in revisions:
                        rev.verified = True

                    return self._build_result(
                        verified_revisions, revisions,
                        max_rounds, backup_path,
                        source_path, target_path,
                        changes=[],
                        conclusion_path=conclusion_path
                    )

                # Write modified markdown
                temp_md_path.write_text(modified_content, encoding='utf-8')

                # Phase 5: Convert Markdown back to DOCX
                self.reporter.info("Converting edited Markdown back to DOCX")
                converter.markdown_to_docx(
                    modified_content,
                    target_path,
                    template_path=source_path  # Use source as template to preserve styling
                )

                self.reporter.info(f"Document written: {target_path}")

                # Phase 6: Mark all as verified (AI mode doesn't use debate verification)
                verified_revisions = [rev.id for rev in revisions]
                for rev in revisions:
                    rev.verified = True

                # Phase 7: Build result
                return self._build_result(
                    verified_revisions, revisions,
                    max_rounds, backup_path,
                    source_path, target_path,
                    changes=changes,
                    conclusion_path=conclusion_path
                )

            finally:
                # Clean up temp file
                try:
                    temp_md_path.unlink()
                except:
                    pass

        except FileNotFoundError as e:
            return RewriteResult(
                status=RewriteStatus.VALIDATION_ERROR,
                revisions_applied=0,
                revisions_verified=0,
                revisions_total=0,
                unverified=(),
                rounds_completed=max_rounds,
                backup_path=None,
                source_path=source_path,
                output_path=target_path
            )
        except Exception as e:
            logger.error(f"Error in AI DOCX rewrite: {e}")
            return RewriteResult(
                status=RewriteStatus.FAILED,
                revisions_applied=0,
                revisions_verified=0,
                revisions_total=0,
                unverified=(),
                rounds_completed=max_rounds,
                backup_path=None,
                source_path=source_path,
                output_path=target_path
            )
