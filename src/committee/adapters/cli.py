"""
CLI validation adapter for product committee.

This adapter provides Pydantic models for validating and parsing
CLI arguments with proper type checking and constraints.
"""

import logging
import re
from pathlib import Path
from typing import Optional, List

from pydantic import BaseModel, Field, field_validator, model_validator


logger = logging.getLogger(__name__)


# Constants for validation
MIN_CONCURRENCY = 0
MAX_CONCURRENCY = 4
MIN_PRD_LENGTH = 100
DEFAULT_MAX_RETRIES = 2
DEFAULT_MAX_CONCURRENCY = 2
DEFAULT_OUTPUT_DIR = "./committee_output"
DEFAULT_ROLES_DIR = "prompts/roles/"


class CommitteeCliInput(BaseModel):
    """
    Validated CLI input for product committee.

    This model encapsulates all CLI arguments with validation rules
    and type coercion. It serves as the boundary between the external
    world (CLI) and the application layer.
    """

    # Required fields
    prd_path: Path = Field(..., description="Path to PRD document (.docx or .txt)")
    question: str = Field(..., min_length=1, description="Committee question for all rooms")

    # Optional fields with defaults
    model: Optional[str] = Field(None, description="LLM model name")
    max_retries: int = Field(DEFAULT_MAX_RETRIES, ge=0, description="Maximum retry attempts per room")
    max_concurrency: int = Field(DEFAULT_MAX_CONCURRENCY, ge=MIN_CONCURRENCY, le=MAX_CONCURRENCY,
                                  description="Max parallel rooms (0=all at once)")
    output_dir: Path = Field(Path(DEFAULT_OUTPUT_DIR), description="Base output directory for artifacts")
    roles_dir: Path = Field(Path(DEFAULT_ROLES_DIR), description="Directory containing role prompts")
    run_id: Optional[str] = Field(None, description="Manual run identifier (auto-generated if omitted)")
    language: Optional[str] = Field(None, description="Language for debate output")
    verbose: bool = Field(False, description="Enable verbose logging")
    quiet: bool = Field(False, description="Enable quiet mode")

    @field_validator("prd_path")
    @classmethod
    def validate_prd_exists(cls, v: Path) -> Path:
        """Validate that PRD file exists."""
        if not v.exists():
            raise ValueError(f"PRD file not found: {v}")
        if not v.is_file():
            raise ValueError(f"PRD path is not a file: {v}")
        return v

    @field_validator("prd_path")
    @classmethod
    def validate_prd_extension(cls, v: Path) -> Path:
        """Validate PRD file extension."""
        valid_extensions = {".docx", ".txt", ".md"}
        if v.suffix.lower() not in valid_extensions:
            logger.warning(f"PRD file extension {v.suffix} may not be supported")
        return v

    @field_validator("roles_dir")
    @classmethod
    def validate_roles_dir(cls, v: Path) -> Path:
        """Validate that roles directory exists and contains TPM prompt."""
        if not v.exists():
            raise ValueError(f"Roles directory not found: {v}")
        if not v.is_dir():
            raise ValueError(f"Roles path is not a directory: {v}")

        # Check required TPM prompt
        tpm_prompt = v / "tpm.txt"
        if not tpm_prompt.exists():
            raise ValueError(f"Required TPM prompt file not found: {tpm_prompt}")

        return v

    @field_validator("question")
    @classmethod
    def validate_question_not_empty(cls, v: str) -> str:
        """Validate question is not empty or whitespace only."""
        if not v or not v.strip():
            raise ValueError("Question cannot be empty")
        return v.strip()

    @field_validator("output_dir")
    @classmethod
    def validate_output_dir(cls, v: Path) -> Path:
        """Validate output directory can be created."""
        # If directory doesn't exist, parent must be writable
        if not v.exists():
            parent = v.parent
            if parent and not parent.exists():
                raise ValueError(f"Output directory parent does not exist: {parent}")
        return v

    @model_validator(mode="after")
    def validate_mutually_exclusive_flags(self) -> "CommitteeCliInput":
        """Validate that verbose and quiet are not both set."""
        if self.verbose and self.quiet:
            raise ValueError("--verbose and --quiet are mutually exclusive")
        return self

    @model_validator(mode="after")
    def warn_on_optional_role_prompts(self) -> "CommitteeCliInput":
        """Log warnings for missing optional role prompts."""
        optional_roles = ["cpo.txt", "cfo.txt", "cto.txt", "bdm.txt"]
        for role_file in optional_roles:
            role_path = self.roles_dir / role_file
            if not role_path.exists():
                role_name = role_file.replace(".txt", "").upper()
                logger.warning(f"{role_name} prompt file not found at {role_path}. Room will be skipped.")
        return self

    def get_available_roles(self) -> List[str]:
        """
        Get list of available opponent roles.

        Returns:
            List of role names (e.g., ["cpo", "cfo", "cto", "bdm"])
        """
        available = ["tpm"]  # TPM is always available (validated above)
        optional_roles = ["cpo", "cfo", "cto", "bdm"]

        for role in optional_roles:
            if (self.roles_dir / f"{role}.txt").exists():
                available.append(role)

        return available

    def get_role_prompt_path(self, role: str) -> Path:
        """
        Get path to role's prompt file.

        Args:
            role: Role name (e.g., "tpm", "cpo")

        Returns:
            Path to role's prompt file

        Raises:
            ValueError: If role prompt file doesn't exist
        """
        path = self.roles_dir / f"{role.lower()}.txt"
        if not path.exists():
            raise ValueError(f"Role prompt file not found: {path}")
        return path


def parse_arguments_to_input(args: dict) -> CommitteeCliInput:
    """
    Parse raw CLI arguments dict to validated CommitteeCliInput.

    This function serves as the bridge between argparse (or similar)
    and the Pydantic validation model.

    Args:
        args: Dictionary of CLI arguments (e.g., from argparse.Namespace)

    Returns:
        Validated CommitteeCliInput instance

    Raises:
        ValueError: If validation fails
        ValidationError: If Pydantic validation fails
    """
    try:
        return CommitteeCliInput(**args)
    except Exception as e:
        logger.error(f"Failed to validate CLI input: {e}")
        raise


def sanitize_run_id(question: str, manual_id: Optional[str] = None) -> str:
    """
    Generate run ID from question or use manual ID.

    Args:
        question: Committee question
        manual_id: Optional manual run identifier

    Returns:
        Run ID string in format RUN_{timestamp}_{slug}
    """
    if manual_id:
        # Sanitize manual ID
        sanitized = re.sub(r'[^a-zA-Z0-9_-]', '', manual_id)
        if not sanitized:
            raise ValueError("Manual run ID contains no valid characters")
        return sanitized

    # Generate slug from first 3-5 words of question
    from datetime import datetime, timezone

    words = question.strip().split()[:5]
    slug = "-".join(words).lower()
    # Remove non-alphanumeric characters except hyphens
    slug = re.sub(r'[^a-z0-9-]', '', slug)

    # Limit slug length
    if len(slug) > 50:
        slug = slug[:50].rstrip('-')

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    return f"RUN_{timestamp}_{slug}"
