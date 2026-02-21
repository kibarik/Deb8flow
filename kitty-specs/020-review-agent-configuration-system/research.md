# Research: Review Agent Configuration System

**Feature**: 020-review-agent-configuration-system
**Date**: 2025-02-21

## Research Scope

Исследовать паттерны конфигурации для YAML-based систем в Python, особенно для LLM приложений.

## Findings

### 1. YAML Configuration Patterns

**Изученные проекты**:
- LangChain: Использует Pydantic для валидации конфигурации
- OpenAI SDK: Простые dataclass конфигурации
-_existing project pattern_: `RewriteConfig.from_dict()`

**Вывод**: Используем существующий паттерн dataclass + `from_dict()` для консистентности с проектом.

### 2. Hierarchical Configuration Merge

**Паттерны мерджа**:
- **Deep merge**: Рекурсивный мердж по всем ключам
- **Shallow merge**: Только верхний уровень
- **Key-based override**: Только явно указанные ключи

**Решение**: Key-based override (выбрано пользователем):
- Профили переопределяют только указанные поля
- Непереопределённые поля наследуются от базовой конфигурации
- CLI флаги имеют наивысший приоритет

### 3. Configuration Validation

**Подходы**:
1. **Pydantic**: Мощная валидация, но добавляет зависимость
2. **dataclass + __post_init__**: Лёгкая валидация (выбрано)
3. **Manual validation**: Громоздко

**Решение**: `dataclass` с `__post_init__` для валидации — соответствует существующему `RewriteConfig`.

### 4. Placeholder Substitution

**Изученные решения**:
- Python `str.format()`: Простой, но небезопасный для пользовательского ввода
- `string.Template`: Безопаснее, но менее гибкий
- Jinja2: Мощный, но избыточный

**Решение**: `str.format()` с контролируемыми переменными — достаточно для текущих нужд.

### 5. Profile Management

**Паттерны**:
- **External files**: Профили в отдельных YAML файлах
- **Embedded dict**: Профили внутри основного конфига (выбрано)

**Решение**: Embedded в `rewrite.review.profiles.{profile_name}` — проще в использовании и поддержке.

## Technical Decisions

| Decision | Alternative | Rationale |
|----------|-------------|-----------|
| dataclass (not Pydantic) | Pydantic, attrs | Соответствие существующему коду, минимальные зависимости |
| from_dict() pattern | __init__, kwargs | Соответствие RewriteConfig паттерну |
| Embedded profiles | Separate files | Проще для пользователя, всё в одном файле |
| Key-based merge | Deep merge, full override | Предсказуемое поведение, гибкость |
| str.format() | Jinja2, Template | Достаточно для текущих нужд |

## Dependencies

**Нет новых внешних зависимостей**:
- `PyYAML`: Уже используется в проекте
- `dataclasses`: Встроенный в Python 3.7+
- `pathlib`: Встроенный в Python 3.4+

## Best Practices Applied

1. **Immutable configuration**: frozen dataclass prevents accidental modification
2. **Validation at construction**: Errors caught early
3. **Type hints**: Full type coverage for IDE support
4. **Defaults for all values**: Config always valid even with minimal input
5. **Clear error messages**: Validation errors explain what's wrong and how to fix

## Lessons Learned

1. **Keep it simple**: Не нужно Pydantic для конфигурации
2. **Follow existing patterns**: RewriteConfig показал хороший подход
3. **User experience first**: Профили должны быть простыми в использовании
4. **Validation matters**: Ошибки конфигурации должны быть понятными

## References

- Existing code: `src/rewrite/domain/value_objects.py` (RewriteConfig)
- Existing config: `config/debate_config.yaml`
- Project constitution: `.kittify/memory/constitution.md`

## Conclusion

Нет необходимости в дополнительном research. Используем существующие паттерны проекта. Все требования могут быть реализованы с помощью dataclass value objects и YAML конфигурации.
