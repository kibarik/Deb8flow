"""
CLI adapter for rewrite feature.

Provides argument parsing and validation for the rewrite command.
"""
import argparse
import logging
import re
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field, field_validator


logger = logging.getLogger(__name__)


# Constants
DEFAULT_MAX_ROUNDS = None  # None = use config default
DEFAULT_OUTPUT = None  # None = overwrite source


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
  # Basic rewrite (AI-powered by default)
  %(prog)s --file prd.md --conclusion committee_output/RUN_123/conclusion.md

  # Custom round limit
  %(prog)s --file prd.md --conclusion ... --max-rounds 10

  # Output to different file
  %(prog)s --file prd.md --conclusion ... --output prd_revised.md

  # Skip backup
  %(prog)s --file prd.md --conclusion ... --no-backup

  # Disable AI (mechanical text replacement only)
  %(prog)s --file prd.md --conclusion ... --no-ai
        """
    )

    # Required arguments
    parser.add_argument(
        "--file",
        type=Path,
        required=True,
        metavar="PATH",
        help="Path to source document to modify (.md, .txt, .docx)"
    )

    parser.add_argument(
        "--conclusion",
        type=Path,
        required=True,
        metavar="PATH",
        help="Path to conclusion.md with revisions"
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

    Args:
        args: Dictionary of CLI arguments (e.g., from argparse.Namespace)

    Returns:
        Validated RewriteCliInput instance

    Raises:
        ValueError: If validation fails
    """
    # Map argparse argument names to Pydantic field names
    mapped_args = {
        "file_path": args.get("file"),
        "conclusion_path": args.get("conclusion"),
        "max_rounds": args.get("max_rounds"),
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

    # Create RewriteConfig
    rewrite_config = RewriteConfig.from_dict(config_dict)

    logger.info(f"Config loaded: max_rounds={rewrite_config.max_rounds}")

    return rewrite_config
