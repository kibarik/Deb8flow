---
work_package_id: "WP04"
subtasks: ["T026", "T027", "T028", "T029", "T030", "T031", "T032", "T033", "T034"]
title: "Conclusion Node and Writer"
phase: "Phase 2 - Implementation"
lane: "planned"
dependencies: ["WP01", "WP02", "WP03"]
history:
  - timestamp: "2026-02-15T09:39:49Z"
    lane: "planned"
    agent: "system"
    action: "Prompt generated"
---

# WP04: Conclusion Node and Writer

Implement LangGraph node that generates conclusion reports and markdown writer utility.

## Subtasks

### T026-T031: Conclusion Node
- Create `src/nodes/conclusion_report_node.py`
- Inherit from BaseComponent, implement __init__ and __call__
- Detect debate type (committee vs standard vs document)
- Route to appropriate extractor (WP02 for committee, WP03 for standard)
- Call LLM with conclusion prompt
- Parse LLM response and validate against ConclusionData
- Add token tracking and retry logic

### T032-T034: Markdown Writer
- Create `src/utils/conclusion_writer.py`
- Implement markdown formatting per spec structure
- Add "Нет рекомендаций" placeholder for agents with no recommendations
- Handle file I/O with directory creation and UTF-8 encoding

## Implementation Notes

- Follow BaseComponent pattern from `src/nodes/base_component.py`
- Use structured output chain for LLM calls
- Handle UTF-8 encoding and create output directory if missing
- Return conclusion data in state for downstream use
