# CLI Interface Contract: PRD Completeness Validator

**Feature**: 010-prd-completeness-validator
**Date**: 2025-02-15
**Phase**: Phase 1 - Design & Contracts

## Overview

This document defines the contract between the CLI (`main.py`) and the PRD validator node (`nodes/prd_validator_node.py`).

## CLI Arguments

### Primary Command

```bash
python main.py --check-prd <path-to-prd> [options]
```

### Arguments Specification

| Argument | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `--check-prd` | flag | Yes | - | Enable PRD validation mode |
| `<path-to-prd>` | string | Yes | - | Absolute or relative path to PRD markdown file |
| `--output-format` | enum | No | `both` | Output format: `console`, `file`, or `both` |
| `--min-score` | integer | No | None | Minimum score threshold (0-10) for pipeline integration |

### Argument Parsing Implementation

```python
import argparse

def parse_args():
    parser = argparse.ArgumentParser(description="Deb8flow - AI Debate Framework")

    # Existing debate arguments
    parser.add_argument(
        "--debate-mode",
        choices=["standard", "committee", "document"],
        help="Debate mode to run"
    )

    # New PRD validator arguments
    parser.add_argument(
        "--check-prd",
        type=str,
        metavar="PATH",
        help="Validate a PRD document against the template"
    )

    parser.add_argument(
        "--output-format",
        choices=["console", "file", "both"],
        default="both",
        help="Output format for validation results"
    )

    parser.add_argument(
        "--min-score",
        type=int,
        choices=range(0, 11),
        metavar="0-10",
        help="Minimum acceptable score (for pipeline integration)"
    )

    return parser.parse_args()
```

## Input Contract

### From CLI to Node

```python
{
    "prd_file_path": str,  # Absolute path to PRD markdown file
    "output_format": Literal["console", "file", "both"],  # Default: "both"
}
```

### Validation Rules

1. **`prd_file_path`**:
   - Must be a valid file path
   - File must exist (or raise `FileNotFoundError`)
   - Should have `.md` extension (warning if not)
   - Must be readable

2. **`output_format`**:
   - Must be one of: `"console"`, `"file"`, `"both"`
   - Default: `"both"`

## Output Contract

### From Node to CLI

```python
{
    "validation_result": PRDValidationResult,  # Structured AI output
    "report_file_path": Optional[str],  # Path to generated prd_review.md
    "prompt_tokens": int,
    "completion_tokens": int,
    "error": Optional[str]  # Only present if validation failed
}
```

### Exit Codes

| Code | Meaning | Usage |
|------|---------|-------|
| 0 | Success | Validation completed (PRD may have low score, but no errors) |
| 1 | Error | File not found, unreadable, or API failure |
| 2 | Invalid arguments | Missing required args, invalid values |

## Console Output Format

### Success Output

```
📋 PRD Validation Report
═══════════════════════════════════════════
File: path/to/prd.md
Score: 7/10 (Good)

✅ Present Sections (8/10):
  • Executive Summary
  • Background & Context
  • Goals & Success Metrics
  • User Personas
  • Functional Requirements
  • Non-Functional Requirements
  • Technical Constraints
  • Timeline & Milestones

❌ Missing Sections (2/10):
  • Risks & Mitigations
  • Open Questions

⚠️  Underdeveloped Sections:
  • User Personas (insufficient detail on use cases)
  • Functional Requirements (missing user story format)

💡 Top Recommendations:
  1. Add "Risks & Mitigations" section with identified project risks
  2. Add "Open Questions" section for unresolved decisions
  3. Expand "User Personas" with specific use case scenarios

📄 Detailed report: prd_review.md
```

### Error Output

```
❌ Error: PRD file not found: path/to/prd.md

Usage: python main.py --check-prd <path-to-prd>

Example: python main.py --check-prd my_product_prd.md
```

## File Output Format

### Report File Location

- **Name**: `prd_review.md`
- **Location**: Adjacent to source PRD file
- **Overwrite**: Always overwrites existing `prd_review.md`

### Report Structure

```markdown
# PRD Validation Report

**Generated**: 2025-02-15 at 14:30 UTC
**Source File**: path/to/prd.md
**Validator**: Deb8flow PRD Completeness Validator v1.0

## Executive Summary

**Overall Score**: 7/10 (Good)

**Assessment**: The PRD covers most required sections but is missing critical risk analysis and open questions. The functional requirements section needs more detail in user story format.

## Section-by-Section Analysis

### Executive Summary
- **Status**: ✅ Present
- **Word Count**: 127
- **Quality**: Well-written problem statement with clear success criteria
- **Suggestions**: None - this section is strong

### Background & Context
- **Status**: ✅ Present
- **Word Count**: 234
- **Quality**: Good market context, but missing user pain point details
- **Suggestions**:
  - Add specific user pain points with examples
  - Include market size or competitive landscape data

### Risks & Mitigations
- **Status**: ❌ Missing
- **Suggestions**:
  - Identify technical risks (e.g., integration complexity)
  - Identify business risks (e.g., market adoption)
  - Propose mitigation strategies for each risk

### Open Questions
- **Status**: ❌ Missing
- **Suggestions**:
  - List unresolved decisions (e.g., architecture choices)
  - Identify areas requiring stakeholder input

## Recommendations by Priority

### High Priority
- [ ] Add "Risks & Mitigations" section with at least 3 identified risks and mitigation strategies
- [ ] Add "Open Questions" section documenting unresolved decisions

### Medium Priority
- [ ] Expand "User Personas" with specific use case scenarios
- [ ] Convert functional requirements to user story format: "As a [user], I want [feature] so that [benefit]"

### Low Priority
- [ ] Add quantitative metrics to success criteria
- [ ] Include competitive analysis in background section

## Best Practices Reference

For examples of well-written PRD sections, see:
- Marty Cagan's "INSPIRED" - Chapter on Product Requirements
- Silicon Valley Product Group templates

## Next Steps

1. Address the missing and underdeveloped sections above
2. Re-run validation: `python main.py --check-prd path/to/prd.md`
3. Aim for score 8+ before using this PRD for committee debate

## Scoring Breakdown

- **Presence (40%)**: 3.2/4 (8 of 10 sections present)
- **Depth (40%)**: 2.8/4 (several sections need more detail)
- **Coherence (20%)**: 1.0/2 (good flow but missing connections between sections)
```

## Pipeline Integration

### Pre-flight Check Behavior

When `--check-prd` is combined with `--debate-mode`:

```bash
python main.py --debate-mode=committee --prd path/to/prd.md --check-prd --min-score 6
```

**Behavior**:

1. Run PRD validation first
2. If score >= `--min-score`: Proceed to debate
3. If score < `--min-score`: Prompt user

```
⚠️  PRD Score Below Threshold

Score: 4/10 (Threshold: 6/10)

The PRD appears incomplete. Continuing may result in an unfocused debate.

Options:
  1. View recommendations and abort
  2. View recommendations and continue anyway
  3. Continue without viewing

Enter choice (1-3):
```

## Integration Points

### main.py Modifications

```python
async def main():
    setup_logging()
    validate_env()
    logger = logging.getLogger("main")

    args = parse_args()

    # PRD validation mode
    if args.check_prd:
        from nodes.prd_validator_node import PRDValidatorNode
        from configurations.llm_config import OpenAILLMConfig

        llm_config = OpenAILLMConfig(
            model_name="gpt-4",
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )

        validator = PRDValidatorNode(llm_config=llm_config)

        try:
            result = validator.validate_prd(
                prd_path=args.check_prd,
                output_format=args.output_format
            )

            # Pipeline integration: check threshold
            if args.min_score and result['validation_result'].overall_score < args.min_score:
                handle_low_score(result, args.min_score)

            return  # Exit after validation

        except FileNotFoundError as e:
            console.print(f"[red]Error: {e}[/]")
            sys.exit(1)
        except Exception as e:
            logger.error(f"Validation failed: {e}", exc_info=True)
            sys.exit(1)

    # Existing debate workflow
    # ...
```

## Test Cases

### Contract Tests

```python
# tests/contract/test_prd_validator_contract.py

def test_cli_accepts_prd_path():
    """Test that CLI accepts PRD path argument"""
    # Test implementation

def test_cli_accepts_output_format():
    """Test that CLI accepts output format option"""
    # Test implementation

def test_cli_rejects_invalid_output_format():
    """Test that CLI rejects invalid output format"""
    # Test implementation

def test_node_returns_expected_structure():
    """Test that node returns expected output structure"""
    # Test implementation

def test_exit_code_zero_on_success():
    """Test exit code 0 on successful validation"""
    # Test implementation

def test_exit_code_one_on_file_not_found():
    """Test exit code 1 when file not found"""
    # Test implementation
```

## References

1. **Specification**: `kitty-specs/010-prd-completeness-validator/spec.md`
2. **Data Model**: `kitty-specs/010-prd-completeness-validator/data-model.md`
3. **argparse documentation**: https://docs.python.org/3/library/argparse.html
