---
work_package_id: WP05
title: Rewriter Agent Core
lane: planned
dependencies:
- WP01
subtasks:
- T022
- T023
- T024
- T025
- T026
- T027
phase: Phase 2 - Implementation
assignee: ''
agent: ''
shell_pid: ''
review_status: ''
reviewed_by: ''
history:
- timestamp: '2026-02-17T21:00:00Z'
  lane: planned
  agent: system
  shell_pid: ''
  action: Prompt created via /spec-kitty.tasks
---

# Work Package Prompt: WP05 – Rewriter Agent Core

## Objectives & Success Criteria

- **Goal**: Implement the rewriter agent with LLM integration, recommendation parsing, and document rewriting logic.
- **Success Criteria**:
  - `BaseAgent` class provides LLM integration inheriting from existing `BaseComponent`
  - Can extract recommendations from conclusion.md using LLM with structured output
  - Can rewrite documents using LLM with aggressive recommendation application
  - Validates that recommendations were applied (completeness check)
  - Handles edge cases (empty conclusion, contradictory recommendations)

## Context & Constraints

- **Prerequisites**: WP01 (types), WP03 (converters)
- **Supporting Documents**:
  - `kitty-specs/015-document-rewrite-agent/data-model.md` - Recommendation structure
  - `kitty-specs/015-document-rewrite-agent/contracts/rewriter_agent_contract.json` - Agent contract
  - `kitty-specs/015-document-rewrite-agent/research.md` - Prompt strategy, conclusion parsing
  - `nodes/base_component.py` - Existing BaseComponent pattern to inherit from
- **Constraints**:
  - Use same LLM configuration as debate participants
  - Single comprehensive prompt (not chunked)
  - Apply recommendations aggressively without asking user
  - Resolve contradictions independently
  - Preserve sections without recommendations

## Subtasks & Detailed Guidance

### Subtask T022 – Create base agent class

**Purpose**: Create base agent class that provides LLM integration for the rewriter.

**Steps**:
1. Create `src/agents/base_agent.py` (new file)
2. Import `BaseComponent` from `nodes.base_component`
3. Import `LLMConfig`, `RewriteOptions` from `src.types.rewrite_types`
4. Create `BaseAgent` class inheriting from `BaseComponent`:
   - Accept `llm_config: LLMConfig` in `__init__`
   - Store LLM configuration for use in agent methods
   - Provide `create_chain()` method for structured output (reuse from BaseComponent)
   - Provide `invoke_chain()` helper for calling LLM with retry logic
   - Add token tracking for monitoring LLM usage
5. Add docstrings explaining the agent pattern and usage

**Files**:
- `src/agents/base_agent.py` (new, ~80 lines)

**Validation**:
- [ ] `BaseAgent` inherits from `BaseComponent`
- [ ] Can instantiate with LLMConfig
- [ ] Provides chain creation and invocation helpers
- [ ] Token tracking works (can be verified in logs)

**Notes**:
- Follow existing BaseComponent pattern from `nodes/base_component.py`
- The agent is NOT a LangGraph node - it's a standalone script
- Reuse retry logic and token tracking from BaseComponent

---

### Subtask T023 – Extract recommendations from conclusion

**Purpose**: Use LLM to extract structured recommendations from conclusion.md.

**Steps**:
1. Create `src/agents/rewriter_agent.py` (new file)
2. Import `BaseAgent` from `src.agents.base_agent`
3. Import types: `RewriteRequest`, `Recommendation`, `ActionType`
4. Create `RewriterAgent` class inheriting from `BaseAgent`:
5. Implement `extract_recommendations(conclusion_path: str) -> list[Recommendation]`:
   - Read conclusion.md file
   - Build extraction prompt:
     - System: "Extract actionable recommendations from conclusion report"
     - Task: "For each recommendation, provide: section_reference, action_type (REMOVE/UPDATE/ADD/REPLACE/RESTRUCTURE), target_content, new_content, priority (1-5), rationale"
     - Output: "Return as JSON list of recommendations"
   - Call LLM with structured output (JSON mode if available)
   - Parse JSON response into `Recommendation` objects
   - Return list of recommendations
   - Handle errors: return empty list, log warning

**Files**:
- `src/agents/rewriter_agent.py` (new, ~200 lines total with other subtasks)

**Extraction prompt structure**:
```
Extract all actionable recommendations from the conclusion report below.

For each recommendation, identify:
- Section reference (e.g., "Section 3.2" or null if global)
- Action to take: REMOVE, UPDATE, ADD, REPLACE, or RESTRUCTURE
- Target content (what to change)
- New content (what to change to)
- Priority (1-5, where 1 is highest)
- Rationale (why this change is recommended)

Output as JSON list with this structure:
[
  {
    "section_reference": "Section 3.2" | null,
    "action_type": "REMOVE" | "UPDATE" | "ADD" | "REPLACE" | "RESTRUCTURE",
    "target_content": "content to change" | null,
    "new_content": "new content" | null,
    "priority": 1-5,
    "rationale": "why this change" | null
  }
]

Conclusion report:
{conclusion_text}
```

**Validation**:
- [ ] Reads conclusion.md file
- [ ] Calls LLM with extraction prompt
- [ ] Parses JSON response into Recommendation objects
- [ ] Returns list of recommendations
- [ ] Handles parsing errors gracefully

**Notes**:
- Use LLM's JSON mode if available (OpenAI supports this)
- Fallback: try parsing JSON, if fails, return empty list and use full text
- The full conclusion text will be used as fallback context in rewrite step

---

### Subtask T024 – Rewrite document with LLM

**Purpose**: Implement the core rewriting logic that applies recommendations to the document.

**Steps**:
1. In `src/agents/rewriter_agent.py`, implement `rewrite_document(request: RewriteRequest) -> RewriteResult`:
   - Start timer for tracking processing time
   - Read original document (markdown format from converter)
   - Read conclusion.md
   - Extract recommendations using `extract_recommendations()`
   - Build rewrite prompt:
     - System: "You are a document rewriter. Apply recommendations from conclusion report."
     - Context: Original document (markdown), Conclusion report, Recommendations list
     - Rules: Apply ALL recommendations aggressively, preserve sections without recommendations, resolve contradictions independently, add `<!-- REVIEW NOTE: -->` only when absolutely necessary
     - Task: "Rewrite the document applying all recommendations. Return the complete rewritten document as markdown."
   - Call LLM with rewrite prompt
   - Parse rewritten markdown from LLM response
   - Track: recommendations_count, recommendations_applied (estimated), inline_notes_count (count `<!-- REVIEW NOTE: -->`)
   - Convert back to original format using appropriate converter
   - Generate output filename using timestamp
   - Save rewritten document to output directory
   - Return `RewriteResult` with all fields populated

**Files**:
- `src/agents/rewriter_agent.py` (append to existing file from T023)

**Rewrite prompt structure**:
```
You are a document rewriter. Your task is to apply ALL recommendations from a debate conclusion report to rewrite a document.

## Original Document
{original_markdown}

## Conclusion Report
{conclusion_text}

## Recommendations to Apply
{recommendations_list}

## Rules
1. Apply ALL recommendations aggressively - do not ask for clarification
2. Preserve sections of the document that have no corresponding recommendations
3. Resolve any contradictions in recommendations independently by choosing the most consistent option
4. Do NOT remove important sections unless explicitly instructed in the recommendations
5. Preserve the document structure unless the recommendations recommend a different structure
6. Only add inline comments like `<!-- REVIEW NOTE: explanation -->` when you absolutely cannot apply a recommendation unambiguously
7. Do NOT leave "TODO" or placeholder text in the final output
8. Return the COMPLETE rewritten document - not just the changes

## Task
Rewrite the document above applying all the recommendations. Return your response as the complete rewritten document in markdown format.
```

**Validation**:
- [ ] Reads original document and conclusion
- [ ] Calls LLM with comprehensive rewrite prompt
- [ ] Parses rewritten markdown from response
- [ ] Saves rewritten document with correct filename format
- [ ] Returns RewriteResult with all fields populated

**Notes**:
- Use the same model as debate participants (from LLMConfig)
- Temperature 0.3-0.5 for more deterministic rewriting (lower than debate)
- Max tokens should accommodate full rewritten document
- Handle LLM errors gracefully (return error in RewriteResult)

---

### Subtask T025 – Create rewriter prompts

**Purpose**: Create system and human prompts for the rewriter agent.

**Steps**:
1. Create `src/prompts/rewriter_prompts.md` (new file)
2. Add system prompt for recommendation extraction:
   - Role: "You are a recommendation extraction assistant"
   - Task: "Extract actionable recommendations from debate conclusion reports"
   - Output format: JSON with structure matching Recommendation dataclass
3. Add system prompt for document rewriting:
   - Role: "You are a document rewriter applying debate recommendations"
   - Task: "Rewrite documents applying all recommendations aggressively"
   - Rules: Apply ALL, preserve unchanged sections, resolve contradictions, add review notes only when necessary
   - Output format: Complete rewritten document in markdown
4. Add notes section explaining prompt design decisions

**Files**:
- `src/prompts/rewriter_prompts.md` (new, ~120 lines)

**Extraction prompt** (excerpt):
```
# Recommendation Extraction System Prompt

You are a recommendation extraction assistant. Your task is to extract all actionable recommendations from debate conclusion reports.

For each recommendation, identify:
- **Section reference**: Which section this applies to (e.g., "Section 3.2") or null if global
- **Action type**: What action to take (REMOVE, UPDATE, ADD, REPLACE, RESTRUCTURE)
- **Target content**: What content to change (if applicable)
- **New content**: What to change to (if applicable)
- **Priority**: 1-5 where 1 is highest priority
- **Rationale**: Why this change is recommended

Output format: JSON list matching the Recommendation schema.
```

**Rewrite prompt** (excerpt):
```
# Document Rewriter System Prompt

You are a professional document rewriter. Your task is to rewrite documents by applying ALL recommendations from a debate conclusion report.

## Core Principles

1. **Aggressive Application**: Apply ALL recommendations without asking for clarification
2. **Preservation**: Keep sections unchanged if they have no corresponding recommendations
3. **Independence**: Resolve contradictions yourself - choose the most consistent option
4. **Clarity**: Only add `<!-- REVIEW NOTE: -->` when absolutely necessary (should be rare)
5. **Completeness**: Never leave TODO or placeholder text

## What to Change

- Remove sections explicitly marked for removal
- Update content as specified in recommendations
- Add new content where recommended
- Replace content when directed
- Restructure document if recommended

## What to Preserve

- Sections without any corresponding recommendations
- Document structure (unless restructuring is recommended)
- Overall tone and voice (unless changed by recommendations)

Return the complete rewritten document in markdown format.
```

**Validation**:
- [ ] System prompts clearly define the agent's role
- [ ] Extraction prompt specifies JSON output format
- [ ] Rewrite prompt emphasizes aggressive application
- [ ] Both prompts include examples where helpful

---

### Subtask T026 – Validate rewrite completeness

**Purpose**: Check that all recommendations were applied during rewriting.

**Steps**:
1. In `src/agents/rewriter_agent.py`, implement `validate_rewrite_completeness(original_markdown: str, rewritten_markdown: str, recommendations: list[Recommendation]) -> tuple[bool, str]`:
   - For each recommendation:
     - If action_type == REMOVE: Check section/content removed from rewritten
     - If action_type == UPDATE: Check content updated in rewritten
     - If action_type == ADD: Check new content added to rewritten
     - If action_type == REPLACE: Check replacement done in rewritten
     - If action_type == RESTRUCTURE: Check structure changed appropriately
   - Count applied recommendations (estimate based on string matching)
   - Calculate completeness percentage: `applied / total * 100`
   - If completeness < 95%: Return (False, details_message)
   - Return (True, "All recommendations applied") if completeness >= 95%
2. Add `_check_removal()` helper to verify content removed
3. Add `_check_update()` helper to verify content updated
4. Update `rewrite_document()` to call `validate_rewrite_completeness()` and populate `validation_passed` and `validation_details` in RewriteResult

**Files**:
- `src/agents/rewriter_agent.py` (append to existing file from T023, T024)

**Validation**:
- [ ] Checks each recommendation type appropriately
- [ ] Returns (True, message) for >=95% completeness
- [ ] Returns (False, details) for <95% completeness
- [ ] Helper methods verify specific action types

**Notes**:
- Validation is heuristic (string matching) - not perfect but good enough
- For REMOVE: check that target content NOT in rewritten
- For UPDATE: check that new content IS in rewritten
- For ADD: check that new content IS in rewritten (wasn't in original)
- For REPLACE: check old content NOT in rewritten, new content IS in rewritten
- For RESTRUCTURE: check that overall structure changed (harder to verify, may skip)

---

### Subtask T027 – Rewriter agent unit tests

**Purpose**: Test rewriter agent functionality for correctness.

**Steps**:
1. Create `tests/agents/test_rewriter_agent.py` (new file)
2. Create test fixtures: sample conclusion.md with recommendations, sample document
3. Test `extract_recommendations()`:
   - `test_extract_recommendations_parses_json()` - JSON parsing works
   - `test_extract_recommendations_handles_empty()` - Empty conclusion handled
   - `test_extract_recommendations_fallback()` - Fallback to full text
4. Test `validate_rewrite_completeness()`:
   - `test_validate_all_applied()` - 100% completeness passes
   - `test_validate_partial_applied()` - <95% completeness fails
   - `test_validate_handles_empty_recs()` - Empty recommendations passes
5. Test `rewrite_document()` (integration-style with mocked LLM):
   - `test_rewrite_creates_output()` - Output file created
   - `test_rewrite_saves_metadata()` - Metadata JSON saved
   - `test_rewrite_returns_result()` - RewriteResult populated

**Files**:
- `tests/agents/test_rewriter_agent.py` (new, ~150 lines)

**Commands**:
```bash
pytest tests/agents/test_rewriter_agent.py -v
```

**Mocking**:
- Use `unittest.mock.patch` to mock LLM calls
- Provide predefined responses for testing
- Or use fixtures with real small documents for integration-style tests

---

## Test Strategy

Rewriter agent tests should verify:
- Recommendation extraction from conclusion.md
- Document rewriting with LLM integration
- Completeness validation logic
- Error handling for various failure modes
- Metadata tracking and result reporting

---

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| LLM doesn't apply all recommendations | Validation step with retry logic |
| Large documents exceed context window | Document limitation, add size check |
| JSON parsing fails for recommendations | Fallback to full conclusion text |
| Validation heuristics inaccurate | Accept as best-effort, document limitations |

---

## Review Guidance

**Key acceptance checkpoints**:
- [ ] `BaseAgent` provides LLM integration via BaseComponent inheritance
- [ ] `extract_recommendations()` parses conclusion.md with LLM
- [ ] `rewrite_document()` calls LLM with comprehensive prompt
- [ ] `validate_rewrite_completeness()` checks recommendation application
- [ ] Prompts in `rewriter_prompts.md` are clear and comprehensive
- [ ] Unit tests pass with mocked or real LLM calls

**Context for reviewers**:
- Verify that the agent uses the same LLM configuration as debate participants
- Check that prompts emphasize aggressive application and independence
- Confirm that validation uses 95% threshold (as specified)
- Ensure error handling preserves debate results even on rewrite failure

---

## Activity Log

- 2026-02-17T21:00:00Z – system – lane=planned – Prompt created.
