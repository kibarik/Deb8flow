# Feature Specification: PRD Document Debate Workflow

**Feature Number:** 002
**Status:** Draft
**Created:** 2025-02-12

## 1. Feature Overview

### 1.1 Summary

Create a new universal workflow that enables AI agents to analyze any .docx document through structured debate. Users provide a .docx file, and the system extracts text content and generates a comprehensive analysis highlighting both strengths and weaknesses through adversarial discussion between PRO and CON agents. While designed for PRD analysis, the workflow is document-agnostic and can process any .docx content.

### 1.2 Problem Statement

Currently, the Deb8flow system supports debates on internally generated topics. Product teams need an automated way to evaluate PRD documents from multiple perspectives before implementation. Manual review is time-consuming and may miss critical weaknesses or risks.

### 1.3 Proposed Solution

Implement a new `document_debate_workflow.py` as a standalone workflow that:
- Reads PRD content from .docx files
- Conducts structured debate between PRO agent (arguing strengths) and CON agent (arguing weaknesses)
- Maintains the existing 4-stage debate structure (opening, rebuttal, counter, final_argument)
- Includes fact-checking for all claims
- Produces a comprehensive result.md with debate transcript and judge's verdict
- **Does NOT modify the existing `debate_workflow.py` - both workflows coexist independently**

### 1.4 Actors

| Actor | Description |
|-------|-------------|
| Product Manager | Provides .docx PRD file for analysis |
| PRO Agent | AI agent that identifies and argues strengths of the PRD |
| CON Agent | AI agent that identifies and argues weaknesses and risks of the PRD |
| Moderator | Orchestrates debate flow and stage transitions |
| Fact-Checker | Validates claims and statistics mentioned by agents |
| Judge | Evaluates arguments and provides final verdict; assesses both rhetorical performance AND document viability for management presentation |

## Clarifications

### Session 2025-02-13
- Q: The spec mentions creating a new `document_debate_workflow.py` file (Section 1.3), while your implementation plan describes modifying the existing `debate_workflow.py` to accept `initial_state` and replace `GenerateTopicNode`. Which approach should be taken? → A: Create new standalone `document_debate_workflow.py` file keeping existing workflow unchanged
- Q: The spec defines a `DocumentDebateState` entity with attribute `prd_content`, while your implementation plan uses `document_input` and extends the existing `DebateState`. What is the correct state structure? → A: Extend existing `DebateState` with `document_input` field; module should be universal for any .docx content, not PRD-specific
- Q: Your implementation plan reuses existing `topic_generator_prompts` and adds `{document_text}` to debater prompts. Should the prompt strategy be specialized for document analysis or reuse existing generic prompts? → A: Extend existing prompts with document-specific instructions for PRO/CON roles
- Q: Should .docx reading happen only at entry point (main.py) or should the node also handle file paths? → A: Read .docx only in DocumentTopicNode, pass file path from main
- Q: The spec states the judge evaluates "rhetorical performance" (existing behavior), but for document analysis debates, should the judge evaluate the document's business viability instead? → A: Judge evaluates both rhetoric and document viability

## 2. User Scenarios & Testing

### 2.1 Primary Scenario: Analyze New PRD

**Given:** A Product Manager has completed a PRD document in .docx format

**When:** They run the document debate workflow with the PRD file

**Then:**
1. The system extracts text from the .docx file
2. The PRD content is provided to both PRO and CON agents
3. PRO agent presents opening statement highlighting PRD strengths
4. CON agent presents rebuttal highlighting weaknesses
5. Both agents exchange counter-arguments
6. Each statement is fact-checked for accuracy
7. Judge evaluates all arguments and declares winner
8. Result is written to `result.md` in the same format as existing debate workflow

### 2.2 Edge Cases

| Scenario | Expected Behavior |
|----------|------------------|
| Empty .docx file | Workflow exits with error message indicating empty document |
| Corrupted .docx file | Workflow exits with error message indicating file read failure |
| Non-.docx file | Workflow exits with error message indicating unsupported format |
| Very large PRD (>100 pages) | Workflow completes but may take longer; content is truncated if exceeding token limits |
| PRD with no clear requirements | Agents note ambiguity and highlight it as a weakness |

### 2.3 Acceptance Criteria

- [ ] Workflow accepts .docx file path as input
- [ ] Text is correctly extracted from .docx file
- [ ] PRO agent argues PRD strengths specifically
- [ ] CON agent argues PRD weaknesses specifically
- [ ] Fact-checking validates claims after each argument
- [ ] All 4 debate stages complete (opening, rebuttal, counter, final_argument)
- [ ] result.md is generated with same format as existing debate workflow
- [ ] Judge provides final verdict with reasoning

## 3. Functional Requirements

### 3.1 Document Reading

**REQ-001:** The system shall read .docx files and extract text content

**Acceptance Criteria:**
- File path to .docx is passed from main.py via `initial_state`
- DocumentTopicNode handles .docx reading using python-docx library
- Text is extracted preserving paragraph structure
- Tables are converted to readable text format
- Extraction completes within 5 seconds for typical document (1-20 pages)

**REQ-002:** The system shall validate input file before processing

**Acceptance Criteria:**
- File extension must be .docx
- File must be readable
- File must contain non-empty content

### 3.2 Debate Workflow

**REQ-003:** The system shall conduct debate between PRO and CON agents about document content

**Acceptance Criteria:**
- PRO agent focuses exclusively on defending the document's validity (strengths, opportunities, positive aspects)
- CON agent focuses exclusively on critiquing the document (weaknesses, risks, gaps, concerns)
- Both agents reference specific content from the document via `document_text` variable
- Prompts are extended with document-specific instructions for PRO (defend) and CON (critique) roles

**REQ-004:** The system shall maintain the 4-stage debate structure

**Acceptance Criteria:**
- Opening stage: PRO presents initial strengths
- Rebuttal stage: CON presents weaknesses and counter-points
- Counter stage: PRO addresses CON's concerns
- Final Argument stage: CON presents final critique

### 3.3 Fact-Checking

**REQ-005:** The system shall fact-check each agent statement

**Acceptance Criteria:**
- Claims with numbers, statistics, or specific references are validated
- Failed fact-checks require agent revision
- Three consecutive failures result in disqualification

### 3.4 Output Generation

**REQ-006:** The system shall generate result.md with debate transcript

**Acceptance Criteria:**
- Format matches existing debate_workflow.py output
- Includes all agent arguments with stage labels
- Includes fact-check results
- Includes judge's final verdict with winner declaration AND assessment of document viability

## 4. Success Criteria

| Criterion | Metric |
|-----------|--------|
| Analysis completeness | All PRD sections are referenced in debate |
| Output consistency | result.md format matches existing workflow output |
| Processing time | Workflow completes within 3 minutes for typical PRD |
| Actionability | Judge's verdict provides clear, actionable recommendations |

## 5. Key Entities

| Entity | Attributes |
|--------|------------|
| DocumentInput | filepath, content_text (extracted from .docx), extracted_at |
| DebateState (extended) | **document_input** (NEW), debate_topic (derived from document), positions, messages, stage, speaker, opening_statement_pro_agent, times_pro_fact_checked, times_con_fact_checked |
| DebateMessage | speaker, content, validated, stage |
| AnalysisResult | winner, reasoning, strengths_identified, weaknesses_identified, document_viability_assessment |

## 6. Assumptions

1. The .docx file contains a valid PRD with readable text content
2. Users have `python-docx` library installed or will install as dependency
3. PRD content is in a language supported by the configured LLM
4. Existing debate infrastructure (BaseComponent, StateGraph, prompts) can be reused
5. The existing output format is sufficient for PRD analysis results
6. Token limits of the LLM can accommodate typical PRD documents (1-20 pages)

## 7. Dependencies

| Dependency | Type | Description |
|------------|------|-------------|
| python-docx | External | Library for reading .docx files |
| debate_state.py | Internal | Existing state definitions (may need extension) |
| BaseComponent | Internal | Base class for all workflow nodes |
| Existing prompts | Internal | May need adaptation for PRD context |

## 8. Risks & Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| Large PRD exceeds token limits | Medium | Implement content summarization/truncation with warning to user |
| .docx parsing fails for complex formatting | Low | Use robust extraction library; handle errors gracefully |
| Agents generate generic arguments | Medium | Create specialized prompts emphasizing specific PRD content reference |
| Result format differs from expected output | Low | Reuse existing output generation code; test against reference |

## 9. Out of Scope

The following items are explicitly out of scope for this feature:

- Support for other document formats (PDF, markdown, plain text)
- Multi-document comparison debates
- Integration with external project management tools
- Real-time debate streaming
- Web UI for document upload
- Automated PRD generation or improvement suggestions beyond debate analysis
