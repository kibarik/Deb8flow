# Research: Custom Prompt Debate Workflow

**Feature**: 003-tpm-cpo-product-funding-debate-workflow
**Date**: 2025-02-13
**Status**: Complete

## Research Questions

### RQ1: Existing Debate Workflow Architecture

**Question:** How does `document_debate_workflow.py` orchestrate debates using LangGraph?

**Findings:**
- Uses `StateGraph` from `langgraph.graph` with custom `DebateState` TypedDict
- Nodes added via `workflow.add_node(name, node_instance)`
- Flow defined with `workflow.add_edge(source, target)` and `workflow.set_entry_point()`
- Entry point: `generate_topic_node` → `pro_debater_node` → `fact_check_node` → conditional routing → repeat
- Fact-check routing uses `fact_check_router_node` to determine next speaker
- Final verdict: `judge_node` → `END`
- `document_debate_workflow.py` extends `debate_workflow.py` pattern for document-based debates

**Decision:** Reuse existing `document_debate_workflow.py` without creating new workflow

### RQ2: Node Implementation Pattern

**Question:** How are debate nodes structured and how can prompts be injected?

**Findings:**
- All nodes inherit from `BaseComponent` class in `base_component.py`
- BaseComponent provides LLM client initialization and chain creation methods
- Nodes accept `llm_config` parameter in constructor
- Nodes use `SYSTEM_PROMPT` constants for role-specific behavior
- Chain creation methods in BaseComponent allow custom prompt injection
- Example from `pro_debater_node.py`:
  ```python
  class ProDebaterNode(BaseComponent):
      def __init__(self, llm_config: dict):
          super().__init__(llm_config)
      # Uses SYSTEM_PROMPT from pro_debater_prompts.py
  ```

**Decision:** Modify existing `ProDebaterNode` and `ConDebaterNode` to inject custom prompts when present

### RQ3: State Management

**Question:** How is debate state managed between nodes?

**Findings:**
- `DebateState` is a TypedDict with fields: `debate_topic`, `positions`, `messages`
- `DebateMessage` TypedDict for individual messages: `speaker`, `content`, `validated`, `stage`
- DebateStage literal: `"opening" | "rebuttal" | "counter" | "final_argument"`
- State includes metadata for fact-checking limits and speaker tracking
- Feature 002 added `document_input` field for .docx debates
- State can be extended with optional fields using `NotRequired` from typing_extensions

**Decision:** Extend `DebateState` with `pro_custom_prompt` and `con_custom_prompt` optional fields

### RQ4: Prompt System

**Question:** How are prompts structured for different agent roles?

**Findings:**
- Prompts organized in `prompts/` directory with separate files per role
- `pro_debater_prompts.py`: Defines PRO role prompts for each stage
- `con_debater_prompts.py`: Defines CON role prompts for each stage
- `topic_generator_prompts.py`: Defines topic generation prompts
- `judge_prompts.py`: Defines verdict prompts
- Prompts use template strings with role-specific instructions
- Base prompts provide structure that can be extended with custom content

**Decision:** No new prompt files needed - custom prompts will be read from text files and injected into existing base prompts

### RQ5: CLI Implementation Pattern

**Question:** How does `document_debate_cli.py` handle arguments and file I/O?

**Findings:**
- Uses `argparse` for CLI argument parsing
- Existing flags: `--text`, `--docx`, `--request`
- File validation happens before workflow initialization
- Arguments are passed to state initialization
- Error handling with clear messages for invalid inputs
- Example from existing code:
  ```python
  parser.add_argument('--text', type=str, help='Direct text input')
  parser.add_argument('--docx', type=str, help='Path to .docx file')
  ```

**Decision:** Add `--pro-prompt` and `--con-prompt` flags following existing pattern

### RQ6: Fact-Checking Integration

**Question:** Can existing fact-checking be reused?

**Findings:**
- `FactCheckNode` and `FactCheckRouterNode` are role-agnostic
- They validate claims regardless of speaker identity
- FactCheckRouter determines next speaker based on current state
- No modification needed for custom prompt feature

**Decision:** Reuse existing `FactCheckNode` and `FactCheckRouterNode` without changes

## Technical Decisions Summary

| Decision | Rationale | Alternatives Considered |
|----------|----------|----------------------|
| Prompt injection into existing nodes | Simplicity, no code duplication, leverages existing infrastructure | New dedicated node classes |
| Extend DebateState with optional fields | Backward compatibility, minimal changes | New separate state TypedDict |
| CLI flags for prompt files | User-friendly, flexible, no code changes needed for new roles | Hardcoded role selection |
| No new prompt files | Custom prompts provided by users, reduces maintenance burden | Separate prompt files for each role |

### RQ7: Prompt Injection Strategy

**Question:** How should custom prompts be injected into existing system prompts?

**Findings:**
- BaseComponent provides chain creation methods that accept custom system prompts
- Existing nodes use `SYSTEM_PROMPT` constants from prompt files
- Custom prompts should be prepended or appended to base prompts
- LLM receives combined prompt during chain creation
- Prompt injection is a common pattern in LangChain/LangGraph

**Decision:** Prepend custom prompt to base system prompt to establish role context first

## Technical Decisions Summary

| Decision | Rationale | Alternatives Considered |
|----------|----------|----------------------|
| Prompt injection into existing nodes | Simplicity, no code duplication, leverages existing infrastructure | New dedicated node classes |
| Extend DebateState with optional fields | Backward compatibility, minimal changes | New separate state TypedDict |
| CLI flags for prompt files | User-friendly, flexible, no code changes needed for new roles | Hardcoded role selection |
| No new prompt files | Custom prompts provided by users, reduces maintenance burden | Separate prompt files for each role |
| Prepend custom to base prompt | Establish role context before debate instructions | Append after base prompt |

## Open Questions Resolved

All clarifications from planning phase resolved. No outstanding unknowns.
