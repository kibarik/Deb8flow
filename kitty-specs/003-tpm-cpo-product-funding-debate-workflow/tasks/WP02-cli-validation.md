---
work_package_id: "WP02"
title: "CLI Custom Prompt Flags and File Validation"
phase: "Phase 2 - Implementation"
lane: "for_review"
assignee: ""
agent: ""
shell_pid: ""
review_status: ""
reviewed_by: ""
dependencies:
- WP01
subtasks:
- T005
- T006
- T007
- T008
- T009
- T010
history:
  - timestamp: "2026-02-14T00:00:00Z"
    lane: "planned"
    agent: "system"
    shell_pid: ""
    action: "Prompt generated via /spec-kitty.tasks"
---

# Work Package Prompt: WP02 – CLI Custom Prompt Flags and File Validation

## Markdown Formatting
Wrap HTML/XML tags in backticks: `` `<div>` ``, `` `<script>` ``
Use language identifiers in code blocks: ````python`, ````bash

---

## Objectives & Success Criteria

**Objective:** Extend `document_debate_cli.py` to accept custom prompt file paths via CLI flags and validate those files before workflow execution.

**Success Criteria:**
- `--pro-prompt <path>` flag added to argument parser (optional)
- `--con-prompt <path>` flag added to argument parser (optional)
- `validate_prompt_file()` function implements all validation rules
- Validated prompts passed to `initial_state` for workflow
- Clear error messages for all validation failure cases
- No changes to existing CLI behavior when flags not provided

## Context & Constraints

**Feature:** 003-tpm-cpo-product-funding-debate-workflow
**Plan:** [plan.md](../plan.md)
**Spec:** [spec.md](../spec.md)
**Quickstart:** [quickstart.md](../quickstart.md)

**Key Constraints:**
- **BOTH FLAGS MUST BE OPTIONAL** - Users can provide one, both, or neither
- **VALIDATION MUST HAPPEN BEFORE WORKFLOW** - Fail fast with clear errors
- **MUST PRESERVE EXISTING BEHAVIOR** - No changes when flags not provided
- **FILE SIZE LIMIT** - Maximum 5000 characters per prompt file
- **CLEAR ERROR MESSAGES** - Users must understand what went wrong

**Technical Context:**
- CLI is implemented in `document_debate_cli.py` at project root
- Uses `argparse` for argument parsing
- Workflow state initialized via `initial_state` dictionary
- Base state requires: `debate_topic`, `positions`, `messages`
- Custom prompts are added to state as optional fields

**Validation Rules from Spec (FR5):**
- File must exist on filesystem
- File must not be empty (size > 0)
- File must be <= 5000 characters
- File must be readable as text

## Subtasks & Detailed Guidance

### Subtask T005 – Add --pro-prompt CLI Argument

**Purpose:** Add the `--pro-prompt` flag to accept custom PRO debater prompt file path.

**Files:**
- `document_debate_cli.py` (modify)

**Steps:**
1. Open `document_debate_cli.py` from project root
2. Locate the argparse argument definitions (search for `parser.add_argument`)
3. Add `--pro-prompt` argument after existing arguments
4. Set `type=str` to accept file path string
5. Add helpful description for users

**Implementation Pattern:**
```python
# In argument parsing section, after --request argument:
parser.add_argument(
    '--pro-prompt',
    type=str,
    help='Path to custom PRO debater prompt file (optional)'
)
```

**Validation:**
- Argument added with correct type (`str`)
- Argument is optional (no `required=True`)
- Help text clearly describes purpose
- Argument parser `help` output includes new flag

**Parallel?** No - Must complete before T008-T009

**Notes:**
- Do NOT set `required=True` - this is an optional feature
- Place after existing arguments but before `args = parser.parse_args()`
- Keep help text concise but clear

---

### Subtask T006 – Add --con-prompt CLI Argument

**Purpose:** Add the `--con-prompt` flag to accept custom CON debater prompt file path.

**Files:**
- `document_debate_cli.py` (modify)

**Steps:**
1. Open `document_debate_cli.py` from project root
2. Locate the argparse argument definitions
3. Add `--con-prompt` argument after `--pro-prompt`
4. Set `type=str` to accept file path string
5. Add helpful description for users

**Implementation Pattern:**
```python
# After --pro-prompt argument:
parser.add_argument(
    '--con-prompt',
    type=str,
    help='Path to custom CON debater prompt file (optional)'
)
```

**Validation:**
- Argument added with correct type (`str`)
- Argument is optional (no `required=True`)
- Help text clearly describes purpose
- Argument parser `help` output includes new flag

**Parallel?** No - Should complete alongside T005

**Notes:**
- Keep `--pro-prompt` and `--con-prompt` adjacent for readability
- Use consistent help text format

---

### Subtask T007 – Implement validate_prompt_file Function

**Purpose:** Create a validation function that checks prompt files meet all requirements.

**Files:**
- `document_debate_cli.py` (modify)

**Steps:**
1. Open `document_debate_cli.py` from project root
2. Add `validate_prompt_file()` function before `main()` function
3. Implement file existence check
4. Implement file empty check
5. Implement file size check (<= 5000 characters)
6. Return tuple of `(is_valid, content_or_error_message)`
7. Add docstring explaining validation logic

**Implementation Pattern:**
```python
def validate_prompt_file(file_path: str) -> tuple[bool, str]:
    """Validate custom prompt file exists, is non-empty, and within size limits.

    Args:
        file_path: Path to prompt file to validate

    Returns:
        Tuple of (is_valid, content_or_error_message)
        - If valid: (True, file_content)
        - If invalid: (False, error_message)

    Validation Rules:
        1. File must exist on filesystem
        2. File must not be empty (size > 0)
        3. File must be <= 5000 characters
        4. File must be readable as text
    """
    # Check file exists
    if not os.path.exists(file_path):
        return False, f"Prompt file not found: {file_path}"

    # Check file not empty
    if os.path.getsize(file_path) == 0:
        return False, f"Prompt file is empty: {file_path}"

    # Check file size <= 5000 chars and read content
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            if len(content) > 5000:
                return False, f"Prompt file too large (max 5000 characters): {file_path}"
    except Exception as e:
        return False, f"Failed to read prompt file {file_path}: {str(e)}"

    return True, content
```

**Validation:**
- Function returns tuple of `(bool, str)`
- File existence check implemented
- File empty check implemented
- File size check implemented (5000 char limit)
- Error handling for file read errors
- Function has clear docstring
- All validation rules from spec FR5 are implemented

**Parallel?** No - Must complete before T008-T009

**Notes:**
- Use `utf-8` encoding for file reading
- Return file content on success to avoid re-reading file
- Include file path in error messages for clarity

---

### Subtask T008 – Integrate Validation into Argument Parsing

**Purpose:** Call validation function for each provided prompt file and handle errors.

**Files:**
- `document_debate_cli.py` (modify)

**Steps:**
1. Locate where `base_state` dictionary is initialized
2. After `args = parser.parse_args()`, add validation logic
3. Check if `args.pro_prompt` is provided, validate if so
4. Check if `args.con_prompt` is provided, validate if so
5. For validation failures, log error and exit with `sys.exit(1)`
6. For validation success, add to `base_state` dictionary

**Implementation Pattern:**
```python
# After args = parser.parse_args():
base_state = {
    "debate_topic": "",
    "positions": {},
    "messages": []
}

# Validate and add pro_custom_prompt if provided
if args.pro_prompt:
    is_valid, result = validate_prompt_file(args.pro_prompt)
    if not is_valid:
        logger.error(f"❌ {result}")
        sys.exit(1)
    base_state["pro_custom_prompt"] = result
    logger.info(f"[cyan]📄 Loaded PRO custom prompt from: {args.pro_prompt}[/]")

# Validate and add con_custom_prompt if provided
if args.con_prompt:
    is_valid, result = validate_prompt_file(args.con_prompt)
    if not is_valid:
        logger.error(f"❌ {result}")
        sys.exit(1)
    base_state["con_custom_prompt"] = result
    logger.info(f"[cyan]📄 Loaded CON custom prompt from: {args.con_prompt}[/]")
```

**Validation:**
- Validation called for both flags independently
- Invalid files cause `sys.exit(1)` with error message
- Valid files added to `base_state` with correct field names
- Success messages logged when files loaded
- Code handles `--pro-prompt` only case
- Code handles `--con-prompt` only case
- Code handles both flags provided case
- Code handles neither flag provided case (existing behavior)

**Parallel?** No - Depends on T005-T007

**Notes:**
- Use `if args.pro_prompt` (not `is not None`) - argparse sets default to None
- Exit immediately on validation failure (fail fast)
- Log success messages to inform users which prompts were loaded

---

### Subtask T009 – Pass Validated Prompts to initial_state

**Purpose:** Ensure `base_state` with custom prompts is passed to workflow.

**Files:**
- `document_debate_cli.py` (modify)

**Steps:**
1. Locate where `workflow.run()` is called with `initial_state`
2. Verify `base_state` (with custom prompts if any) is passed correctly
3. Ensure no state fields are lost in the transition

**Implementation Pattern:**
```python
# At the bottom of main(), where workflow is invoked:
# Ensure base_state is passed (may include pro_custom_prompt, con_custom_prompt)
workflow_result = await workflow.run(initial_state=base_state)
```

**Validation:**
- `base_state` (not a separate dict) passed to workflow
- All required fields present (`debate_topic`, `positions`, `messages`)
- Optional fields present if provided (`pro_custom_prompt`, `con_custom_prompt`)
- Workflow receives complete state

**Parallel?** No - Depends on T008

**Notes:**
- Verify `base_state` contains all required fields before passing
- If validation errors occurred, workflow should not be reached

---

### Subtask T010 – Add Validation Error Handling and Messages

**Purpose:** Ensure all validation failure cases have clear, actionable error messages.

**Files:**
- `document_debate_cli.py` (modify)

**Steps:**
1. Review all error messages in `validate_prompt_file()` function
2. Ensure messages are clear and actionable
3. Ensure messages include file path for debugging
4. Test each error case manually if possible

**Error Message Guidelines:**
```python
# Good error messages:
"Prompt file not found: /path/to/file.txt"  # Clear what's wrong and which file
"Prompt file is empty: /path/to/file.txt"      # Clear what's wrong
"Prompt file too large (max 5000 characters): /path/to/file.txt"  # Clear limit

# Bad error messages:
"File not found"              # Which file?
"Invalid file"                # What's wrong?
"Error"                       # Useless
```

**Validation:**
- "File not found" error message includes file path
- "Empty file" error message includes file path
- "File too large" error message includes file path and limit
- Error messages use emoji for visibility (❌)
- Error messages formatted with Rich markup
- All error cases from T007 have clear messages

**Parallel?** Yes - Can be done alongside T008-T009

**Notes:**
- Use consistent error message format
- Include actionable information (what's wrong, which file, how to fix)
- Test error messages by triggering each case manually

## Test Strategy

**Manual Testing:**
- Test CLI with `--help` to see new flags in usage
- Test CLI with invalid file path (should show error)
- Test CLI with empty file (should show error)
- Test CLI with file > 5000 chars (should show error)
- Test CLI with valid `--pro-prompt` only
- Test CLI with valid `--con-prompt` only
- Test CLI with both valid prompts
- Test CLI without custom prompts (existing behavior)

**No Automated Tests in This WP:**
- Full testing happens in WP05 (Testing)
- This WP focuses on implementation

**Definition of Done:**
- `--pro-prompt` and `--con-prompt` flags added to CLI
- `validate_prompt_file()` function implements all validation rules
- Validated prompts passed to `initial_state`
- Clear error messages for all failure cases
- Existing CLI behavior unchanged when flags not provided

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| File I/O errors during validation | Medium | Wrap file operations in try/except; return clear error messages |
| Empty files cause unexpected behavior | Medium | Check file size > 0; validate before reading content |
| Large files impact performance | Low | Enforce 5000 character limit; fail with clear error |
| Users provide binary/non-text files | Low | Try reading as UTF-8 text; fail with clear error if fails |
| Validation happens too late | Medium | Validate immediately after argparse; exit before workflow starts |

## Review Guidance

**Key Acceptance Checkpoints:**
- [ ] `--pro-prompt` flag added and optional
- [ ] `--con-prompt` flag added and optional
- [ ] `validate_prompt_file()` validates: file exists, not empty, <= 5000 chars
- [ ] Validation failures show clear error messages with file paths
- [ ] Validated prompts added to `base_state` with correct field names
- [ ] Existing CLI behavior unchanged when flags not provided
- [ ] Code exits with `sys.exit(1)` on validation failure

**Review Context:**
- Spec requirement FR1: CLI must accept `--pro-prompt` and `--con-prompt` flags
- Spec requirement FR5: File validation rules must be implemented
- Spec requirement FR6: Must preserve existing behavior (backward compatibility)
- Quickstart examples: `--pro-prompt tpm_prompt.txt --con-prompt cpo_prompt.txt`

## Activity Log

> **CRITICAL**: Activity log entries MUST be in chronological order (oldest first, newest last).

### How to Add Activity Log Entries

**When adding an entry:**
1. Scroll to the bottom of this file (Activity Log section below "Valid lanes")
2. **APPEND** the new entry at the END (do NOT prepend or insert in middle)
3. Use exact format: `- YYYY-MM-DDTHH:MM:SSZ – agent_id – lane=<lane> – <action>`
4. Timestamp MUST be current time in UTC (check with `date -u "+%Y-%m-%dT%H:%M:%SZ"`)
5. Lane MUST match the frontmatter `lane:` field exactly
6. Agent ID should identify who made the change (claude-sonnet-4-5, codex, etc.)

**Format:**
```
- YYYY-MM-DDTHH:MM:SSZ – <agent_id> – lane=<lane> – <brief action description>
```

**Example (correct chronological order):**
```
- 2026-02-14T00:00:00Z – system – lane=planned – Prompt created
- 2026-02-14T01:30:00Z – claude – lane=doing – Started implementation
- 2026-02-14T02:00:00Z – codex – lane=for_review – Implementation complete, ready for review
- 2026-02-14T02:30:00Z – claude – lane=done – Review passed, all tests passing  ← LATEST (at bottom)
```

**Common mistakes (DO NOT DO THIS):**
- Adding new entry at the top (breaks chronological order)
- Using future timestamps (causes acceptance validation to fail)
- Lane mismatch: frontmatter says `lane: "done"` but log entry says `lane=doing`
- Inserting in middle instead of appending to end

**Why this matters**: The acceptance system reads the LAST activity log entry as the current state. If entries are out of order, acceptance will fail even when the work is complete.

**Initial entry:**
- 2026-02-14T00:00:00Z – system – lane=planned – Prompt created.

---

### Updating Lane Status

To change a work package's lane, either:

1. **Edit directly**: Change the `lane:` field in frontmatter AND append activity log entry (at the end)
2. **Use CLI**: `spec-kitty agent tasks move-task <WPID> --to <lane> --note "message"` (recommended)

The CLI command updates both frontmatter and activity log automatically.

**Valid lanes**: `planned`, `doing`, `for_review`, `done`
- 2026-02-13T23:56:25Z – unknown – lane=for_review – Ready for review: CLI flags --pro-prompt and --con-prompt with file validation
