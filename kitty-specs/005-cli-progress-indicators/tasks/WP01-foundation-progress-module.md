---
work_package_id: WP01
title: Foundation - Progress Module
lane: planned
dependencies: []
subtasks:
- T001
- T002
- T003
- T004
- T005
phase: Phase 1
assignee: ''
agent: ''
shell_pid: ''
review_status: ''
reviewed_by: ''
history:
- timestamp: '2025-02-14T00:00:00Z'
  lane: planned
  agent: system
  shell_pid: ''
  action: Prompt generated via /spec-kitty.tasks
---

# Work Package WP01 – Foundation - Progress Module

## ⚠️ IMPORTANT: Review Feedback Status

**Read this first if you are implementing this task!**

- **Has review feedback?**: Check the `review_status` field above. If it says `has_feedback`, scroll to the **Review Feedback** section immediately (right below this notice).
- **You must address all feedback** before your work is complete. Feedback items are your implementation TODO list.
- **Mark as acknowledged**: When you understand the feedback and begin addressing it, update `review_status: acknowledged` in the frontmatter.
- **Report progress**: As you address each feedback item, update the Activity Log explaining what you changed.

---

## Review Feedback

> **Populated by `/spec-kitty.review`** – Reviewers add detailed feedback here when work needs changes. Implementer must address every item listed below before returning for re-review.

*[This section is empty initially. Reviewers will populate it if the work is returned from review. If you see feedback here, treat each item as a must-Do before completion.]*

---

## Markdown Formatting

Wrap HTML/XML tags in backticks: `<div>`, `<script>`

Use language identifiers in code blocks: ````python`, ````bash`

---

## Objectives & Success Criteria

- **Create `src/progress/` module** with ProgressLevel enum, ProgressManager class, and CLIOutput class
- **Unit test coverage** for ProgressManager with verbosity filtering
- **Module exports** both classes through `__init__.py`
- **Zero existing code impact** (new module only)

## Context & Constraints

### Prerequisite Work
None (this is the foundational work package)

### Related Documents
- Spec: `kitty-specs/005-cli-progress-indicators/spec.md`
- Plan: `kitty-specs/005-cli-progress-indicators/plan.md`
- Data Model: `kitty-specs/005-cli-progress-indicators/data-model.md`
- Contracts:
  - `kitty-specs/005-cli-progress-indicators/contracts/progress_manager_interface.md`
  - `kitty-specs/005-cli-progress-indicators/contracts/cli_output_interface.md`
- Research: `kitty-specs/005-cli-progress-indicators/research.md`

### Architectural Decisions
- Use `tqdm.rich.tqdm` for Rich-compatible progress bars
- ProgressManager injected through state, not stored
- Underscore prefix `_progress_manager` indicates transient state data
- CLIOutput separates output filtering from progress display

---

## Subtasks & Detailed Guidance

### Subtask T001 – Create ProgressLevel enum

**Purpose**: Define the three verbosity levels (QUIET, DEFAULT, VERBOSE) as an enum for type safety and clear API.

**Files**:
- `src/progress/__init__.py` (new file, create directory first)

**Steps**:
1. Create `src/progress/` directory if it doesn't exist
2. Create `__init__.py` with ProgressLevel enum:
   ```python
   from enum import Enum

   class ProgressLevel(Enum):
       """Verbosity level for CLI progress display."""
       QUIET = 0      # Minimal output - only errors and final results
       DEFAULT = 1     # Standard step-by-step progress
       VERBOSE = 2     # Detailed sub-step progress and timing
   ```
3. Export enum from module

**Parallel?**: Yes (independent file)

**Validation**:
- [ ] Enum has exactly three values: QUIET=0, DEFAULT=1, VERBOSE=2
- [ ] Docstring explains each level's purpose
- [ ] Enum is importable from `src.progress`

---

### Subtask T002 – Create ProgressManager class with tqdm integration

**Purpose**: Implement the main progress tracking class that wraps tqdm with verbosity-aware behavior.

**Files**:
- `src/progress/progress_manager.py` (new file)

**Steps**:
1. Create ProgressManager class matching the interface contract:
   ```python
   from typing import Optional
   from tqdm.rich import tqdm as RichTqdm
   from rich.console import Console
   from .cli_output import ProgressLevel  # Will create in T003, import relative

   class ProgressManager:
       """Manages progress display for workflow execution."""

       def __init__(
           self,
           level: ProgressLevel = ProgressLevel.DEFAULT,
           console: Optional[Console] = None
       ):
           self.level = level
           self.console = console or Console()
           self.current_bar: Optional[RichTqdm] = None
           self.step_count = 0
           self.total_steps = 0

       def start_step(self, name: str, total: int = 1, current: Optional[int] = None):
           if self.level == ProgressLevel.QUIET:
               return
           self.step_count = current or (self.step_count + 1)
           self.total_steps = max(self.total_steps, self.step_count)
           description = f"Step {self.step_count}/{self.total_steps}: {name}"
           self.current_bar = RichTqdm(total=total, desc=description, console=self.console)

       def update_progress(self, increment: int = 1):
           if self.current_bar:
               self.current_bar.update(increment)

       def complete_step(self):
           if self.current_bar:
               self.current_bar.close()
               self.current_bar = None

       def set_verbosity(self, level: ProgressLevel):
           self.level = level
           if self.current_bar and level == ProgressLevel.QUIET:
               self.complete_step()

       def close(self):
           if self.current_bar:
               self.current_bar.close()
               self.current_bar = None
   ```
2. Handle edge case: When verbosity changes to QUIET, close existing bar
3. Ensure step counter increments correctly when `current` is None

**Parallel?**: No (depends on T003 for ProgressLevel import)

**Validation**:
- [ ] All methods from interface contract implemented
- [ ] QUIET mode suppresses all tqdm output
- [ ] Step counter auto-increments when current is None
- [ ] Existing bar closed when starting new step

---

### Subtask T003 – Create CLIOutput class for verbosity filtering

**Purpose**: Implement CLIOutput class to filter messages based on verbosity level.

**Files**:
- `src/progress/cli_output.py` (new file)

**Steps**:
1. Create CLIOutput class matching the interface contract:
   ```python
   from rich.console import Console
   from rich.text import Text
   from .progress_manager import ProgressLevel  # Circular import, handle carefully

   class CLIOutput:
       """Manages CLI output based on verbosity level."""

       def __init__(
           self,
           level: ProgressLevel = ProgressLevel.DEFAULT,
           console: Optional[Console] = None
       ):
           self.level = level
           self.console = console or Console()

       def info(self, message: str):
           if self.level != ProgressLevel.QUIET:
               self.console.print(f"[info]{message}[/info]")

       def verbose(self, message: str):
           if self.level == ProgressLevel.VERBOSE:
               self.console.print(f"[dim]{message}[/dim]")

       def error(self, message: str):
           self.console.print(f"[error]ERROR: {message}[/error]")

       def success(self, message: str):
           self.console.print(f"[success]{message}[/success]")

       def set_verbosity(self, level: ProgressLevel):
           self.level = level
   ```
2. Use Rich markup for colored/styled output
3. Implement proper message filtering per verbosity level

**Circular Import**: Both files need each other. Resolve by:
- T002 creates `progress_manager.py` first (without CLIOutput)
- T003 creates `cli_output.py` importing ProgressLevel directly from enum
- Fix imports after both files exist

**Parallel?**: Yes (can be done alongside T002)

**Validation**:
- [ ] info() hidden in QUIET mode
- [ ] verbose() only shows in VERBOSE mode
- [ ] error() and success() always show
- [ ] Rich markup renders colors/styles correctly

---

### Subtask T004 – Write __init__.py for progress module

**Purpose**: Create the module initialization file that exports both ProgressManager and CLIOutput.

**Files**:
- `src/progress/__init__.py` (create if not exists from T001)

**Steps**:
1. Export ProgressLevel enum
2. Export ProgressManager class
3. Export CLIOutput class
4. Add module docstring explaining purpose
5. Handle circular imports between progress_manager and cli_output

**Implementation**:
```python
"""
Progress tracking module for CLI workflows.

Provides verbosity-aware progress display using tqdm and Rich.
"""

from .progress_manager import ProgressManager
from .cli_output import CLIOutput
from .progress_manager import ProgressLevel  # Export enum

__all__ = ["ProgressManager", "CLIOutput", "ProgressLevel"]
```

**Parallel?**: No (must wait for T001, T002, T003)

**Validation**:
- [ ] Module imports successfully (from src.progress import ProgressManager)
- [ ] All three exports are accessible
- [ ] Module docstring is present

---

### Subtask T005 – Add unit tests for ProgressManager

**Purpose**: Ensure ProgressManager behaves correctly across all verbosity levels and state transitions.

**Files**:
- `tests/unit/test_progress_manager.py` (new file)

**Steps**:
1. Create test file with pytest setup
2. Test QUIET mode: No tqdm bars displayed
3. Test DEFAULT mode: Step progress shown with correct formatting
4. Test VERBOSE mode: Detailed progress displayed
5. Test state transitions: start → update → complete → start
6. Test edge cases: Multiple start_step calls without complete
7. Test verbosity switching: set_verbosity() changes behavior

**Test Cases**:
```python
def test_quiet_mode_disables_progress():
    progress = ProgressManager(level=ProgressLevel.QUIET)
    progress.start_step("Test", total=10, current=1)
    assert progress.current_bar is None

def test_default_mode_shows_progress():
    progress = ProgressManager(level=ProgressLevel.DEFAULT)
    progress.start_step("Loading", total=5, current=1)
    assert progress.current_bar is not None
    assert progress.step_count == 1

def test_step_counter_auto_increments():
    progress = ProgressManager(level=ProgressLevel.DEFAULT)
    progress.start_step("Step 1", total=1)  # No current
    assert progress.step_count == 1
    progress.start_step("Step 2", total=1)  # No current
    assert progress.step_count == 2
```

**Parallel?**: Yes (independent test file)

**Validation**:
- [ ] All tests pass with pytest
- [ ] Coverage > 80% for ProgressManager
- [ ] Edge cases tested (verbosity changes, multiple steps)

---

## Test Strategy

**Note**: Tests are explicitly required by the feature specification.

### Unit Tests
- **Location**: `tests/unit/test_progress_manager.py`
- **Purpose**: Verify ProgressManager behavior independent of other components
- **Required Tests**:
  - QUIET mode suppression
  - Step counter auto-increment
  - Progress bar lifecycle
  - Verbosity switching
  - Multiple step handling

### Integration Tests
- **Location**: `tests/integration/test_progress_workflow.py` (create in WP06)
- **Purpose**: Verify progress works within actual workflow
- **Tests**:
  - ProgressManager propagates through workflow state
  - Nodes can access and use progress from state
  - Verbosity flags control output correctly

**Running Tests**:
```bash
# Unit tests only for this WP
pytest tests/unit/test_progress_manager.py -v

# Full integration tests in WP06
pytest tests/integration/test_progress_workflow.py -v
```

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|-------|--------|-----------|
| Circular imports between progress_manager and cli_output | Module import error | Create both files first, then add imports in __init__.py |
| tqdm.rich incompatible with existing rich setup | Progress bars crash | Use tqdm.rich integration which is designed for Rich |
| Progress overhead > 5% of execution time | NFR violated | Profile before finalizing, optimize tqdm refresh rate |
| Windows terminal encoding issues | Unicode display problems | Test on Windows, ensure UTF-8 in tqdm |

---

## Review Guidance

**Key Acceptance Checkpoints for `/spec-kitty.review`**:
- [ ] `src/progress/` module exists with all three files
- [ ] ProgressLevel enum has correct values (0, 1, 2)
- [ ] ProgressManager wraps tqdm correctly with verbosity checks
- [ ] CLIOutput filters messages per verbosity level correctly
- [ ] Unit tests cover all public methods and edge cases
- [ ] Module can be imported: `from src.progress import ProgressManager, CLIOutput, ProgressLevel`
- [ ] No existing code modified (new module only)

**Integration Context**:
- Next WP (WP02) will depend on this module being created
- Ensure module structure matches `src/progress/` from plan.md
- Verify tqdm dependency is added to requirements.txt in WP02

---

## Activity Log

> **CRITICAL**: Activity log entries MUST be in chronological order (oldest first, newest last).

### Valid lanes
`planned`, `doing`, `for_review`, `done`

### How to Add Activity Log Entries

**When adding an entry**:
1. Scroll to the bottom of this file (below "Valid lanes")
2. **APPEND** new entry at the **END** (do NOT prepend or insert in middle)
3. Use exact format: `- YYYY-MM-DDTHH:MM:SSZ – agent_id – lane=<lane> – <action>`

**Format**:
```
- YYYY-MM-DDTHH:MM:SSZ – <agent_id> – lane=<lane> – <brief action description>
```

**Example (correct chronological order)**:
```
- 2026-01-12T10:00:00Z – system – lane=planned – Prompt created
```

---

## Valid lanes

`planned`, `doing`, `for_review`, `done`

---

2025-02-14T00:00:00Z – system – lane=planned – Prompt generated via /spec-kitty.tasks
