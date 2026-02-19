# Debate Quality Enhancement with Prompt Management System

## Overview

This feature improves the quality of AI-generated debates in the Deb8flow product committee framework by extracting hardcoded prompts into a centralized management system and enhancing prompt engineering for deeper, more substantive discussions.

## Background

The current Deb8flow implementation has several quality limitations:

1. **Hardcoded prompts** throughout the codebase make it difficult to experiment with and improve debate quality
2. **Debates lack depth** - they have become faster and less thorough compared to earlier versions
3. **Limited prompt customization** requires code changes for any adjustments
4. **No standardized prompt structure** across different debate components
5. **The StandardDebateOrchestrator** (multi-turn interactive) is unused while SimpleDebateOrchestrator (single LLM call) produces less nuanced debates

## User Scenarios

### Scenario 1: Product Manager Improving Debate Quality

**Persona:** Product Manager using Deb8flow to evaluate PRDs

**Flow:**
1. User runs a debate and finds the arguments lack depth
2. User navigates to `src/prompts/` directory
3. User opens and edits the relevant prompt file (e.g., `debate/stages/opening_pro.md`)
4. User runs debate again with improved prompts
5. User observes more substantive arguments and better decision-making

**Outcome:** Debate quality improves through prompt iteration without touching code

### Scenario 2: Developer Adding a New Debate Stage

**Persona:** Developer extending the debate system

**Flow:**
1. Developer identifies need for a new debate stage (e.g., "clarification questions")
2. Developer creates new prompt file in `src/prompts/debate/stages/clarification.md`
3. Developer updates prompt configuration to reference the new file
4. System loads and uses the new prompt automatically

**Outcome:** Extensible prompt system that supports new debate stages

### Scenario 3: User Selecting Debate Mode

**Persona:** User with different debate quality/time needs

**Flow:**
1. User configures debate mode in `config/debate_config.yaml`
2. User selects "standard" mode for deep multi-turn interactive debates
3. OR user selects "simple" mode for quick single-LLM debates
4. System uses appropriate orchestrator and prompts
5. User receives debate output matching their quality/time preferences

**Outcome:** Flexible debate quality options for different use cases

### Scenario 4: Analyzing Debate Results

**Persona:** Stakeholder reviewing committee output

**Flow:**
1. User receives final debate report with conclusions
2. User reads structured takeaways extracted from improved prompts
3. User sees clearer, more actionable insights
4. User understands why specific decisions were reached

**Outcome:** Better decision-making support from improved debate analysis

## Functional Requirements

### FR-01: Prompt Directory Structure

The system MUST organize prompts in a hierarchical structure under `src/prompts/`:

```
src/prompts/
├── debate/
│   ├── stages/
│   │   ├── opening_pro.md
│   │   ├── opening_con.md
│   │   ├── rebuttal_pro.md
│   │   ├── rebuttal_con.md
│   │   ├── counter_pro.md
│   │   ├── counter_con.md
│   │   ├── final_pro.md
│   │   └── final_con.md
│   ├── judge/
│   │   └── verdict.md
│   ├── context/
│   │   └── debate_context.md
│   └── modes/
│       ├── standard.md
│       └── simple.md
├── analysis/
│   ├── system_prompt.md
│   └── takeaway_analysis.md
└── roles/
    ├── tpm.md
    ├── cpo.md
    ├── cfo.md
    ├── cto.md
    └── bdm.md
```

### FR-02: Prompt Template System

The system MUST support template variables in prompt files with the following syntax:

| Variable | Description | Example Usage |
|----------|-------------|---------------|
| `{question}` | The debate question | "Should we build this feature?" |
| `{topic}` | PRD topic/context (truncated) | First 500-800 chars of PRD |
| `{prd_content}` | Full PRD content | Complete PRD text |
| `{language}` | Language instruction | "English" or "Russian" |
| `{recent_context}` | Recent debate messages | Last 2-3 exchanges |
| `{pro_prompt}` | PRO role description | TPM agent prompt |
| `{con_prompt}` | CON role description | Opponent agent prompt |

### FR-03: Prompt Loader Service

The system MUST provide a `PromptLoader` service that:

1. Loads prompts from files at application startup
2. Caches prompts in memory for performance
3. Validates prompt templates (required variables present)
4. Supports hot-reloading during development (optional)
5. Provides clear error messages for missing or malformed prompts
6. Returns prompts with variables substituted from provided context

### FR-04: Enhanced Debate Stage Prompts

Each debate stage prompt MUST:

1. Specify clear instructions for argument structure (e.g., "200-400 words")
2. Require evidence-based arguments referencing PRD content
3. Mandate direct addressing of opponent's specific points
4. Enforce professional, constructive tone
5. Encourage depth over brevity while maintaining focus
6. Include examples of good argument structure (in prompt comments)

### FR-05: Judge Prompt Enhancement

The judge prompt MUST:

1. Provide clear evaluation criteria for arguments
2. Specify weights for different factors (evidence quality, logic, rebuttal effectiveness)
3. Require specific references to debate content in verdict
4. Include structured output format for verdict explanation
5. Encourage nuanced judgment (not just binary win/lose)

### FR-06: Takeaway Analysis Prompt Enhancement

The takeaway analyzer prompt MUST:

1. Define clear categories for takeaways (strengths, weaknesses, risks, positives)
2. Specify actionable format for each takeaway
3. Require evidence from debate dialogue
4. Balance PRO and CON perspectives
5. Limit takeaways to most impactful insights
6. Provide examples of well-formed takeaways

### FR-07: StandardDebateOrchestrator Restoration

The system MUST restore and upgrade the StandardDebateOrchestrator to:

1. Execute debates as separate LLM calls for each stage (not single prompt)
2. Allow each stage to build on previous context
3. Support longer, more iterative exchanges
4. Enable more nuanced judge evaluation with full conversation history
5. Maintain conversation state across multiple API calls

### FR-08: Debate Mode Selection

The system MUST support configurable debate modes:

1. **Standard Mode**: Multi-turn interactive debates with separate LLM calls per stage
2. **Simple Mode**: Single LLM call generating entire debate (current behavior)
3. Mode selection via configuration file (`config/debate_config.yaml`)
4. Default mode: Standard (for quality)

### FR-09: Prompt Configuration

The system MUST provide a configuration file mapping prompt types to file paths:

```yaml
prompts:
  stages:
    opening_pro: "src/prompts/debate/stages/opening_pro.md"
    opening_con: "src/prompts/debate/stages/opening_con.md"
    # ... etc
  judge: "src/prompts/debate/judge/verdict.md"
  context: "src/prompts/debate/context/debate_context.md"
  analysis:
    system: "src/prompts/analysis/system_prompt.md"
    takeaway: "src/prompts/analysis/takeaway_analysis.md"
```

### FR-10: Role Prompt Migration

Existing role prompts from `config/prompts/roles/` MUST be:

1. Migrated to `src/prompts/roles/` directory
2. Converted to Markdown format with `.md` extension
3. Enhanced with quality guidelines (argument depth, evidence requirements)
4. Maintained in English (language instruction handled separately)

### FR-11: Backward Compatibility

The system MUST maintain backward compatibility:

1. Existing `config/prompts/roles/` files continue to work if prompts not migrated
2. Existing debate outputs remain valid
3. No breaking changes to public APIs
4. Configuration file format allows optional prompt paths

## Success Criteria

### SC-01: Measurable Quality Improvements

- **Debate depth**: Average argument word count increases by 50%+ compared to baseline
- **Argument specificity**: 90%+ of arguments reference specific PRD content
- **Rebuttal quality**: 95%+ of rebuttals directly address opponent's specific points
- **Takeaway actionability**: 85%+ of takeaways contain actionable insights

### SC-02: Prompt Maintainability

- All prompts editable from `src/prompts/` without touching code files
- Prompt changes take effect without code recompilation
- New prompts can be added via file creation only
- Clear error messages for missing or malformed prompts

### SC-03: Debate Mode Performance

- Standard mode produces debates 2x+ longer than simple mode
- Standard mode debates demonstrate higher argument diversity (measured by unique concepts mentioned)
- Users can switch between modes via configuration only
- Both modes produce valid, parseable output

### SC-04: Developer Experience

- New developers can locate and modify prompts within 5 minutes
- Prompt template syntax is documented and discoverable
- Adding a new debate stage requires <30 minutes
- No code changes required for prompt adjustments

### SC-05: System Quality

- No decrease in debate execution speed (after initial prompt loading)
- Memory usage increase <10MB from prompt caching
- All existing tests pass after migration
- New tests added for prompt loading and validation

## Key Entities

### Prompt

| Attribute | Type | Description |
|-----------|------|-------------|
| `id` | string | Unique identifier (e.g., "debate.stages.opening_pro") |
| `file_path` | string | Absolute path to prompt file |
| `template` | string | Raw prompt template with variable placeholders |
| `required_vars` | string[] | List of required template variables |
| `language` | string | Prompt language ("en", "ru") |

### PromptContext

| Attribute | Type | Description |
|-----------|------|-------------|
| `question` | string | Debate question |
| `topic` | string | PRD topic excerpt |
| `prd_content` | string | Full PRD content |
| `language` | string | Output language |
| `recent_messages` | DebateMessage[] | Recent debate history |
| `pro_prompt` | string | PRO role description |
| `con_prompt` | string | CON role description |

### PromptLoader

| Method | Description |
|--------|-------------|
| `load(prompt_id: str) -> str` | Load prompt template by ID |
| `load_with_context(prompt_id: str, context: PromptContext) -> str` | Load and substitute variables |
| `validate(prompt_id: str) -> ValidationResult` | Validate prompt template |
| `reload() -> None` | Hot-reload all prompts (development) |

### DebateMode

| Value | Description |
|-------|-------------|
| `standard` | Multi-turn interactive debates (separate LLM calls) |
| `simple` | Single LLM call generating entire debate |

## Assumptions

1. **LLM API costs** are acceptable for standard mode (multiple API calls per debate)
2. **English prompts** are preferred for standardization; language instruction handled at runtime
3. **PRD content** is the primary source of evidence for debate arguments
4. **Debate participants** (TPM vs opponents) structure remains unchanged
5. **Existing role prompts** in `config/prompts/roles/` can be migrated without losing content
6. **Users** prefer quality over speed for most debate scenarios
7. **File system** access is available for prompt loading
8. **Prompt hot-reloading** is a nice-to-have but not required for production

## Dependencies

### Internal Dependencies

1. **Existing debate orchestration infrastructure** (`src/shared/debate/infrastructure/llm/`)
2. **Configuration system** (`src/shared/config/config_loader.py`)
3. **Domain entities** (`DebateRoom`, `DebateMessage`, `Verdict`)
4. **Report generators** (final report, conclusion)

### External Dependencies

1. **LLM Provider API** (OpenAI, Anthropic, or compatible) - for debate execution
2. **File system** - for prompt file storage
3. **YAML parser** - for configuration files
4. **Jinja2 or similar** (optional) - for advanced template rendering

## Out of Scope

The following items are explicitly out of scope for this feature:

1. **New debate participants** or role definitions (existing roles only)
2. **UI for prompt editing** (file-based editing only)
4. **Prompt versioning** or A/B testing infrastructure
5. **Multi-language prompts** (prompts in English only; language parameter for output)
6. **Real-time debate streaming** or web-based debate execution
7. **Prompt optimization algorithms** or automated prompt tuning
8. **Debate quality metrics dashboard** or analytics
9. **Changes to verdict format** or report structure (prompt improvements only)
10. **Authentication** or authorization for prompt access

## Edge Cases

| Scenario | Handling |
|----------|----------|
| Prompt file missing | System fails fast with clear error message indicating which file is missing |
| Prompt file empty | System returns error indicating empty prompt file |
| Required variable not provided | System validates before rendering and returns clear error |
| Circular prompt references | System detects and prevents circular references during loading |
| Prompt syntax error | System provides line number and specific error details |
| File permission errors | System returns actionable error message |
| Concurrent prompt modifications | System uses last-write-wins; recommends single editor per file |
| Very long prompt files (>100KB) | System warns but allows loading; performance may degrade |
| Special characters in templates | System properly escapes or handles special characters |
| Debate mode not specified | System defaults to "standard" mode with logged warning |

## Risks and Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Prompt extraction breaks existing functionality | High | Medium | Comprehensive test suite before and after migration |
| Standard mode significantly increases API costs | Medium | High | Cost monitoring; configurable default mode |
| Users don't adopt new prompt system | Medium | Low | Clear documentation; migration examples |
| Prompt hot-reloading causes instability | Low | Medium | Development-only feature; disabled in production |
| Template syntax complexity confuses users | Medium | Medium | Simple variable substitution; examples provided |
| Performance degradation from file I/O | Low | Low | In-memory caching; load-once pattern |
| Lost prompt improvements during migration | High | Low | Backup existing prompts before migration |
