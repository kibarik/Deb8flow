---
work_package_id: "WP01"
subtasks:
  - "T001"
  - "T002"
  - "T003"
  - "T004"
  - "T005"
  - "T006"
  - "T007"
  - "T008"
title: "Output Module Foundation"
phase: "Phase 1 - Foundation"
lane: "planned"
assignee: ""
agent: ""
shell_pid: ""
review_status: ""
reviewed_by: ""
history:
  - timestamp: "2025-02-14T12:00:00Z"
    lane: "planned"
    agent: "system"
    shell_pid: ""
    action: "Prompt generated via /spec-kitty.tasks"
---

# Work Package Prompt: WP01 – Output Module Foundation

## ⚠️ IMPORTANT: Review Feedback Status

**Read this first if you are implementing this task!**

- **Has review feedback?**: Check `review_status` field above. If it says `has_feedback`, scroll to **Review Feedback** section immediately (right below this notice).
- **You must address all feedback** before your work is complete. Feedback items are your implementation TODO list.
- **Mark as acknowledged**: When you understand the feedback and begin addressing it, update `review_status: acknowledged` in frontmatter.
- **Report progress**: As you address each feedback item, update Activity Log explaining what you changed.

---

## Review Feedback

> **Populated by `/spec-kitty.review`** – Reviewers add detailed feedback here when work needs changes. Implementation must address every item listed below before returning for re-review.

*[This section is empty initially. Reviewers will populate it if work is returned from review. If you see feedback here, treat each item as a must-do before completion.]*

---

## Objectives & Success Criteria

**Primary Objective**: Create the `src/output/` module with all required classes (AsyncFileWriter, TranscriptFormatter, DebateMessage) that enables non-blocking, fault-tolerant file writing.

**Success Criteria**:
- [ ] `src/output/` directory exists with `__init__.py`, `async_file_writer.py`, `transcript_formatter.py`
- [ ] All classes import without errors (`from src.output import AsyncFileWriter, TranscriptFormatter, DebateMessage`)
- [ ] `DebateMessage` dataclass has all required fields (speaker, timestamp, content)
- [ ] `TranscriptFormatter.format_message()` produces correct format: `[SPEAKER] ISO_TIMESTAMP\ncontent\n\n`
- [ ] `TranscriptFormatter.validate_path()` returns bool and handles errors gracefully
- [ ] `AsyncFileWriter` initializes with asyncio.Queue, starts background task
- [ ] `AsyncFileWriter.write_message()` is non-blocking (queues and returns immediately)
- [ ] `AsyncFileWriter.close()` drains queue and stops background task
- [ ] Code handles all specified error scenarios (unwritable path, I/O failures)

---

## Context & Constraints

**Prerequisites**:
- None (first work package)

**Related Documents**:
- [Data Model](../data-model.md) - Entity definitions for DebateMessage, AsyncFileWriter, TranscriptFormatter
- [Research](../research.md) - Technical decisions: aiofiles usage, error handling, message format
- [Spec](../spec.md) - Functional requirements FR-001 through FR-011

**Key Constraints**:
- Must use `aiofiles` library for async file I/O (will be added to requirements.txt in WP02)
- Write failures MUST NOT crash or raise exceptions (log and continue only)
- Queue max size must be 1000 to prevent unbounded memory growth
- Message format must be exactly: `[SPEAKER] ISO8601_TIMESTAMP\n<message content>\n\n`
- All async operations must properly handle cancellation and cleanup

**Architecture Decisions**:
- Separate `TranscriptFormatter` class for formatting logic (testable in isolation)
- `AsyncFileWriter` owns background task lifecycle (creates in `__init__`, stops in `close`)
- `DebateMessage` is a simple dataclass (value object, no behavior)

---

## Subtasks & Detailed Guidance

### Subtask T001 – Create src/output Module Structure

**Purpose**: Establish the module directory and exports for the output recording functionality.

**Steps**:
1. Create directory `src/output/` at repository root
2. Create `src/output/__init__.py` with module docstring
3. Add imports for all public classes (will create them in later subtasks)
4. Export public API: `AsyncFileWriter`, `TranscriptFormatter`, `DebateMessage`

**Files**:
- `src/output/__init__.py` (new file, ~15 lines)

**Implementation**:
```python
"""
Output recording module for debate transcripts.

Provides non-blocking, fault-tolerant file writing for AI debate workflows.
"""

from src.output.async_file_writer import AsyncFileWriter
from src.output.transcript_formatter import TranscriptFormatter, DebateMessage

__all__ = ["AsyncFileWriter", "TranscriptFormatter", "DebateMessage"]
```

**Validation**:
- [ ] Directory exists: `src/output/`
- [ ] `from src.output import AsyncFileWriter, TranscriptFormatter, DebateMessage` works without errors
- [ ] Module has descriptive docstring

**Notes**:
- Keep this minimal - just exports. Real implementations come in T002-T008.

---

### Subtask T002 – Implement TranscriptFormatter.format_message()

**Purpose**: Convert DebateMessage objects into plain text format for file output.

**Steps**:
1. Create `src/output/transcript_formatter.py`
2. Import required modules: `datetime`, `dataclasses`, `typing`
3. Implement `TranscriptFormatter` class with `format_message()` method
4. Format: `[SPEAKER] ISO_TIMESTAMP\n<message content>\n\n` (double newline after each message)
5. Handle multi-line content correctly (preserve newlines within message)

**Files**:
- `src/output/transcript_formatter.py` (new file, ~60 lines)

**Implementation**:
```python
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass(frozen=True)
class DebateMessage:
    """A single debate message to be written to output file."""
    speaker: str  # "PRO", "CON", "JUDGE", "MODERATOR"
    timestamp: str  # ISO 8601 formatted datetime
    content: str  # The message text


class TranscriptFormatter:
    """Formats debate messages into plain text strings for file output."""

    @staticmethod
    def format_message(message: DebateMessage) -> str:
        """
        Convert a DebateMessage to plain text format.

        Format: [SPEAKER] ISO_TIMESTAMP
        <message content line 1>
        <message content line 2>
        ...

        Args:
            message: DebateMessage with speaker, timestamp, content

        Returns:
            Formatted string ready for file write
        """
        header = f"[{message.speaker}] {message.timestamp}"
        return f"{header}\n{message.content}\n\n"

    # validate_path() comes in T003
```

**Validation**:
- [ ] `format_message()` returns string starting with `[` and ending with `\n\n`
- [ ] Format matches: `[PRO] 2025-02-14T12:00:00Z\nThe evidence...\n\n`
- [ ] Multi-line content is preserved (not double-wrapped)

**Notes**:
- Use `frozen=True` on DebateMessage dataclass for immutability
- No timestamp generation here - that happens in nodes (they pass ISO string)
- Speaker values should NOT be validated here - that's caller's responsibility

---

### Subtask T003 – Implement TranscriptFormatter.validate_path()

**Purpose**: Check if a file path is writable before creating AsyncFileWriter.

**Steps**:
1. Add static method `validate_path(path: str) -> bool` to `TranscriptFormatter`
2. Check path is non-empty string
3. Attempt to create/truncate file at path (write test)
4. Return True if successful, False if any error occurs
5. Log errors for debugging (use `logging` module)

**Files**:
- `src/output/transcript_formatter.py` (modify, add ~20 lines)

**Implementation**:
```python
import logging
import aiofiles.aio as aiofiles  # For async I/O testing
from pathlib import Path

logger = logging.getLogger(__name__)

class TranscriptFormatter:
    # ... existing code ...

    @staticmethod
    async def validate_path(path: str) -> bool:
        """
        Check if a file path is writable by attempting to create/truncate it.

        Args:
            path: File path to validate

        Returns:
            True if path is writable, False otherwise
        """
        if not path or not path.strip():
            logger.error("Path is empty")
            return False

        try:
            # Attempt to create/truncate file
            async with aiofiles.open(path, mode='w') as f:
                await f.write("")  # Empty test write
                await f.flush()
            logger.info(f"Path validated: {path}")
            return True
        except (OSError, IOError) as e:
            logger.error(f"Path validation failed for {path}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error validating {path}: {e}", exc_info=True)
            return False
```

**Validation**:
- [ ] Empty string path returns False
- [ ] Valid writable path returns True
- [ ] Read-only path returns False (logs error)
- [ ] Non-existent directory returns False (logs error)
- [ ] Method is async (uses aiofiles)

**Notes**:
- Must be async to use aiofiles (matches AsyncFileWriter pattern)
- Don't create parent directories - fail gracefully per spec assumption #6
- Log all failures for debugging but never raise exceptions

---

### Subtask T004 – Implement DebateMessage Dataclass

**Purpose**: Create the value object that carries debate message data.

**Steps**:
1. Move or create `DebateMessage` dataclass in `transcript_formatter.py`
2. Define fields: `speaker: str`, `timestamp: str`, `content: str`
3. Use `@dataclass(frozen=True)` for immutability
4. Add docstring explaining each field
5. No methods needed - this is a value object

**Files**:
- `src/output/transcript_formatter.py` (modify, already partially created in T002)

**Implementation**:
```python
from dataclasses import dataclass

@dataclass(frozen=True)
class DebateMessage:
    """
    A single debate message to be written to output file.

    This is a value object (immutable data holder) representing one
    utterance in a debate. It does not contain any behavior.

    Attributes:
        speaker: Message source - must be one of "PRO", "CON", "JUDGE", "MODERATOR"
        timestamp: ISO 8601 datetime string indicating when message was generated
        content: The actual text content of the message (non-empty)
    """
    speaker: str
    timestamp: str
    content: str
```

**Validation**:
- [ ] `DebateMessage("PRO", "2025-02-14T12:00:00Z", "Test")` creates instance
- [ ] Attempting to modify field raises `FrozenInstanceError` (frozen=True working)
- [ ] Has descriptive docstring
- [ ] Used by `TranscriptFormatter.format_message()`

**Notes**:
- Validation of speaker values ("PRO", "CON", etc.) happens at call site (in nodes)
- No need for `__post_init__` validation - keep it simple
- Frozen ensures accidental modifications don't happen

---

### Subtask T005 – Implement AsyncFileWriter.__init__()

**Purpose**: Initialize the async file writer with queue and background task.

**Steps**:
1. Create `src/output/async_file_writer.py`
2. Import: `asyncio`, `logging`, `aiofiles`, `typing`
3. Define `AsyncFileWriter` class
4. In `__init__(self, file_path: str)`:
   - Store file_path
   - Create asyncio.Queue(maxsize=1000)
   - Start background task (store as instance variable)
   - Set `enabled` flag based on path validation
5. Import TranscriptFormatter and DebateMessage for internal use

**Files**:
- `src/output/async_file_writer.py` (new file, ~40 lines for this subtask)

**Implementation**:
```python
import asyncio
import logging
from typing import Optional

from src.output.transcript_formatter import TranscriptFormatter, DebateMessage

logger = logging.getLogger(__name__)


class AsyncFileWriter:
    """
    Manages asynchronous, non-blocking writes of debate messages to a file.

    Writes are queued and processed by a background task, ensuring the
    main debate flow is never blocked by file I/O. Write failures are logged
    but do not crash the application.
    """

    def __init__(self, file_path: str):
        """
        Initialize the async file writer.

        Args:
            file_path: Path to output file (will be created/truncated)

        Note:
            This must be called within an active asyncio event loop.
        """
        self.file_path = file_path
        self.write_queue: asyncio.Queue[str] = asyncio.Queue(maxsize=1000)
        self._writer_task: Optional[asyncio.Task] = None
        self._stop_event = asyncio.Event()
        self.enabled = False

        # Background task creation happens in T006 or caller

    # write_message(), _writer_task(), close() in subsequent subtasks
```

**Validation**:
- [ ] `writer = AsyncFileWriter("/tmp/test.txt")` creates instance
- [ ] `writer.write_queue` is asyncio.Queue with maxsize=1000
- [ ] `writer.enabled` is initially False (set during validation)
- [ ] Instance can be created without errors

**Notes**:
- Don't validate path or start background task in `__init__` - do that in async setup method
- Queue maxsize=1000 prevents memory runaway if writes fail repeatedly
- `_stop_event` will be used to signal background task to stop (T008)

**Risks**:
- If no event loop is running, queue/task operations will fail
- Document that this must be created within async context

---

### Subtask T006 – Implement AsyncFileWriter._writer_task()

**Purpose**: Create the background coroutine that processes queued writes asynchronously.

**Steps**:
1. Add async method `_writer_task(self) -> None` to `AsyncFileWriter`
2. Implement infinite loop: get message from queue, write to file, repeat
3. Use `aiofiles.open()` with mode='a' (append mode)
4. Handle all exceptions: log error, continue to next message (NEVER re-raise)
5. Support stop signal: check `_stop_event` or sentinel value (None)
6. Mark task done for each queue item

**Files**:
- `src/output/async_file_writer.py` (modify, add ~30 lines)

**Implementation**:
```python
import aiofiles.aio as aiofiles

class AsyncFileWriter:
    # ... __init__ and other methods ...

    async def _writer_task(self) -> None:
        """
        Background task that processes queued write operations.

        Continuously pulls formatted messages from write_queue and appends
        them to the output file. Logs errors but never raises exceptions.

        Runs until:
        - Sentinel (None) received from queue
        - _stop_event is set
        """
        logger.info(f"Writer task started for {self.file_path}")

        try:
            while not self._stop_event.is_set():
                # Get message with timeout to allow checking stop_event
                try:
                    message = await asyncio.wait_for(
                        self.write_queue.get(),
                        timeout=0.1
                    )
                except asyncio.TimeoutError:
                    continue  # Check stop_event and loop again

                if message is None:  # Sentinel to stop
                    break

                try:
                    async with aiofiles.open(self.file_path, mode='a') as f:
                        await f.write(message)
                        await f.flush()  # Ensure data is written
                    logger.debug(f"Wrote message to {self.file_path}")
                except Exception as e:
                    # CRITICAL: Log but NEVER re-raise
                    logger.error(f"Failed to write to {self.file_path}: {e}", exc_info=True)
                finally:
                    self.write_queue.task_done()

        except asyncio.CancelledError:
            logger.info("Writer task cancelled")
        except Exception as e:
            logger.error(f"Writer task crashed: {e}", exc_info=True)
        finally:
            logger.info(f"Writer task stopped for {self.file_path}")
```

**Validation**:
- [ ] Task runs until sentinel (None) or stop_event
- [ ] Uses aiofiles.open() with mode='a' (append)
- [ ] All exceptions caught and logged, never re-raised
- [ ] Calls `task_done()` for each queue item
- [ ] Logs info messages on start/stop

**Notes**:
- Timeout on queue.get() ensures responsive stop_event checking
- Sentinel (None) is passed by `close()` to signal clean shutdown
- Mode='a' means each message appends to file (not overwrite)
- flush() ensures data hits disk before continuing

**Risks**:
- If aiofiles is not installed, import will fail (added to requirements in WP02)
- Very long messages could block async loop - accept this as edge case

---

### Subtask T007 – Implement AsyncFileWriter.write_message()

**Purpose**: Provide public API to queue messages for async writing.

**Steps**:
1. Add method `write_message(self, message: DebateMessage) -> None` to `AsyncFileWriter`
2. Check if `self.enabled` is False - if so, return immediately (no-op)
3. Use `TranscriptFormatter.format_message()` to convert DebateMessage to string
4. Put formatted string into `write_queue` (non-blocking)
5. Don't await anything - return immediately after queuing

**Files**:
- `src/output/async_file_writer.py` (modify, add ~15 lines)

**Implementation**:
```python
from src.output.transcript_formatter import TranscriptFormatter, DebateMessage

class AsyncFileWriter:
    # ... __init__, _writer_task ...

    def write_message(self, message: DebateMessage) -> None:
        """
        Queue a message for async file writing.

        This method is NON-BLOCKING. It formats the message and
        places it in the queue, then returns immediately.

        Args:
            message: DebateMessage to write to file

        Note:
            If writer is not enabled (path validation failed), this is a no-op.
            If queue is full, this will block briefly - accept this as edge case.
        """
        if not self.enabled:
            return  # No-op if writer disabled

        formatted = TranscriptFormatter.format_message(message)
        try:
            self.write_queue.put_nowait(formatted)
        except asyncio.QueueFull:
            # Queue full (1000 items) - log but don't crash
            logger.warning(f"Write queue full, message dropped: {message.speaker}")

        # No await - this is synchronous/non-blocking
```

**Validation**:
- [ ] `writer.write_message(DebateMessage(...))` returns immediately (not awaitable)
- [ ] If `enabled=False`, method returns without error
- [ ] Uses `TranscriptFormatter.format_message()` to convert
- [ ] Puts formatted string into queue
- [ ] Uses `put_nowait()` to avoid blocking (with QueueFull fallback)

**Notes**:
- `put_nowait()` is truly non-blocking but may raise QueueFull (handle gracefully)
- Queue filling to 1000 items is extreme edge case (debate would be 1000 messages long)
- If queue is full, we log warning and drop message - acceptable tradeoff for non-blocking

**Risks**:
- QueueFull means we're dropping messages - but this prevents memory exhaustion
- Alternative: `await queue.put()` would block - violates non-blocking requirement

---

### Subtask T008 – Implement AsyncFileWriter.close()

**Purpose**: Flush pending writes and stop the background task gracefully.

**Steps**:
1. Add async method `close(self) -> None` to `AsyncFileWriter`
2. Put sentinel (None) into queue to signal background task to stop
3. Wait for queue to drain (`await write_queue.join()`)
4. Wait for background task to complete (`await _writer_task`)
5. Handle cancellation if task takes too long (optional timeout)
6. Log closure for debugging

**Files**:
- `src/output/async_file_writer.py` (modify, add ~20 lines)

**Implementation**:
```python
class AsyncFileWriter:
    # ... all other methods ...

    async def close(self) -> None:
        """
        Stop the writer and flush all pending writes.

        Signals the background task to stop, waits for queue to drain,
        and awaits task completion. Call this before program exit.

        Note:
            This is async - must be awaited.
        """
        if not self._writer_task:
            return  # Never started, nothing to close

        logger.info(f"Closing writer for {self.file_path}")

        # Signal task to stop by putting sentinel
        try:
            self.write_queue.put_nowait(None)
        except asyncio.QueueFull:
            logger.error("Queue full during close, cancelling task")
            self._writer_task.cancel()

        # Wait for all items to be processed
        try:
            await asyncio.wait_for(
                self.write_queue.join(),
                timeout=5.0  # Give up to 5 seconds
            )
        except asyncio.TimeoutError:
            logger.warning("Queue drain timed out, forcing task stop")

        # Wait for task to exit
        try:
            await asyncio.wait_for(
                self._writer_task,
                timeout=2.0  # Give up to 2 more seconds
            )
        except asyncio.TimeoutError:
            logger.warning("Task stop timed out")
            self._writer_task.cancel()

        self.enabled = False
        logger.info(f"Writer closed for {self.file_path}")
```

**Validation**:
- [ ] `await writer.close()` drains queue before returning
- [ ] Background task exits cleanly after sentinel
- [ ] `writer.enabled` is set to False after close
- [ ] Method has timeout to prevent hanging indefinitely
- [ ] Logs closure process for debugging

**Notes**:
- Sentinel (None) tells `_writer_task()` to exit its loop
- `join()` waits until all queued items are marked done
- Timeouts prevent indefinite hangs if task is stuck
- After close(), any further `write_message()` calls are no-ops (enabled=False)

**Risks**:
- If close() is not called, background task may never stop (orphaned)
- Timeout on join() means messages might be lost - acceptable for graceful shutdown

---

## Test Strategy

*Note: Full testing happens in WP04. During this WP, verify basic functionality manually.*

**Manual Verification**:
1. Create test script to verify module works:
```python
import asyncio
from src.output import AsyncFileWriter, TranscriptFormatter, DebateMessage

async def test():
    writer = AsyncFileWriter("/tmp/test_debate.txt")
    writer.enabled = True  # Skip validation for quick test

    msg = DebateMessage(
        speaker="PRO",
        timestamp="2025-02-14T12:00:00Z",
        content="Test message"
    )
    writer.write_message(msg)
    await writer.close()

asyncio.run(test())
```

2. Run and verify `/tmp/test_debate.txt` contains formatted output

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|-------|---------|------------|
| **aiofiles not installed** | ImportError, module unusable | Will be added to requirements.txt in WP02. For now, document dependency clearly |
| **Background task never stops** | Orphaned coroutine, resource leak | Ensure close() is called, use timeout, add cancellation fallback |
| **Queue fills (1000 items)** | Messages dropped, incomplete transcript | Acceptable to prevent memory exhaustion. Log warning when it happens |
| **File becomes unwritable mid-debate** | All subsequent writes fail | Log error, continue debate. Each write attempted independently (per FR-006) |
| **Event loop not running** | Queue/Task operations fail | Document in docstrings that __init__ requires active loop |

**Monitoring Considerations**:
- Log queue size warning if >500 items (half full)
- Log every write failure with full traceback for debugging
- Track background task lifecycle in logs (start, stop, errors)

---

## Review Guidance

**Acceptance Checkpoints for Reviewers**:

1. **Module Structure**:
   - [ ] `src/output/` directory exists with 3 Python files
   - [ ] All classes importable from `src.output`
   - [ ] No circular imports

2. **DebateMessage**:
   - [ ] Is frozen dataclass with 3 fields
   - [ ] Has descriptive docstring

3. **TranscriptFormatter**:
   - [ ] `format_message()` produces exact spec format
   - [ ] `validate_path()` is async and returns bool
   - [ ] Errors logged but never raised

4. **AsyncFileWriter**:
   - [ ] Queue created with maxsize=1000
   - [ ] Background task uses aiofiles.open() with mode='a'
   - [ ] `write_message()` returns immediately (non-blocking)
   - [ ] All exceptions in _writer_task are caught and logged
   - [ ] `close()` drains queue before returning
   - [ ] `enabled` flag properly controls behavior

5. **Integration**:
   - [ ] All classes work together (manual test passes)
   - [ ] Code follows data model from ../data-model.md
   - [ ] No hardcoded file paths or messages

**Failure Criteria** (return for rework if any true):
- ❌ `write_message()` blocks or awaits anything
- ❌ `_writer_task()` raises exceptions on write failures
- ❌ Background task lacks stop mechanism
- ❌ Format doesn't match `[SPEAKER] ISO_TIMESTAMP\ncontent\n\n`
- ❌ aiofiles imports but dependency not in requirements.txt (will add in WP02)

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
- 2025-02-14T12:00:00Z – system – lane=planned – Prompt generated.
