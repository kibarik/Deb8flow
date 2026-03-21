---
id: TASK-6
title: '[IMPL] Создать SDD prompts'
status: To Do
assignee: []
created_date: '2026-03-19 20:53'
updated_date: '2026-03-20 01:49'
labels: []
dependencies: []
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Создать директорию `src/prompts/sdd/` с промптами для анализа SDD спецификаций.

**Требуемые файлы:**
1. `src/prompts/sdd/system.md` - системный промпт анализатора
2. `src/prompts/sdd/architect.md` - роль архитектора (проверка структуры)
3. `src/prompts/sdd/reviewer.md` - роль ревьюера (проверка качества)

**Содержимое промптов (базовая структура):**
- system.md: инструкции по анализу SDD спецификаций
- architect.md: фокус на архитектурных аспектах
- reviewer.md: фокус на полноте и ясности

**Шаги:**
1. Создать директорию `src/prompts/sdd/`
2. Создать три файла с промптами
3. Адаптировать существующие промпты из `src/prompts/roles/`

**Критерий завершённости:**
- PASS: все 3 файла существуют и содержат >100 символов
- FAIL: хотя бы один файл отсутствует или пуст

**Сценарий демонстрации:**
1. Выполнить `ls -la src/prompts/sdd/`
2. Увидеть 3 файла: system.md, architect.md, reviewer.md
3. Проверить содержимое через `cat src/prompts/sdd/system.md`

**Зависимости:** TASK-5 (структура конфига должна быть определена)

[SCRUM-NOTE: добавлены конкретные файлы, критерии PASS/FAIL, сценарий демонстрации, зависимости]
<!-- SECTION:DESCRIPTION:END -->
