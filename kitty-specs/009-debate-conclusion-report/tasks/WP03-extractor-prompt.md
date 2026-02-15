---
work_package_id: "WP03"
subtasks: ["T017", "T018", "T019", "T020", "T021", "T022", "T023", "T024", "T025"]
title: "State Extractor and Prompt"
phase: "Phase 1 - Data Extraction"
lane: "done"
dependencies: ["WP01"]
reviewed_by: "ALeks ishmanov"
review_status: "approved"
history:
  - timestamp: "2026-02-15T09:39:49Z"
    lane: "planned"
    agent: "system"
    action: "Prompt generated"
---

# WP03: State Extractor and Prompt

Extract conclusion data from debate state for standard/document debates and create LLM prompt.

## Subtasks

### T017-T022: State Extractor
- Create `src/extractors/debate_state_extractor.py`
- Extract debate question, judge verdict, TPM role
- Extract Q&A pairs (3-10), weaknesses, recommendations
- Handle document context for document-based debates

### T023-T025: LLM Prompt
- Create `src/prompts/conclusion_report_prompt.md`
- Define system prompt with structure requirements
- Add few-shot examples for weaknesses and recommendations
- Include Russian formatting instructions ("От [Role]:")

## Implementation Notes

- Follow DebateState structure from `src/debate_state.py`
- Parse verdict from "WINNER: PRO/CON" message content
- Detect TPM role from `pro_custom_prompt` field
- Filter messages by stage and validation for Q&A extraction

## Activity Log

- 2026-02-15T10:09:21Z – unknown – lane=for_review – Ready for review: Implemented DebateStateExtractor and ConclusionReportPrompt with comprehensive extraction logic for standard/document/committee debates
- 2026-02-15T10:38:01Z – unknown – lane=done – Review passed: DebateStateExtractor extracts conclusion data from all debate types.
