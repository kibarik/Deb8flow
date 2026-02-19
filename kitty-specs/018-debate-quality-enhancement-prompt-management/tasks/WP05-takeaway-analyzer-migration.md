---
work_package_id: WP05
title: Takeaway Analyzer Prompt Migration
lane: "for_review"
dependencies: []
base_branch: main
base_commit: 342427918887f75b81161a15dc1cadb8bf66438e
created_at: '2026-02-19T07:14:06.333037+00:00'
subtasks: [T026, T027, T028, T029, T030]
shell_pid: "78974"
agent: "claude"
history:
- timestamp: '2025-02-19T00:00:00Z'
  action: Created
  agent: spec-kitty
---

# WP05: Takeaway Analyzer Prompt Migration

## Objective

Refactor `TakeawayAnalyzer` to use PromptLoader for system and analysis prompts instead of hardcoded strings.

## Context

Now that PromptLoader exists (WP03), we need to:
1. Inject PromptLoader into TakeawayAnalyzer
2. Replace hardcoded system prompts with loaded templates
3. Replace hardcoded analysis prompts with loaded templates
4. Remove old hardcoded prompt strings
5. Test that takeaway generation still works correctly

**Files to modify:**
- `src/shared/debate/application/analyzers.py`
- `src/shared/debate/infrastructure/executors/cli_executor.py`

## Implementation Guidance

### T026: Inject PromptLoader into TakeawayAnalyzer

**Purpose:** Modify TakeawayAnalyzer to accept PromptLoader.

**Steps:**

1. Modify `TakeawayAnalyzer.__init__()`:
   ```python
   # In analyzers.py

   from .prompt_loader import PromptLoader, PromptContext

   class TakeawayAnalyzer:
       def __init__(
           self,
           config: Optional[TakeawayConfig] = None,
           prompt_loader: Optional[PromptLoader] = None  # NEW parameter
       ):
           """
           Initialize the takeaway analyzer.

           Args:
               config: Configuration for takeaway generation
               prompt_loader: PromptLoader for loading analysis prompts
           """
           self.config = config or TakeawayConfig()
           self.prompt_loader = prompt_loader  # Store it

           # Initialize LLM (unchanged)
           # ...
   ```

2. Also update the convenience function signature:
   ```python
   async def generate_takeaways_from_dialogue_json(
       dialogue_json: Dict[str, Any],
       config: Optional[TakeawayConfig] = None,
       prompt_loader: Optional[PromptLoader] = None  # NEW
   ) -> List[str]:
       """..."""
       analyzer = TakeawayAnalyzer(config, prompt_loader)
       # ...
   ```

**Files:**
- `src/shared/debate/application/analyzers.py` (modify, ~15 lines)

**Validation:**
- [ ] Constructor accepts `prompt_loader` parameter
- [ ] PromptLoader is stored as instance variable
- [ ] Parameter is optional for backward compatibility

---

### T027: Replace _get_system_prompt() with Loaded Templates

**Purpose:** Replace language-based hardcoded system prompts.

**Steps:**

1. Replace `_get_system_prompt()` method:
   ```python
   def _get_system_prompt(self, language: str) -> str:
       """
       Get the system prompt for the analyst LLM.

       Now loads from template instead of hardcoded strings.
       """
       # Load appropriate prompt based on language
       if self.prompt_loader:
           try:
               # Try language-specific prompt first
               prompt_id = f"analysis.system_{language}"
               return self.prompt_loader.load(prompt_id)
           except KeyError:
               # Fall back to English
               return self.prompt_loader.load("analysis.system")
       else:
           # Fallback to hardcoded if no PromptLoader (backward compat)
           return self._get_fallback_system_prompt(language)

   def _get_fallback_system_prompt(self, language: str) -> str:
       """Fallback hardcoded system prompt (for backward compatibility)."""
       if language == "ru":
           return """Вы аналитик продукта комитета..."""
       else:
           return """You are a product committee analyst..."""
   ```

**Note:** This requires creating language-specific analysis prompts:
- `src/prompts/analysis/system_prompt_ru.md` (Russian)
- `src/prompts/analysis/system_prompt_en.md` (English - rename existing)

**Files:**
- `src/shared/debate/application/analyzers.py` (modify, ~40 lines)
- `src/prompts/analysis/system_prompt_en.md` (create/rename, ~30 lines)
- `src/prompts/analysis/system_prompt_ru.md` (create, ~30 lines)

**Validation:**
- [ ] System prompt uses loaded templates
- [ ] Language selection works correctly
- [ ] Fallback exists for backward compatibility
- [ ] Both English and Russian prompts exist

---

### T028: Replace _build_analysis_prompt() with Loaded Templates

**Purpose:** Replace hardcoded analysis prompts with loaded templates.

**Steps:**

1. Replace `_build_analysis_prompt()` method:
   ```python
   def _build_analysis_prompt(
       self,
       question: str,
       dialogue_summary: str,
       verdict_explanation: Optional[str],
       winner: Optional[str],
       language: str
   ) -> str:
       """
       Build the analysis prompt for the LLM.

       Now loads from template instead of hardcoded strings.
       """
       if self.prompt_loader:
           # Build context with all variables
           context = PromptContext(
               question=question,
               dialogue_summary=dialogue_summary,
               verdict_explanation=verdict_explanation or "",
               winner=winner or "",
               min_takeaways=self.config.min_takeaways,
               max_takeaways=self.config.max_takeaways
           )

           # Load and render template
           try:
               prompt_id = f"analysis.takeaway_{language}"
               template = self.prompt_loader.load(prompt_id)
           except KeyError:
               template = self.prompt_loader.load("analysis.takeaway")

           # Render with context
           return template.format(**context.to_dict())
       else:
           # Fallback to hardcoded (backward compat)
           return self._get_fallback_analysis_prompt(...)

   def _get_fallback_analysis_prompt(self, ...) -> str:
       """Fallback hardcoded analysis prompt."""
       # Move existing hardcoded logic here
       # ...
   ```

**Note:** The template needs to use all the context variables. Update `src/prompts/analysis/takeaway_analysis.md`:
```markdown
# Takeaway Analysis

## Committee Question

{question}

## Debate Dialogue

{dialogue_summary}

{verdict_explanation}

## Task

Analyze the debate and create a list of {min_takeaways} to {max_takeaways} key takeaways.

## Format

Each takeaway should be in format: "- [Brief description]"

## Examples

- Example takeaway 1
- Example takeaway 2

Generate takeaways now:
```

**Files:**
- `src/shared/debate/application/analyzers.py` (modify, ~50 lines)
- `src/prompts/analysis/takeaway_analysis.md` (update, ~35 lines)

**Validation:**
- [ ] Analysis prompt uses loaded templates
- [ ] All context variables are used
- [ ] Language selection works
- [ ] Fallback exists for backward compatibility

---

### T029: Remove Unused Hardcoded Prompt Strings

**Purpose:** Clean up remaining hardcoded prompts after migration.

**Steps:**

1. Search for remaining hardcoded prompts in `analyzers.py`:
   - Old Russian system prompt
   - Old English system prompt
   - Old Russian analysis prompt (f-string)
   - Old English analysis prompt (f-string)

2. Remove or move to fallback methods only

**Files:**
- `src/shared/debate/application/analyzers.py` (modify, cleanup)

**Validation:**
- [ ] No top-level hardcoded prompt strings
- [ ] Only fallback methods have hardcoded prompts
- [ ] Code is cleaner

---

### T030: Create Unit Tests for Takeaway Generation

**Purpose:** Test takeaway generation with file-based prompts.

**Steps:**

1. Create `tests/shared/debate/application/test_takeaway_analyzer_prompts.py`:
   ```python
   """Tests for takeaway analyzer with file-based prompts."""

   import pytest
   from pathlib import Path

   from shared.debate.application.analyzers import TakeawayAnalyzer, TakeawayConfig
   from shared.debate.application.prompt_loader import create_prompt_loader, PromptContext
   from shared.config.models import PromptsConfig


   @pytest.fixture
   def prompt_loader(tmp_path):
       """Create PromptLoader with analysis prompts."""
       analysis_dir = tmp_path / "prompts" / "analysis"
       analysis_dir.mkdir(parents=True)

       # Create test analysis prompts
       (analysis_dir / "system_prompt_en.md").write_text(
           "You are an analyst. Analyze: {dialogue_summary}"
       )
       (analysis_dir / "takeaway_analysis.md").write_text(
           "Q: {question}\nDialogue: {dialogue_summary}\n\nGenerate {min_takeaways} takeaways."
       )

       config = PromptsConfig(
           stages={},
           judge="judge.md",
           context="context.md",
           analysis={
               "system": str(analysis_dir / "system_prompt_en.md"),
               "takeaway": str(analysis_dir / "takeaway_analysis.md")
           }
       )

       return create_prompt_loader(config, base_path=tmp_path)


   @pytest.mark.asyncio
   async def test_takeaway_analyzer_with_file_prompts(prompt_loader, mock_llm):
       """Test TakeawayAnalyzer with file-based prompts."""
       config = TakeawayConfig(min_takeaways=3, max_takeaways=10)
       analyzer = TakeawayAnalyzer(config, prompt_loader=prompt_loader)

       dialogue = [
           {"speaker": "PRO", "content": "Good point", "stage": "opening"},
           {"speaker": "CON", "content": "Bad idea", "stage": "opening"}
       ]

       with patch.object(analyzer, 'llm') as mock_llm:
           mock_llm.invoke.return_value = MagicMock(
               content="- Good point\n- Bad idea\n- Need more info"
           )

           takeaways = await analyzer.generate_takeaways(
               dialogue=dialogue,
               question="Should we proceed?",
               winner="PRO"
           )

           assert len(takeaways) >= 3
           assert "Good point" in takeaways


   @pytest.mark.asyncio
   async def test_takeaway_analyzer_backward_compatibility():
       """Test analyzer works without PromptLoader."""
       config = TakeawayConfig(min_takeaways=3, max_takeaways=10)
       analyzer = TakeawayAnalyzer(config, prompt_loader=None)

       # Should use fallback prompts
       assert analyzer._get_system_prompt("en")  # Should not raise
       assert analyzer._get_system_prompt("ru")  # Should not raise
   ```

**Files:**
- `tests/shared/debate/application/test_takeaway_analyzer_prompts.py` (new, ~80 lines)

**Validation:**
- [ ] Tests pass with file-based prompts
- [ ] Tests verify backward compatibility
- [ ] Tests mock LLM calls

---

## Test Strategy

**Unit tests:**
- Test TakeawayAnalyzer with PromptLoader
- Test fallback to hardcoded prompts
- Test language selection
- Test takeaway generation

**Integration tests:**
- Test full takeaway generation flow
- Verify output quality

---

## Definition of Done

- [ ] TakeawayAnalyzer accepts PromptLoader
- [ ] System prompts use loaded templates
- [ ] Analysis prompts use loaded templates
- [ ] Language-specific prompts exist
- [ ] Fallback logic exists for backward compatibility
- [ ] Hardcoded prompts are cleaned up
- [ ] Unit tests pass
- [ ] Takeaway generation works correctly

---

## Reviewer Guidance

**Check these specific items:**
1. PromptLoader is properly injected
2. Language selection works
3. All template variables are used
4. Fallback logic exists
5. Backward compatibility is maintained
6. Tests cover new functionality
7. Code is cleaner than before

**Files to Review:**
- `src/shared/debate/application/analyzers.py`
- `src/prompts/analysis/system_prompt_en.md`
- `src/prompts/analysis/system_prompt_ru.md`
- `src/prompts/analysis/takeaway_analysis.md`
- `tests/shared/debate/application/test_takeaway_analyzer_prompts.py`

## Activity Log

- 2026-02-19T07:15:10Z – claude – shell_pid=78974 – lane=for_review – Moved to for_review
