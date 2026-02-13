# TPM-CPO Product Funding Debate Workflow

**Feature Number**: 003
**Status**: Draft
**Mission**: software-dev

## Overview

A debate workflow that simulates a product funding decision conversation between a Technical Product Manager (TPM) advocating for project launch and a Chief Product Officer (CPO) evaluating completeness, value, and resource allocation. The workflow accepts any text-based Product Requirement Document (PRD) as input and orchestrates a structured debate with fact-checking and a final verdict.

## User Problem Statement

Product teams need a structured way to evaluate project proposals before committing resources. Current evaluation lacks rigorous debate and validation of claims made in PRDs. Decisions are often made based on incomplete information or unverified assumptions about market size, competitive landscape, technical feasibility, and resource requirements.

## Goals

### Primary Goals
- Enable structured debate between TPM (project advocate) and CPO (resource steward) about project funding
- Validate claims made in PRD documents through fact-checking
- Provide a reasoned verdict on whether a project should receive funding

### Secondary Goals
- Expose gaps and assumptions in product proposals
- Create an auditable record of the funding decision rationale
- Reuse existing debate orchestration patterns from `debate_workflow.py`

## Out of Scope

- Direct integration with project management tools (Jira, Linear, etc.)
- Automatic resource allocation or budgeting
- Real-time human-in-the-loop debate participation
- Multi-stakeholder debates beyond TPM vs CPO
- PRD generation or writing assistance

## User Scenarios & Testing

### Scenario 1: Simple Product Idea Evaluation

**User**: A product manager submits a brief 2-paragraph product idea via plain text.

**Flow**:
1. User provides text input (any format) containing the product concept
2. Workflow extracts the core project proposal
3. TPM presents opening arguments for why this project should launch
4. Fact-checker validates any market/competitive/technical claims
5. CPO rebuts with concerns about completeness, value, and resource impact
6. Fact-checker validates CPO's counter-claims
7. TPM counters with additional evidence
8. Fact-checker validates TPM's counter-arguments
9. CPO delivers final argument maintaining skeptical position
10. Fact-checker validates final claims
11. Judge renders verdict: Approve funding or Deny

**Acceptance**: Workflow completes with a clear verdict and reasoning

### Scenario 2: Full PRD Document Evaluation

**User**: A product manager submits a comprehensive 20-page PRD document (markdown, text, or pasted content).

**Flow**: Same as Scenario 1, but the TPM and CPO engage in deeper debate covering more aspects of the detailed specification.

**Acceptance**: Workflow handles longer input without breaking; debate references specific sections of the PRD

### Scenario 3: PRD with Verifiable Claims

**User**: PRD contains specific market size numbers, competitor references, or technical assertions.

**Flow**: Fact-checker nodes verify these claims against available data sources and report on accuracy.

**Acceptance**: Fact-check results are included in the debate output; unverified claims are flagged

## Functional Requirements

### FR1: PRD Input Handling
- The system MUST accept PRD content as plain text input
- The system MUST handle PRD documents ranging from short ideas to full specifications
- The system MUST extract the project concept from the provided text

### FR2: Role-Based Debate Orchestration
- The system MUST implement a TPM agent that advocates for project funding
- The system MUST implement a CPO agent that challenges project value and resource allocation
- The system MUST follow the debate sequence: TPM opening → Fact-check → CPO rebuttal → Fact-check → TPM counter → Fact-check → CPO final → Fact-check → Judge verdict

### FR3: Fact-Checking
- The system MUST verify claims made by both TPM and CPO
- The system MUST report verification status for factual claims
- The system MUST identify unverified or unverifiable claims

### FR4: Judge Verdict
- The system MUST render a final decision (Approve/Deny)
- The system MUST provide reasoning for the verdict
- The system MUST summarize key points from the debate

### FR5: Workflow Structure
- The system MUST be implemented as a separate workflow file `tpm_cpo_debate_workflow.py`
- The system MUST reuse the LangGraph StateGraph orchestration pattern from `debate_workflow.py`
- The system MUST use the existing state management and node patterns

## Non-Functional Requirements

### NFR1: Extensibility
- Node implementations should follow the existing pattern for consistency
- New agent roles should be swappable following the current architecture

### NFR2: Observability
- Debate progress should be logged at each stage
- Fact-check results should be clearly indicated

## Success Criteria

- Workflow successfully processes PRD text input and produces a funding decision verdict
- TPM agent consistently argues for project launch based on provided PRD content
- CPO agent consistently challenges completeness, value, and resource allocation
- Fact-checking validates claims and reports verification status
- Final verdict includes clear reasoning
- Workflow reuses existing LangGraph StateGraph patterns without duplicating core orchestration logic

## Assumptions

- Input PRD is in a text-parseable format (plain text, markdown, or paste from .docx)
- Fact-checking has access to relevant data sources for verification
- The existing `debate_workflow.py` provides a valid architectural pattern to follow
- LLM configuration uses the same pattern as existing nodes (`requesty_llm_config_map`)

## Dependencies

- Existing `debate_workflow.py` as architectural reference
- LangGraph for state management and orchestration
- Existing LLM configuration patterns
- Fact-checking infrastructure (already implemented)

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| PRD parsing fails on complex formatting | Medium | Accept plain text input; advise users to paste text content |
| TPM role becomes too optimistic | Low | Judge role balances by requiring evidence |
| CPO role becomes too skeptical | Low | Judge role considers both arguments fairly |
| Fact-checking cannot verify claims | Medium | Flag unverifiable claims rather than failing |
