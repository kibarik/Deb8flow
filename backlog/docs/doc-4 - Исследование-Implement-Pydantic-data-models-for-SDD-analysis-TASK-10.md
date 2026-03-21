---
id: doc-4
title: 'Исследование: Implement Pydantic data models for SDD analysis (TASK-10)'
type: other
created_date: '2026-03-20 07:51'
---
# Исследование задачи TASK-10

## Контекст

Создание Pydantic моделей для MCP SDD Analyzer - структурированный вывод анализа спецификаций.

## Источник требований

Файл: `kitty-specs/mcp-sdd-analyzer/data-model.md`

## Список сущностей

| Сущность | Описание | Ключевые поля |
|----------|----------|---------------|
| AnalysisStatus | Enum статуса | success, partial, error |
| WeakPoint | Проблема в спеке | id (WP-XXX), category, severity, confidence |
| Recommendation | Рекомендация | id (REC-XXX), action, priority |
| UnclearSection | Неясный раздел | id (UNS-XXX), content_snippet (max 500) |
| AnalysisMetadata | Метаданные анализа | spec_type, spec_path, timestamp (ISO 8601) |
| AnalysisError | Ошибка анализа | type enum, recoverable, suggestion |
| SDDAnalysisResult | Главный результат | aggregates all entities + optional error |

## Решения

1. [DEV-DECISION] Использовать Pydantic v2 BaseModel | обоснование: валидация ID форматов через field_validator, сериализация в JSON по схеме | альтернативы: dataclasses (нет валидации)

2. [DEV-DECISION] Создать отдельный файл src/mcp/models.py | обоснование: все модели в одном месте, легко импортировать | альтернативы: разбить на несколько файлов (over-engineering)

3. [DEV-DECISION] Использовать pattern validator для ID форматов | обоснование: WP-\d{3}, REC-\d{3}, UNS-\d{3} | альтернативы: отдельный тип (сложнее)

4. [DEV-DECISION] confidence validator: Field(ge=0.0, le=1.0) | обоснование: встроенная валидация диапазона | альтернативы: ручной validator

5. [DEV-DECISION] timestamp через datetime с ISO 8601 сериализацией | обоснование: стандартный формат | альтернативы: строка (нет валидации)

## Структура файла

```python
# src/mcp/models.py

from enum import Enum
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, field_validator

# Enums
class AnalysisStatus(str, Enum): ...
class WeakPointCategory(str, Enum): ...
class Severity(str, Enum): ...
class ActionType(str, Enum): ...
class Priority(str, Enum): ...
class SpecType(str, Enum): ...
class ErrorType(str, Enum): ...

# Models
class WeakPoint(BaseModel): ...
class Recommendation(BaseModel): ...
class UnclearSection(BaseModel): ...
class AnalysisMetadata(BaseModel): ...
class AnalysisError(BaseModel): ...
class SDDAnalysisResult(BaseModel): ...
```

## Зависимости

- TASK-9: FastMCP dependency and MCP package structure (DONE)
- pydantic: уже есть в проекте
