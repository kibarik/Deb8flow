---
work_package_id: WP02
title: Foundation - Analyzer Base & Pipeline Utilities
lane: "done"
dependencies: []
base_branch: main
base_commit: 9d5705de96b438c1c93f45e8d9bcaad029b92cfe
created_at: '2026-02-15T22:39:49.113155+00:00'
subtasks:
- T007
- T008
- T009
- T010
- T011
phase: Phase 1 - Foundation
assignee: ''
agent: "claude"
shell_pid: "84863"
review_status: "approved"
reviewed_by: "ALeks ishmanov"
history:
- timestamp: '2025-02-16T12:00:00Z'
  lane: planned
  agent: system
  shell_pid: ''
  action: Prompt generated via /spec-kitty.tasks
---

# Work Package Prompt: WP02 – Foundation - Analyzer Base & Pipeline Utilities

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
Wrap HTML/XML tags in backticks: `` `<div>` ``, `` `<script>` ``
Use language identifiers in code blocks: ````python`, ````bash`

---

## Objectives & Success Criteria

**Objectives**:
1. Create base analyzer class following existing BaseComponent pattern
2. Implement LLM chain creation methods for structured and unstructured output
3. Implement prompt loading utility for markdown prompts
4. Add retry logic with exponential backoff for reliability

**Success Criteria**:
- EnhancedAnalyzer base class extends BaseComponent correctly
- Structured chain supports Pydantic model output
- Text chain supports raw text output with JSON fallback
- Prompt loading works from src/prompts/enhanced_conclusion/
- Retry logic handles LLM failures gracefully
- Unit tests verify all functionality

---

## Context & Constraints

**Supporting Documents**:
- Spec: `kitty-specs/011-enhanced-committee-debate-conclusion/spec.md` (WF-002: extensible pipeline)
- Plan: `kitty-specs/011-enhanced-committee-debate-conclusion/plan.md` (architecture design)
- Quickstart: `kitty-specs/011-enhanced-committee-debate-conclusion/quickstart.md` (analyzer template)

**Existing Code**:
- BaseComponent in `src/nodes/base_component.py` (follow this pattern)
- Existing chain creation in ConclusionReportNode

**Constraints**:
- Must extend BaseComponent pattern for consistency
- Must support both OpenAI and Requesty (DeepSeek) LLMs
- Retry logic must not cause excessive delays
- Prompt directory must exist or be created

**Architectural Decisions**:
- Create new `src/analyzers/` directory for enhanced conclusion pipeline
- Use langchain for chain creation (consistent with existing code)
- Retry decorator with 3 attempts, exponential backoff (2^0, 2^1, 2^2 seconds)

---

## Subtasks & Detailed Guidance

### Subtask T007 – Create Analyzer Directory and Base Class
- **Purpose**: Foundational infrastructure for all enhanced conclusion analyzers
- **Steps**:
  1. Create `src/analyzers/` directory
  2. Create `src/analyzers/__init__.py` with:
     ```python
     from src.analyzers.base_analyzer import EnhancedAnalyzer

     __all__ = ["EnhancedAnalyzer"]
     ```
  3. Create `src/analyzers/base_analyzer.py` with EnhancedAnalyzer class:
     ```python
     from nodes.base_component import BaseComponent
     from typing import Dict, Any, Optional, TypeVar, Type
     from pathlib import Path
     import logging

     T = TypeVar('T', bound=object)

     class EnhancedAnalyzer(BaseComponent):
         """Base class for enhanced conclusion analyzers.

         Provides LLM chain creation, prompt loading, and retry logic
         for the two-stage enhanced conclusion pipeline.
         """

         def __init__(self, llm_config=None):
             super().__init__(llm_config)
             self.logger = logging.getLogger(self.__class__.__name__)
             self._prompts_dir = Path("src/prompts/enhanced_conclusion")

         def __call__(self, *args, **kwargs):
             raise NotImplementedError("Subclasses must implement __call__")
     ```

**Files**:
- `src/analyzers/__init__.py` (new file, ~5 lines)
- `src/analyzers/base_analyzer.py` (new file, ~80 lines)

**Parallel?**: No

**Notes**:
- Follow BaseComponent pattern exactly
- TypeVar T for generic return types in chain methods

---

### Subtask T008 – LLM Chain Creation Methods
- **Purpose**: Support both structured (Pydantic) and unstructured (text) output
- **Steps**:
  1. Add `_create_structured_chain()` method:
     ```python
     def _create_structured_chain(self, prompt_template: str, output_model: Type[T]):
         from langchain_core.prompts import ChatPromptTemplate
         from langchain.output_parsers import PydanticOutputParser
         from langchain_core.runnables import RunnablePassthrough

         # Check if LLM supports structured output
         if hasattr(self.llm, 'with_structured_output'):
             # OpenAI supports native structured output
             structured_llm = self.llm.with_structured_output(output_model)
             prompt = ChatPromptTemplate.from_messages([
                 ("system", "You are a debate analyst. Follow instructions precisely."),
                 ("human", "{input}")
             ])
             return prompt | structured_llm
         else:
             # Fallback: use PydanticOutputParser
             parser = PydanticOutputParser(pydantic_object=output_model)
             prompt = ChatPromptTemplate.from_messages([
                 ("system", "You are a debate analyst. Output ONLY valid JSON."),
                 ("human", "{format_instructions}\n\n{input}")
             ])
             return prompt | self.llm | parser
     ```
  2. Add `_create_text_chain()` method:
     ```python
     def _create_text_chain(self, system_message: str = None):
         from langchain_core.prompts import ChatPromptTemplate
         from langchain_core.output_parsers import StrOutputParser

         system_msg = system_message or "You are a debate analyst. Output ONLY valid JSON, no markdown."
         prompt = ChatPromptTemplate.from_messages([
             ("system", system_msg),
             ("human", "{input}")
         ])
         return prompt | self.llm | StrOutputParser()
     ```

**Files**:
- `src/analyzers/base_analyzer.py` (extend, ~60 lines)

**Parallel?**: No

**Notes**:
- Structured output requires OpenAI or compatible LLM
- Requesty/DeepSeek uses text chain with JSON fallback
- StrOutputParser ensures string return type

---

### Subtask T009 – Prompt Loading Utility
- **Purpose**: Load markdown prompts from standardized location
- **Steps**:
  1. Add `_load_prompt()` method:
     ```python
     def _load_prompt(self, prompt_name: str) -> str:
         """Load prompt template from markdown file.

         Args:
             prompt_name: Name of prompt file (e.g., 'verdict_extraction_prompt.md')

         Returns:
             Prompt template as string

         Raises:
             FileNotFoundError: If prompt file doesn't exist
         """
         prompt_path = self._prompts_dir / prompt_name

         if not prompt_path.exists():
             raise FileNotFoundError(f"Prompt file not found: {prompt_path}")

         # Read with UTF-8 encoding for Russian/English support
         return prompt_path.read_text(encoding='utf-8')
     ```
  2. Add `_format_prompt()` helper:
     ```python
     def _format_prompt(self, prompt_template: str, **kwargs) -> str:
         """Format prompt template with variables.

         Args:
             prompt_template: Prompt template string
             **kwargs: Variables to substitute

         Returns:
             Formatted prompt string
         """
         return prompt_template.format(**kwargs)
     ```

**Files**:
- `src/analyzers/base_analyzer.py` (extend, ~40 lines)

**Parallel?**: No

**Notes**:
- UTF-8 encoding is critical for Russian text
- Create prompts directory if it doesn't exist yet

---

### Subtask T010 – Retry Logic with Exponential Backoff
- **Purpose**: Handle transient LLM API failures gracefully
- **Steps**:
  1. Add retry decorator:
     ```python
     import time
     from functools import wraps

     def retry_with_backoff(max_retries=3, base_delay=1.0):
         def decorator(func):
             @wraps(func)
             def wrapper(*args, **kwargs):
                 last_exception = None
                 for attempt in range(max_retries):
                     try:
                         return func(*args, **kwargs)
                     except Exception as e:
                         last_exception = e
                         if attempt < max_retries - 1:
                             delay = base_delay * (2 ** attempt)
                             self.logger.warning(
                                 f"Attempt {attempt + 1} failed: {e}. "
                                 f"Retrying in {delay}s..."
                             )
                             time.sleep(delay)
                         else:
                             self.logger.error(
                                 f"All {max_retries} attempts failed: {e}"
                             )
                 raise last_exception
             return wrapper
         return decorator
     ```
  2. Add `_invoke_with_retry()` method:
     ```python
     def _invoke_with_retry(self, chain, input_data: Dict[str, Any]):
         return retry_with_backoff()(chain.invoke)(input_data)
     ```

**Files**:
- `src/analyzers/base_analyzer.py` (extend, ~50 lines)

**Parallel?**: No

**Notes**:
- Max 3 retries: 0s, 1s, 2s delays (total ~3s on failure)
- Log warnings for retries, errors for final failure
- Re-raise last exception after all retries exhausted

---

### Subtask T011 – Unit Tests for Base Analyzer
- **Purpose**: Verify base analyzer functionality
- **Steps**:
  1. Create `tests/test_enhanced_conclusion/test_base_analyzer.py`
  2. Test class instantiation:
     - Create EnhancedAnalyzer with mock LLM
     - Verify logger is created
  3. Test prompt loading:
     - Create test prompt file
     - Load prompt successfully
     - Test FileNotFoundError for missing file
  4. Test chain creation:
     - Create structured chain with mock Pydantic model
     - Create text chain
     - Verify chain types are correct
  5. Test retry logic:
     - Mock function that fails twice then succeeds
     - Verify retry attempts and timing
     - Verify final exception after all retries

**Files**:
- `tests/test_enhanced_conclusion/test_base_analyzer.py` (new file, ~150 lines)

**Parallel?**: Yes

**Notes**:
- Use unittest.mock for LLM mocking
- Use time.sleep to verify retry delays (with appropriate tolerances)

---

## Test Strategy

**Test Location**: `tests/test_enhanced_conclusion/test_base_analyzer.py`

**Test Commands**:
```bash
# Run all base analyzer tests
pytest tests/test_enhanced_conclusion/test_base_analyzer.py -v

# Run specific test
pytest tests/test_enhanced_conclusion/test_base_analyzer.py::test_prompt_loading -v

# Run with coverage
pytest tests/test_enhanced_conclusion/test_base_analyzer.py --cov=src/analyzers/base_analyzer
```

**Fixtures Needed**:
- Mock LLM instance
- Test prompt file in src/prompts/enhanced_conclusion/test_prompt.md
- Mock Pydantic model for structured output tests

**Coverage Target**: > 90%

---

## Risks & Mitigations

**Risk 1**: BaseComponent pattern changed since feature 009
- **Mitigation**: Check current BaseComponent implementation before extending

**Risk 2**: LLM structured output not supported by Requesty/DeepSeek
- **Mitigation**: Fallback to PydanticOutputParser implemented in T008

**Risk 3**: Retry logic causes excessive delays
- **Mitigation**: Exponential backoff limits total retry time to ~3 seconds

**Risk 4**: Prompts directory doesn't exist
- **Mitigation**: Create directory in WP03 when creating first prompt file

---

## Review Guidance

**Key Acceptance Checkpoints**:
1. EnhancedAnalyzer extends BaseComponent correctly
2. Structured chain supports Pydantic models
3. Text chain supports raw text output
4. Prompt loading works with UTF-8 encoding
5. Retry logic handles failures gracefully
6. Unit tests pass with > 90% coverage

**Review Before Approval**:
- Verify BaseComponent inheritance is correct
- Check structured chain fallback logic for non-OpenAI LLMs
- Verify retry delays are appropriate (not too long)
- Check prompt loading handles missing files gracefully

---

## Activity Log

> **CRITICAL**: Activity log entries MUST be in chronological order (oldest first, newest last).

### How to Add Activity Log Entries

**When adding an entry**:
1. Scroll to the bottom of this file (Activity Log section below "Valid lanes")
2. **APPEND the new entry at the END** (do NOT prepend or insert in middle)
3. Use exact format: `- YYYY-MM-DDTHH:MM:SSZ – agent_id – lane=<lane> – <action>`
4. Timestamp MUST be current time in UTC (check with `date -u "+%Y-%m-%dT%H:%M:%SZ"`)
5. Lane MUST match the frontmatter `lane:` field exactly
6. Agent ID should identify who made the change (claude-sonnet-4-5, codex, etc.)

**Format**:
```
- YYYY-MM-DDTHH:MM:SSZ – <agent_id> – lane=<lane> – <brief action description>
```

**Example (correct chronological order)**:
```
- 2026-01-12T10:00:00Z – system – lane=planned – Prompt created
- 2026-01-12T10:30:00Z – claude – lane=doing – Started implementation
- 2026-01-12T11:00:00Z – codex – lane=for_review – Implementation complete, ready for review
- 2026-01-12T11:30:00Z – claude – lane=done – Review passed, all tests passing  ← LATEST (at bottom)
```

**Common mistakes (DO NOT DO THIS)**:
- ❌ Adding new entry at the top (breaks chronological order)
- ❌ Using future timestamps (causes acceptance validation to fail)
- ❌ Lane mismatch: frontmatter says `lane: "done"` but log entry says `lane=doing`
- ❌ Inserting in middle instead of appending to end

**Why this matters**: The acceptance system reads the LAST activity log entry as the current state. If entries are out of order, acceptance will fail even when the work is complete.

**Initial entry**:
- 2025-02-16T12:00:00Z – system – lane=planned – Prompt created.

---

### Updating Lane Status

To change a work package's lane, either:

1. **Edit directly**: Change the `lane:` field in frontmatter AND append activity log entry (at the end)
2. **Use CLI**: `spec-kitty agent tasks move-task <WPID> --to <lane> --note "message"` (recommended)

The CLI command updates both frontmatter and activity log automatically.

**Valid lanes**: `planned`, `doing`, `for_review`, `done`

### Optional Phase Subdirectories

For large features, organize prompts under `tasks/` to keep bundles grouped while maintaining lexical ordering.
- 2026-02-15T22:39:49Z – claude-sonnet-4-5 – shell_pid=73799 – lane=doing – Assigned agent via workflow command
- 2026-02-15T22:43:34Z – claude-sonnet-4-5 – shell_pid=73799 – lane=for_review – Ready for review: Implemented EnhancedAnalyzer base class extending BaseComponent. Structured chain creation with native support or PydanticOutputParser fallback. Text chain creation with JSON output. Prompt loading with UTF-8 encoding. Retry logic with exponential backoff (0s, 1s, 2s). 24 unit tests passing.
- 2026-02-15T23:40:11Z – claude – shell_pid=84863 – lane=doing – Started review via workflow command
- 2026-02-15T23:40:33Z – claude – shell_pid=84863 – lane=done – Review passed: 24/24 tests passing. EnhancedAnalyzer base class with LLM chain utilities, prompt loading, exponential backoff retry logic.
