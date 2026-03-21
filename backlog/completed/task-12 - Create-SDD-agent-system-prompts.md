---
id: TASK-12
title: Create SDD agent system prompts
status: Done
assignee: []
created_date: '2026-03-20 01:50'
updated_date: '2026-03-20 08:33'
labels:
  - phase-3
  - prompts
dependencies: []
priority: medium
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Create 4 SDD agent system prompts in src/prompts/sdd/: architect.md (PRO), devlead.md (CON), qa.md (CON), security.md (CON). Each prompt defines the agent role, perspective, and debate behavior for analyzing SDD specifications.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 src/prompts/sdd/architect.md exists — PRO role evaluating architecture, patterns, scalability
- [x] #2 src/prompts/sdd/devlead.md exists — CON role challenging feasibility, complexity, maintainability
- [x] #3 src/prompts/sdd/qa.md exists — CON role identifying testability gaps, quality risks
- [x] #4 src/prompts/sdd/security.md exists — CON role flagging vulnerabilities, auth gaps, data exposure
- [x] #5 All prompts follow consistent structure matching existing src/prompts/ conventions
- [x] #6 Prompts reference SDD-specific concerns (not PRD/business requirements)
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
[DEV-LOG started | timestamp: 2026-03-20T01:50]

[DEV-LOG files_created | architect.md, devlead.md, qa.md, security.md]

[DEV-REPORT] All 4 SDD prompts created in src/prompts/sdd/ following existing conventions

[REVIEW-REPORT] Code review completed. VERDICT: APPROVE. All 4 files exist, structure matches convention, PRO/CON distribution correct (1+3), SDD-specific content verified, all 6 AC PASS. Ready for QA.
<!-- SECTION:NOTES:END -->
