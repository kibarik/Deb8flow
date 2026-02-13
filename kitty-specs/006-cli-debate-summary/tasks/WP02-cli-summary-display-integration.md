---
work_package_id: WP02
title: CLI Summary Display Integration
lane: planned
dependencies: [WP01]
subtasks: [T006, T007, T008, T009, T010]
history:
- date: 2026-02-14
  action: Created
  author: spec-kitty.tasks
---

# Work Package: CLI Summary Display Integration

## Implementation Command

```bash
spec-kitty implement WP02 --base WP01
```

## Objective

Implement the console summary output in the CLI tool after winner selection. This creates the user-facing component that displays the question-answer pairs in a readable format.

## Context

The CLI tool currently displays the winner verdict but does not show a summary of what question was asked and what answer was determined. This work package creates a formatter class and integrates it into the CLI display flow.

**Key files to create/modify**:
- `cli/debate_summary_formatter.py` (new file) - Summary formatting logic
- `document_debate_cli.py` - Integration point for summary display

## Subtasks

### T006: Create `DebateSummaryFormatter` class for output formatting

**Purpose**: Create a dedicated class for formatting and displaying debate summaries.

**Steps**:
1. Create new file `cli/debate_summary_formatter.py`
2. Create a class `DebateSummaryFormatter` that accepts `DebateState` in constructor
3. Store the state as an instance variable
4. Add a placeholder method `format_summary()` that returns an empty string
5. Add type hints for the state parameter

**Implementation Template**:
```python
from typing import Dict, Any
from rich.console import Console
from rich.panel import Panel

class DebateSummaryFormatter:
    """Formats and displays debate summaries for CLI output."""

    def __init__(self, state: Dict[str, Any]):
        """
        Initialize formatter with debate state.

        Args:
            state: Final debate state containing original_question and final_answer
        """
        self.state = state
        self.console = Console()

    def format_summary(self) -> str:
        """
        Format the debate summary for display.

        Returns:
            Formatted summary string
        """
        # Implementation in T007
        pass
```

**Files**:
- `cli/debate_summary_formatter.py` (new file, ~40 lines)

**Validation**:
- [ ] File created at correct path
- [ ] Class accepts state in constructor
- [ ] Type hints are present
- [ ] Placeholder `format_summary()` method exists
- [ ] Console from Rich is initialized

**Notes**:
- This class isolates summary formatting logic from the CLI
- Rich Console is used for consistent styling with existing CLI output
- The class will be expanded in T007

---

### T007: Implement `format_summary()` method with question/answer display

**Purpose**: Implement the core formatting logic that displays question-answer pairs.

**Steps**:
1. Open `cli/debate_summary_formatter.py`
2. Implement the `format_summary()` method
3. Extract `original_question` and `final_answer` from state
4. Format output using Rich Panel with this structure:
   ```
   ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
   ┃         DEBATE SUMMARY                  ┃
   ┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫
   ┃                                            ┃
   ┃ Q: {original_question}                   ┃
   ┃                                            ┃
   ┃ A: {final_answer}                        ┃
   ┃                                            ┃
   ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
   ```
5. Handle missing fields gracefully (empty strings, None values)
6. Return the formatted panel as a string

**Implementation Details**:
- Use `Panel` from Rich for the border container
- Title: "DEBATE SUMMARY" in bold cyan
- Content: formatted with "Q: " and "A: " prefixes
- If `original_question` is empty, show "[No question recorded]"
- If `final_answer` is empty, show "[No answer determined]"
- Use proper spacing for readability

**Example Implementation**:
```python
from rich.panel import Panel
from rich.text import Text

def format_summary(self) -> Panel:
    """Format the debate summary for display."""
    original_question = self.state.get("original_question", "[No question recorded]")
    final_answer = self.state.get("final_answer", "[No answer determined]")

    # Build content with Q/A formatting
    content = f"Q: {original_question}\n\nA: {final_answer}"

    # Create panel with border
    panel = Panel(
        content,
        title="[bold cyan]DEBATE SUMMARY[/]",
        title_align="left",
        border_style="cyan",
        padding=(0, 1)
    )

    return panel
```

**Files**:
- `cli/debate_summary_formatter.py` (~70 lines, add ~30 lines)

**Validation**:
- [ ] Method returns a Rich Panel object
- [ ] Panel has "DEBATE SUMMARY" title in cyan
- [ ] Question is prefixed with "Q: "
- [ ] Answer is prefixed with "A: "
- [ ] Empty fields show placeholder text
- [ ] Content has proper spacing and formatting

**Edge Cases** (to be fully handled in WP03):
- Both fields empty → Show "[No question recorded]" and "[No answer determined]"
- One field empty → Show placeholder for empty field, actual value for other
- Very long content → Rich Panel handles wrapping automatically

---

### T008: Add summary display to `document_debate_cli.py` main function

**Purpose**: Integrate the summary formatter into the CLI display flow.

**Steps**:
1. Open `document_debate_cli.py`
2. Locate the verdict display section (lines 156-168)
3. Import `DebateSummaryFormatter` at the top of the file
4. After the verdict display block, add summary display code
5. Create formatter instance with `workflow_result`
6. Call `format_summary()` and print the result
7. Ensure summary appears after the verdict but before the final success message

**Implementation Location**:
```python
# After this block (lines 156-168):
if "messages" in workflow_result and workflow_result["messages"]:
    final_message = workflow_result["messages"][-1]["content"]
    # ... verdict display ...

# Add summary display here:
if workflow_result.get("original_question") or workflow_result.get("final_answer"):
    from cli.debate_summary_formatter import DebateSummaryFormatter

    formatter = DebateSummaryFormatter(workflow_result)
    summary_panel = formatter.format_summary()
    console.print("\n")
    console.print(summary_panel)

# Then the success message (line 169)
logger.info("[bold green]Workflow completed successfully | Status: [bold]SUCCESS[/][/]")
```

**Files**:
- `document_debate_cli.py` (~179 lines, add ~10 lines)

**Validation**:
- [ ] Import added at top of file
- [ ] Summary appears after verdict display
- [ ] Summary appears before final success message
- [ ] Only shows if at least one field has content
- [ ] Uses same console object as existing output
- [ ] Blank line printed before summary for separation

**Notes**:
- Conditional display prevents empty summary box
- Placement after verdict maintains logical flow
- Same console object ensures consistent styling

---

### T009: Style summary output with Rich console formatting

**Purpose**: Enhance the visual presentation of the summary for better readability.

**Steps**:
1. Review the summary display in T008
2. Apply Rich formatting for visual polish:
   - Use `[bold cyan]` for the summary title
   - Use `[cyan]` for the border style
   - Add padding for better spacing
   - Ensure alignment matches existing CLI output
3. Test with actual debate output to verify styling
4. Adjust colors/styles to match existing CLI aesthetic

**Styling Specifications**:
- Border color: Cyan (matches CLI theme)
- Title: Bold cyan text "DEBATE SUMMARY"
- Padding: (0, 1) - no vertical padding, 1 space horizontal padding
- Title alignment: Left
- Content: Plain text (no markup in Q/A content to avoid injection)

**Files**:
- `cli/debate_summary_formatter.py` (adjust formatting)
- `document_debate_cli.py` (verify integration)

**Validation**:
- [ ] Summary visually stands out from other output
- [ ] Colors are consistent with CLI theme
- [ ] Spacing makes Q/A pairs easy to distinguish
- [ ] No markup rendering issues in content
- [ ] Professional appearance matching existing CLI style

**Notes**:
- Don't over-format; keep it clean and readable
- Avoid markup in user-provided content to prevent injection
- Test with Russian characters (user's example language)

---

### T010: Ensure summary appears after verdict display

**Purpose**: Verify and guarantee the summary appears in the correct position in the output flow.

**Steps**:
1. Review the complete CLI output sequence in `document_debate_cli.py`
2. Ensure the order is:
   a. Debate messages (if shown)
   b. Winner verdict (existing display)
   c. **Summary (new)**
   d. Success message
3. Add blank lines before/after summary for visual separation
4. Test full CLI run to verify order
5. Adjust spacing if needed

**Expected Output Flow**:
```
[debate messages...]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  🏆 WINNER: PRO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃         DEBATE SUMMARY                  ┃
┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫
┃                                            ┃
┃ Q: какой потенциал у этого проекта?      ┃
┃                                            ┃
┃ A: [final answer content...]             ┃
┃                                            ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

✅ Workflow completed successfully | Status: SUCCESS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**Files**:
- `document_debate_cli.py` (verify ordering)

**Validation**:
- [ ] Summary appears after verdict box
- [ ] Summary appears before success message
- [ ] Blank lines provide visual separation
- [ ] Test run confirms correct order
- [ ] No output duplication or overlapping

**Notes**:
- The verdict shows "who won", the summary shows "what was decided"
- This order provides a complete conclusion to the debate

---

## Test Strategy

**Manual Testing**:
1. Run full CLI with document and question:
   ```bash
   python3 document_debate_cli.py --docx test.docx --request "какой потенциал у этого проекта?"
   ```
2. Verify summary appears after verdict
3. Check formatting is clean and readable
4. Test with `--text` mode as well
5. Verify Russian characters display correctly

**Scenarios**:
- Single question debate → Should show one Q/A pair
- Document-based debate with `--docx --request` → Should show question
- Direct topic with `--text` → Should show question (topic is the question)

---

## Definition of Done

This work package is complete when:
- [ ] `DebateSummaryFormatter` class exists and works
- [ ] Summary displays in CLI after verdict
- [ ] Format matches specification (Q: question, A: answer)
- [ ] Rich styling is applied consistently
- [ ] Output order is correct (verdict → summary → success)
- [ ] No regressions in existing CLI functionality
- [ ] Manual test confirms summary displays correctly

---

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|-------|------------|--------|------------|
| Summary placement feels awkward in output | Medium | Low | Spacing and separation lines help |
| Rich Panel formatting issues | Low | Medium | Tested with existing Rich usage patterns |
| Missing fields cause display issues | Medium | Low | Conditional display and placeholders (T007) |
| Import errors for new cli module | Low | Medium | Verify import path works in project structure |

---

## Reviewer Guidance

**Focus areas for code review**:
1. Summary format matches spec (Q: / A: prefixes)
2. Display order is correct (after verdict, before success message)
3. Rich styling is consistent with existing CLI
4. Error handling for missing fields is present
5. No hardcoded text that should be internationalized later

**Integration points**:
- Reads `original_question` and `final_answer` from state (set by WP01)
- Uses existing Rich Console from CLI
- Called in main CLI flow after verdict display

**Next work package**: WP03 adds edge case handling and validation.

---

## Dependencies

This work package depends on **WP01** because:
- Requires `original_question` field to be available in state
- Requires `final_answer` field to be available in state
- WP01 establishes these state fields before WP02 can display them

Use `--base WP01` when implementing to branch from the completed WP01 work.
