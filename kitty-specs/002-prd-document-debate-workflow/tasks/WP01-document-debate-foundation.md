---
work_package_id: WP01
title: Document Debate Workflow Foundation
lane: "done"
dependencies: []
base_branch: main
base_commit: 16ba55b33084323debb536425288c6df02fa10ba
created_at: '2026-02-12T21:26:28.342098+00:00'
subtasks:
- T001
- T002
- T003
- T004
- T005
- T006
- T007
- T008
- T009
- T010
- T011
description: Document Debate Workflow Foundation - Establish state extensions, document processing node, and CLI integration
shell_pid: "32923"
agent: "claude"
reviewed_by: "ALeks ishmanov"
review_status: "approved"
---

## Objective

Establish the foundational components for the document debate workflow. This work package creates the infrastructure needed for AI agents to analyze .docx documents through structured debate: state extensions, document processing, prompt modifications, workflow orchestration, CLI integration, and contract compliance tests.

**After this WP:**
- DocumentTopicNode can be created and used in workflow
- PRO/CON agents can reference document content in their arguments
- Judge can assess document viability alongside rhetorical performance
- Users can run workflow via `--docx` CLI argument

## Context

**Feature:** 002-prd-document-debate-workflow
**Plan:** [plan.md](../plan.md)
**Spec:** [spec.md](../spec.md)
**Research:** [research.md](../research.md)
**Data Model:** [data-model.md](../data-model.md)
**Contracts:**
- [debate_state.py.md](../contracts/debate_state.py.md)
- [document_topic_node.py.md](../contracts/document_topic_node.py.md)
- [debater_prompts.py.md](../contracts/debater_prompts.py.md)
- [judge_node.py.md](../contracts/judge_node.py.md)

**Quickstart:** [quickstart.md](../quickstart.md)

## Implementation Strategy

**Key Design Decisions:**
1. **New standalone workflow** - `document_debate_workflow.py` does not modify existing `debate_workflow.py`
2. **State extension** - Add `document_input: NotRequired[str]` to `DebateState`
3. **Document processing** - `DocumentTopicNode` reads .docx files using `python-docx`
4. **Prompt extensions** - Add `{document_text}` variable to all debater prompts
5. **Judge enhancement** - Evaluate both rhetoric AND document viability

## Subtasks

### T001: Extend DebateState with document_input field

**Purpose:** Add `document_input` field to existing `DebateState` TypedDict to support document input throughout the workflow.

**Files:**
- `src/models/debate_state.py` (modify)
- `workflow/debate/document_debate_workflow.py` (will use extended state)

**Steps:**
1. Open `src/models/debate_state.py`
2. Add `document_input: NotRequired[str]` field to the `DebateState` TypedDict
3. Update type hints if present
4. Verify backward compatibility with existing `debate_workflow.py`

**Validation:**
- [ ] Field added to TypedDict with correct type annotation
- [ ] Existing `debate_workflow.py` still compiles (no breaking changes)
- [ ] New `document_debate_workflow.py` can import and use extended state

**Guidance:**
- Use `NotRequired[str]` to allow optional document input
- Preserve all existing fields for backward compatibility
- Add docstring explaining the new field

---

### T002: Add python-docx dependency

**Purpose:** Add `python-docx` library for reading .docx files.

**Files:**
- `pyproject.toml` (modify)

**Steps:**
1. Open `pyproject.toml`
2. Add `python-docx` to dependencies list
3. Optionally update to requirements.txt if present

**Validation:**
- [ ] Dependency added to pyproject.toml
- [ ] Version pin specified (use latest stable)
- [ ] Installation test passes

**Guidance:**
- Use latest stable version from python-docx
- Consider version pinning if stability issues arise
- No specific version constraints per research.md

---

### T003: Create DocumentTopicNode for .docx processing

**Purpose:** Create new node to replace `GenerateTopicNode` that reads .docx documents and generates debate topics from document content.

**Files:**
- `src/nodes/document_topic_node.py` (create)
- `prompts/document_topic_prompts.py` (may modify - add document_text variable)

**Steps:**
1. Create `src/nodes/document_topic_node.py`
2. Inherit from `BaseComponent`
3. Implement `__call__` method:
   - Extract `document_input` from state
   - Check if value ends with `.docx`
   - If yes, read file using `Document()` from python-docx
   - Extract text: `"\n".join(p.text for p in doc.paragraphs)`
   - Pass extracted text to LLM for topic generation
4. Return state with:
   - `debate_topic`: Generated topic
   - `positions`: {"pro": "In favor", "con": "Against"}
   - `stage`: "opening"
   - `speaker`: "pro"

**Validation:**
- [ ] Node created with correct class structure
- [ ] Inherits from BaseComponent properly
- [ ] Handles .docx file reading
- [ ] Handles pre-extracted text gracefully
- [ ] Returns correct state structure

**Guidance:**
- Use `__name__ = "document_topic_node"` for workflow routing
- Handle both file paths and pre-extracted text
- Implement error handling for corrupted files

---

### T004: Extend PRO/CON debater prompts with document context

**Purpose:** Extend existing debater prompts to include document context for specialized document debate roles.

**Files:**
- `src/prompts/pro_debater_prompts.py` (modify)
- `src/prompts/con_debater_prompts.py` (modify)

**Steps:**
1. Open both prompt files
2. Add `{document_text}` variable to all prompt templates
3. Update prompt instructions to reflect document-specific roles:
   - **PRO agent:** Defend document's validity, strengths, opportunities
   - **CON agent:** Critique document's weaknesses, risks, gaps

**PRO Prompts to Modify:**
- `OPENING_HUMAN_PROMPT` - Add document context and defense role
- `OPENING_RETRY_HUMAN_PROMPT` - Add document context and defense role
- `COUNTER_HUMAN_PROMPT` - Add document context and defense role
- `COUNTER_RETRY_HUMAN_PROMPT` - Add document context and defense role

**CON Prompts to Modify:**
- `REBUTTAL_HUMAN_PROMPT` - Add document context and critique role
- `REBUTTAL_RETRY_HUMAN_PROMPT` - Add document context and critique role
- `FINAL_ARGUMENT_HUMAN_PROMPT` - Add document context and critique role
- `FINAL_ARGUMENT_RETRY_HUMAN_PROMPT` - Add document context and critique role

**Validation:**
- [ ] All prompts include `{document_text}` variable
- [ ] PRO prompts emphasize defending the document
- [ ] CON prompts emphasize critiquing the document
- [ ] Existing `{debate_topic}` variable preserved
- [ ] Existing `{opponent_statement}` variable preserved
- [ ] Existing `{debate_history}` variable preserved

**Guidance:**
- Keep existing `SYSTEM_PROMPT` unchanged
- Place `{document_text}` after `{debate_topic}` for flow
- Use clear role instructions in prompt text

---

### T005: Extend JudgeNode with document viability assessment

**Purpose:** Extend JudgeNode to evaluate document business viability in addition to rhetorical performance.

**Files:**
- `src/nodes/judge_node.py` (modify)
- `prompts/judge_prompts.py` (may modify)

**Steps:**
1. Update `DebateVerdict` model to include `document_viability: str`
2. Update `JUDGE_HUMAN_PROMPT` to:
   - Include `{document_text}` variable
   - Add instruction to evaluate document viability
   - Request clear viability assessment (e.g., "Ready for presentation", "Needs significant rework")
3. Update `__call__` method to pass `document_input` to chain
4. Update final message format to include viability assessment

**Validation:**
- [ ] `DebateVerdict` includes `document_viability` field
- [ ] Prompt includes document context
- [ ] Prompt instructs evaluation of both rhetoric AND viability
- [ ] Final verdict message includes viability assessment
- [ ] Existing `debate_workflow.py` output format preserved

**Guidance:**
- Viability assessment should be actionable for product managers
- Consider document quality levels in prompt guidance
- Maintain backward compatibility with existing verdict format

---

### T006: Create document_debate_workflow.py orchestration

**Purpose:** Create standalone workflow orchestration with DocumentTopicNode replacing GenerateTopicNode.

**Files:**
- `workflow/debate/document_debate_workflow.py` (create)

**Steps:**
1. Create `workflow/debate/` directory if needed
2. Create `document_debate_workflow.py`:
   - Import `StateGraph` from langgraph
   - Import `DocumentTopicNode` as `document_topic_node`
   - Import existing nodes: ProDebaterNode, ConDebaterNode, etc.
   - Import `DebateState` (extended with `document_input`)
   - Define `DocumentDebateWorkflow` class
   - In `_initialize_workflow()` method:
     - Create `StateGraph(DebateState)`
     - Add `document_topic_node` node with `DocumentTopicNode(llm_config)`
     - Add all other nodes (pro_debater_node, con_debater_node, etc.)
     - Set entry point to `document_topic_node`
     - Add edges from document_topic_node to pro_debater_node
     - Add conditional edge to judge_node after debate stages
   - Implement `run()` method:
     - Accept optional `initial_state` parameter
     - Pass `initial_state` to `graph.ainvoke()`
     - Return final_state

**Validation:**
- [ ] Workflow file created in correct location
- [ ] Uses `StateGraph(DebateState)` with extended state
- [ ] Entry point set to `document_topic_node`
- [ ] Accepts `initial_state` parameter
- [ ] All existing nodes imported and wired correctly
- [ ] Returns final_state after graph execution

**Guidance:**
- Use `__name__ = "document_topic_node"` for the new node
- Preserve existing node structure for all other components
- Ensure `initial_state` defaults are compatible with new entry point
- Do NOT modify existing `debate_workflow.py`

---

### T007: Update main.py CLI with --docx argument

**Purpose:** Update CLI to accept `--docx` argument and pass document to workflow.

**Files:**
- `src/cli/main.py` (modify)

**Steps:**
1. Add `--docx` argument to argparse
2. Implement .docx file reading using python-docx:
   - `doc = Document(args.docx)`
   - `doc_text = "\n".join(p.text for p in doc.paragraphs)`
3. Pass `document_input` via `initial_state`:
   - `initial_state={"document_input": doc_text}`
4. Handle errors gracefully:
   - File not found
   - Corrupted file
   - Empty file

**Validation:**
- [ ] `--docx` argument added and required
- [ ] .docx file reading implemented correctly
- [ ] `document_input` passed via initial_state
- [ ] Error messages are clear and actionable
- [ ] Existing `debate_workflow.py` invocation pattern preserved

**Guidance:**
- Use `required=True` for --docx argument
- Provide helpful error message for missing files
- Support both file paths and pre-extracted text for flexibility

---

### T008: Add contract test for DebateState extension

**Purpose:** Test that DebateState extension works correctly with workflow.

**Files:**
- `tests/contract/test_debate_state.py` (create)

**Steps:**
1. Create test file
2. Import extended `DebateState`
3. Test `document_input` field:
   - Verify field exists
   - Verify type annotation
   - Test optional behavior (NotRequired)
4. Test backward compatibility:
   - Ensure existing fields still work
   - Verify serialization with LangGraph

**Validation:**
- [ ] Test file created
- [ ] Tests verify `document_input` field behavior
- [ ] Tests confirm LangGraph compatibility
- [ ] All tests passing

**Guidance:**
- Test with both file paths and pre-extracted text
- Verify state can be passed through all workflow stages
- Use LangGraph's state validation

---

### T009: Add contract test for DocumentTopicNode

**Purpose:** Test that DocumentTopicNode fulfills its contract correctly.

**Files:**
- `tests/contract/test_document_topic_node.py` (create)

**Steps:**
1. Create test file
2. Mock `Document` class from python-docx
3. Test `__call__` method:
   - File path reading (`.docx` ending check)
   - Document text extraction
   - LLM chain invocation with document_text
   - Return state structure
4. Test error handling:
   - Empty document input
   - Corrupted file handling
   - Non-.docx file handling

**Validation:**
- [ ] Test file created
- [ ] Node correctly processes .docx files
- [ ] Node correctly handles pre-extracted text
- [ ] Error cases handled appropriately
- [ ] Returns correct state structure

**Guidance:**
- Mock python-docx Document to avoid file I/O
- Verify topic generation from document content
- Test with various document types (empty, large, etc.)

---

### T010: Add contract test for debater prompt extensions

**Purpose:** Test that debater prompt extensions include document context correctly.

**Files:**
- `tests/contract/test_debater_prompts.py` (create)

**Steps:**
1. Create test file
2. Import extended prompts
3. Test all prompt templates:
   - Verify `{document_text}` variable present
   - Verify PRO role instructions (defend document)
   - Verify CON role instructions (critique document)
4. Test prompt variable substitution
5. Verify existing variables preserved (`{debate_topic}`, `{opponent_statement}`, `{debate_history}`)

**Validation:**
- [ ] Test file created
- [ ] All prompts include `{document_text}` variable
- [ ] PRO prompts emphasize defending the document
- [ ] CON prompts emphasize critiquing the document
- [ ] Existing variables remain functional
- [ ] Prompt instructions are clear

**Guidance:**
- Test with mock chain invocations
- Verify role clarity in prompt text
- Test variable substitution behavior

---

### T011: Add contract test for JudgeNode extension

**Purpose:** Test that JudgeNode extension includes document viability assessment.

**Files:**
- `tests/contract/test_judge_node.py` (create)

**Steps:**
1. Create test file
2. Import extended `DebateVerdict` model
3. Test `__call__` method:
   - Verify `document_input` passed to chain
   - Verify document_viability field in result
4. Test verdict output includes viability assessment
5. Verify prompt includes document context and viability instructions

**Validation:**
- [ ] Test file created
- [ ] `DebateVerdict` includes `document_viability` field
- [ ] Prompt includes `{document_text}` variable
- [ ] Prompt instructs evaluation of both rhetoric AND viability
- [ ] Final message format includes viability
- [ ] Existing verdict structure preserved

**Guidance:**
- Test with various document qualities (good, bad, mixed)
- Verify viability assessment is actionable
- Test backward compatibility with existing workflow output

## Testing Strategy

**Independent Tests:**
- Each contract test file verifies its respective component independently
- Tests use mocking to isolate unit under test
- No integration tests included in this work package

**Definition of Done:**
- All subtasks T001-T011 implemented
- All contract tests passing
- Components integrate correctly in workflow

## Activity Log

- 2026-02-12T21:26:51Z – claude – shell_pid=32923 – lane=doing – Assigned agent via workflow command
- 2026-02-13T21:14:47Z – claude – shell_pid=32923 – lane=for_review – Moved to for_review
- 2026-02-13T21:14:55Z – claude – shell_pid=32923 – lane=done – Implementation complete: All contract tests (9), E2E tests (10), and full workflow demo passed. Document debate workflow is fully functional.
