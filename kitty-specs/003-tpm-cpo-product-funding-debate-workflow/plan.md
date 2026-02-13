# Implementation Plan: Custom Prompt Debate Workflow

**Branch**: `main` | **Date**: 2025-02-13 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/kitty-specs/003-tpm-cpo-product-funding-debate-workflow/spec.md`

## Summary

Add custom prompt injection capabilities to the existing debate workflow, enabling role-based debates (e.g., TPM vs CPO funding debates) through CLI flags. Instead of creating new node classes or workflow files, the system accepts custom prompt files that are injected into the existing PRO and CON debater system prompts. This approach allows flexible role customization without duplicating infrastructure.

**Key Design Decisions:**
- Extend existing `document_debate_cli.py` with `--pro-prompt` and `--con-prompt` flags
- Extend `DebateState` with `pro_custom_prompt` and `con_custom_prompt` fields
- Modify existing `pro_debater_node.py` and `con_debater_node.py` to inject custom prompts
- No new node classes, workflow files, or prompt files needed
- Reuse existing `document_debate_workflow.py` orchestration
- Custom prompts add role context on top of base system prompts

## Technical Context

**Language/Version**: Python 3.12+
**Primary Dependencies**:
- LangGraph (Internal) - Existing workflow orchestration
- OpenAI LLM - Debate generation via existing LLM configs
- Existing base node infrastructure (`BaseComponent`)
- argparse - CLI argument parsing

**Storage**: File-based (no database required)
**Testing**: pytest (existing framework)
**Target Platform**: Linux/macOS/Windows (CLI tool)

**Project Type**: CLI enhancement to existing workflow
**Performance Goals**: No performance impact (file I/O at startup only)
**Constraints**: Prompt file size limit (5000 characters)
**Scale/Scope**: Minimal changes - 4 files modified, no new files

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
└── contracts/           # Phase 1 output
    ├── debate_state.py.md
    ├── pro_debater_node.py.md
    ├── con_debater_node.py.md
    └── document_debate_cli.py.md
```

### Source Code (repository root)

```
workflow/
└── document_debate_workflow.py  # MODIFY - accept custom prompts in state

nodes/
├── pro_debater_node.py          # MODIFY - inject pro_custom_prompt
├── con_debater_node.py          # MODIFY - inject con_custom_prompt
└── (existing nodes...)          # Unchanged

prompts/
└── (existing prompts...)         # No new prompt files

debate_state.py                   # MODIFY - add pro_custom_prompt, con_custom_prompt

document_debate_cli.py            # MODIFY - add --pro-prompt, --con-prompt flags
```

### Files to Modify

| File | Purpose | Phase |
|-------|---------|--------|
| `debate_state.py` | Add `pro_custom_prompt`, `con_custom_prompt` fields | 1 |
| `nodes/pro_debater_node.py` | Inject `pro_custom_prompt` into system prompt | 1 |
| `nodes/con_debater_node.py` | Inject `con_custom_prompt` into system prompt | 1 |
| `document_debate_cli.py` | Add `--pro-prompt`, `--con-prompt` flags and validation | 1 |

### New Files to Create

None - all changes are modifications to existing files.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | No new node classes or workflows | Simpler than creating separate classes - leverages existing infrastructure |

## Parallel Work Analysis

### Dependency Graph

```
Foundation (must complete first):
- DebateState extension (pro_custom_prompt, con_custom_prompt)

Wave 1 (can proceed in parallel):
- CLI flags implementation (document_debate_cli.py)
- Prompt file validation logic

Wave 2 (after Wave 1):
- PRO debater node modification (pro_custom_prompt injection)
- CON debater node modification (con_custom_prompt injection)

Integration (final):
- End-to-end testing with custom prompts
- Backward compatibility testing
```

### Work Distribution

**Sequential work:**
- State extension must complete before node modifications
- CLI flags and validation must complete before node modifications

**Parallel streams:**
- PRO debater node and CON debater node modifications can proceed independently
- CLI implementation and state extension can proceed independently

**Agent assignments:**
- Single developer for entire feature (minimal scope, clear modifications)

### Coordination Points

- **Sync schedule:** N/A (single developer)
- **Integration tests:** Run after all components complete to verify end-to-end workflow

## Implementation Phases

### Phase 0: Outline & Research ✅

**Status:** Complete

**Output:** `research.md`

**Research conducted:**
- Analyzed existing `document_debate_workflow.py` and `debate_workflow.py` architecture
- Studied prompt injection approach in existing nodes
- Examined state management in `DebateState`
- Identified file I/O patterns and CLI validation strategies
- Confirmed backward compatibility requirements

**Technical decisions confirmed:**
- Use prompt injection into existing nodes (no new classes)
- Extend state with optional fields (not separate TypedDict)
- Add CLI flags for prompt file paths
- Preserve all existing functionality

### Phase 1: Design & Contracts ✅

**Status:** Complete

**Prerequisites:** `research.md` complete

**Completed Artifacts:**
- ✅ `data-model.md` - DebateState extension entities, relationships
- ✅ `contracts/debate_state.py.md` - State extension contract
- ✅ `contracts/pro_debater_node.py.md` - PRO node modification contract
- ✅ `contracts/con_debater_node.py.md` - CON node modification contract
- ✅ `contracts/document_debate_cli.py.md` - CLI enhancement contract
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
