---
id: TASK-9
title: Add FastMCP dependency and create MCP package structure
status: Done
assignee: []
created_date: '2026-03-20 01:49'
updated_date: '2026-03-20 07:45'
labels:
  - phase-1
  - foundation
dependencies: []
priority: high
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Install FastMCP SDK, create src/mcp/ package structure, add sdd-analyzer script entry point to pyproject.toml. This is the foundation for all subsequent MCP work.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 fastmcp is added to pyproject.toml dependencies
- [x] #2 poetry lock && poetry install succeeds without errors
- [x] #3 src/mcp/__init__.py exists and is importable
- [x] #4 src/mcp/tools/__init__.py exists and is importable
- [x] #5 sdd-analyzer script entry point added to pyproject.toml
- [x] #6 python -c 'import fastmcp' succeeds
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
[DEV-LOG started | checkpoint: dev-start-TASK-9]

[DEV-LOG research-doc: doc-3]

[DEV-LOG branch: task-9-fastmcp | worktree: /Users/aleksishmanov/.superset/worktrees/dev8flow-stable/task-9-fastmcp]

[DEV-LOG plan-ready | подзадач: 5 | checkpoint: dev-plan-TASK-9]

[DEV-LOG verified | continue-checks: skipped | тесты: no tests in project]

[DEV-DIFF]
diff --git a/pyproject.toml b/pyproject.toml
index 0171270..dce1e83 100644
--- a/pyproject.toml
+++ b/pyproject.toml
@@ -23,6 +23,7 @@ rich = "^14.0.0"
 typing-extensions = "^4.0.0"
 dotenv = "^0.9.9"
 docker = "^7.0.0"
+fastmcp = "^2.0.0"
 
 [tool.poetry.group.dev.dependencies]
 pytest = "^8.3.5"
@@ -31,6 +32,7 @@ pytest = "^8.3.5"
 product-committee = "product_committee:main"
 conclusion-results = "conclusion_results:main"
 rewrite = "scripts.rewrite:main"
+sdd-analyzer = "src.mcp.server:main"

diff --git a/src/mcp/__init__.py b/src/mcp/__init__.py
new file mode 100644
--- /dev/null
+++ b/src/mcp/__init__.py
@@ -0,0 +1,8 @@
+"""
+MCP (Model Context Protocol) package for deb8flow.
+
+This package provides MCP server implementation for integrating
+with Claude and other LLM clients.
+"""
+
+__version__ = "0.1.0"

diff --git a/src/mcp/server.py b/src/mcp/server.py
new file mode 100644
--- /dev/null
+++ b/src/mcp/server.py
@@ -0,0 +1,20 @@
+"""
+MCP Server for deb8flow SDD Analyzer.
+
+This module provides the main entry point for the MCP server
+that exposes debate analysis tools to LLM clients.
+"""
+
+from fastmcp import FastMCP
+
+# Create MCP server instance
+mcp = FastMCP(name="SDD Analyzer")
+
+
+def main():
+    """Entry point for sdd-analyzer script."""
+    mcp.run()
+
+
+if __name__ == "__main__":
+    main()

diff --git a/src/mcp/tools/__init__.py b/src/mcp/tools/__init__.py
new file mode 100644
--- /dev/null
+++ b/src/mcp/tools/__init__.py
@@ -0,0 +1,6 @@
+"""
+MCP Tools package for deb8flow.
+
+This package contains MCP tools for debate analysis,
+document processing, and other utilities.
+"""

[DEV-REVIEW-CONTEXT]
Chto realizovano: Dobavlena zavisimost fastmcp ^2.0.0, sozdana struktura paketa src/mcp/ s podpaketaom tools/, dobavlen entry point sdd-analyzer
Klyuchevye resheniya:
- [DEV-DECISION] Ispolzovat prefecthq/fastmcp - oficialny paket s vysokim benchmark score
- [DEV-DECISION] Sozdat src/mcp/ s tools/ podpaketaom - sleduet sushchestvuyushchey Clean Architecture
- [DEV-DECISION] Entry point sdd-analyzer -> src.mcp.server:main - standartny Poetry scripts pattern
Gde smotret v pervuyu ochered: pyproject.toml (dependencies, scripts), src/mcp/server.py (server instance)
Testovoe pokrytie: net testov v projekte, import proveren vruchnuyu

[DEV-REPORT]
Epik: TASK-9
Status: CODE-REVIEW

Vetka: task-9-fastmcp
Worktree: /Users/aleksishmanov/.superset/worktrees/dev8flow-stable/task-9-fastmcp
Bazovaya vetka: main

Izmeneny faily:
 pyproject.toml | 2 ++
 src/mcp/__init__.py | 8 ++++++++
 src/mcp/server.py | 20 ++++++++++++++++++++
 src/mcp/tools/__init__.py | 6 ++++++
 4 files changed, 36 insertions(+)

Podzadachi: TASK-20, TASK-21, TASK-22, TASK-23, TASK-24 -- vse done
Dokument issledovaniya: doc-3
Testy: net testov v projekte
Kriterii PASS: vse 6 vypolneny

Gotovo k Code Review.
 cd /Users/aleksishmanov/.superset/worktrees/dev8flow-stable/task-9-fastmcp && git diff origin/main --stat

[REVIEW-REPORT]
Вердикт: ОДОБРИТЬ
Итерация: #1

Review задача: TASK-25
Связанные задачи: TASK-20, TASK-21, TASK-22, TASK-23, TASK-24
Статус задач: ready-for-testing

Все 6 acceptance criteria выполнены.
Код корректный, минимальный, без over-engineering.
Следующий шаг: QA берёт в работу
<!-- SECTION:NOTES:END -->
