---
work_package_id: "WP02"
subtasks:
  - "T009"
  - "T010"
  - "T011"
  - "T012"
  - "T013"
title: "CLI Integration"
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

# Work Package Prompt: WP02 – CLI Integration

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

**Primary Objective**: Integrate the AsyncFileWriter into `document_debate_cli.py` by adding `--output` argument, creating writer instance, and ensuring proper cleanup.

**Success Criteria**:
- [ ] CLI accepts `--output <filepath>` argument (optional)
- [ ] `aiofiles>=24.1.0` added to `requirements.txt`
- [ ] AsyncFileWriter created when `--output` provided, None when omitted
- [ ] Writer creation failures logged but don't crash CLI
- [ ] Writer passed to workflow.run() as parameter
- [ ] Writer.close() called in finally block (always executed)
- [ ] CLI runs normally without `--output` (backward compatible)
- [ ] Manual test: `python document_debate_cli.py --docx test.docx --output out.txt` creates file

---

## Context & Constraints

**Prerequisites**:
- **WP01** must be complete (AsyncFileWriter, TranscriptFormatter, DebateMessage must exist)

**Related Documents**:
- [Spec FR-001](../spec.md#functional-requirements) - `--output` argument requirement
- [Spec FR-008](../spec.md#functional-requirements) - Backward compatibility requirement
- [Quickstart](../quickstart.md) - CLI integration examples
- [document_debate_cli.py](../../document_debate_cli.py) - Existing CLI code to modify

**Key Constraints**:
- Writer creation MUST NOT crash CLI if path is invalid (log error, set writer to None)
- `--output` is optional - CLI must work exactly as before when omitted
- Writer must be cleaned up in finally block (guaranteed execution)
- Pass writer to workflow, don't access global state
- Use existing async main() structure (already using asyncio.run())

**Architecture Decisions**:
- Writer created in main() after argparse, before workflow.run()
- Pass writer as parameter to workflow.run() (not in state dict)
- Use try/finally for cleanup (not with/except, to avoid catching unrelated errors)
- Log validation failures but continue CLI execution

---

## Subtasks & Detailed Guidance

### Subtask T009 – Add --output Argument to Argparse

**Purpose**: Enable users to specify output file path via CLI flag.

**Steps**:
1. Open `document_debate_cli.py`
2. Locate argparse ArgumentParser creation (around line 80-90)
3. Add new argument: `--output` with help text
4. Place after existing `--text` argument (around line 88-89)
5. Ensure argument is optional (no required=True)

**Files**:
- `document_debate_cli.py` (modify, add ~4 lines)

**Implementation**:
```python
# In main() function, after parser setup:

parser.add_argument(
    "--output",
    help="Path to file for recording debate transcript (optional)"
)
```

**Full context** (where it fits):
```python
parser = argparse.ArgumentParser(
    description="Run an AI debate based on a document"
)
parser.add_argument(
    "--docx",
    help="Path to .docx file for debate analysis"
)
parser.add_argument(
    "--text",
    help="Direct text input (alternative to --docx)"
)
# NEW: Add --output argument
parser.add_argument(
    "--output",
    help="Path to file for recording debate transcript (optional)"
)

args = parser.parse_args()
```

**Validation**:
- [ ] `python document_debate_cli.py --help` shows `--output` in help text
- [ ] Argument is optional (can run CLI without it)
- [ ] Help text is clear and concise
- [ ] Argument takes a value (not store_true)

**Notes**:
- Keep it simple - just basic argparse configuration
- No validation here - that happens in T011 when creating writer
- Use `--output` name (not `--output-file` or other variant)

---

### Subtask T010 – Add aiofiles Dependency to requirements.txt

**Purpose**: Ensure aiofiles library is installed for async file I/O.

**Steps**:
1. Open `requirements.txt` at repository root
2. Add line: `aiofiles>=24.1.0` (or `^24.1.0` for exact)
3. Place after existing dependencies, maintain alphabetical/order
4. Save file

**Files**:
- `requirements.txt` (modify, add 1 line)

**Implementation**:
```text
# Add to requirements.txt (alphabetical placement):
aiofiles>=24.1.0
```

**Full context** (where it fits):
```text
langchain_community==0.3.20
langchain_core==0.3.49
langchain_openai==0.3.11
langgraph==0.3.21
openai==1.69.0
pydantic==2.11.1
pytest==8.3.5
python-dotenv==1.1.0
python-docx==1.1.2
rich==14.0.0
typing_extensions>=4.0.0
aiofiles>=24.1.0  # NEW: Add this line
```

**Validation**:
- [ ] `aiofiles>=24.1.0` appears in requirements.txt
- [ ] Version specification uses `>=` or `^` (not unpinned)
- [ ] Line is properly formatted (no syntax errors)
- [ ] After running `pip install -r requirements.txt`, `import aiofiles` works

**Notes**:
- Use `>=24.1.0` (not exact `==24.1.0`) for flexibility
- Could use `^24.1.0` if using poetry (but this uses requirements.txt)
- This is the only new external dependency for the feature

---

### Subtask T011 – Create AsyncFileWriter Instance in CLI main()

**Purpose**: Instantiate the writer when `--output` is provided, handle init failures gracefully.

**Steps**:
1. In `document_debate_cli.py` main() function, after argparse
2. Import AsyncFileWriter and TranscriptFormatter at top of file
3. After loading docx/text, before workflow.run():
   - Check if `args.output` is provided
   - If yes: create `AsyncFileWriter(args.output)` via asyncio (need to handle this)
   - If no: set `writer = None`
4. Handle validation failure: if `writer.enabled == False`, log warning, set `writer = None`
5. Use ` TranscriptFormatter.validate_path()` for async validation (need to await in existing loop)

**Files**:
- `document_debate_cli.py` (modify, add ~25 lines including imports)

**Implementation**:
```python
# At top of file, add imports:
from src.output.async_file_writer import AsyncFileWriter
from src.output.transcript_formatter import TranscriptFormatter

# In main() function, after args.parse_args():

# Existing code loads document or text
# ... doc_text = read_docx_file(args.docx) or args.text ...

# NEW: Create output writer if --output provided
writer = None
if args.output:
    # Need to validate path async - but we're already in async main()
    # Use TranscriptFormatter.validate_path() then create writer
    # Actually: let AsyncFileWriter handle validation internally
    # Create writer (it's not async to create, only its methods are)
    writer = AsyncFileWriter(args.output)

    # Validate path is writable
    # Note: validate_path is async, need to handle in existing loop
    # For simplicity: writer validates in __init__ or we call validate here
    # Let's call validate_path synchronously since we can't easily await here yet
    # Actually: best to pass validation flag to init or check writer.enabled
    if not writer.enabled:
        logger.warning(f"Output file could not be initialized: {args.output}")
        writer = None  # Don't use failed writer

# Continue with existing workflow code...
```

**Refined Implementation** (better pattern - handle in existing async context):
The existing main() already has `asyncio.run(main())` at the end, so the inner `main()` is async. Let's place writer creation INSIDE the async main() function:

```python
async def main():
    """Main entry point for the document debate CLI."""
    setup_logging()
    validate_env()
    logger = logging.getLogger("main")

    try:
        # ... existing parser setup ...
        args = parser.parse_args()

        # ... existing docx/text loading ...
        # ... base_state setup ...

        # NEW: Create output writer (inside async main)
        writer = None
        if args.output:
            # Import here to avoid top-level import issues
            from src.output.async_file_writer import AsyncFileWriter

            writer = AsyncFileWriter(args.output)

            # Validate path is writable (async)
            from src.output.transcript_formatter import TranscriptFormatter
            is_valid = await TranscriptFormatter.validate_path(args.output)

            if not is_valid:
                logger.warning(f"Output file path is not writable: {args.output}")
                writer = None
            else:
                writer.enabled = True
                logger.info(f"Output will be recorded to: {args.output}")

        # Continue with workflow...
        workflow = DocumentDebateWorkflow()
        workflow_result = await workflow.run(
            initial_state=initial_state,
            output_writer=writer  # T012 adds this
        )

        # ... rest of existing code ...
    finally:
        # T013 adds cleanup here
        pass
```

**Validation**:
- [ ] Writer created only when `args.output` has value
- [ ] If validation fails, `writer` is set to None (not crashed)
- [ ] Info log confirms output file path when writer created
- [ ] Warning log when validation fails
- [ ] Code continues even if writer creation fails

**Notes**:
- Must be inside async main() to await validate_path()
- Or: simplify by having writer validate in its own async initializer
- Key point: Writer = None is acceptable and expected (backward compatible)
- Import at module level to avoid import errors

---

### Subtask T012 – Pass output_writer to workflow.run()

**Purpose**: Make writer available to workflow and nodes for message writing.

**Steps**:
1. Locate call to `workflow.run(initial_state=initial_state)` in main()
2. Add parameter: `output_writer=writer`
3. Note: This requires modifying DocumentDebateWorkflow.run() signature (done in WP03 T014)
4. For now, just pass the parameter - workflow will be updated next

**Files**:
- `document_debate_cli.py` (modify, 1 line change)

**Implementation**:
```python
# Existing code (before this task):
workflow_result = await workflow.run(initial_state=initial_state)

# New code (after this task):
workflow_result = await workflow.run(
    initial_state=initial_state,
    output_writer=writer
)
```

**Validation**:
- [ ] `output_writer=writer` passed to workflow.run()
- [ ] If writer is None, still passed (workflow handles None case)
- [ ] No other changes to this line (just adding parameter)

**Notes**:
- DocumentDebateWorkflow.run() will be modified in WP03 to accept this parameter
- It's OK that this won't work yet - WP03 will implement the workflow side
- For now, this just sets up the integration

---

### Subtask T013 – Add Writer Cleanup in finally Block

**Purpose**: Ensure writer is properly closed and queue is drained before program exit.

**Steps**:
1. In main() function, wrap existing workflow execution in try/finally
2. In finally block: check if writer is not None
3. If writer exists: `await writer.close()` to drain queue and stop task
4. Use existing try/except structure (add finally to it)

**Files**:
- `document_debate_cli.py` (modify, add ~5 lines)

**Implementation**:
```python
# Existing code structure:
try:
    logger.info("[bold green]Starting document debate workflow...[/]")
    # ... workflow execution ...
    logger.info("[bold green]Workflow completed successfully | Status: [bold]SUCCESS[/][/]")
except Exception as e:
    logger.error(f"Workflow failed: %s", str(e))
    raise
# NEW: Add finally block
finally:
    if writer:
        logger.info("Closing output writer...")
        await writer.close()
```

**Full Context**:
```python
async def main():
    setup_logging()
    validate_env()
    logger = logging.getLogger("main")

    # ... argparse and setup ...

    writer = None
    if args.output:
        writer = AsyncFileWriter(args.output)
        # ... validation ...

    try:
        logger.info("[bold green]Starting document debate workflow...[/]")

        workflow = DocumentDebateWorkflow()
        workflow_result = await workflow.run(
            initial_state=initial_state,
            output_writer=writer
        )

        # ... existing verdict display ...
        logger.info("[bold green]Workflow completed successfully...[/]")

    except Exception as e:
        logger.error(f"Workflow failed: %s", str(e))
        raise
    finally:
        # NEW: Cleanup writer
        if writer:
            logger.info("Flushing and closing output writer...")
            await writer.close()
```

**Validation**:
- [ ] `finally:` block added after existing except block
- [ ] `if writer:` check prevents calling close() on None
- [ ] `await writer.close()` called to drain queue
- [ ] Works even when workflow crashes (finally always executes)
- [ ] Log message indicates cleanup is happening

**Notes**:
- finally is CRITICAL - ensures cleanup even on crashes or keyboard interrupts
- No need to handle exceptions from close() - it does its own error handling
- Log message helps debugging (shows cleanup in action)
- Writer may be None (no --output flag) - must check before calling close()

**Risks**:
- If writer.close() hangs, program exit is delayed (has timeout internally)
- Forgetting finally could leave writes incomplete or task orphaned

---

## Test Strategy

**Manual Integration Testing** (before WP04 tests are written):

1. **Test without --output** (backward compatibility):
```bash
python document_debate_cli.py --docx test_data/simple.docx
# Should work exactly as before
# No output file should be created
```

2. **Test with --output**:
```bash
python document_debate_cli.py --docx test_data/simple.docx --output /tmp/debate.txt
# Should run successfully
# Check /tmp/debate.txt contains formatted messages
```

3. **Test with invalid --output**:
```bash
python document_debate_cli.py --docx test_data/simple.docx --output /read-only/path/debate.txt
# Should log warning but continue debate
# CLI should complete successfully despite unwritable path
```

4. **Verify --help**:
```bash
python document_debate_cli.py --help | grep output
# Should show: --output  Path to file for recording debate transcript (optional)
```

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|-------|---------|------------|
| **Writer validation in wrong context** | Can't await validate_path() | Place writer creation inside async main(), not at module level |
| **Forgetting finally block** | Writer never closed, queue orphaned | MUST add finally block, test with KeyboardInterrupt |
| **Writer conflicts with existing code** | Unintended side effects | Minimal changes, only additive, existing code paths unchanged |
| **requirements.txt sync** | aiofiles not installed | Update requirements.txt in same WP (T010) |
| **Import order issues** | Circular imports or load errors | Import writer classes at module level, create instance in main() |

**Monitoring Considerations**:
- Log when writer is created with file path
- Log warning when validation fails
- Log when writer is closed (finally block execution)
- Track time spent in writer.close() (should be <5 seconds normally)

---

## Review Guidance

**Acceptance Checkpoints for Reviewers**:

1. **CLI Argument**:
   - [ ] `--output` appears in help text
   - [ ] Argument is optional (no required=True)
   - [ ] Help text is clear

2. **Requirements**:
   - [ ] `aiofiles>=24.1.0` added to requirements.txt
   - [ ] Version format consistent with other entries

3. **Writer Creation**:
   - [ ] Created only when args.output is truthy
   - [ ] Validation failure sets writer to None (doesn't crash)
   - [ ] Async validation properly awaited
   - [ ] Info/warning logs present for debugging

4. **Integration**:
   - [ ] output_writer passed to workflow.run()
   - [ ] Writer available to workflow (will be used in WP03)

5. **Cleanup**:
   - [ ] finally block exists
   - [ ] writer.close() called with await
   - [ ] None check prevents errors

6. **Backward Compatibility**:
   - [ ] CLI works without --output flag
   - [ ] No changes to existing behavior when flag omitted

**Failure Criteria** (return for rework if any true):
- ❌ CLI crashes when --output points to invalid path
- ❌ writer.close() not called (missing finally block)
- ❌ --output is required (mandatory flag)
- ❌ Workflow execution changes when writer is None
- ❌ Import errors at runtime

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
