---
work_package_id: WP04
title: Self-Reflection Integration
lane: planned
dependencies: []
subtasks:
- T021
- T022
- T023
- T024
phase: Foundation
---

## Work Package Prompt: WP04 – Self-Reflection Integration

**Summary**: Implement TPM self-reflection subprocess call that consumes PRD, question, and all successful room results, then generates reflection JSON with learned insights and recommendations. This WP completes the core orchestration flow before report generation.

**Priority**: P1 (Reflection - required for report generation)

**Phase**: Foundation

**Independent Test**: Reflection subprocess can be invoked with mock room data and produces valid `tpm_reflection.json` per schema.

## Context & Constraints

**Reference Documents**:
- [spec.md](spec.md) - Functional requirements FR-008 through FR-012
- [plan.md](plan.md) - Section 0.5 "Self-Reflection Prompt Research"
- [data-model.md](data-model.md) - TPMReflection entity definition
- [contracts/reflection_schema.json](contracts/reflection_schema.json) - Target JSON structure

**Architectural Decisions**:
- **Subprocess approach**: Reuse subprocess wrapper from WP02 for LLM invocation
- **Prompt location**: `prompts/tpm_reflection.txt` (new file)
- **Input aggregation**: Collect only successful rooms (status == "success") for reflection
- **Graceful degradation**: If 0 rooms succeed, reflection still runs with explicit note about lack of perspectives

**Constraints**:
- Must not modify existing `document_debate_cli.py` (use subprocess only)
- Reflection prompt must request JSON output matching schema
- Timeout should be generous (debates are long-form content)

## Subtasks & Detailed Guidance

### Subtask T021 – Create TPM self-reflection prompt

**Purpose**: Establish structured prompt that instructs LLM to synthesize insights from multiple room perspectives.

**Steps**:
1. Create `prompts/tpm_reflection.txt` with:
   - Clear role definition for TPM in synthesis mode
   - Input specification: PRD text, question, room JSONs
   - Output requirements: JSON format matching `reflection_schema.json`
   - Explicit instructions on handling missing perspectives (if 0 rooms succeeded)
   - Required output sections:
     * `learned_insights`: What TPM learned from each role
     * `potential_assessment`: Updated project potential view (overall + confidence)
     * `recommendations`: Concrete, actionable recommendations for PRD author
     * `argument_decisions`: Which arguments TPM accepts/rejects and why
     * `missing_perspectives`: Notes on which perspectives are absent
     * `hypotheses_to_test`: Suggested hypotheses to validate
     * `risks_prioritized`: Key risks with severity and mitigation
2. Add instructions for structured JSON output
3. Include example input/output for clarity

**Files**:
- `prompts/tpm_reflection.txt` (new file, ~200 lines)

**Validation**:
- [ ] Prompt exists at `prompts/tpm_reflection.txt`
- [ ] Prompt requests JSON output format
- [ ] Prompt handles case with 0 successful rooms
- [ ] All required output sections specified

**Notes**:
- Reflection prompt is distinct from debate prompts (synthesis mode vs. adversarial mode)
- Prompt quality directly impacts reflection JSON quality and final report quality
- Consider adding "think step by step" instructions for complex synthesis

---

### Subtask T022 – Implement reflection subprocess invocation

**Purpose**: Create subprocess wrapper that invokes LLM with reflection prompt and parses JSON output.

**Steps**:
1. Create `run_reflection(prd_path, question, room_results, model=None, timeout=None)` function
2. Read `prompts/tpm_reflection.txt` content
3. Prepare input aggregation:
   - PRD content (read from file)
   - Question string
   - Successful room results (filtered list: [r for r in room_results if r.status == "success"])
   - Room count information (e.g., "3 of 4 rooms succeeded")
4. Call subprocess.run() with:
   - Command: `[sys.executable, document_debate_cli.py, --docx, prd_path, --request, reflection_prompt, --capture-output-only, --model, model]`
   - Capture output: capture_output=True
   - Timeout: timeout or 600 seconds default
   - Text: text=True
5. Parse JSON output from stdout
6. Return `TPMReflection` TypedDict (or appropriate structure) with fields:
   - timestamp, learned_insights, potential_assessment, recommendations, argument_decisions
   - missing_perspectives, hypotheses_to_test, risks_prioritized

**Files**:
- `product_committee.py` (modify, add ~150 lines)
- Add from product_committee.wp04 import run_reflection, TPMReflection

**Validation**:
- [ ] Function accepts all required parameters
- [ ] Only successful rooms passed to reflection
- [ ] Reflection prompt loaded correctly
- [ ] JSON output parsed into structured result
- [ ] Timestamp in ISO 8601 format

**Parallel?**: No (single LLM call)

**Notes**:
- Reuse subprocess wrapper patterns from WP02
- Consider making reflection prompt configurable via `--reflection-prompt` flag (future enhancement)
- Timeout should be longer than rooms (reflection is more complex synthesis)

---

### Subtask T023 – Parse reflection JSON output

**Purpose**: Parse subprocess stdout into structured `TPMReflection` object matching schema.

**Steps**:
1. Create `parse_reflection_json(output: str, room_count: int)` function
2. Use `json.loads()` to parse stdout
3. Validate parsed JSON against `contracts/reflection_schema.json`:
   - All required fields present
   - Data types match (strings, arrays, objects)
   - Enum values valid
4. Extract and return structured data
5. Handle parse errors gracefully:
   - Invalid JSON: Return TPMReflection with error_message field
   - Validation failures: Log warning, return TPMReflection with validation_errors field

**Files**:
- `product_committee.py` (modify, add ~80 lines)
- Add parse_reflection_json() function
- Add from contracts.reflection_schema import (for validation reference)

**Validation**:
- [ ] Valid JSON parses correctly
- [ ] Invalid JSON returns error structure
- [ ] Validation failures logged
- [ ] Returns TPMReflection TypedDict or appropriate structure

**Parallel?**: No (single function)

**Notes**:
- JSON validation is MVP only (presence checks); full schema validation is enhancement
- Parse errors should not crash orchestrator
- Consider schema validation library (jsonschema) for future

---

### Subtask T024 – Handle zero-successful-rooms edge case

**Purpose**: Ensure reflection can run even when all 4 rooms fail, with appropriate prompt adaptation.

**Steps**:
1. Modify `run_reflection()` to detect successful_room_count
2. If successful_room_count == 0:
   - Add explicit context to reflection prompt: "All 4 debate rooms failed. Please note the lack of diverse perspectives in your response."
   - Set special_flag="no_perspectives" in TPMReflection output
3. Update reflection prompt instructions:
   - Request acknowledgment of zero successful rooms
   - Ask for recommendations based only on PRD and question
   - Suggest running rooms again after addressing issues
4. Handle TPMReflection output parsing with no room data
5. Log warning in verbose mode: "Reflection proceeding with 0 successful rooms"

**Files**:
- `prompts/tpm_reflection.txt` (modify, add ~30 lines)
- `product_committee.py` (modify, add ~40 lines)

**Validation**:
- [ ] special_flag="no_perspectives" set when zero rooms succeed
- [ ] Reflection prompt adapted with zero-room context
- [ ] Parsing handles missing learned_insights gracefully
- [ ] Warning logged in verbose mode

**Parallel?**: No (single function modification)

**Notes**:
- This is graceful degradation per spec requirements
- Zero rooms is extreme edge case; test thoroughly

---

## Test Strategy

Not applicable for this WP (tested in WP06).

## Risks & Mitigations

**Risk**: Reflection prompt quality directly impacts report quality.
- **Mitigation**: Invest time in crafting clear, structured prompt with examples

**Risk**: Zero successful rooms case produces limited reflection.
- **Mitigation**: Test edge case explicitly; add prompt context for no perspectives

**Risk**: JSON parsing may be fragile for complex LLM output.
- **Mitigation**: Add robust error handling; log raw output for debugging

## Review Guidance

**Acceptance Criteria**:
- [ ] TPM can invoke reflection subprocess with successful room data
- [ ] Reflection subprocess produces valid JSON output
- [ ] Reflection JSON parsed into TPMReflection structure
- [ ] Zero-successful-rooms case handled gracefully
- [ ] Reflection result includes all required fields per schema

**Key Checkpoints**:
- Reflection prompt requests JSON output explicitly
- Successful room filtering is correct (only status == "success")
- Subprocess wrapper reused from WP02
- Edge case for zero successful rooms is handled
- Timestamp formats match ISO 8601 standard

**Context for Reviewers**:
- Reflection is synthesis step, not adversarial debate
- Prompt quality matters more than room prompts (synthesis requires clarity)
- Zero-room edge case is unlikely but must be handled
