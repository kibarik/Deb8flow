# Feature Specification: Review Agent Configuration System

**Feature Branch**: `020-review-agent-configuration-system`
**Created**: 2025-02-21
**Status**: Draft
**Input**: User description: "хочу кратно повысить качество работы review агента. Давай добавим в config.yaml параметры для его настройки. Хочу чтобы можно было задавать кастомный prompt-инструкцию и шаблон результата. Чтобы получать качественный результат от доработок."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Custom Prompts and Result Templates (Priority: P1)

Пользователь может определить собственные system и user промпты для review агента, а также задать шаблон результата с плейсхолдерами для структурированного вывода.

**Why this priority**: Это базовая возможность, которая直接影响 качество ревью. Без неё невозможно адаптировать агента под специфику проекта.

**Independent Test**: Можно протестировать independently, создав config.yaml с кастомными промптами и запустив review агента на тестовом файле. Результат должен соответствовать шаблону с подставленными плейсхолдерами.

**Acceptance Scenarios**:

1. **Given** config.yaml с заданным `system_prompt`, **When** запускается review агент, **Then** используется кастомный system prompt вместо дефолтного
2. **Given** config.yaml с заданным `user_prompt` содержащим плейсхолдер `{file_path}`, **When** агент обрабатывает файл, **Then** плейсхолдер заменяется на реальный путь
3. **Given** `result_template` с плейсхолдерами `{summary}`, `{issues}`, `{rating}`, **When** агент завершает анализ, **Then** результат форматируется согласно шаблону

---

### User Story 2 - Model and LLM Parameters Configuration (Priority: P1)

Пользователь может выбирать модель, провайдера и настраивать параметры LLM (temperature, top_p, max_tokens) для контроля поведения review агента.

**Why this priority**: Это критически важно для баланса между строгостью и креативностью ревью, а также для управления стоимостью и скоростью.

**Independent Test**: Можно протестировать, установив различные значения temperature и запустив анализ одного и того же кода. Результаты должны отличаться по строгости комментариев.

**Acceptance Scenarios**:

1. **Given** config.yaml с `provider: "openai"` и `model: "gpt-4"`, **When** запускается review, **Then** используется указанная модель
2. **Given** `temperature: 0.1`, **When** выполняется review, **Then** комментарии более детерминированны и консервативны
3. **Given** `temperature: 0.9`, **When** выполняется review, **Then** комментарии более вариативны
4. **Given** `max_tokens_request: 4000` и `max_tokens_response: 2000`, **When** формируется запрос, **Then** лимиты соблюдаются

---

### User Story 3 - Review Profiles with Hierarchical Merge (Priority: P2)

Пользователь может выбирать профиль ревью (strict/balanced/lenient) который наследует базовые настройки и переопределяет только указанные параметры, с возможностью дальнейшего перекрытия через CLI флаги.

**Why this priority**: Профили позволяют быстро переключаться между режимами работы без дублирования всей конфигурации. Иерархический мердж обеспечивает гибкость.

**Independent Test**: Можно создать базовую конфигурацию, профиль с одним переопределённым параметром, и запустить с CLI флагом. Должен примениться приоритет: base → profile → CLI.

**Acceptance Scenarios**:

1. **Given** базовая конфигурация с `temperature: 0.5` и профиль `strict` с `temperature: 0.1`, **When** запускается `--profile strict`, **Then** используется temperature=0.1
2. **Given** базовая конфигурация с `temperature: 0.5` и профиль `strict` без указания temperature, **When** запускается `--profile strict`, **Then** используется temperature=0.5 (наследование)
3. **Given** профиль с `temperature: 0.1`, **When** запускается `--profile strict --temperature 0.7`, **Then** используется temperature=0.7 (CLI приоритет)
4. **Given** профиль `lenient`, **When** запускается review, **Then** применяются все настройки lenient профиля

---

### User Story 4 - Selective Check Toggling (Priority: P2)

Пользователь может включать и выключать отдельные категории проверок: security, performance, style.

**Why this priority**: Позволяет адаптировать ревью под конкретные задачи. Например, при security-аудите важны только проверки безопасности, а при рефакторинге — style.

**Independent Test**: Можно включить только `security` проверки и запустить review. Результат должен содержать только security-комментарии.

**Acceptance Scenarios**:

1. **Given** config.yaml с `checks.security: true`, `checks.performance: false`, `checks.style: false`, **When** выполняется review, **Then** выводятся только security замечания
2. **Given** все проверки выключены, **When** выполняется review, **Then** агент возвращает сообщение что проверки отключены
3. **Given** профиль `strict` с переопределением `checks.style: false`, **When** запускается `--profile strict`, **Then** security и performance включены, style выключен

---

### User Story 5 - Retry Policy and Timeouts Configuration (Priority: P3)

Пользователь может настраивать число попыток при ошибках LLM, backoff стратегию и таймауты на запросы.

**Why this priority**: Это важно для надёжности работы в условиях нестабильного API или временных сетевых проблем, но не влияет на базовую функциональность.

**Independent Test**: Можно установить `max_retries: 3` и `backoff: exponential` и искусственно вызвать ошибку API. Агент должен сделать 3 попытки с экспоненциальным backoff.

**Acceptance Scenarios**:

1. **Given** `max_retries: 3` и `backoff: exponential`, **When** запрос к API fails, **Then** агент повторяет с увеличенной задержкой
2. **Given** `request_timeout: 30`, **When** API не отвечает в течение 30 секунд, **Then** запрос прерывается и применяется retry политика
3. **Given** `max_retries: 0`, **When** происходит ошибка, **Then** агент завершает работу без повторов

---

### User Story 6 - Output Format Control (Priority: P3)

Пользователь может управлять форматом вывода: markdown vs JSON, наличие сниппетов кода, максимальная длина комментариев.

**Why this priority**: Это полезно для интеграции с другими инструментами (CI/CD, dashboards) но не критично для базовой работы.

**Independent Test**: Можно установить `output.format: "json"` и запустить review. Результат должен быть валидным JSON.

**Acceptance Scenarios**:

1. **Given** `output.format: "json"`, **When** review завершается, **Then** выводится валидный JSON
2. **Given** `output.format: "markdown"` и `output.include_snippets: true`, **When** найдены проблемы, **Then** в выводе присутствуют кодовые сниппеты
3. **Given** `output.max_comment_length: 200`, **When** генерируются комментарии, **Then** каждый комментарий ограничен 200 символами

---

### User Story 7 - Context and Filtering Configuration (Priority: P3)

Пользователь может настраивать контекст через prompt_variables, ограничивать размер контекстного окна, и фильтровать файлы по include/exclude паттернам.

**Why this priority**: Это расширенные возможности для оптимизации и кастомизации, не требуемые для базовой функциональности.

**Independent Test**: Можно добавить `prompt_variables.project_name: "MyProject"` и использовать этот плейсхолдер в промпте. При выполнении плейсхолдер должен быть заменён.

**Acceptance Scenarios**:

1. **Given** `prompt_variables: {project: "MyApp", team: "Backend"}`, **When** промпт содержит `{project}` и `{team}`, **Then** плейсхолдеры заменяются на "MyApp" и "Backend"
2. **Given** `context_window_size: 8000`, **When** анализируется большой файл, **Then** контент обрезается/суммаризируется до лимита
3. **Given** `include_patterns: ["src/**/*.py"]` и `exclude_patterns: ["**/test_*.py"]`, **When** запускается review, **Then** анализируются только .py файлы в src, кроме тестовых

---

### User Story 8 - Logging and Debug Mode (Priority: P3)

Пользователь может настраивать уровень логирования и включать debug-режим для детальной диагностики работы review агента.

**Why this priority**: Это полезно для troubleshooting и разработки, но не влияет на основную функциональность.

**Independent Test**: Можно установить `log_level: "debug"` и `debug: true`. При выполнении должны выводиться детальные логи всех этапов работы агента.

**Acceptance Scenarios**:

1. **Given** `log_level: "error"`, **When** происходит ошибка, **Then** выводится только error лог
2. **Given** `log_level: "debug"`, **When** выполняется review, **Then** выводятся подробные логи всех операций
3. **Given** `debug: true`, **When** завершается review, **Then** выводится статистика (tokens, time, retries)

---

### Edge Cases

- Что происходит при указании несуществующей модели? → Должна быть понятная ошибка с подсказкой доступных моделей
- Что происходит если шаблон результата содержит невалидный плейсхолдер? → Плейсхолдер должен оставаться как текст или предупреждение в логах
- Что происходит при конфликте типов (например, temperature: "high" вместо числа)? → Валидация при загрузке конфига с понятным сообщением об ошибке
- Что происходит если профиль не существует? → Ошибка с указанием доступных профилей
- Что происходит если все проверки выключены? → Предупреждение что ревью не будет содержать проверок

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST поддерживать загрузку конфигурации из config.yaml файла
- **FR-002**: System MUST поддерживать кастомные system и user промпты с подстановкой плейсхолдеров
- **FR-003**: System MUST поддерживать шаблоны результата с плейсхолдерами для форматирования вывода
- **FR-004**: System MUST поддерживать выбор провайдера LLM (openai, anthropic, и другие)
- **FR-005**: System MUST поддерживать выбор модели в рамках выбранного провайдера
- **FR-006**: System MUST поддерживать настройку temperature параметра (диапазон 0.0 - 1.0)
- **FR-007**: System MUST поддерживать настройку top_p параметра (диапазон 0.0 - 1.0)
- **FR-008**: System MUST поддерживать раздельную настройку max_tokens для запроса и ответа
- **FR-009**: System MUST поддерживать настройку retry политики (число попыток, тип backoff)
- **FR-010**: System MUST поддерживать настройку таймаутов на запросы к API
- **FR-011**: System MUST поддерживать включение/выключение отдельных проверок (security, performance, style)
- **FR-012**: System MUST поддерживать профили ревью (strict/balanced/lenient) с иерархическим мерджем
- **FR-013**: System MUST поддерживать CLI флаги с наивысшим приоритетом над конфигом
- **FR-014**: System MUST поддерживать порядок мерджа: base config → profile → CLI flags (по ключам)
- **FR-015**: System MUST поддерживать настройку формата вывода (markdown/json)
- **FR-016**: System MUST поддерживать настройку включения сниппетов кода в вывод
- **FR-017**: System MUST поддерживать настройку максимальной длины комментариев
- **FR-018**: System MUST поддерживать prompt_variables словарь для подстановки в промпты
- **FR-019**: System MUST поддерживать настройку context_window_size для ограничения контекста
- **FR-020**: System MUST поддерживать include_patterns для выборочного анализа файлов
- **FR-021**: System MUST поддерживать exclude_patterns для исключения файлов из анализа
- **FR-022**: System MUST поддерживать настройку уровня логирования (error, warn, info, debug)
- **FR-023**: System MUST поддерживать debug-режим с детальным выводом статистики
- **FR-024**: System MUST валидировать конфигурацию при загрузке и сообщать об ошибках
- **FR-025**: System MUST предоставлять дефолтную конфигурацию для всех параметров
- **FR-026**: System MUST поддерживать подстановку плейсхолдеров в промптах: {file_path}, {project_name}, {team_context} и другие из prompt_variables
- **FR-027**: System MUST поддерживать выбор профиля через `--profile` CLI флаг
- **FR-028**: System MUST позволять переопределять любой параметр через CLI флаг

### Key Entities

- **Configuration**: Представляет полную конфигурацию review агента, включая все параметры, профили и настройки
- **Profile**: Представляет пресет настроек (strict/balanced/lenient) который наследует и переопределяет базовые параметры
- **PromptTemplate**: Представляет промпт (system/user) с плейсхолдерами для динамической подстановки
- **ResultTemplate**: Представляет шаблон вывода с плейсхолдерами для структурированного форматирования результатов
- **RetryPolicy**: Представляет стратегию повторных попыток (число, backoff тип)
- **CheckConfig**: Представляет конфигурацию включённых проверок (security, performance, style)
- **OutputConfig**: Представляет настройки форматирования вывода (формат, сниппеты, длина)

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Пользователь может создать и применить кастомный промпт к review агенту менее чем за 5 минут
- **SC-002**: Смена профиля ревью (strict/balanced/lenient) применяется мгновенно без перезагрузки системы
- **SC-003**: Изменение параметров LLM (temperature, top_p) даёт предсказуемое изменение поведения агента
- **SC-004**: Выборочные проверки (например, только security) работают корректно — irrelevant проверки не выполняются
- **SC-005**: Конфигурация валидируется при загрузке с понятными сообщениями об ошибках
- **SC-006**: Иерархический мердж (base → profile → CLI) работает корректно во всех комбинациях
- **SC-007**: Плейсхолдеры в промптах и шаблонах заменяются корректно во всех сценариях
- **SC-008**: Retry политика корректно обрабатывает временные ошибки API
- **SC-009**: JSON вывод валиден и может быть парсинган другими инструментами
