# Implementation Plan: PRD Completeness Validator

**Branch**: `main` | **Date**: 2025-02-15 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `kitty-specs/010-prd-completeness-validator/spec.md`

## Summary

Add a `--check-prd` CLI command that validates Product Requirements Documents (PRDs) against a predefined template using an AI agent. The validator analyzes completeness, scores the document (0-10), identifies gaps, and provides actionable improvement suggestions via console output and a generated markdown report.

**Technical Approach**: Create a new `prd_validator_node.py` node inheriting from `BaseComponent`, following existing node patterns in the codebase. Integrate as a standalone CLI command in `main.py` with optional pipeline integration for debate pre-flight checks.

## Technical Context

**Language/Version**: Python 3.12+
**Primary Dependencies**:
- LangChain (already in project)
- LangGraph (already in project)
- Rich for console output (already in project)
- Standard library: `pathlib`, `argparse`, `re` for markdown parsing

**Storage**: N/A (reads PRD files, generates report alongside source)
**Testing**: pytest (already in project)
**Target Platform**: Cross-platform (Linux, macOS, Windows) via CLI
**Project Type**: Single project (CLI utility)
**Performance Goals**: <30 seconds for typical PRD (<5000 words)
**Constraints**: Must reuse existing LLM infrastructure (BaseComponent, LLM configs)
**Scale/Scope**: Single new node, CLI integration, no new infrastructure

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Requirements from Constitution

| Requirement | Status | Notes |
|------------|--------|-------|
| Python 3.12+ | ✅ PASS | Uses existing Python 3.12+ infrastructure |
| pytest required | ✅ PASS | Will add pytest tests for new node |
| pip installable | ✅ PASS | No new external dependencies required |
| Cross-platform | ✅ PASS | Uses pathlib for cross-platform file paths |
| Spec-driven development | ✅ PASS | Working from approved spec.md |
| TDD approach | ✅ PASS | Tests to be written before implementation |
| Minimal dependencies | ✅ PASS | Reuses existing BaseComponent, no new deps |

### Decision Log

1. **Architecture**: New node in `nodes/` directory inheriting from `BaseComponent`
   - Rationale: Follows existing patterns, reuses LLM infrastructure
   - Constitution Alignment: ✅ Minimal dependencies, spec-driven

2. **CLI Integration**: Extend `main.py` with new `--check-prd` argument
   - Rationale: Single entry point, consistent with existing CLI
   - Constitution Alignment: ✅ pip installable package

3. **Markdown Parsing**: Use Python standard library (`re` for header detection)
   - Rationale: Avoids new dependency, sufficient for ## header parsing
   - Constitution Alignment: ✅ Minimal dependencies

**All gates passed**. No violations to justify.

## Project Structure

### Documentation (this feature)

```
kitty-specs/010-prd-completeness-validator/
├── plan.md              # This file (/spec-kitty.plan command output)
├── research.md          # Phase 0 output (/spec-kitty.plan command)
├── data-model.md        # Phase 1 output (/spec-kitty.plan command)
├── quickstart.md        # Phase 1 output (/spec-kitty.plan command)
├── contracts/           # Phase 1 output (/spec-kitty.plan command)
└── tasks.md             # Phase 2 output (/spec-kitty.tasks command - NOT created by /spec-kitty.plan)
```

### Source Code (repository root)

```
nodes/
├── __init__.py                          # Existing: exports all nodes
├── base_component.py                    # Existing: base class for all nodes
├── prd_validator_node.py                # NEW: PRD validation node
└── [other existing nodes...]

prompts/
├── prd_validator_system.md              # NEW: System prompt for PRD validation
└── [other existing prompts...]

main.py                                   # MODIFIED: Add --check-prd CLI argument

tests/
├── test_prd_validator_node.py           # NEW: Unit tests for PRD validator
├── contract/
│   └── test_prd_validator_contract.py   # NEW: Contract tests for state handling
└── [other existing tests...]
```

**Structure Decision**: Single project structure with new node in `nodes/` directory. The PRD validator is a LangGraph node that can be called standalone or integrated into debate workflows. Follows existing patterns: inherits from `BaseComponent`, uses Rich for logging, and integrates via `main.py` CLI.

## Complexity Tracking

*No violations to track - all gates passed*

## Phase 0: Research & Unknowns

### Unknowns to Resolve

1. **Markdown Structure Parsing**
   - Question: How to reliably detect and extract markdown sections (## headers)?
   - Approach: Use Python `re` module with pattern `^##\s+(.+)$` for header detection
   - Fallback: If AI fails, implement basic keyword matching

2. **Scoring Algorithm**
   - Question: How to measure "depth" of content programmatically?
   - Approach: Use LLM to assess depth qualitatively; supplement with quantitative metrics (word count per section, bullet point density)

3. **Console Output Formatting**
   - Question: How to achieve the specified emoji-based format with Rich?
   - Approach: Use Rich's markup syntax with custom emoji rendering

### Research Tasks

1. **Markdown Best Practices**: Industry-standard PRD templates (Marty Cagan, Inspired)
   - Output: Reference list of well-structured PRD examples
   - Source: Already documented in spec.md FR-001

2. **LangGraph Node Integration**: How to call a node standalone vs. in workflow
   - Output: Pattern for direct node instantiation and execution
   - Source: Examine existing node usage in `workflow/debate_workflow.py`

3. **Rich Console Output**: Advanced formatting with tables, emojis, colors
   - Output: Code examples for console output format
   - Source: Rich documentation and existing usage in `main.py`

### Research Output Location

`kitty-specs/010-prd-completeness-validator/research.md`

## Phase 1: Design & Contracts

### Data Model

**Location**: `kitty-specs/010-prd-completeness-validator/data-model.md`

**Entities**:

1. **PRDValidationResult** (structured output from AI)
   ```python
   class PRDValidationResult(BaseModel):
       overall_score: int  # 0-10
       section_analysis: List[SectionAnalysis]
       recommendations: List[str]
       missing_sections: List[str]
       underdeveloped_sections: List[str]
   ```

2. **SectionAnalysis** (per-section evaluation)
   ```python
   class SectionAnalysis(BaseModel):
       section_name: str
       status: Literal["present", "missing", "underdeveloped"]
       content_quality: Optional[str]  # AI assessment
       word_count: int
       suggestions: List[str]
   ```

3. **PRDTemplate** (hardcoded template definition)
   ```python
   PRD_TEMPLATE = {
       "Executive Summary": {"required": True, "description": "Problem, Solution, Success Criteria"},
       "Background & Context": {"required": True, "description": "Market situation, User pain points"},
       # ... (all 10 sections from FR-001)
   }
   ```

### API Contracts

**Location**: `kitty-specs/010-prd-completeness-validator/contracts/`

Since this is a CLI node, the "contract" is the interface between `main.py` and the node:

**Input Contract** (from CLI to node):
```python
{
    "prd_file_path": str,  # Absolute path to PRD markdown file
    "output_format": Literal["console", "file", "both"]  # Default: "both"
}
```

**Output Contract** (from node to CLI):
```python
{
    "validation_result": PRDValidationResult,  # Structured AI output
    "report_file_path": Optional[str],  # Path to generated prd_review.md if output_format includes "file"
    "prompt_tokens": int,
    "completion_tokens": int
}
```

**CLI Behavior Contract**:
- Exit code 0: Validation successful (PRD may still have low score, but no errors)
- Exit code 1: Error (file not found, unreadable, API failure)
- Console output: Follows format specified in FR-003
- File output: Creates `prd_review.md` adjacent to source PRD

### Quickstart Guide

**Location**: `kitty-specs/010-prd-completeness-validator/quickstart.md`

**Usage Examples**:

```bash
# Basic validation
python main.py --check-prd path/to/prd.md

# Console output only
python main.py --check-prd path/to/prd.md --output-format console

# Validate before debate (with threshold)
python main.py --debate-mode=committee --prd path/to/prd.md --check-prd --min-score 6
```

**Development Workflow**:

1. Write test in `tests/test_prd_validator_node.py`
2. Implement node in `nodes/prd_validator_node.py`
3. Add prompt in `prompts/prd_validator_system.md`
4. Integrate CLI in `main.py`
5. Run tests: `pytest tests/test_prd_validator_node.py`
6. Manual test: `python main.py --check-prd tests/fixtures/sample_prd.md`

### Agent Context Update

**Agent to update**: Claude Code (current session)

**New technology to add**:
- `nodes/prd_validator_node.py`: New node for PRD validation
- `prompts/prd_validator_system.md`: System prompt for validation
- PRD template structure: 10 required sections (FR-001)

**Update location**: This session already has context; no separate agent file needed for this feature.

## Phase 1 Completion Checklist

- [ ] research.md generated with all unknowns resolved
- [ ] data-model.md created with Pydantic models
- [ ] contracts/ directory created with interface definitions
- [ ] quickstart.md created with usage examples
- [ ] Constitution Check re-evaluated (no new violations expected)
- [ ] All design artifacts committed to git

## Next Steps

After Phase 1 completion:
1. User runs `/spec-kitty.tasks` to generate work packages
2. Work packages (WP##) are created in `kitty-specs/010-prd-completeness-validator/tasks/`
3. User runs `/spec-kitty.implement WP##` to create implementation worktrees
