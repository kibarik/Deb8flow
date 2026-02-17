# Implementation Plan: Language and Style Configuration

**Branch**: `main` | **Date**: 2025-02-17 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/kitty-specs/012-language-and-style-configuration/spec.md`

## Summary

Add a `--language` CLI flag that allows users to specify language and tone settings for all AI agents. The flag accepts free-form text (e.g., "Русский официальный стиль", "English", "кратко и по-факту") and injects it as a global modifier into the base system prompt of every agent via centralized modification of `BaseComponent.create_chain()`.

**Technical Approach**:
- Add `language_setting: NotRequired[Optional[str]]` to `DebateState`
- Add `--language` argparse argument to both CLI entry points
- Modify `BaseComponent.create_chain()` to prepend language instruction to system template
- Maintain 100% backward compatibility (optional flag, empty = no change)

## Technical Context

**Language/Version**: Python 3.12+ (asyncio support)
**Primary Dependencies**: LangChain (ChatPromptTemplate, ChatOpenAI), pytest, argparse (stdlib), rich (logging)
**Storage**: N/A (in-memory state through DebateState TypedDict)
**Testing**: pytest with contract tests for DebateState, E2E tests for workflows
**Target Platform**: Cross-platform (Linux, macOS, Windows)
**Project Type**: Single CLI application
**Performance Goals**: Not critical (prototype/hypothesis validation prioritized)
**Constraints**: Minimal external dependencies, pip installable package
**Scale/Scope**: Small feature - ~5 files modified, 3 new test cases

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Requirement | Status | Notes |
|-------------|--------|-------|
| **Python 3.12+** | ✅ PASS | Project uses Python 3.12+ with asyncio |
| **pytest required** | ✅ PASS | New test cases will be added |
| **CI green** | ⏳ PENDING | CI must pass after implementation |
| **Spec-driven** | ✅ PASS | Working from approved specification |
| **Self-documenting code** | ⏳ PENDING | Code should be clear without excessive comments |
| **Minimal dependencies** | ✅ PASS | No new dependencies required |
| **Cross-platform** | ✅ PASS | CLI changes work on all platforms |

**Constitution Compliance**: ✅ All initial checks pass

## Project Structure

### Documentation (this feature)

```
kitty-specs/012-language-and-style-configuration/
├── spec.md              # Feature specification (COMPLETE)
├── plan.md              # This file
├── research.md          # Phase 0 output (see below)
├── data-model.md        # Phase 1 output (see below)
├── quickstart.md        # Phase 1 output (see below)
├── checklists/
│   └── requirements.md  # Quality checklist (COMPLETE)
└── tasks/               # Created by /spec-kitty.tasks (NOT NOW)
```

### Source Code (repository root)

```
debate_state.py                    # MODIFIED: Add language_setting field
├── nodes/
│   └── base_component.py          # MODIFIED: Add language injection in create_chain()
├── workflow/
│   ├── debate_workflow.py         # MODIFIED: Pass language_setting to initial state
│   └── document_debate_workflow.py # MODIFIED: Pass language_setting to initial state
├── prompts/                       # NO CHANGES: BaseComponent handles injection
│   ├── pro_debater_prompts.py
│   ├── con_debater_prompts.py
│   ├── judge_prompts.py
│   └── ...
├── tests/
│   ├── contract/
│   │   └── test_debate_state.py   # MODIFIED: Add test for language_setting field
│   └── e2e/
│       ├── test_full_debate_flow.py       # MODIFIED: Add language flag test
│       └── test_document_debate_e2e.py    # MODIFIED: Add language flag test
├── main.py                         # MODIFIED: Add --language argparse argument
└── document_debate_cli.py          # MODIFIED: Add --language argparse argument
```

**Structure Decision**: Single Python CLI application with existing project structure. Modifications are localized to:
1. State definition (`debate_state.py`)
2. Base component (`nodes/base_component.py`)
3. CLI entry points (`main.py`, `document_debate_cli.py`)
4. Workflow initialization (both workflows)
5. Tests (new cases for language flag)

No new directories or files required beyond test modifications.

## Complexity Tracking

*No violations - feature aligns with constitution*

| Aspect | Impact | Rationale |
|--------|--------|-----------|
| Dependencies | None | Uses existing argparse, LangChain, pytest |
| Architecture | Minimal | Single centralized change in BaseComponent |
| Testing | Small | 3 new test cases, no new test infrastructure |
| Cross-platform | None | Python stdlib argparse works everywhere |

---

## Phase 0: Research

*Status: SKIP - No NEEDS CLARIFICATION markers in spec*

Since the specification has no [NEEDS CLARIFICATION] markers and all technical decisions are clear (centralized approach in BaseComponent, argparse for CLI, existing test infrastructure), no research phase is required. Proceeding directly to Phase 1 design.

**Research Output**: research.md marked as N/A

---

## Phase 1: Design & Contracts

### 1.1 Data Model

**File**: `kitty-specs/012-language-and-style-configuration/data-model.md`

```markdown
# Data Model: Language and Style Configuration

## Entity: DebateState.language_setting

**Field**: `language_setting`
**Type**: `NotRequired[Optional[str]]`
**Location**: `debate_state.py` → `DebateState` TypedDict

### Field Definition

```python
class DebateState(TypedDict):
    # ... existing fields ...
    language_setting: NotRequired[Optional[str]]  # NEW FIELD
```

### Validation Rules

| Rule | Description |
|------|-------------|
| Optional | Field may be absent from state |
| Nullable | Value may be None |
| Max length | 500 characters (enforced at CLI level) |
| No validation | Content is free-form text, passed directly to prompts |

### State Flow

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│ CLI --language  │────▶│ DebateState      │────▶│ BaseComponent   │
│                 │     │ .language_setting│     │ .create_chain() │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                                                            │
                                                            ▼
                                                    ┌───────────────┐
                                                    │ SYSTEM_PROMPT │
                                                    │ + language    │
                                                    │ injection     │
                                                    └───────────────┘
```

### Example States

**Default (no language setting)**:
```python
state = {
    "debate_topic": "AI safety",
    "positions": {},
    "messages": []
    # language_setting absent
}
```

**With language setting**:
```python
state = {
    "debate_topic": "AI safety",
    "positions": {},
    "messages": [],
    "language_setting": "Русский официальный стиль"
}
```

### Migration

**No migration required** - `NotRequired[Optional[str]]` is backward compatible:
- Existing states without the field continue to work
- Existing code that doesn't reference the field is unaffected
```

### 1.2 API Contracts

**File**: `kitty-specs/012-language-and-style-configuration/contracts/cli-interface.md`

```markdown
# CLI Contract: --language Flag

## Interface Specification

### main.py

```bash
python main.py [--language LANGUAGE]
```

### document_debate_cli.py

```bash
python document_debate_cli.py --docx FILE --request REQUEST [--language LANGUAGE]
python document_debate_cli.py --text TOPIC [--language LANGUAGE]
```

## Argument Specification

| Flag | Type | Required | Max Length | Default | Description |
|------|------|----------|------------|---------|-------------|
| `--language` | str | No | 500 chars | None | Free-form language/style instruction |

## Error Handling

| Scenario | Behavior |
|----------|----------|
| Flag not provided | Workflow runs normally (no language injection) |
| Empty string (`--language ""`) | Treated as None (no language injection) |
| Exceeds 500 chars | argparse error before workflow starts |
| Special characters | Passed through as-is |

## Implementation Pattern

```python
parser.add_argument(
    "--language",
    type=str,
    help="Language and style setting for all agents (e.g., 'Русский официальный стиль', 'English, concise')"
)

# Usage
language_setting = args.language if args.language else None
if language_setting:
    # Validate length
    if len(language_setting) > 500:
        logger.error("❌ --language value too long (max 500 characters)")
        sys.exit(1)

# Pass to initial state
initial_state = {
    # ... other fields ...
    "language_setting": language_setting
}
```
```

### 1.3 Quickstart Guide

**File**: `kitty-specs/012-language-and-style-configuration/quickstart.md`

```markdown
# Quickstart: Language and Style Configuration

## Basic Usage

### Standard Debate

```bash
# Default (no language setting)
python main.py

# Russian formal style
python main.py --language "Русский официальный стиль"

# English, concise
python main.py --language "English, concise and factual, no fluff"

# Casual Russian
python main.py --language "Русский как другу"
```

### Document Debate

```bash
# With direct topic
python document_debate_cli.py --text "GitHub полезен для разработчиков" \
    --language "Русский официальный стиль"

# With document context
python document_debate_cli.py --docx project.docx --request "какой потенциал?" \
    --language "кратко и по-факту, без лишней воды"
```

## Examples

### Russian Formal Debate

```bash
$ python document_debate_cli.py \
    --text "GitHub полезен для разработчиков" \
    --language "Русский официальный стиль"

# All agents (PRO, CON, Judge, Fact Checker) respond in formal Russian
```

### Multi-Language Context

```bash
$ python main.py --language "English professional tone with citations"

# Debate in English with professional tone and citation requirements
```

### Style Modifiers

```bash
# Concise style
--language "Short responses, bullet points where possible"

# Academic style
--language "Academic tone with citations and formal language"

# Casual style
--language "Conversational tone, explain like I'm 12"
```

## Testing

```bash
# Run all tests
pytest

# Run specific language test
pytest tests/e2e/test_full_debate_flow.py::test_language_flag

# Run with coverage
pytest --cov=nodes --cov=workflow
```

## Troubleshooting

**Problem**: Language setting not applied

**Solution**: Check that:
1. `--language` flag is correctly passed to CLI
2. `language_setting` is in initial state
3. `BaseComponent.create_chain()` is called (not bypassed)

**Problem**: Empty language setting causes issues

**Solution**: Empty strings are treated as None - use `if args.language:` check
```

---

## Implementation Tasks (Preview)

*These tasks will be expanded into work packages by `/spec-kitty.tasks`*

### WP01: State Definition
- Add `language_setting: NotRequired[Optional[str]]` to `DebateState`
- Add contract test for new field

### WP02: CLI Integration
- Add `--language` argument to `main.py`
- Add `--language` argument to `document_debate_cli.py`
- Add length validation (500 chars max)

### WP03: Base Component Modification
- Modify `BaseComponent.create_chain()` to accept `language_setting`
- Inject language instruction into system template when present
- Preserve existing behavior when `language_setting` is None/absent

### WP04: Workflow Integration
- Pass `language_setting` from CLI to initial state in both workflows
- Ensure state propagates to all agents

### WP05: Testing
- Add E2E test for `--language` flag in standard debate
- Add E2E test for `--language` flag in document debate
- Add backward compatibility test (no flag)
- Verify all existing tests pass

---

## Next Steps

**Mandatory Stop Point**: Planning complete.

Run `/spec-kitty.tasks` to generate work packages for implementation.

**Generated Artifacts**:
- ✅ `plan.md` (this file)
- ⏭️ `research.md` (N/A - no clarifications needed)
- ⏭️ `data-model.md` (Phase 1 output)
- ⏭️ `contracts/cli-interface.md` (Phase 1 output)
- ⏭️ `quickstart.md` (Phase 1 output)
- ❌ `tasks.md` (NOT created - run `/spec-kitty.tasks` next)
