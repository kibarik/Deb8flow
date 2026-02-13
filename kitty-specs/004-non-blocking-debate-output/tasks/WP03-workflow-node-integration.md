---
work_package_id: "WP03"
subtasks:
  - "T014"
  - "T015"
  - "T016"
  - "T017"
  - "T018"
  - "T019"
title: "Workflow Node Integration"
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

# Work Package Prompt: WP03 – Workflow Node Integration

## ⚠️ IMPORTANT: Review Feedback Status

**Read this first if you are implementing this task!**

- **Has review feedback?**: Check `review_status` field above. If it says `has_feedback`, scroll to **Review Feedback** section immediately (right below this notice).
- **You must address all feedback** before your work is complete. Feedback items are your implementation TODO list.
- **Mark as acknowledged**: When you understand the feedback and begin addressing it, use `Edit` to update `review_status: acknowledged` in frontmatter.
- **Report progress**: As you address each feedback item, update Activity Log explaining what you changed.

---

## Review Feedback

> **Populated by `/spec-kitty.review`** – Reviewers add detailed feedback here when work needs changes. Implementation must address every item listed below before returning for re-review.

*[This section is empty initially. Reviewers will populate it if work is returned from review. If you see feedback here, treat each item as a must-do before completion.]*

---

## Objectives & Success Criteria

**Primary Objective**: Wire the `output_writer` into DocumentDebateWorkflow and all debate nodes so messages are written to the output file during debates.

**Success Criteria**:
- [ ] `DocumentDebateWorkflow.run()` accepts optional `output_writer` parameter
- [ ] `output_writer` is accessible to nodes (via state or function parameter)
- [ ] document_topic_node writes topic messages to output_writer
- [ ] pro_debater_node writes PRO messages to output_writer
- [ ] con_debater_node writes CON messages to output_writer
- [ ] judge_node writes JUDGE messages to output_writer
- [ ] debate_moderator_node writes messages (if applicable)
- [ ] All nodes handle `output_writer=None` gracefully (no errors)
- [ ] Speaker labels match node type (PRO/CON/JUDGE/MODERATOR)
- [ ] Timestamps use UTC ISO 8601 format
- [ ] Integration test: running debate with --output produces complete transcript

---

## Context & Constraints

**Prerequisites**:
- **WP01** must be complete (AsyncFileWriter, DebateMessage exist)
- **WP02** must be complete (CLI passes writer to workflow)

**Related Documents**:
- [Spec FR-002](../spec.md#functional-requirements) - Write each message to output file
- [Spec FR-003](../spec.md#functional-requirements) - Message includes speaker, timestamp, content
- [Data Model](../data-model.md) - DebateMessage structure
- [Quickstart](../quickstart.md) - Node integration examples
- [workflow/document_debate_workflow.py](../../workflow/document_debate_workflow.py) - Main workflow
- [nodes/document_topic_node.py](../../nodes/document_topic_node.py) - Topic generation node
- [nodes/pro_debater_node.py](../../nodes/pro_debater_node.py) - PRO debater node
- [nodes/con_debater_node.py](../../nodes/con_debater_node.py) - CON debater node
- [nodes/judge_node.py](../../nodes/judge_node.py) - Judge node
- [nodes/debate_moderator_node.py](../../nodes/debate_moderator_node.py) - Moderator node

**Key Constraints**:
- Writer MUST be optional - all code must handle `None` value
- DO NOT block workflow for file writes (use non-blocking write_message())
- Extract correct speaker label from each node context
- Use UTC timezone for timestamps
- Minimal changes to node logic (just add write call, don't refactor)
- Preserve existing node behavior when writer is None

**Architecture Decisions**:
- Pass `output_writer` through function parameters (not state dict)
- Each node checks `if output_writer and output_writer.enabled:` before writing
- Speaker labels derived from node class/function name
- Use `datetime.now(timezone.utc).isoformat()` for timestamps

---

## Subtasks & Detailed Guidance

### Subtask T014 – Modify DocumentDebateWorkflow.run() Signature

**Purpose**: Enable workflow to accept and propagate output_writer parameter.

**Steps**:
1. Open `workflow/document_debate_workflow.py`
2. Locate `run()` method definition (around line 83-110)
3. Add parameter: `output_writer=None` to method signature
4. Store output_writer for potential use (though nodes will receive it via parameters)
5. Document that parameter is optional in docstring

**Files**:
- `workflow/document_debate_workflow.py` (modify, ~5 lines)

**Implementation**:
```python
# In DocumentDebateWorkflow class:

async def run(self, initial_state: dict = None, output_writer=None):
    """
    Run the document debate workflow.

    Args:
        initial_state: Optional initial state dict. Must contain 'document_input'
                      if not using default empty state.
        output_writer: Optional AsyncFileWriter for recording debate messages.

    Returns:
        Final debate state with messages and verdict

    Example:
        workflow = DocumentDebateWorkflow()
        result = await workflow.run(
            initial_state={
                "document_input": "path/to/document.docx"
            },
            output_writer=writer  # Optional file writer
        )
    """
    # ... existing implementation ...
```

**Note**: The workflow itself doesn't need to use output_writer - it just needs to pass it along. Individual nodes will use it. If nodes are invoked via LangGraph state, you may need to put output_writer in state instead.

**Alternative Approach** (if using state-based node invocation):
If LangGraph nodes only receive state dict (not function parameters), put output_writer in state:

```python
# In run() method, before invoking graph:
if output_writer:
    initial_state = initial_state or {}
    initial_state["output_writer"] = output_writer
```

Then in T015-T019, nodes access via `state.get("output_writer")`.

**Validation**:
- [ ] Method signature includes `output_writer=None`
- [ ] Docstring documents the parameter
- [ ] Parameter is passed along (to state or nodes, depending on approach)
- [ ] Code still works when output_writer is None (no errors)

**Notes**:
- Decide: pass as parameter vs. put in state dict
- Parameter approach is cleaner if nodes accept parameters
- State approach works better if nodes only receive state dict
- Check existing node signatures to determine which approach fits

**For this codebase**: Nodes are invoked via LangGraph StateGraph, which passes state dict to nodes. So put output_writer in initial_state:

```python
async def run(self, initial_state: dict = None, output_writer=None):
    workflow = self._initialize_workflow()
    graph = workflow.compile()

    if initial_state is None:
        initial_state = {"document_input": ""}

    # NEW: Add output_writer to state for nodes to access
    if output_writer is not None:
        initial_state["output_writer"] = output_writer

    final_state = await graph.ainvoke(initial_state, config={"recursion_limit": 50})
    return final_state
```

---

### Subtask T015 – Update document_topic_node.py to Write Messages

**Purpose**: Record topic generation messages to output file.

**Steps**:
1. Open `nodes/document_topic_node.py`
2. Import DebateMessage and datetime at top
3. In node's `__call__` method, after generating topic:
   - Extract output_writer from state: `state.get("output_writer")`
   - Check if writer is not None and writer.enabled is True
   - Create DebateMessage with speaker="MODERATOR" (or "TOPIC")
   - Get UTC timestamp: `datetime.now(timezone.utc).isoformat()`
   - Extract topic text from result
   - Call `writer.write_message(message)`
4. Don't modify existing return behavior

**Files**:
- `nodes/document_topic_node.py` (modify, add ~15 lines)

**Implementation**:
```python
# Add imports at top:
from datetime import datetime, timezone
from src.output.transcript_formatter import DebateMessage

# In DocumentTopicNode.__call__ method:

def __call__(self, state: DebateState) -> dict:
    # ... existing LLM call and topic generation ...

    # NEW: Write to output file
    output_writer = state.get("output_writer")
    if output_writer and output_writer.enabled:
        try:
            # Extract topic from state or LLM response
            topic_text = state.get("debate_topic", "")
            if topic_text:
                message = DebateMessage(
                    speaker="MODERATOR",  # or "TOPIC" - choose one
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    content=topic_text
                )
                output_writer.write_message(message)
        except Exception as e:
            # Log but don't fail the node
            pass  # Writer logs its own errors

    # ... existing return statement ...
    return {"debate_topic": generated_topic, "messages": [...]}
```

**Validation**:
- [ ] output_writer retrieved from state dict
- [ ] None and enabled checks before using writer
- [ ] DebateMessage created with correct fields
- [ ] Speaker label is appropriate for topic node
- [ ] Timestamp is UTC ISO format
- [ ] write_message() called (not awaited - it's non-blocking)
- [ ] Node return value unchanged

**Notes**:
- Speaker label: "MODERATOR" makes sense for topic generation
- Alternative: "TOPIC" or "SYSTEM" - choose consistently
- Wrap write in try/except to ensure node never fails due to output
- Don't extract content from state["messages"] - use the generated topic directly

---

### Subtask T016 – Update pro_debater_node.py to Write Messages

**Purpose**: Record PRO debater messages to output file.

**Steps**:
1. Open `nodes/pro_debater_node.py`
2. Add imports: `DebateMessage`, `datetime`, `timezone` (if not present)
3. In `__call__` method, after generating argument:
   - Get output_writer from state
   - Check writer is not None and enabled
   - Create DebateMessage with speaker="PRO"
   - Use UTC timestamp
   - Extract argument content from LLM response or state
   - Call writer.write_message()
4. Preserve all existing functionality

**Files**:
- `nodes/pro_debater_node.py` (modify, add ~15 lines)

**Implementation**:
```python
# Add imports (if not already there):
from datetime import datetime, timezone
from src.output.transcript_formatter import DebateMessage

# In ProDebaterNode.__call__ method:

def __call__(self, state: DebateState) -> dict:
    # ... existing LLM call to generate PRO argument ...

    # NEW: Write to output file
    output_writer = state.get("output_writer")
    if output_writer and output_writer.enabled:
        try:
            # Extract argument text from LLM response
            # Depending on implementation, might be in response or need to extract
            argument_text = llm_response.content  # Or however you access it
            if argument_text:
                message = DebateMessage(
                    speaker="PRO",
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    content=argument_text
                )
                output_writer.write_message(message)
        except Exception:
            # Don't let output failures crash the node
            pass

    # ... existing return with new message added to state ...
    return {"messages": state["messages"] + [new_message]}
```

**Validation**:
- [ ] Speaker is "PRO" (uppercase, exact match)
- [ ] Timestamp uses UTC timezone
- [ ] Message content extracted from node's output
- [ ] Writer check prevents errors when not enabled
- [ ] Existing node behavior unchanged

**Notes**:
- Speaker must be exactly "PRO" to match transcript format
- Try/except ensures output bugs don't crash debates
- Content extraction depends on how node stores/accesses LLM response

---

### Subtask T017 – Update con_debater_node.py to Write Messages

**Purpose**: Record CON debater messages to output file.

**Steps**:
1. Open `nodes/con_debater_node.py`
2. Add imports for DebateMessage and datetime
3. In `__call__` method:
   - Get output_writer from state
   - Check writer availability
   - Create DebateMessage with speaker="CON"
   - Add timestamp and content
   - Call writer.write_message()
4. Ensure existing behavior preserved

**Files**:
- `nodes/con_debater_node.py` (modify, add ~15 lines)

**Implementation**:
```python
from datetime import datetime, timezone
from src.output.transcript_formatter import DebateMessage

# In ConDebaterNode.__call__:

def __call__(self, state: DebateState) -> dict:
    # ... existing CON argument generation ...

    output_writer = state.get("output_writer")
    if output_writer and output_writer.enabled:
        try:
            argument_text = llm_response.content  # Or appropriate extraction
            if argument_text:
                message = DebateMessage(
                    speaker="CON",
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    content=argument_text
                )
                output_writer.write_message(message)
        except Exception:
            pass

    # ... return state update ...
    return {"messages": [...]}
```

**Validation**:
- [ ] Speaker is "CON"
- [ ] UTC timestamp used
- [ ] Message written to output
- [ ] No impact on existing functionality

**Notes**:
- Mirror T016 structure but with "CON" speaker
- Same error handling pattern
- Content extraction method must match node's implementation

---

### Subtask T018 – Update judge_node.py to Write Messages

**Purpose**: Record judge verdict messages to output file.

**Steps**:
1. Open `nodes/judge_node.py`
2. Import DebateMessage, datetime if needed
3. In `__call__` method, after verdict generation:
   - Access output_writer from state
   - Validate writer is available
   - Create DebateMessage with speaker="JUDGE"
   - Use current time (UTC)
   - Include verdict content in message
   - Write to output
4. Maintain existing judge behavior

**Files**:
- `nodes/judge_node.py` (modify, add ~15 lines)

**Implementation**:
```python
from datetime import datetime, timezone
from src.output.transcript_formatter import DebateMessage

# In JudgeNode.__call__:

def __call__(self, state: DebateState) -> dict:
    # ... existing verdict generation ...

    output_writer = state.get("output_writer")
    if output_writer and output_writer.enabled:
        try:
            verdict_text = judge_response.content  # Extract appropriately
            if verdict_text:
                message = DebateMessage(
                    speaker="JUDGE",
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    content=verdict_text
                )
                output_writer.write_message(message)
        except Exception:
            pass

    # ... existing return with verdict ...
    return {"verdict": verdict, "messages": [...]}
```

**Validation**:
- [ ] Speaker is "JUDGE"
- [ ] Verdict content written to output
- [ ] UTC timestamp format
- [ ] Writer errors don't affect judge operation

**Notes**:
- Judge messages often include "WINNER: PRO" or similar - include this in content
- Verdict format may differ from PRO/CON - adapt extraction accordingly
- Judge is typically last message - ensure writer is still active (close() not called yet)

---

### Subtask T019 – Update debate_moderator_node.py to Write Messages

**Purpose**: Record moderator messages to output file (if applicable).

**Steps**:
1. Open `nodes/debate_moderator_node.py`
2. Check if node generates messages (some moderators just route, don't generate content)
3. If node generates messages:
   - Add imports
   - In `__call__`: get output_writer, check availability
   - Create DebateMessage with speaker="MODERATOR"
   - Add timestamp and content
   - Write to output
4. If node doesn't generate messages: Add comment noting this

**Files**:
- `nodes/debate_moderator_node.py` (modify, add ~15 lines OR add comment)

**Implementation** (if node generates messages):
```python
from datetime import datetime, timezone
from src.output.transcript_formatter import DebateMessage

# In DebateModeratorNode.__call__:

def __call__(self, state: DebateState) -> dict:
    # ... existing moderation logic ...

    # If this node generates messages:
    output_writer = state.get("output_writer")
    if output_writer and output_writer.enabled:
        try:
            # If moderator generates summary/announcement
            moderator_text = generated_content  # If applicable
            if moderator_text:
                message = DebateMessage(
                    speaker="MODERATOR",
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    content=moderator_text
                )
                output_writer.write_message(message)
        except Exception:
            pass

    # ... existing return ...
```

**Alternative** (if node only routes):
```python
# In DebateModeratorNode.__call__:

def __call__(self, state: DebateState) -> dict:
    # ... existing routing logic ...

    # NOTE: This node only routes between other nodes,
    # it doesn't generate messages. No output recording needed.
    # If this changes in future, add DebateMessage writing here.

    return {"next": "pro_debater_node"}  # Or whatever the routing is
```

**Validation**:
- [ ] If node generates messages: they are written to output
- [ ] If node doesn't generate: comment added for clarity
- [ ] Speaker is "MODERATOR" when applicable
- [ ] No changes to existing node functionality

**Notes**:
- Some moderator nodes only control flow (no message content)
- If this is the case, just add a comment for future maintainers
- Only add full write logic if node actually generates output

---

## Test Strategy

**Manual Integration Test** (run after completing all subtasks):

1. **Setup**:
```bash
# Create test document
echo "Test debate content" > /tmp/test.docx

# Run CLI with output
python document_debate_cli.py --docx /tmp/test.docx --output /tmp/debate_transcript.txt
```

2. **Verify Output File**:
```bash
cat /tmp/debate_transcript.txt

# Should contain:
# [MODERATOR] 2025-02-14T... (topic)
# [PRO] 2025-02-14T... (pro argument)
# [CON] 2025-02-14T... (con argument)
# [JUDGE] 2025-02-14T... (verdict)
```

3. **Verify Format**:
```
# Each message should be:
[SPEAKER] ISO8601_TIMESTAMP
<content line 1>
<content line 2>
...

# Double newline between messages
```

4. **Verify Non-Blocking**:
- Debate should complete in similar time with/without --output
- No perceptible pause between message generation and terminal display

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|-------|---------|------------|
| **output_writer not in state** | Nodes can't access it | Ensure T014 puts it in initial_state dict |
| **Nodes have different signatures** | Can't add parameter uniformly | Use state.get("output_writer") pattern consistently |
| **Speaker label inconsistency** | Unclear transcript | Use exact strings: "PRO", "CON", "JUDGE", "MODERATOR" |
| **Content extraction varies** | Empty or wrong content | Extract from appropriate source per node (response, state, etc.) |
| **Timestamp timezone issues** | Non-UTC or wrong format | Always use datetime.now(timezone.utc).isoformat() |
| **Writer becomes disabled** | Later messages lost | Each node checks enabled flag independently |

**Monitoring Considerations**:
- Each node should log when it skips writing (writer=None or disabled)
- Track number of messages written vs. expected
- Monitor for any exceptions in node (shouldn't crash due to output)

---

## Review Guidance

**Acceptance Checkpoints for Reviewers**:

1. **Workflow Changes**:
   - [ ] `run()` method accepts `output_writer` parameter
   - [ ] output_writer added to state for node access
   - [ ] Backward compatible (works when None)

2. **Node Integration** (for each of T015-T019):
   - [ ] output_writer retrieved via `state.get("output_writer")`
   - [ ] Writer checked for None and enabled before use
   - [ ] DebateMessage created with correct speaker label
   - [ ] UTC timestamp generated
   - [ ] write_message() called (not awaited)
   - [ ] Try/except prevents crashes

3. **Speaker Labels**:
   - [ ] PRO node uses "PRO"
   - [ ] CON node uses "CON"
   - [ ] Judge uses "JUDGE"
   - [ ] Moderator uses "MODERATOR" (if applicable)

4. **No Behavior Changes**:
   - [ ] All nodes return same values as before
   - [ ] Node logic unchanged (output is additive)
   - [ ] Errors in output don't affect node results

5. **Integration**:
   - [ ] Manual test produces complete transcript
   - [ ] Format matches spec: `[SPEAKER] ISO_TIMESTAMP\ncontent\n\n`
   - [ ] All message types appear (topic, pro, con, judge)

**Failure Criteria** (return for rework if any true):
- ❌ Any node crashes when output_writer is None
- ❌ output_writer not added to state in T014
- ❌ Speaker labels don't match node type (e.g., PRO node writes "CON")
- ❌ write_message() is awaited (blocking behavior)
- ❌ Nodes don't handle writer=None case
- ❌ Existing workflow behavior broken

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
