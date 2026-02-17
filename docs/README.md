# Deb8flow - Полный справочник по функциям

**Deb8flow** — мульти-агентный фреймворк для AI дебатов, построенный на LangGraph. Симулирует структурированные дебаты между двумя AI агентами (PRO и CON) с модератором и судьёй.

---

## 🚀 Быстрый старт

### Установка и настройка

```bash
# Установка зависимостей
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Настройка API ключа
echo "OPENAI_API_KEY=your_key" > .env
```

---

## 📚 Основные функции

### 1. Стандартный AI дебат

**Команда**: `python main.py`

Запускает полноценный AI дебат между агентами PRO и CON с автоматической генерацией темы.

**Как работает**:
1. Генерируется тема дебата
2. PRO агент выступает с открытием
3. Fact-checker проверяет утверждения
4. CON агент отвечает с опровержением
5. PRO агент отвечает с контраргументом
6. CON агент делает финальное заявление
7. Judge выносит вердикт

**Пример**:
```bash
python main.py
```

**Опции**:
- `--language "<стиль>"` — Язык и стиль всех агентов (например, "Русский официальный стиль")

---

### 2. Документные дебаты

**Команда**: `python document_debate_cli.py`

Запускает дебат на основе документа или自定义 темы.

#### Режимы использования

**А) Прямая тема:**
```bash
python document_debate_cli.py --text "GitHub полезен для разработчиков"
```

**Б) Документ + вопрос:**
```bash
python document_debate_cli.py \
  --docx '/path/to/document.docx' \
  --request "какой потенциал у этого проекта?"
```

**В) Кастомные роли:**
```bash
python document_debate_cli.py \
  --docx 'PRD.docx' \
  --request "оценить потенциал" \
  --pro-prompt 'prompts/tpm.txt' \
  --con-prompt 'prompts/cpo.txt'
```

**Все опции**:
| Флаг | Описание |
|------|------------|
| `--text <topic>` | Прямая тема для дебата |
| `--docx <file>` | Путь к .docx файлу |
| `--request <question>` | Вопрос/тема (с --docx) |
| `--pro-prompt <file>` | Кастомный промпт для PRO |
| `--con-prompt <file>` | Кастомный промпт для CON |
| `--language "<стиль>"` | Язык и стиль агентов |
| `--verbose` | Детальный вывод промптов |
| `--json-output <file>` | Сохранить результат в JSON |

---

## 🎛️ Дополнительные функции

### 3. Настройка языка и стиля дебата

**Фича**: `--language` флаг

Позволяет задать язык и тон общения для всех AI агентов.

**Использование**:
```bash
# Русский официальный стиль
python main.py --language "Русский официальный стиль"

# Документный дебат на русском
python document_debate_cli.py --text "Тема" --language "Русский как другу"

# Лаконичный английский
python main.py --language "English, concise and factual, no fluff"
```

**Как влияет на результат**:
- Все агенты (PRO, CON, Judge, Fact Checker) отвечают на указанном языке
- Стиль общения применяется единообразно
- Если флаг не указан — используется стандартное поведение

**Ограничения**:
- Максимум 500 символов
- Специальные символы передаются как есть
- Пустая строка treated как отсутствие настройки

📖 **Подробнее**: `docs/language-flag.md`

---

### 4. Сводка дебата (Q&A формат)

**Команда**: Используется автоматически после завершения дебата

Выводит структурированную сводку дебата с парами "Вопрос-Ответ".

**Как работает**:
- Extracts all messages from debate
- Formats as Q&A pairs
- Shows PRO/CON positions on each question

**Пример вывода**:
```
Q: [Тема дебата]
A (PRO): [Позиция PRO]
A (CON): [Позиция CON]

Q: [Следующий вопрос]
...
```

📖 **Подробнее**: `docs/cli-debate-summary.md`

---

### 5. Комитетная экспертиза PRD

**Команда**: Используется через `document_debate_cli.py` с кастомными промптами

Мульти-перспективный анализ PRD с дебатом между ролями (TPM vs CPO/CFO/CTO/BDM).

**Как работает**:
- 4 "комнаты" для дебатов между ролями
- TPM self-reflection процесс
- Graceful partial failure handling

**Использование**:
```bash
python document_debate_cli.py \
  --docx 'PRD.docx' \
  --request "оценить PRD" \
  --pro-prompt 'prompts/tpm.txt' \
  --con-prompt 'prompts/cpo.txt'
```

📖 **Подробнее**: `docs/product-committee-orchestrator.md`

---

### 6. Отчет о заключении дебата

**Команда**: Автоматически генерируется после завершения дебата

Создаёт структурированный отчёт `conclusion_reports/{date}_{topic}.md` с:
- Вердиктом судьи
- Q&A сводкой
- Рекомендациями по улучшению
- Анализом победителя

**Структура отчёта**:
```markdown
# Debate Conclusion Report

## Verdict
WINNER: PRO/CON

## Question & Answer Summary
[Все Q&A из дебата]

## Recommendations
[Рекомендации от фокусной группы]

## Victory Analysis
[Почему победила эта сторона]

## Action Plan
[Приоритизированные действия]
```

📖 **Подробнее**: `docs/debate-conclusion-report.md`

---

### 7. Валидация полноты PRD

**Команда**: Автоматически запускается при документных дебатах

Проверяет PRD на соответствие шаблону и оценивает полноту.

**Как работает**:
- Сравнивает PRD с шаблоном
- Выставляет оценку 0-10
- Генерирует отчёт с рекомендациями

**Критерии оценки**:
- Наличие обязательных секций
- Качество описания
- Полнота требований
- Метрики и KPI

📖 **Подробнее**: `docs/prd-completeness-validator.md`

---

### 8. Улучшенный отчет о заключении комитета

**Фича**: Enhanced committee debate conclusion

Расширенная версия отчета о заключении с:
- Уровнем уверенности (Confidence Level)
- Ролевым анализом с отслеживанием доказательств
- Приоритизированным планом действий с метриками
- Лимитами длины для читаемости

**Отличия от стандартного отчёта**:
- Более детальный анализ
- Цифровые метрики
- Структурированные рекомендации

📖 **Подробнее**: `docs/enhanced-committee-debate-conclusion.md`

---

### 9. YAML конфигурация дебатов

**Команда**: Используется через специальную конфигурацию

Позволяет настраивать дебаты через YAML файл вместо CLI аргументов.

**Пример конфигурации**:
```yaml
debate_name: "Product Strategy Debate"
roles:
  pro_agent:
    system_prompt: "You are a Product Manager..."
  con_agent:
    system_prompt: "You are a CTO..."
```

**Возможности**:
- Inline промпты для ролей
- Файловые промпты
- Вспомогательные роли с условиями триггера
- Валидация конфигурации

📖 **Подробнее**: `docs/flexible-debate-config-yaml.md`

---

### 10. Переписывание документов

**Фича**: Document rewrite agent

Автоматически переписывает документы на основе заключения дебата.

**Использование**:
```bash
python document_debate_cli.py \
  --docx 'document.docx' \
  --request "как улучшить?" \
  --make-review
```

**Как работает**:
- Анализирует заключение дебата
- Переписывает документ с учётом рекомендаций
- Поддерживает .docx, .md, .txt, .rtf

**Обработка правил**:
- Сохраняет основную структуру
- Интегрирует улучшения
- Сохраняет метаданные

📖 **Подробнее**: `docs/document-rewrite-agent.md`

---

## 🧪 Тестирование

### Запуск тестов

```bash
# Все тесты
pytest

# Конкретный тест
pytest tests/test_base_component_language.py

# С coverage
pytest --cov=.
```

### E2E тесты

```bash
# Полный дебат flow
pytest tests/e2e/test_full_debate_flow.py

# Документный дебат
pytest tests/e2e/test_document_debate_e2e.py
```

---

## 🔧 Конфигурация

### LLM Провайдеры

Поддерживаются несколько провайдеров через `configurations/llm_config.py`:
- OpenAI (GPT-4, GPT-3.5)
- Azure OpenAI
- Zhipu AI
- Requesty (DeepSeek)

### Переменные окружения

```bash
# Обязательные
OPENAI_API_KEY=your_key

# Опциональные (для трассировки)
LANGCHAIN_API_KEY=your_key
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=deb8flow

# Для Requesty (DeepSeek)
REQ_API_KEY=your_key
```

---

## 📖 Структура проекта

```
Deb8flow/
├── main.py                    # Стандартные AI дебаты
├── document_debate_cli.py     # Документные дебаты
├── nodes/                     # AI агенты (PRO, CON, Judge, Fact Checker)
├── workflow/                  # LangGraph workflows
├── prompts/                   # Системные промпты для агентов
├── configurations/            # LLM конфигурации
├── debate_state.py            # Определение состояния дебата
├── tests/                     # Unit и E2E тесты
└── docs/                      # Документация функций
```

---

## 🎯 Common Use Cases

### Sценарий 1: Анализ PRD документа

```bash
python document_debate_cli.py \
  --docx 'docs/PRD.md' \
  --request "Каковы основные риски?" \
  --language "Русский официальный стиль"
```

### Сценарий 2: Быстрый дебат на тему

```bash
python main.py --language "English, concise, bullet points"
```

### Сценарий 3: Ролевой дебат (Technical vs Business)

```bash
python document_debate_cli.py \
  --text "Нужно ли внедрять CI/CD?" \
  --pro-prompt 'prompts/devops.txt' \
  --con-prompt 'prompts/manager.txt'
```

### Сценарий 4: Комитетная экспертиза

```bash
# Создаём промпты для ролей
echo "You are TPM..." > prompts/tpm.txt
echo "You are CPO..." > prompts/cpo.txt

# Запускаем дебат
python document_debate_cli.py \
  --docx 'PRD.docx' \
  --request "Оценить приоритеты" \
  --pro-prompt 'prompts/tpm.txt' \
  --con-prompt 'prompts/cpo.txt'
```

---

## ⚙️ Работа промптов

Промпты для кастомизации находятся в `prompts/`:

| Файл | Назначение |
|------|------------|
| `topic_generator_prompts.py` | Генератор тем дебатов |
| `pro_debater_prompts.py` | PRO агент (открывающий) |
| `con_debater_prompts.py` | CON агент (опроверяющий) |
| `judge_prompts.py` | Судья |
| `fact_checker_prompts.py` | Fact-checker |
| `debate_moderator_prompts.py` | Модератор |

**Создание кастомного промпта**:
```bash
# Создаём файл с промптом
cat > prompts/my_custom_role.txt << 'EOF'
You are a Senior Security Architect.
Focus on: attack vectors, compliance, scalability.
Tone: technical but accessible.
EOF

# Используем в дебате
python document_debate_cli.py \
  --text "Внедрить ли новую систему?" \
  --pro-prompt 'prompts/my_custom_role.txt'
```

---

## 🐛 Troubleshooting

### Ошибка: Missing environment variable
```bash
# Решение: создать .env файл
echo "OPENAI_API_KEY=your_key" > .env
```

### Дебат застрял
```bash
# Проверить токены
echo "LANGCHAIN_API_KEY=sk-..." > .env
LANGCHAIN_TRACING_V2=true

# Запустить с отладкой
python main.py
```

### Fact-check failures
- Агенты автоматически дисквалифицируются после 3 фактических ошибок
- Проверьте логи для сообщений `FACT-CHECK FAIL`

---

## 📚 Полная документация по функциям

Более детальная документация по каждой функции доступна в `docs/`:

- `language-flag.md` — Флаг `--language`
- `prd-document-debate-workflow.md` — Документные дебаты
- `cli-debate-summary.md` — Q&A сводка
- `product-committee-orchestrator.md` — Комитетная экспертиза
- `debate-conclusion-report.md` — Отчёт о заключении
- `prd-completeness-validator.md` — Валидация PRD
- `enhanced-committee-debate-conclusion.md` — Улучшенные заключения
- `flexible-debate-config-yaml.md` — YAML конфигурация
- `document-rewrite-agent.md` — Переписывание документов

---

## 🔄 Версионность и статус

**Версия**: 1.0
**Текущий статус**: Active Development
**E2E Tests**: 19/19 passing

**Последнее обновление**: Февраль 2025
