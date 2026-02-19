---
work_package_id: WP04
title: Debate Orchestrator Prompt Integration
lane: planned
dependencies: []
subtasks: [T018, T019, T020, T021, T022, T023, T024, T025]
history:
- timestamp: '2025-02-19T00:00:00Z'
  action: Created
  agent: spec-kitty
---

# WP04: Debate Orchestrator Prompt Integration

## Objective

Refactor `LLMDebateOrchestrator` and `SimpleDebateOrchestrator` to use PromptLoader instead of hardcoded prompts. This is the big bang migration that removes all hardcoded prompt strings.

## Context

Now that PromptLoader exists (WP03), we need to:
1. Inject PromptLoader into both orchestrator classes
2. Replace all hardcoded prompts with loaded templates
3. Update the executor to create and pass PromptLoader
4. Remove old hardcoded prompt strings
5. Test that debates still work correctly

This is a **breaking change** - comprehensive testing is required.

**Files to modify:**
- `src/shared/debate/infrastructure/llm/debate_orchestrator.py`
- `src/shared/debate/infrastructure/executors/cli_executor.py`

**Prompt files to use:**
- `debate.context` → Debate context template
- `debate.stages.*` → Stage-specific prompts (opening, rebuttal, counter, final)
- `debate.judge` → Judge verdict prompt
- `debate.modes.simple` → Simple mode single-call prompt

## Implementation Guidance

### T018: Inject PromptLoader into Orchestrator Constructors

**Purpose:** Modify both orchestrator classes to accept PromptLoader.

**Steps:**

1. Modify `LLMDebateOrchestrator.__init__()`:
   ```python
   # In debate_orchestrator.py

   from ..application.prompt_loader import PromptLoader

   class LLMDebateOrchestrator:
       def __init__(
           self,
           prompt_loader: PromptLoader,  # NEW: Required parameter
           model: Optional[str] = None,
           temperature: float = 0.7,
           max_tokens: int = 1000,
           api_key: Optional[str] = None,
           base_url: Optional[str] = None,
           language: str = "en"
       ):
           # Store prompt_loader
           self.prompt_loader = prompt_loader
           self.language = language
           # ... rest of initialization (unchanged)
   ```

2. Modify `SimpleDebateOrchestrator.__init__()`:
   ```python
   class SimpleDebateOrchestrator:
       def __init__(
           self,
           prompt_loader: PromptLoader,  # NEW: Required parameter
           model: Optional[str] = None,
           temperature: float = 0.8,
           api_key: Optional[str] = None,
           base_url: Optional[str] = None,
           language: str = "en"
       ):
           # Store prompt_loader
           self.prompt_loader = prompt_loader
           self.language = language
           # ... rest of initialization (unchanged)
   ```

**Files:**
- `src/shared/debate/infrastructure/llm/debate_orchestrator.py` (modify, ~20 lines)

**Validation:**
- [ ] Both constructors accept `prompt_loader` parameter
- [ ] PromptLoader is stored as instance variable
- [ ] All other parameters remain unchanged

---

### T019: Replace _build_debate_context() Hardcoded Prompt

**Purpose:** Replace hardcoded debate context with loaded template.

**Steps:**

1. In `LLMDebateOrchestrator`, replace `_build_debate_context()`:
   ```python
   def _build_debate_context(self, topic: str, question: str, prd_content: str) -> str:
       """
       Build the context string for the debate.

       Now loads from template instead of hardcoded string.
       """
       # Load context template and render with variables
       context = self.prompt_loader.load_with_context(
           "debate.context",
           PromptContext(
               question=question,
               topic=topic[:500],  # Truncate as before
               prd_content=prd_content[:2000],  # Truncate as before
               language=self._get_language_instruction()
           )
       )
       return context

   def _get_language_instruction(self) -> str:
       """Get language instruction string."""
       language_instructions = {
           "ru": "Вы должны вести дебаты на РУССКОМ языке. All responses must be in Russian.",
           "en": "You must conduct the debate in ENGLISH.",
           "de": "Sie müssen die Debatte auf DEUTSCH führen.",
           "fr": "Vous devez mener le débat en FRANÇAIS.",
           "es": "Debe realizar el debate en ESPAÑOL.",
           "zh": "您必须用中文进行辩论。",
       }
       return language_instructions.get(
           self.language.lower(),
           f"You must conduct the debate in {self.language.upper()}."
       )
   ```

**Files:**
- `src/shared/debate/infrastructure/llm/debate_orchestrator.py` (modify, ~30 lines)

**Validation:**
- [ ] Old hardcoded prompt is removed
- [ ] New version uses PromptLoader
- [ ] Language instruction logic is preserved
- [ ] Truncation logic is preserved

---

### T020: Replace Stage-Specific Hardcoded Prompts

**Purpose:** Replace hardcoded prompts in all stage methods.

**Steps:**

1. Replace `_run_opening_statements()`:
   ```python
   async def _run_opening_statements(self, context: str, pro_prompt: str, con_prompt: str):
       """Run opening statements from both sides."""
       # Build base context for rendering
       base_context = PromptContext(
           question=context,  # Will be extracted
           topic=self._current_topic,  # Store in instance var
           language=self.language
       )

       # PRO opening
       pro_template = self.prompt_loader.load_with_context(
           "debate.stages.opening_pro",
           base_context
       )
       pro_response = await self._generate_response(
           system_prompt=pro_prompt,
           human_prompt=pro_template,
           stage="opening",
           speaker="PRO"
       )
       self.messages.append(DebateMessage("PRO", pro_response, "opening", validated=True))

       # CON opening
       con_template = self.prompt_loader.load_with_context(
           "debate.stages.opening_con",
           base_context
       )
       con_response = await self._generate_response(
           system_prompt=con_prompt,
           human_prompt=con_template,
           stage="opening",
           speaker="CON"
       )
       self.messages.append(DebateMessage("CON", con_response, "opening", validated=True))
   ```

2. Replace `_run_rebuttals()`:
   ```python
   async def _run_rebuttals(self, context: str, pro_prompt: str, con_prompt: str):
       """Run rebuttal stage."""
       recent_context = self._get_recent_context()

       base_context = PromptContext(
           question=context,
           recent_context=recent_context,
           language=self.language
       )

       # CON rebuttal
       con_template = self.prompt_loader.load_with_context(
           "debate.stages.rebuttal_con",
           base_context
       )
       con_rebuttal = await self._generate_response(
           system_prompt=con_prompt,
           human_prompt=con_template,
           stage="rebuttal",
           speaker="CON"
       )
       self.messages.append(DebateMessage("CON", con_rebuttal, "rebuttal", validated=True))

       # PRO rebuttal
       recent_context = self._get_recent_context()
       base_context.recent_context = recent_context
       pro_template = self.prompt_loader.load_with_context(
           "debate.stages.rebuttal_pro",
           base_context
       )
       pro_rebuttal = await self._generate_response(
           system_prompt=pro_prompt,
           human_prompt=pro_template,
           stage="rebuttal",
           speaker="PRO"
       )
       self.messages.append(DebateMessage("PRO", pro_rebuttal, "rebuttal", validated=True))
   ```

3. Similarly replace `_run_counter_arguments()` and `_run_final_arguments()`:
   ```python
   # Use prompt IDs:
   # - debate.stages.counter_pro
   # - debate.stages.counter_con
   # - debate.stages.final_pro
   # - debate.stages.final_con
   ```

**Files:**
- `src/shared/debate/infrastructure/llm/debate_orchestrator.py` (modify, ~80 lines)

**Validation:**
- [ ] All 8 stage prompts use loaded templates
- [ ] Recent context is updated between calls
- [ ] System prompt (role prompt) still comes from parameter
- [ ] Message appending logic is unchanged

---

### T021: Replace Hardcoded Judge Prompt

**Purpose:** Replace hardcoded judge verdict prompt.

**Steps:**

1. Replace `_run_verdict()`:
   ```python
   async def _run_verdict(self, context: str) -> str:
       """Run the judge's verdict and determine winner."""
       recent_context = self._get_recent_context()

       # Load judge template
       judge_template = self.prompt_loader.load_with_context(
           "debate.judge",
           PromptContext(
               question=context,
               recent_context=recent_context,
               language=self.language
           )
       )

       verdict = await self._generate_response(
           system_prompt=judge_template,  # Was hardcoded, now loaded
           human_prompt=f"Based on the debate above, provide your verdict.",
           stage="verdict",
           speaker="JUDGE"
       )
       self.messages.append(DebateMessage("JUDGE", verdict, "verdict", validated=True))

       # Extract winner (unchanged)
       if "WINNER: PRO" in verdict.upper():
           return "PRO"
       elif "WINNER: CON" in verdict.upper():
           return "CON"
       # ... rest unchanged
   ```

**Files:**
- `src/shared/debate/infrastructure/llm/debate_orchestrator.py` (modify, ~20 lines)

**Validation:**
- [ ] Old hardcoded judge prompt is removed
- [ ] Loaded template is used as system prompt
- [ ] Winner extraction logic is unchanged

---

### T022: Replace SimpleDebateOrchestrator Hardcoded Prompt

**Purpose:** Replace the large hardcoded debate prompt in SimpleDebateOrchestrator.

**Steps:**

1. First, create the simple mode prompt file `src/prompts/debate/modes/simple.md` (if not already created):
   ```markdown
   # Simple Mode Debate Template

   You are simulating a product committee debate about the following question:

   ## Question

   {question}

   ## Context (PRD excerpt)

   {topic}

   ## Full PRD Content

   {prd_content}

   ---

   ## Language

   LANGUAGE: {language}

   ## Participants

   You need to generate a realistic debate between two participants:
   - **PRO** (arguing FOR the project): {pro_prompt}
   - **CON** (arguing AGAINST the project): {con_prompt}

   ## Debate Structure

   Generate a debate following this exact structure:

   **PRO (opening):** [200-300 words arguing for the project]

   **CON (opening):** [200-300 words arguing against the project]

   **PRO (rebuttal):** [150-200 words responding to CON's opening]

   **CON (rebuttal):** [150-200 words responding to PRO's rebuttal]

   **PRO (final):** [100-150 words closing argument]

   **CON (final):** [100-150 words closing argument]

   **JUDGE:** After reviewing both arguments, WINNER: [PRO or CON]. [Brief 2-3 sentence explanation]

   ## Guidelines

   - Make the arguments specific to the actual PRD content
   - The PRO should focus on technical feasibility and benefits
   - The CON should focus on risks, costs, and concerns
   - The winner should be determined by who made stronger, more convincing arguments
   - Be detailed and specific, not generic

   Begin the debate now:
   ```

2. Update `SimpleDebateOrchestrator.execute_debate()`:
   ```python
   async def execute_debate(
       self,
       topic: str,
       pro_prompt: str,
       con_prompt: str,
       question: str,
       prd_content: str
   ) -> Tuple[List[Dict[str, Any]], str]:
       """
       Execute a debate using a single structured LLM call.
       """
       # Get language instruction
       language_instruction = self._get_language_instruction()

       # Load and render debate template
       debate_prompt = self.prompt_loader.load_with_context(
           "debate.modes.simple",
           PromptContext(
               question=question,
               topic=topic[:800],
               prd_content=prd_content[:1500],
               language=language_instruction,
               pro_prompt=pro_prompt[:300],
               con_prompt=con_prompt[:300]
           )
       )

       try:
           response = await asyncio.to_thread(
               self.llm.invoke,
               [HumanMessage(content=debate_prompt)]
           )
           # ... rest unchanged
   ```

**Files:**
- `src/prompts/debate/modes/simple.md` (create if needed, ~40 lines)
- `src/shared/debate/infrastructure/llm/debate_orchestrator.py` (modify, ~30 lines)

**Validation:**
- [ ] Simple mode prompt file exists
- [ ] Hardcoded prompt in execute_debate() is removed
- [ ] Loaded template is used
- [ ] All truncation logic is preserved

---

### T023: Update CliDebateExecutor to Instantiate Orchestrators with PromptLoader

**Purpose:** Modify the executor to create PromptLoader and pass it to orchestrators.

**Steps:**

1. First, note that `CliDebateExecutor` calls `scripts/document_debate_cli.py` as a subprocess.
   The actual orchestrator instantiation happens in that script.

2. We need to modify both the executor and the script:

   **In `cli_executor.py`:**
   ```python
   # Add PromptLoader creation (will be passed to subprocess via env or args)
   # For now, the subprocess handles orchestrator creation
   ```

   **In `scripts/document_debate_cli.py`:**
   ```python
   # Add imports
   from shared.debate.application.prompt_loader import create_prompt_loader, PromptContext
   from shared.config.config_loader import load_config
   from shared.config.models import PromptsConfig

   async def main():
       # ... existing argument parsing ...

       # Load configuration
       config = load_config()

       # Create prompts config from loaded config
       prompts_config = PromptsConfig(
           stages=config.prompts.stages,
           judge=config.prompts.judge,
           context=config.prompts.context,
           analysis=config.prompts.analysis
       )

       # Create PromptLoader
       prompt_loader = create_prompt_loader(prompts_config)

       # Create orchestrator with PromptLoader
       orchestrator = SimpleDebateOrchestrator(
           prompt_loader=prompt_loader,
           model=args.model,
           language=args.language
       )

       # ... rest of execution
   ```

**Files:**
- `scripts/document_debate_cli.py` (modify, ~30 lines)
- `src/shared/debate/infrastructure/executors/cli_executor.py` (may need updates, ~10 lines)

**Validation:**
- [ ] Script loads configuration
- [ ] PromptLoader is created
- [ ] Orchestrator receives PromptLoader
- [ ] Script still works from command line

---

### T024: Remove Unused Hardcoded Prompt Strings

**Purpose:** Clean up all remaining hardcoded prompts.

**Steps:**

1. Search for all remaining hardcoded prompts in `debate_orchestrator.py`:
   - Look for multi-line strings with prompt content
   - Look for f-strings with "You are", "Please present", etc.
   - Remove or replace with comments

2. Specifically, ensure these are removed:
   - Old `_build_debate_context()` return string
   - Old judge prompt in `_run_verdict()`
   - Old stage prompts in all stage methods
   - Old simple mode prompt in `SimpleDebateOrchestrator`

**Files:**
- `src/shared/debate/infrastructure/llm/debate_orchestrator.py` (modify, cleanup)

**Validation:**
- [ ] No multi-line hardcoded prompts remain
- [ ] No f-string prompts with debate instructions
- [ ] Code is cleaner and easier to read

---

### T025: Create Integration Tests for Debate Execution

**Purpose:** Test that debates execute correctly with file-based prompts.

**Steps:**

1. Create `tests/integration/test_debate_execution.py`:
   ```python
   """Integration tests for debate execution with file-based prompts."""

   import pytest
   import asyncio
   from pathlib import Path

   from shared.debate.infrastructure.llm.debate_orchestrator import (
       SimpleDebateOrchestrator,
       LLMDebateOrchestrator
   )
   from shared.debate.application.prompt_loader import (
       create_prompt_loader,
       PromptContext
     )
   from shared.config.models import PromptsConfig


   @pytest.fixture
   def prompt_loader(tmp_path):
       """Create PromptLoader with test prompts."""
       # Create test prompt files
       stages_dir = tmp_path / "prompts" / "debate" / "stages"
       judge_dir = tmp_path / "prompts" / "debate" / "judge"
       context_dir = tmp_path / "prompts" / "debate" / "context"
       modes_dir = tmp_path / "prompts" / "debate" / "modes"

       for d in [stages_dir, judge_dir, context_dir, modes_dir]:
           d.mkdir(parents=True)

       # Create minimal test prompts
       (stages_dir / "opening_pro.md").write_text("Q: {question}\nT: {topic}")
       (stages_dir / "opening_con.md").write_text("Q: {question}\nT: {topic}")
       # ... create all required prompts ...

       (judge_dir / "verdict.md").write_text("Q: {question}\nCtx: {recent_context}")
       (context_dir / "debate_context.md").write_text("Q: {question}\nT: {topic}")
       (modes_dir / "simple.md").write_text("Q: {question}\nT: {topic}")

       config = PromptsConfig(
           stages={
               "opening_pro": str(stages_dir / "opening_pro.md"),
               # ... all stages ...
           },
           judge=str(judge_dir / "verdict.md"),
           context=str(context_dir / "debate_context.md"),
           analysis={}
       )

       return create_prompt_loader(config, base_path=tmp_path)


   @pytest.mark.integration
   async def test_simple_debate_with_file_prompts(prompt_loader, mock_llm):
       """Test SimpleDebateOrchestrator with file-based prompts."""
       orchestrator = SimpleDebateOrchestrator(
           prompt_loader=prompt_loader,
           model="gpt-4o"
       )

       # Mock the LLM response
       with patch.object(orchestrator, 'llm') as mock_llm:
           mock_llm.invoke.return_value = MagicMock(
               content="PRO (opening): Test\n\nCON (opening): Test\n\nJUDGE: WINNER: PRO"
           )

       dialogue, winner = await orchestrator.execute_debate(
           topic="Test topic",
           pro_prompt="PRO role",
           con_prompt="CON role",
           question="Test question",
           prd_content="Test PRD"
       )

           assert winner == "PRO"
           assert len(dialogue) > 0


   @pytest.mark.integration
   async def test_orchestrator_loads_prompts(prompt_loader):
       """Test that orchestrator loads prompts from files."""
       orchestrator = SimpleDebateOrchestrator(
           prompt_loader=prompt_loader
       )

       # Should not raise any errors
       assert orchestrator.prompt_loader is not None
       assert len(orchestrator.prompt_loader.get_cached_prompt_ids()) > 0
   ```

**Files:**
- `tests/integration/test_debate_execution.py` (new, ~100 lines)

**Validation:**
- [ ] Integration tests pass
- [ ] Tests use real PromptLoader
- [ ] Tests mock LLM calls (don't make real API calls)
- [ ] Tests verify debate output structure

**Run Tests:**
```bash
pytest tests/integration/test_debate_execution.py -v -m integration
```

---

## Test Strategy

**Integration tests:**
- Test SimpleDebateOrchestrator with file prompts
- Test LLMDebateOrchestrator with file prompts
- Verify debate output structure
- Verify prompt rendering
- Use mocked LLM to avoid API calls

**Manual testing:**
- Run a full debate with real prompts
- Compare output quality before/after
- Verify all prompts are loaded correctly

---

## Definition of Done

- [ ] Both orchestrators accept PromptLoader in constructor
- [ ] _build_debate_context() uses loaded template
- [ ] All stage methods use loaded templates
- [ ] Judge verdict uses loaded template
- [ ] SimpleDebateOrchestrator uses loaded template
- [ ] CliDebateExecutor creates PromptLoader
- [ ] All hardcoded prompts are removed
- [ ] Integration tests pass
- [ ] Manual debate test succeeds
- [ ] Debate output quality is maintained

---

## Risks

1. **Breaking Debate Execution**: Mitigated by comprehensive testing
2. **Performance Degradation**: Mitigated by in-memory caching
3. **Prompt Loading Errors**: Mitigated by validation in PromptLoader
4. **Template Rendering Errors**: Mitigated by clear error messages

---

## Reviewer Guidance

**Check these specific items:**
1. All hardcoded prompts are removed
2. PromptLoader is properly injected
3. Template variables match PromptContext fields
4. Truncation logic is preserved
5. Message flow is unchanged
6. Error handling is maintained
7. Integration tests cover main scenarios
8. Code is cleaner than before

**Files to Review:**
- `src/shared/debate/infrastructure/llm/debate_orchestrator.py`
- `src/shared/debate/infrastructure/executors/cli_executor.py`
- `scripts/document_debate_cli.py`
- `tests/integration/test_debate_execution.py`

**Common Issues to Look For:**
- Remaining hardcoded prompts
- Missing PromptContext variables
- Broken message flow
- Lost truncation logic
- Missing error handling
- Weak test coverage
