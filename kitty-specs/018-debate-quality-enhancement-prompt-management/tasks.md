# Work Packages: Debate Quality Enhancement with Prompt Management System

**Feature:** Debate Quality Enhancement with Prompt Management System
**Feature Number:** 018
**Created:** 2025-02-19

## Overview

This feature improves AI-generated debate quality by extracting hardcoded prompts into a centralized management system and restoring multi-turn interactive debates. The implementation involves creating a PromptLoader service, organizing prompt files, enhancing debate orchestrators, and maintaining backward compatibility.

**Total Work Packages:** 8
**Total Subtasks:** 38
**Estimated Prompt Size Range:** 250-480 lines per WP

---

## Phase 0: Foundation Setup

### WP01: Prompt Directory Structure and Initial Files

**Priority:** P0 (Blocking)
**Estimated Prompt Size:** ~320 lines
**Prompt File:** [tasks/WP01-prompt-directory-structure.md](tasks/WP01-prompt-directory-structure.md)
**Dependencies:** None

**Summary:** Create the complete prompt directory hierarchy under `src/prompts/` with all necessary Markdown files for debate stages, judge prompts, analysis prompts, and role prompts. This foundational work enables all subsequent prompt extraction and enhancement.

**Included Subtasks:**
- [ ] **T001:** Create `src/prompts/` directory structure with all subdirectories (debate/stages/, debate/judge/, debate/context/, debate/modes/, analysis/, roles/)
- [ ] **T002:** Create enhanced debate stage prompt files (opening_pro.md, opening_con.md, rebuttal_pro.md, rebuttal_con.md, counter_pro.md, counter_con.md, final_pro.md, final_con.md)
- [ ] **T003:** Create judge verdict prompt file (judge/verdict.md) with enhanced evaluation criteria
- [ ] **T004:** Create debate context template (debate/context/debate_context.md) with variable placeholders
- [ ] **T005:** Create analysis prompt files (analysis/system_prompt.md, analysis/takeaway_analysis.md) with improved guidelines
- [ ] **T006:** Migrate and enhance role prompt files from `config/prompts/roles/*.txt` to `src/prompts/roles/*.md`

**Implementation Sketch:**
1. Create directory hierarchy using `Path.mkdir(parents=True, exist_ok=True)`
2. For each prompt file, write enhanced Markdown with:
   - Clear instructions for argument structure (200-400 words per response)
   - Evidence-based argument requirements referencing PRD content
   - Direct address of opponent's points
   - Professional tone guidelines
   - Template variables using `{variable}` syntax
3. Migrate role prompts by reading existing `.txt` files and converting to `.md` with quality enhancements

**Parallel Opportunities:** T002-T006 can be done in parallel (different files)

**Risks:** Role prompt content loss during migration - backup originals first

**Dependencies:** None - this is the foundation WP

---

### WP02: Prompt Configuration Schema

**Priority:** P0 (Blocking)
**Estimated Prompt Size:** ~280 lines
**Prompt File:** [tasks/WP02-prompt-configuration-schema.md](tasks/WP02-prompt-configuration-schema.md)
**Dependencies:** WP01

**Summary:** Create the configuration schema for prompt file paths in `config/debate_config.yaml` and add Pydantic models for prompt configuration validation. This enables the system to locate and validate prompt files.

**Included Subtasks:**
- [ ] **T007:** Add `prompts:` section to `config/debate_config.yaml` with mappings for all prompt types
- [ ] **T008:** Create `PromptConfig` Pydantic model in `src/shared/config/models.py` for validation
- [ ] **T009:** Add `debate_mode` configuration option to `config/debate_config.yaml` (standard/simple)
- [ ] **T010:** Create unit tests for prompt configuration loading and validation

**Implementation Sketch:**
1. Extend `config/debate_config.yaml` with:
   ```yaml
   prompts:
     stages:
       opening_pro: "src/prompts/debate/stages/opening_pro.md"
       # ... all stage prompts
     judge: "src/prompts/debate/judge/verdict.md"
     context: "src/prompts/debate/context/debate_context.md"
     analysis:
       system: "src/prompts/analysis/system_prompt.md"
       takeaway: "src/prompts/analysis/takeaway_analysis.md"
   debate:
     mode: "standard"  # or "simple"
   ```
2. Create Pydantic model with validation for file existence
3. Add tests that verify configuration loading fails gracefully with missing files

**Parallel Opportunities:** None (sequential configuration updates)

**Risks:** YAML syntax errors could break existing config - use schema validation

**Dependencies:** WP01 must create prompt files first

---

### WP03: PromptLoader Service

**Priority:** P0 (Blocking)
**Estimated Prompt Size:** ~420 lines
**Prompt File:** [tasks/WP03-prompt-loader-service.md](tasks/WP03-prompt-loader-service.md)
**Dependencies:** WP01, WP02

**Summary:** Implement the core PromptLoader service that loads, caches, validates, and renders prompt templates with variable substitution. This is the heart of the prompt management system.

**Included Subtasks:**
- [ ] **T011:** Create `PromptLoader` class in `src/shared/debate/application/prompt_loader.py` with load(), load_with_context(), validate(), and reload() methods
- [ ] **T012:** Implement in-memory caching with thread-safe access
- [ ] **T013:** Add template variable validation (check for required variables like {question}, {prd_content})
- [ ] **T014:** Implement string-based template rendering using Python str.format() (simple replacement)
- [ ] **T015:** Add comprehensive error handling for missing files, empty prompts, invalid variables
- [ ] **T016:** Create unit tests for PromptLoader covering loading, caching, validation, rendering, and error cases
- [ ] **T017:** Add logging for prompt loading and rendering operations

**Implementation Sketch:**
1. Create `PromptLoader` with:
   - `_cache: Dict[str, str]` for loaded templates
   - `_config: PromptConfig` for file path mappings
   - `load(prompt_id: str) -> str`: Load from cache or disk
   - `load_with_context(prompt_id: str, context: PromptContext) -> str`: Load and substitute
   - `validate(prompt_id: str) -> ValidationResult`: Check required variables
   - `reload() -> None`: Clear cache and reload
2. Template rendering uses `template.format(**context_dict)` with error handling for missing keys
3. Create `PromptContext` dataclass with all required fields
4. Tests should cover: cache hits, cache misses, missing files, variable validation

**Parallel Opportunities:** T012-T017 can partially parallelize (different concerns)

**Risks:** Template injection attacks - validate variable names, sanitize input

**Dependencies:** WP01 (prompt files), WP02 (configuration schema)

---

### WP04: Debate Orchestrator Prompt Integration

**Priority:** P0 (Blocking)
**Estimated Prompt Size:** ~460 lines
**Prompt File:** [tasks/WP04-orchestrator-prompt-integration.md](tasks/WP04-orchestrator-prompt-integration.md)
**Dependencies:** WP03

**Summary:** Refactor `LLMDebateOrchestrator` and `SimpleDebateOrchestrator` to use PromptLoader instead of hardcoded prompts. This is the big bang migration that removes all hardcoded prompt strings.

**Included Subtasks:**
- [ ] **T018:** Inject PromptLoader into `LLMDebateOrchestrator.__init__()` and `SimpleDebateOrchestrator.__init__()`
- [ ] **T019:** Replace `_build_debate_context()` hardcoded prompt with loaded template from `debate/context/debate_context.md`
- [ ] **T020:** Replace stage-specific hardcoded prompts in `_run_opening_statements()`, `_run_rebuttals()`, `_run_counter_arguments()`, `_run_final_arguments()` with loaded templates
- [ ] **T021:** Replace hardcoded judge prompt in `_run_verdict()` with loaded template from `judge/verdict.md`
- [ ] **T022:** Replace hardcoded debate prompt in `SimpleDebateOrchestrator.execute_debate()` with loaded template from `debate/modes/simple.md`
- [ ] **T023:** Update `CliDebateExecutor` to instantiate orchestrators with PromptLoader
- [ ] **T024:** Remove all now-unused hardcoded prompt strings from debate_orchestrator.py
- [ ] **T025:** Create integration tests for debate execution with file-based prompts

**Implementation Sketch:**
1. Modify orchestrator constructors to accept `prompt_loader: PromptLoader`
2. For each prompt location, replace:
   ```python
   # OLD: hardcoded string
   context = f"""DEBATE CONTEXT: ..."""

   # NEW: loaded template
   context = prompt_loader.load_with_context(
       "debate.context",
       PromptContext(question=question, topic=topic, prd_content=prd_content, language=language)
   )
   ```
3. Update factory methods in `CliDebateExecutor` to create PromptLoader instance
4. Integration tests should run full debates and verify output quality

**Parallel Opportunities:** T019-T022 can be done in parallel (different methods)

**Risks:** Breaking existing debate behavior - comprehensive integration tests required

**Dependencies:** WP03 (PromptLoader must be implemented)

---

### WP05: Takeaway Analyzer Prompt Migration

**Priority:** P1 (High)
**Estimated Prompt Size:** ~340 lines
**Prompt File:** [tasks/WP05-takeaway-analyzer-migration.md](tasks/WP05-takeaway-analyzer-migration.md)
**Dependencies:** WP03

**Summary:** Refactor `TakeawayAnalyzer` to use PromptLoader for system and analysis prompts instead of hardcoded strings.

**Included Subtasks:**
- [ ] **T026:** Inject PromptLoader into `TakeawayAnalyzer.__init__()`
- [ ] **T027:** Replace `_get_system_prompt()` hardcoded strings with loaded templates from `analysis/system_prompt.md`
- [ ] **T028:** Replace `_build_analysis_prompt()` hardcoded strings with loaded templates from `analysis/takeaway_analysis.md`
- [ ] **T029:** Remove all unused hardcoded prompt strings from analyzers.py
- [ ] **T030:** Create unit tests for takeaway generation with file-based prompts

**Implementation Sketch:**
1. Modify `TakeawayAnalyzer.__init__()` to accept `prompt_loader: PromptLoader`
2. Replace language-based prompt selection:
   ```python
   # OLD: if language == "ru": return """..."""
   # NEW: prompt_id = "analysis.system_ru" if language == "ru" else "analysis.system_en"
   ```
3. Update `CliDebateExecutor._generate_takeaways()` to pass PromptLoader
4. Tests verify takeaway generation produces expected output

**Parallel Opportunities:** T027-T028 can be done in parallel

**Risks:** Breaking takeaway generation - tests should verify output quality

**Dependencies:** WP03 (PromptLoader must be implemented)

---

### WP06: StandardDebateOrchestrator Restoration

**Priority:** P1 (High)
**Estimated Prompt Size:** ~480 lines
**Prompt File:** [tasks/WP06-standard-orchestrator-restoration.md](tasks/WP06-standard-orchestrator-restoration.md)
**Dependencies:** WP04

**Summary:** Restore and upgrade the `StandardDebateOrchestrator` (multi-turn interactive debates) with separate LLM calls per stage. This enables deeper, more iterative debates compared to SimpleDebateOrchestrator.

**Included Subtasks:**
- [ ] **T031:** Create `StandardDebateOrchestrator` class in `src/shared/debate/infrastructure/llm/standard_orchestrator.py` with multi-turn architecture
- [ ] **T032:** Implement stage-by-stage execution with separate LLM calls (opening → rebuttal → counter → final → verdict)
- [ ] **T033:** Add conversation state management across stages (accumulate full history for each call)
- [ ] **T034:** Implement enhanced context building with full debate history for judge evaluation
- [ ] **T035:** Add retry logic per-stage with fallback to continue debate
- [ ] **T036:** Create integration tests comparing standard vs simple mode output quality

**Implementation Sketch:**
1. Create `StandardDebateOrchestrator` that:
   - Executes each stage as separate `await self._generate_response()` call
   - Accumulates full message history: `self.messages.append(DebateMessage(...))`
   - Passes full history to judge: `recent_context = self._get_full_context()`
2. Use same PromptLoader interface as SimpleDebateOrchestrator
3. Key difference: Each stage gets fresh LLM call with full context
4. Tests compare debate length, argument diversity, word count between modes

**Parallel Opportunities:** T032-T035 can be done in parallel (different stages)

**Risks:** API cost increase (5+ calls per debate) - documented in config

**Dependencies:** WP04 (orchestrator prompt integration pattern)

---

### WP07: Debate Mode Selection and Configuration

**Priority:** P1 (High)
**Estimated Prompt Size:** ~320 lines
**Prompt File:** [tasks/WP07-debate-mode-selection.md](tasks/WP07-debate-mode-selection.md)
**Dependencies:** WP06

**Summary:** Implement debate mode selection logic allowing users to choose between standard (multi-turn) and simple (single-call) modes via configuration. Create factory pattern for orchestrator instantiation.

**Included Subtasks:**
- [ ] **T037:** Create `DebateMode` enum in `src/shared/debate/domain/entities.py` with values STANDARD and SIMPLE
- [ ] **T038:** Create `DebateOrchestratorFactory` in `src/shared/debate/infrastructure/llm/factory.py` with mode-based instantiation
- [ ] **T039:** Update `CliDebateExecutor` to use factory for creating orchestrators based on config
- [ ] **T040:** Add configuration validation for `debate.mode` with default to "standard"
- [ ] **T041:** Create unit tests for factory and mode selection logic

**Implementation Sketch:**
1. Create enum:
   ```python
   class DebateMode(str, Enum):
       STANDARD = "standard"
       SIMPLE = "simple"
   ```
2. Factory method:
   ```python
   def create_orchestrator(mode: DebateMode, prompt_loader: PromptLoader, ...) -> DebateOrchestrator:
       if mode == DebateMode.STANDARD:
           return StandardDebateOrchestrator(...)
       else:
           return SimpleDebateOrchestrator(...)
   ```
3. Update `CliDebateExecutor` to read `config.debate.mode` and pass to factory
4. Tests verify correct orchestrator type for each mode

**Parallel Opportunities:** T037-T040 can be done in parallel

**Risks:** Mode configuration errors - clear validation messages required

**Dependencies:** WP06 (StandardDebateOrchestrator must exist)

---

### WP08: Backward Compatibility and Migration

**Priority:** P1 (High)
**Estimated Prompt Size:** ~380 lines
**Prompt File:** [tasks/WP08-backward-compatibility-migration.md](tasks/WP08-backward-compatibility-migration.md)
**Dependencies:** WP04, WP05

**Summary:** Ensure backward compatibility with existing `config/prompts/roles/` files, add fallback logic, create migration guide, and update documentation. This allows gradual migration without breaking existing setups.

**Included Subtasks:**
- [ ] **T042:** Add fallback logic to PromptLoader to check `config/prompts/roles/` if `src/prompts/roles/` not found
- [ ] **T043:** Create migration script `scripts/migrate_prompts.py` to copy old prompts to new location
- [ ] **T044:** Add deprecation warnings for old prompt paths
- [ ] **T045:** Update README with new prompt management documentation
- [ ] **T046:** Create PROMPTS.md guide with template variable reference and examples
- [ ] **T047:** Run full integration test suite to verify no regressions

**Implementation Sketch:**
1. Fallback logic in PromptLoader:
   ```python
   def _load_prompt_file(self, path: str) -> str:
       if Path(path).exists():
           return Path(path).read_text()
       # Fallback to old location
       old_path = path.replace("src/prompts", "config/prompts")
       if Path(old_path).exists():
           logger.warning(f"Using deprecated path: {old_path}")
           return Path(old_path).read_text()
       raise PromptNotFound(f"Prompt not found: {path}")
   ```
2. Migration script:
   - Backs up existing `config/prompts/roles/`
   - Copies to `src/prompts/roles/`
   - Updates config file paths
3. Documentation includes:
   - Quick start for editing prompts
   - Template variable reference
   - Adding new debate stages
   - Troubleshooting guide

**Parallel Opportunities:** T042-T046 can be done in parallel

**Risks:** Breaking existing user workflows - thorough testing required

**Dependencies:** WP04, WP05 (prompt integration must be complete)

---

## Dependencies Graph

```
WP01 (Prompt Files)
    ↓
WP02 (Config Schema) ─┐
    ↓                  │
WP03 (PromptLoader) ←─┘
    ↓
    ├─→ WP04 (Orchestrator Integration) ──→ WP06 (Standard Orchestrator) ──→ WP07 (Mode Selection)
    │
    └─→ WP05 (Takeaway Migration) ─────────────────────────────────────────→ WP08 (Compatibility)
```

## Parallelization Opportunities

**Maximum Parallel WPs:** 2 (after WP01-WP03)
- WP04 and WP05 can run in parallel (both depend on WP03)
- WP06 and WP05 can run in parallel (WP06 depends on WP04, WP05 depends on WP03)

## MVP Scope

**Minimum Viable Product:** WP01 + WP02 + WP03 + WP04 + WP08
- Enables prompt management for simple mode
- Maintains backward compatibility
- ~20 subtasks

**Full Feature:** All WPs (WP01-WP08)
- Adds standard mode with multi-turn debates
- Complete prompt migration
- ~47 subtasks

## Risk Summary

| Risk | Impact | Mitigation |
|------|--------|------------|
| Breaking existing debates | High | Comprehensive integration tests, gradual migration |
| API cost increase (standard mode) | Medium | Configurable default mode, cost monitoring |
| Prompt file corruption | Medium | Validation on load, backup before migration |
| Performance degradation | Low | In-memory caching, async I/O |
| Lost prompt content during migration | High | Backup originals, verify migration script |

---

## Next Steps

1. Review work packages and approve task breakdown
2. Begin implementation with `/spec-kitty.implement WP01`
3. Parallelize work where possible (WP04 + WP5 after WP03)
4. Run `/spec-kitty.review` after each WP completion
