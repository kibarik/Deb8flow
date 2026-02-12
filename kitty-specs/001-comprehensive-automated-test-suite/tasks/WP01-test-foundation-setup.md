---
work_package_id: WP01
title: Test Foundation Setup
lane: "for_review"
dependencies: []
base_branch: main
base_commit: eed99af94f712955289571fe23a5d2f9c813fa0b
created_at: '2026-02-12T21:26:35.727181+00:00'
subtasks: [T001, T002, T003, T004]
shell_pid: "32751"
agent: "claude"
history:
- timestamp: '2025-02-13T00:00:00Z'
  event: Work package created
  agent: claude-code
---

# Work Package: Test Foundation Setup

**Feature**: 001-Comprehensive Automated Test Suite
**Priority**: High
**Dependencies**: None
**Implement Command**: `spec-kitty implement WP01`

---

## Objective

Create the foundational test infrastructure that will be used by all subsequent test work packages. This includes directory structure, shared pytest fixtures, centralized mock LLM responses, and test dependencies.

---

## Context

The Deb8flow project currently has minimal test coverage with a few basic test files directly in `tests/`. To implement a comprehensive test suite, we need:

1. **Organized test structure**: Separate directories for fixtures, unit tests, and integration tests
2. **Shared fixtures**: Common test data and configurations available to all tests via `conftest.py`
3. **Mock responses**: Centralized location for mocked LLM responses to ensure consistency
4. **Test dependencies**: Add missing test packages (pytest-asyncio, pytest-cov)

From research.md:
- Use pytest-asyncio for async testing
- Centralized fixtures file approach (single source of truth for mocks)
- Mock at LLM client level using `unittest.mock.patch`

From data-model.md:
- Tests operate on DebateState structure from `debate_state.py`
- Need fixtures for initial state creation and mock LLM responses

---

## Subtasks

### T001: Create Test Directory Structure

**Purpose**: Set up organized directories for test categories and fixtures.

**Steps**:
1. Create the following directory structure under `tests/`:
   ```
   tests/
   ├── fixtures/
   ├── unit/
   └── integration/
   ```

2. Add `__init__.py` files to make them Python packages:
   - `tests/fixtures/__init__.py`
   - `tests/unit/__init__.py`
   - `tests/integration/__init__.py`

3. Move existing test files to appropriate locations:
   - Keep `tests/__init__.py` as-is
   - Move `test_pro_debater_node.py` → `tests/unit/`
   - Move `test_con_debater_node.py` → `tests/unit/`
   - Move `test_fact_checker_node.py` → `tests/unit/`
   - Move `test_full_workflow.py` → `tests/integration/`

**Files**:
- `tests/fixtures/__init__.py` (new, empty file)
- `tests/unit/__init__.py` (new, empty file)
- `tests/integration/__init__.py` (new, empty file)
- Move/rename existing test files

**Validation**:
- [ ] All directories exist with correct structure
- [ ] Each directory has `__init__.py`
- [ ] Existing test files are moved to unit/ or integration/
- [ ] `pytest tests/unit/` discovers tests in unit directory
- [ ] `pytest tests/integration/` discovers tests in integration directory

---

### T002: Create conftest.py with Shared Fixtures

**Purpose**: Set up shared pytest fixtures that all tests can use.

**Steps**:
1. Create `tests/conftest.py` with the following fixtures:

```python
import pytest
from typing import Dict, Any
from debate_state import DebateState

@pytest.fixture
def initial_state() -> DebateState:
    """Provides a valid initial state for tests"""
    return {
        "debate_topic": "Should AI be used in education?",
        "positions": {
            "pro": "AI enhances personalized learning",
            "con": "AI may replace human teachers"
        },
        "messages": [],
        "opening_statement_pro_agent": "",
        "stage": "opening",
        "speaker": "pro",
        "times_pro_fact_checked": 0,
        "times_con_fact_checked": 0,
    }

@pytest.fixture
def mock_config():
    """Provides a mock LLM configuration for testing"""
    from configurations.llm_config import RequestyLLMConfig
    return RequestyLLMConfig(
        model_name="test-model",
        req_api_key="test-key",
        base_url="http://test"
    )

@pytest.fixture
def empty_state() -> DebateState:
    """Provides an empty state for edge case testing"""
    return {
        "debate_topic": "",
        "positions": {},
        "messages": [],
        "opening_statement_pro_agent": "",
        "stage": "opening",
        "speaker": "pro",
        "times_pro_fact_checked": 0,
        "times_con_fact_checked": 0,
    }
```

**Files**:
- `tests/conftest.py` (new, ~60 lines)

**Validation**:
- [ ] `conftest.py` exists in tests directory
- [ ] `initial_state` fixture provides valid DebateState
- [ ] `mock_config` fixture provides test LLM config
- [ ] `empty_state` fixture provides minimal state for edge cases
- [ ] Fixtures are auto-discoverable by pytest (no import needed)

---

### T003: Create mock_responses.py with Centralized Mock LLM Responses

**Purpose**: Create realistic mock LLM responses for each node type to ensure consistent, fast tests without API calls.

**Steps**:
1. Create `tests/fixtures/mock_responses.py` with mock response builder:

```python
"""Centralized mock LLM responses for testing"""

class MockLLMResponses:
    """Factory for creating realistic mock LLM responses"""
    
    @staticmethod
    def topic_generator() -> str:
        return """Artificial Intelligence in Healthcare: Promise or Peril?
        
        The integration of AI into healthcare systems presents both unprecedented opportunities 
        for improving patient outcomes and significant ethical challenges that must be 
        carefully navigated."""

    @staticmethod
    def pro_debater_opening() -> str:
        return """Ladies and gentlemen, the integration of Artificial Intelligence 
        into healthcare represents one of the most promising frontiers in modern medicine. 
        AI systems can analyze medical images with greater accuracy than human radiologists, 
        predict patient deterioration hours before it becomes clinically apparent, and personalize 
        treatment plans based on comprehensive patient data."""

    @staticmethod
    def con_debater_rebuttal() -> str:
        return """While the potential benefits of AI in healthcare are noteworthy, 
        we must not overlook the significant risks. AI systems can perpetuate biases 
        present in their training data, leading to disparities in care delivery. 
        There are also concerns about diagnostic errors and the lack of transparency 
        in AI decision-making processes."""

    @staticmethod
    def fact_checker_passed() -> str:
        return "PASSED"

    @staticmethod
    def fact_checker_failed() -> str:
        return "FAILED"

    @staticmethod
    def judge_verdict_pro() -> str:
        return """After carefully considering both arguments presented during this debate, 
        I have reached a decision. The PRO side effectively demonstrated the 
        transformative potential of AI in healthcare while acknowledging the genuine concerns 
        raised by the CON side. 
        
        WINNER: PRO"""

    @staticmethod
    def judge_verdict_con() -> str:
        return """After careful evaluation of the debate, the CON side successfully 
        highlighted critical implementation challenges and ethical considerations that cannot be 
        ignored.
        
        WINNER: CON"""
```

**Files**:
- `tests/fixtures/mock_responses.py` (new, ~80 lines)
- `tests/fixtures/__init__.py` (update to export MockLLMResponses)

**Validation**:
- [ ] `mock_responses.py` contains responses for all 7 node types
- [ ] Responses are realistic and match expected formats
- [ ] Judge responses include "WINNER: PRO" or "WINNER: CON" pattern
- [ ] All responses are non-empty strings
- [ ] Class can be imported as `from tests.fixtures.mock_responses import MockLLMResponses`

---

### T004: Update requirements.txt with Test Dependencies

**Purpose**: Ensure all required testing packages are available.

**Steps**:
1. Review current `requirements.txt` to identify existing test dependencies
2. Add the following if not present:
   ```
   pytest-asyncio>=0.21.0
   pytest-cov>=4.0.0
   ```

3. Verify version compatibility with Python 3.10+

**Files**:
- `requirements.txt` (modify, add 2 lines)

**Validation**:
- [ ] `pytest-asyncio` is in requirements.txt
- [ ] `pytest-cov` is in requirements.txt
- [ ] Versions are compatible with Python 3.10+
- [ ] `pip install -r requirements.txt` completes without errors

---

## Implementation Sequence

1. **T001**: Create directory structure (5 min)
2. **T002**: Create conftest.py fixtures (10 min)
3. **T003**: Create mock responses (15 min)
4. **T004**: Update requirements.txt (5 min)

Total estimated time: 35 minutes

---

## Test Strategy

This work package creates test infrastructure, so testing focuses on:

1. **Structure validation**: Ensure pytest can discover tests in new directories
2. **Fixture functionality**: Verify fixtures provide valid data
3. **Import paths**: Ensure tests can import from fixtures

Run these validation commands after completion:
```bash
# Test discovery
pytest --collect-only tests/unit/
pytest --collect-only tests/integration/

# Test fixtures work
python -c "from tests.fixtures.mock_responses import MockLLMResponses; print(MockLLMResponses.topic_generator())"

# Verify dependencies
pip list | grep pytest
```

---

## Definition of Done

- [ ] Test directory structure exists with fixtures/, unit/, integration/ subdirectories
- [ ] Each subdirectory has `__init__.py` making them Python packages
- [ ] Existing test files moved to appropriate subdirectories
- [ ] `tests/conftest.py` provides initial_state, mock_config, empty_state fixtures
- [ ] `tests/fixtures/mock_responses.py` contains realistic mocks for all node types
- [ ] `requirements.txt` includes pytest-asyncio and pytest-cov
- [ ] Pytest can discover tests in new structure
- [ ] All fixtures are importable without errors

---

## Risks & Mitigations

| Risk | Mitigation |
|--------|-------------|
| Existing test files may break when moved | Update imports after moving to new locations |
| Mock responses may not match real LLM output patterns | Use examples from actual debate runs if available |
| Directory structure may conflict with existing test patterns | Follow standard pytest conventions (fixtures/, unit/, integration/) |

---

## Reviewer Guidance

When reviewing this work package:

1. **Check directory structure**: Verify tests/fixtures/, tests/unit/, tests/integration/ exist
2. **Verify fixture quality**: Fixtures should return valid DebateState structures
3. **Mock response realism**: Responses should be similar format to actual LLM outputs
4. **Import test**: Try importing fixtures from a test file
5. **Backward compatibility**: Ensure existing tests still work after restructuring

**Key files to review**:
- `tests/conftest.py` (shared fixtures)
- `tests/fixtures/mock_responses.py` (mock data)
- `requirements.txt` (dependencies)

## Activity Log

- 2026-02-12T21:28:37Z – claude – shell_pid=32751 – lane=for_review – Moved to for_review
