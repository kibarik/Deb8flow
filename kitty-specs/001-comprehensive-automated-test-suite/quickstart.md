# Quick Start Guide: Automated Test Suite

**Feature**: 001-Comprehensive Automated Test Suite
**Last Updated**: 2025-02-12

---

## Overview

This guide helps you quickly get started with running and writing tests for the Deb8flow project.

---

## Prerequisites

1. **Python Environment**: Python 3.10+
2. **Virtual Environment**: Activate your project's venv
   ```bash
   source venv/bin/activate  # macOS/Linux
   # or
   venv\Scripts\activate  # Windows
   ```

3. **Dependencies Installed**:
   ```bash
   pip install -r requirements.txt
   ```

---

## Running Tests

### Run All Tests

```bash
pytest
```

### Run Specific Test Categories

```bash
# Unit tests only
pytest tests/unit/

# Integration tests only  
pytest tests/integration/

# Specific test file
pytest tests/unit/test_topic_generator_node.py

# Specific test function
pytest tests/unit/test_topic_generator_node.py::test_topic_generator_creates_valid_topic
```

### Run with Coverage Report

```bash
# Generate coverage report
pytest --cov=. --cov-report=html --cov-report=term

# View HTML report (opens in browser)
open htmlcov/index.html  # macOS
# or
xdg-open htmlcov/index.html  # Linux
```

### Run Verbose Output

```bash
pytest -v  # Show test names
pytest -vv  # Show more detail
pytest -s  # Show print statements
```

---

## Writing New Tests

### Basic Test Structure

```python
# tests/unit/test_new_node.py
import pytest
from nodes.new_node import NewNode
from tests.fixtures.mock_responses import mock_llm_response
from unittest.mock import patch

@pytest.mark.asyncio
async def test_new_node_produces_valid_output():
    """Test that NewNode produces valid state update"""
    # Arrange
    node = NewNode(mock_config)
    initial_state = create_initial_state()
    
    # Act
    with patch.object(BaseComponent, 'execute_chain', return_value="Mock response"):
        result = node(initial_state)
    
    # Assert
    assert "messages" in result
    assert result["stage"] in valid_stages
```

### Using Fixtures

```python
# tests/conftest.py - Shared fixtures
@pytest.fixture
def initial_state():
    """Provides a valid initial state for tests"""
    return {
        "debate_topic": "Test topic",
        "positions": {"pro": "In favor", "con": "Against"},
        "messages": [],
        "stage": "opening",
        "speaker": "pro",
        "times_pro_fact_checked": 0,
        "times_con_fact_checked": 0,
    }

# Use in your test
def test_with_fixture(initial_state):
    assert initial_state["stage"] == "opening"
```

### Mocking LLM Responses

```python
from unittest.mock import patch, MagicMock

def test_node_with_mocked_llm():
    """Test node behavior without real API calls"""
    # Mock the LLM chain execution
    with patch('nodes.base_component.BaseComponent.execute_chain') as mock_exec:
        mock_exec.return_value = "This is a mocked LLM response"
        
        node = TopicGeneratorNode(mock_config)
        result = node(initial_state)
        
        # Verify the mock was called
        mock_exec.assert_called_once()
        
        # Assert on the result
        assert "topic" in result
```

---

## Test Organization

```
tests/
├── fixtures/
│   └── mock_responses.py    # All mock LLM responses
├── conftest.py              # Shared pytest fixtures
├── unit/                    # Unit tests for individual nodes
│   ├── test_topic_generator_node.py
│   ├── test_pro_debater_node.py
│   ├── test_con_debater_node.py
│   ├── test_fact_checker_node.py
│   ├── test_debate_moderator_node.py
│   └── test_judge_node.py
└── integration/              # Multi-node tests
    └── test_workflow_execution.py
```

---

## Common Test Patterns

### Testing State Transitions

```python
def test_stage_progression():
    """Test that workflow stages progress correctly"""
    state = create_initial_state(stage="opening")
    
    # After pro debater, stage might change
    result = pro_node(state)
    assert result["stage"] in ["opening", "rebuttal", "counter"]
```

### Testing Fact-Check Logic

```python
def test_fact_check_accumulation():
    """Test that fact-check failures accumulate"""
    state = create_initial_state(times_pro_fact_checked=2)
    
    result = fact_checker_node(state, validated=False)
    
    assert result["times_pro_fact_checked"] == 3
    # At 3 failures, speaker should be disqualified
    assert result["speaker"] == "con"  # Only con remains
```

### Testing Workflow Completion

```python
@pytest.mark.asyncio
async def test_full_workflow_completes():
    """Test that full workflow reaches verdict"""
    workflow = DebateWorkflow()
    result = await workflow.run()
    
    # Check final state
    assert "messages" in result
    assert any("WINNER:" in msg.get("content", "") for msg in result["messages"])
```

---

## Troubleshooting

### Tests Fail with "No module named 'nodes'"

**Solution**: Run tests from project root:
```bash
pytest  # Run from /path/to/Deb8flow/
```

### Async Tests Fail with "coroutine never awaited"

**Solution**: Ensure pytest-asyncio is installed and using `@pytest.mark.asyncio`:
```bash
pip install pytest-asyncio
```

### Coverage Shows Missing Lines

**Solution**: This is normal for some branches. Focus on:
- Core logic paths (aim for 80%+)
- Critical workflow code (aim for 100%)

### Tests Pass Locally But Fail in CI

**Common causes**:
1. Missing environment variables → Tests should mock these
2. Dependency version differences → Use same requirements.txt
3. File path issues → Use absolute paths or project-relative paths

---

## Best Practices

1. **Test Behavior, Not Implementation**: Focus on what the code does, not how
2. **One Assertion Per Test**: Keep tests focused and readable
3. **Descriptive Test Names**: `test_node_does_x_when_y` format
4. **Arrange-Act-Assert**: Structure tests clearly
5. **Mock External Dependencies**: Don't call real APIs in tests
6. **Test Edge Cases**: Empty inputs, boundary conditions, error paths

---

## Next Steps

1. Run the test suite to see current status: `pytest`
2. Check coverage: `pytest --cov=. --cov-report=term`
3. Add tests for new nodes you create
4. Run tests before committing code

