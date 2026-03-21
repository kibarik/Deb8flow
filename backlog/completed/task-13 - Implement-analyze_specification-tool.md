---
id: TASK-13
title: Implement analyze_specification tool
status: Done
assignee: []
created_date: '2026-03-20 01:50'
updated_date: '2026-03-20 13:00'
labels:
  - phase-4
  - core
dependencies:
  - TASK-10
  - TASK-11
  - TASK-12
priority: high
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Core analysis tool in src/mcp/tools/analyze_specification.py. Orchestrates SDD debate: validates input, loads spec content, runs debate with timeout handling, returns structured SDDAnalysisResult. Accepts spec_path (file) or spec_content (raw text).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Accepts spec_path (path to .md file) as input
- [x] #2 Accepts spec_content (raw text/markdown) as alternative input
- [x] #3 Validates exactly one of spec_path/spec_content is provided
- [x] #4 File validation: checks existence, .md extension, size < 100k chars
- [x] #5 Raw text validation: non-empty, size < 100k chars
- [x] #6 Optional parameters: spec_type (default SDD), focus_areas, detail_level (quick/thorough)
- [x] #7 Integrates with debate orchestrator using SDD config and agents
- [x] #8 On 120s timeout returns partial results with status: partial
- [x] #9 All errors returned as structured AnalysisError (no exceptions to client)
- [x] #10 Chunking applied for specs > 8000 tokens
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Изучить зависимости: src/mcp/models.py (TASK-10), config/sdd_config.yaml (TASK-11), src/prompts/sdd/ (TASK-12)
2. Создать src/mcp/tools/analyze_specification.py:
   - Input validation (spec_path vs spec_content)
   - File/text validation (exists, .md, size < 100k chars)
   - Chunking для specs > 8000 tokens
   - Timeout handling (120s, partial results)
   - Error handling (structured AnalysisError)
3. Интеграция с debate_orchestrator:
   - Загрузка SDD config
   - Загрузка agent prompts (architect, devlead, qa, security)
   - Запуск debate с timeout
4. Тестирование:
   - Unit tests для validation
   - Integration tests для chunking
   - Timeout handling tests
5. Git commit + push
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
[DEV-LOG started | timestamp: 2026-03-20]

[DEV-DECISION] Worktree от task-10-models | обоснование: TASK-13 зависит от TASK-10 (модели Pydantic) | альтернативы: ждать merge в main

[DEV-LOG branch: task-13-analyze-tool | worktree: /Users/aleksishmanov/.superset/worktrees/dev8flow-stable/task-13-analyze-tool]

[DEV-DIFF] src/mcp/tools/analyze_specification.py (new file, 295 lines)

[DEV-REPORT] Epik: TASK-13

Status: code-review

Vetka: task-13-analyze-tool

worktree: /Users/aleksishmanov/.superset/worktrees/dev8flow-stable/task-13-analyze-tool

path из notes: {extract worktree path and current worktree}

[DEV-LOG tests fixed] 56/56 tests pass

[DEV-LOG all AC verified]

[REVIEW-REPORT] APPROVED #1 | verdict: all 10 ACs PASS | tests: 56/56 passing | reviewer: TASK-32 | no critical issues | minor: DetailLevel class unused
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
## TASK-13: Implement analyze_specification tool - COMPLETE

### Implementation Summary

Core MCP tool for SDD (Software Design Document) analysis implemented in `/src/mcp/tools/analyze_specification.py` (827 lines).

### Key Features Implemented

1. **Input Validation (AC #1-3)**
   - Accepts `spec_path` (file path to .md/.txt)
   - Accepts `spec_content` (raw text/markdown) as alternative
   - Validates exactly one is provided via `AnalyzeSpecInput` Pydantic model

2. **File Validation (AC #4)**
   - Checks file existence
   - Validates .md or .txt extension
   - Size limit: < 100k characters

3. **Raw Text Validation (AC #5)**
   - Rejects empty/whitespace-only content
   - Size limit: < 100k characters

4. **Optional Parameters (AC #6)**
   - `spec_type`: PRD, SDD, TDD, UNKNOWN (default: SDD)
   - `focus_areas`: Optional list of focus areas
   - `detail_level`: "quick" (2 rounds) or "thorough" (4 rounds)

5. **Debate Orchestrator Integration (AC #7)**
   - Uses `SimpleDebateOrchestrator` for quick mode (2 rounds)
   - Uses `LLMDebateOrchestrator` for thorough mode (4+ rounds)
   - Loads agent prompts from `src/prompts/sdd/` with fallback defaults
   - Loads config from `config/sdd_config.yaml` with fallback defaults

6. **Timeout Handling (AC #8)**
   - 120 second default timeout
   - Returns partial results with `status: partial` on timeout
   - Error marked as `recoverable: true`

7. **Structured Error Handling (AC #9)**
   - All errors returned as `AnalysisError` model
   - No exceptions exposed to client
   - Includes `type`, `message`, `recoverable`, `suggestion` fields

8. **Chunking (AC #10)**
   - Splits specs > 8000 tokens (~32k chars)
   - Header-aware splitting preserves section boundaries
   - Each chunk respects size limit

### Test Coverage

- **56 tests passing** in `tests/test_analyze_specification.py`
- Complete coverage of all 10 acceptance criteria
- Test classes for each AC with multiple test cases

### Files Changed

| File | Change |
|------|--------|
| `src/mcp/tools/analyze_specification.py` | New (827 lines) |
| `src/mcp/tools/__init__.py` | Modified (exports) |
| `tests/test_analyze_specification.py` | New (675 lines) |

### Branch & PR

- **Branch**: `task-13-analyze-tool`
- **Worktree**: `/Users/aleksishmanov/.superset/worktrees/dev8flow-stable/task-13-analyze-tool`
- **PR URL**: https://github.com/kibarik/Deb8flow/pull/new/task-13-analyze-tool
<!-- SECTION:FINAL_SUMMARY:END -->
