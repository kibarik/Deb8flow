---
work_package_id: WP01
title: Summary Data Model & State Enhancement
lane: "doing"
dependencies: []
base_branch: main
base_commit: 3ecea4ff3618acf623bc6b6ee9933e30a725c9e5
created_at: '2026-02-13T23:46:39.073070+00:00'
subtasks: [T001, T002, T003, T004, T005]
shell_pid: "48535"
history:
- date: 2026-02-14
  action: Created
  author: spec-kitty.tasks
---

# Work Package: Summary Data Model & State Enhancement

## Implementation Command

```bash
spec-kitty implement WP01
```

## Objective

Enhance the debate state and data model to capture the information needed for summary output. This work package establishes the data foundation for displaying question-answer pairs after debate completion.

## Context

The current `DebateState` TypedDict tracks debate topics and messages but does not explicitly store the original question asked by the user or the final answer determined by the judge. The summary feature requires these two pieces of information to be available in the state when the CLI displays results.

**Key files to modify**:
- `debate_state.py` - Contains the DebateState TypedDict
- `nodes/document_topic_node.py` - Generates topic from document
- `nodes/judge_node.py` - Produces final verdict
- `workflow/document_debate_workflow.py` - Orchestrates the workflow

## Subtasks

### T001: Add `original_question` field to DebateState TypedDict

**Purpose**: Store the user's original question in the debate state for later display in the summary.

**Steps**:
1. Open `debate_state.py`
2. Add `original_question: NotRequired[str]` field to the `DebateState` TypedDict
3. Add a docstring comment explaining the field's purpose:
   ```python
   # The original question/request provided by the user (e.g., from --request CLI argument)
   # Used for summary output to show "Q: {original_question}"
   ```
4. Ensure the field uses `NotRequired[str]` to maintain backward compatibility

**Files**:
- `debate_state.py` (~30 lines modified)

**Validation**:
- [ ] Field added to TypedDict without breaking existing type checks
- [ ] Field is marked as NotRequired for backward compatibility
- [ ] Docstring explains the field's purpose

**Notes**:
- The `original_question` represents what the user asked (e.g., "какой потенциал у этого проекта?")
- This differs from `debate_topic` which is the formatted topic for AI debaters
- Source is typically the `--request` CLI argument

---

### T002: Add `final_answer` field to DebateState to store judge's conclusion

**Purpose**: Store the judge's final answer/verdict in the state for summary display.

**Steps**:
1. Open `debate_state.py`
2. Add `final_answer: NotRequired[str]` field to the `DebateState` TypedDict
3. Add a docstring comment:
   ```python
   # The final answer/verdict determined by the judge after reviewing the debate
   # Used for summary output to show "A: {final_answer}"
   ```
4. Ensure the field uses `NotRequired[str]` for backward compatibility

**Files**:
- `debate_state.py` (~30 lines modified)

**Validation**:
- [ ] Field added to TypedDict
- [ ] Field is marked as NotRequired
- [ ] Docstring clearly explains the field's purpose

**Notes**:
- The `final_answer` should be a concise summary of the judge's reasoning
- This is different from the full `judge_verdict` which contains structured data
- For now, storing the justification text is sufficient

---

### T003: Update DocumentTopicNode to preserve original question in state

**Purpose**: Capture the user's original question when the topic is generated and store it in `original_question`.

**Steps**:
1. Open `nodes/document_topic_node.py`
2. Locate the `__call__` method that returns state updates
3. Check if `state.get("direct_topic")` exists (this is the user's question)
4. If `direct_topic` exists, add it to the return state as `original_question`
5. Also check for `document_context` + `direct_topic` combination (document-based debate with question)
6. Return state update: `{"original_question": state.get("direct_topic", "")}`

**Implementation Example**:
```python
def __call__(self, state: DebateState) -> Dict[str, Any]:
    # ... existing code ...

    # Preserve original question for summary output
    original_question = state.get("direct_topic", "")

    return {
        "debate_topic": generated_topic,
        "original_question": original_question,
        # ... other fields ...
    }
```

**Files**:
- `nodes/document_topic_node.py` (~100 lines, modify return statement)

**Validation**:
- [ ] `direct_topic` is captured and stored as `original_question`
- [ ] Empty string is used as fallback if `direct_topic` doesn't exist
- [ ] State update is returned correctly
- [ ] Existing topic generation logic is not broken

**Edge Cases**:
- No `direct_topic` provided (old behavior with `--docx` only) → use empty string
- Empty `direct_topic` → store as-is (edge case handling in WP03)

---

### T004: Update JudgeNode to extract and store final answer in state

**Purpose**: Parse the judge's verdict and store the justification as `final_answer` in the state.

**Steps**:
1. Open `nodes/judge_node.py`
2. Locate the `__call__` method that processes the verdict
3. After parsing the verdict (using `_parse_verdict_response`), extract the justification
4. Add `final_answer` to the state update return value
5. Use `result.get("justification", "")` as the final answer text

**Implementation Example**:
```python
def __call__(self, state: DebateState) -> Dict[str, Any]:
    # ... existing code to get response ...

    result = self._parse_verdict_response(response)

    return {
        "judge_verdict": result,
        "final_answer": result.get("justification", ""),
        "messages": messages + [{
            "speaker": SPEAKER_JUDGE,
            "content": f"WINNER: {result['winner'].upper()}\n\nREASON: {result['justification']}",
            "validated": True,
            "stage": "verdict"
        }]
    }
```

**Files**:
- `nodes/judge_node.py` (~82 lines, modify return statement)

**Validation**:
- [ ] `justification` from verdict is extracted and stored as `final_answer`
- [ ] Empty string fallback is used if justification is missing
- [ ] Existing verdict message formatting is not broken
- [ ] State update includes both `judge_verdict` and `final_answer`

**Notes**:
- The `justification` field contains the judge's reasoning
- This serves as the "answer" to the user's question
- In future, the judge could be prompted to provide a more direct answer

---

### T005: Add state validation to ensure summary fields are populated

**Purpose**: Add basic validation to ensure the summary fields are populated when expected.

**Steps**:
1. Add a validation function in `workflow/document_debate_workflow.py`
2. The function should check if `original_question` and `final_answer` exist in state
3. Log a warning if either field is missing after workflow completion
4. Call the validation in the `run()` method after `graph.ainvoke()` completes
5. Use the existing logger for warnings

**Implementation Example**:
```python
def _validate_summary_fields(self, state: DebateState) -> None:
    """Validate that summary fields are populated."""
    if not state.get("original_question"):
        logger.warning("original_question not found in state - summary may be incomplete")
    if not state.get("final_answer"):
        logger.warning("final_answer not found in state - summary may be incomplete")
```

**Files**:
- `workflow/document_debate_workflow.py` (~113 lines, add ~10 lines)

**Validation**:
- [ ] Validation function added to workflow class
- [ ] Function is called after workflow completion
- [ ] Warnings are logged for missing fields
- [ ] Validation doesn't break the workflow (only warnings)

**Notes**:
- This is defensive logging to help debug issues
- Missing fields are not errors (WP03 handles edge cases)
- Uses existing logger from the workflow

---

## Test Strategy

**Manual Testing Approach**:
1. Run the CLI with a simple debate: `python3 document_debate_cli.py --docx test.docx --request "What is X?"`
2. Add debug logging to print state after workflow completion
3. Verify `original_question` equals "What is X?"
4. Verify `final_answer` contains the judge's justification
5. Run with `--text` mode and verify same behavior

**No automated tests** are required for this work package unless explicitly requested.

---

## Definition of Done

This work package is complete when:
- [ ] Both `original_question` and `final_answer` fields exist in `DebateState`
- [ ] `DocumentTopicNode` captures and stores the original question
- [ ] `JudgeNode` extracts and stores the final answer
- [ ] Validation warnings are logged for missing fields
- [ ] Existing workflow functions without errors
- [ ] Type checks pass with the new TypedDict fields
- [ ] Manual test confirms state contains both fields after a debate

---

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|-------|------------|--------|------------|
| TypedDict changes break type checking | Medium | Medium | Used `NotRequired` for backward compatibility |
| JudgeNode parsing fails to extract justification | Low | Medium | Empty string fallback, existing parser is robust |
| State fields are not populated in some execution paths | Medium | Low | Validation logging helps debug; WP03 handles edge cases |

---

## Reviewer Guidance

**Focus areas for code review**:
1. TypedDict changes maintain backward compatibility (`NotRequired`)
2. State updates are correctly returned from nodes
3. Validation doesn't break workflow flow
4. Field naming is consistent (`original_question`, `final_answer`)

**Integration points**:
- `DocumentTopicNode` → sets `original_question`
- `JudgeNode` → sets `final_answer`
- CLI (WP02) → reads both fields for summary

**Next work package**: WP02 uses these fields to display the summary in the CLI.
