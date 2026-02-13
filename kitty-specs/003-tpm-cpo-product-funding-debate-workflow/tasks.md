# Tasks: TPM-CPO Product Funding Debate Workflow

**Feature**: 003-tpm-cpo-product-funding-debate-workflow
**Generated**: 2025-02-13
**Status**: Planned

## Overview

This feature implements a new debate workflow for evaluating product funding proposals. A Technical Product Manager (TPM) advocates for project launch while a Chief Product Officer (CPO) challenges completeness, value, and resource allocation. The workflow accepts any text-based PRD as input and produces a funding decision verdict (Approve/Deny).

**Total Work Packages**: 6
**Total Subtasks**: 17
**Average Subtasks per WP**: 2.8 (ideal range: 3-7)

---

## WP01: State Foundation

**Summary**: Add TPM-CPO debate state structures to existing `debate_state.py`

**Priority**: Foundation (blocks all other WPs)
**Estimated Prompt Size**: ~200 lines
**Implementation Command**: `spec-kitty implement WP01`

**Included Subtasks**:
- [ ] **T001**: Add `TpmCpoDebateStage` Literal to `debate_state.py`
- [ ] **T002**: Add `TpmCpoDebateMessage` TypedDict to `debate_state.py`
- [ ] **T003**: Add `TpmCpoDebateState` TypedDict to `debate_state.py`

**Implementation Sketch**:
1. Add imports: `Literal`, `NotRequired` from typing_extensions
2. Define `TpmCpoDebateStage = Literal["opening", "rebutal", "counter", "final_argument"]`
3. Define `TpmCpoDebateMessage` with fields: speaker, content, validated, stage
4. Define `TpmCpoDebateState` with fields: debate_topic, positions, messages, prd_input, stage, speaker, times_tpm_fact_checked, times_cpo_fact_checked, funding_decision, verdict_reasoning
5. Follow existing pattern of `DebateState` and `DebateMessage` from feature 001

**Parallel Opportunities**: None (foundation work)

**Dependencies**: None

**Risks**: 
- Ensure compatibility with existing `DebateState` usage in other workflows
- Use `NotRequired` for optional fields to maintain backward compatibility

---

## WP02: TPM Role Implementation

**Summary**: Implement TPM advocate node and prompts

**Priority**: High (required for workflow)
**Estimated Prompt Size**: ~300 lines
**Implementation Command**: `spec-kitty implement WP02 --base WP01`

**Included Subtasks**:
- [ ] **T004**: Create `tpm_prompts.py` with OPENING and COUNTER prompt templates
- [ ] **T007**: Create `tpm_node.py` with TPMNode class inheriting from BaseComponent
- [ ] **T008**: Implement `TPMNode.generate_opening()` method
- [ ] **T009**: Implement `TPMNode.generate_counter()` method

**Implementation Sketch**:
1. **T004**: Create `prompts/tpm_prompts.py`:
   - Define `OPENING_PROMPT_TEMPLATE` for opening statements
   - Define `COUNTER_PROMPT_TEMPLATE` for counter-arguments
   - Include placeholders: `{prd_input}`, `{debate_topic}`, `{cpo_rebuttal}`
2. **T007**: Create `nodes/tpm_node.py`:
   - Inherit from `BaseComponent`
   - Accept `llm_config` in constructor
   - Import prompts from `prompts.tpm_prompts`
3. **T008**: Implement `generate_opening(state)`:
   - Format prompt with prd_input and debate_topic
   - Call LLM to generate opening statement
   - Return content as string
4. **T009**: Implement `generate_counter(state)`:
   - Format prompt with prd_input, debate_topic, and CPO's rebuttal
   - Call LLM to generate counter-argument
   - Return content as string

**Parallel Opportunities**: TPM work can proceed in parallel with CPO work (WP03)

**Dependencies**: WP01 (must complete first - state required)

**Risks**:
- LLM prompt quality affects debate quality
- Must handle edge cases (empty state, missing fields)

---

## WP03: CPO Role Implementation

**Summary**: Implement CPO skeptic node and prompts

**Priority**: High (required for workflow)
**Estimated Prompt Size**: ~300 lines
**Implementation Command**: `spec-kitty implement WP03 --base WP01`

**Included Subtasks**:
- [ ] **T005**: Create `cpo_prompts.py` with REBUTTAL and FINAL_ARGUMENT prompt templates
- [ ] **T010**: Create `cpo_node.py` with CPONode class inheriting from BaseComponent
- [ ] **T011**: Implement `CPONode.generate_rebuttal()` method
- [ ] **T012**: Implement `CPONode.generate_final_argument()` method

**Implementation Sketch**:
1. **T005**: Create `prompts/cpo_prompts.py`:
   - Define `REBUTTAL_PROMPT_TEMPLATE` for rebuttal
   - Define `FINAL_ARGUMENT_PROMPT_TEMPLATE` for final argument
   - Include placeholders: `{prd_input}`, `{debate_topic}`, `{tpm_opening}`, `{debate_history}`
2. **T010**: Create `nodes/cpo_node.py`:
   - Inherit from `BaseComponent`
   - Accept `llm_config` in constructor
   - Import prompts from `prompts.cpo_prompts`
3. **T011**: Implement `generate_rebuttal(state)`:
   - Format prompt with prd_input, debate_topic, TPM's opening
   - Call LLM to generate rebuttal
   - Return content as string
4. **T012**: Implement `generate_final_argument(state)`:
   - Format prompt with prd_input, debate_topic, debate history
   - Call LLM to generate final argument
   - Return content as string

**Parallel Opportunities**: CPO work can proceed in parallel with TPM work (WP02)

**Dependencies**: WP01 (must complete first - state required)

**Risks**:
- CPO prompts must maintain skeptical tone while being constructive
- Final argument should summarize entire debate history

---

## WP04: Topic Generator

**Summary**: Implement PRD-to-topic extraction node

**Priority**: High (required for workflow)
**Estimated Prompt Size**: ~250 lines
**Implementation Command**: `spec-kitty implement WP04 --base WP01`

**Included Subtasks**:
- [ ] **T013**: Create `tpm_cpo_topic_generator_node.py` with TpmCpoTopicGeneratorNode class
- [ ] **T014**: Implement `TpmCpoTopicGeneratorNode.generate_topic()` method

**Implementation Sketch**:
1. **T013**: Create `nodes/tpm_cpo_topic_generator_node.py`:
   - Inherit from `BaseComponent`
   - Accept `llm_config` in constructor
   - Create `generate_topic(prd_text: str) -> str` method signature
2. **T014**: Implement `generate_topic()`:
   - Use LLM to extract core project concept from PRD text
   - Format as debatable topic question: "Should [project description] receive funding and be launched?"
   - Handle variable PRD lengths (short ideas to full specifications)
   - Return topic string

**Parallel Opportunities**: Can proceed in parallel with WP02 and WP03

**Dependencies**: WP01 (must complete first - for consistency with state patterns)

**Risks**:
- Long PRDs may exceed token limits
- Topic extraction quality affects entire debate focus

---

## WP05: Judge Prompts

**Summary**: Implement funding decision judge prompts

**Priority**: High (required for workflow)
**Estimated Prompt Size**: ~200 lines
**Implementation Command**: `spec-kitty implement WP05`

**Included Subtasks**:
- [ ] **T006**: Create `tpm_cpo_judge_prompts.py` with VERDICT prompt template

**Implementation Sketch**:
1. **T006**: Create `prompts/tpm_cpo_judge_prompts.py`:
   - Define `VERDICT_PROMPT_TEMPLATE` for funding decision
   - Include placeholders: `{debate_topic}`, `{prd_input}`, `{debate_history}`
   - Instruct judge to evaluate both TPM and CPO arguments
   - Require binary decision: APPROVE or DENY
   - Require reasoning explanation (2-4 paragraphs)

**Parallel Opportunities**: Can proceed in parallel with WP02, WP03, WP04

**Dependencies**: None (prompts are independent)

**Risks**:
- Judge prompt must be balanced between TPM and CPO perspectives
- Decision criteria must be clear and consistent

---

## WP06: Workflow Orchestration

**Summary**: Implement main TPM-CPO debate workflow with LangGraph

**Priority**: Critical (integrates all components)
**Estimated Prompt Size**: ~350 lines
**Implementation Command**: `spec-kitty implement WP06 --base WP01 --base WP02 --base WP03 --base WP04 --base WP05`

**Included Subtasks**:
- [ ] **T015**: Create `tpm_cpo_debate_workflow.py` with TmpCpoDebateWorkflow class
- [ ] **T016**: Implement `TmpCpoDebateWorkflow._initialize_workflow()` with all nodes
- [ ] **T017**: Implement `TmpCpoDebateWorkflow.run()` method with async invocation

**Implementation Sketch**:
1. **T015**: Create `workflow/tpm_cpo_debate_workflow.py`:
   - Import `StateGraph`, `END` from `langgraph.graph`
   - Import `TpmCpoDebateState` from `debate_state`
   - Import all node classes: `TpmCpoTopicGeneratorNode`, `TPMNode`, `CPONode`
   - Import existing: `FactCheckNode`, `FactCheckRouterNode`, `JudgeNode`
   - Define `TmpCpoDebateWorkflow` class
2. **T016**: Implement `_initialize_workflow()`:
   - Create `StateGraph(TpmCpoDebateState)`
   - Add nodes with LLM configs from `requesty_llm_config_map`
   - Set entry point to topic generator
   - Add edges: topic_gen → tpm → fact_check → cpo → fact_check → tpm → fact_check → cpo → fact_check → judge
   - Return workflow
3. **T017**: Implement `run()`:
   - Compile workflow with `workflow.compile()`
   - Initialize state with prd_input
   - Await `graph.ainvoke()` with recursion_limit
   - Return final state with funding_decision and verdict_reasoning

**Parallel Opportunities**: None (integration work)

**Dependencies**: WP01, WP02, WP03, WP04, WP05 (all must complete first)

**Risks**:
- Complex dependency graph - ensure all nodes exist before importing
- State transitions must match expected debate flow
- Recursion limit must accommodate full debate (10+ rounds)

---

## MVP Scope

**Minimum Viable Product**: WP01 + WP02 + WP03 + WP06

For a functional end-to-end demo:
1. **WP01** (State Foundation) - Required
2. **WP02** (TPM Role) - One side of debate
3. **WP03** (CPO Role) - Other side of debate
4. **WP06** (Workflow Orchestration) - Ties it all together

**Optional for MVP**:
- **WP04** (Topic Generator): Can use hardcoded topic for demo
- **WP05** (Judge Prompts): Can use existing judge node for demo

---

## Dependency Graph

```
                    ┌─────────────┐
                    │   WP01: State  │
                    │    Foundation   │
                    └─────────────┘
                          │
            ┌───────────┼────────────┬────────────┬────────────┐
            │           │            │            │            │
        ┌─────┐   ┌─────┐   ┌────────┐   ┌────────┐   ┌────────┐
        │ WP02 │   │ WP03 │   │   WP04   │   │  WP05   │
        │  TPM │   │  CPO │   │  Topic   │   │  Judge   │
        └─────┘   └─────┘   └────────┘   └────────┘   └────────┘
            │           │            │            │            │
            └───────────┴────────────┴────────────┴────────────┘
                          │
                    ┌─────────────┐
                    │   WP06:       │
                    │   Workflow    │
                    │ Orchestration  │
                    └─────────────┘
```

**Legend**:
- Boxes = Work Packages
- Lines = Dependencies (arrow points from dependent to prerequisite)
- WP02, WP03, WP04, WP05 can proceed in parallel after WP01
- WP06 requires all previous WPs to complete
