# Interface Contract: ProgressManager

**Module**: `src/progress/progress_manager.py`
**Version**: 1.0.0
**Feature**: 005-cli-progress-indicators

---

## Purpose

Manages progress display for workflow execution using tqdm progress bars. Provides a clean interface for tracking workflow steps with different verbosity levels.

---

## Interface Definition

```python
from typing import Optional
from enum import Enum

class ProgressLevel(Enum):
    """Verbosity level for CLI progress display."""
    QUIET = 0
    DEFAULT = 1
    VERBOSE = 2

class ProgressManager:
    """Manages progress display for workflow execution."""

    def __init__(
        self,
        level: ProgressLevel = ProgressLevel.DEFAULT,
        console: Optional[Console] = None
    ) -> None:
        """
        Initialize the progress manager.

        Args:
            level: Verbosity level for output (default: DEFAULT)
            console: Optional rich Console for output (creates new if None)

        Raises:
            ValueError: If level is not a valid ProgressLevel
        """
        pass

    def start_step(
        self,
        name: str,
        total: int = 1,
        current: Optional[int] = None
    ) -> None:
        """
        Begin a new workflow step with progress tracking.

        Args:
            name: Human-readable step description (max 100 chars)
            total: Total iterations for this step (must be >= 1)
            current: Step position if known, auto-increment if None

        Behavior:
            - Increments internal step counter if current is None
            - Creates new tqdm progress bar unless in QUIET mode
            - Closes any existing progress bar before starting new one
            - Formats description as "Step N/M: {name}"

        Raises:
            ValueError: If total < 1 or name is empty
            RuntimeError: If called while another step is running
        """
        pass

    def update_progress(self, increment: int = 1) -> None:
        """
        Update current step progress.

        Args:
            increment: Number of units to increment (must be >= 0)

        Behavior:
            - No-op if in QUIET mode or no step is active
            - Updates tqdm progress bar by increment units
            - Automatically renders progress display

        Raises:
            ValueError: If increment < 0
            RuntimeError: If called without active step
        """
        pass

    def complete_step(self) -> None:
        """
        Mark current step as complete and close its progress bar.

        Behavior:
            - No-op if in QUIET mode or no step is active
            - Closes tqdm progress bar
            - Progress bar displays 100% completion before closing
        """
        pass

    def set_verbosity(self, level: ProgressLevel) -> None:
        """
        Change verbosity level dynamically.

        Args:
            level: New verbosity level

        Behavior:
            - Closes any existing progress bar if switching to QUIET
            - Future start_step() calls will use new level
            - Does not affect currently running step (except closing)

        Raises:
            ValueError: If level is not a valid ProgressLevel
        """
        pass

    def close(self) -> None:
        """
        Clean up progress bars and indicators.

        Behavior:
            - Safe to call multiple times (idempotent)
            - Closes any active progress bar
            - Resets internal state
        """
        pass
```

---

## Usage Example

```python
from src.progress import ProgressManager, ProgressLevel

# Create with default verbosity
progress = ProgressManager()

# Use in workflow
progress.start_step("Loading document", total=1)
# ... do work ...
progress.complete_step()

# Start multi-iteration step
progress.start_step("Processing chunks", total=10)
for i in range(10):
    # ... process chunk ...
    progress.update_progress(1)
progress.complete_step()

# Cleanup
progress.close()
```

---

## Error Handling

| Exception | Condition | Recovery |
|-----------|-----------|----------|
| ValueError | Invalid ProgressLevel | Use valid enum value |
| ValueError | `total < 1` in start_step() | Use positive integer |
| ValueError | `increment < 0` in update_progress() | Use non-negative integer |
| RuntimeError | start_step() called without completing previous | Call complete_step() first |

---

## Thread Safety

**Not thread-safe**. This class is designed for single-threaded async usage within LangGraph workflows. Do not share instances across threads.

---

## Dependencies

- `rich.Console` - For rich console output
- `tqdm.rich.tqdm` - For progress bars
- `typing` - For type hints
- `enum` - For ProgressLevel enum

---

## Testing Requirements

**Unit Tests**:
- Initialize with each ProgressLevel
- start_step() with valid and invalid parameters
- update_progress() increments correctly
- complete_step() closes bar
- set_verbosity() changes behavior
- close() is idempotent
- Error conditions raise appropriate exceptions

**Integration Tests**:
- Progress bar renders correctly in terminal
- QUIET mode suppresses all output
- VERBOSE mode shows detailed progress
