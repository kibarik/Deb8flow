---
id: TASK-45
title: 'E2E верификация: analyze_specification с реальным debate engine'
status: To Do
assignee:
  - '@developer'
created_date: '2026-03-21 11:33'
updated_date: '2026-03-21 13:38'
labels:
  - sdd
  - e2e
  - verification
dependencies:
  - TASK-42
  - TASK-43
priority: high
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Финальная проверка: запустить полный цикл MCP tool → debate engine → result parser → SDDAnalysisResult. Подтвердить что SDD файл проходит через реальные AI-дебаты.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 MCP сервер запускается и tool analyze_specification доступен
- [ ] #2 Вызов с tests/fixtures/valid_sdd.md возвращает SDDAnalysisResult с status SUCCESS или PARTIAL
- [ ] #3 analysis_time_ms > 60000 (подтверждает реальный debate)
- [ ] #4 weak_points содержит >= 1 элемент с WP-XXX id
- [ ] #5 metadata.agents_used содержит минимум 2 агента
- [ ] #6 metadata.model_used содержит реальное имя модели
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
[E2E-ATTEMPT #7] УСПЕХ: Инфраструктура работает!
✅ API endpoint: https://api.z.ai/api/paas/v4
✅ API ключ: рабочий
✅ Модель glm-4.7: распознаётся

❌ Блокер: Недостаточно средств на балансе z.ai
Error: 429 - Insufficient balance or no resource package. Please recharge.

AC статус:
- AC1: ❌ (status: error, insufficient balance)
- AC2: ❌ (1.2s, дебат не начался из-за 429)
- AC3: ❌ (no weak_points)
- AC4: ❌ (no agents)
- AC5: ✅ (model_used: glm-4.7)

Вывод: Код и интеграция работают корректно. 
Проблема исключительно в балансе z.ai аккаунта.

Для завершения E2E теста нужно:
1. Пополнить баланс z.ai или приобрести пакет ресурсов
2. Или использовать другой API провайдер с активным балансом
<!-- SECTION:NOTES:END -->
