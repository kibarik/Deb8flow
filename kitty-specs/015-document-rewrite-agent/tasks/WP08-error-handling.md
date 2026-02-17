---
work_package_id: "WP08"
subtasks:
  - "T038"
  - "T039"
  - "T040"
  - "T041"
  - "T042"
  - "T043"
title: "Error Handling & Edge Cases"
phase: "Phase 3 - Integration"
lane: "planned"
assignee: ""
agent: ""
shell_pid: ""
review_status: ""
reviewed_by: ""
history:
  - timestamp: "2026-02-17T21:00:00Z"
    lane: "planned"
    agent: "system"
    shell_pid: ""
    action: "Prompt created via /spec-kitty.tasks"
dependencies: ["WP05", "WP06", "WP07"]
---

# Work Package Prompt: WP08 – Error Handling & Edge Cases

## Objectives & Success Criteria

- **Goal**: Implement graceful error handling, fallback behaviors, and edge case management.
- **Success Criteria**:
  - Fallback copy created on conversion/LLM failures
  - File-not-found handled without crashing
  - Empty conclusion handled with "no changes" note
  - Large files handled with warning
  - Unsupported format shows clear error
  - Error scenario tests pass

## Context & Constraints

- **Prerequisites**: WP05, WP06, WP07 (needs agent and CLI integration)
- **Supporting Documents**:
  - `kitty-specs/015-document-rewrite-agent/research.md` - Error recovery mechanism
  - `kitty-specs/015-document-rewrite-agent/spec.md` - User Story 5 acceptance scenarios
- **Constraints**:
  - Never crash main workflow
  - Always preserve debate results
  - Error messages must be actionable

## Subtasks & Detailed Guidance

### Subtask T038 – Create fallback copy with note

**Purpose**: Create a fallback document when rewrite fails, explaining what happened.

**Steps**:
1. In `src/agents/rewriter_agent.py`, create `create_fallback_copy(original_path: str, output_dir: str, error_message: str) -> str`:
   - Copy original to output directory with `_rewrite_failed.md` suffix
   - Add explanatory note at top of file:
     ```markdown
     # Document Rewrite Failed

     The automatic rewrite could not be completed. The original document is provided below for reference.

     **Error**: {error_message}

     **Recommendations**:
     - Review the conclusion.md for recommendations
     - Apply changes manually to the original document
     - Check the error message above for troubleshooting hints

     ---

     # Original Document
     ```
   - Append original content
   - Return path to fallback file
2. Update `rewrite_document()` to call `create_fallback_copy()` on exceptions

**Files**:
- `src/agents/rewriter_agent.py` (modify, ~40 lines added)

**Validation**:
- [ ] Fallback file created on error
- [ ] File includes error message and recommendations
- [ ] Original content preserved
- [ ] Returns path to fallback file

---

### Subtask T039 – Handle file not found

**Purpose**: Gracefully handle missing source or conclusion files.

**Steps**:
1. In file operations, add file existence checks:
   - `copy_document_with_metadata()`: Check source exists before copy
   - Raise `FileNotFoundError` with helpful message if not found
2. In rewriter agent, handle file not found:
   - In `rewrite_document()`: Check files exist before processing
   - If original not found: log error, return error result, don't crash
   - If conclusion not found: log warning, create copy with "no conclusion available" note
3. Update CLI integrations to catch file not found errors

**Files**:
- `src/utils/file_utils.py` (modify)
- `src/agents/rewriter_agent.py` (modify)

**Validation**:
- [ ] Missing original file logged and skipped
- [ ] Missing conclusion handled gracefully
- [ ] Error messages are actionable
- [ ] Main workflow not affected

---

### Subtask T040 – Handle empty conclusion

**Purpose**: Handle case where conclusion.md is empty or has no recommendations.

**Steps**:
1. In `src/agents/rewriter_agent.py`, update `extract_recommendations()`:
   - Check if conclusion file is empty (0 bytes)
   - Check if conclusion has no actionable recommendations
   - Return empty list in both cases
2. Update `rewrite_document()`:
   - If recommendations list empty: log message "No recommendations found"
   - Create copy of original with note: "No changes were applied - conclusion.md had no recommendations"
   - Return success result with `recommendations_applied=0`
3. Add message to top of file explaining no changes

**Files**:
- `src/agents/rewriter_agent.py` (modify, ~20 lines added)

**Validation**:
- [ ] Empty conclusion handled without error
- [ ] Copy created with "no changes" note
- [ ] Returns success result
- [ ] Message logged for user

---

### Subtask T041 – Handle large files

**Purpose**: Add size checking and warnings for large documents.

**Steps**:
1. In `src/utils/file_utils.py`, create `check_file_size(file_path: str, max_size_mb: int = 10) -> tuple[bool, str]`:
   - Get file size using `os.path.getsize()`
   - Check if exceeds max_size_mb
   - Return (True, "") if under limit
   - Return (False, warning_message) if over limit
2. In `src/agents/rewriter_agent.py`, add size check:
   - Before processing, call `check_file_size(original_path, 10)`
   - If over limit: log warning, continue with note about potential timeout
   - Consider extending LLM timeout for large files
3. Update CLI to display warning if file is large

**Files**:
- `src/utils/file_utils.py` (modify, ~15 lines added)
- `src/agents/rewriter_agent.py` (modify, ~10 lines added)

**Validation**:
- [ ] Size check performed before processing
- [ ] Warning logged for large files
- [ ] Processing continues (not blocked)
- [ ] User informed of potential timeout

**Notes**:
- 10MB is a reasonable limit (may timeout with larger files)
- Consider adding --timeout flag for large files in future

---

### Subtask T042 – Unsupported format error

**Purpose**: Provide clear error message when file format is not supported.

**Steps**:
1. In `src/utils/file_utils.py`, create `get_supported_formats() -> list[str]`:
   - Return list: ["docx", "md", "txt"]
2. In CLI integrations, add format validation:
   - Check file extension against supported formats
   - If unsupported: display error with supported list
   - Exit gracefully before debate starts
3. Error message format:
   ```
   Error: Unsupported file format '.pdf'
   Supported formats: .docx, .md, .txt
   ```

**Files**:
- `src/utils/file_utils.py` (modify, ~10 lines added)
- `product_committee.py` (modify, ~5 lines added)
- `document_debate_cli.py` (modify, ~5 lines added)

**Validation**:
- [ ] Unsupported format detected
- [ ] Clear error message with supported list
- [ ] Exits before debate
- [ ] Supported formats process normally

---

### Subtask T043 – Error handling tests

**Purpose**: Create tests for all error scenarios.

**Steps**:
1. Create `tests/integration/test_rewriter_error_handling.py`
2. Test cases:
   - `test_fallback_copy_on_conversion_error()` - Fallback created
   - `test_file_not_found_handling()` - Error logged, no crash
   - `test_empty_conclusion_handling()` - Copy with "no changes" note
   - `test_large_file_warning()` - Warning logged
   - `test_unsupported_format_error()` - Clear error message
3. Use fixtures for various error conditions
4. Verify debate results preserved in all cases

**Files**:
- `tests/integration/test_rewriter_error_handling.py` (new, ~120 lines)

**Commands**:
```bash
pytest tests/integration/test_rewriter_error_handling.py -v
```

---

## Test Strategy

Error handling tests should verify:
- Each error type is handled gracefully
- Debate results always preserved
- Error messages are clear and actionable
- Fallback behaviors work as expected

---

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Too many error cases overwhelm | Group related errors, common patterns |
| Error messages confuse users | Test with real users, iterate on wording |
| Fallback behavior not clear | Add clear explanation in fallback file |

---

## Review Guidance

**Key acceptance checkpoints**:
- [ ] Fallback copy created on rewrite failures
- [ ] All file not found cases handled
- [ ] Empty conclusion produces copy with note
- [ ] Large files trigger warnings
- [ ] Unsupported formats show clear errors
- [ ] All error tests pass
- [ ] Main workflow never crashes

**Context for reviewers**:
- Verify error messages are actionable
- Check that fallback files include helpful context
- Confirm debate results always preserved
- Ensure error logging at appropriate levels

---

## Activity Log

- 2026-02-17T21:00:00Z – system – lane=planned – Prompt created.
