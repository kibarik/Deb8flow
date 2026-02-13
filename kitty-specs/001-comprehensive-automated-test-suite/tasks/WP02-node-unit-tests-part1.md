---
work_package_id: WP02
title: Node Unit Tests - Part 1
lane: "doing"
dependencies: [WP01]
base_branch: 001-comprehensive-automated-test-suite-WP01
base_commit: 1ad8d01d77f90f9befc4dc4a4854e0b91648389d
created_at: '2026-02-13T10:01:57.456197+00:00'
subtasks: [T005, T006, T007, T008]
shell_pid: "55282"
history:
- timestamp: '2025-02-13T00:00:00Z'
  event: Work package created
  agent: claude-code
---

# Work Package: Node Unit Tests - Part 1

**Feature**: 001-Comprehensive Automated Test Suite
**Priority**: High
**Dependencies**: WP01 (Test Foundation Setup)
**Implement Command**: `spec-kitty implement WP02 --base WP01`

---

## Objective

Create comprehensive unit tests for the first batch of workflow nodes: Topic Generator, Pro Debater, Con Debater, and Fact Checker. Tests use mocked LLM responses for fast, reliable execution.

---

## Context

From research.md:
- Use pytest-asyncio with `@pytest.mark.asyncio` decorator for async tests
- Mock at LLM client level using `unittest.mock.patch.object(BaseComponent, 'execute_chain')`
- Target 70-80% code coverage for node modules

From spec.md FR-1:
- Each node tested in isolation with mocked dependencies
- All execution paths covered
- Edge cases tested (invalid inputs, empty states, malformed responses)

From data-model.md:
- Tests operate on DebateState structure
- Nodes return dict updates (state deltas)
- Stage constants: STAGE_OPENING, STAGE_REBUTTAL, etc.

Nodes to test:
1. **TopicGeneratorNode** (`nodes/topic_generator_node.py`): Generates debate topic
2. **ProDebaterNode** (`nodes/pro_debater_node.py`): Generates pro arguments
3. **ConDebaterNode** (`nodes/con_debater_node.py`): Generates con arguments
4. **FactCheckNode** (`nodes/fact_checker_node.py`): Validates claims

---

## Subtasks

### T005: Unit Tests for topic_generator_node.py

**Purpose**: Ensure TopicGeneratorNode produces valid debate topics with proper state updates.

**Steps**:
1. Create `tests/unit/test_topic_generator_node.py` with the following test cases:

```python
import pytest
from unittest.mock import patch, MagicMock
from nodes.topic_generator_node import TopicGeneratorNode
from tests.fixtures.mock_responses import MockLLMResponses
from tests.conftest import initial_state, mock_config

@pytest.mark.asyncio
async def test_topic_generator_creates_topic_with_valid_state(mock_config):
    """Test that node generates a topic and updates state"""
    # Arrange
    node = TopicGeneratorNode(mock_config)
    test_state = initial_state()
    
    # Act
    with patch.object(node.__class__, 'execute_chain', return_value=MockLLMResponses.topic_generator()):
        result = node(test_state)
    
    # Assert
    assert "debate_topic" in result
    assert len(result["debate_topic"]) > 0
    assert result["stage"] == "opening"

@pytest.mark.asyncio
async def test_topic_generator_handles_empty_state(mock_config):
    """Test that node handles empty/minimal state gracefully"""
    node = TopicGeneratorNode(mock_config)
    empty_state = {
        "debate_topic": "",
        "positions": {},
        "messages": [],
        "stage": "opening",
        "speaker": "pro",
        "times_pro_fact_checked": 0,
        "times_con_fact_checked": 0,
    }
    
    with patch.object(node.__class__, 'execute_chain', return_value=MockLLMResponses.topic_generator()):
        result = node(empty_state)
    
    assert "debate_topic" in result
    assert result["debate_topic"] != ""

def test_topic_generator_initializes_correctly(mock_config):
    """Test that TopicGeneratorNode initializes with LLM config"""
    node = TopicGeneratorNode(mock_config)
    assert node.llm is not None
    assert node.output_parser is not None
```

**Files**:
- `tests/unit/test_topic_generator_node.py` (new, ~80 lines)

**Validation**:
- [ ] All tests use @pytest.mark.asyncio for async support
- [ ] execute_chain is mocked (no real API calls)
- [ ] Tests validate state updates (debate_topic field)
- [ ] Edge case included (empty state handling)
- [ ] `pytest tests/unit/test_topic_generator_node.py` passes

---

### T006: Unit Tests for pro_debater_node.py

**Purpose**: Ensure ProDebaterNode produces valid pro arguments for different debate stages.

**Steps**:
1. Create `tests/unit/test_pro_debater_node.py` with test cases for:
   - Opening statement generation
   - Counter-argument generation
   - State updates with messages
   - Stage handling

```python
import pytest
from unittest.mock import patch
from nodes.pro_debater_node import ProDebaterNode
from tests.fixtures.mock_responses import MockLLMResponses
from configurations.debate_constants import STAGE_OPENING, STAGE_COUNTER

@pytest.mark.asyncio
async def test_pro_debater_opening_statement(mock_config, initial_state):
    """Test pro debater generates opening statement"""
    node = ProDebaterNode(mock_config)
    test_state = {**initial_state, "stage": STAGE_OPENING, "speaker": "pro"}
    
    with patch.object(node.__class__, 'execute_chain', return_value=MockLLMResponses.pro_debater_opening()):
        result = node(test_state)
    
    assert "messages" in result
    assert len(result["messages"]) > 0
    assert result["messages"][-1]["speaker"] == "pro"

@pytest.mark.asyncio
async def test_pro_debater_counter_argument(mock_config):
    """Test pro debater generates counter argument"""
    node = ProDebaterNode(mock_config)
    test_state = {**initial_state, "stage": STAGE_COUNTER, "speaker": "pro"}
    
    with patch.object(node.__class__, 'execute_chain', return_value="Counter argument here"):
        result = node(test_state)
    
    assert "messages" in result
    assert result["messages"][-1]["speaker"] == "pro"
```

**Files**:
- `tests/unit/test_pro_debater_node.py` (new, ~90 lines)

**Validation**:
- [ ] Tests cover both opening and counter stages
- [ ] Message structure validated (speaker, content, validated, stage fields)
- [ ] Mock responses used consistently
- [ ] `pytest tests/unit/test_pro_debater_node.py` passes

---

### T007: Unit Tests for con_debater_node.py

**Purpose**: Ensure ConDebaterNode produces valid con arguments for rebuttal and final_argument stages.

**Steps**:
1. Create `tests/unit/test_con_debater_node.py` with similar structure to T006:
   - Rebuttal generation
   - Final argument generation
   - Message structure validation
   - Stage handling

```python
import pytest
from unittest.mock import patch
from nodes.con_debater_node import ConDebaterNode
from tests.fixtures.mock_responses import MockLLMResponses
from configurations.debate_constants import STAGE_REBUTTAL, STAGE_FINAL_ARGUMENT

@pytest.mark.asyncio
async def test_con_debater_rebuttal(mock_config, initial_state):
    """Test con debater generates rebuttal"""
    node = ConDebaterNode(mock_config)
    test_state = {**initial_state, "stage": STAGE_REBUTTAL, "speaker": "con"}
    
    with patch.object(node.__class__, 'execute_chain', return_value=MockLLMResponses.con_debater_rebuttal()):
        result = node(test_state)
    
    assert "messages" in result
    assert result["messages"][-1]["speaker"] == "con"

@pytest.mark.asyncio
async def test_con_debater_final_argument(mock_config):
    """Test con debater generates final argument"""
    node = ConDebaterNode(mock_config)
    test_state = {**initial_state, "stage": STAGE_FINAL_ARGUMENT, "speaker": "con"}
    
    with patch.object(node.__class__, 'execute_chain', return_value="Final argument here"):
        result = node(test_state)
    
    assert "messages" in result
```

**Files**:
- `tests/unit/test_con_debater_node.py` (new, ~85 lines)

**Validation**:
- [ ] Tests cover rebuttal and final_argument stages
- [ ] Speaker field validated as "con"
- [ ] State transitions tested
- [ ] `pytest tests/unit/test_con_debater_node.py` passes

---

### T008: Enhance Unit Tests for fact_checker_node.py

**Purpose**: Enhance existing fact checker tests with edge cases and better coverage.

**Steps**:
1. Review existing `tests/unit/test_fact_checker_node.py` (currently in tests/)
2. Add additional test cases for:
   - Fact check passing
   - Fact check failing (incrementing counter)
   - Disqualification at 3 failures
   - Edge cases (empty message history)

```python
import pytest
from nodes.fact_checker_node import FactCheckNode
from tests.fixtures.mock_responses import MockLLMResponses

@pytest.mark.asyncio
async def test_fact_checker_passes_valid_claim(mock_config, initial_state):
    """Test fact checker validates a valid claim"""
    node = FactCheckNode()
    test_state = {
        **initial_state,
        "messages": [{"speaker": "pro", "content": "AI was developed in the 20th century.", "validated": False, "stage": "opening"}],
        "speaker": "pro"
    }
    
    with patch.object(node.__class__, 'execute_chain', return_value=MockLLMResponses.fact_checker_passed()):
        result = node(test_state)
    
    assert result["validated"] == True
    assert "messages" in result

@pytest.mark.asyncio
async def test_fact_checker_fails_invalid_claim(mock_config, initial_state):
    """Test fact checker rejects invalid claim and increments counter"""
    node = FactCheckNode()
    test_state = {
        **initial_state,
        "messages": [{"speaker": "pro", "content": "AI was developed in the 19th century.", "validated": False, "stage": "opening"}],
        "speaker": "pro",
        "times_pro_fact_checked": 0
    }
    
    with patch.object(node.__class__, 'execute_chain', return_value=MockLLMResponses.fact_checker_failed()):
        result = node(test_state)
    
    assert result["validated"] == False
    assert result["times_pro_fact_checked"] == 1

@pytest.mark.asyncio
async def test_fact_checker_disqualifies_at_three_failures(mock_config, initial_state):
    """Test that speaker is disqualified after 3 fact check failures"""
    node = FactCheckNode()
    test_state = {
        **initial_state,
        "speaker": "pro",
        "times_pro_fact_checked": 2  # This will be the 3rd failure
    }
    
    with patch.object(node.__class__, 'execute_chain', return_value=MockLLMResponses.fact_checker_failed()):
        result = node(test_state)
    
    # After 3rd failure, should increment and potentially switch speaker
    assert result["times_pro_fact_checked"] == 3
```

**Files**:
- `tests/unit/test_fact_checker_node.py` (enhance existing, add ~60 lines)

**Validation**:
- [ ] Existing tests preserved and enhanced
- [ ] New tests cover pass/fail cases
- [ ] Disqualification logic tested (3 failures = disqualify)
- [ ] Both pro and con speaker fact-check counters tested
- [ ] `pytest tests/unit/test_fact_checker_node.py -v` shows all tests passing

---

## Implementation Sequence

1. **T005**: Create topic generator tests (15 min)
2. **T006**: Create pro debater tests (15 min)
3. **T007**: Create con debater tests (15 min)
4. **T008**: Enhance fact checker tests (20 min)

Total estimated time: 65 minutes

---

## Test Strategy

After completing this work package, run:

```bash
# Run all unit tests for this WP
pytest tests/unit/test_topic_generator_node.py -v
pytest tests/unit/test_pro_debater_node.py -v
pytest tests/unit/test_con_debater_node.py -v
pytest tests/unit/test_fact_checker_node.py -v

# Run with coverage for these modules
pytest tests/unit/test_topic_generator_node.py tests/unit/test_pro_debater_node.py tests/unit/test_con_debater_node.py tests/unit/test_fact_checker_node.py --cov=nodes --cov-report=term-missing
```

Target coverage: ≥80% for tested nodes

---

## Definition of Done

- [ ] `test_topic_generator_node.py` created with 3+ test cases
- [ ] `test_pro_debater_node.py` created with 3+ test cases
- [ ] `test_con_debater_node.py` created with 3+ test cases
- [ ] `test_fact_checker_node.py` enhanced with edge case tests
- [ ] All tests use `@pytest.mark.asyncio` decorator
- [ ] All LLM calls mocked via `patch.object(BaseComponent, 'execute_chain')`
- [ ] All tests pass: `pytest tests/unit/ -v`
- [ ] Coverage for tested nodes ≥70%

---

## Risks & Mitigations

| Risk | Mitigation |
|--------|-------------|
| Existing test_fact_checker_node.py may conflict | Review and merge with existing tests, don't overwrite |
| Mock responses may not cover all test scenarios | Add multiple mock responses per node type if needed |
| Node implementations may be async but tests don't wait | Ensure all test functions use async/await properly |

---

## Reviewer Guidance

When reviewing this work package:

1. **Test coverage**: Run `pytest --cov=nodes tests/unit/` and verify ≥70%
2. **Mock verification**: Ensure no test makes real API calls (check for patches)
3. **Async correctness**: Verify all test functions are async and use await
4. **State validation**: Check that tests assert on correct state fields
5. **Import paths**: Ensure tests can import from tests.fixtures and tests.conftest

**Key files to review**:
- `tests/unit/test_topic_generator_node.py`
- `tests/unit/test_pro_debater_node.py`
- `tests/unit/test_con_debater_node.py`
- `tests/unit/test_fact_checker_node.py`

**Acceptance criteria for review**:
- All 4 test files exist
- Each file has 3+ test cases
- Tests use mocked LLM responses
- No network calls in tests
