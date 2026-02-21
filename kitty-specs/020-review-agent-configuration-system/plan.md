# Implementation Plan: Review Agent Configuration System

**Branch**: `020-review-agent-configuration-system` | **Date**: 2025-02-21 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/kitty-specs/020-review-agent-configuration-system/spec.md`

## Summary

Добавить гибкую систему конфигурации для review агента в секцию `rewrite` файла `config/debate_config.yaml`. Система позволит настраивать:
- Кастомные промпты (system/user) с плейсхолдерами
- Шаблоны результатов с подстановкой
- Параметры LLM (модель, провайдер, temperature, top_p, max_tokens)
- Профили ревью (strict/balanced/lenient) с иерархическим мерджем
- Выборочные проверки (security, performance, style)
- Retry политику, таймауты, логирование
- Формат вывода и контекстные настройки

**Технический подход**: Расширение существующей конфигурации YAML, добавление новых value objects для review настроек, интеграция с текущей системой загрузки конфига.

## Technical Context

**Language/Version**: Python 3.12+
**Primary Dependencies**: PyYAML (существует в проекте), pytest (для тестов)
**Storage**: YAML конфигурационные файлы (config/debate_config.yaml)
**Testing**: pytest
**Target Platform**: CLI приложение, кроссплатформенность (Linux, macOS, Windows)
**Project Type**: Single CLI project с clean architecture (adapters, application, domain, infrastructure)
**Performance Goals**: Не критично для прототипа
**Constraints**: pip installable, минимальные внешние зависимости
**Scale/Scope**: Расширение существующего кода rewrite модуля

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Based on Deb8flow Constitution:

| Requirement | Status | Notes |
|------------|--------|-------|
| Python 3.12+ | ✅ PASS | Проект уже использует Python 3.12+ |
| pytest required | ✅ PASS | Будут добавлены тесты для новых value objects |
| pip installable | ✅ PASS | Изменения в рамках существующей структуры |
| Documentation | ⚠️ TODO | Будет создан docs/review-agent-config.md |
| Spec-driven | ✅ PASS | Спецификация существует (spec.md) |
| Self-documenting code | ✅ PASS | Code будет понятным без излишних комментариев |

**GATE STATUS**: ✅ PASS - Нет критических нарушений конституции. Документация будет добавлена в Phase 1.

## Project Structure

### Documentation (this feature)

```
kitty-specs/020-review-agent-configuration-system/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (not applicable - no API)
└── tasks.md             # Phase 2 output (/spec-kitty.tasks command)
```

### Source Code (repository root)

```
src/
├── rewrite/
│   ├── domain/
│   │   ├── value_objects.py     # Existing: RewriteConfig
│   │   └── review_config.py     # NEW: ReviewConfig, ProfileConfig, etc.
│   ├── infrastructure/
│   │   ├── storage.py           # Existing: file storage
│   │   └── config_loader.py     # NEW: YAML config loading with merge
│   └── cli/
│       └── review.py            # NEW: Review CLI command (future feature)

config/
└── debate_config.yaml           # MODIFY: Add review section

docs/
└── review-agent-config.md       # NEW: Feature documentation

tests/
├── unit/
│   └── rewrite/
│       └── test_review_config.py  # NEW: Unit tests for review config
└── integration/
    └── test_review_config_workflow.py  # NEW: Integration tests
```

**Structure Decision**: Single project structure (существующая). Новые value objects добавляются в `src/rewrite/domain/`, инфраструктура загрузки конфига в `src/rewrite/infrastructure/`. Clean architecture сохраняется.

## Phase 0: Research

### Outstanding Clarifications

Нет необходимости в дополнительном research - все требования четко определены в спецификации. Используется существующий паттерн `RewriteConfig.from_dict()` для загрузки YAML конфигурации.

### Technical Decisions

| Decision | Rationale |
|----------|-----------|
| YAML формат | Уже используется в проекте (debate_config.yaml) |
| Расширение секции `rewrite` | Сохраняет единый точку конфигурации для rewrite функциональности |
| Value objects (dataclass) | Соответствует существующему паттерну (RewriteConfig) |
| from_dict() паттерн | Соответствует существующей архитектуре загрузки конфига |
| Профили как nested dict | Простая реализация иерархического мерджа |

## Phase 1: Design

### Data Model

Будет создан в `data-model.md`:

**Сущности**:
- `ReviewConfig`: Основная конфигурация review агента
- `ProfileConfig`: Конфигурация профилей (strict/balanced/lenient)
- `PromptConfig`: Конфигурация промптов (system/user/template)
- `LLMConfig`: Параметры LLM (model, provider, temperature, etc.)
- `RetryConfig`: Retry политика
- `OutputConfig`: Настройки форматирования вывода
- `CheckConfig`: Включённые проверки (security, performance, style)

**Отношения**:
- `ReviewConfig` содержит `ProfileConfig`, `PromptConfig`, `LLMConfig`, `RetryConfig`, `OutputConfig`, `CheckConfig`
- `ProfileConfig` переопределяет части базовой конфигурации

### Configuration Schema

Пример структуры YAML (расширение секции `rewrite`):

```yaml
rewrite:
  # Existing settings...
  max_rounds: 5
  batch_size: 5
  backup_suffix: ".backup"

  # NEW: Review agent configuration
  review:
    # Profile selection (strict/balanced/lenient)
    profile: "balanced"

    # LLM settings
    llm:
      provider: "${DEBATE_PROVIDER:openai}"
      model: "${DEBATE_MODEL:gpt-4o-mini}"
      temperature: ${DEBATE_TEMPERATURE:0.7}
      top_p: 0.9
      max_tokens_request: 4000
      max_tokens_response: 2000
      timeout: 120

    # Custom prompts
    prompts:
      system: "src/prompts/review/system_prompt.md"
      user: "src/prompts/review/user_prompt.md"
      result_template: "src/prompts/review/result_template.md"

    # Prompt variables for substitution
    prompt_variables:
      project_name: "Deb8flow"
      team_context: "Backend development team"

    # Retry policy
    retry:
      max_retries: 3
      backoff: "exponential"  # or "linear", "constant"
      initial_delay: 1.0

    # Checks to perform
    checks:
      security: true
      performance: true
      style: true

    # Output format
    output:
      format: "markdown"  # or "json"
      include_snippets: true
      max_comment_length: 500

    # Context settings
    context:
      window_size: 8000
      include_patterns: ["src/**/*.py"]
      exclude_patterns: ["**/test_*.py", "**/__pycache__/**"]

    # Logging
    logging:
      level: "INFO"  # ERROR, WARN, INFO, DEBUG
      debug: false

    # Profiles presets
    profiles:
      strict:
        llm:
          temperature: 0.1
          top_p: 0.5
        checks:
          security: true
          performance: true
          style: true
        output:
          format: "json"

      balanced:
        llm:
          temperature: 0.5
          top_p: 0.8
        checks:
          security: true
          performance: true
          style: false
        output:
          format: "markdown"

      lenient:
        llm:
          temperature: 0.9
          top_p: 0.95
        checks:
          security: false
          performance: false
          style: true
        output:
          format: "markdown"
```

### Implementation Classes

**New files to create**:

1. `src/rewrite/domain/review_config.py`:
   - `ReviewConfig` dataclass
   - `ProfileConfig` dataclass
   - `PromptConfig` dataclass
   - `LLMConfig` dataclass
   - `RetryConfig` dataclass
   - `OutputConfig` dataclass
   - `CheckConfig` dataclass
   - Метод `from_dict()` для загрузки из YAML
   - Метод `merge_with_profile()` для иерархического мерджа
   - Метод `merge_with_cli()` для применения CLI флагов

2. `src/rewrite/infrastructure/config_loader.py`:
   - Функция `load_config(path: Path) -> Dict[str, Any]`
   - Функция `merge_configs(base: Dict, profile: Dict, cli: Dict) -> Dict`
   - Валидация конфигурации

3. `tests/unit/rewrite/test_review_config.py`:
   - Тесты загрузки конфигурации
   - Тесты мерджа профилей
   - Тесты мерджа CLI флагов
   - Тесты валидации

4. `docs/review-agent-config.md`:
   - Документация новой функциональности
   - Примеры конфигурации
   - Описание профилей и мерджа

## Complexity Tracking

Нет нарушений конституции, требующих оправдания. Реализация следует существующим паттернам проекта.

---

**Status**: Phase 1 complete. Ready for `/spec-kitty.tasks` to generate work packages.
