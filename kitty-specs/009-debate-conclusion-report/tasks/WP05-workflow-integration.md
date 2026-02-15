---
work_package_id: "WP05"
subtasks: ["T035", "T036", "T037", "T038", "T039", "T040", "T041"]
title: "Workflow Integration"
phase: "Phase 2 - Integration"
lane: "planned"
dependencies: ["WP04"]
history:
  - timestamp: "2026-02-15T09:39:49Z"
    lane: "planned"
    agent: "system"
    action: "Prompt generated"
---

# WP05: Workflow Integration

Integrate conclusion node into both debate workflows (standard and document).

## Subtasks

### T035-T037: Standard Workflow
- Modify `src/workflow/debate_workflow.py`
- Import ConclusionReportNode
- Add node to graph after judge_node
- Add edges: judge → conclusion → END

### T038-T040: Document Workflow
- Modify `src/workflow/document_debate_workflow.py`
- Import ConclusionReportNode
- Add node to graph after judge_node
- Add edges: judge → conclusion → END

### T041: Integration Tests
- Write integration tests for both workflows
- Verify Conclusion.md is generated in correct location

## Implementation Notes

- Add node after judge verdict per WF-001, WF-002
- Pass output directory through state
- Ensure workflow completes without errors
- Test with actual debate runs
