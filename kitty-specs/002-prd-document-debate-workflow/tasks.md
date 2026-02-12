# Work Packages: PRD Document Debate Workflow

**Feature:** 002-prd-document-debate-workflow
**Branch:** `###-002-prd-document-debate-workflow`
**Generated:** 2025-02-13

## Overview

This feature implements a standalone document debate workflow for analyzing .docx files through adversarial AI debate. The work is organized into a single work package (WP01) encompassing all foundational and implementation tasks.

---

## Work Package: WP01 - Document Debate Foundation

**Title:** Document Debate Workflow Foundation
**Work Package ID:** WP01
**Priority:** P0 (Foundation)
**Lane:** planned
**Dependencies:** None
**Parallel:** No

**Goal:** Establish project skeleton and shared tooling for the document debate workflow, including state extensions, new nodes, and CLI integration.

### Summary

Create the foundational components for the document debate workflow:
1. Extend `DebateState` with `document_input` field
2. Add `python-docx` dependency for .docx file reading
3. Create `DocumentTopicNode` to replace `GenerateTopicNode` for document-based topics
4. Extend PRO and CON debater prompts with document context
5. Extend `JudgeNode` to assess document viability alongside rhetorical performance
6. Create `document_debate_workflow.py` orchestration with new node
7. Update `main.py` CLI to accept `--docx` argument
8. Add contract compliance tests for all new components

### Included Subtasks

| ID | Description | Parallel | Files |
|----|-------------|----------|--------|
| T001 | Extend DebateState with document_input field | No | `src/models/debate_state.py` (modify), `workflow/debate/document_debate_workflow.py` |
| T002 | Add python-docx dependency | No | `pyproject.toml` |
| T003 | Create DocumentTopicNode for .docx processing | No | `src/nodes/document_topic_node.py`, `prompts/document_topic_prompts.py` |
| T004 | Extend PRO/CON debater prompts with document context | No | `src/prompts/pro_debater_prompts.py`, `src/prompts/con_debater_prompts.py` |
| T005 | Extend JudgeNode with document viability assessment | No | `src/nodes/judge_node.py`, `prompts/judge_prompts.py` |
| T006 | Create document_debate_workflow.py orchestration | No | `workflow/debate/document_debate_workflow.py` |
| T007 | Update main.py CLI with --docx argument | No | `src/cli/main.py` |
| T008 | Add contract test for DebateState extension | Yes | `tests/contract/test_debate_state.py` |
| T009 | Add contract test for DocumentTopicNode | Yes | `tests/contract/test_document_topic_node.py` |
| T010 | Add contract test for debater prompt extensions | Yes | `tests/contract/test_debater_prompts.py` |
| T011 | Add contract test for JudgeNode extension | Yes | `tests/contract/test_judge_node.py` |

### Implementation Notes

**Sequential Requirements:**
- T001 must complete before T003 can use `document_input` in prompts
- T002 must complete before T006 can import `DocumentTopicNode`
- T003 and T004 should complete in parallel (independent prompt modifications)
- T006 through T008 can complete in parallel once T002 and T003 are done
- T009-T011 can proceed after T007 workflow is created

### Implementation Sketch

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│ T001: Extend DebateState                                       │
│   - Add document_input: NotRequired[str] field                 │
│   - Update type hints                                         │
│   - Verify backward compatibility                               │
└───────────────────────┬─────────────────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│ T002: Add python-docx dependency                              │
│   - Update pyproject.toml                                    │
│   - Add to requirements.txt                                  │
└───────────────────────┬─────────────────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│ T003: Create DocumentTopicNode                                │
│   - Inherits from BaseComponent                               │
│   - Implements __call__ with .docx reading                   │
│   - Uses topic_generator_prompts with document_text variable     │
│   - Returns debate_topic, stage="opening", speaker="pro"        │
└───────────────────────┬─────────────────────────────────────────────────────┘
                       │
         ┌───────────────┴───────────────┐
         │                           │
         ▼                           ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│ T004: Extend Debater Prompts                            │
│   - Add document_text variable to all prompts                │
│   - PRO: defend document, CON: critique document             │
│   - Update system prompts if needed                         │
└───────────────────────────────────────────────────────────────────────────┬─────────────┘
                                                           │
                                                           ▼
                                      ┌─────────────────────────────────────────────────────────────────────────────┐
                                      │ T006: Create document_debate_workflow.py                   │
                                      │   - New standalone workflow file                          │
                                      │   - Replaces GenerateTopicNode with DocumentTopicNode         │
                                      │   - Adds node with __name__ = "document_topic_node"        │
                                      │   - Accepts initial_state with document_input                 │
                                      │   - Maintains 4-stage debate structure                    │
                                      └───────────────────────────────┬─────────────────────────────────┘
                                                             │
                                                             ▼
                                            ┌─────────────────────────────────────────────────────────────────────────────────────┐
                                            │ T005: Extend JudgeNode                            │
                                            │   - Add document_viability to DebateVerdict model           │
                                            │   - Extend prompts to include document context                │
                                            │   - Update verdict output to include viability assessment       │
                                            └───────────────────────────────────────────────────────────────────────────────┘
                                                          │
                                                          ▼
                                        ┌─────────────────────────────────────────────────────────────────────────────────────┐
                                        │ T007: Update main.py CLI                           │
                                        │   - Add --docx argument                               │
                                        │   - Pass document_input via initial_state                 │
                                        │   - Read .docx file if needed                           │
                                        │   - Handle errors gracefully                             │
                                        └───────────────────────────────────────────────────────────────────────────────┘
                                                              │
                                                              ▼
                                                   ┌─────────────────────────────────────────────────────────────────────────────────────┐
                                                   │ T008-T011: Contract Tests                          │
                                                   │   - test_debate_state.py: Verify state extension           │
                                                   │   - test_document_topic_node.py: Verify node contract         │
                                                   │   - test_debater_prompts.py: Verify prompt extensions        │
                                                   │   - test_judge_node.py: Verify judge extension            │
                                                   └───────────────────────────────────────────────────────────────────────────────┘
                                                              │
                                                                ▼
                                                   End of WP01
```

### Dependencies

- None (foundation work package)

### Parallel Opportunities

- T003 (DocumentTopicNode creation) and T004 (prompt extensions) can proceed in parallel once T001 (state extension) is complete
- T005 (workflow) and T006 (judge extension) can proceed in parallel once T002 (DocumentTopicNode) exists
- T007 (CLI) can proceed independently
- T008-T011 (contract tests) must complete after their respective implementations

### Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| python-docx installation may fail | Provide clear error message to user; verify in setup tests |
| DocumentTopicNode may not handle all .docx formats | Test with various .docx files; graceful error handling |
| Prompt extensions may not propagate correctly | Contract tests verify document_text variable is present |
| Large documents exceed token limits | Implement content truncation with warning; document in quickstart |
| Judge viability assessment may be generic | Provide clear guidelines in prompt; test with varied document quality |

### Definition of Done

- [ ] All subtasks T001-T011 implemented
- [ ] `python-docx` dependency added successfully
- [ ] DocumentTopicNode can read .docx and extract text
- [ ] PRO agent references document in arguments
- [ ] CON agent references document in arguments
- [ ] Judge includes document viability assessment
- [ ] CLI accepts --docx argument
- [ ] Result.md generated with all components
- [ ] All contract tests passing
- [ ] Integration test passes end-to-end workflow
