# Implementation Plan: PRD Document Debate Workflow

**Branch:** `###-002-prd-document-debate-workflow`
**Date:** 2025-02-13
**Spec:** [spec.md](./spec.md)

## Summary

[Extract from feature spec: primary requirement + technical approach from research]

Create a new standalone workflow that enables AI agents to analyze any .docx document through structured debate. The system reads .docx files, extracts text content, and conducts a 4-stage debate (opening → rebuttal → counter → final_argument) between PRO agent (defending) and CON agent (critiquing), with fact-checking and a final verdict assessing both rhetorical performance and document viability.

**Key Design Decisions:**
- New standalone `document_debate_workflow.py` (not modifying existing)
- Extend `DebateState` with `document_input` field
- Read .docx in `DocumentTopicNode`, pass file path from main
- Extend prompts with document-specific instructions (PRO defends, CON critiques)
- Judge evaluates both rhetoric AND document viability

## Technical Context

**Language/Version:** Python 3.11+
**Primary Dependencies:**
- python-docx (External) - Library for reading .docx files
- LangGraph (Internal) - Workflow orchestration from existing codebase
- OpenAI LLM (gpt-4.1) - Topic generation, debate arguments, verdict

**Storage:** File-based (no database required)
**Testing:** pytest (existing framework)
**Target Platform:** Linux/macOS (CLI tool)

**Project Type:** Single Python package (CLI workflow)
**Performance Goals:** Complete within 3 minutes for typical document (1-20 pages)
**Constraints:** Token limits of LLM - documents larger than ~20 pages may need truncation
**Scale/Scope:** Single workflow feature, ~5 new files, extends existing state

## Project Structure

### Documentation (this feature)
```
kitty-specs/002-prd-document-debate-workflow/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── debate_state.py.md
│   ├── document_topic_node.py.md
│   ├── debater_prompts.py.md
│   └── judge_node.py.md
└── tasks.md             # Phase 2 output (NOT created yet)
```

### Source Code (repository root)

```
src/
├── models/                    # Existing - state definitions
├── services/                 # Existing - business logic
│   ├── debate/            # Existing - debate workflows
│   │   ├── debate_workflow.py        # EXISTING - unchanged
│   │   └── document_debate_workflow.py  # NEW - standalone workflow
├── cli/                       # CLI entry points
│   └── main.py               # MODIFY - add --docx argument
├── lib/                       # Shared utilities
└── tests/
    ├── unit/                    # Existing
    ├── integration/              # Existing
    └── contract/                 # NEW - test contract compliance
```

### New Files to Create

| File | Purpose | Phase |
|-------|---------|--------|
| `workflow/debate/document_debate_workflow.py` | Main workflow orchestration | 1 |
| `nodes/document_topic_node.py` | Document topic generation node | 1 |
| `prompts/document_debater_prompts.py` | PRO/CON prompts with document context | 1 |
| Modify `debate_state.py` | Add document_input field | 1 |
| Modify `cli/main.py` | Add --docx argument and pass-through | 1 |
| `tests/contract/test_debate_state.py` | Test state extension | 2 |
| `tests/contract/test_document_topic_node.py` | Test DocumentTopicNode contract | 2 |
| `tests/contract/test_debater_prompts.py` | Test prompt extensions | 2 |

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | No constitution exists | N/A - Using standard practices |

## Parallel Work Analysis

### Dependency Graph

```
Foundation (Day 1):
- debate_state.py extension
- python-docx dependency added

Wave 1 (Days 2-3, parallel):
- document_debate_workflow.py creation
- document_topic_node.py creation
- debater_prompts.py modifications
- main.py modifications
- contract tests creation

Wave 2 (Days 4-5, parallel):
- judge_node.py prompt extension
- integration tests

Integration (Day 6):
- Full workflow testing
```

### Work Distribution

**Sequential work:**
- State extension must complete before workflow can use `document_input`
- `document_topic_node.py` must exist before `document_debate_workflow.py` can import it

**Parallel streams:**
- `document_debate_workflow.py` can be developed independently from prompt modifications
- Contract tests can be written in parallel with node implementations

**Agent assignments:**
- Single developer for entire feature (small scope, clear architecture)

### Coordination Points

- **Sync schedule:** N/A (single developer)
- **Integration tests:** Run after all components complete to verify end-to-end workflow

## Implementation Phases

### Phase 0: Outline & Research ✅

**Status:** Complete

**Output:** `research.md`

All technical decisions confirmed. No unknowns remaining after clarification session.

### Phase 1: Design & Contracts ✅

**Status:** Complete

**Prerequisites:** `research.md` complete

**Completed Artifacts:**
- ✅ `data-model.md` - Entities, relationships, state transitions
- ✅ `contracts/debate_state.py.md` - DebateState extension contract
- ✅ `contracts/document_topic_node.py.md` - DocumentTopicNode contract
- ✅ `contracts/debater_prompts.py.md` - PRO/CON prompt extension contract
- ✅ `contracts/judge_node.py.md` - JudgeNode extension contract
- ✅ `quickstart.md` - Usage guide

### Phase 2: Implementation (Pending)

**Status:** ⏸️ **NOT STARTED**

**Prerequisites:** Phase 1 artifacts complete

**Pending Tasks:**
- Generate `tasks.md` with work packages
- Create implementation work packages

---

## STOP

**Planning phase complete.**

The following artifacts have been generated and committed to the planning repository:

1. `plan.md` - This file
2. `research.md` - Phase 0 research output
3. `data-model.md` - Phase 1 data model
4. `quickstart.md` - Phase 1 quickstart guide
5. `contracts/` - Phase 1 design contracts

**DO NOT PROCEED to implementation.**

Run `/spec-kitty.tasks` to generate work packages when ready to begin development.
