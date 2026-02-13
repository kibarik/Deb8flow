# Developer Quickstart: Debate Output Recording

**Feature**: 004-non-blocking-debate-output
**For**: Developers adding output recording to CLI tools

## Overview

The debate output recording module provides non-blocking, fault-tolerant file writing for debate transcripts. It's designed to be easily integrated into any async CLI tool.

## Quick Integration Guide

### Step 1: Install Dependencies

Add to `requirements.txt`:

```
aiofiles>=24.1.0
```

### Step 2: Import the Module

```python
from src.output.async_file_writer import AsyncFileWriter
from src.output.transcript_formatter import TranscriptFormatter, DebateMessage
```

### Step 3: Parse CLI Argument

Add `--output` to your argument parser:

```python
parser.add_argument(
    "--output",
    help="Path to file for recording debate transcript (optional)"
)
```

### Step 4: Create the Writer

In your async main function:

```python
async def main():
    # ... existing setup ...

    # Create writer if --output provided
    writer = None
    if args.output:
        writer = AsyncFileWriter(args.output)
        if not writer.enabled:
            logger.warning(f"Output file could not be initialized: {args.output}")
```

### Step 5: Pass Writer to Workflow

Modify your workflow to accept and use the writer:

```python
# Option A: Pass as parameter to workflow.run()
result = await workflow.run(initial_state, output_writer=writer)

# Option B: Store in state for nodes to access
initial_state["output_writer"] = writer
result = await workflow.run(initial_state=initial_state)
```

### Step 6: Write Messages in Nodes

In each debate node (PRO, CON, JUDGE, etc.):

```python
async def some_debater_node(state: DebateState, output_writer=None):
    # ... generate message ...

    # Write to output file if writer enabled
    if output_writer and output_writer.enabled:
        message = DebateMessage(
            speaker="PRO",  # or "CON", "JUDGE", etc.
            timestamp=datetime.now(timezone.utc).isoformat(),
            content=generated_message_text
        )
        await output_writer.write_message(message)

    return {"messages": [...]}
```

### Step 7: Cleanup on Completion

```python
try:
    result = await workflow.run(initial_state, output_writer=writer)
    # ... display results ...
finally:
    if writer:
        await writer.close()
```

## Complete Example

```python
import argparse
import asyncio
import logging
from datetime import datetime, timezone

from src.output.async_file_writer import AsyncFileWriter
from src.output.transcript_formatter import DebateMessage
from workflow.document_debate_workflow import DocumentDebateWorkflow

logger = logging.getLogger(__name__)

async def main():
    parser = argparse.ArgumentParser(description="Run debate with output recording")
    parser.add_argument("--docx", help="Path to .docx file")
    parser.add_argument("--output", help="Output file for transcript")
    args = parser.parse_args()

    # Create writer
    writer = AsyncFileWriter(args.output) if args.output else None
    if writer and not writer.enabled:
        logger.warning(f"Output file not writable: {args.output}")
        writer = None

    try:
        # Run workflow
        workflow = DocumentDebateWorkflow()
        result = await workflow.run(
            initial_state={"document_input": load_docx(args.docx)},
            output_writer=writer
        )

        # Display verdict
        logger.info(f"Debate complete: {result['verdict']}")
    finally:
        if writer:
            await writer.close()

if __name__ == "__main__":
    asyncio.run(main())
```

## Testing

### Unit Tests (Mocking File I/O)

```python
import pytest
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_write_message():
    writer = AsyncFileWriter("/tmp/test.txt")

    # Mock the async write
    with patch("aiofiles.aio.open") as mock_open:
        mock_file = AsyncMock()
        mock_file.write = AsyncMock()
        mock_file.flush = AsyncMock()
        mock_open.return_value.__aenter__.return_value = mock_file

        message = DebateMessage(
            speaker="PRO",
            timestamp="2025-02-14T12:00:00Z",
            content="Test message"
        )
        await writer.write_message(message)

        # Verify write was called
        assert mock_file.write.called
```

### Integration Tests (Real File)

```python
@pytest.mark.asyncio
async def test_real_file_write(tmp_path):
    output_file = tmp_path / "debate.txt"
    writer = AsyncFileWriter(str(output_file))

    message = DebateMessage(
        speaker="PRO",
        timestamp="2025-02-14T12:00:00Z",
        content="Integration test message"
    )
    await writer.write_message(message)
    await writer.close()

    # Verify file content
    content = output_file.read_text()
    assert "[PRO] 2025-02-14T12:00:00Z" in content
    assert "Integration test message" in content
```

## Error Scenarios

### Unwritable Path

```python
# On read-only filesystem
writer = AsyncFileWriter("/read-only/file.txt")
assert writer.enabled == False  # Disabled gracefully

# Writes are no-ops
await writer.write_message(message)  # Logs error, doesn't crash
```

### Disk Full

```python
# When disk fills mid-debate
# - Writer logs error
# - Debate continues
# - Subsequent writes are attempted
```

## Troubleshooting

**Problem**: Messages not appearing in file
- Check: `writer.enabled` is `True`
- Check: `await writer.close()` is called in `finally` block
- Check: File path is absolute or relative to correct directory

**Problem**: CLI slowed down with output
- Verify: Writes are truly async (no `.wait()` or `.result()` calls)
- Profile: Queue size should be < 1000 items

**Problem**: Permission errors
- Check: Parent directory exists
- Check: User has write permissions
- Verify: `--output` path is not a directory
