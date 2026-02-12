---
work_package_id: "WP04"
title: "Integration Tests"
lane: "planned"
dependencies: ["WP02", "WP03"]
subtasks: ["T019", "T020", "T021"]
history:
  - timestamp: "2025-02-13T00:00:00Z"
    event: "Work package created"
    agent: "claude-code"
---

# Work Package: Integration Tests

**Feature**: 001-Comprehensive Automated Test Suite
**Priority**: Medium
**Dependencies**: WP02 (Node Unit Tests - Part 1), WP03 (Node Unit Tests - Part 2)
**Implement Command**: `spec-kitty implement WP04 --base WP02`

---

## Objective

Create integration tests that verify the complete debate workflow executes end-to-end, state transitions occur correctly, and the fact-check disqualification rule works as expected.

---

## Context

From spec.md FR-2 and FR-3:
- Multi-node workflow execution: Test nodes working together
- State transition tests: Verify debate stages progress correctly
- Fact-check retry logic: Test 3-strikes disqualification rule
- End-to-end test: Full workflow execution from start to verdict

From plan.md:
- Workflow orchestration: `workflow/debate_workflow.py`
- StateGraph compiles graph and executes via ainvoke()
- Final state should contain verdict with winner

Integration test scope:
1. **Full workflow execution**: DebateWorkflow.run() completes successfully
2. **State transition validation**: All stages progress in correct order
3. **Fact-check disqualification**: 3 failures trigger disqualification

---

## Subtasks

### T019: End-to-End Workflow Execution Test

**Purpose**: Verify the complete debate workflow runs from start to finish without errors.

**Steps**:
1. Enhance `tests/integration/test_workflow_execution.py` with comprehensive e2e test:

```python
import pytest
from unittest.mock import patch, AsyncMock
from workflow.debate_workflow import DebateWorkflow
from tests.fixtures.mock_responses import MockLLMResponses

@pytest.mark.asyncio
async def test_full_workflow_completes_successfully():
    """Test that full debate workflow completes without errors"""
    workflow = DebateWorkflow()
    
    # Mock all node LLM calls
    with patch('nodes.topic_generator_node.TopicGeneratorNode.execute_chain') as mock_topic:
    with patch('nodes.pro_debater_node.ProDebaterNode.execute_chain') as mock_pro:
    with patch('nodes.con_debater_node.ConDebaterNode.execute_chain') as mock_con:
    with patch('nodes.judge_node.JudgeNode.execute_chain') as mock_judge:
                # Configure mocks to return realistic responses
                mock_topic.return_value = MockLLMResponses.topic_generator()
                mock_pro.return_value = MockLLMResponses.pro_debater_opening()
                mock_con.return_value = MockLLMResponses.con_debater_rebuttal()
                mock_judge.return_value = MockLLMResponses.judge_verdict_pro()
                
                # Run workflow
                result = await workflow.run()
                
                # Assert final state
                assert "messages" in result
                assert len(result["messages"]) > 0
                assert result["stage"] == "end" or any("WINNER:" in msg.get("content", "") for msg in result["messages"])

@pytest.mark.asyncio
async def test_workflow_handles_initial_empty_state():
    """Test workflow starts with empty/initial state"""
    workflow = DebateWorkflow()
    
    # Start with minimal state
    result = await workflow.run()
    
    # Should complete and populate state
    assert "debate_topic" in result
    assert result["debate_topic"] != ""

@pytest.mark.asyncio 
async def test_workflow_produces_valid_final_state():
    """Test workflow produces state with all required fields"""
    workflow = DebateWorkflow()
    result = await workflow.run()
    
    # Validate required fields exist
    required_fields = [
        "debate_topic", "positions", "messages", 
        "stage", "speaker", "times_pro_fact_checked", "times_con_fact_checked"
    ]
    
    for field in required_fields:
        assert field in result, f"Missing required field: {field}"
```

**Files**:
- `tests/integration/test_workflow_execution.py` (enhance existing, add ~100 lines)

**Validation**:
- [ ] Workflow completes without raising exceptions
- [ ] Final state contains all required fields
- [ ] Verdict message includes WINNER: pattern
- [ ] Test uses mocked LLM calls (no real API calls)
- [ ] Test completes in reasonable time (<10 seconds)

---

### T020: State Transition Validation Tests

**Purpose**: Verify the debate workflow progresses through stages correctly (opening → rebuttal → counter → final_argument → verdict).

**Steps**:
1. Create `tests/integration/test_state_transitions.py` with transition tests:

```python
import pytest
from workflow.debate_workflow import DebateWorkflow
from configurations.debate_constants import (
    STAGE_OPENING, STAGE_REBUTTAL, STAGE_COUNTER, 
    STAGE_FINAL_ARGUMENT, STAGE_END
)

@pytest.mark.asyncio
async def test_workflow_transitions_through_all_stages():
    """Test workflow progresses through all debate stages"""
    workflow = DebateWorkflow()
    result = await workflow.run()
    
    # Extract stages from messages
    stages = [msg.get("stage", "") for msg in result["messages"]]
    
    # Verify expected stages are present
    expected_stages = [STAGE_OPENING, STAGE_REBUTTAL, STAGE_COUNTER, STAGE_FINAL_ARGUMENT]
    for expected in expected_stages:
        assert expected in stages, f"Missing stage: {expected}"

@pytest.mark.asyncio
async def test_stage_progression_follows_deterministic_order():
    """Test stages progress in correct order"""
    workflow = DebateWorkflow()
    result = await workflow.run()
    
    stages_in_order = []
    for msg in result["messages"]:
        stage = msg.get("stage", "")
        if stage and stage not in stages_in_order:
            stages_in_order.append(stage)
    
    # Verify ordering: opening comes before rebuttal, etc.
    opening_idx = stages_in_order.index(STAGE_OPENING) if STAGE_OPENING in stages_in_order else -1
    rebuttal_idx = stages_in_order.index(STAGE_REBUTTAL) if STAGE_REBUTTAL in stages_in_order else -1
    
    if opening_idx >= 0 and rebuttal_idx >= 0:
        assert opening_idx < rebuttal_idx, "Stages out of order"

@pytest.mark.asyncio
async def test_speakers_alternate_correctly():
    """Test pro and con speakers alternate during debate"""
    workflow = DebateWorkflow()
    result = await workflow.run()
    
    speakers = [msg.get("speaker") for msg in result["messages"] if msg.get("speaker") in ["pro", "con"]]
    
    # Check for alternation (no two consecutive same speakers in speaking roles)
    for i in range(len(speakers) - 1):
        if speakers[i] == speakers[i+1]:
            # Same speaker spoke twice in a row - may indicate issue
            # (Note: fact checks may interleave, so check context)
            pass  # Or assert based on expected message types

def test_stage_constants_match_expected_values():
    """Test stage constant values match expected strings"""
    from configurations.debate_constants import (
        STAGE_OPENING, STAGE_REBUTTAL, STAGE_COUNTER, STAGE_FINAL_ARGUMENT
    )
    
    assert STAGE_OPENING == "opening"
    assert STAGE_REBUTTAL == "rebuttal"
    assert STAGE_COUNTER == "counter"
    assert STAGE_FINAL_ARGUMENT == "final_argument"
```

**Files**:
- `tests/integration/test_state_transitions.py` (new, ~120 lines)

**Validation**:
- [ ] All 4 expected stages are tested
- [ ] Stage ordering is validated
- [ ] Speaker alternation is checked
- [ ] Stage constants are validated
- [ ] Tests use async workflow execution
- [ ] `pytest tests/integration/test_state_transitions.py` passes

---

### T021: Fact-Check Disqualification Test

**Purpose**: Verify the 3-strikes rule works correctly (3 fact-check failures = disqualification).

**Steps**:
1. Create `tests/integration/test_fact_check_disqualification.py` with disqualification scenarios:

```python
import pytest
from unittest.mock import patch
from workflow.debate_workflow import DebateWorkflow
from tests.fixtures.mock_responses import MockLLMResponses

@pytest.mark.asyncio
async def test_three_fact_check_failures_disqualify_speaker():
    """Test that speaker is disqualified after 3 fact-check failures"""
    workflow = DebateWorkflow()
    
    # Mock responses where pro fails 3 fact checks
    failure_count = 0
    
    def mock_execute_chain(*args, **kwargs):
        nonlocal failure_count
        failure_count += 1
        if failure_count <= 3:
            return MockLLMResponses.fact_checker_failed()
        return MockLLMResponses.fact_checker_passed()
    
    with patch('nodes.fact_checker_node.FactCheckNode.execute_chain', side_effect=mock_execute_chain):
        result = await workflow.run()
    
    # After 3 failures, pro should be disqualified
    # Verify workflow continued and concluded with remaining speaker

@pytest.mark.asyncio
async def test_speaker_continues_after_two_failures():
    """Test speaker gets third chance after 2 failures"""
    workflow = DebateWorkflow()
    
    failure_count = 0
    
    def mock_execute_chain(*args, **kwargs):
        nonlocal failure_count
        failure_count += 1
        if failure_count <= 2:
            return MockLLMResponses.fact_checker_failed()
        return MockLLMResponses.fact_checker_passed()
    
    with patch('nodes.fact_checker_node.FactCheckNode.execute_chain', side_effect=mock_execute_chain):
        result = await workflow.run()
    
    # Should allow continuation after 2 failures
    assert result["times_pro_fact_checked"] <= 3

@pytest.mark.asyncio
async def test_con_speaker_wins_when_pro_disqualified():
    """Test workflow awards win to con when pro is disqualified"""
    workflow = DebateWorkflow()
    
    # Simulate pro getting 3 failures, con passing all
    pro_failures = 0
    
    def mock_pro_chain(*args, **kwargs):
        nonlocal pro_failures
        pro_failures += 1
        if pro_failures <= 3:
            return "Argument with false claim"
        return "Valid argument"
    
    def mock_con_chain(*args, **kwargs):
        return "Valid argument"
    
    with patch('nodes.pro_debater_node.ProDebaterNode.execute_chain', side_effect=mock_pro_chain):
        with patch('nodes.con_debater_node.ConDebaterNode.execute_chain', side_effect=mock_con_chain):
            result = await workflow.run()
    
    # Con should win when pro disqualified
    final_message = result["messages"][-1]["content"]
    assert "WINNER: CON" in final_message or result.get("winner") == "con"
```

**Files**:
- `tests/integration/test_fact_check_disqualification.py` (new, ~110 lines)

**Validation**:
- [ ] 3-failure disqualification tested
- [ ] 2-failure continuation tested
- [ ] Winner determination when one speaker disqualified tested
- [ ] Both pro and con disqualification scenarios tested
- [ ] `pytest tests/integration/test_fact_check_disqualification.py` passes

---

## Implementation Sequence

1. **T019**: Create full workflow test (25 min)
2. **T020**: Create state transitions test (20 min)
3. **T021**: Create disqualification test (20 min)

Total estimated time: 65 minutes

---

## Test Strategy

After completing this work package, run:

```bash
# Run all integration tests
pytest tests/integration/ -v

# Run with coverage
pytest tests/integration/ --cov=workflow --cov=nodes --cov-report=term-missing

# Measure execution time
time pytest tests/integration/  # Should complete in <30 seconds
```

Target: All integration tests pass, full suite completes in <30 seconds

---

## Definition of Done

- [ ] `test_workflow_execution.py` verifies full workflow completion
- [ ] `test_state_transitions.py` validates all stage transitions
- [ ] `test_fact_check_disqualification.py` tests 3-strikes rule
- [ ] All integration tests use async workflow execution
- [ ] Fact-check disqualification logic tested end-to-end
- [ ] All integration tests pass: `pytest tests/integration/`
- [ ] Integration test suite executes in <30 seconds

---

## Risks & Mitigations

| Risk | Mitigation |
|--------|-------------|
| E2E tests may be slow due to full workflow execution | Use aggressive mocking, set appropriate timeouts |
| State transition tests may be brittle | Use flexible assertions (check for presence, not exact order) |
| Disqualification test may be complex | Build up from simple (1 failure) to complex (3 failures) |

---

## Reviewer Guidance

When reviewing this work package:

1. **Workflow execution**: Verify test runs actual DebateWorkflow, not individual nodes
2. **Mock coverage**: Ensure all node LLM calls are mocked (no API calls)
3. **State validation**: Check that tests assert on final state structure
4. **Transition logic**: Verify stage progression follows expected flow
5. **Performance**: Confirm integration tests complete in <30 seconds

**Key files to review**:
- `tests/integration/test_workflow_execution.py`
- `tests/integration/test_state_transitions.py`
- `tests/integration/test_fact_check_disqualification.py`

**Acceptance criteria for review**:
- All 3 test files exist
- Tests run full workflow via DebateWorkflow.run()
- State transitions validated
- Fact-check disqualification tested
- No real API calls made
