# Custom Prompt Debate Workflow

**Feature Number**: 003
**Status**: Draft
**Mission**: software-dev

## Overview

A flexible debate workflow enhancement that enables custom role-based debates through CLI prompt injection. Instead of creating separate node classes for each role combination, the system accepts custom prompt files that are injected into the existing PRO and CON debater system prompts. This approach allows TPM vs CPO funding debates, or any other custom role combination, without creating new node classes or workflow files.

## User Problem Statement

Product teams need to evaluate project proposals from different professional perspectives. Current debate system uses generic PRO/CON roles that don't capture specific professional contexts like Technical Product Manager (TPM) advocating for launch vs Chief Product Officer (CPO) evaluating resource allocation. Rather than creating hardcoded node classes for each role combination, users need a flexible way to customize debater personalities and contexts.

## Goals

### Primary Goals
- Enable custom role-based debates through CLI prompt flags
- Inject custom prompts into existing system prompts without replacing them
- Support TPM vs CPO funding debates and any other custom role combinations
- Maintain backward compatibility with existing debates

### Secondary Goals
- Allow rapid experimentation with different role combinations
- Avoid creating separate node classes for each role type
- Reuse existing debate orchestration patterns from `document_debate_workflow.py`

## Out of Scope

- Creating separate TPM/CPO node classes
- Creating new workflow files (e.g., `tpm_cpo_debate_workflow.py`)
- Modifying the existing debate flow sequence
- Breaking existing tests or functionality
- Direct integration with project management tools (Jira, Linear, etc.)
- Real-time human-in-the-loop debate participation

## User Scenarios & Testing

### Scenario 1: TPM vs CPO Funding Debate

**User**: A product manager wants to debate a funding decision with TPM and CPO roles.

**Flow**:
1. User prepares two prompt files: `tpm_prompt.txt` and `cpo_prompt.txt`
2. User runs: `python3 document_debate_cli.py --text "Build AI-powered feature X" --pro-prompt tpm_prompt.txt --con-prompt cpo_prompt.txt`
3. Workflow reads custom prompts and validates them
4. TPM prompt is injected into PRO system prompt
5. CPO prompt is injected into CON system prompt
6. Debate proceeds with role-specific arguments
7. Judge renders verdict with role context

**Acceptance**: Debate reflects TPM and CPO perspectives throughout all stages

### Scenario 2: Standard Debate (No Custom Prompts)

**User**: User wants a standard debate without custom roles.

**Flow**:
1. User runs: `python3 document_debate_cli.py --text "GitHub полезен для разработчиков"`
2. No custom prompts are provided
3. Debate uses default PRO/CON system prompts
4. Workflow proceeds normally

**Acceptance**: System works exactly as before without custom prompts

### Scenario 3: PRO-Only Custom Prompt

**User**: User wants to customize only the PRO debater with a specific role.

**Flow**:
1. User runs: `python3 document_debate_cli.py --docx prd.docx --pro-prompt engineer_prompt.txt`
2. Only PRO debater uses custom prompt
3. CON debater uses default system prompt
4. Debate proceeds with mixed roles

**Acceptance**: System handles single-side customization correctly

### Scenario 4: Invalid Prompt File

**User**: User provides a prompt file that doesn't exist or is empty.

**Flow**:
1. User runs with `--pro-prompt missing.txt`
2. System validates file existence and content
3. System displays clear error message
4. Workflow exits without starting

**Acceptance**: Validation prevents invalid inputs with helpful error messages

## Functional Requirements

### FR1: CLI Custom Prompt Flags
- The system MUST add `--pro-prompt <path>` flag to `document_debate_cli.py`
- The system MUST add `--con-prompt <path>` flag to `document_debate_cli.py`
- The system MUST treat both flags as optional
- The system MUST treat both flags as independent (can specify one, both, or neither)
- The system MUST validate file paths before starting workflow

### FR2: Prompt Injection into System Prompts
- The system MUST read custom prompt content from provided file paths
- The system MUST inject custom prompts into existing SYSTEM_PROMPT
- The system MUST NOT replace base system prompts
- The system MUST preserve existing debate flow and logic
- Custom prompts SHOULD add character personality, role context, and perspective

### FR3: State Extension for Custom Prompts
- The system MUST add `pro_custom_prompt` field to `DebateState`
- The system MUST add `con_custom_prompt` field to `DebateState`
- The system MUST propagate custom prompts through workflow to debater nodes
- The system MUST handle None values for missing custom prompts

### FR4: Debater Node Modifications
- The system MUST modify `pro_debater_node.py` to accept and use `pro_custom_prompt`
- The system MUST modify `con_debater_node.py` to accept and use `con_custom_prompt`
- The system MUST inject custom prompt into chain creation when present
- The system MUST work normally when custom prompt is None

### FR5: File Validation
- The system MUST validate custom prompt file exists
- The system MUST validate file is not empty
- The system MUST validate file size <= 5000 characters
- The system MUST provide clear error messages for validation failures
- The system MUST accept plain text (.txt) files

### FR6: Backward Compatibility
- The system MUST work without custom prompts (default behavior)
- The system MUST NOT break existing tests
- The system MUST NOT change behavior when flags are not provided
- The system MUST maintain all existing functionality

## Non-Functional Requirements

### NFR1: Simplicity
- No new node classes should be created
- No new workflow files should be created
- Implementation should reuse existing patterns

### NFR2: Usability
- Error messages should clearly indicate what went wrong
- Validation should happen before workflow starts
- CLI help should document the new flags

### NFR3: Observability
- Custom prompt usage should be logged when present
- Debate progress should remain observable

## Success Criteria

- CLI accepts `--pro-prompt` and `--con-prompt` flags independently
- Custom prompts are injected into system prompts correctly
- TPM vs CPO debate demonstrates role-specific arguments
- Standard debates work exactly as before (backward compatibility)
- File validation prevents invalid inputs
- All existing tests continue to pass
- No new node classes or workflow files are created
- Single-side customization (PRO-only or CON-only) works correctly

## Implementation Details

### Prompt File Format
- Plain text files (.txt)
- Read content as-is from file path
- Content should describe role, personality, and context
- Example TPM prompt: "You are a Technical Product Manager advocating for project funding. Focus on technical feasibility, market opportunity, and user value."
- Example CPO prompt: "You are a Chief Product Officer evaluating resource allocation. Focus on completeness, strategic alignment, and ROI."

### Prompt Injection Strategy
- Custom prompt is prepended or appended to base SYSTEM_PROMPT
- Base prompt structure remains unchanged
- Custom prompt provides role-specific context
- LLM receives combined prompt during chain creation

### State Changes
- Add to `DebateState` in `debate_state.py`:
  ```python
  pro_custom_prompt: Optional[str] = None
  con_custom_prompt: Optional[str] = None
  ```

### Node Changes
- Modify `pro_debater_node.py`:
  - Accept `pro_custom_prompt` from state
  - Inject into system prompt during chain creation
  - Handle None value (no custom prompt)

- Modify `con_debater_node.py`:
  - Accept `con_custom_prompt` from state
  - Inject into system prompt during chain creation
  - Handle None value (no custom prompt)

### CLI Changes
- Add to `document_debate_cli.py`:
  ```python
  parser.add_argument('--pro-prompt', type=str, help='Path to custom PRO debater prompt file')
  parser.add_argument('--con-prompt', type=str, help='Path to custom CON debater prompt file')
  ```
- Implement validation function for prompt files
- Pass validated prompts to state initialization

## Assumptions

- Custom prompts are text files containing role context
- Base system prompts remain compatible with prompt injection
- Existing nodes can be modified without breaking other workflows
- File I/O for prompt reading is acceptable

## Dependencies

- Existing `document_debate_workflow.py` for debate orchestration
- Existing `pro_debater_node.py` and `con_debater_node.py` for modification
- Existing `DebateState` for state extension
- Existing `document_debate_cli.py` for CLI enhancement

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Prompt injection breaks base system prompt | Medium | Test injection with various prompt styles |
| File I/O errors during prompt reading | Low | Validate files exist before workflow starts |
| Custom prompt makes debaters ignore instructions | Low | Keep base system prompt structure intact |
| Backward compatibility broken | High | Run all existing tests after changes |
| Performance impact from file reading | Low | Read files once at startup, cache in state |
