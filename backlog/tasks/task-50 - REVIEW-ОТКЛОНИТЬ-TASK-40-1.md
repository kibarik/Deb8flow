---
id: TASK-50
title: '[REVIEW] ОТКЛОНИТЬ TASK-40 #1'
status: To Do
assignee: []
created_date: '2026-03-21 11:48'
labels: []
dependencies:
  - TASK-40
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Вердикт: ОТКЛОНИТЬ

## Summary
Конфигурационный файл создан и валиден как YAML, но имеет критическую проблему: все пути к SDD-специфичным промптам указывают на несуществующие файлы. Задача требует создания рабочей конфигурации, а не только синтаксически корректной.

## Разбор по уровням

### Соответствие задаче
**КРИТИЧЕСКИЙ ОТКАЗ**: Acceptance criteria #4 требует "Секция prompts: пути к SDD-специфичным промптам в src/prompts/sdd/". В конфиге указаны пути:
- src/prompts/sdd/architect.md
- src/prompts/sdd/devlead.md
- src/prompts/sdd/qa.md
- src/prompts/sdd/security.md

НО этих файлов не существует. Директория src/prompts/sdd/ отсутствует в кодовой базе.

Acceptance criteria #6 требует "Конфиг загружается без ошибок via PyYAML" - это выполнено, но технически YAML может быть валидным даже если пути указывают на несуществующие файлы. Конфигuration загружается, но не работает.

### Качество тестов
**НЕТ ТЕСТОВ**: В Changes нет тестовых файлов. DEV утверждает "Все тесты: пройдены (YAML валидация + проверка структуры)", но:
- Нет тестового файла который бы проверял что промпт-файлы существуют
- Нет теста который бы проверял что конфиг работает реальным образом
- Bash команда проверки (python3 -c "import yaml...") проверяет только YAML syntax

Это нарушение критерия качества: нет verification что конфиг actually functional.

### Корректность логики
Логика конфига корректна в части структуры (все секции на месте), но paths pointing to nonexistent files делают конфиг unusable for actual SDD debates.

### Бесполезная логика
Секция rewrite в sdd_config.yaml полностью скопирована из debate_config.yaml и содержит:
- Review agent configuration (profiles: strict/balanced/lenient)
- Retry policy, checks configuration, context settings

Это избыточно для задачи которая требует только "SDD-специфичную конфигурацию для дебатов". Rewrite секция не используется в SDD debate процессе и добавлена без необходимости.

## Что именно нужно исправить

1. **Создать SDD prompt files** (критично):
   - Создать src/prompts/sdd/architect.md
   - Создать src/prompts/sdd/devlead.md  
   - Создать src/prompts/sdd/qa.md
   - Создать src/prompts/sdd/security.md
   - ЛИБО обновить конфиг с указанием на существующие файлы

2. **Добавить verification test** (критично):
   - Создать тест который проверяет existence всех prompt files указанных в конфиге
   - Тест должен fail если файл не существует
   - Файл: tests/test_sdd_config.py или аналогичный

3. **Удалить избыточную rewrite секцию** (серьезно):
   - Убрать секцию rewrite из sdd_config.yaml
   - Она не требуется для SDD debate functionality
   - Это duplicate кода из debate_config.yaml

## Самопроверка Continue.dev
skipped: not installed - DEV не прошел автоматическую самопроверку. Это означает что механические ошибки (если есть) не были отловлены.

## Что хорошо
- YAML синтаксис валиден
- Структура конфига следует pattern из debate_config.yaml (consistency)
- Секции llm, agents, debate, output, logging все присутствуют и правильно оформлены
- Environment variable substitution syntax корректный (${VAR:default})
- Agent names (Architect PRO vs DevLead/QA/Security CON) соответствуют SDD контексту
<!-- SECTION:DESCRIPTION:END -->
