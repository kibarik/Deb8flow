---
work_package_id: "WP06"
subtasks:
  - "T015"
  - "T016"
  - "T017"
title: "Workflow Orchestration"
phase: "Phase 1 - Design & Contracts"
lane: "planned"
dependencies: ["WP01", "WP02", "WP03", "WP04", "WP05"]
assignee: ""
agent: ""
shell_pid: ""
review_status: ""
reviewed_by: ""
history:
  - timestamp: "2025-02-13T00:00:00Z"
    lane: "planned"
    agent: "system"
    shell_pid: ""
    action: "Prompt generated via /spec-kitty.tasks"
---

# Work Package Prompt: WP06 – Workflow Orchestration

## ⚠️ IMPORTANT: Review Feedback Status

**Read this first if you are implementing this task!**

- **Has review feedback?**: Check the `review_status` field above. If it says `has_feedback`, scroll to the **Review Feedback** section immediately (right below this notice).
- **You must address all feedback** before your work is complete. Feedback items are your implementation TODO list.
- **Mark as acknowledged**: When you understand the feedback and begin addressing it, update `review_status: acknowledged` in the frontmatter.
- **Report progress**: As you address each feedback item, update the Activity Log explaining what you changed.

---

## Review Feedback

> **Populated by `/spec-kitty.review`** – Reviewers add detailed feedback here when work needs changes. Implementation must address every item listed below before returning for re-review.

*[This section is empty initially. Reviewers will populate it if the work is returned from review. If you see feedback here, treat each item as a must-do before completion.]*

---

## Markdown Formatting
Wrap HTML/XML tags in backticks: `<div>`, `<script>`
Use language identifiers in code blocks: ```python, ```bash

---

## Objectives & Success Criteria

- Implement main TPM-CPO debate workflow using LangGraph StateGraph
- Orchestrate all nodes (topic generator, TPM, CPO, fact-check, judge)
- Provide async `run()` method that accepts PRD input and returns funding decision

**Success Criteria**:
- [ ] `workflow/tpm_cpo_debate_workflow.py` created with TmpCpoDebateWorkflow class
- [ ] `_initialize_workflow()` creates StateGraph with all nodes
- [ ] `run()` method accepts PRD input, returns final state
- [ ] Debate flow: topic → TPM opening → fact-check → CPO rebuttal → fact-check → TPM counter → fact-check → CPO final → fact-check → judge verdict
- [ ] Final state includes funding_decision and verdict_reasoning

## Context & Constraints

**Implementation Command**:
```bash
spec-kitty implement WP06 --base WP01 --base WP02 --base WP03 --base WP04 --base WP05
```

**Reference Documents**:
- [Data Model](../data-model.md) - State entity definitions
- [Plan](../plan.md) - Architecture decisions
- [Quickstart](../quickstart.md) - Usage examples
- [Existing debate_workflow.py](../../../../workflow/debate_workflow.py) - Reference for orchestration pattern
- [requesty_llm_config_map](../../../../configurations/llm_config.py) - LLM configuration

**Architectural Decisions**:
- Follow exact pattern of `DebateWorkflow` from existing codebase
- Use `StateGraph(TpmCpoDebateState)` for type-safe state management
- Reuse existing `FactCheckNode` and `FactCheckRouterNode` (role-agnostic)
- Entry point: topic generator (not hardcoded topic)

**Constraints**:
- Must use LangGraph StateGraph (not custom orchestration)
- Must use `TpmCpoDebateState` from WP01
- Must import all required nodes (TPM, CPO, topic generator, fact-check, judge)
- Must configure nodes with LLM configs from `requesty_llm_config_map`

## Subtasks & Detailed Guidance

### Subtask T015 – Create Workflow Class

**Purpose**: Create the main TPM-CPO debate workflow class.

**Steps**:
1. Create `workflow/tpm_cpo_debate_workflow.py`
2. Import required modules:
   ```python
   from langgraph.graph import StateGraph, END
   from debate_state import TpmCpoDebateState
   from nodes.tpm_cpo_topic_generator_node import TpmCpoTopicGeneratorNode
   from nodes.tpm_node import TPMNode
   from nodes.cpo_node import CPONode
   from nodes.fact_checker_node import FactCheckNode
   from nodes.fact_check_router_node import FactCheckRouterNode
   from nodes.judge_node import JudgeNode
   from configurations.llm_config import requesty_llm_config_map
   ```
3. Define `TmpCpoDebateWorkflow` class:
   ```python
   class TmpCpoDebateWorkflow:
       def __init__(self):
           pass  # Will add methods in subsequent subtasks
   ```

**Files**: `workflow/tpm_cpo_debate_workflow.py` (create, ~20 lines)

**Parallel?**: No (depends on all other WPs for imports)

**Notes**:
- Follow exact import pattern of `DebateWorkflow` from existing codebase
- Ensure all node imports are correct (files created in WP02, WP03, WP04)
- Use `TpmCpoDebateState` (not `DebateState`)

### Subtask T016 – Implement _initialize_workflow() Method

**Purpose**: Initialize LangGraph StateGraph with all nodes and edges.

**Steps**:
1. In `TmpCpoDebateWorkflow`, add `_initialize_workflow(self) -> StateGraph` method
2. Create workflow: `workflow = StateGraph(TpmCpoDebateState)`
3. Add nodes with LLM configs:
   ```python
   workflow.add_node("tpm_cpo_topic_generator_node", TpmCpoTopicGeneratorNode(requesty_llm_config_map["deepseek-chat"]))
   workflow.add_node("tpm_node", TPMNode(requesty_llm_config_map["deepseek-chat"]))
   workflow.add_node("cpo_node", CPONode(requesty_llm_config_map["deepseek-chat"]))
   workflow.add_node("fact_check_node", FactCheckNode())
   workflow.add_node("fact_check_router_node", FactCheckRouterNode())
   workflow.add_node("judge_node", JudgeNode(requesty_llm_config_map["deepseek-chat"]))
   ```
4. Set entry point: `workflow.set_entry_point("tpm_cpo_topic_generator_node")`
5. Add edges for debate flow:
   ```python
   workflow.add_edge("tpm_cpo_topic_generator_node", "tpm_node")
   workflow.add_edge("tpm_node", "fact_check_node")
   workflow.add_edge("cpo_node", "fact_check_node")
   workflow.add_edge("fact_check_node", "fact_check_router_node")
   workflow.add_edge("judge_node", END)
   ```
6. Return workflow

**Files**: `workflow/tpm_cpo_debate_workflow.py` (modify, add ~30 lines)

**Parallel?**: No (depends on T015)

**Notes**:
- FactCheckRouter handles conditional routing (TPM ↔ CPO alternation)
- Judge node terminates workflow (edges to END)
- Entry point is topic generator (derives topic from PRD)
- Reference existing workflow for edge pattern

### Subtask T017 – Implement run() Method

**Purpose**: Implement async run method that executes workflow and returns final state.

**Steps**:
1. In `TmpCpoDebateWorkflow`, add `async def run(self, prd_input: str) -> TpmCpoDebateState` method
2. Get workflow: `workflow = self._initialize_workflow()`
3. Compile graph: `graph = workflow.compile()`
4. Initialize state with PRD input:
   ```python
   initial_state = {
       "prd_input": prd_input,
       "debate_topic": "",
       "messages": [],
       "positions": {}
   }
   ```
5. Invoke workflow: `final_state = await graph.ainvoke(initial_state, config={"recursion_limit": 50})`
6. Return final state

**Files**: `workflow/tpm_cpo_debate_workflow.py` (modify, add ~25 lines)

**Parallel?**: No (depends on T016)

**Notes**:
- State initialization matches `TpmCpoDebateState` required fields
- Recursion limit of 50 accommodates full debate (10+ rounds)
- Method is async (matches existing workflow pattern)
- Return type is `TpmCpoDebateState` for type safety

## Test Strategy

**Manual Testing** (tests not auto-generated):
1. Create test PRD input (2-3 paragraphs describing a product idea)
2. Run workflow: `workflow = TmpCpoDebateWorkflow(); result = await workflow.run(prd_input)`
3. Verify output:
   - result["debate_topic"] is non-empty
   - result["messages"] has 8+ entries (4 rounds × 2 speakers)
   - result["funding_decision"] is "approve" or "deny"
   - result["verdict_reasoning"] is non-empty
4. Test with empty PRD: verify graceful handling

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Node import failures | High | Verify all node files exist before implementing |
| FactCheckRouter incompatibility | Medium | Reuse existing node (tested in other workflows) |
| State type mismatches | Medium | Use `TpmCpoDebateState` explicitly, not `DebateState` |
| Recursion limit exceeded | Low | Set recursion_limit to 50 (sufficient for 10+ rounds) |

## Review Guidance

**Acceptance Checkpoints**:
- [ ] `tpm_cpo_debate_workflow.py` created with TmpCpoDebateWorkflow class
- [ ] `_initialize_workflow()` returns StateGraph
- [ ] All 6 nodes added to workflow
- [ ] Entry point set to topic generator
- [ ] Edges define correct debate flow
- [ ] `run()` is async, accepts prd_input, returns TpmCpoDebateState
- [ ] State initialization uses correct field names
- [ ] Recursion limit configured

**Review Context**:
- Compare with `DebateWorkflow` implementation for consistency
- Verify node imports match files created in WP02, WP03, WP04
- Check state type is `TpmCpoDebateState` (not `DebateState`)

## Activity Log

### Updating Lane Status

To change a work package's lane, either:

1. **Edit directly**: Change the `lane:` field in frontmatter AND append activity log entry (at the end)
2. **Use CLI**: `spec-kitty agent tasks move-task WP06 --to <lane> --note "message"` (recommended)

The CLI command updates both frontmatter and activity log automatically.

**Valid lanes**: `planned`, `doing`, `for_review`, `done`

- 2025-02-13T00:00:00Z – system – lane=planned – Prompt created.
