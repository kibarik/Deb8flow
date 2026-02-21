"""
CLI adapter for rewrite feature.

Provides argument parsing and validation for the rewrite command.
"""
import argparse
import json
import logging
import re
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field, field_validator


logger = logging.getLogger(__name__)


# Constants
DEFAULT_MAX_ROUNDS = None  # None = use config default
DEFAULT_OUTPUT = None  # None = overwrite source


def find_latest_committee_run() -> tuple[Optional[Path], Optional[Path]]:
    """
    Find the latest committee run directory and return paths to conclusion.md and source file.

    Returns:
        Tuple of (conclusion_path, source_file_path) or (None, None) if not found
    """
    committee_dir = Path("committee_output")
    if not committee_dir.exists():
        return None, None

    # Find all conclusion.md files and sort by modification time
    conclusion_files = list(committee_dir.glob("*/conclusion.md"))
    if not conclusion_files:
        return None, None

    # Sort by modification time (newest first)
    conclusion_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    latest_conclusion = conclusion_files[0]
    run_dir = latest_conclusion.parent

    # Try to get source file from metadata.json
    metadata_file = run_dir / "metadata.json"
    source_file = None

    if metadata_file.exists():
        try:
            with open(metadata_file, "r", encoding="utf-8") as f:
                metadata = json.load(f)
            prd_path = metadata.get("prd_path")
            if prd_path:
                source_file = Path(prd_path)
                if source_file.exists():
                    logger.info(f"Found source file from metadata: {source_file}")
                else:
                    # Try relative path from run directory
                    source_file = run_dir / Path(prd_path).name
                    if source_file.exists():
                        logger.info(f"Found source file in run directory: {source_file}")
                    else:
                        source_file = None
        except Exception as e:
            logger.debug(f"Could not read metadata.json: {e}")

    # If no source file from metadata, look for document files in run directory
    if source_file is None:
        for ext in [".docx", ".md", ".txt"]:
            candidates = list(run_dir.glob(f"*{ext}"))
            if candidates:
                source_file = candidates[0]
                logger.info(f"Found source file in run directory: {source_file}")
                break

    return latest_conclusion, source_file


class RewriteCliInput(BaseModel):
    """
    Validated CLI input for rewrite command.

    Attributes:
        file_path: Path to source document to modify
        conclusion_path: Path to conclusion.md with revisions
        max_rounds: Optional override for max debate rounds
        output_path: Optional output file path (default: overwrite input)
        no_backup: Skip backup creation flag
        verbose: Enable verbose output flag
        use_ai: Use AI-powered editing for enhanced quality
    """
    file_path: Path = Field(..., description="Path to source document")
    conclusion_path: Path = Field(..., description="Path to conclusion.md")
    max_rounds: Optional[int] = Field(None, ge=0, description="Max debate rounds (0 = skip verification)")
    batch_size: Optional[int] = Field(None, ge=1, description="Revisions per AI batch (default: 5)")
    output_path: Optional[Path] = Field(None, description="Output file path")
    no_backup: bool = Field(False, description="Skip backup creation")
    verbose: bool = Field(False, description="Enable verbose output")
    use_ai: bool = Field(True, description="Use AI-powered editing for markdown files")

    @field_validator("file_path", "conclusion_path")
    @classmethod
    def validate_file_exists(cls, v: Path) -> Path:
        """Validate that file exists."""
        if not v.exists():
            raise ValueError(f"File not found: {v}")
        if not v.is_file():
            raise ValueError(f"Path is not a file: {v}")
        return v

    @field_validator("conclusion_path")
    @classmethod
    def validate_conclusion_has_recommendations(cls, v: Path) -> Path:
        """Validate that conclusion.md contains recommendations."""
        import re

        content = v.read_text(encoding="utf-8", errors="ignore")

        # Check for Recommendations section
        if "## Рекомендации" not in content:
            raise ValueError(
                f"conclusion.md does not contain a '## Рекомендации' section.\n"
                f"Please run the committee first to generate recommendations:\n"
                f"  python3 scripts/product_committee --file <document> --question \"<question>\"\n"
                f"Or generate conclusion from existing dialogues:\n"
                f"  python3 scripts/conclusion_results --dir <committee_run_dir>"
            )

        # Check for actual numbered recommendations (not just "Нет доступных рекомендаций")
        recommendations_section = re.search(r'## Рекомендации\s*(.*?)(?:\n##|\Z)', content, re.DOTALL)
        if recommendations_section:
            section_text = recommendations_section.group(1)
            # Check for numbered items (1. 2. 3. etc.)
            has_numbered = bool(re.search(r'^\d+\.', section_text, re.MULTILINE))
            # Check if it says "нет рекомендаций" or similar
            has_no_rec = any(phrase in section_text.lower() for phrase in [
                "нет доступных рекомендаций",
                "нет рекомендаций",
                "no recommendations",
                "no available"
            ])

            if has_no_rec and not has_numbered:
                raise ValueError(
                    f"conclusion.md contains no recommendations (\"нет доступных рекомендаций\").\n"
                    f"The committee did not produce any actionable revisions.\n"
                    f"\n"
                    f"Please run the committee again to generate recommendations:\n"
                    f"  python3 scripts/product_committee --file <document> --question \"<question>\"\n"
                    f"Or use a conclusion from a different committee run that has recommendations."
                )

        return v

    @field_validator("file_path")
    @classmethod
    def validate_file_extension(cls, v: Path) -> Path:
        """Validate file extension is supported."""
        valid_extensions = {".md", ".txt", ".docx"}
        if v.suffix.lower() not in valid_extensions:
            logger.warning(f"File extension {v.suffix} may not be supported")
        return v

    @field_validator("output_path")
    @classmethod
    def validate_output_dir_writable(cls, v: Optional[Path]) -> Optional[Path]:
        """Validate output directory is writable."""
        if v is None:
            return v
        if v.exists():
            if not v.is_file():
                raise ValueError(f"Output path exists but is not a file: {v}")
        else:
            parent = v.parent
            if parent and not parent.exists():
                raise ValueError(f"Output directory does not exist: {parent}")
        return v


def create_argument_parser() -> argparse.ArgumentParser:
    """
    Create argument parser for rewrite command.

    Returns:
        Configured ArgumentParser instance
    """
    parser = argparse.ArgumentParser(
        prog="rewrite",
        description="Apply revisions from conclusion.md to source document with AI-powered editing",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Quick mode - use latest committee run (auto-detects file and conclusion)
  %(prog)s

  # Basic rewrite with explicit paths
  %(prog)s --file prd.md --conclusion committee_output/RUN_123/conclusion.md

  # Custom round limit
  %(prog)s --file prd.md --conclusion ... --max-rounds 10

  # Output to different file
  %(prog)s --file prd.md --conclusion ... --output prd_revised.md

  # Skip backup
  %(prog)s --file prd.md --conclusion ... --no-backup

  # Disable AI (mechanical text replacement only)
  %(prog)s --file prd.md --conclusion ... --no-ai

Quick Mode:
  When --file and --conclusion are not specified, the script will:
  - Find the most recent committee run in committee_output/
  - Use its conclusion.md
  - Extract the source file path from metadata.json
        """
    )

    # Optional arguments (auto-detect if not specified)
    parser.add_argument(
        "--file",
        type=Path,
        required=False,
        metavar="PATH",
        help="Path to source document to modify (.md, .txt, .docx). Auto-detected from latest committee run if not specified."
    )

    parser.add_argument(
        "--conclusion",
        type=Path,
        required=False,
        metavar="PATH",
        help="Path to conclusion.md with revisions. Auto-detected from latest committee run if not specified."
    )

    # Optional arguments
    parser.add_argument(
        "--max-rounds",
        type=int,
        default=None,
        metavar="N",
        help="Maximum debate verification rounds (default: from config)"
    )

    parser.add_argument(
        "--batch-size",
        type=int,
        default=None,
        metavar="N",
        help="Revisions per AI batch (default: 5). 50 revisions + --batch-size 5 = 10 passes"
    )

    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=None,
        metavar="PATH",
        help="Output file path (default: overwrite source file)"
    )

    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Skip backup creation (use with caution)"
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose output"
    )

    parser.add_argument(
        "--ai",
        dest="ai",
        action="store_true",
        help="Use AI-powered editing for enhanced quality (default: enabled)"
    )

    parser.add_argument(
        "--no-ai",
        dest="ai",
        action="store_false",
        help="Disable AI-powered editing (use mechanical text replacement)"
    )

    parser.set_defaults(ai=True)

    return parser


def parse_arguments(args: dict) -> RewriteCliInput:
    """
    Parse raw CLI arguments dict to validated RewriteCliInput.

    If file or conclusion are not specified, auto-detect from latest committee run.

    Args:
        args: Dictionary of CLI arguments (e.g., from argparse.Namespace)

    Returns:
        Validated RewriteCliInput instance

    Raises:
        ValueError: If validation fails
    """
    # Auto-detect if not specified
    file_path = args.get("file")
    conclusion_path = args.get("conclusion")

    if file_path is None or conclusion_path is None:
        logger.info("No --file or --conclusion specified, auto-detecting from latest committee run...")
        auto_conclusion, auto_file = find_latest_committee_run()

        if conclusion_path is None:
            if auto_conclusion is None:
                raise ValueError(
                    "Could not auto-detect conclusion.md. Please specify --conclusion argument.\n"
                    "Run the committee first: python3 scripts/product_committee --file <document>"
                )
            conclusion_path = auto_conclusion
            logger.info(f"Auto-detected conclusion: {conclusion_path}")

        if file_path is None:
            if auto_file is None:
                raise ValueError(
                    "Could not auto-detect source file from metadata.json.\n"
                    "Please specify --file argument."
                )
            file_path = auto_file
            logger.info(f"Auto-detected source file: {file_path}")

    # Map argparse argument names to Pydantic field names
    mapped_args = {
        "file_path": file_path,
        "conclusion_path": conclusion_path,
        "max_rounds": args.get("max_rounds"),
        "batch_size": args.get("batch_size"),
        "output_path": args.get("output"),
        "no_backup": args.get("no_backup", False),
        "verbose": args.get("verbose", False),
        "use_ai": args.get("ai", True)
    }

    try:
        return RewriteCliInput(**mapped_args)
    except Exception as e:
        logger.error(f"CLI validation failed: {e}")
        raise


def validate_conclusion_format(conclusion_path: Path) -> None:
    """
    Validate conclusion.md has expected format.

    Args:
        conclusion_path: Path to conclusion file

    Raises:
        ValueError: If format is invalid
    """
    content = conclusion_path.read_text()

    # Check for Russian header
    if "## Рекомендации" not in content:
        if "##" not in content:
            raise ValueError(
                f"conclusion.md appears invalid: no section headers found.\n"
                f"Expected format: ## Рекомендации followed by numbered list"
            )
        else:
            logger.warning(
                f"conclusion.md may not be in expected format "
                f"(missing '## Рекомендации' section)"
            )

    # Check for numbered items
    lines = content.split("\n")
    has_numbered = any(re.match(r"^\d+\.", line) for line in lines)
    if not has_numbered:
        raise ValueError(
            f"conclusion.md contains no numbered items.\n"
            f"Expected format: '1. Revision text [Room]'"
        )


def validate_document_type(file_path: Path) -> str:
    """
    Detect and validate document type.

    Args:
        file_path: Path to source document

    Returns:
        Document type string ("markdown", "text", "docx")

    Raises:
        ValueError: If type not supported
    """
    suffix = file_path.suffix.lower()
    type_map = {
        ".md": "markdown",
        ".txt": "text",
        ".docx": "docx"
    }

    if suffix not in type_map:
        raise ValueError(
            f"Unsupported file type: {suffix}\n"
            f"Supported types: {', '.join(type_map.keys())}"
        )

    return type_map[suffix]


def load_rewrite_config(
    cli_input: RewriteCliInput,
    config_path: Optional[Path] = None
):
    """
    Load rewrite configuration with CLI overrides.

    Args:
        cli_input: Validated CLI input
        config_path: Optional path to config file

    Returns:
        RewriteConfig with CLI overrides applied
    """
    # Import here to avoid circular dependency
    from src.shared.config import load_config
    from ..domain.value_objects import RewriteConfig

    # Load base configuration
    try:
        debate_config = load_config(str(config_path) if config_path else None)
        config_dict = debate_config.to_dict()
    except Exception as e:
        logger.warning(f"Failed to load config: {e}, using defaults")
        config_dict = {}

    # Apply CLI overrides
    if cli_input.max_rounds is not None:
        if "rewrite" not in config_dict:
            config_dict["rewrite"] = {}
        config_dict["rewrite"]["max_rounds"] = cli_input.max_rounds

    if cli_input.batch_size is not None:
        if "rewrite" not in config_dict:
            config_dict["rewrite"] = {}
        config_dict["rewrite"]["batch_size"] = cli_input.batch_size

    # Create RewriteConfig
    rewrite_config = RewriteConfig.from_dict(config_dict)

    logger.info(f"Config loaded: max_rounds={rewrite_config.max_rounds}")

    return rewrite_config
