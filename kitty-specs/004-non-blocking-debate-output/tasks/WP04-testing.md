---
work_package_id: "WP04"
subtasks:
  - "T020"
  - "T021"
  - "T022"
  - "T023"
  - "T024"
title: "Testing"
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

# Work Package Prompt: WP04 – Testing

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

**Primary Objective**: Write comprehensive unit tests for the output module and integration tests for the full CLI workflow with output recording.

**Success Criteria**:
- [ ] `tests/unit/output/` directory exists with `__init__.py`
- [ ] `test_transcript_formatter.py` tests format_message() and validate_path()
- [ ] `test_async_file_writer.py` tests queue behavior, write operations, close()
- [ ] All unit tests pass (`pytest tests/unit/output/`)
- [ ] `test_debate_output_integration.py` runs full workflow with output
- [ ] Integration test verifies file content matches expected format
- [ ] Error scenario tests cover read-only path, invalid speaker, special characters
- [ ] Tests use proper fixtures (tmp_path, mock asyncio)
- [ ] Code coverage for output module >80%

---

## Context & Constraints

**Prerequisites**:
- **WP01** must be complete (module to test must exist)
- **WP02-WP03** helpful for integration tests (full workflow working)

**Related Documents**:
- [Spec User Stories](../spec.md#user-scenarios-testing) - Acceptance scenarios
- [Data Model](../data-model.md) - Entity behavior to verify
- [Quickstart Testing Section](../quickstart.md#testing) - Test examples

**Key Constraints**:
- Use pytest for all tests
- Mock aiofiles operations in unit tests (no actual disk I/O)
- Use tmp_path fixtures for integration tests (real file I/O)
- Tests must be async (use @pytest.mark.asyncio)
- Verify error handling doesn't raise exceptions
- Test both success and failure paths

**Architecture Decisions**:
- Unit tests: Mock aiofiles to test queue logic without file dependencies
- Integration tests: Use real files with tmp_path fixture
- Error tests: Simulate failure conditions (read-only paths, disk full)
- Use fixtures for common setup (test message, mock writer)

---

## Subtasks & Detailed Guidance

### Subtask T020 – Create Unit Test Directory Structure

**Purpose**: Establish testing infrastructure for output module.

**Steps**:
1. Create directory: `tests/unit/output/`
2. Create `tests/unit/output/__init__.py` with test package initialization
3. Ensure pytest can discover tests in this directory
4. Create conftest.py if needed for shared test configuration

**Files**:
- `tests/unit/output/__init__.py` (new file, ~5 lines)
- `tests/unit/output/conftest.py` (optional, for shared fixtures)

**Implementation**:
```python
# tests/unit/output/__init__.py
"""
Unit tests for debate output recording module.
"""
```

**Optional conftest.py**:
```python
import pytest
from datetime import datetime, timezone
from src.output.transcript_formatter import DebateMessage

@pytest.fixture
def sample_message():
    """Provide a sample DebateMessage for tests."""
    return DebateMessage(
        speaker="PRO",
        timestamp="2025-02-14T12:00:00Z",
        content="Test argument content"
    )

@pytest.fixture
def sample_messages():
    """Provide multiple sample messages."""
    return [
        DebateMessage("PRO", "2025-02-14T12:00:00Z", "Pro argument"),
        DebateMessage("CON", "2025-02-14T12:01:00Z", "Con argument"),
        DebateMessage("JUDGE", "2025-02-14T12:05:00Z", "Verdict"),
    ]
```

**Validation**:
- [ ] `tests/unit/output/` directory exists
- [ ] `__init__.py` file created
- [ ] `pytest tests/unit/output/` discovers tests (create one dummy test if needed)
- [ ] Conftest.py fixtures import without errors

**Notes**:
- Keep __init__.py minimal (just docstring)
- Use fixtures for reusable test data (sample_message, etc.)
- Consider using pyproject.toml pytest config if needed

---

### Subtask T021 – Write Unit Tests for TranscriptFormatter

**Purpose**: Verify format_message() and validate_path() work correctly.

**Steps**:
1. Create `tests/unit/output/test_transcript_formatter.py`
2. Import TranscriptFormatter, DebateMessage, pytest
3. Test format_message():
   - Test with basic message (single line content)
   - Test with multi-line content (preserves internal newlines)
   - Test special characters (Unicode, quotes, brackets)
   - Verify format: `[SPEAKER] ISO_TIMESTAMP\ncontent\n\n`
4. Test validate_path() (async):
   - Test valid writable path (returns True)
   - Test empty string (returns False)
   - Test read-only path (returns False)
   - Test non-existent directory (returns False)
5. Use fixtures and parameters for variety

**Files**:
- `tests/unit/output/test_transcript_formatter.py` (new file, ~80 lines)

**Implementation**:
```python
import pytest
from unittest.mock import patch
from src.output.transcript_formatter import TranscriptFormatter, DebateMessage

# Use fixtures from T020 conftest.py

class TestTranscriptFormatterFormatMessage:
    """Test TranscriptFormatter.format_message() behavior."""

    def test_basic_message_format(self, sample_message):
        """Format basic message with speaker, timestamp, content."""
        result = TranscriptFormatter.format_message(sample_message)

        assert result.startswith("[PRO] 2025-02-14T12:00:00Z\n")
        assert result.endswith("\n\n")
        assert "Test argument content" in result

    def test_multiline_content(self, sample_message):
        """Preserve internal newlines in message content."""
        multi_line_msg = DebateMessage(
            speaker="PRO",
            timestamp="2025-02-14T12:00:00Z",
            content="Line 1\nLine 2\nLine 3"
        )
        result = TranscriptFormatter.format_message(multi_line_msg)

        # Should preserve internal newlines
        assert "Line 1\nLine 2\nLine 3" in result
        # But still end with double newline
        assert result.endswith("\n\n")

    def test_special_characters(self, sample_message):
        """Handle Unicode and special characters in content."""
        special_msg = DebateMessage(
            speaker="CON",
            timestamp="2025-02-14T12:00:00Z",
            content="Quotes: \"hello\", emojis: 😀, brackets: [test]"
        )
        result = TranscriptFormatter.format_message(special_msg)

        assert "[CON]" in result
        assert "quotes:" in result
        assert "😀" in result

    def test_all_speaker_types(self):
        """Format works for all valid speaker types."""
        for speaker in ["PRO", "CON", "JUDGE", "MODERATOR"]:
            msg = DebateMessage(
                speaker=speaker,
                timestamp="2025-02-14T12:00:00Z",
                content="Test"
            )
            result = TranscriptFormatter.format_message(msg)
            assert result.startswith(f"[{speaker}]")

    def test_timestamp_preservation(self, sample_message):
        """Include exact timestamp string in output."""
        result = TranscriptFormatter.format_message(sample_message)
        assert "2025-02-14T12:00:00Z" in result
        # ISO timestamp should be verbatim


@pytest.mark.asyncio
class TestTranscriptFormatterValidatePath:
    """Test TranscriptFormatter.validate_path() async behavior."""

    async def test_valid_writable_path(self, tmp_path):
        """Return True for writable file path."""
        test_file = tmp_path / "test_writable.txt"
        result = await TranscriptFormatter.validate_path(str(test_file))
        assert result is True
        # Verify file was created/truncated
        assert test_file.exists()

    async def test_empty_string_path(self):
        """Return False for empty path string."""
        result = await TranscriptFormatter.validate_path("")
        assert result is False
        result = await TranscriptFormatter.validate_path("   ")
        assert result is False

    @patch("aiofiles.aio.open")
    async def test_unwritable_path(self, mock_open, tmp_path):
        """Return False when path is not writable."""
        # Make aiofiles.open raise OSError
        mock_open.side_effect = OSError("Permission denied")

        result = await TranscriptFormatter.validate_path(str(tmp_path / "read-only.txt"))
        assert result is False

    @patch("aiofiles.aio.open")
    async def test_ioexception_handling(self, mock_open):
        """Handle IOError gracefully."""
        mock_open.side_effect = IOError("Disk error")
        result = await TranscriptFormatter.validate_path("/bad/path")
        assert result is False
```

**Validation**:
- [ ] All format tests pass (basic, multi-line, special chars, all speakers)
- [ ] All validate tests pass (valid, empty, unwritable, error handling)
- [ ] Tests are async (where appropriate)
- [ ] Tests use fixtures and patches appropriately
- [ ] Test file named correctly: `test_transcript_formatter.py`

**Notes**:
- Use @pytest.mark.asyncio for async tests
- Patch aiofiles.open to simulate errors without real I/O
- Test both success and failure paths
- Verify exact format matches spec requirement

---

### Subtask T022 – Write Unit Tests for AsyncFileWriter

**Purpose**: Verify AsyncFileWriter queue behavior, non-blocking writes, and cleanup.

**Steps**:
1. Create `tests/unit/output/test_async_file_writer.py`
2. Import AsyncFileWriter, TranscriptFormatter, DebateMessage, pytest, asyncio
3. Test __init__():
   - Verify queue is created with maxsize=1000
   - Verify enabled flag defaults to False
   - Verify _writer_task is stored but not started
4. Test write_message():
   - Verify it's non-blocking (returns immediately, not awaitable)
   - Verify message formatted and queued (check queue size)
   - Verify no-op when enabled=False
5. Test _writer_task():
   - Mock aiofiles to verify write operations
   - Verify exceptions are caught and logged (not raised)
   - Verify task stops on sentinel (None)
6. Test close():
   - Verify sentinel is queued
   - Verify queue is drained before return
   - Verify background task is stopped
7. Test integration (write + close):
   - Multiple messages written, closed, verify all written

**Files**:
- `tests/unit/output/test_async_file_writer.py` (new file, ~120 lines)

**Implementation**:
```python
import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from src.output.async_file_writer import AsyncFileWriter
from src.output.transcript_formatter import DebateMessage

@pytest.mark.asyncio
class TestAsyncFileWriter:
    """Test AsyncFileWriter behavior."""

    async def test_init_creates_queue(self):
        """__init__ creates write_queue with maxsize=1000."""
        writer = AsyncFileWriter("/tmp/test.txt")
        assert writer.write_queue.maxsize == 1000
        assert writer.enabled == False  # Not validated yet

    async def test_write_message_is_non_blocking(self, tmp_path):
        """write_message() returns immediately without await."""
        writer = AsyncFileWriter(str(tmp_path / "test.txt"))
        writer.enabled = True

        msg = DebateMessage("PRO", "2025-02-14T12:00:00Z", "Test")

        # This should NOT be awaitable
        result = writer.write_message(msg)
        assert result is None  # Function returns None

        # But message should be queued
        assert writer.write_queue.qsize() == 1

    async def test_write_message_formats_before_queuing(self, tmp_path):
        """write_message() formats message before queueing."""
        writer = AsyncFileWriter(str(tmp_path / "test.txt"))
        writer.enabled = True

        msg = DebateMessage("CON", "2025-02-14T12:00:00Z", "Test content")

        with patch.object(writer) as mock_formatter:
            # Should call format_message
            mock_formatter.TranscriptFormatter.format_message.return_value = "formatted"

            writer.write_message(msg)

        # Verify format was called
        from unittest.mock import call
        call_args = call(mock_formatter.TranscriptFormatter.format_message)
        assert call_args[0][0] == msg

    async def test_write_message_noop_when_disabled(self, tmp_path):
        """write_message() does nothing when enabled=False."""
        writer = AsyncFileWriter(str(tmp_path / "test.txt"))
        writer.enabled = False  # Explicitly disable

        msg = DebateMessage("PRO", "2025-02-14T12:00:00Z", "Test")
        writer.write_message(msg)

        # Should not queue
        assert writer.write_queue.qsize() == 0

    @patch("aiofiles.aio.open")
    async def test_writer_task_writes_to_file(self, mock_open, tmp_path):
        """Background task writes formatted messages to file."""
        # Setup mock
        mock_file = AsyncMock()
        mock_file.write = AsyncMock()
        mock_file.flush = AsyncMock()
        mock_open.return_value.__aenter__.return_value = mock_file

        writer = AsyncFileWriter(str(tmp_path / "test.txt"))
        writer.enabled = True

        # Start task manually for testing
        task = asyncio.create_task(writer._writer_task())

        # Queue a message
        msg = DebateMessage("PRO", "2025-02-14T12:00:00Z", "Test")
        writer.write_message(msg)

        # Give task time to process
        await asyncio.sleep(0.1)

        # Verify write was attempted
        assert mock_file.write.called
        assert mock_file.flush.called

        # Clean up
        await writer.close()

    @patch("aiofiles.aio.open")
    async def test_writer_task_handles_write_failures(self, mock_open):
        """Write failures are logged but not raised."""
        import logging
        from unittest.mock import Mock

        # Make aiofiles.open raise exception
        mock_open.side_effect = OSError("Write failed")

        # Capture log calls
        with patch.object(logging.getLogger) as mock_logger:
            writer = AsyncFileWriter("/tmp/test.txt")
            writer.enabled = True

            msg = DebateMessage("PRO", "2025-02-14T12:00:00Z", "Test")
            writer.write_message(msg)

            # Start and run task briefly
            task = asyncio.create_task(writer._writer_task())
            await asyncio.sleep(0.1)
            await writer.close()

            # Verify error was logged (not raised)
            assert mock_logger.return_value.error.called

    async def test_close_drains_queue(self, tmp_path):
        """close() waits for queue to drain before returning."""
        with patch("aiofiles.aio.open"):
            writer = AsyncFileWriter(str(tmp_path / "test.txt"))
            writer.enabled = True

            # Queue multiple messages
            for i in range(5):
                msg = DebateMessage("PRO", f"2025-02-14T12:0{i}:00Z", f"Msg {i}")
                writer.write_message(msg)

            # Start background task
            asyncio.create_task(writer._writer_task())

            # Close should drain queue
            await writer.close()

            # All messages should be processed
            assert writer.write_queue.qsize() == 0
```

**Validation**:
- [ ] All tests pass (init, write, task, close)
- [ ] Async tests use @pytest.mark.asyncio
- [ ] Mocks used appropriately (aiofiles.open, logging)
- [ ] Tests verify non-blocking behavior
- [ ] Tests verify error handling (logged, not raised)
- [ ] Tests verify cleanup (queue drain, task stop)

**Notes**:
- Mock aiofiles for unit tests (no real disk I/O)
- Use AsyncMock for async file operations
- Test both happy path and error scenarios
- Verify queue behavior directly (qsize, task_done)
- Task lifecycle tests: start, process, stop

---

### Subtask T023 – Write Integration Test for Full Workflow

**Purpose**: Verify end-to-end CLI workflow with output produces correct transcript file.

**Steps**:
1. Create `tests/integration/test_debate_output_integration.py`
2. Import necessary modules: pytest, document_debate_cli.py, DebateMessage
3. Test full workflow:
   - Create simple .docx test file (or use existing)
   - Run workflow with --output flag pointing to tmp_path
   - Verify output file created
   - Verify file contains all message types (topic, pro, con, judge)
   - Verify format matches spec: `[SPEAKER] ISO_TIMESTAMP\ncontent\n\n`
4. Test without --output:
   - Verify CLI works normally
   - Verify no output file created
5. Use tmp_path fixture for temporary files

**Files**:
- `tests/integration/test_debate_output_integration.py` (new file, ~80 lines)
- `test_data/simple.docx` (create minimal test docx, ~20 lines)

**Implementation**:
```python
import pytest
import asyncio
from pathlib import Path
from document_debate_cli import main as cli_main
from src.output.transcript_formatter import DebateMessage

@pytest.mark.asyncio
async def test_workflow_with_output_creates_transcript(tmp_path):
    """Running debate with --output creates complete transcript file."""
    # Create test document
    test_docx = tmp_path / "test_debate.docx"
    # Add minimal content (or use existing test file)

    output_file = tmp_path / "debate_transcript.txt"

    # Mock sys.argv for CLI
    import sys
    original_argv = sys.argv
    sys.argv = ["cli", "--docx", str(test_docx), "--output", str(output_file)]

    try:
        # Run CLI main function
        await cli_main()
    finally:
        sys.argv = original_argv

    # Verify output file exists
    assert output_file.exists()
    content = output_file.read_text()

    # Verify format
    assert "[MODERATOR]" in content or "[TOPIC]" in content  # Topic generation
    assert "[PRO]" in content  # PRO arguments
    assert "[CON]" in content  # CON arguments
    assert "[JUDGE]" in content  # Verdict

    # Verify message format
    for line in content.split("\n"):
            if line.startswith("["):
                # Should have timestamp on same line
                assert "T" in line  # ISO timestamp has T
                # Header line ends
                assert line.count("]") >= 2  # [SPEAKER] TIMESTAMP

    # Verify double newlines between messages
    assert "\n\n" in content

@pytest.mark.asyncio
async def test_workflow_without_output_no_file(tmp_path):
    """Running debate without --output doesn't create file."""
    test_docx = tmp_path / "test_debate.docx"

    import sys
    original_argv = sys.argv
    sys.argv = ["cli", "--docx", str(test_docx)]

    try:
        await cli_main()
    finally:
        sys.argv = original_argv

    # Verify no output file created
    output_files = list(tmp_path.glob("*.txt"))
    assert len(output_files) == 0  # No .txt files created
```

**Validation**:
- [ ] Integration test runs full workflow
- [ ] Output file created with --output flag
- [ ] No output file without --output flag
- [ ] All message types present in output
- [ ] Format matches specification
- [ ] Test is async and uses tmp_path

**Notes**:
- Integration test is slow (runs full debate) but necessary
- May need to mock LLM calls to speed up (or accept slow test)
- Verify both with and without --output flags
- Check for all speaker types in output

---

### Subtask T024 – Write Error Scenario Tests

**Purpose**: Verify writer handles error conditions gracefully without crashing.

**Steps**:
1. Add error scenario tests to `test_async_file_writer.py` or separate file
2. Test read-only path:
   - Try to create writer with read-only path
   - Verify enabled is False
   - Verify write_message() is no-op
3. Test disk full simulation:
   - Mock aiofiles to raise OSError("No space left")
   - Verify error logged
   - Verify writer continues (doesn't crash)
4. Test concurrent writes (race condition):
   - Multiple nodes write simultaneously
   - Verify all messages queued
   - Verify order preserved
5. Test special characters:
   - Unicode, emojis, quotes in content
   - Verify written correctly to file

**Files**:
- `tests/unit/output/test_async_file_writer.py` (extend, add ~40 lines)
- OR: `tests/unit/output/test_error_scenarios.py` (new file)

**Implementation**:
```python
# Add to test_async_file_writer.py or separate file

import pytest
from pathlib import Path
from src.output.async_file_writer import AsyncFileWriter
from src.output.transcript_formatter import DebateMessage

@pytest.mark.asyncio
async def test_readonly_path_disables_writer(tmp_path):
    """Unwritable path results in enabled=False."""
    # Create read-only directory
    readonly_dir = tmp_path / "readonly"
    readonly_dir.mkdir()
    readonly_dir.chmod(0o555)  # Read-only

    readonly_file = readonly_dir / "test.txt"

    writer = AsyncFileWriter(str(readonly_file))

    # Should be disabled
    assert writer.enabled == False

    # Writes should be no-ops
    msg = DebateMessage("PRO", "2025-02-14T12:00:00Z", "Test")
    writer.write_message(msg)
    assert writer.write_queue.qsize() == 0

@patch("aiofiles.aio.open")
async def test_disk_full_error_logged(mock_open):
    """Disk full errors are logged, not raised."""
    import logging

    mock_open.side_effect = OSError("No space left on device")

    with patch.object(logging.getLogger) as mock_logger:
        writer = AsyncFileWriter("/tmp/full.txt")
        writer.enabled = True

        # Start task
        asyncio.create_task(writer._writer_task())

        msg = DebateMessage("PRO", "2025-02-14T12:00:00Z", "Test")
        writer.write_message(msg)

        # Give time to process
        await asyncio.sleep(0.1)

        # Verify error was logged
        assert mock_logger.return_value.error.called

    # Task should still be running (not crashed)
    # Verify by checking if task is done (should not be)

@pytest.mark.asyncio
async def test_concurrent_writes_preserve_order(tmp_path):
    """Multiple simultaneous writes preserve order."""
    writer = AsyncFileWriter(str(tmp_path / "test.txt"))
    writer.enabled = True

    # Simulate concurrent writes (as if from multiple nodes)
    messages = [
        DebateMessage("PRO", "2025-02-14T12:00:00Z", "Message 1"),
        DebateMessage("CON", "2025-02-14T12:00:01Z", "Message 2"),
        DebateMessage("PRO", "2025-02-14T12:00:02Z", "Message 3"),
    ]

    # Write all rapidly (simulating concurrent nodes)
    for msg in messages:
        writer.write_message(msg)

    # Start task and wait
    task = asyncio.create_task(writer._writer_task())
    await asyncio.sleep(0.2)  # Let task process
    await writer.close()

    # Verify all written in order
    content = (tmp_path / "test.txt").read_text()
    lines = [l for l in content.split("\n") if l.strip()]

    # Should preserve order (FIFO queue)
    assert "Message 1" in content
    assert "Message 2" in content
    assert "Message 3" in content
    # Check order in file
    msg1_idx = content.index("Message 1")
    msg2_idx = content.index("Message 2")
    msg3_idx = content.index("Message 3")
    assert msg1_idx < msg2_idx < msg3_idx

@pytest.mark.asyncio
async def test_unicode_and_special_characters(tmp_path):
    """Unicode, emojis, and special chars written correctly."""
    writer = AsyncFileWriter(str(tmp_path / "test.txt"))
    writer.enabled = True

    special_messages = [
        DebateMessage("PRO", "2025-02-14T12:00:00Z", "Unicode: 你好"),
        DebateMessage("CON", "2025-02-14T12:01:00Z", "Emoji: 😀 🎉"),
        DebateMessage("JUDGE", "2025-02-14T12:02:00Z", "Quotes: \"test\" 'test'"),
        DebateMessage("MODERATOR", "2025-02-14T12:03:00Z", "Brackets: [test] (test)"),
    ]

    for msg in special_messages:
        writer.write_message(msg)

    task = asyncio.create_task(writer._writer_task())
    await asyncio.sleep(0.2)
    await writer.close()

    content = (tmp_path / "test.txt").read_text()
    assert "Unicode: 你好" in content
    assert "Emoji: 😀 🎉" in content
    assert "Quotes: \"test\" 'test'" in content
    assert "[test] (test)" in content
```

**Validation**:
- [ ] Read-only path test disables writer
- [ ] Disk full error is logged (not raised)
- [ ] Concurrent writes preserve order
- [ ] Unicode and special characters work
- [ ] All error scenarios pass without crashes

**Notes**:
- Error scenario tests are crucial for reliability (FR-005, FR-006)
- Mock conditions rather than requiring real disk full state
- Concurrent write test verifies queue FIFO behavior
- Unicode test prevents encoding issues

---

## Test Strategy

**Running All Tests**:

```bash
# Run unit tests only
pytest tests/unit/output/ -v

# Run integration tests only
pytest tests/integration/ -v

# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src/output --cov-report=html
```

**Fixtures** (defined in T020):
- `sample_message` - Single DebateMessage for tests
- `sample_messages` - List of DebateMessages
- `tmp_path` - pytest builtin for temp directories

**Coverage Goals**:
- src/output module: >80% coverage
- All branches in write_message() covered
- All exception paths covered
- Async task lifecycle covered

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|-------|---------|------------|
| **Integration test is slow** | Long test runtimes | Accept for verification, may mock LLM to speed up |
| **aiofiles mocking complexity** | Tests don't verify real behavior | Use integration test with real files for confidence |
| **Async test flakiness** | Tests don't actually test async behavior | Use @pytest.mark.asyncio, await asyncio.sleep() |
| **Fixture conflicts** | Tests fail to find fixtures | Define fixtures clearly in conftest.py |

**Monitoring Considerations**:
- Track test execution time
- Monitor coverage percentage
- Identify failing tests early

---

## Review Guidance

**Acceptance Checkpoints for Reviewers**:

1. **Test Structure**:
   - [ ] `tests/unit/output/` directory exists
   - [ ] `__init__.py` present in test directories
   - [ ] Test files follow naming: `test_*.py`

2. **Unit Tests**:
   - [ ] test_transcript_formatter.py exists
   - [ ] Tests cover format_message() (basic, multi-line, special chars)
   - [ ] Tests cover validate_path() (valid, invalid, errors)
   - [ ] test_async_file_writer.py exists
   - [ ] Tests cover __init__, write_message, _writer_task, close
   - [ ] Tests use mocks for aiofiles (no real I/O)

3. **Async Tests**:
   - [ ] Async tests use @pytest.mark.asyncio
   - [ ] Test functions are async (def test... async)
   - [ ] asyncio.sleep() used for timing
   - [ ] No race conditions in tests

4. **Error Scenarios**:
   - [ ] Read-only path tested
   - [ ] Write failures tested (mocked)
   - [ ] Concurrent writes tested
   - [ ] Unicode/special chars tested

5. **Integration Test**:
   - [ ] test_debate_output_integration.py exists
   - [ ] Full workflow run with --output flag
   - [ ] Output file content verified
   - [ ] Test without --output flag also covered

6. **Coverage**:
   - [ ] Unit tests cover main paths
   - [ ] Error handling covered
   - [ ] Edge cases tested

**Failure Criteria** (return for rework if any true):
- ❌ Tests use real file I/O in unit tests (should mock)
- ❌ Integration test doesn't verify actual output file
- ❌ Async tests not marked with @pytest.mark.asyncio
- ❌ Error scenarios not tested
- ❌ Tests pass but code doesn't work (integration mismatch)
- ❌ Coverage <50% for output module

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
