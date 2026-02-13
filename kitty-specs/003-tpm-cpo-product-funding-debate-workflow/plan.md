# Implementation Plan: TPM-CPO Product Funding Debate Workflow

**Branch**: `main` | **Date**: 2025-02-13 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/kitty-specs/003-tpm-cpo-product-funding-debate-workflow/spec.md`

## Summary

Create a new debate workflow where a Technical Product Manager (TPM) advocates for project funding while a Chief Product Officer (CPO) challenges completeness, value, and resource allocation. The workflow accepts any text-based PRD as input and orchestrates a structured debate with fact-checking and a final funding decision verdict (Approve/Deny).

**Key Design Decisions:**
- New standalone `tpm_cpo_debate_workflow.py` following exact architectural pattern from `debate_workflow.py`
- New dedicated node classes: `TPMNode` (advocate), `CPONode` (skeptic), `TpmCpoTopicGeneratorNode`
- New `TpmCpoDebateState` extending existing state patterns with PRD input field
- New prompt sets: `tpm_prompts.py`, `cpo_prompts.py`, `tpm_cpo_judge_prompts.py`
- Reuse existing fact-checking infrastructure (`FactCheckNode`, `FactCheckRouterNode`)
- Judge renders funding decision (Approve/Deny) with business rationale

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**:
- LangGraph (Internal) - Workflow orchestration from existing codebase
- OpenAI LLM (gpt-4.1 or deepseek-chat) - TPM/CPO arguments, verdict via `requesty_llm_config_map`
- Existing base node infrastructure (`BaseComponent`)

**Storage**: File-based (no database required)
**Testing**: pytest (existing framework)
**Target Platform**: Linux/macOS (CLI tool)

**Project Type**: Single Python package (CLI workflow extension)
**Performance Goals**: Complete debate within 5 minutes for typical PRD (1-10 pages)
**Constraints**: Token limits of LLM - PRDs larger than ~50 pages may need summarization pre-processing
**Scale/Scope**: Single workflow feature, ~7 new files, extends existing state/node patterns

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**⚠️ No constitution file exists** - Skipping constitution check. Using standard software development best practices.

## Project Structure

### Documentation (this feature)

```
kitty-specs/003-tpm-cpo-product-funding-debate-workflow/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── tpm_cpo_debate_state.py.md
│   ├── tpm_node.py.md
│   ├── cpo_node.py.md
│   ├── tpm_cpo_topic_generator_node.py.md
│   ├── tpm_prompts.py.md
│   ├── cpo_prompts.py.md
│   └── tpm_cpo_judge_prompts.py.md
└── tasks.md             # Phase 2 output (NOT created yet)
```

### Source Code (repository root)

```
workflow/
├── debate_workflow.py        # EXISTING - unchanged
└── tpm_cpo_debate_workflow.py  # NEW - standalone workflow

nodes/
├── (existing nodes...)      # Unchanged
├── tpm_node.py              # NEW - TPM advocate node
├── cpo_node.py              # NEW - CPO skeptic node
└── tpm_cpo_topic_generator_node.py  # NEW - PRD-to-topic generator

prompts/
├── (existing prompts...)     # Unchanged
├── tpm_prompts.py           # NEW - TPM agent prompts
├── cpo_prompts.py           # NEW - CPO agent prompts
└── tpm_cpo_judge_prompts.py # NEW - Funding decision judge prompts

debate_state.py              # MODIFY - add TpmCpoDebateState
```

### New Files to Create

| File | Purpose | Phase |
|-------|---------|--------|
| `workflow/tpm_cpo_debate_workflow.py` | Main workflow orchestration | 1 |
| `nodes/tpm_node.py` | TPM advocate node (opening, counter) | 1 |
| `nodes/cpo_node.py` | CPO skeptic node (rebuttal, final) | 1 |
| `nodes/tpm_cpo_topic_generator_node.py` | PRD topic/extraction node | 1 |
| `prompts/tpm_prompts.py` | TPM role prompts | 1 |
| `prompts/cpo_prompts.py` | CPO role prompts | 1 |
| `prompts/tpm_cpo_judge_prompts.py` | Funding decision judge prompts | 1 |
| Modify `debate_state.py` | Add TpmCpoDebateState with prd_input field | 1 |

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | No constitution exists | N/A - Using standard practices |

## Parallel Work Analysis

### Dependency Graph

```
Foundation (must complete first):
- TpmCpoDebateState added to debate_state.py

Wave 1 (can proceed in parallel):
- tpm_node.py creation
- cpo_node.py creation
- tpm_cpo_topic_generator_node.py creation
- tpm_prompts.py creation
- cpo_prompts.py creation

Wave 2 (after Wave 1):
- tpm_cpo_judge_prompts.py creation
- tpm_cpo_debate_workflow.py orchestration

Integration (final):
- Full workflow testing
```

### Work Distribution

**Sequential work:**
- State extension (TpmCpoDebateState) must complete before nodes can use it
- Topic generator must exist before workflow can import it

**Parallel streams:**
- TPM node and prompts can be developed independently from CPO node and prompts
- Once nodes exist, workflow orchestration can proceed independently

**Agent assignments:**
- Single developer for entire feature (small scope, clear architecture pattern)

### Coordination Points

- **Sync schedule:** N/A (single developer)
- **Integration tests:** Run after all components complete to verify end-to-end workflow

## Implementation Phases

### Phase 0: Outline & Research ✅

**Status:** Complete

**Output:** `research.md`

**Research conducted:**
- Analyzed existing `debate_workflow.py` architecture pattern
- Studied node inheritance from `BaseComponent`
- Examined state management in `DebateState`
- Identified prompt patterns in existing PRO/CON agents
- Confirmed LLM configuration via `requesty_llm_config_map`

**Technical decisions confirmed:**
- Use same LangGraph StateGraph pattern
- Create dedicated node classes (not parameterized variants)
- Extend state with new TypedDict (not modify existing)
- Preserve fact-checking infrastructure

### Phase 1: Design & Contracts ✅

**Status:** Complete

**Prerequisites:** `research.md` complete

**Completed Artifacts:**
- ✅ `data-model.md` - TpmCpoDebateState entities, relationships
- ✅ `contracts/tpm_cpo_debate_state.py.md` - State extension contract
- ✅ `contracts/tpm_node.py.md` - TPM node contract
- ✅ `contracts/cpo_node.py.md` - CPO node contract
- ✅ `contracts/tpm_cpo_topic_generator_node.py.md` - Topic generator contract
- ✅ `contracts/tpm_prompts.py.md` - TPM prompt contract
- ✅ `contracts/cpo_prompts.py.md` - CPO prompt contract
- ✅ `contracts/tpm_cpo_judge_prompts.py.md` - Judge prompt contract
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
