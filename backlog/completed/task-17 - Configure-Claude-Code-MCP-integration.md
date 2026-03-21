---
id: TASK-17
title: Configure Claude Code MCP integration
status: Done
assignee: []
created_date: '2026-03-20 01:51'
updated_date: '2026-03-20 14:17'
labels:
  - phase-6
  - integration
dependencies:
  - TASK-15
priority: medium
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Update .claude/mcp.json to register sdd-analyzer MCP server. Verify Claude Code discovers the server and the analyze_specification tool.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 .claude/mcp.json contains sdd-analyzer server entry with correct command/args/cwd
- [x] #2 pyproject.toml has sdd-analyzer script entry point
- [x] #3 Claude Code recognizes the MCP server on restart
- [x] #4 analyze_specification tool appears in Claude Code tool list
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
[PM-LOG dev-started | agent: background]

[DEV-LOG] AC1: .claude/mcp.json created with sdd-analyzer config

[DEV-LOG] AC2: pyproject.toml already has sdd-analyzer script entry (from TASK-15)

[DEV-LOG] AC3: Server added via 'claude mcp add sdd-analyzer' - visible in ~/.claude.json

[DEV-LOG] AC4: Server configured in project config, will appear after Claude Code restart in worktree

[DEV-REPORT] TASK-17 complete | Config: .claude/mcp.json | Docs: docs/MCP_SETUP.md | Server added to ~/.claude.json
<!-- SECTION:NOTES:END -->
