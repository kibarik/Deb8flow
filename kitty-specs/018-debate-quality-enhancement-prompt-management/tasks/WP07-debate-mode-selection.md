---
work_package_id: WP07
title: Debate Mode Selection and Configuration
lane: "done"
dependencies: []
base_branch: main
base_commit: d0bdf3ec47acad8a667a822138ce94e46d630605
created_at: '2026-02-19T07:16:31.807818+00:00'
subtasks: [T037, T038, T039, T040, T041]
shell_pid: "8374"
agent: "claude"
reviewed_by: "ALeks ishmanov"
review_status: "approved"
history:
- timestamp: '2025-02-19T00:00:00Z'
  action: Created
  agent: spec-kitty
---

# WP07: Debate Mode Selection and Configuration

## Objective

Implement debate mode selection logic allowing users to choose between standard (multi-turn) and simple (single-call) modes via configuration.

## Context

We now have two orchestrators:
- `SimpleDebateOrchestrator` - Fast, single LLM call
- `StandardDebateOrchestrator` - Slower, 9 LLM calls, better quality

We need to:
1. Create a `DebateMode` enum
2. Create a factory for orchestrator instantiation
3. Update executor to use factory based on config
4. Add configuration validation
5. Test mode selection

## Implementation Guidance

### T037: Create DebateMode Enum

**Purpose:** Define the debate mode enumeration.

**Steps:**

1. Add to `src/shared/debate/domain/entities.py`:
   ```python
   """Debate domain entities."""

   from enum import Enum


   class DebateMode(str, Enum):
       """Debate execution mode."""

       STANDARD = "standard"  # Multi-turn, separate LLM calls per stage
       SIMPLE = "simple"      # Single LLM call for entire debate

       @classmethod
       def from_string(cls, value: str) -> "DebateMode":
           """Parse string to DebateMode, with validation."""
           try:
               return cls(value.lower())
           except ValueError:
               valid = [m.value for m in cls]
               raise ValueError(
                   f"Invalid debate mode: {value}. "
                   f"Must be one of: {valid}"
               )

       def is_standard(self) -> bool:
           """Check if this is standard mode."""
           return self == DebateMode.STANDARD

       def is_simple(self) -> bool:
           """Check if this is simple mode."""
           return self == DebateMode.SIMPLE
   ```

2. Export in `__init__.py`:
   ```python
   from .entities import DebateMode, DebateRoom, DebateMessage, Verdict

   __all__ = ["DebateMode", "DebateRoom", "DebateMessage", "Verdict"]
   ```

**Files:**
- `src/shared/debate/domain/entities.py` (modify, add ~25 lines)
- `src/shared/debate/domain/__init__.py` (modify, add ~5 lines)

**Validation:**
- [ ] Enum has STANDARD and SIMPLE values
- [ ] from_string() validates input
- [ ] Helper methods work correctly

---

### T038: Create DebateOrchestratorFactory

**Purpose:** Create factory for mode-based orchestrator instantiation.

**Steps:**

1. Create `src/shared/debate/infrastructure/llm/factory.py`:
   ```python
   """Factory for creating debate orchestrators."""

   import logging
   from typing import Optional

   from .debate_orchestrator import SimpleDebateOrchestrator
   from .standard_orchestrator import StandardDebateOrchestrator
   from ..application.prompt_loader import PromptLoader
   from ..domain.entities import DebateMode


   logger = logging.getLogger(__name__)


   class DebateOrchestratorFactory:
       """
       Factory for creating debate orchestrators based on mode.

       This factory centralizes orchestrator creation logic and ensures
       consistent initialization across the application.
       """

       @staticmethod
       def create(
           mode: DebateMode,
           prompt_loader: PromptLoader,
           model: Optional[str] = None,
           temperature: float = 0.7,
           api_key: Optional[str] = None,
           base_url: Optional[str] = None,
           language: str = "en"
       ):
           """
           Create a debate orchestrator based on the specified mode.

           Args:
               mode: Debate mode (standard or simple)
               prompt_loader: PromptLoader for loading prompts
               model: LLM model name
               temperature: Sampling temperature
               api_key: API key for LLM
               base_url: Base URL for LLM API
               language: Output language

           Returns:
               Configured orchestrator instance

           Raises:
               ValueError: If mode is invalid
           """
           logger.info(f"Creating {mode.value} debate orchestrator")

           if mode == DebateMode.STANDARD:
               return StandardDebateOrchestrator(
                   prompt_loader=prompt_loader,
                   model=model,
                   temperature=temperature,
                   api_key=api_key,
                   base_url=base_url,
                   language=language
               )
           elif mode == DebateMode.SIMPLE:
               return SimpleDebateOrchestrator(
                   prompt_loader=prompt_loader,
                   model=model,
                   temperature=temperature,
                   api_key=api_key,
                   base_url=base_url,
                   language=language
               )
           else:
               raise ValueError(f"Unsupported debate mode: {mode}")


   def create_orchestrator(
       mode: str | DebateMode,
       prompt_loader: PromptLoader,
       **kwargs
   ):
       """
       Convenience function for creating orchestrators.

       Args:
           mode: Debate mode as string or DebateMode enum
           prompt_loader: PromptLoader instance
           **kwargs: Additional arguments passed to orchestrator

       Returns:
           Configured orchestrator instance
       """
       # Convert string to enum if needed
       if isinstance(mode, str):
           mode = DebateMode.from_string(mode)

       return DebateOrchestratorFactory.create(mode, prompt_loader, **kwargs)
   ```

**Files:**
- `src/shared/debate/infrastructure/llm/factory.py` (new, ~80 lines)

**Validation:**
- [ ] Factory creates correct orchestrator type
- [ ] Both modes are supported
- [ ] Invalid mode raises error
- [ ] Convenience function works

---

### T039: Update CliDebateExecutor to Use Factory

**Purpose:** Modify executor to create orchestrators via factory.

**Steps:**

1. Update `scripts/document_debate_cli.py`:
   ```python
   from shared.debate.infrastructure.llm.factory import create_orchestrator
   from shared.debate.domain.entities import DebateMode

   async def main():
       # ... existing setup ...

       # Load debate mode from config
       mode = DebateMode.from_string(
           os.environ.get("DEBATE_MODE", config.debate.mode)
       )

       # Create orchestrator via factory
       orchestrator = create_orchestrator(
           mode=mode,
           prompt_loader=prompt_loader,
           model=args.model,
           language=args.language
       )

       # Execute debate (unchanged)
       dialogue, winner = await orchestrator.execute_debate(...)
   ```

**Files:**
- `scripts/document_debate_cli.py` (modify, ~20 lines)

**Validation:**
- [ ] Factory is used for orchestrator creation
- [ ] Mode is read from config
- [ ] Environment variable can override config
- [ ] Both modes work

---

### T040: Add Configuration Validation

**Purpose:** Validate debate mode in configuration.

**Note:** Already done in WP02 (T008-T009) with Pydantic validation.

**Validation:**
- [ ] `debate.mode` accepts "standard" or "simple"
- [ ] Invalid modes raise ValidationError
- [ ] Default is "standard"

---

### T041: Create Unit Tests for Factory

**Purpose:** Test factory and mode selection logic.

**Steps:**

1. Create `tests/shared/debate/infrastructure/llm/test_factory.py`:
   ```python
   """Tests for debate orchestrator factory."""

   import pytest

   from shared.debate.infrastructure.llm.factory import (
       DebateOrchestratorFactory,
       create_orchestrator
   )
   from shared.debate.domain.entities import DebateMode
   from shared.debate.infrastructure.llm.debate_orchestrator import SimpleDebateOrchestrator
   from shared.debate.infrastructure.llm.standard_orchestrator import StandardDebateOrchestrator


   @pytest.fixture
   def prompt_loader(tmp_path):
       """Create test PromptLoader."""
       # ... setup ...

   class TestDebateOrchestratorFactory:
       """Test factory methods."""

       def test_create_simple_orchestrator(self, prompt_loader):
           """Test creating simple mode orchestrator."""
           orchestrator = DebateOrchestratorFactory.create(
               DebateMode.SIMPLE,
               prompt_loader
           )
           assert isinstance(orchestrator, SimpleDebateOrchestrator)

       def test_create_standard_orchestrator(self, prompt_loader):
           """Test creating standard mode orchestrator."""
           orchestrator = DebateOrchestratorFactory.create(
               DebateMode.STANDARD,
               prompt_loader
           )
           assert isinstance(orchestrator, StandardDebateOrchestrator)

       def test_invalid_mode_raises_error(self, prompt_loader):
           """Test invalid mode raises ValueError."""
           with pytest.raises(ValueError):
               DebateOrchestratorFactory.create(
                   "invalid",
                   prompt_loader
               )

       def test_convenience_function_with_string(self, prompt_loader):
           """Test convenience function accepts string mode."""
           orchestrator = create_orchestrator(
               "simple",
               prompt_loader
           )
           assert isinstance(orchestrator, SimpleDebateOrchestrator)
   ```

**Files:**
- `tests/shared/debate/infrastructure/llm/test_factory.py` (new, ~60 lines)

**Validation:**
- [ ] Tests verify correct orchestrator type
- [ ] Tests cover both modes
- [ ] Tests verify error handling

---

## Definition of Done

- [ ] DebateMode enum exists
- [ ] Factory creates correct orchestrator type
- [ ] Executor uses factory
- [ ] Configuration validates mode
- [ ] Unit tests pass
- [ ] Both modes work

---

## Reviewer Guidance

**Check these specific items:**
1. Enum has correct values
2. Factory handles both modes
3. Invalid mode raises clear error
4. Configuration validation works
5. Executor integration is clean
6. Tests cover all cases

**Files to Review:**
- `src/shared/debate/domain/entities.py`
- `src/shared/debate/infrastructure/llm/factory.py`
- `scripts/document_debate_cli.py`
- `tests/shared/debate/infrastructure/llm/test_factory.py`

## Activity Log

- 2026-02-19T07:17:36Z – claude – shell_pid=79879 – lane=for_review – Moved to for_review
- 2026-02-19T11:25:07Z – claude – shell_pid=8374 – lane=doing – Started review via workflow command
- 2026-02-19T11:25:08Z – claude – shell_pid=8374 – lane=done – Review passed
