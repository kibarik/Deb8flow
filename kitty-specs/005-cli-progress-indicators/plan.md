# Implementation Plan: CLI Progress Indicators for Document Debate

**Branch**: `main` | **Date**: 2025-02-14 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/kitty-specs/005-cli-progress-indicators/spec.md`

## Summary

Add real-time progress tracking to the document debate CLI workflow using tqdm for progress bars and indicators. The workflow will display detailed step-by-step progress by default, with support for `--verbose` and `--quiet` flags to control verbosity levels. This eliminates user uncertainty during long-running LLM operations.

## Technical Context

**Language/Version**: Python 3.9+
**Primary Dependencies**: langgraph, langchain, python-docx, rich (existing), tqdm (new)
**Storage**: N/A (in-memory workflow state)
**Testing**: pytest (existing framework)
**Target Platform**: CLI (macOS, Linux, Windows terminals)
**Project Type**: single (CLI tool with LangGraph workflow)
**Performance Goals**: Progress tracking adds < 5% execution time overhead
**Constraints**: Must work with existing LangGraph workflow structure, non-blocking progress updates
**Scale/Scope**: Single CLI module, ~5 workflow nodes to instrument

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

No constitution file exists - skipping constitution check.

## Project Structure

### Documentation (this feature)

```
kitty-specs/005-cli-progress-indicators/
├── plan.md              # This file (/spec-kitty.plan command output)
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output (N/A - no API contracts)
```

### Source Code (repository root)

```
src/
└── progress/                    # New module for progress tracking
    ├── __init__.py
    ├── progress_manager.py      # Main progress tracking interface
    └── cli_output.py            # Verbosity level management

nodes/
├── document_topic_node.py       # Existing - will add progress hooks
├── pro_debater_node.py          # Existing - will add progress hooks
├── con_debater_node.py          # Existing - will add progress hooks
├── debate_moderator_node.py     # Existing - will add progress hooks
├── fact_check_node.py           # Existing - will add progress hooks
├── fact_check_router_node.py    # Existing - minimal/no progress needed
└── judge_node.py                # Existing - will add progress hooks

workflow/
└── document_debate_workflow.py   # Existing - will integrate progress

tests/
├── unit/
│   ├── test_progress_manager.py
│   └── test_cli_output.py
└── integration/
    └── test_progress_workflow.py

requirements.txt                 # Existing - will add tqdm
document_debate_cli.py           # Existing - will add verbosity flags
```

**Structure Decision**: Single project structure with a new `src/progress/` module for reusable progress tracking components. Existing nodes and workflow will be instrumented with progress hooks without major restructuring.

## Complexity Tracking

*Fill ONLY if Constitution Check has violations that must be justified*

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | N/A | N/A |

---

## Phase 0: Research & Technology Decisions

### Research Tasks

1. **tqdm Integration Patterns**
   - Research tqdm usage in async/await contexts with LangGraph workflows
   - Identify best practices for non-blocking progress updates
   - Determine how to integrate tqdm with existing rich logging

2. **Verbosity Flag Implementation**
   - Research argparse verbosity flag patterns (click vs argparse)
   - Investigate quiet/verbose mode implementations in similar CLI tools
   - Determine interaction between tqdm and rich console output

3. **LangGraph Callback/Hook Points**
   - Research LangGraph callback mechanisms for progress tracking
   - Identify if nodes can emit progress events during execution
   - Determine if middleware/interceptor pattern is viable

### Expected Research Output

Create `research.md` documenting:
- tqdm async integration patterns
- Verbosity flag implementation approach
- LangGraph progress hook strategy
- Code examples for each pattern

---

## Phase 1: Design & Contracts

### Data Model

Create `data-model.md` defining:
- ProgressLevel enum (QUIET, DEFAULT, VERBOSE)
- ProgressEvent structure (step_name, current, total, sub_steps)
- ProgressManager interface

### API/Interface Contracts

Create interface contracts in `contracts/`:

**contracts/progress_manager_interface.md**
```python
class ProgressManager:
    """Manages progress display for workflow execution."""

    def __init__(self, level: ProgressLevel = ProgressLevel.DEFAULT):
        """Initialize with verbosity level."""

    def start_step(self, name: str, total: int, current: int) -> None:
        """Begin a new workflow step with progress tracking."""

    def update_progress(self, increment: int = 1) -> None:
        """Update current step progress."""

    def complete_step(self) -> None:
        """Mark current step as complete."""

    def set_verbosity(self, level: ProgressLevel) -> None:
        """Change verbosity level dynamically."""

    def close(self) -> None:
        """Clean up progress bars and indicators."""
```

**contracts/cli_output_interface.md**
```python
class CLIOutput:
    """Manages CLI output based on verbosity level."""

    def info(self, message: str) -> None:
        """Display info message (hidden in quiet mode)."""

    def verbose(self, message: str) -> None:
        """Display verbose message (only in verbose mode)."""

    def error(self, message: str) -> None:
        """Display error message (always shown)."""

    def success(self, message: str) -> None:
        """Display success message (always shown)."""
```

### Quickstart Guide

Create `quickstart.md` with:
- How to run the CLI with progress indicators
- Verbosity flag usage examples
- Troubleshooting progress display issues

### Agent Context Update

Run agent context update scripts to add tqdm and progress tracking patterns.

---

## Design Justification

### Why tqdm

1. **Lightweight**: Minimal dependencies, single-package solution
2. **Cross-platform**: Works on macOS, Linux, Windows without issues
3. **Async-safe**: Supports non-blocking updates in async contexts
4. **Standard**: Widely-used, well-documented, stable API
5. **Compatible**: Works alongside existing rich logging infrastructure

### Why New src/progress/ Module

1. **Separation of Concerns**: Progress logic isolated from workflow/nodes
2. **Reusability**: Can be used by other CLI tools in the project
3. **Testability**: Easy to unit test progress manager independently
4. **Maintainability**: Clear ownership of progress-related code

### Why Verbosity Levels

1. **User Flexibility**: Different users have different output preferences
2. **Debugging Support**: Verbose mode aids troubleshooting
3. **CI/CD Friendly**: Quiet mode for automated scripts
4. **Default UX**: Balanced default for typical interactive use

---

## Implementation Phases (Summary)

**Phase 0**: Research → `research.md`
**Phase 1**: Design → `data-model.md`, `contracts/*`, `quickstart.md`

**STOP HERE** - Use `/spec-kitty.tasks` to generate work packages when ready.
