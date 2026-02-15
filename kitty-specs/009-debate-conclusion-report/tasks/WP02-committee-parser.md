---
work_package_id: WP02
title: Committee Report Parser
lane: "for_review"
dependencies: [WP01]
base_branch: 009-debate-conclusion-report-WP01
base_commit: 95dc3be0916c42092fbdad09b67ace7c4498abf5
created_at: '2026-02-15T10:02:12.434496+00:00'
subtasks: [T008, T009, T010, T011, T012, T013, T014, T015, T016]
phase: Phase 1 - Data Extraction
shell_pid: "94493"
agent: "claude"
history:
- timestamp: '2026-02-15T09:39:49Z'
  lane: planned
  agent: system
  action: Prompt generated
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

## Activity Log

- 2026-02-15T10:02:12Z – claude – shell_pid=94493 – lane=doing – Assigned agent via workflow command
- 2026-02-15T10:06:24Z – claude – shell_pid=94493 – lane=for_review – Ready for review: Implemented FinalReportParser with section extraction, verdict parsing, Q&A summary, TPM analysis, and metadata extraction. Includes error handling and defensive parsing.
