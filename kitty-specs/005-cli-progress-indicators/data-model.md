# Data Model: CLI Progress Indicators

**Feature**: 005-cli-progress-indicators
**Date**: 2025-02-14
**Phase**: 1 - Design & Contracts

---

## Overview

This document defines the data structures for progress tracking in the document debate CLI.

---

## Enum: ProgressLevel

Controls the verbosity of progress display.

```python
from enum import Enum

class ProgressLevel(Enum):
    """Verbosity level for CLI progress display."""
    QUIET = 0      # Minimal output - only errors and final results
    DEFAULT = 1     # Standard step-by-step progress
    VERBOSE = 2     # Detailed sub-step progress and timing
```

**Attributes**:
- `QUIET`: Suppresses all progress indicators, only shows errors and final verdict
- `DEFAULT`: Shows step progress with "Step N/M: description" format
- `VERBOSE`: Shows detailed sub-steps, timing information, and internal operations

**State Machine**:
```
QUIET ←→ DEFAULT ←→ VERBOSE
   (can only transition through explicit flag changes)
```

---

## Class: ProgressEvent

Represents a single progress update event in the workflow.

```python
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class ProgressEvent:
    """A progress event during workflow execution."""

    step_name: str           # Human-readable step description
    current_step: int         # Current step number (1-indexed)
    total_steps: int          # Total number of steps
    sub_step: Optional[str]   # Optional sub-step description (verbose mode)
    timestamp: datetime       # When this event occurred
    status: str               # "running", "complete", "error"
```

**Validation Rules**:
- `current_step` must be >= 1 and <= `total_steps`
- `total_steps` must be >= 1
- `sub_step` is required only in VERBOSE mode
- `status` must be one of: "running", "complete", "error"

**Usage Example**:
```python
event = ProgressEvent(
    step_name="Generating pro arguments",
    current_step=2,
    total_steps=5,
    sub_step="Calling LLM API",
    timestamp=datetime.now(),
    status="running"
)
```

---

## Class: ProgressManager

Manages progress display for workflow execution.

```python
from typing import Optional
from tqdm.rich import tqdm as RichTqdm

class ProgressManager:
    """Manages progress display for workflow execution."""

    def __init__(
        self,
        level: ProgressLevel = ProgressLevel.DEFAULT,
        console: Optional[Console] = None
    ):
        """
        Initialize the progress manager.

        Args:
            level: Verbosity level for output
            console: Optional rich Console for output
        """
        self.level = level
        self.console = console or Console()
        self.current_bar: Optional[RichTqdm] = None
        self.step_count = 0
        self.total_steps = 0

    def start_step(
        self,
        name: str,
        total: int = 1,
        current: Optional[int] = None
    ) -> None:
        """
        Begin a new workflow step with progress tracking.

        Args:
            name: Human-readable step description
            total: Total iterations for this step (default: 1)
            current: Step position if known, auto-increment if None
        """
        self.step_count = current or (self.step_count + 1)
        self.total_steps = max(self.total_steps, self.step_count)

        if self.level == ProgressLevel.QUIET:
            return

        description = f"Step {self.step_count}/{self.total_steps}: {name}"
        self.current_bar = RichTqdm(
            total=total,
            desc=description,
            console=self.console,
            disable=False
        )

    def update_progress(self, increment: int = 1) -> None:
        """
        Update current step progress.

        Args:
            increment: Number of units to increment (default: 1)
        """
        if self.current_bar:
            self.current_bar.update(increment)

    def complete_step(self) -> None:
        """Mark current step as complete and close its progress bar."""
        if self.current_bar:
            self.current_bar.close()
            self.current_bar = None

    def set_verbosity(self, level: ProgressLevel) -> None:
        """
        Change verbosity level dynamically.

        Args:
            level: New verbosity level
        """
        self.level = level
        # Close any existing bar when changing verbosity
        if self.current_bar and level == ProgressLevel.QUIET:
            self.complete_step()

    def close(self) -> None:
        """Clean up progress bars and indicators."""
        if self.current_bar:
            self.current_bar.close()
            self.current_bar = None
```

**State Transitions**:
```
INIT → start_step() → RUNNING → update_progress() → RUNNING → complete_step() → READY
                                                          ↓
                                                      close()
                                                          ↓
                                                         CLOSED
```

---

## Class: CLIOutput

Manages CLI output based on verbosity level.

```python
from rich.console import Console
from rich.text import Text

class CLIOutput:
    """Manages CLI output based on verbosity level."""

    def __init__(
        self,
        level: ProgressLevel = ProgressLevel.DEFAULT,
        console: Optional[Console] = None
    ):
        """
        Initialize CLI output manager.

        Args:
            level: Verbosity level for output
            console: Optional rich Console for output
        """
        self.level = level
        self.console = console or Console()

    def info(self, message: str) -> None:
        """
        Display info message (hidden in quiet mode).

        Args:
            message: Message to display
        """
        if self.level != ProgressLevel.QUIET:
            self.console.print(f"[info]{message}[/info]")

    def verbose(self, message: str) -> None:
        """
        Display verbose message (only in verbose mode).

        Args:
            message: Message to display
        """
        if self.level == ProgressLevel.VERBOSE:
            self.console.print(f"[dim]{message}[/dim]")

    def error(self, message: str) -> None:
        """
        Display error message (always shown).

        Args:
            message: Message to display
        """
        self.console.print(f"[error]ERROR: {message}[/error]")

    def success(self, message: str) -> None:
        """
        Display success message (always shown).

        Args:
            message: Message to display
        """
        self.console.print(f"[success]{message}[/success]")
```

---

## Data Flow

```
CLI Input (--verbose/--quiet)
        ↓
CLIOutput + ProgressManager created
        ↓
Pass to workflow.run()
        ↓
Added to state["_progress_manager"]
        ↓
Nodes access state["_progress_manager"]
        ↓
start_step() → update_progress() → complete_step()
        ↓
User sees progress bars and messages
```

---

## Relationships

```
ProgressLevel (enum)
    └── used by ───────────────┐
                             │
                        ProgressManager
                              │
                              │ manages
                              ↓
                         ProgressEvent
                              │
                    CLIOutput ──┘
                              │
                              └── uses ──→ Console (rich)
```

---

## Storage Requirements

**No persistence required** - All progress data is in-memory only for display purposes.

**Lifetime**: ProgressManager exists only during workflow execution, then is garbage collected.

---

## Testing Considerations

**Unit Tests Should Cover**:
- ProgressLevel enum values
- ProgressEvent validation (invalid ranges)
- ProgressManager state transitions
- CLIOutput verbosity filtering

**Integration Tests Should Cover**:
- ProgressManager within actual LangGraph workflow
- Verbosity flag propagation through CLI
- Progress display rendering in terminal
