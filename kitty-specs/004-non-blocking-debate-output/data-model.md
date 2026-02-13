# Data Model: Non-Blocking Debate Output Recording

**Feature**: 004-non-blocking-debate-output
**Date**: 2025-02-14

## Overview

This document defines the data entities and their relationships for the debate output recording feature.

## Entities

### DebateMessage

A value object representing a single debate message to be written to the output file.

**Fields**

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| `speaker` | `str` | Source of the message | Must be one of: `"PRO"`, `"CON"`, `"JUDGE"`, `"MODERATOR"` |
| `timestamp` | `str` | ISO 8601 datetime string | Must be valid ISO 8601 format |
| `content` | `str` | The message text | Must be non-empty string |

**Relationships**: None (value object)

**Example**

```python
DebateMessage(
    speaker="PRO",
    timestamp="2025-02-14T12:00:00Z",
    content="The document presents compelling evidence..."
)
```

---

### AsyncFileWriter

Manages asynchronous, non-blocking writes of debate messages to a file.

**Fields**

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| `file_path` | `str` | Absolute or relative path to output file | Must be non-empty string |
| `enabled` | `bool` | Whether writing is active | False if initialization failed |
| `write_queue` | `asyncio.Queue` | Queue of pending formatted message strings | Maximum size: 1000 (prevents unbounded memory growth) |

**Methods**

| Method | Signature | Description |
|--------|------------|-------------|
| `__init__` | `(file_path: str) -> None` | Initializes writer; validates path, starts background task |
| `write_message` | `(message: DebateMessage) -> None` | Formats and queues a message for async write |
| `_writer_task` | `() -> Coroutine` | Background task that processes write_queue |
| `close` | `() -> Coroutine` | Flushes remaining writes and stops background task |

**State Transitions**

```
[Initialized] → [Running] → [Closing] → [Closed]
                    ↓
               [Disabled] (if init fails)
```

**Behavior**

- If `file_path` is invalid/unwritable during init: sets `enabled=False`, logs error, becomes no-op
- Each `write_message()` call queues formatted string and returns immediately (non-blocking)
- Background task processes queue asynchronously, writing one message at a time
- Write failures are logged but do not stop the task (continues processing next message)
- `close()` waits for queue to drain, then stops background task

---

### TranscriptFormatter

Formats debate messages into plain text strings for file output.

**Methods**

| Method | Signature | Description |
|--------|------------|-------------|
| `format_message` | `(message: DebateMessage) -> str` | Converts message to plain text format |
| `validate_path` | `(path: str) -> bool` | Checks if path is writable (creates/truncates test file) |

**Output Format**

```
[SPEAKER] ISO8601_TIMESTAMP
<content_line_1>
<content_line_2>
...

```

**Example**

```python
formatter.format_message(DebateMessage(
    speaker="PRO",
    timestamp="2025-02-14T12:00:00Z",
    content="The evidence shows..."
))

# Returns:
# "[PRO] 2025-02-14T12:00:00Z\nThe evidence shows...\n\n"
```

---

## Data Flow

```
┌─────────────────┐
│  Debate Node    │
│  (generates     │
│   message)      │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  AsyncFileWriter.write_message()      │
│  - Accepts DebateMessage             │
│  - Formats via TranscriptFormatter   │
│  - Puts in asyncio.Queue            │
│  - Returns immediately               │
└─────────────────────────────────────┘
         │
         │ (async background)
         ▼
┌─────────────────────────────────────┐
│  _writer_task()                     │
│  - Gets from queue                  │
│  - Writes to file via aiofiles     │
│  - Logs errors, continues           │
└─────────────────────────────────────┘
```

---

## Validation Rules

1. **Speaker Validation**
   - Must be exact match to one of: `"PRO"`, `"CON"`, `"JUDGE"`, `"MODERATOR"`
   - Case-sensitive

2. **Timestamp Validation**
   - Must parse as valid ISO 8601 datetime
   - Should include timezone (use UTC or local offset)

3. **Content Validation**
   - Must be non-empty string (after stripping whitespace)
   - No length limit (allow long arguments)

4. **File Path Validation**
   - Must be non-empty string
   - Parent directory must exist (not auto-created)
   - Must be writable (test via attempted open/create)
   - If validation fails: log error, set `enabled=False`, continue without crash
