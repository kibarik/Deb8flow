# Research: PRD Document Debate Workflow

**Feature:** 002-prd-document-debate-workflow
**Date:** 2025-02-13

## Summary

This feature adapts the existing Deb8flow multi-agent debate system to accept and analyze .docx documents. Key technical decisions confirmed during clarification session.

## Decisions

### Decision 1: Workflow Architecture
**Choice:** Create new standalone `document_debate_workflow.py`
**Rationale:** Keeps existing workflow unchanged, allows both workflows to coexist independently
**Alternatives Considered:**
- Modify existing `debate_workflow.py` (rejected: would break existing functionality)
- Use inheritance/base class (rejected: unnecessary complexity for single use case)

### Decision 2: State Management
**Choice:** Extend existing `DebateState` with `document_input` field
**Rationale:** Reuses proven state structure, maintains compatibility with existing nodes
**Implementation:** Add `document_input: str` to `DebateState` TypedDict

### Decision 3: Document Reading Location
**Choice:** Read .docx in `DocumentTopicNode`, pass file path from main
**Rationale:** Centralizes document processing logic in the node that generates the topic
**Implementation:** `DocumentTopicNode` checks if `document_input` ends with `.docx` and extracts text

### Decision 4: Prompt Strategy
**Choice:** Extend existing prompts with document-specific instructions
**Rationale:** Minimal changes to existing prompt structure, clear separation of concerns
**Implementation:**
- PRO agent: defend document's validity, strengths, opportunities
- CON agent: critique document's weaknesses, risks, gaps
- Add `{document_text}` variable to all debater prompt chains

### Decision 5: Judge Evaluation Criteria
**Choice:** Judge evaluates both rhetoric AND document viability
**Rationale:** Document analysis requires assessing business viability, not just rhetorical skill
**Implementation:** Extend `JudgeNode` prompts to include document content and viability assessment

## Technology Choices

### python-docx
**Purpose:** Reading .docx files
**Version:** Latest stable
**Alternatives:** `python-docx` (selected - de facto standard), `docx2txt` (rejected - loses formatting)

### LangGraph StateGraph
**Purpose:** Workflow orchestration
**Version:** Existing in codebase
**Rationale:** Proven infrastructure, no changes needed

### OpenAI LLM (gpt-4.1)
**Purpose:** Topic generation, debate arguments, verdict
**Version:** Existing in codebase
**Note:** Token limits adequate for typical documents (1-20 pages)

## Integration Patterns

### Reuse BaseComponent
All new nodes inherit from existing `BaseComponent` class for:
- Chain creation (`create_chain`)
- Execution with retry logic (`execute_chain`)
- Token tracking

### Reuse Existing Prompts
Base prompts extended with document context:
- `SYSTEM_PROMPT`: Generic debate instruction (kept as-is)
- Human prompts: Add `{document_text}` variable alongside existing `{debate_topic}`, `{opponent_statement}`, `{debate_history}`

## Dependencies Resolved

- **DebateState extension:** Add `document_input: str` field
- **DocumentTopicNode creation:** New node in `nodes/document_topic_node.py`
- **Prompt modifications:** Update `pro_debater_prompts.py` and `con_debater_prompts.py`
- **main.py changes:** Add `--docx` argument, pass `document_input` via `initial_state`
- **Workflow changes:** `document_debate_workflow.py` with `DocumentTopicNode` replacing `GenerateTopicNode`

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Large documents exceed token limits | Implement content truncation with warning to user |
| .docx parsing fails for complex formatting | Handle errors gracefully, provide clear error messages |
| Generic arguments instead of document-specific | Use specialized prompts emphasizing document content reference |
