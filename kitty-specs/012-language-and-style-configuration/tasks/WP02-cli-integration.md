---
work_package_id: WP02
title: CLI Integration
lane: planned
dependencies: []
subtasks:
- T007
- T008
- T009
- T010
- T011
phase: Phase 1 - Implementation
assignee: ''
agent: ''
shell_pid: ''
review_status: ''
reviewed_by: ''
history:
- timestamp: '2025-02-17T16:00:00Z'
  lane: planned
  agent: system
  shell_pid: ''
  action: Prompt generated via /spec-kitty.tasks
---

# Work Package Prompt: WP02 – CLI Integration

## ⚠️ IMPORTANT: Review Feedback Status

**Read this first if you are implementing this task!**

- **Has review feedback?**: Check the `review_status` field above. If it says `has_feedback`, scroll to the **Review Feedback** section immediately (right below this notice).
- **You must address all feedback** before your work is complete. Feedback items are your implementation TODO list.
- **Mark as acknowledged**: When you understand the feedback and begin addressing it, update `review_status: acknowledged` in the frontmatter.
- **Report progress**: As you address each feedback item, update the Activity Log explaining what you changed.

---

## Review Feedback

> **Populated by `/spec-kitty.review`** – Reviewers add detailed feedback here when work needs changes. Implementation must address every item listed below before returning for re-review.

*[This section is empty initially. Reviewers will populate it if the work is returned from review. If you see feedback here, treat each item as a must-do before completion.]*

---

## Markdown Formatting
Wrap HTML/XML tags in backticks: `<div>`, `<script>`
Use language identifiers in code blocks: `python`, `bash`

---

## Objectives & Success Criteria

**Primary Objective**: Add the `--language` CLI flag to both `main.py` and `document_debate_cli.py` with proper validation and state propagation.

**Success Criteria**:
- `main.py` accepts `--language` argument
- `document_debate_cli.py` accepts `--language` argument
- Length validation rejects values > 500 characters
- Empty strings treated as None (no language injection)
- Language setting passed to initial state in both workflows
- Help text explains the flag's purpose
- Backward compatible: existing commands work unchanged

---

## Context & Constraints

**Feature Specification**: [spec.md](../spec.md)
**Implementation Plan**: [plan.md](../plan.md)
**CLI Contract**: [contracts/cli-interface.md](../contracts/cli-interface.md)

**Prerequisites**:
- WP01 must be complete (`DebateState.language_setting` field exists)

**Key Design Decisions**:
1. **Both CLIs**: Flag added to `main.py` AND `document_debate_cli.py`
2. **Length Limit**: 500 characters max (enforced at CLI level)
3. **Empty Handling**: `args.language if args.language else None` treats empty string as None
4. **Validation**: Error and exit if length exceeded

**Constitution Requirements**:
- Cross-platform (Linux, macOS, Windows)
- No new dependencies (use argparse from stdlib)
- Self-documenting code with clear error messages

---

## Subtasks & Detailed Guidance

### Subtask T007 – Add --language argument to main.py

**Purpose**: Add the `--language` CLI flag to `main.py` for standard debates.

**Files**:
- `main.py`

**Steps**:

1. **Read current main.py structure**:
   ```python
   async def main():
       setup_logging()
       validate_env()
       logger = logging.getLogger("main")
       try:
           logger.info("[bold green]Starting debate workflow...[/]")
           workflow = DebateWorkflow()
           workflow_result = await workflow.run()
           # ... rest of code
   ```

2. **Add argparse integration** before workflow creation:
   ```python
   import argparse

   async def main():
       setup_logging()
       validate_env()
       logger = logging.getLogger("main")

       # Parse CLI arguments
       parser = argparse.ArgumentParser(
           description="Run an AI debate between PRO and CON agents"
       )
       parser.add_argument(
           "--language",
           type=str,
           help="Language and style setting for all agents (e.g., 'Русский официальный стиль', 'English, concise')"
       )
       args = parser.parse_args()

       try:
           logger.info("[bold green]Starting debate workflow...[/]")

           # Prepare language setting
           language_setting = None
           if args.language:
               if len(args.language) > 500:
                   logger.error("❌ --language value too long (max 500 characters)")
                   sys.exit(1)
               language_setting = args.language if args.language.strip() else None

           workflow = DebateWorkflow()
           workflow_result = await workflow.run(initial_state={"language_setting": language_setting})
   ```

3. **Add missing imports**:
   ```python
   import sys
   import argparse
   ```

**Validation**:
- [ ] `python main.py --help` shows the new flag
- [ ] `python main.py --language "test"` works without error
- [ ] `python main.py` (no flag) works as before

**Notes**:
- Use empty string check: `args.language.strip()` to catch whitespace-only input
- Exit code 1 for validation errors
- Initial state dict passed to `workflow.run()`

---

### Subtask T008 – Add --language argument to document_debate_cli.py [PARALLEL]

**Purpose**: Add the `--language` CLI flag to `document_debate_cli.py` for document-based debates.

**Files**:
- `document_debate_cli.py`

**Steps**:

1. **Locate existing argparse setup** in `document_debate_cli.py` (around line 108):
   ```python
   parser = argparse.ArgumentParser(
       description="Run an AI debate based on a document"
   )
   parser.add_argument("--docx", help="Path to .docx file for context")
   parser.add_argument("--text", help="Direct topic input")
   # ... other arguments
   ```

2. **Add the --language argument** after existing arguments:
   ```python
   parser.add_argument(
       "--language",
       type=str,
       help="Language and style setting for all agents (e.g., 'Русский официальный стиль', 'English, concise')"
   )
   ```

3. **Add validation after args.parse_args()** (around line 144):
   ```python
   args = parser.parse_args()

   # Validate language setting length
   language_setting = None
   if args.language:
       if len(args.language) > 500:
           logger.error("❌ --language value too long (max 500 characters)")
           sys.exit(1)
       language_setting = args.language if args.language.strip() else None
       logger.info(f"[cyan]🌐 Language setting: {language_setting}[/]")
   ```

**Validation**:
- [ ] `python document_debate_cli.py --help` shows the flag
- [ ] Works with `--text` and `--docx` modes
- [ ] Length validation works

**Parallel Notes**: Can be implemented simultaneously with T007 (different files)

---

### Subtask T009 – Implement length validation in both CLIs [PARALLEL]

**Purpose**: Ensure both CLIs validate the 500-character limit consistently.

**Files**:
- `main.py`
- `document_debate_cli.py`

**Steps**:

1. **Validation logic** (same for both files):
   ```python
   if args.language:
       if len(args.language) > 500:
           logger.error("❌ --language value too long (max 500 characters)")
           sys.exit(1)
   ```

2. **Test validation** manually:
   ```bash
   # Should fail
   python main.py --language "$(python -c 'print("a" * 501)')"

   # Should succeed
   python main.py --language "$(python -c 'print("a" * 500)')"
   ```

**Validation**:
- [ ] 501-character string triggers error
- [ ] 500-character string passes
- [ ] Error message is user-friendly
- [ ] Exit code is 1

**Parallel Notes**: Implement in both files simultaneously

---

### Subtask T010 – Pass language_setting to initial state in main.py

**Purpose**: Ensure the language setting from CLI is propagated to the workflow state.

**Files**:
- `main.py`

**Steps**:

1. **After validation**, prepare initial state:
   ```python
   # Prepare language setting
   language_setting = None
   if args.language:
       if len(args.language) > 500:
           logger.error("❌ --language value too long (max 500 characters)")
           sys.exit(1)
       language_setting = args.language if args.language.strip() else None

   # Create initial state
   initial_state = {"language_setting": language_setting}

   # Run workflow with initial state
   workflow = DebateWorkflow()
   workflow_result = await workflow.run(initial_state=initial_state)
   ```

2. **Verify workflow.run() accepts initial_state** parameter (check signature).

**Validation**:
- [ ] `workflow.run()` receives `initial_state` dict
- [ ] State includes `language_setting` when flag provided
- [ ] State has `language_setting: None` when flag not provided

**Notes**:
- If `workflow.run()` doesn't accept `initial_state`, check `workflow/debate_workflow.py` for alternative method

---

### Subtask T011 – Pass language_setting to initial state in document_debate_cli.py [PARALLEL]

**Purpose**: Ensure the language setting from CLI is propagated to the document workflow state.

**Files**:
- `document_debate_cli.py`

**Steps**:

1. **Locate base_state initialization** (around line 153):
   ```python
   base_state = {
       "debate_topic": "",
       "positions": {},
       "messages": []
   }
   ```

2. **Add language_setting to base_state**:
   ```python
   # Prepare language setting
   language_setting = None
   if args.language:
       if len(args.language) > 500:
           logger.error("❌ --language value too long (max 500 characters)")
           sys.exit(1)
       language_setting = args.language if args.language.strip() else None
       logger.info(f"[cyan]🌐 Language setting: {language_setting}[/]")

   base_state = {
       "debate_topic": "",
       "positions": {},
       "messages": [],
       "language_setting": language_setting  # NEW
   }
   ```

3. **Verify** that `base_state` is passed to workflow:
   ```python
   workflow = DocumentDebateWorkflow()
   workflow_result = await workflow.run(initial_state=initial_state)
   ```

**Validation**:
- [ ] Language setting in base_state when flag provided
- [ ] Works with both `--text` and `--docx` modes
- [ ] Logging shows language setting when present

**Parallel Notes**: Can be implemented simultaneously with T010

---

## Test Strategy

**Manual Testing**:
```bash
# Test main.py
python main.py --help  # Should show --language flag
python main.py --language "Русский официальный стиль"  # Should work
python main.py --language ""  # Should work (treated as None)
python main.py --language "$(python -c 'print("a" * 501)')"  # Should fail with error

# Test document_debate_cli.py
python document_debate_cli.py --help  # Should show --language flag
python document_debate_cli.py --text "test" --language "English"  # Should work
python document_debate_cli.py --text "test" --language "$(python -c 'print("a" * 501)')"  # Should fail
```

**Integration Testing** (after WP03):
- Full workflow with language flag
- Verify language reaches agents

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| workflow.run() doesn't accept initial_state | Medium | Check workflow signature; may need to pass during workflow __init__ |
| Empty string not handled correctly | Low | Use `.strip()` check: `args.language.strip()` |
| argparse conflicts with existing args | Low | Add at end of argument list |
| Cross-platform argparse behavior | Low | argparse is stdlib, consistent across platforms |

---

## Review Guidance

**Key Acceptance Checkpoints**:
1. Both CLIs have `--language` flag with help text
2. 500-character limit enforced with clear error message
3. Empty strings treated as None (no injection)
4. Language setting passed to initial state in both workflows
5. Existing commands work unchanged (backward compatibility)

**What to Review**:
- `main.py`: argparse setup, validation, initial state
- `document_debate_cli.py`: argparse setup, validation, base_state
- Error messages are clear and actionable

**Red Flags**:
- Missing sys.exit(1) after validation error
- Language setting not passed to workflow
- Breaking changes to existing argument parsing

---

## Activity Log

> **CRITICAL**: Activity log entries MUST be in chronological order (oldest first, newest last).

- 2025-02-17T16:00:00Z – system – lane=planned – Prompt created.

---

### Updating Lane Status

To change a work package's lane, either:

1. **Edit directly**: Change the `lane:` field in frontmatter AND append activity log entry (at the end)
2. **Use CLI**: `spec-kitty agent tasks move-task WP02 --to <lane> --note "message"` (recommended)

The CLI command updates both frontmatter and activity log automatically.

**Valid lanes**: `planned`, `doing`, `for_review`, `done`

**Implementation Command**:
```bash
spec-kitty implement WP02 --base WP01
```
