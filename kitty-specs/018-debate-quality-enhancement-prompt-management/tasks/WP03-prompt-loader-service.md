---
work_package_id: WP03
title: PromptLoader Service
lane: "for_review"
dependencies: []
base_branch: main
base_commit: a28b939c400a6ec521988da83e38d70d86d105e3
created_at: '2026-02-19T07:05:26.652570+00:00'
subtasks: [T011, T012, T013, T014, T015, T016, T017]
shell_pid: "75767"
agent: "claude-code"
history:
- timestamp: '2025-02-19T00:00:00Z'
  action: Created
  agent: spec-kitty
---

# WP03: PromptLoader Service

## Objective

Implement the core PromptLoader service that loads, caches, validates, and renders prompt templates with variable substitution. This is the heart of the prompt management system.

## Context

Now that we have:
- Prompt files created (WP01)
- Configuration schema defined (WP02)

We need the service that:
- Loads prompts from files
- Caches them in memory for performance
- Validates template variables
- Renders templates with variable substitution
- Provides clear error handling

The PromptLoader will be used by:
- `LLMDebateOrchestrator` (WP04)
- `SimpleDebateOrchestrator` (WP04)
- `TakeawayAnalyzer` (WP05)

## Implementation Guidance

### T011: Create PromptLoader Class Structure

**Purpose:** Create the core PromptLoader class with all required methods.

**Steps:**
1. Create `src/shared/debate/application/prompt_loader.py`:
   ```python
   """PromptLoader service for loading and rendering prompt templates."""

   import logging
   import re
   from pathlib import Path
   from typing import Dict, Optional, Any, List
   from dataclasses import dataclass, field
   from threading import Lock

   from shared.config.models import PromptsConfig


   logger = logging.getLogger(__name__)


   @dataclass
   class PromptContext:
       """Context variables for prompt template rendering."""

       question: str
       topic: str = ""
       prd_content: str = ""
       language: str = "en"
       recent_context: str = ""
       pro_prompt: str = ""
       con_prompt: str = ""
       dialogue_summary: str = ""
       verdict_explanation: str = ""
       winner: str = ""
       min_takeaways: int = 3
       max_takeaways: int = 10

       def to_dict(self) -> Dict[str, Any]:
           """Convert to dictionary for template rendering."""
           return {
               "question": self.question,
               "topic": self.topic,
               "prd_content": self.prd_content,
               "language": self.language,
               "recent_context": self.recent_context,
               "pro_prompt": self.pro_prompt,
               "con_prompt": self.con_prompt,
               "dialogue_summary": self.dialogue_summary,
               "verdict_explanation": self.verdict_explanation,
               "winner": self.winner,
               "min_takeaways": self.min_takeaways,
               "max_takeaways": self.max_takeaways,
           }


   @dataclass
   class ValidationResult:
       """Result of prompt validation."""

       is_valid: bool
       prompt_id: str
       missing_variables: List[str] = field(default_factory=list)
       errors: List[str] = field(default_factory=list)


   class PromptLoader:
       """
       Service for loading, caching, and rendering prompt templates.

       Features:
       - Loads prompts from files
       - Caches templates in memory
       - Validates template variables
       - Renders templates with context substitution
       - Thread-safe operations
       """

       # Required template variables by prompt type
       REQUIRED_VARS = {
           "debate.stages.opening_pro": ["question", "topic"],
           "debate.stages.opening_con": ["question", "topic"],
           "debate.stages.rebuttal_pro": ["question", "recent_context"],
           "debate.stages.rebuttal_con": ["question", "recent_context"],
           "debate.stages.counter_pro": ["question", "recent_context"],
           "debate.stages.counter_con": ["question", "recent_context"],
           "debate.stages.final_pro": ["question", "recent_context"],
           "debate.stages.final_con": ["question", "recent_context"],
           "debate.judge": ["question", "recent_context"],
           "debate.context": ["question", "topic", "prd_content", "language"],
           "analysis.takeaway": ["question", "dialogue_summary", "min_takeaways", "max_takeaways"],
       }

       def __init__(self, config: PromptsConfig, base_path: Path = None):
           """
           Initialize the PromptLoader.

           Args:
               config: Prompt configuration with file paths
               base_path: Base path for resolving relative file paths (default: current working directory)
           """
           self.config = config
           self.base_path = base_path or Path.cwd()
           self._cache: Dict[str, str] = {}
           self._lock = Lock()

           # Preload all prompts on initialization
           self._load_all_prompts()

       def _load_all_prompts(self) -> None:
           """Load all prompts into cache."""
           logger.info("Loading prompts into cache...")

           # Load stage prompts
           for stage_name, path in self.config.stages.items():
               prompt_id = f"debate.stages.{stage_name}"
               self._load_file(prompt_id, path)

           # Load judge prompt
           self._load_file("debate.judge", self.config.judge)
           self._load_file("debate.context", self.config.context)

           # Load analysis prompts
           for analysis_type, path in self.config.analysis.items():
               prompt_id = f"analysis.{analysis_type}"
               self._load_file(prompt_id, path)

           # Load role prompts if configured
           if self.config.roles:
               for role_name, path in self.config.roles.items():
                   prompt_id = f"roles.{role_name}"
                   self._load_file(prompt_id, path)

           logger.info(f"Loaded {len(self._cache)} prompts into cache")

       def _load_file(self, prompt_id: str, file_path: str) -> None:
           """
           Load a single prompt file into cache.

           Args:
               prompt_id: Unique identifier for the prompt
               file_path: Path to the prompt file

           Raises:
               FileNotFoundError: If the file doesn't exist
               ValueError: If the file is empty
           """
           path = self._resolve_path(file_path)

           if not path.exists():
               # Try fallback to old location
                   old_path = self._resolve_path(file_path.replace("src/prompts", "config/prompts"))
                   if old_path.exists():
                       logger.warning(f"Using deprecated path for {prompt_id}: {old_path}")
                       path = old_path
                   else:
                       raise FileNotFoundError(f"Prompt file not found: {path}")

           content = path.read_text(encoding='utf-8').strip()

           if not content:
               raise ValueError(f"Prompt file is empty: {path}")

           with self._lock:
               self._cache[prompt_id] = content

           logger.debug(f"Loaded prompt: {prompt_id} from {path}")

       def _resolve_path(self, file_path: str) -> Path:
           """Resolve a file path relative to base path."""
           path = Path(file_path)
           if not path.is_absolute():
               path = self.base_path / path
           return path

       def load(self, prompt_id: str) -> str:
           """
           Load a prompt template from cache.

           Args:
               prompt_id: Unique identifier for the prompt (e.g., "debate.context")

           Returns:
               The prompt template string

           Raises:
               KeyError: If the prompt_id is not found
           """
           if prompt_id not in self._cache:
               available = list(self._cache.keys())
               raise KeyError(
                   f"Prompt not found: {prompt_id}. "
                   f"Available prompts: {available}"
               )

           return self._cache[prompt_id]

       def load_with_context(self, prompt_id: str, context: PromptContext) -> str:
           """
           Load and render a prompt template with context variables.

           Args:
               prompt_id: Unique identifier for the prompt
               context: Context variables for template rendering

           Returns:
               The rendered prompt with variables substituted

           Raises:
               KeyError: If the prompt_id is not found
               ValueError: If required variables are missing from context
           """
           template = self.load(prompt_id)
           return self._render_template(template, context.to_dict())

       def _render_template(self, template: str, context: Dict[str, Any]) -> str:
           """
           Render a template with variable substitution.

           Uses Python's str.format() for simple variable substitution.
           Variables are specified as {variable_name} in templates.

           Args:
               template: The template string with {variable} placeholders
               context: Dictionary of variable names to values

           Returns:
               The rendered template with variables substituted

           Raises:
               ValueError: If a required variable is missing from context
           """
           try:
               return template.format(**context)
           except KeyError as e:
               missing_var = str(e).strip("'")
               raise ValueError(
                   f"Missing required variable '{missing_var}' in context. "
                   f"Template requires: {self._extract_variables(template)}"
               )

       def _extract_variables(self, template: str) -> List[str]:
           """Extract all variable names from a template."""
           return re.findall(r'\{([^}]+)\}', template)

       def validate(self, prompt_id: str) -> ValidationResult:
           """
           Validate a prompt template.

           Checks that:
           - Prompt exists in cache
           - Template is well-formed
           - Required variables are present (if configured)

           Args:
               prompt_id: Unique identifier for the prompt

           Returns:
               ValidationResult with validation status and any errors
           """
           errors = []
           missing_vars = []

           try:
               template = self.load(prompt_id)
               variables = set(self._extract_variables(template))

               # Check required variables if configured
               if prompt_id in self.REQUIRED_VARS:
                   required = set(self.REQUIRED_VARS[prompt_id])
                   missing = required - variables
                   if missing:
                       missing_vars = list(missing)
                       errors.append(f"Missing required variables: {missing}")

           except KeyError as e:
               errors.append(str(e))
           except Exception as e:
               errors.append(f"Validation error: {e}")

           return ValidationResult(
               is_valid=len(errors) == 0,
               prompt_id=prompt_id,
               missing_variables=missing_vars,
               errors=errors
           )

       def reload(self) -> None:
           """
           Reload all prompts from disk.

           Clears the cache and reloads all prompts.
           Useful for development when prompts are being edited.
           """
           logger.info("Reloading prompts...")
           with self._lock:
               self._cache.clear()
           self._load_all_prompts()
           logger.info("Prompts reloaded")

       def get_cached_prompt_ids(self) -> List[str]:
           """Get list of all cached prompt IDs."""
           return list(self._cache.keys())


   def create_prompt_loader(config: PromptsConfig, base_path: Path = None) -> PromptLoader:
       """
       Factory function to create a PromptLoader instance.

       Args:
           config: Prompt configuration
           base_path: Base path for resolving relative file paths

       Returns:
           Configured PromptLoader instance
       """
       return PromptLoader(config, base_path)
   ```

2. Update `src/shared/debate/application/__init__.py` to export the new classes:
   ```python
   from .prompt_loader import (
       PromptLoader,
       PromptContext,
       ValidationResult,
       create_prompt_loader
   )

   __all__ = [
       "PromptLoader",
       "PromptContext",
       "ValidationResult",
       "create_prompt_loader"
   ]
   ```

**Files:**
- `src/shared/debate/application/prompt_loader.py` (new, ~250 lines)
- `src/shared/debate/application/__init__.py` (modify, add ~10 lines)

**Validation:**
- [ ] PromptLoader class compiles without errors
- [ ] All methods are implemented
- [ ] Thread-safe operations use Lock correctly
- [ ] PromptContext dataclass has all required fields
- [ ] Classes are exported in __init__.py

---

### T012: Implement In-Memory Caching

**Purpose:** Add thread-safe caching for loaded prompts.

**Note:** This is already implemented in T011 as part of the PromptLoader class.

**Validation:**
- [ ] `_cache` dictionary stores loaded prompts
- [ ] `_lock` ensures thread-safe access
- [ ] Cache is populated on initialization
- [ ] Multiple calls to `load()` return cached content

---

### T013: Add Template Variable Validation

**Purpose:** Validate that templates contain required variables.

**Note:** This is already implemented in T011 as part of the `validate()` method.

**Validation:**
- [ ] `REQUIRED_VARS` dict specifies required variables per prompt type
- [ ] `validate()` checks for missing variables
- [ ] `ValidationResult` includes missing variables list
- [ ] Regex extraction finds all `{variable}` patterns

---

### T014: Implement String-Based Template Rendering

**Purpose:** Implement template variable substitution using Python's str.format().

**Note:** This is already implemented in T011 as part of the `_render_template()` method.

**Validation:**
- [ ] `str.format(**context)` substitutes variables
- [ ] Missing variables raise clear error messages
- [ ] Template can contain any variables from PromptContext
- [ ] Rendering is idempotent (can render multiple times)

---

### T015: Add Comprehensive Error Handling

**Purpose:** Add clear error handling for all failure scenarios.

**Scenarios to Handle:**
1. **File not found**: Clear message with file path
2. **Empty file**: ValueError indicating empty file
3. **Missing variable**: ValueError listing missing and required variables
4. **Invalid prompt_id**: KeyError listing available prompts
5. **Fallback to old location**: Warning when using deprecated path

**Note:** These are already implemented in T011. Verify they work correctly.

**Validation:**
- [ ] FileNotFoundError has clear message
- [ ] Empty file raises ValueError
- [ ] Missing variable raises ValueError with helpful message
- [ ] Invalid prompt_id lists available prompts
- [ ] Fallback to old location logs warning

---

### T016: Create PromptLoader Unit Tests

**Purpose:** Create comprehensive tests for PromptLoader functionality.

**Steps:**
1. Create `tests/shared/debate/application/test_prompt_loader.py`:
   ```python
   """Tests for PromptLoader service."""

   import pytest
   from pathlib import Path
   from unittest.mock import Mock, patch

   from shared.debate.application.prompt_loader import (
       PromptLoader,
       PromptContext,
       ValidationResult,
       create_prompt_loader
   )
   from shared.config.models import PromptsConfig
   from pydantic import ValidationError


   @pytest.fixture
   def temp_prompt_dir(tmp_path):
       """Create temporary prompt directory structure."""
       # Create directories
       (tmp_path / "prompts" / "debate" / "stages").mkdir(parents=True)
       (tmp_path / "prompts" / "debate" / "judge").mkdir(parents=True)
       (tmp_path / "prompts" / "debate" / "context").mkdir(parents=True)
       (tmp_path / "prompts" / "analysis").mkdir(parents=True)

       # Create test prompt files
       (tmp_path / "prompts" / "debate" / "stages" / "opening_pro.md").write_text(
           "Question: {question}\n\nTopic: {topic}"
       )
       (tmp_path / "prompts" / "debate" / "judge" / "verdict.md").write_text(
           "Question: {question}\n\nContext: {recent_context}"
       )
       (tmp_path / "prompts" / "debate" / "context" / "debate_context.md").write_text(
           "Q: {question}\nTopic: {topic}\nPRD: {prd_content}"
       )
       (tmp_path / "prompts" / "analysis" / "takeaway_analysis.md").write_text(
           "Q: {question}\nDialogue: {dialogue_summary}"
       )

       return tmp_path


   @pytest.fixture
   def prompt_config(temp_prompt_dir):
       """Create test prompt configuration."""
       base = str(temp_prompt_dir / "prompts")

       return PromptsConfig(
           stages={
               "opening_pro": f"{base}/debate/stages/opening_pro.md",
               "opening_con": f"{base}/debate/stages/opening_con.md",
               "rebuttal_pro": f"{base}/debate/stages/rebuttal_pro.md",
               "rebuttal_con": f"{base}/debate/stages/rebuttal_con.md",
               "counter_pro": f"{base}/debate/stages/counter_pro.md",
               "counter_con": f"{base}/debate/stages/counter_con.md",
               "final_pro": f"{base}/debate/stages/final_pro.md",
               "final_con": f"{base}/debate/stages/final_con.md",
           },
           judge=f"{base}/debate/judge/verdict.md",
           context=f"{base}/debate/context/debate_context.md",
           analysis={
               "system": f"{base}/analysis/system_prompt.md",
               "takeaway": f"{base}/analysis/takeaway_analysis.md"
           }
       )


   @pytest.fixture
   def prompt_loader(prompt_config, temp_prompt_dir):
       """Create PromptLoader instance for testing."""
       return PromptLoader(prompt_config, base_path=temp_prompt_dir)


   class TestPromptLoaderInitialization:
       """Test PromptLoader initialization and loading."""

       def test_loads_prompts_on_init(self, prompt_loader):
           """Test that prompts are loaded into cache on initialization."""
           assert len(prompt_loader.get_cached_prompt_ids()) > 0
           assert "debate.stages.opening_pro" in prompt_loader._cache
           assert "debate.judge" in prompt_loader._cache

       def test_missing_file_raises_error(self, temp_prompt_dir):
           """Test that missing prompt files raise FileNotFoundError."""
           config = PromptsConfig(
               stages={},
               judge="nonexistent.md",
               context="context.md",
               analysis={}
           )
           with pytest.raises(FileNotFoundError):
               PromptLoader(config, base_path=temp_prompt_dir)

       def test_empty_file_raises_error(self, temp_prompt_dir):
           """Test that empty prompt files raise ValueError."""
           empty_file = temp_prompt_dir / "prompts" / "empty.md"
           empty_file.write_text("")

           config = PromptsConfig(
               stages={},
               judge=str(empty_file),
               context="context.md",
               analysis={}
           )
           with pytest.raises(ValueError, match="empty"):
               PromptLoader(config, base_path=temp_prompt_dir)


   class TestPromptLoading:
       """Test prompt loading methods."""

       def test_load_cached_prompt(self, prompt_loader):
           """Test loading a prompt from cache."""
           prompt = prompt_loader.load("debate.judge")
           assert "Question:" in prompt
           assert "{question}" in prompt

       def test_load_nonexistent_prompt_raises_error(self, prompt_loader):
           """Test loading nonexistent prompt raises KeyError."""
           with pytest.raises(KeyError, match="not found"):
               prompt_loader.load("nonexistent.prompt")

       def test_load_with_context(self, prompt_loader):
           """Test loading prompt with context substitution."""
           context = PromptContext(
               question="Should we build this?",
               topic="A new feature",
               recent_context="Previous arguments..."
           )
           rendered = prompt_loader.load_with_context("debate.judge", context)

           assert "Should we build this?" in rendered
           assert "Previous arguments..." in rendered
           assert "{question}" not in rendered  # Variables substituted

       def test_load_with_context_missing_variable_raises_error(self, prompt_loader):
           """Test missing context variable raises ValueError."""
           context = PromptContext(question="Test")
           # Missing 'recent_context'

           with pytest.raises(ValueError, match="Missing required variable"):
               prompt_loader.load_with_context("debate.judge", context)


   class TestTemplateRendering:
       """Test template variable rendering."""

       def test_simple_variable_substitution(self, prompt_loader):
           """Test basic variable substitution."""
           context = PromptContext(
               question="Test Question",
               topic="Test Topic",
               prd_content="Test PRD"
           )
           rendered = prompt_loader.load_with_context("debate.context", context)

           assert "Test Question" in rendered
           assert "Test Topic" in rendered
           assert "Test PRD" in rendered

       def test_all_context_variables(self, prompt_loader):
           """Test all PromptContext fields can be used."""
           context = PromptContext(
               question="Q",
               topic="T",
               prd_content="P",
               language="ru",
               recent_context="R",
               pro_prompt="PRO",
               con_prompt="CON",
               dialogue_summary="D",
               verdict_explanation="V",
               winner="PRO",
               min_takeaways=3,
               max_takeaways=10
           )
           # Should not raise any errors
           prompt_loader.load_with_context("debate.context", context)


   class TestValidation:
       """Test prompt validation."""

       def test_validate_valid_prompt(self, prompt_loader):
           """Test validating a valid prompt."""
           result = prompt_loader.validate("debate.judge")
           assert result.is_valid
           assert result.prompt_id == "debate.judge"
           assert len(result.errors) == 0

       def test_validate_missing_required_vars(self, temp_prompt_dir):
           """Test validation detects missing required variables."""
           # Create prompt without required variables
           (temp_prompt_dir / "prompts" / "debate" / "stages" / "test.md").write_text(
               "Just some text without variables"
           )

           config = PromptsConfig(
               stages={
                   "opening_pro": f"{temp_prompt_dir}/prompts/debate/stages/test.md",
                   # ... (other stages required for validation)
               },
               judge=f"{temp_prompt_dir}/prompts/debate/judge/verdict.md",
               context=f"{temp_prompt_dir}/prompts/debate/context/debate_context.md",
               analysis={}
           )

           loader = PromptLoader(config, base_path=temp_prompt_dir)
           result = loader.validate("debate.stages.opening_pro")

           assert not result.is_valid
           assert len(result.missing_variables) > 0


   class TestCaching:
       """Test prompt caching behavior."""

       def test_reload_clears_cache(self, prompt_loader, temp_prompt_dir):
           """Test that reload clears and repopulates cache."""
           original_cache_size = len(prompt_loader.get_cached_prompt_ids())

           # Modify a file
           judge_file = temp_prompt_dir / "prompts" / "debate" / "judge" / "verdict.md"
           original_content = judge_file.read_text()
           judge_file.write_text("Modified content")

           prompt_loader.reload()

           assert "Modified content" in prompt_loader.load("debate.judge")

           # Restore original
           judge_file.write_text(original_content)


   class TestPromptContext:
       """Test PromptContext dataclass."""

       def test_to_dict_includes_all_fields(self):
           """Test that to_dict includes all context fields."""
           context = PromptContext(
               question="Q",
               topic="T",
               prd_content="P"
           )
           context_dict = context.to_dict()

           assert "question" in context_dict
           assert "topic" in context_dict
           assert "prd_content" in context_dict
           assert context_dict["question"] == "Q"


   class TestFactoryFunction:
       """Test the factory function."""

       def test_create_prompt_loader(self, prompt_config, temp_prompt_dir):
           """Test factory function creates PromptLoader."""
           loader = create_prompt_loader(prompt_config, temp_prompt_dir)
           assert isinstance(loader, PromptLoader)
           assert len(loader.get_cached_prompt_ids()) > 0
   ```

**Files:**
- `tests/shared/debate/application/test_prompt_loader.py` (new, ~200 lines)

**Validation:**
- [ ] All tests pass
- [ ] Tests cover loading, rendering, validation, caching
- [ ] Tests cover error cases
- [ ] Tests use fixtures for setup

**Run Tests:**
```bash
pytest tests/shared/debate/application/test_prompt_loader.py -v
```

---

### T017: Add Logging for Prompt Operations

**Purpose:** Add logging for debugging and monitoring prompt operations.

**Note:** Logging is already included in T011 implementation. Verify it's working correctly.

**Validation:**
- [ ] Prompts are logged when loaded
- [ ] Errors are logged with context
- [ ] Reload operations are logged
- [ ] Cache size is logged

---

## Test Strategy

**Unit tests cover:**
- Initialization and loading
- Prompt retrieval from cache
- Template rendering with variables
- Error handling (missing files, empty files, missing variables)
- Validation of prompts
- Cache reload
- PromptContext conversion

**No integration tests** - those will come in WP04 when orchestrators use PromptLoader.

---

## Definition of Done

- [ ] PromptLoader class exists with all methods
- [ ] Thread-safe caching is implemented
- [ ] Template rendering uses str.format()
- [ ] Variable validation works correctly
- [ ] Error handling covers all scenarios
- [ ] Unit tests exist and pass
- [ ] Logging is added for key operations
- [ ] Classes are exported in __init__.py
- [ ] Factory function exists
- [ ] PromptContext has all required fields

---

## Risks

1. **Template Injection**: Mitigated by using str.format() (not eval) and validating variable names
2. **Thread Safety**: Mitigated by using Lock for cache operations
3. **Memory Leaks**: Mitigated by fixed cache size (all prompts loaded once)
4. **File I/O Errors**: Mitigated by error handling in _load_file()

---

## Reviewer Guidance

**Check these specific items:**
1. Thread safety is properly implemented with Lock
2. Template rendering uses safe methods (str.format, not eval)
3. Error messages are clear and actionable
4. All required methods are implemented
5. Unit tests cover success and failure paths
6. Logging is present but not excessive
7. PromptContext includes all necessary fields
8. REQUIRED_VARS covers all prompt types

**Files to Review:**
- `src/shared/debate/application/prompt_loader.py`
- `src/shared/debate/application/__init__.py`
- `tests/shared/debate/application/test_prompt_loader.py`

**Common Issues to Look For:**
- Missing thread safety on cache access
- Unsafe template rendering (eval, exec)
- Unclear error messages
- Missing error scenarios
- Incomplete PromptContext fields
- Weak validation logic

## Activity Log

- 2026-02-19T07:05:26Z – claude-code – shell_pid=75767 – lane=doing – Assigned agent via workflow command
- 2026-02-19T07:06:48Z – claude-code – shell_pid=75767 – lane=for_review – Ready for review: PromptLoader service implemented with caching, validation, and template rendering
