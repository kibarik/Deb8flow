# Language and Style Configuration

**Feature Number**: 012
**Status**: Draft
**Mission**: software-dev
**Created**: 2025-02-17

## Overview

Add a `--language` CLI flag that allows users to specify language and tone settings for all AI agents participating in debates. The flag accepts free-form text describing the desired language style (e.g., "Русский официальный стиль", "English", "кратко и по-факту, без лишней воды"). This language setting is injected as a global modifier into the base system prompt of every agent, ensuring consistent language and tone across the entire debate.

## Problem Statement

Currently, Deb8flow operates with hardcoded English prompts and no way for users to control the language or style of debate. Users who want debates in Russian, formal/official tone, or specific communication styles have no mechanism to request this. Adding a global language configuration flag provides this flexibility while maintaining backward compatibility.

## User Scenarios & Testing

### Scenario 1: Russian Formal Debate
**User**: Researcher conducting debates in Russian

**Action**: Runs `python document_debate_cli.py --text "GitHub полезен для разработчиков" --language "Русский официальный стиль"`

**Expected outcome**: All agents (PRO, CON, Moderator, Judge, Fact Checker) respond in formal Russian style

**Acceptance criteria**:
- All debate outputs are in Russian
- Language maintains formal/official tone
- Debate flows naturally without language inconsistencies

### Scenario 2: English Debate with Concise Style
**User**: Product manager wanting brief, factual arguments

**Action**: Runs `python main.py --language "English, concise and factual, no fluff"`

**Expected outcome**: All agents respond in English with minimal verbiage, focused on facts

**Acceptance criteria**:
- All outputs are in English
- Responses are noticeably shorter and more direct than default
- No unnecessary conversational filler

### Scenario 3: Default Behavior (No Flag)
**User**: Existing user running system without language flag

**Action**: Runs `python main.py` (no `--language` flag)

**Expected outcome**: System behaves exactly as before (backward compatibility)

**Acceptance criteria**:
- Debate proceeds in default language/style
- No errors or warnings about missing language setting
- Outputs identical to current system behavior

## Functional Requirements

### FR-01: CLI Flag Integration
- The system MUST provide a `--language` flag in both `main.py` and `document_debate_cli.py`
- The flag MUST accept free-form text input without validation
- The flag MUST be optional (not required)
- Maximum length of language text: 500 characters

### FR-02: State Propagation
- The system MUST add a `language_setting` field to `DebateState` TypedDict
- The language setting MUST be propagated to all agents through the state
- The field MUST be optional (NotRequired)

### FR-03: Prompt Injection
- The system MUST inject the language setting into the SYSTEM_PROMPT of each agent
- Injection MUST occur before any agent-specific instructions
- Injection format: "\n\n**Language and Style Setting**: {language_setting}\n\n"
- If no language setting is provided, NO injection occurs (maintains exact current prompts)

### FR-04: Agent Coverage
- Language injection MUST apply to: PRO debater, CON debater, Moderator, Judge, Fact Checker, Topic Generator
- All agents MUST receive identical language settings
- No per-agent language configuration is required

### FR-05: Backward Compatibility
- When `--language` is not specified, system behavior MUST be identical to current state
- Existing tests MUST pass without modification
- No breaking changes to API or state structure

## Success Criteria

1. **Usability**: Users can specify any language/style description via single CLI flag
2. **Consistency**: All agents respect the same language setting in a given debate
3. **Compatibility**: System without flag behaves identically to before (100% backward compatibility)
4. **Testability**: All existing E2E tests pass without modification
5. **Coverage**: At least 3 new test cases covering language flag usage scenarios

## Key Entities

| Entity | Description | Properties |
|--------|-------------|------------|
| `language_setting` | User-provided language and style instruction | Type: Optional[str], Max length: 500 chars |
| `DebateState.language_setting` | State field carrying language through workflow | NotRequired[Optional[str]] |
| CLI argument `--language` | Command-line flag for language specification | Type: str, Optional, Max 500 chars |

## Dependencies & Assumptions

### Dependencies
- Existing `BaseComponent.create_chain()` method for prompt construction
- Existing `DebateState` TypedDict for state management
- Existing CLI infrastructure in both `main.py` and `document_debate_cli.py`

### Assumptions
- Users will provide meaningful language/style descriptions
- AI models will respect language instructions in system prompts
- 500-character limit is sufficient for language/style descriptions
- Single global setting is adequate (no per-agent language needs)

## Out of Scope

- Per-agent language configuration (different languages for PRO vs CON)
- Language detection or validation
- Multi-language debates (agents using different languages)
- Translation services
- Language-specific prompt templates
- Formal language code support (e.g., en-US, ru-RU)

## Edge Cases & Error Handling

| Scenario | Expected Behavior |
|----------|-------------------|
| Empty language string (`--language ""`) | Treated as no language setting (same as not providing flag) |
| Very long language description (>500 chars) | CLI error before workflow starts |
| Special characters in language text | Passed through as-is to prompts |
| Language setting conflicts with custom prompts | Language setting prepended to custom prompts |
| Invalid language model cannot understand setting | Model falls back to default behavior (graceful degradation) |
