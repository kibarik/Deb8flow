---
work_package_id: "WP02"
subtasks: ["T008", "T009", "T010", "T011", "T012", "T013", "T014", "T015", "T016"]
title: "Committee Report Parser"
phase: "Phase 1 - Data Extraction"
lane: "planned"
dependencies: ["WP01"]
history:
  - timestamp: "2026-02-15T09:39:49Z"
    lane: "planned"
    agent: "system"
    action: "Prompt generated"
---

# WP02: Committee Report Parser

Parse final_report.md files from committee debates into structured ConclusionData.

## Subtasks

### T008: Create parser module
Create `src/parsers/final_report_parser.py` with `FinalReportParser` class.

### T009: Section extraction
Use regex `## (.+)` to extract sections. Handle missing sections gracefully.

### T010: Parse question and summary
Extract Committee Question and Executive Summary sections.

### T011: Parse room results
Parse Room-by-Room Analysis with TPM_vs_{ROLE} format.

### T012: Extract verdicts
Extract winner, justification, key takeaways from each room.

### T013: Parse TPM reflection
Extract insights, assessment, recommendations from TPM Reflection section.

### T014: Parse metadata
Extract run_id, timestamps from Metadata section.

### T015: Error handling
Add try/except blocks for missing/malformed sections.

### T016: Unit tests
Test with sample final_report.md from research.md.

## Implementation Notes

- Return data matching ConclusionData contract from WP01
- Preserve original language (no translation)
- Handle edge cases: failed rooms, missing sections
- Follow defensive parsing with multiple regex patterns

## Dependencies

WP01 (type definitions)
