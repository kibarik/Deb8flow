---
work_package_id: WP03
title: Edge Case Handling & Validation
lane: planned
dependencies: [WP02]
subtasks: [T011, T012, T013, T014]
history:
- date: 2026-02-14
  action: Created
  author: spec-kitty.tasks
---

# Work Package: Edge Case Handling & Validation

## Implementation Command

```bash
spec-kitty implement WP03 --base WP02
```

## Objective

Handle edge cases gracefully and validate summary output under various conditions. This ensures the summary feature is robust and doesn't break the workflow when data is missing or incomplete.

## Context

The summary feature assumes `original_question` and `final_answer` exist in the state, but there are scenarios where these fields may be missing or empty:
- Legacy workflow paths that don't populate these fields
- Debate failures or early terminations
- Malformed or unexpected state data
- Empty user input

This work package adds defensive handling to make the feature production-ready.

**Key files to modify**:
- `cli/debate_summary_formatter.py` - Add defensive formatting logic
- `document_debate_cli.py` - Add error handling around summary display

## Subtasks

### T011: Handle missing `original_question` (display placeholder or skip)

**Purpose**: Ensure the summary displays gracefully when the original question is not recorded.

**Steps**:
1. Open `cli/debate_summary_formatter.py`
2. Modify `format_summary()` to check for empty/missing `original_question`
3. Define "empty" as: `None`, empty string `""`, or whitespace-only string
4. When empty, display placeholder: `"[No question recorded]"`
5. Consider adding a subtle indicator that this is incomplete data
6. Ensure the summary still displays (don't skip entirely)

**Implementation Details**:
```python
def _is_empty(self, value: str) -> bool:
    """Check if a string value is empty or whitespace."""
    return value is None or (isinstance(value, str) and not value.strip())

def format_summary(self) -> Panel:
    """Format the debate summary for display."""
    original_question = self.state.get("original_question", "")
    final_answer = self.state.get("final_answer", "")

    # Handle missing question
    if self._is_empty(original_question):
        question_display = "[italic dim]No question recorded[/]"
    else:
        question_display = original_question

    # ... rest of formatting
```

**Files**:
- `cli/debate_summary_formatter.py` (~80 lines, add ~15 lines)

**Validation**:
- [ ] Empty `original_question` shows placeholder
- [ ] Placeholder text is styled (italic/dim) to indicate it's not real data
- [ ] Summary still displays (not skipped)
- [ ] No crashes or exceptions when field is missing
- [ ] Log warning when placeholder is used

**Edge Cases**:
- Field is `None` → Show placeholder
- Field is `""` → Show placeholder
- Field is `"   "` (whitespace) → Show placeholder
- Field exists but is very long → Truncate or wrap (Rich handles wrapping)

---

### T012: Handle missing `final_answer` (display verdict instead)

**Purpose**: Provide fallback display when the judge's answer is not available.

**Steps**:
1. Open `cli/debate_summary_formatter.py`
2. Check for empty/missing `final_answer` using same `_is_empty()` logic
3. When empty, attempt to fallback to `judge_verdict.justification`
4. If verdict is also missing, display placeholder: `"[No answer determined]"`
5. Style placeholder text to indicate incomplete data
6. Log a warning when fallback to placeholder is needed

**Implementation Details**:
```python
def format_summary(self) -> Panel:
    """Format the debate summary for display."""
    original_question = self.state.get("original_question", "")
    final_answer = self.state.get("final_answer", "")

    # Handle missing answer with fallback
    if self._is_empty(final_answer):
        # Try to get from judge_verdict
        judge_verdict = self.state.get("judge_verdict", {})
        verdict_justification = judge_verdict.get("justification", "")
        if self._is_empty(verdict_justification):
            answer_display = "[italic dim]No answer determined[/]"
            logger.warning("Summary: final_answer and judge_verdict.justification both missing")
        else:
            answer_display = verdict_justification
    else:
        answer_display = final_answer

    # ... rest of formatting
```

**Files**:
- `cli/debate_summary_formatter.py` (~90 lines, add ~15 lines)

**Validation**:
- [ ] Missing `final_answer` falls back to verdict justification
- [ ] Missing both shows placeholder
- [ ] Placeholder is styled differently from real data
- [ ] Warning logged when using placeholder
- [ ] No crashes or exceptions

**Notes**:
- Fallback to verdict makes the summary more useful
- Judge verdict should always exist in normal workflow
- If verdict is also missing, indicates a workflow issue

---

### T013: Handle empty/null state (display appropriate message)

**Purpose**: Ensure the summary formatter handles completely empty or null state gracefully.

**Steps**:
1. Add defensive check in `DebateSummaryFormatter.__init__`
2. If state is `None`, raise a clear error or use empty dict
3. Add method `_should_display_summary()` to check if summary should be shown
4. Criteria for display: at least one of `original_question` or `final_answer` exists and is non-empty
5. Return `False` if both fields are empty/missing
6. Update CLI to call this check before displaying summary

**Implementation Details**:
```python
class DebateSummaryFormatter:
    def __init__(self, state: Dict[str, Any]):
        """Initialize formatter with debate state."""
        if state is None:
            raise ValueError("DebateState cannot be None")
        self.state = state
        self.console = Console()

    def should_display_summary(self) -> bool:
        """Check if summary has meaningful content to display."""
        original_question = self.state.get("original_question", "")
        final_answer = self.state.get("final_answer", "")

        # Check if either field has content
        return not (self._is_empty(original_question) and self._is_empty(final_answer))
```

**Files**:
- `cli/debate_summary_formatter.py` (~100 lines, add ~20 lines)
- `document_debate_cli.py` (~185 lines, modify summary display)

**Validation**:
- [ ] `None` state raises clear error
- [ ] Empty state returns `False` from `should_display_summary()`
- [ ] CLI checks `should_display_summary()` before showing summary
- [ ] No summary displayed when both fields are empty
- [ ] No crashes with any valid state shape

**CLI Integration**:
```python
# In document_debate_cli.py, update T008 code:
formatter = DebateSummaryFormatter(workflow_result)
if formatter.should_display_summary():
    summary_panel = formatter.format_summary()
    console.print("\n")
    console.print(summary_panel)
```

---

### T014: Add manual test scenarios for all edge cases

**Purpose**: Document and verify edge case handling through manual testing.

**Steps**:
1. Create test scenarios covering all edge cases
2. For each scenario, describe expected behavior
3. Run manual tests and document results
4. Create a test checklist document

**Test Scenarios**:

| Scenario | Setup | Expected Behavior |
|----------|-------|-------------------|
| Normal flow | `--docx file.docx --request "Q?"` | Shows Q and A |
| Missing question | Old workflow without direct_topic | Shows placeholder for Q |
| Missing answer | Judge produces no verdict | Shows placeholder for A |
| Both missing | Empty state | No summary displayed |
| Empty string question | `--request ""` | Shows placeholder for Q |
| Verdict fallback | final_answer missing, verdict exists | Shows verdict justification |
| Very long content | Long question/answer | Rich wraps text nicely |
| Russian characters | Non-ASCII content | Displays correctly |
| Special characters | Question has quotes, markdown | Displays as-is (no rendering) |

**Documentation**:
Create `kitty-specs/006-cli-debate-summary/checklists/edge-case-testing.md`:
```markdown
# Edge Case Testing Checklist

## Normal Flow
- [ ] Test with --docx and --request
- [ ] Summary shows both Q and A
- [ ] Formatting is correct

## Missing Fields
- [ ] Test with missing original_question
- [ ] Test with missing final_answer
- [ ] Test with both missing
- [ ] Placeholders display correctly

## Empty Content
- [ ] Test with empty string question
- [ ] Test with whitespace-only content
- [ ] Placeholders used appropriately

## Verdict Fallback
- [ ] Test with final_answer missing, verdict present
- [ ] Verdict justification displayed as answer

## Character Handling
- [ ] Test with Russian characters
- [ ] Test with special characters
- [ ] Test with very long content
```

**Files**:
- `kitty-specs/006-cli-debate-summary/checklists/edge-case-testing.md` (new file)

**Validation**:
- [ ] All test scenarios documented
- [ ] Each scenario has expected behavior
- [ ] At least one manual test run per scenario
- [ ] Results documented in checklist
- [ ] Any failing scenarios have issues logged

**Notes**:
- Manual testing is sufficient; automated tests not required
- Focus on user-facing correctness rather than code coverage
- Document any scenarios that don't work as expected

---

## Test Strategy

**Manual Testing Approach**:
1. For each scenario in T014 table, run the CLI
2. Verify expected behavior matches actual behavior
3. Document any deviations or issues
4. Retest after fixes

**Priority Scenarios** (must pass):
- Normal flow with `--docx --request`
- Missing question (legacy workflow)
- Missing answer (workflow issue)
- Empty state

**Secondary Scenarios** (nice to have):
- Character encoding (Russian, special chars)
- Long content wrapping
- Verdict fallback

---

## Definition of Done

This work package is complete when:
- [ ] Missing `original_question` shows placeholder
- [ ] Missing `final_answer` falls back to verdict
- [ ] Both missing → no summary displayed
- [ ] `should_display_summary()` check implemented
- [ ] CLI integrates the display check
- [ ] All edge case scenarios documented
- [ ] Manual testing confirms expected behaviors
- [ ] No crashes or exceptions from edge cases
- [ ] Appropriate warnings logged for missing data

---

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|-------|------------|--------|------------|
| Too many edge cases to handle | Medium | Low | Focus on common scenarios from spec |
| Placeholder text confuses users | Low | Medium | Use styling (italic/dim) to indicate it's a placeholder |
| Workflow changes break edge case handling | Low | High | Defensive checks and warnings |
| Character encoding issues | Low | Low | Rich handles Unicode; verify with manual test |

---

## Reviewer Guidance

**Focus areas for code review**:
1. Edge cases don't cause crashes or exceptions
2. Placeholder text is clearly indicated as not real data
3. Fallback logic (verdict) is reasonable
4. `should_display_summary()` logic is correct
5. CLI integration doesn't break when summary is skipped

**Integration points**:
- `DebateSummaryFormatter` handles missing data defensively
- CLI checks `should_display_summary()` before showing
- Warnings logged for debugging missing fields

**No next work package** - This is the final work package for the feature.

---

## Dependencies

This work package depends on **WP02** because:
- Requires `DebateSummaryFormatter` class to exist
- Requires summary display integration to be complete
- Edge case handling is built on top of the base implementation

Use `--base WP02` when implementing to branch from the completed WP02 work.

---

## Notes

- Edge case handling is about graceful degradation, not perfection
- It's acceptable for edge cases to show placeholders rather than skip entirely
- Warnings help debug issues without breaking the workflow
- Future enhancements could add retry logic or recovery for some edge cases
