---
id: doc-3
title: 'Исследование: Add FastMCP dependency and create MCP package structure (TASK-9)'
type: other
created_date: '2026-03-20 02:21'
---
# Исследование задачи TASK-9

## Контекст и понимание задачи
Необходимо добавить FastMCP SDK как зависимость в проект и создать базовую структуру пакета src/mcp/ для будущей разработки MCP-сервера. Это фундаментальная задача (phase-1, foundation) для всего последующего MCP-развития.

## Изученные артефакты
- pyproject.toml: текущая конфигурация Poetry, Python 3.12+
- Структура src/: committee/, orchestrator/, rewrite/, shared/ (Clean Architecture)
- Context7 документация FastMCP: /prefecthq/fastmcp

## Ключевые технические решения
1. **[DEV-DECISION] Использовать prefecthq/fastmcp** — официальный пакет с высоким benchmark score (88.28)
2. **[DEV-DECISION] Создать src/mcp/ с tools/ подпакетом** — следует существующей Clean Architecture
3. **[DEV-DECISION] Entry point sdd-analyzer → src/mcp/server.py:main** — стандартный Poetry scripts паттерн

## Выбранный подход
1. Добавить fastmcp в dependencies pyproject.toml
2. Создать src/mcp/__init__.py с базовым экспортом
3. Создать src/mcp/tools/__init__.py (заглушка для будущих tools)
4. Создать src/mcp/server.py с минимальным FastMCP сервером
5. Добавить sdd-analyzer script entry point
6. Выполнить poetry lock && poetry install

## Риски и edge cases
- poetry lock может конфликтовать с существующими зависимостями langchain — проверить совместимость
- fastmcp требует Python 3.10+, проект использует 3.12 — OK
