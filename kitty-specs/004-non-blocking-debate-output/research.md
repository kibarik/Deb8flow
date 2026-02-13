# Research: Non-Blocking Debate Output Recording

**Feature**: 004-non-blocking-debate-output
**Date**: 2025-02-14
**Status**: Complete

## Overview

This document captures technical research and decisions for implementing non-blocking file output recording in the document debate CLI.

## Research Topic 1: Async File I/O in Python

### Question

What is the best approach for non-blocking file writes in Python 3.11+ that integrates with the existing asyncio-based workflow?

### Options Evaluated

| Option | Pros | Cons | Verdict |
|--------|-------|-------|---------|
| **aiofiles library** | Native async/await syntax, integrates with existing asyncio event loop, battle-tested | External dependency (but small and stable) | **CHOSEN** |
| **threading.Thread** | No external dependencies, simple to understand | Adds thread management complexity, requires queue coordination, less "pythonic async" | Rejected |
| **concurrent.futures.ThreadPoolExecutor** | Built-in, managed thread pool | Overkill for single-file writes, harder to ensure non-blocking semantics | Rejected |

### Decision

**Use aiofiles library with asyncio**

**Rationale**:
- The existing workflow is already async (`DocumentDebateWorkflow.run()` returns an awaitable)
- aiofiles provides `async_open()`, `await file.write()`, `await file.flush()` - natural fit
- Zero additional thread management complexity
- User confirmed this choice during planning discovery

### Implementation Notes

```python
import aiofiles.aio as aiofiles

async def write_to_file(path: str, content: str):
    async with aiofiles.open(path, mode='a') as f:
        await f.write(content)
        await f.flush()  # Ensure data is written
```

---

## Research Topic 2: Error Handling for Non-Blocking Writes

### Question

How should the system handle file write failures without blocking or crashing the main debate workflow?

### Options Evaluated

| Option | Pros | Cons | Verdict |
|--------|-------|-------|---------|
| **Log and continue** | Simple, meets requirement "failures must not impact main flow" | Silent failures if logs not monitored | **CHOSEN** |
| **Retry with backoff** | May recover from transient failures | Could delay main flow, adds complexity | Rejected |
| **Circuit breaker** | Prevents cascading failures | Over-engineering for single-file writes | Rejected |

### Decision

**Log error with traceback, continue debate immediately**

**Rationale**:
- User explicitly stated: "падение записи также не должно влиять на основной поток дебатов" (write failures must not impact main flow)
- Retries could delay the main debate if writes are slow/failing repeatedly
- Logging provides visibility for debugging without interrupting execution
- Each write failure is handled independently (one failure doesn't disable all future writes)

### Implementation Pattern

```python
import logging

logger = logging.getLogger(__name__)

async def _writer_task(self):
    while True:
        message = await self.write_queue.get()
        if message is None:  # Sentinel to stop
            break
        try:
            async with aiofiles.open(self.file_path, mode='a') as f:
                await f.write(message)
                await f.flush()
        except Exception as e:
            logger.error(f"Failed to write to output file: {e}", exc_info=True)
        finally:
            self.write_queue.task_done()
```

---

## Research Topic 3: Message Format for Plain Text Output

### Question

What format should debate messages use in the plain text output file?

### Options Evaluated

| Option | Pros | Cons | Verdict |
|--------|-------|-------|---------|
| **Bracketed speaker + ISO timestamp** | Human-readable, machine-parseable, standard format | ISO timestamps not "pretty" | **CHOSEN** |
| **Markdown with headers** | Familiar to devs, renders nicely | Not "plain text" per spec requirement | Rejected |
| **JSON lines (JSONL)** | Machine-parseable, structured | Not "plain text" per spec requirement | Rejected |

### Decision

**Format: `[SPEAKER] ISO8601_TIMESTAMP\n<message content>\n\n`**

**Rationale**:
- Meets "plain text" requirement from FR-007
- Speaker in brackets is clear and parseable (`[PRO]`, `[CON]`, `[JUDGE]`)
- ISO 8601 timestamp is machine-sortable and unambiguous
- Double newline separates messages for readability

### Example Output

```
[PRO] 2025-02-14T12:00:00Z
The document presents a compelling case for increased investment in AI infrastructure. The evidence shows...

[CON] 2025-02-14T12:01:23Z
While the document makes some valid points, it fails to address critical concerns about energy consumption…

[JUDGE] 2025-02-14T12:05:47Z
After evaluating both positions, the evidence supports PRO position. WINNER: PRO
```

---

## Dependencies

### New Dependency

| Package | Version | Purpose |
|----------|---------|---------|
| **aiofiles** | ^24.1.0 | Async file I/O operations |

### Add to requirements.txt

```
aiofiles>=24.1.0
```

---

## Summary

All research topics resolved. Key decisions:

1. **Async I/O**: Use aiofiles library (user-confirmed)
2. **Error handling**: Log and continue (meets non-blocking requirement)
3. **Message format**: `[SPEAKER] ISO_TIMESTAMP\ncontent\n\n` (meets plain text requirement)

No NEEDS CLARIFICATION items remain. Ready to proceed with implementation.
