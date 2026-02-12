# Data Model: Comprehensive Automated Test Suite

**Feature**: 001-Comprehensive Automated Test Suite
**Date**: 2025-02-12

---

## Overview

This document describes the data structures and entities used in the test suite for Deb8flow.

---

## Test Domain Entities

### TestSuite

Represents a collection of test cases for the Deb8flow project.

| Field | Type | Description |
|-------|------|-------------|
| `name` | str | Name of the test suite (e.g., "unit", "integration", "e2e") |
| `tests` | List[TestCase] | Collection of test cases in this suite |

### TestCase

Represents a single test case with its configuration.

| Field | Type | Description |
|-------|------|-------------|
| `id` | str | Unique test identifier (e.g., "test_topic_generator_creates_valid_topic") |
| `category` | str | Test category: "unit", "integration", or "e2e" |
| `target` | str | Module/class being tested (e.g., "nodes.topic_generator_node") |
| `mocks` | List[str] | List of mocked dependencies (e.g., ["BaseComponent.execute_chain"]) |

### MockLLMResponse

Represents a mocked LLM response used in tests.

| Field | Type | Description |
|-------|------|-------------|
| `source` | str | Which node/LLM this mock is for (e.g., "topic_generator", "pro_debater") |
| `response` | str | The mocked text response |
| `structured` | bool | Whether this is a structured output (Pydantic model) |

### TestFixture

Represents a pytest fixture configuration.

| Field | Type | Description |
|-------|------|-------------|
| `name` | str | Fixture name (e.g., "mock_llm_response", "initial_state") |
| `scope` | str | Fixture scope: "function", "class", "module", or "session" |
| `autouse` | bool | Whether fixture is automatically used |

---

## Debate State (From Production)

The test suite operates on the production `DebateState` structure from `debate_state.py`:

### DebateState (TypedDict)

| Field | Type | Description |
|-------|------|-------------|
| `debate_topic` | str | The current debate topic |
| `positions` | Dict[str, str] | Pro/Con position descriptions |
| `messages` | List[DebateMessage] | List of all debate messages |
| `opening_statement_pro_agent` | str | Pro's opening statement |
| `stage` | str | Current debate stage |
| `speaker` | str | Current speaker ("pro" or "con") |
| `times_pro_fact_checked` | int | Pro's fact-check failure count |
| `times_con_fact_checked` | int | Con's fact-check failure count |

### DebateMessage (TypedDict)

| Field | Type | Description |
|-------|------|-------------|
| `speaker` | str | "pro" or "con" |
| `content` | str | The message content |
| `validated` | bool | Whether fact-check passed |
| `stage` | str | Stage when message was produced |

---

## Test Data Structures

### InitialStateFactory

Factory pattern for creating valid initial states for tests.

```python
def create_initial_state(
    topic: str = "Test topic",
    stage: str = "opening",
    speaker: str = "pro"
) -> DebateState:
    """Creates a valid initial state for testing"""
```

### MockResponseBuilder

Builder pattern for creating realistic LLM response mocks.

```python
class MockResponseBuilder:
    def for_topic_generator(self) -> str
    def for_pro_debater(self, stage: str) -> str
    def for_con_debater(self, stage: str) -> str
    def for_judge(self) -> str
```

---

## State Transition Model

The debate workflow follows a deterministic state machine:

```
[Generate Topic]
       ↓
[Opening Stage]
       ↓
[Pro Opening] → [Fact Check] → [Router]
       ↓
[Con Rebuttal] → [Fact Check] → [Router]
       ↓
[Pro Counter] → [Fact Check] → [Router]
       ↓
[Con Final] → [Fact Check] → [Router]
       ↓
[Judge Verdict]
```

### Stage Constants

From `configurations/debate_constants.py`:

| Constant | Value |
|-----------|--------|
| `STAGE_OPENING` | "opening" |
| `STAGE_REBUTTAL` | "rebuttal" |
| `STAGE_COUNTER` | "counter" |
| `STAGE_FINAL_ARGUMENT` | "final_argument" |
| `STAGE_END` | "end" |

### Speaker Constants

| Constant | Value |
|-----------|--------|
| `SPEAKER_PRO` | "pro" |
| `SPEAKER_CON` | "con" |
| `SPEAKER_JUDGE` | "judge" |

---

## Validation Rules

### State Validation

Tests should validate:

1. **State completeness**: All required fields present
2. **Type correctness**: Field values match expected types
3. **Stage progression**: Stage follows valid transitions
4. **Speaker alternation**: Pro/Con speakers alternate correctly
5. **Fact-check limits**: `times_*_fact_checked` ≤ 3

### Output Validation

Tests should validate node outputs:

1. **Required fields returned**: Each node returns expected state updates
2. **Message structure**: `DebateMessage` has all required fields
3. **Content non-empty**: Generated content is not empty
4. **Verdict format**: Judge output includes winner declaration

---

## Relationships

```
TestSuite
    ├── TestCase[]
    │       ├── targets → Node (production)
    │       └── mocks → MockLLMResponse[]
    └── TestFixture[]
            └── provides → TestState

TestState
    ├── uses → DebateState (production)
    └── validates against → StateTransitionModel
```

