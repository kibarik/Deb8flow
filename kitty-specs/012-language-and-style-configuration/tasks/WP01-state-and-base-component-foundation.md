---
work_package_id: WP01
title: State & Base Component Foundation
lane: planned
dependencies: []
subtasks:
- T001
- T002
- T003
- T004
- T005
- T006
phase: Phase 1 - Foundation
assignee: ''
agent: ''
shell_pid: ''
review_status: ''
reviewed_by: ''
history:
- timestamp: '2025-02-17T16:00:00Z'
  lane: planned
  agent: system
  shell_pid: ''
  action: Prompt generated via /spec-kitty.tasks
---

# Work Package Prompt: WP01 – State & Base Component Foundation

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
Use language identifiers in code blocks: `python`, `bash`

---

## Objectives & Success Criteria

**Primary Objective**: Add the `language_setting` field to `DebateState` and implement centralized language injection in `BaseComponent`.

**Success Criteria**:
- `DebateState` includes `language_setting: NotRequired[Optional[str]]` field
- `BaseComponent.__call__()` captures `language_setting` from state when present
- `BaseComponent.create_chain()` accepts optional `language_setting` parameter
- Language injection prepends to system template when `language_setting` is truthy
- Contract test validates `language_setting` field in DebateState
- Unit test validates language injection logic in BaseComponent
- Existing code continues to work without modification (backward compatibility)

---

## Context & Constraints

**Feature Specification**: [spec.md](../spec.md)
**Implementation Plan**: [plan.md](../plan.md)
**Data Model**: [data-model.md](../data-model.md)

**Key Design Decisions**:
1. **Centralized Injection**: Language setting injected in `BaseComponent.create_chain()`, not in individual prompt files
2. **Backward Compatibility**: Field is `NotRequired[Optional[str]]` - existing states without the field work unchanged
3. **Injection Format**: `\n\n**Language and Style Setting**: {language_setting}\n\n` prepended to system template

**Constitution Requirements** (from `.kittify/memory/constitution.md`):
- Python 3.12+ with asyncio support
- Self-documenting code preferred
- Minimal dependencies (no new libraries)

**Technical Constraints**:
- No breaking changes to existing `create_chain()` signature (parameter must be optional)
- Language setting passed through `DebateState` - no new propagation mechanism
- All agents inherit from `BaseComponent`, so one change affects all

---

## Subtasks & Detailed Guidance

### Subtask T001 – Add language_setting to DebateState

**Purpose**: Add the `language_setting` field to the `DebateState` TypedDict to carry language preferences through the workflow.

**Files**:
- `debate_state.py` (repository root)

**Steps**:

1. **Read the current DebateState definition**:
   ```python
   # debate_state.py
   class DebateState(TypedDict):
       debate_topic: str
       positions: Dict[str, str]
       messages: List[DebateMessage]
       # ... existing fields ...
   ```

2. **Add the new field** at the end of the TypedDict:
   ```python
   language_setting: NotRequired[Optional[str]]  # Language/style instruction for all agents
   ```

3. **Verify imports** include:
   ```python
   from typing_extensions import NotRequired
   ```

4. **No other changes needed** - the field is optional and backward compatible

**Validation**:
- [ ] File compiles without errors
- [ ] Existing code that creates DebateState instances still works
- [ ] New field can be included or omitted from state dictionaries

**Notes**:
- Position at end of TypedDict to minimize merge conflicts
- Use `NotRequired[Optional[str]]` double wrapper for maximum compatibility
- Field may be absent OR None - both are valid

---

### Subtask T002 – Add contract test for language_setting

**Purpose**: Validate that `language_setting` field is properly defined in DebateState and accepts expected values.

**Files**:
- `tests/contract/test_debate_state.py`

**Steps**:

1. **Add a new test function**:
   ```python
   def test_language_setting_field():
       """Test that language_setting field is properly defined."""
       from debate_state import DebateState

       # Test with language_setting present
       state_with_language: DebateState = {
           "debate_topic": "Test topic",
           "positions": {},
           "messages": [],
           "language_setting": "Русский официальный стиль"
       }

       # Test without language_setting (backward compatibility)
       state_without_language: DebateState = {
           "debate_topic": "Test topic",
           "positions": {},
           "messages": []
           # language_setting omitted
       }

       # Test with None value
       state_with_none: DebateState = {
           "debate_topic": "Test topic",
           "positions": {},
           "messages": [],
           "language_setting": None
       }
   ```

2. **Run the test**:
   ```bash
   pytest tests/contract/test_debate_state.py::test_language_setting_field -v
   ```

**Validation**:
- [ ] Test passes with language_setting present
- [ ] Test passes with language_setting omitted
- [ ] Test passes with language_setting = None
- [ ] Type checker accepts all three variants

**Notes**:
- Contract tests validate the "shape" of data structures
- No need to test runtime behavior here (that's T006)

---

### Subtask T003 – Modify BaseComponent.__call__() to capture language_setting

**Purpose**: Capture the `language_setting` from state when BaseComponent is called, making it available for prompt injection.

**Files**:
- `nodes/base_component.py`

**Steps**:

1. **Locate the `__call__` method**:
   ```python
   def __call__(self, state: DebateState) -> None:
       """Updates the node's local copy of the state."""
       self.state = state
       for key, value in state.items():
           setattr(self, key, value)
   ```

2. **Add language_setting capture** (existing pattern already handles this via the loop):
   ```python
   # The existing for loop already captures all state fields
   # including language_setting. No changes needed to __call__.
   ```

3. **Verify** that `self.language_setting` will be available after `__call__` executes.

**Validation**:
- [ ] After `__call__(state)` executes, `self.language_setting` reflects state value
- [ ] Works when `language_setting` is absent (attribute not set)
- [ ] Works when `language_setting` is None (attribute set to None)

**Notes**:
- The existing `setattr` loop already handles this automatically
- No code changes needed - this subtask is for understanding/verification
- If the loop doesn't exist, add: `self.language_setting = state.get("language_setting")`

---

### Subtask T004 – Modify BaseComponent.create_chain() to accept language_setting

**Purpose**: Extend `create_chain()` signature to accept an optional `language_setting` parameter for prompt injection.

**Files**:
- `nodes/base_component.py`

**Steps**:

1. **Read current `create_chain()` signature**:
   ```python
   def create_chain(
       self, system_template: str, human_template: str
   ) -> RunnableSequence:
       """Creates a chain for unstructured outputs."""
       self.validate_initialization()
       self.prompt_template = ChatPromptTemplate.from_messages([
           ("system", system_template),
           ("human", human_template),
       ])
       self.chain = self.prompt_template | self.llm | self.output_parser
       return self.chain
   ```

2. **Add optional parameter** (maintains backward compatibility):
   ```python
   def create_chain(
       self, system_template: str, human_template: str, language_setting: Optional[str] = None
   ) -> RunnableSequence:
   ```

3. **Add import** if not present:
   ```python
   from typing import Optional
   ```

**Validation**:
- [ ] Existing calls to `create_chain()` without language_setting still work
- [ ] New calls can pass `language_setting="some text"`
- [ ] Type signature accepts both usages

**Notes**:
- Default value of `None` ensures backward compatibility
- Don't implement injection yet (that's T005)

---

### Subtask T005 – Implement language injection logic

**Purpose**: Inject the language setting into the system template when present, using the specified format.

**Files**:
- `nodes/base_component.py`

**Steps**:

1. **Add injection logic** after `validate_initialization()`:
   ```python
   def create_chain(
       self, system_template: str, human_template: str, language_setting: Optional[str] = None
   ) -> RunnableSequence:
       """Creates a chain for unstructured outputs."""
       self.validate_initialization()

       # Inject language setting into system template if provided
       if language_setting:
           injection = f"\n\n**Language and Style Setting**: {language_setting}\n\n"
           system_template = injection + system_template

       self.prompt_template = ChatPromptTemplate.from_messages([
           ("system", system_template),
           ("human", human_template),
       ])
       self.chain = self.prompt_template | self.llm | self.output_parser
       return self.chain
   ```

2. **Verify injection format** matches specification:
   - Double newline before and after
   - Bold heading with asterisks
   - No trailing spaces

**Validation**:
- [ ] When `language_setting=None`, system_template unchanged
- [ ] When `language_setting="Русский"`, injection prepended correctly
- [ ] Original system_template content preserved after injection
- [ ] Empty string `""` is falsy, no injection occurs

**Notes**:
- String concatenation is simple and reliable
- Using `if language_setting:` handles None, "", and other falsy values
- Injection at beginning of system template ensures maximum visibility

---

### Subtask T006 – Add unit test for language injection

**Purpose**: Verify that language injection works correctly in BaseComponent and doesn't break existing behavior.

**Files**:
- `tests/nodes/` (create new test file if needed, or add to existing)

**Steps**:

1. **Create test file** `tests/nodes/test_base_component_language.py`:
   ```python
   import pytest
   from nodes.base_component import BaseComponent
   from configurations.llm_config import OpenAILLMConfig
   import os

   @pytest.fixture
   def mock_llm_config():
       """Mock LLM config for testing."""
       return OpenAILLMConfig(
           model_name="gpt-4",
           openai_api_key="test-key"
       )

   def test_create_chain_without_language_setting(mock_llm_config):
       """Test create_chain works without language setting (backward compatibility)."""
       component = BaseComponent(llm_config=mock_llm_config)
       system_template = "You are a helpful assistant."
       human_template = "Hello {name}."

       chain = component.create_chain(system_template, human_template)

       assert chain is not None
       assert component.prompt_template is not None

   def test_create_chain_with_language_setting(mock_llm_config):
       """Test create_chain injects language setting when provided."""
       component = BaseComponent(llm_config=mock_llm_config)
       system_template = "You are a helpful assistant."
       human_template = "Hello {name}."
       language_setting = "Русский официальный стиль"

       chain = component.create_chain(system_template, human_template, language_setting)

       assert chain is not None
       # Verify injection was prepended
       assert "**Language and Style Setting**:" in str(component.prompt_template.messages[0].content)
       assert language_setting in str(component.prompt_template.messages[0].content)

   def test_create_chain_empty_language_setting(mock_llm_config):
       """Test create_chain treats empty string as no language setting."""
       component = BaseComponent(llm_config=mock_llm_config)
       system_template = "You are a helpful assistant."
       human_template = "Hello {name}."

       chain = component.create_chain(system_template, human_template, "")

       # Empty string should not trigger injection
       assert "**Language and Style Setting**:" not in str(component.prompt_template.messages[0].content)

   def test_create_chain_none_language_setting(mock_llm_config):
       """Test create_chain treats None as no language setting."""
       component = BaseComponent(llm_config=mock_llm_config)
       system_template = "You are a helpful assistant."
       human_template = "Hello {name}."

       chain = component.create_chain(system_template, human_template, None)

       # None should not trigger injection
       assert "**Language and Style Setting**:" not in str(component.prompt_template.messages[0].content)
   ```

2. **Run tests**:
   ```bash
   pytest tests/nodes/test_base_component_language.py -v
   ```

**Validation**:
- [ ] All 4 tests pass
- [ ] Backward compatibility test (no language_setting) passes
- [ ] Injection test verifies language_setting in final prompt
- [ ] Empty and None cases handled correctly

**Notes**:
- Tests verify behavior without requiring actual LLM calls
- Use string representation of prompt for verification (simple approach)
- Tests can run without API keys (mock config)

---

## Test Strategy

**Test Files**:
- `tests/contract/test_debate_state.py` - Add contract test (T002)
- `tests/nodes/test_base_component_language.py` - Create new test file (T006)

**Running Tests**:
```bash
# Run contract test
pytest tests/contract/test_debate_state.py::test_language_setting_field -v

# Run BaseComponent language tests
pytest tests/nodes/test_base_component_language.py -v

# Run all related tests
pytest tests/contract/test_debate_state.py tests/nodes/test_base_component_language.py -v
```

**Test Coverage**:
- Contract test: Field definition and type safety
- Unit test: Language injection logic with multiple inputs
- Backward compatibility: Existing usage patterns still work

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Breaking existing `create_chain()` calls | High | Make `language_setting` parameter optional with default `None` |
| Injection at wrong position in prompt | Medium | Prepend to system_template (beginning) for maximum visibility |
| TypedDict incompatibility | Low | Use `NotRequired[Optional[str]]` double wrapper for max compatibility |
| Attribute not set in `__call__` | Low | Existing `setattr` loop handles this; verify with test |

---

## Review Guidance

**Key Acceptance Checkpoints**:
1. `DebateState.language_setting` field defined correctly
2. `BaseComponent.create_chain()` signature is backward compatible
3. Language injection format matches specification exactly
4. All tests pass, including backward compatibility cases
5. No breaking changes to existing code

**What to Review**:
- `debate_state.py`: Field definition and type annotations
- `nodes/base_component.py`: `create_chain()` modification and injection logic
- Test files: Coverage of edge cases (None, empty string, absent)

**Red Flags**:
- Required `language_setting` parameter (breaks existing code)
- Injection after system template instead of before
- Missing import for `Optional` or `NotRequired`

---

## Activity Log

> **CRITICAL**: Activity log entries MUST be in chronological order (oldest first, newest last).

- 2025-02-17T16:00:00Z – system – lane=planned – Prompt created.

---

### Updating Lane Status

To change a work package's lane, either:

1. **Edit directly**: Change the `lane:` field in frontmatter AND append activity log entry (at the end)
2. **Use CLI**: `spec-kitty agent tasks move-task WP01 --to <lane> --note "message"` (recommended)

The CLI command updates both frontmatter and activity log automatically.

**Valid lanes**: `planned`, `doing`, `for_review`, `done`
