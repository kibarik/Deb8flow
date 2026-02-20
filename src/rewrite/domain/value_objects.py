"""
Value objects for rewrite domain.

These represent immutable concepts with fixed sets of values.
"""
from enum import Enum
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Dict, Any


class RevisionAction(Enum):
    """Types of revision actions that can be applied."""
    INSERT = "insert"    # Add new content
    UPDATE = "update"    # Modify existing content
    DELETE = "delete"    # Remove content


class RewriteStatus(Enum):
    """
    Final status of a rewrite operation.

    Maps directly to exit codes:
    - SUCCESS: 0 - All revisions applied and verified
    - PARTIAL: 1 - Some revisions applied but not all verified
    - FAILED: 2 - No revisions could be applied or critical error
    - VALIDATION_ERROR: 3 - Input files invalid or missing
    """
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"
    VALIDATION_ERROR = "validation_error"

    @property
    def exit_code(self) -> int:
        """Get the exit code associated with this status."""
        return {
            RewriteStatus.SUCCESS: 0,
            RewriteStatus.PARTIAL: 1,
            RewriteStatus.FAILED: 2,
            RewriteStatus.VALIDATION_ERROR: 3,
        }[self]


class DocumentType(Enum):
    """Supported document types for rewrite operations."""
    MARKDOWN = "md"
    TEXT = "txt"
    DOCX = "docx"

    @classmethod
    def from_path(cls, path: Path) -> "DocumentType":
        """Detect document type from file extension."""
        suffix = path.suffix.lower().lstrip('.')
        for doc_type in cls:
            if doc_type.value == suffix:
                return doc_type
        raise ValueError(f"Unsupported document type: {suffix}")

    def supports_sections(self) -> bool:
        """Check if this document type supports section-based editing."""
        return self == DocumentType.MARKDOWN


@dataclass(frozen=True)
class RewriteConfig:
    """
    Configuration loaded from debate_config.yaml rewrite section.

    This value object encapsulates all configuration for rewrite operations,
    making it easy to test with different configurations.

    Attributes:
        max_rounds: Maximum debate verification rounds (default: 5)
        backup_suffix: Suffix for backup files (default: ".backup")
        pro_prompt_path: Path to PRO verification prompt
        con_prompt_path: Path to CON verification prompt
        judge_prompt_path: Path to judge verdict prompt
        partial_report_path: Path for partial completion report
    """
    max_rounds: int = 5
    backup_suffix: str = ".backup"
    pro_prompt_path: Path = Path("src/prompts/rewrite/pro_verification.md")
    con_prompt_path: Path = Path("src/prompts/rewrite/con_verification.md")
    judge_prompt_path: Path = Path("src/prompts/rewrite/judge_verdict.md")
    partial_report_path: str = "rewrite_partial_report.md"

    def __post_init__(self):
        """Validate configuration values."""
        if self.max_rounds < 1:
            raise ValueError("max_rounds must be at least 1")
        if not self.backup_suffix or self.backup_suffix.strip() == "":
            raise ValueError("backup_suffix cannot be empty")

    @classmethod
    def from_dict(cls, config: Dict[str, Any]) -> "RewriteConfig":
        """
        Create RewriteConfig from loaded YAML config dict.

        Expected format:
        {
            "rewrite": {
                "max_rounds": 5,
                "backup_suffix": ".backup",
                "prompts": {
                    "pro": "src/prompts/rewrite/pro_verification.md",
                    "con": "src/prompts/rewrite/con_verification.md",
                    "judge": "src/prompts/rewrite/judge_verdict.md"
                },
                "partial_report": "rewrite_partial_report.md"
            }
        }

        Args:
            config: Full configuration dictionary from YAML

        Returns:
            RewriteConfig instance with values extracted or defaults
        """
        rewrite_config = config.get("rewrite", {})
        prompts = rewrite_config.get("prompts", {})

        return cls(
            max_rounds=rewrite_config.get("max_rounds", 5),
            backup_suffix=rewrite_config.get("backup_suffix", ".backup"),
            pro_prompt_path=Path(prompts.get("pro", "src/prompts/rewrite/pro_verification.md")),
            con_prompt_path=Path(prompts.get("con", "src/prompts/rewrite/con_verification.md")),
            judge_prompt_path=Path(prompts.get("judge", "src/prompts/rewrite/judge_verdict.md")),
            partial_report_path=rewrite_config.get("partial_report", "rewrite_partial_report.md")
        )

    def get_backup_path(self, source_path: Path) -> Path:
        """Get the backup file path for a given source file."""
        return source_path.with_suffix(source_path.suffix + self.backup_suffix)
