---
work_package_id: WP01
title: Progress Manager Module
lane: planned
dependencies: []
subtasks:
- T001
- T002
- T003
- T004
- T005
- T006
- T007
phase: Phase 1 - Foundation
assignee: ''
agent: ''
shell_pid: ''
review_status: ''
reviewed_by: ''
history:
- timestamp: '2025-02-14T12:30:00Z'
  lane: planned
  agent: system
  shell_pid: ''
  action: Prompt generated via /spec-kitty.plan
---

# Work Package Prompt: WP01 – Progress Manager Module

## ⚠️ IMPORTANT: Review Feedback Status

**Read this first if you are implementing this task!**

- **Has review feedback?**: Check `review_status` field above. If it says `has_feedback`, scroll to **Review Feedback** section immediately (right below this notice).
- **You must address all feedback** before your work is complete. Feedback items are your implementation TODO list.
- **Mark as acknowledged**: When you understand the feedback and begin addressing it, update `review_status: acknowledged` in frontmatter via `Edit`.
- **Report progress**: As you address each feedback item, update Activity Log explaining what you changed.

---

## Review Feedback

> **Populated by `/spec-kitty.review`** – Reviewers add detailed feedback here when work needs changes. Implementation must address every item listed below before returning for re-review.

*[This section is empty initially. Reviewers will populate it if work is returned from review. If you see feedback here, treat each item as a must-do before completion.]*

---

## Objectives & Success Criteria

**Primary Objective**: Create the `src/progress/` module with `ProgressManager` and `CLIOutput` classes to manage progress tracking and display for the document debate workflow.

**Success Criteria**:
- [ ] `src/progress/__init__.py` exists with proper exports
- [ ] `ProgressLevel` enum defined with QUIET, DEFAULT, VERBOSE values
- [ ] `ProgressEvent` dataclass created with all required fields
- [ ] `ProgressManager` class implements start_step(), update_progress(), complete_step(), set_verbosity(), close()
- [ ] `CLIOutput` class implements info(), verbose(), error(), success() methods
- [ ] tqdm integrated with Rich-compatible mode (tqdm.rich)
- [ ] Interface contracts written in contracts/progress_manager_interface.md and contracts/cli_output_interface.md
- [ ] All classes importable: `from src.progress import ProgressManager, CLIOutput`
- [ ] Code follows data model from ../data-model.md

---

## Context & Constraints

**Prerequisites**:
- None (first work package)

**Related Documents**:
- [Data Model](../data-model.md) - ProgressLevel, ProgressEvent, ProgressManager, CLIOutput definitions
- [Research](../research.md) - Technology decisions (tqdm with Rich, verbosity levels)
- [Spec](../spec.md) - FR-001 through FR-005 (progress display requirements)

**Key Constraints**:
- Must use `tqdm` library with Rich compatibility (tqdm.rich)
- Progress display must NOT block or slow workflow execution (<5% overhead)
- Support three verbosity levels: QUIET (minimal), DEFAULT (step progress), VERBOSE (detailed)
- ProgressManager must be usable in async context (non-blocking operations)
- CLIOutput must filter messages based on current verbosity level
- tqdm must work alongside existing Rich console output without conflicts

**Architecture Decisions**:
- Separate `ProgressManager` (state management, tqdm integration) from `CLIOutput` (display filtering)
- `ProgressManager` owns tqdm lifecycle (creates bars, updates them, closes them)
- `CLIOutput` wraps console output with verbosity-aware methods
- Use dataclass for ProgressEvent (immutable value object)
- Use underscore prefix for progress_manager in state to avoid collisions

---

## Subtasks & Detailed Guidance

### Subtask T001 – Create Progress Module Structure

**Purpose**: Establish the directory and module exports for progress tracking.

**Steps**:
1. Create directory `src/progress/` at repository root
2. Create `src/progress/__init__.py` with module docstring
3. Add imports for public classes (will create in later subtasks)
4. Export public API: `ProgressManager`, `CLIOutput`, `ProgressLevel`, `ProgressEvent`

**Files**:
- `src/progress/__init__.py` (new file, ~15 lines)

**Implementation**:
```python
"""
Progress tracking module for document debate CLI.

Provides progress bars, step indicators, and verbosity-aware output
for long-running workflow operations.
"""

# Imports will be added in later subtasks
from src.progress.progress_manager import ProgressManager
from src.progress.cli_output import CLIOutput
from src.progress.progress_level import ProgressLevel
from src.progress.progress_event import ProgressEvent

__all__ = ["ProgressManager", "CLIOutput", "ProgressLevel", "ProgressEvent"]
```

**Validation**:
- [ ] `src/progress/` directory exists
- [ ] `from src.progress import ProgressManager, CLIOutput` works without errors
- [ ] Module has descriptive docstring
- [ ] All classes listed in __all__ (even if not implemented yet)

**Notes**:
- Keep __init__.py minimal - just docstring and exports
- Imports will reference classes created in T002-T007
- Use __all__ to explicitly define public API

---

### Subtask T002 – Implement ProgressLevel Enum

**Purpose**: Define the three verbosity levels for progress display.

**Steps**:
1. Create `src/progress/progress_level.py`
2. Import Enum from enum module
3. Define `ProgressLevel` class inheriting from Enum
4. Add three values: QUIET = 0, DEFAULT = 1, VERBOSE = 2
5. Add docstring explaining each level
6. Consider comparison operators if needed (usually enums support this)

**Files**:
- `src/progress/progress_level.py` (new file, ~25 lines)

**Implementation**:
```python
from enum import Enum

class ProgressLevel(Enum):
    """
    Verbosity level for CLI progress display.

    Levels control how much information is displayed during workflow execution:
    - QUIET: Suppress all non-critical output. No progress bars.
    - DEFAULT: Show step-by-step progress with position indicators.
    - VERBOSE: Show detailed sub-step progress, timing, and internal operations.

    Priority ordering: QUIET > DEFAULT > VERBOSE
    (If both --quiet and --verbose are provided, quiet takes precedence.)
    """
    QUIET = 0      # Suppress all progress indicators
    DEFAULT = 1     # Standard step-by-step progress
    VERBOSE = 2      # Detailed sub-step progress and diagnostics
```

**Validation**:
- [ ] ProgressLevel.QUIET == 0
- [ ] ProgressLevel.DEFAULT == 1
- [ ] ProgressLevel.VERBOSE == 2
- [ ] Has comprehensive docstring
- [ ] Enum values are ordered (0, 1, 2)

**Notes**:
- Integer values enable easy comparison (higher = more verbose)
- Priority ordering documented for CLI flag logic
- Can be used in if statements: `if level == ProgressLevel.QUIET:`

**Risks**:
- Ensure integers don't conflict with future additions
- Document the priority ordering clearly

---

### Subtask T003 – Implement ProgressEvent Dataclass

**Purpose**: Create immutable data structure for progress event data.

**Steps**:
1. Create `src/progress/progress_event.py`
2. Import dataclass from dataclasses module
3. Define `ProgressEvent` class with @dataclass decorator
4. Add fields: step_name (str), current_step (int), total_steps (int), sub_step (Optional[str]), timestamp (datetime)
5. Add validation in __post_init__ if needed
6. Add comprehensive docstring

**Files**:
- `src/progress/progress_event.py` (new file, ~30 lines)

**Implementation**:
```python
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass(frozen=True)
class ProgressEvent:
    """
    A progress update event during workflow execution.

    This is a value object (immutable) representing a single state
    transition or progress update. It does not contain behavior.

    Attributes:
        step_name: Human-readable name of current step (e.g., "Generating PRO arguments")
        current_step: Position in sequence (1-indexed)
        total_steps: Total number of steps in this phase
        sub_step: Optional detailed description for verbose mode
        timestamp: When this event occurred (for diagnostics/verbose mode)
    """
    step_name: str
    current_step: int
    total_steps: int
    sub_step: Optional[str]  # Only used in VERBOSE mode
    timestamp: datetime
```

**Validation**:
- [ ] ProgressEvent can be instantiated: `ProgressEvent("Step 1", 1, 5, None, datetime.now())`
- [ ] All fields present and typed correctly
- [ ] frozen=True makes instances immutable
- [ ] Docstring explains each field clearly

**Notes**:
- frozen=True prevents accidental modification after creation
- Optional[sub_step] means it can be None (not required)
- Use datetime.now() at creation time for accurate timing
- Used internally by ProgressManager, not exposed in public API

---

### Subtask T004 – Implement ProgressManager Class

**Purpose**: Create the main state machine for managing progress bars and events.

**Steps**:
1. Create `src/progress/progress_manager.py`
2. Import tqdm.rich (from tqdm.rich import tqdm as rich_tqdm)
3. Import ProgressLevel, ProgressEvent, typing modules
4. Define `ProgressManager` class with __init__(level, console)
5. Implement start_step() method: create/update tqdm bar
6. Implement update_progress() method: increment current position
7. Implement complete_step() method: close current bar
8. Implement set_verbosity() method: change level dynamically
9. Implement close() method: cleanup all resources
10. Store current_bar instance variable

**Files**:
- `src/progress/progress_manager.py` (new file, ~120 lines)

**Implementation**:
```python
from typing import Optional, TYPE_CHECKING
from tqdm.rich import tqdm as rich_tqdm
from rich.console import Console

if TYPE_CHECKING:
    from src.progress.progress_level import ProgressLevel
    from src.progress.progress_event import ProgressEvent

class ProgressManager:
    """
    Manages progress display for workflow execution.

    Tracks workflow steps using tqdm progress bars with Rich-compatible
    output. Filters display based on verbosity level. Non-blocking and
    suitable for async contexts.

    Lifecycle: INIT → start_step() → update_progress() → complete_step() → CLOSED
    """

    def __init__(
        self,
        level: ProgressLevel = ProgressLevel.DEFAULT,
        console: Optional[Console] = None
    ):
        """
        Initialize progress manager with verbosity level.

        Args:
            level: Initial verbosity level (controls what is displayed)
            console: Optional Rich Console for output (creates own if None)
        """
        self.level = level
        self.console = console or Console()
        self.current_bar: Optional[rich_tqdm] = None
        self.step_count = 0

    def start_step(
        self,
        name: str,
        total: int = 1,
        current: int = 1,
        sub_step: Optional[str] = None
    ) -> None:
        """
        Begin a new workflow step with progress tracking.

        Creates a new tqdm progress bar (or replaces current one).
        Displays step name and position.

        Args:
            name: Human-readable step name
            total: Total iterations for this step (default: 1)
            current: Starting position (default: 1)
            sub_step: Optional detailed description (VERBOSE mode only)
        """
        # Don't display if QUIET
        if self.level == ProgressLevel.QUIET:
            return

        self.step_count += 1
        description = f"Step {self.step_count}: {name}"

        # Add sub-step in verbose mode
        if self.level == ProgressLevel.VERBOSE and sub_step:
            description += f" ({sub_step})"

        # Close existing bar if any
        if self.current_bar:
            self.current_bar.close()

        # Create new bar
        self.current_bar = rich_tqdm(
            total=total,
            initial=current,
            desc=description,
            console=self.console,
            disable=False
        )

    def update_progress(self, increment: int = 1) -> None:
        """
        Update current step progress.

        Args:
            increment: Units to add to current position (default: 1)
        """
        if self.level == ProgressLevel.QUIET or not self.current_bar:
            return

        self.current_bar.update(increment)

    def complete_step(self) -> None:
        """
        Mark current step as complete and close progress bar.

        Should be called when step finishes. Displays completion and
        prepares for next step.
        """
        if self.level == ProgressLevel.QUIET or not self.current_bar:
            return

        # Update to 100% before closing
        if not self.current_bar.n:  # n is total completed
            self.current_bar.update(self.current_bar.n - self.current_bar.n)

        self.current_bar.close()
        self.current_bar = None

    def set_verbosity(self, level: ProgressLevel) -> None:
        """
        Dynamically change verbosity level.

        Args:
            level: New verbosity level to use
        """
        old_level = self.level
        self.level = level

        # If transitioning from QUIET, notify
        if old_level == ProgressLevel.QUIET and level != ProgressLevel.QUIET:
            pass  # Could add log message

        # If transitioning to QUIET, close existing bar
        if level == ProgressLevel.QUIET and self.current_bar:
            self.complete_step()

    def close(self) -> None:
        """
        Clean up all progress resources.

        Call this before program exit to ensure clean terminal state.
        """
        if self.current_bar:
            self.current_bar.close()
            self.current_bar = None

        self.step_count = 0
```

**Validation**:
- [ ] __init__ accepts level and optional console
- [ ] start_step() creates/updates tqdm bar with correct description
- [ ] update_progress() increments bar position
- [ ] complete_step() closes bar and sets to None
- [ ] set_verbosity() changes level and handles QUIET transition
- [ ] close() cleans up all resources
- [ ] All methods return None (non-void return values)

**Notes**:
- tqdm.rich (imported as rich_tqdm) is Rich-compatible tqdm
- Disable checking on level prevents unnecessary bar creation
- Description format matches spec: "Step N: Name" or "Step N: Name (detail)"
- Sub-step only shown in VERBOSE mode
- Step count increments for each start_step() call

**Risks**:
- tqdm.rich might not be installed - add to requirements in WP04
- Rich console object sharing between modules could cause issues
- Bars might overlap if not closed properly

---

### Subtask T005 – Implement CLIOutput Class

**Purpose**: Create verbosity-aware console output wrapper for progress messages.

**Steps**:
1. Create `src/progress/cli_output.py`
2. Import ProgressLevel from progress_level module
3. Import Console and Text from rich for terminal output
4. Define `CLIOutput` class with __init__(level, console)
5. Implement info() method: displays message unless QUIET
6. Implement verbose() method: displays message only if VERBOSE
7. Implement error() method: always displays (critical messages)
8. Implement success() method: always displays (final results)
9. Use [info] vs [dim] tags for Rich console formatting

**Files**:
- `src/progress/cli_output.py` (new file, ~80 lines)

**Implementation**:
```python
from typing import TYPE_CHECKING
from rich.console import Console
from rich.text import Text

if TYPE_CHECKING:
    from src.progress.progress_level import ProgressLevel

class CLIOutput:
    """
    Manages CLI output based on verbosity level.

    Filters progress and informational messages based on current verbosity setting.
    Error and success messages are always displayed regardless of verbosity.

    Usage:
        output = CLIOutput(level=ProgressLevel.DEFAULT)
        output.info("Processing document...")
        output.verbose("Calling LLM API with timeout...")
        output.error("Failed to process document")
        output.success("Debate complete!")
    """

    def __init__(
        self,
        level: ProgressLevel = ProgressLevel.DEFAULT,
        console: Optional[Console] = None
    ):
        """
        Initialize CLI output with verbosity level.

        Args:
            level: Current verbosity level for filtering
            console: Optional Rich Console for output
        """
        self.level = level
        self.console = console or Console()

    def info(self, message: str) -> None:
        """
        Display informational message (hidden in QUIET mode).

        Args:
            message: Message to display
        """
        if self.level == ProgressLevel.QUIET:
            return

        self.console.print(f"[info]{message}[/info]")

    def verbose(self, message: str) -> None:
        """
        Display verbose message (only shown in VERBOSE mode).

        Args:
            message: Detailed diagnostic message
        """
        if self.level != ProgressLevel.VERBOSE:
            return

        self.console.print(f"[dim]{message}[/dim]")

    def error(self, message: str) -> None:
        """
        Display error message (always shown regardless of verbosity).

        Args:
            message: Error message to display
        """
        self.console.print(f"[error]ERROR: {message}[/error]")

    def success(self, message: str) -> None:
        """
        Display success message (always shown regardless of verbosity).

        Args:
            message: Success message to display
        """
        self.console.print(f"[success]{message}[/success]")
```

**Validation**:
- [ ] __init__ stores level and optional console
- [ ] info() displays message in DEFAULT mode, hidden in QUIET
- [ ] verbose() only displays in VERBOSE mode
- [ ] error() always displays (level ignored)
- [ ] success() always displays (level ignored)
- [ ] Rich tags used: [info], [dim], [error], [success]
- [ ] Methods return None (consistently void return)

**Notes**:
- Error and success bypass level checking (always visible)
- [dim] tag makes verbose text subtle/differentiated
- Color coding helps users scan output quickly
- Matches existing Rich logging patterns in codebase

---

### Subtask T006 – Add tqdm Integration to ProgressManager

**Purpose**: Integrate tqdm.rich for actual progress bar display.

**Steps**:
1. Verify tqdm is imported in progress_manager.py: `from tqdm.rich import tqdm as rich_tqdm`
2. Ensure tqdm.rich usage in start_step() method
3. Test bar creation: `rich_tqdm(total=5, desc="Step 1: Test", console=self.console)`
4. Verify update() and close() calls on bar object
5. Ensure disable parameter is set correctly (only in QUIET mode)

**Files**:
- `src/progress/progress_manager.py` (modify, ensure imports are correct)

**Implementation**:
```python
# At top of progress_manager.py:
from tqdm.rich import tqdm as rich_tqdm
from rich.console import Console

# Verify start_step() uses rich_tqdm:
def start_step(self, ...):
    # ... existing code ...
    self.current_bar = rich_tqdm(
        total=total,
        initial=current,
        desc=description,
        console=self.console,
        disable=False  # Will be controlled by level check
    )
```

**Validation**:
- [ ] `from tqdm.rich import tqdm as rich_tqdm` at top of file
- [ ] rich_tqdm() called in start_step()
- [ ] bar.update() called in update_progress()
- [ ] bar.close() called in complete_step() and close()
- [ ] disable parameter available (though we check level before creating)

**Notes**:
- tqdm.rich is specifically designed to work with Rich console
- Import as `rich_tqdm` to avoid name conflict with other tqdm imports
- tqdm must be added to requirements.txt (in WP04)

**Risks**:
- tqdm.rich version compatibility - ensure it exists (typically >=7.0.0)
- Rich console must be shared or compatible instance
- tqdm might buffer updates - but this is acceptable for progress

---

### Subtask T007 – Write Interface Contracts

**Purpose**: Document public interfaces for ProgressManager and CLIOutput in contract files.

**Steps**:
1. Create `contracts/progress_manager_interface.md`
2. Document ProgressManager interface with all methods
3. Document method signatures, parameters, return types
4. Add usage examples
5. Create `contracts/cli_output_interface.md`
6. Document CLIOutput interface with all methods
7. Document filtering behavior and verbosity handling

**Files**:
- `contracts/progress_manager_interface.md` (new file, ~60 lines)
- `contracts/cli_output_interface.md` (new file, ~40 lines)

**Implementation**:

**contracts/progress_manager_interface.md**:
```markdown
# Progress Manager Interface

## Overview

ProgressManager provides progress tracking and display for long-running workflow operations.

## Interface

```python
class ProgressManager:
    def __init__(self, level: ProgressLevel, console: Optional[Console] = None) -> None:
        """Initialize with verbosity level."""

    def start_step(self, name: str, total: int = 1, current: int = 1, sub_step: Optional[str] = None) -> None:
        """Begin a workflow step with progress bar."""

    def update_progress(self, increment: int = 1) -> None:
        """Update current step progress."""

    def complete_step(self) -> None:
        """Mark current step as complete."""

    def set_verbosity(self, level: ProgressLevel) -> None:
        """Change verbosity level dynamically."""

    def close(self) -> None:
        """Clean up all progress resources."""
```

## Usage Example

```python
from src.progress import ProgressManager, ProgressLevel

# Create with default verbosity
manager = ProgressManager(level=ProgressLevel.DEFAULT)

# Start a step
manager.start_step("Generating PRO arguments", total=5)

# Update progress
manager.update_progress(increment=1)

# Complete step
manager.complete_step()

# Clean up
manager.close()
```

## Verbosity Behavior

- **QUIET**: No progress bars displayed, all methods become no-ops
- **DEFAULT**: Step progress bars with "Step N: Name" format
- **VERBOSE**: Step progress + sub-step details in bar description
```

**contracts/cli_output_interface.md**:
```markdown
# CLI Output Interface

## Overview

CLIOutput provides verbosity-aware console output for progress messages and diagnostics.

## Interface

```python
class CLIOutput:
    def __init__(self, level: ProgressLevel, console: Optional[Console] = None) -> None:
        """Initialize with verbosity level."""

    def info(self, message: str) -> None:
        """Display info message (hidden in QUIET mode)."""

    def verbose(self, message: str) -> None:
        """Display verbose message (VERBOSE mode only)."""

    def error(self, message: str) -> None:
        """Display error message (always shown)."""

    def success(self, message: str) -> None:
        """Display success message (always shown)."""
```

## Verbosity Filtering

| Method | QUIET | DEFAULT | VERBOSE |
|---------|--------|---------|----------|
| info() | Hidden | Shown | Hidden |
| verbose() | Hidden | Hidden | Shown |
| error() | Shown | Shown | Shown |
| success() | Shown | Shown | Shown |

## Usage Example

```python
from src.progress import CLIOutput, ProgressLevel

# Create with default level
output = CLIOutput(level=ProgressLevel.DEFAULT)

# Show info (visible in default mode)
output.info("Processing document...")

# Show diagnostics (only in verbose mode)
output.verbose("Calling LLM API with timeout=30s")

# Show error (always visible)
output.error("Failed to read document")

# Show result (always visible)
output.success("Debate complete: PRO wins")
```
```

**Validation**:
- [ ] Both contract files created
- [ ] All methods documented with signatures
- [ ] Usage examples provided
- [ ] Verbosity behavior documented
- [ ] Files are in valid Markdown format

**Notes**:
- Contracts serve as documentation for future developers
- Include examples for each major method
- Document non-obvious behavior (like verbosity filtering)
- These are NOT code - just documentation

---

## Test Strategy

**Manual Verification** (before WP05 tests are written):

1. **Import Test**:
```python
from src.progress import ProgressManager, CLIOutput, ProgressLevel, ProgressEvent

# Should work without errors
manager = ProgressManager(level=ProgressLevel.DEFAULT)
output = CLIOutput(level=ProgressLevel.DEFAULT)
```

2. **Functionality Test**:
```python
# Test start_step() creates bar
manager.start_step("Test Step", total=5, current=1)
assert manager.current_bar is not None

# Test update_progress() increments
manager.update_progress(1)
# Position should be 2/5

# Test complete_step() closes bar
manager.complete_step()
assert manager.current_bar is None
```

3. **Verbosity Test**:
```python
quiet_manager = ProgressManager(level=ProgressLevel.QUIET)
verbose_manager = ProgressManager(level=ProgressLevel.VERBOSE)

# QUIET: start_step() should be no-op
quiet_manager.start_step("Test", total=5)
# current_bar should be None

# VERBOSE: start_step() should include sub-step
verbose_manager.start_step("Test", total=5, sub_step="detail")
# Bar description should include "(detail)"
```

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|-------|---------|------------|
| **tqdm not installed** | ImportError when importing tqdm.rich | Will add to requirements.txt in WP04. Document in README. |
| **Rich console conflict** | tqdm and Rich both writing to terminal | Use tqdm.rich specifically designed for Rich compatibility |
| **Bar lifecycle bugs** | Bars not closed properly, terminal clutter | Ensure close() called in finally block, implement cleanup in set_verbosity() |
| **Verbosity state sync** | CLIOutput and ProgressManager level mismatch | Ensure same level object/instance shared between both |
| **Non-blocking violations** | Progress updates slow workflow | Keep tqdm operations lightweight, avoid expensive operations in update path |
| **Import order issues** | Circular imports between progress modules | Import ProgressLevel, ProgressEvent first (no dependencies), then classes |

**Monitoring Considerations**:
- Log verbosity level changes
- Track number of active progress bars (should be 0 or 1 at any time)
- Monitor tqdm update frequency (should not spam terminal)

---

## Review Guidance

**Acceptance Checkpoints for Reviewers**:

1. **Module Structure**:
   - [ ] `src/progress/` directory exists with __init__.py
   - [ ] All classes importable from `src.progress`
   - [ ] No circular imports

2. **ProgressLevel**:
   - [ ] Enum defined with QUIET=0, DEFAULT=1, VERBOSE=2
   - [ ] Has docstring explaining each level
   - [ ] Values are integers for comparison

3. **ProgressEvent**:
   - [ ] Dataclass with all required fields
   - [ ] frozen=True for immutability
   - [ ] Has comprehensive docstring

4. **ProgressManager**:
   - [ ] __init__ accepts level and optional console
   - [ ] start_step() creates/updates tqdm bar correctly
   - [ ] update_progress() increments position
   - [ ] complete_step() closes bar
   - [ ] set_verbosity() handles QUIET transition
   - [ ] close() cleans up resources
   - [ ] Uses tqdm.rich (rich_tqdm import)
   - [ ] Level checked before operations (QUIET skips)

5. **CLIOutput**:
   - [ ] __init__ accepts level and optional console
   - [ ] info() filters correctly (QUIET: no, DEFAULT: yes, VERBOSE: no)
   - [ ] verbose() only shows in VERBOSE mode
   - [ ] error() and success() always show
   - [ ] Rich tags used ([info], [dim], [error], [success])

6. **Contracts**:
   - [ ] progress_manager_interface.md exists with full interface
   - [ ] cli_output_interface.md exists with full interface
   - [ ] Usage examples provided
   - [ ] Verbosity behavior documented

7. **Integration**:
   - [ ] Classes work together (manual test passes)
   - [ ] tqdm.rich used correctly
   - [ ] No syntax or import errors

**Failure Criteria** (return for rework if any true):
- ❌ Imports fail due to missing tqdm or circular dependencies
- ❌ ProgressLevel enum values wrong (not 0, 1, 2)
- ❌ ProgressManager methods block or significantly slow workflow
- ❌ CLIOutput filtering logic incorrect
- ❌ tqdm bar not closed properly (terminal clutter on exit)
- ❌ Rich console and tqdm conflict/glitch
- ❌ Contract files missing or incomplete

---

## Activity Log

### Valid Lanes
- `planned`
- `doing`
- `for_review`
- `done`

### How to Add Activity Log Entries

**When adding an entry**:
1. Scroll to bottom of this file (Activity Log section below "Valid lanes")
2. **APPEND** new entry at END (do NOT prepend or insert in middle)
3. Use exact format: `- YYYY-MM-DDTHH:MM:SSZ – agent_id – lane=<lane> – <action>`
4. Timestamp MUST be current time in UTC (check with `date -u "+%Y-%m-%dT%H:%M:%SZ"`)
5. Lane MUST match frontmatter `lane:` field exactly
6. Agent ID should identify who made the change (claude-sonnet-4-6, codex, etc.)

**Format**:
```
- YYYY-MM-DDTHH:MM:SSZ – <agent_id> – lane=<lane> – <brief action description>
```

**Example (correct chronological order)**:
```
- 2026-01-12T10:00:00Z – system – lane=planned – Prompt created
- 2026-01-12T10:30:00Z – claude – lane=doing – Started implementation
- 2026-01-12T11:00:00Z – codex – lane=for_review – Implementation complete, ready for review
- 2026-01-12T11:30:00Z – claude – lane=done – Review passed, all tests passing  ← LATEST (at bottom)
```

**Common mistakes (DO NOT DO THIS)**:
- ❌ Adding new entry at top (breaks chronological order)
- ❌ Using future timestamps (causes acceptance validation to fail)
- ❌ Lane mismatch: frontmatter says `lane: "done"` but log entry says `lane=doing`
- ❌ Inserting in middle instead of appending to end

**Why this matters**: The acceptance system reads LAST activity log entry as current state. If entries are out of order, acceptance will fail even when work is complete.

**Initial entry**:
- 2025-02-14T12:30:00Z – system – lane=planned – Prompt generated.
