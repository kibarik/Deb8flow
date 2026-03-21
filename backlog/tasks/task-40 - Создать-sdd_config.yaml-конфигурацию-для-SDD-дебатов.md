---
id: TASK-40
title: Создать sdd_config.yaml конфигурацию для SDD-дебатов
status: Done
assignee:
  - '@claude'
created_date: '2026-03-21 11:31'
updated_date: '2026-03-21 11:59'
labels:
  - sdd
  - config
  - debate-engine
dependencies: []
references:
  - config/debate_config.yaml
priority: high
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Текущий debate_config.yaml настроен на PRD-анализ (PO vs TPM/CPO/CFO/CTO/BDM). Для анализа SDD спецификаций нужен отдельный конфиг с SDD-специфичными агентами (Architect PRO vs DevLead/QA/Security CON), настройками LLM и путями к промптам. Конфиг должен следовать структуре существующего debate_config.yaml.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Файл config/sdd_config.yaml создан и содержит валидный YAML
- [x] #2 Секция agents: main agent Architect (PRO), opponents: DevLead, QA, Security (CON)
- [x] #3 Секция llm: модель, temperature, timeout, fallback_models — аналогично debate_config.yaml
- [x] #4 Секция prompts: пути к SDD-специфичным промптам в src/prompts/sdd/
- [x] #5 Секция debate: mode standard, language configurable
- [x] #6 Конфиг загружается без ошибок через PyYAML
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
[REVIEW-LOG] Итерация #2: ОДОБРИТЬ (TASK-53)

Все замечания TASK-50 исправлены:
✓ SDD prompt files созданы (architect/devlead/qa/security)
✓ Verification test создан (tests/test_sdd_config.py - 4 tests passed)
✓ Rewrite секция удалена из конфига

Code reviewer: Анализ показал что все критические проблемы устранены.
Git diff: config/sdd_config.yaml + 4 SDD prompt files + test file
Tests: 4/4 passed in 0.04s

Следующий этап: QA тестирование

[QA-LOG verified | timestamp: 2026-03-21T11:59:08Z]

QA VERIFICATION COMPLETE

Evidence:
1. Automated Tests: pytest tests/test_sdd_config.py - 4/4 passed
   - test_sdd_prompt_files_exist ✓
   - test_sdd_prompts_directory_exists ✓
   - test_sdd_config_valid ✓
   - test_rewrite_section_removed ✓

2. Manual AC Verification: 6/6 passed
   - AC #1: YAML syntax valid ✓
   - AC #2: Agents section (Architect PRO, DevLead/QA/Security CON) ✓
   - AC #3: LLM config (model, temp, timeout, fallback_models) ✓
   - AC #4: Prompts paths to src/prompts/sdd/ ✓
   - AC #5: Debate mode standard, language ru ✓
   - AC #6: Config loads via PyYAML ✓

3. Real-world Usage Test: Successful
   - Configuration loads without errors
   - All sections accessible
   - Prompt file paths resolve correctly
   - Environment variable substitution works

4. Prompt Files Validation: 4/4 files exist
   - architect.md (1920 bytes, PRO role)
   - devlead.md (1901 bytes, CON role)
   - qa.md (1895 bytes, CON role)
   - security.md (2083 bytes, CON role)

QA VERDICT: PASS - Ready for production
Worktree: /Users/aleksishmanov/.superset/worktrees/dev8flow-stable/pm/pm-mcp--TASK-40
Branch: pm/mcp-./TASK-40
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Создана и протестирована конфигурация config/sdd_config.yaml для SDD-анализатора спецификаций.

Что создано:
- config/sdd_config.yaml (4399 bytes) - полная конфигурация SDD-дебатов
- src/prompts/sdd/architect.md - PRO агент (защищает архитектуру)
- src/prompts/sdd/devlead.md - CON агент (критикует реализуемость)
- src/prompts/sdd/qa.md - CON агент (критикует тестируемость)
- src/prompts/sdd/security.md - CON агент (критикует безопасность)
- tests/test_sdd_config.py - автоматические тесты (4 test cases)

Конфигурация:
- Agents: Architect (PRO) vs DevLead/QA/Security (CON)
- LLM: gpt-4o-mini, temp 0.8, timeout 120s, 3 fallback models
- Debate: mode standard, language ru
- Prompts: все пути в src/prompts/sdd/
- Output: ./sdd_output с сохранением диалогов и метаданных

QA проверка:
- Автотесты: 4/4 passed (pytest)
- Ручная проверка AC: 6/6 passed
- Real-world usage: успешная загрузка и использование
- Промпт-файлы: 4/4 валидны

QA verdict: PASS - готово к продакшену
<!-- SECTION:FINAL_SUMMARY:END -->
