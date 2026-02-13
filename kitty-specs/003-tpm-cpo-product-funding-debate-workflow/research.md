# Research: TPM-CPO Product Funding Debate Workflow

**Feature**: 003-tpm-cpo-product-funding-debate-workflow
**Date**: 2025-02-13
**Status**: Complete

## Research Questions

### RQ1: Existing Debate Workflow Architecture

**Question:** How does `debate_workflow.py` orchestrate debates using LangGraph?

**Findings:**
- Uses `StateGraph` from `langgraph.graph` with custom `DebateState` TypedDict
- Nodes added via `workflow.add_node(name, node_instance)`
- Flow defined with `workflow.add_edge(source, target)` and `workflow.set_entry_point()`
- Entry point: `generate_topic_node` → `pro_debater_node` → `fact_check_node` → conditional routing → repeat
- Fact-check routing uses `fact_check_router_node` to determine next speaker
- Final verdict: `judge_node` → `END`

**Decision:** Follow exact same pattern for TPM-CPO workflow

### RQ2: Node Implementation Pattern

**Question:** How are debate nodes structured and what do they inherit from?

**Findings:**
- All nodes inherit from `BaseComponent` class in `base_component.py`
- BaseComponent provides LLM client initialization and basic message handling
- Nodes accept `llm_config` parameter in constructor
- Example from `pro_debater_node.py`:
  ```python
  class ProDebaterNode(BaseComponent):
      def __init__(self, llm_config: dict):
          super().__init__(llm_config)
  ```
- Each node implements specific role behavior (opening, rebuttal, counter, final)

**Decision:** Create new `TPMNode` and `CPONode` classes inheriting from `BaseComponent`

### RQ3: State Management

**Question:** How is debate state managed between nodes?

**Findings:**
- `DebateState` is a TypedDict with fields: `debate_topic`, `positions`, `messages`
- `DebateMessage` TypedDict for individual messages: `speaker`, `content`, `validated`, `stage`
- DebateStage literal: `"opening" | "rebuttal" | "counter" | "final_argument"`
- State includes metadata for fact-checking limits and speaker tracking
- Feature 002 added `document_input` field for .docx debates

**Decision:** Create new `TpmCpoDebateState` TypedDict with `prd_input` field for PRD text

### RQ4: Prompt System

**Question:** How are prompts structured for different agent roles?

**Findings:**
- Prompts organized in `prompts/` directory with separate files per role
- `pro_debater_prompts.py`: Defines PRO role prompts for each stage
- `con_debater_prompts.py`: Defines CON role prompts for each stage
- `topic_generator_prompts.py`: Defines topic generation prompts
- `judge_prompts.py`: Defines verdict prompts
- Prompts use template strings with role-specific instructions

**Decision:** Create new prompt files:
- `tpm_prompts.py` - TPM advocate role prompts
- `cpo_prompts.py` - CPO skeptic role prompts
- `tpm_cpo_judge_prompts.py` - Funding decision judge prompts

### RQ5: LLM Configuration

**Question:** How are LLMs configured for nodes?

**Findings:**
- LLM configuration centralized in `configurations/llm_config.py`
- `requesty_llm_config_map` dictionary maps model names to config
- Nodes access LLM via `llm_config` parameter passed during initialization
- Example usage: `GenerateTopicNode(requesty_llm_config_map["deepseek-chat"])`

**Decision:** Use same `requesty_llm_config_map` pattern for TPM-CPO nodes

### RQ6: Fact-Checking Integration

**Question:** Can existing fact-checking be reused?

**Findings:**
- `FactCheckNode` and `FactCheckRouterNode` are role-agnostic
- They validate claims regardless of speaker identity
- FactCheckRouter determines next speaker based on current state
- No modification needed for TPM-CPO workflow

**Decision:** Reuse existing `FactCheckNode` and `FactCheckRouterNode` without changes

## Technical Decisions Summary

| Decision | Rationale | Alternatives Considered |
|----------|----------|----------------------|
| New dedicated node classes | Clarity, separation of concerns, follows existing pattern | Parameterized single node with role argument |
| New TpmCpoDebateState TypedDict | Type safety, explicit field requirements | Extend DebateState with optional fields |
| Separate prompt files for TPM/CPO | Maintainability, clear role boundaries | Single file with role-based branching |
| Reuse fact-checking infrastructure | Proven, tested, role-agnostic | Custom business-logic validation |

## Open Questions Resolved

All clarifications from planning phase resolved. No outstanding unknowns.
