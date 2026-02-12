---
work_package_id: "WP03"
title: "Node Unit Tests - Part 2"
lane: "planned"
dependencies: ["WP01"]
subtasks: ["T009", "T010", "T011"]
history:
  - timestamp: "2025-02-13T00:00:00Z"
    event: "Work package created"
    agent: "claude-code"
---

# Work Package: Node Unit Tests - Part 2

**Feature**: 001-Comprehensive Automated Test Suite
**Priority**: High
**Dependencies**: WP01 (Test Foundation Setup)
**Implement Command**: `spec-kitty implement WP03 --base WP01`

---

## Objective

Create comprehensive unit tests for the remaining workflow nodes: Fact Check Router, Debate Moderator, and Judge. These nodes handle workflow orchestration and final verdict generation.

---

## Context

From research.md:
- Router nodes use special Command objects for state transitions
- Judge node generates final verdict with WINNER: PRO/CON pattern
- State transitions follow deterministic flow

From data-model.md:
- Stage constants: STAGE_OPENING → STAGE_REBUTTAL → STAGE_COUNTER → STAGE_FINAL_ARGUMENT → STAGE_END
- Speaker alternation: pro → con → pro → con
- Fact-check limit: 3 failures = disqualification

Nodes to test:
1. **FactCheckRouterNode** (`nodes/fact_check_router_node.py`): Routes after fact-check
2. **DebateModeratorNode** (`nodes/debate_moderator_node.py`): Manages speaker flow
3. **JudgeNode** (`nodes/judge_node.py`): Generates final verdict

---

## Subtasks

### T009: Unit Tests for fact_check_router_node.py

**Purpose**: Ensure FactCheckRouterNode makes correct routing decisions based on fact-check results.

**Steps**:
1. Create `tests/unit/test_fact_check_router_node.py` with test cases for:
   - Routing to next speaker after passed fact-check
   - Routing to same speaker after failed fact-check (retry)
   - Handling maximum fact-check count (disqualification)
   - Command object structure validation

```python
import pytest
from nodes.fact_check_router_node import FactCheckRouterNode
from configurations.debate_constants import STAGE_OPENING, STAGE_REBUTTAL, SPEAKER_PRO, SPEAKER_CON

def test_fact_check_router_routes_to_next_speaker_after_pass():
    """Test router sends to next speaker after passed fact-check"""
    node = FactCheckRouterNode()
    state = {
        "stage": STAGE_OPENING,
        "speaker": SPEAKER_PRO,
        "validated": True,
        "times_pro_fact_checked": 0,
        "times_con_fact_checked": 0,
    }
    
    result = node(state)
    
    # After pro passes, should route to con
    assert "speaker" in result or result.get("next_speaker")
    # Should alternate speaker

def test_fact_check_router_retries_after_failure():
    """Test router allows retry after failed fact-check"""
    node = FactCheckRouterNode()
    state = {
        "stage": STAGE_OPENING,
        "speaker": SPEAKER_PRO,
        "validated": False,
        "times_pro_fact_checked": 1,  # First failure
    }
    
    result = node(state)
    
    # Should give pro another chance (not yet disqualified)
    assert state["times_pro_fact_checked"] < 3

def test_fact_check_router_disqualifies_at_three_failures():
    """Test router disqualifies speaker after 3 failures"""
    node = FactCheckRouterNode()
    state = {
        "stage": STAGE_REBUTTAL,
        "speaker": SPEAKER_PRO,
        "validated": False,
        "times_pro_fact_checked": 3,  # At limit
    }
    
    result = node(state)
    
    # Should disqualify pro, con continues
    # Verify speaker switching or stage progression
```

**Files**:
- `tests/unit/test_fact_check_router_node.py` (new, ~100 lines)

**Validation**:
- [ ] Tests cover pass/fact_check_failed routing scenarios
- [ ] Disqualification at 3 failures tested
- [ ] Command object structure validated
- [ ] Both pro and con speakers tested
- [ ] `pytest tests/unit/test_fact_check_router_node.py` passes

---

### T010: Unit Tests for debate_moderator_node.py

**Purpose**: Ensure DebateModeratorNode correctly manages debate flow and speaker transitions.

**Steps**:
1. Create `tests/unit/test_debate_moderator_node.py` with test cases for:
   - Speaker alternation (pro → con → pro → con)
   - Stage transitions (opening → rebuttal → counter → final_argument)
   - Command object generation for routing
   - Edge cases (empty message history, missing speakers)

```python
import pytest
from nodes.debate_moderator_node import DebateModeratorNode
from configurations.debate_constants import (
    STAGE_OPENING, STAGE_REBUTTAL, STAGE_COUNTER, 
    STAGE_FINAL_ARGUMENT, SPEAKER_PRO, SPEAKER_CON
)

def test_moderator_alternates_speakers():
    """Test moderator alternates between pro and con speakers"""
    node = DebateModeratorNode()
    
    # After pro, should switch to con
    state_pro = {"speaker": SPEAKER_PRO, "stage": STAGE_OPENING}
    result_pro = node(state_pro)
    assert result_pro["speaker"] == SPEAKER_CON or "next_speaker" in result_pro
    
    # After con, should switch to pro
    state_con = {"speaker": SPEAKER_CON, "stage": STAGE_REBUTTAL}
    result_con = node(state_con)
    assert result_con["speaker"] == SPEAKER_PRO or "next_speaker" in result_con

def test_moderator_transitions_stages():
    """Test moderator progresses through debate stages correctly"""
    node = DebateModeratorNode()
    
    # opening → rebuttal
    state_opening = {"speaker": SPEAKER_CON, "stage": STAGE_OPENING}
    result_rebuttal = node(state_opening)
    # Stage should progress
    
    # rebuttal → counter
    state_rebuttal = {**state_opening, "stage": STAGE_REBUTTAL}
    result_counter = node(state_rebuttal)
    
    # Verify stage transitions follow expected flow
```

**Files**:
- `tests/unit/test_debate_moderator_node.py` (new, ~110 lines)

**Validation**:
- [ ] Tests cover speaker alternation logic
- [ ] Stage transitions validated
- [ ] Command routing tested
- [ ] Edge cases included (empty history, missing fields)
- [ ] `pytest tests/unit/test_debate_moderator_node.py` passes

---

### T011: Unit Tests for judge_node.py

**Purpose**: Ensure JudgeNode generates valid verdicts with correct winner format.

**Steps**:
1. Create `tests/unit/test_judge_node.py` with test cases for:
   - Verdict generation with WINNER: PRO
   - Verdict generation with WINNER: CON
   - Message history analysis
   - Verdict structure validation

```python
import pytest
from unittest.mock import patch
from nodes.judge_node import JudgeNode
from tests.fixtures.mock_responses import MockLLMResponses
from tests.conftest import initial_state, mock_config

@pytest.mark.asyncio
async def test_judge_declares_pro_winner(mock_config, initial_state):
    """Test judge can declare pro as winner"""
    node = JudgeNode(mock_config)
    # Create state with message history
    test_state = {
        **initial_state,
        "messages": [
            {"speaker": "pro", "content": "Pro argument", "validated": True, "stage": "opening"},
            {"speaker": "con", "content": "Con argument", "validated": True, "stage": "rebuttal"},
        ]
    }
    
    with patch.object(node.__class__, 'execute_chain', return_value=MockLLMResponses.judge_verdict_pro()):
        result = node(test_state)
    
    assert "messages" in result
    final_message = result["messages"][-1]["content"]
    assert "WINNER: PRO" in final_message

@pytest.mark.asyncio
async def test_judge_declares_con_winner(mock_config, initial_state):
    """Test judge can declare con as winner"""
    node = JudgeNode(mock_config)
    test_state = {
        **initial_state,
        "messages": [
            {"speaker": "pro", "content": "Pro argument", "validated": False, "stage": "opening"},
            {"speaker": "con", "content": "Con argument", "validated": True, "stage": "rebuttal"},
        ]
    }
    
    with patch.object(node.__class__, 'execute_chain', return_value=MockLLMResponses.judge_verdict_con()):
        result = node(test_state)
    
    assert "messages" in result
    final_message = result["messages"][-1]["content"]
    assert "WINNER: CON" in final_message

def test_judge_analyzes_message_history(mock_config):
    """Test judge receives and analyzes debate history"""
    node = JudgeNode(mock_config)
    test_state = {
        **initial_state,
        "messages": [
            {"speaker": "pro", "content": "Argument 1", "validated": True, "stage": "opening"},
            {"speaker": "con", "content": "Argument 2", "validated": True, "stage": "rebuttal"},
        ]
    }
    
    # Judge should receive message history via chain input
    # Verify the node processes messages correctly
```

**Files**:
- `tests/unit/test_judge_node.py` (new, ~95 lines)

**Validation**:
- [ ] Tests cover both winner outcomes (PRO and CON)
- [ ] Verdict format validated (WINNER: pattern)
- [ ] Message history analysis tested
- [ ] Mock responses used for LLM calls
- [ ] `pytest tests/unit/test_judge_node.py` passes

---

## Implementation Sequence

1. **T009**: Create fact check router tests (20 min)
2. **T010**: Create debate moderator tests (20 min)
3. **T011**: Create judge tests (15 min)

Total estimated time: 55 minutes

---

## Test Strategy

After completing this work package, run:

```bash
# Run all new unit tests
pytest tests/unit/test_fact_check_router_node.py -v
pytest tests/unit/test_debate_moderator_node.py -v
pytest tests/unit/test_judge_node.py -v

# Run all unit tests with coverage
pytest tests/unit/ --cov=nodes --cov-report=term-missing
```

Target coverage: ≥70% for router, moderator, and judge nodes

---

## Definition of Done

- [ ] `test_fact_check_router_node.py` created with 4+ test cases
- [ ] `test_debate_moderator_node.py` created with 4+ test cases
- [ ] `test_judge_node.py` created with 3+ test cases
- [ ] All tests use appropriate mocking patterns
- [ ] Routing logic tested (speaker transitions, stage changes)
- [ ] Verdict generation tested (WINNER: pattern)
- [ ] All tests pass: `pytest tests/unit/`
- [ ] Combined coverage from WP02 + WP03 ≥80%

---

## Risks & Mitigations

| Risk | Mitigation |
|--------|-------------|
| Router Command objects may be complex to mock | Reference existing router implementation for Command structure |
| Judge verdict format may vary | Use MockLLMResponses with exact WINNER: format |
| Moderator logic may have state dependencies | Test all stage transitions, not just happy path |

---

## Reviewer Guidance

When reviewing this work package:

1. **Router logic**: Verify tests check both pass/fail routing paths
2. **State transitions**: Confirm all stage progressions are tested (opening→rebuttal→counter→final)
3. **Speaker alternation**: Check that pro→con→pro pattern is validated
4. **Verdict format**: Ensure WINNER: PRO/CON pattern is explicitly tested
5. **Coverage**: Run `pytest --cov=nodes tests/unit/` and verify ≥70%

**Key files to review**:
- `tests/unit/test_fact_check_router_node.py`
- `tests/unit/test_debate_moderator_node.py`
- `tests/unit/test_judge_node.py`

**Acceptance criteria for review**:
- All 3 test files exist
- Router tests cover pass/fail/disqualification scenarios
- Moderator tests verify speaker alternation
- Judge tests verify verdict format
- No real API calls in tests
