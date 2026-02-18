# WP06: CLI Argument Parsing and Validation

**Work Package**: 017-product-committee-clean-architecture-refactoring / WP06
**Status**: FOR_REVIEW
**Dependencies**: WP04

## Overview

Create Pydantic models for CLI validation and argument parsing. This ensures all inputs are validated before execution starts.

## Implementation Requirements

### 1. CLI Input Model (`src/committee/adapters/cli.py`)

```python
import argparse
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field, field_validator

class CommitteeCliInput(BaseModel):
    """Validated CLI input for product committee."""
    prd: str = Field(..., description="Path to PRD document")
    question: str = Field(..., min_length=1, description="Committee question")
    model: Optional[str] = Field(None, description="LLM model name")
    max_retries: int = Field(2, ge=0, description="Max retry attempts")
    max_concurrency: int = Field(2, ge=0, le=4, description="Max parallel rooms (0=all)")
    output_dir: str = Field("./committee_output", description="Output directory")
    roles_dir: str = Field("prompts/roles/", description="Role prompts directory")
    run_id: Optional[str] = Field(None, description="Manual run ID")
    language: Optional[str] = Field(None, description="Language setting")
    verbose: bool = Field(False, description="Verbose logging")
    quiet: bool = Field(False, description="Quiet mode")

    @field_validator("prd")
    def prd_must_exist(cls, v):
        if not Path(v).exists():
            raise ValueError(f"PRD file not found: {v}")
        return v

    @field_validator("question")
    def question_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("Question cannot be empty")
        return v.strip()

    @field_validator("max_retries")
    def max_retries_non_negative(cls, v):
        if v < 0:
            raise ValueError("max_retries must be >= 0")
        return v

    @field_validator("max_concurrency")
    def max_concurrency_in_range(cls, v):
        if not (0 <= v <= 4):
            raise ValueError("max_concurrency must be 0-4 (0 for unlimited)")
        return v

    @field_validator("verbose", "quiet")
    def not_both_verbose_and_quiet(cls, v, info):
        if info.data.get("verbose") and info.data.get("quiet"):
            raise ValueError("--verbose and --quiet are mutually exclusive")
        return v

    @classmethod
    def from_args(cls, args: argparse.Namespace) -> "CommitteeCliInput":
        """Create validated input from parsed arguments."""
        return cls(
            prd=args.prd,
            question=args.question,
            model=getattr(args, "model", None),
            max_retries=getattr(args, "max_retries", 2),
            max_concurrency=getattr(args, "max_concurrency", 2),
            output_dir=getattr(args, "output_dir", "./committee_output"),
            roles_dir=getattr(args, "roles_dir", "prompts/roles/"),
            run_id=getattr(args, "run_id", None),
            language=getattr(args, "language", None),
            verbose=getattr(args, "verbose", False),
            quiet=getattr(args, "quiet", False)
        )
```

### 2. Argument Parser Setup

```python
# In same file or separate
def parse_arguments() -> argparse.Namespace:
    """Parse and validate CLI arguments."""
    parser = argparse.ArgumentParser(
        description="Simulates a virtual product committee by running four sequential debate rooms.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Required arguments
    parser.add_argument(
        "--prd", "--docx",
        required=True,
        help="Path to PRD document (.docx or text file)",
    )
    parser.add_argument(
        "--question",
        required=True,
        help="Committee question for all rooms",
    )

    # Optional arguments
    parser.add_argument("--model", help="LLM model name")
    parser.add_argument(
        "--max-retries",
        type=int,
        default=2,
        help="Maximum retry attempts per room (default: 2)"
    )
    parser.add_argument(
        "--max-concurrency",
        type=int,
        default=2,
        help="Maximum parallel rooms (0=all, 1=sequential, default: 2)"
    )
    parser.add_argument(
        "--output-dir",
        default="./committee_output",
        help="Output directory for run artifacts"
    )
    parser.add_argument(
        "--roles-dir",
        default="prompts/roles/",
        help="Directory containing role prompt files"
    )
    parser.add_argument("--run-id", help="Manual run identifier")
    parser.add_argument("--language", help="Language and style setting")
    parser.add_argument("--verbose", action="store_true", help="Verbose logging")
    parser.add_argument("--quiet", action="store_true", help="Quiet mode")

    return parser.parse_args()
```

### 3. Validation Tests

```python
# tests/unit/committee/adapters/test_cli_validation.py
import pytest
from pydantic import ValidationError
from src.committee.adapters.cli import CommitteeCliInput

def test_valid_cli_input():
    input = CommitteeCliInput(
        prd="test_prd.txt",
        question="Test question",
        model="gpt-4",
        max_retries=2,
        max_concurrency=2
    )
    assert input.question == "Test question"

def test_prd_must_exist():
    with pytest.raises(ValidationError) as exc:
        CommitteeCliInput(
            prd="nonexistent.txt",
            question="Test"
        )
    assert "PRD file not found" in str(exc.value)

def test_question_not_empty():
    with pytest.raises(ValidationError) as exc:
        CommitteeCliInput(
            prd="test.txt",
            question="   "
        )
    assert "Question cannot be empty" in str(exc.value)

def test_max_concurrency_range():
    with pytest.raises(ValidationError) as exc:
        CommitteeCliInput(
            prd="test.txt",
            question="Test",
            max_concurrency=5  # Too high
        )
    assert "max_concurrency must be 0-4" in str(exc.value)

def test_verbose_quiet_mutually_exclusive():
    with pytest.raises(ValidationError) as exc:
        CommitteeCliInput(
            prd="test.txt",
            question="Test",
            verbose=True,
            quiet=True
        )
    assert "mutually exclusive" in str(exc.value)
```

## Acceptance Criteria

- [ ] All existing CLI arguments preserved
- [ ] Pydantic validation provides clear error messages
- [ ] Invalid inputs rejected before execution starts
- [ ] CLI tests validate all argument combinations
- [ ] `--prd` file existence validation
- [ ] `--question` non-empty validation
- [ ] `--max-concurrency` range validation (0-4)
- [ ] `--verbose` and `--quiet` mutual exclusivity

## Files to Create

1. `src/committee/adapters/cli.py`
2. `tests/unit/committee/adapters/test_cli_validation.py`

## Notes

- Pydantic used ONLY at boundary (not in domain)
- All error messages must be user-friendly
- Preserve exact CLI argument names from current implementation
- Validation happens BEFORE any expensive operations

## Next Steps

After completing this work package:
1. Run `pytest tests/unit/committee/adapters/test_cli_validation.py`
2. Test with various invalid inputs to verify error messages
3. Commit changes with message "feat: implement CLI validation with Pydantic (WP06)"
4. Move to WP07 (Product Committee CLI Refactoring)
