# Interface Contract: CLIOutput

**Module**: `src/progress/cli_output.py`
**Version**: 1.0.0
**Feature**: 005-cli-progress-indicators

---

## Purpose

Manages CLI output based on verbosity level. Provides a filtered logging interface that respects user's verbosity preference.

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

class CLIOutput:
    """Manages CLI output based on verbosity level."""

    def __init__(
        self,
        level: ProgressLevel = ProgressLevel.DEFAULT,
        console: Optional[Console] = None
    ) -> None:
        """
        Initialize CLI output manager.

        Args:
            level: Verbosity level for output (default: DEFAULT)
            console: Optional rich Console for output (creates new if None)

        Raises:
            ValueError: If level is not a valid ProgressLevel
        """
        pass

    def info(self, message: str) -> None:
        """
        Display info message (hidden in quiet mode).

        Args:
            message: Message to display (any string)

        Behavior:
            - QUIET mode: Message is suppressed (not displayed)
            - DEFAULT mode: Message is displayed with [info] style
            - VERBOSE mode: Message is displayed with [info] style

        The message is always processed (side effects occur), just not
        displayed in QUIET mode. This allows for hooks/tracing if needed.

        Raises:
            ValueError: If message is None
        """
        pass

    def verbose(self, message: str) -> None:
        """
        Display verbose message (only in verbose mode).

        Args:
            message: Message to display (any string)

        Behavior:
            - QUIET mode: Message is suppressed
            - DEFAULT mode: Message is suppressed
            - VERBOSE mode: Message is displayed with [dim] style

        Use this for detailed debugging information, timing data, or
        internal operation details that typical users don't need to see.

        Raises:
            ValueError: If message is None
        """
        pass

    def error(self, message: str) -> None:
        """
        Display error message (always shown).

        Args:
            message: Message to display (any string)

        Behavior:
            - Message is ALWAYS displayed regardless of verbosity level
            - Displayed with [error] style (typically red)
            - Written to stderr if using standard logging patterns

        Use this for critical errors, exceptions, and failure conditions
        that the user must be aware of.

        Raises:
            ValueError: If message is None
        """
        pass

    def success(self, message: str) -> None:
        """
        Display success message (always shown).

        Args:
            message: Message to display (any string)

        Behavior:
            - Message is ALWAYS displayed regardless of verbosity level
            - Displayed with [success] style (typically green)
            - Used for completion confirmations, successful results

        Raises:
            ValueError: If message is None
        """
        pass

    def set_verbosity(self, level: ProgressLevel) -> None:
        """
        Change verbosity level dynamically.

        Args:
            level: New verbosity level

        Behavior:
            - Future method calls will use new level
            - Does not affect currently displayed messages

        Raises:
            ValueError: If level is not a valid ProgressLevel
        """
        pass
```

---

## Output Matrix

| Method | QUIET Mode | DEFAULT Mode | VERBOSE Mode |
|--------|-------------|--------------|--------------|
| `info()` | Hidden | Shown | Shown |
| `verbose()` | Hidden | Hidden | Shown |
| `error()` | Shown | Shown | Shown |
| `success()` | Shown | Shown | Shown |

---

## Usage Example

```python
from src.progress import CLIOutput, ProgressLevel

# Create with verbosity from CLI args
output = CLIOutput(level=ProgressLevel.VERBOSE)

# Use throughout workflow
output.info("Starting workflow...")
output.verbose("Loading document from /path/to/file.docx")
output.verbose("Document size: 12345 chars")

if error:
    output.error("Failed to load document")

output.success("Workflow completed successfully")
```

---

## Error Handling

| Exception | Condition | Recovery |
|-----------|-----------|----------|
| ValueError | Invalid ProgressLevel | Use valid enum value |
| ValueError | Message is None | Pass string message |
| RuntimeError | Console I/O error | Handle in calling code |

---

## Thread Safety

**Not thread-safe**. This class is designed for single-threaded async usage within LangGraph workflows. Do not share instances across threads.

---

## Dependencies

- `rich.Console` - For rich console output
- `typing` - For type hints
- `enum` - For ProgressLevel enum

---

## Integration with ProgressManager

`CLIOutput` and `ProgressManager` are designed to work together:

```python
from src.progress import ProgressManager, CLIOutput, ProgressLevel

level = ProgressLevel.VERBOSE
progress = ProgressManager(level=level)
output = CLIOutput(level=level)

output.info("Starting workflow...")
progress.start_step("Loading document", total=1)
output.verbose("Reading document.docx...")
# ... do work ...
progress.complete_step()
output.success("Document loaded")
```

---

## Testing Requirements

**Unit Tests**:
- Initialize with each ProgressLevel
- info() respects verbosity levels
- verbose() only shows in VERBOSE mode
- error() always shows
- success() always shows
- set_verbosity() changes future output behavior

**Integration Tests**:
- Output renders correctly in terminal
- Rich markup (colors, styles) displays properly
- Works alongside ProgressManager without interference
