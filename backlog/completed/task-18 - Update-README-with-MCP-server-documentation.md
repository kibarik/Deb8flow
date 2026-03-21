---
id: TASK-18
title: Update README with MCP server documentation
status: Done
assignee: []
created_date: '2026-03-20 01:52'
updated_date: '2026-03-20 14:27'
labels:
  - phase-7
  - docs
dependencies:
  - TASK-17
priority: low
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Add MCP server setup instructions, Claude Code configuration, example usage, and troubleshooting to README.md.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 README includes MCP server setup instructions (install, configure, run)
- [x] #2 README includes Claude Code configuration section
- [x] #3 README includes example tool invocation and expected output
- [x] #4 README includes troubleshooting for common issues
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
[DEV-REPORT] TASK-18 | Status: Done | README.md updated with comprehensive MCP server documentation

- Added MCP Server section with installation instructions

- Added MCP configuration examples (project-level and user-level)

- Added Usage section with Poetry and Python module examples

- Added MCP Tools reference for analyze_specification tool

- Added Configuration guide with parameters, returns, and examples

- Updated Dependencies section to include fastmcp and python-docx

- Added Project Structure section documenting complete architecture

[DEV-VERIFICATION] Task already complete. README.md contains comprehensive MCP server documentation:
- Lines 340-342: MCP server description
- Lines 345-351: Installation instructions
- Lines 354-386: Configuration examples (project-level and user-level)
- Lines 388-476: Usage examples and tool API reference
- Lines 508-518: System requirements (Python 3.12+, fastmcp, etc.)
Documentation matches actual implementation in src/mcp/server.py and src/mcp/tools/analyze_specification.py
<!-- SECTION:NOTES:END -->
