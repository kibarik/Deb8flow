---
id: TASK-5
title: '[IMPL] Создать SDD config'
status: To Do
assignee: []
created_date: '2026-03-19 20:53'
labels: []
dependencies: []
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Создать `config/sdd_config.yaml` - конфигурацию для анализа SDD спецификаций.

**Структура конфига (адаптация debate_config.yaml):**
```yaml
# SDD Analysis Configuration
llm:
  model: "${DEBATE_MODEL:gpt-4o-mini}"
  temperature: 0.7

analysis:
  mode: "sdd"  # спецификация дизайна
  language: "ru"

prompts:
  system: "src/prompts/sdd/system.md"
  roles:
    architect: "src/prompts/sdd/architect.md"
    reviewer: "src/prompts/sdd/reviewer.md"

output:
  format: "markdown"
```

**Шаги:**
1. Изучить существующий `config/debate_config.yaml`
2. Создать `config/sdd_config.yaml` на его основе
3. Адаптировать секции под SDD-анализ

**Критерий завершённости:**
- PASS: файл существует, YAML валиден, содержит секции llm/prompts/output
- FAIL: файл не существует или YAML невалиден

**Сценарий демонстрации:**
1. Выполнить `cat config/sdd_config.yaml`
2. Увидеть структурированный YAML с настройками анализа

[SCRUM-NOTE: добавлена структура конфига, критерии PASS/FAIL, сценарий демонстрации]
<!-- SECTION:DESCRIPTION:END -->
