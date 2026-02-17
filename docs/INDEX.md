# 📚 Deb8flow - Справочник по всем функциям

**Актуальное руководство по использованию Deb8flow** | Обновлено: Февраль 2025

---

## 🚀 Начало работы

Для первой установки читайте [README.md](README.md) в корне проекта.

Кратко:
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
echo "OPENAI_API_KEY=your_key" > .env
python main.py  # Запуск дебата
```

---

## 📋 Все функции проекта

### Основные функции

| Функция | Команда | Описание | Документация |
|---------|---------|-----------|--------------|
| **Стандартный AI дебат** | `python main.py` | Автоматический дебат между PRO и CON агентами | [README.md](README.md) |
| **Документные дебаты** | `python document_debate_cli.py --text "<тема>"` | Дебат на основе документа или темы | [→](#-документные-дебаты) |

### Дополнительные функции

| Функция | Документация |
|---------|--------------|
| 🌐 **Настройка языка и стиля** (`--language`) | [language-flag.md](language-flag.md) |
| 📊 **Сводка Q&A формата** | [cli-debate-summary.md](cli-debate-summary.md) |
| 👥 **Комитетная экспертиза PRD** | [product-committee-orchestrator.md](product-committee-orchestrator.md) |
| 📝 **Отчет о заключении** | [debate-conclusion-report.md](debate-conclusion-report.md) |
| ✅ **Валидация полноты PRD** | [prd-completeness-validator.md](prd-completeness-validator.md) |
| 🎯 **Улучшенные заключения комитета** | [enhanced-committee-debate-conclusion.md](enhanced-committee-debate-conclusion.md) |
| ⚙️ **YAML конфигурация** | [flexible-debate-config-yaml.md](flexible-debate-config-yaml.md) |
| ✍️ **Переписывание документов** | [document-rewrite-agent.md](document-rewrite-agent.md) |
| 🧪 **Автотесты** | [comprehensive-automated-test-suite.md](comprehensive-automated-test-suite.md) |

---

## 🎓 Быстрый старт по сценариям

### Сценарий 1: Анализ PRD документа

**Задача**: Оценить PRD с разных точек зрения

```bash
python document_debate_cli.py \
  --docx 'docs/PRD.md' \
  --request "Каковы основные риски и возможности?" \
  --language "Русский официальный стиль"
```

**Результат**:
- Мульти-перспективный анализ
- Q&A сводка
- Отчет с рекомендациями

---

### Сценарий 2: Быстрая оценка идеи

**Задача: Быстрый дебат по теме

```bash
python main.py --language "English, concise, bullet points"
```

**Результат**:
- Автоматически сгенерированная тема
- Лаконичные аргументы
- Чёткий вердикт

---

### Сценарий 3: Ролевой дебат (Technical vs Business)

**Задача**: Дебат с позиций ролей

```bash
# Создаём промпты
echo "You are a Senior DevOps, focus on security and scalability" > prompts/devops.txt
echo "You are a Product Manager, focus on user value and time-to-market" > prompts/pm.txt

# Запускаем дебат
python document_debate_cli.py \
  --text "Нужно ли внедрять Kubernetes?" \
  --pro-prompt 'prompts/devops.txt' \
  --con-prompt 'prompts/pm.txt'
```

---

### Сценарий 4: Комитетная экспертиза PRD

**Задача**: Оценка PRD комитетом (TPM, CPO, CFO, CTO, BDM)

```bash
# Подготовка промптов для ролей
echo "You are TPM..." > prompts/tpm.txt
echo "You are CPO..." > prompts/cpo.txt
echo "You are CFO..." > prompts/cfo.txt
echo "You are CTO..." > prompts/cto.txt
echo "You are BDM..." > prompts/bdm.txt

# Запуск
python document_debate_cli.py \
  --docx 'PRD.docx' \
  --request "Приоритизировать функции" \
  --pro-prompt 'prompts/tpm.txt' \
  --con-prompt 'prompts/cpo.txt'
```

**Результат**:
- 4-комнатный дебат (TPM ↔ CPO/CFO/CTO/BDM)
- TPM self-reflection
- Улучшенный отчет с рекомендациями

---

## 📖 Детальная документация по функциям

### Документные дебаты
**📘** [prd-document-debate-workflow.md](prd-document-debate-workflow.md)

Дебаты на основе документов с 4-стадийной структурой:
1. Тема → PRO открытие → Fact check
2. CON опровержение → Fact check
3. PRO контраргумент → Fact check
4. CON финальный аргумент → Judge verdict

**Команды**:
```bash
# С документом
python document_debate_cli.py --docx 'file.docx' --request "Вопрос?"

# С прямой темой
python document_debate_cli.py --text "Тема для дебата"

# С кастомными ролями
python document_debate_cli.py \
  --docx 'file.docx' --request "Вопрос?" \
  --pro-prompt 'prompts/role1.txt' \
  --con-prompt 'prompts/role2.txt'
```

---

### Язык и стиль
**📘** [language-flag.md](language-flag.md)

Глобальная настройка языка и стиля для всех агентов через `--language`.

**Примеры**:
```bash
python main.py --language "Русский официальный стиль"
python main.py --language "English, concise and factual"
python main.py --language "Кратко, по-факту, без лишней воды"
```

**Как работает**:
- Инъекция в system prompt каждого агента
- Формат: `\n\n**Language and Style Setting**: {текст}\n\n`
- Максимум 500 символов

---

### Комитетная экспертиза
**📘** [product-committee-orchestrator.md](product-committee-orchestrator.md)

Мульти-перспективный анализ с ролевыми промптами.

**Особенности**:
- Поддержка до 5 ролей
- Graceful partial failure
- Self-reflection для TPM

---

### Отчеты о заключении
**📘** [debate-conclusion-report.md](debate-conclusion-report.md) | **enhanced-committee-debate-conclusion.md](enhanced-committee-debate-conclusion.md)

Автоматическая генерация отчетов:
- Вердикт судьи
- Q&A сводка
- Рекомендации
- Победитель и анализ

---

### YAML конфигурация
**📘** [flexible-debate-config-yaml.md](flexible-debate-config-yaml.md)

Декларативная настройка дебатов через YAML вместо CLI.

---

### Переписывание документов
**📘** [document-rewrite-agent.md](document-rewrite-agent.md)

Автоматическое переписывание документов на основе рекомендаций из дебата.

```bash
python document_debate_cli.py \
  --docx 'document.docx' \
  --request "как улучшить?" \
  --make-review
```

---

### Валидация PRD
**📘** [prd-completeness-validator.md](prd-completeness-validator.md)

Автоматическая проверка PRD на соответствие шаблону с оценкой 0-10.

---

## 🧪 Тестирование

### Запуск тестов

```bash
# Все тесты
pytest

# Конкретные тесты
pytest tests/test_base_component_language.py
pytest tests/e2e/test_full_debate_flow.py

# С coverage
pytest --cov=nodes --cov=workflow
```

### E2E тесты

Полные тесты всех сценариев:
- 19/19 passing (см. `E2E_TEST_REPORT.md`)

---

## 🔧 Конфигурация

### LLM провайдеры
- OpenAI (GPT-4, GPT-3.5)
- Azure OpenAI
- Zhipu AI
- Requesty (DeepSeek)

### Переменные окружения
```bash
OPENAI_API_KEY=sk-...           # Обязательно
LANGCHAIN_API_KEY=lcv_...       # Опционально (трассировка)
REQ_API_KEY=...                 # Опционально (Requesty/DeepSeek)
```

---

## 📁 Навигация по коду

```
Deb8flow/
├── main.py                    # Вход для стандартных дебатов
├── document_debate_cli.py     # Вход для документных дебатов
├── nodes/                     # AI агенты
│   ├── base_component.py      # Базовый класс для всех агентов
│   ├── pro_debater_node.py
│   ├── con_debater_node.py
│   ├── judge_node.py
│   └── fact_checker_node.py
├── workflow/                  # LangGraph workflows
│   ├── debate_workflow.py
│   └── document_debate_workflow.py
├── prompts/                   # Промпты агентов
├── configurations/            # LLM конфигурации
├── debate_state.py            # State definition
└── tests/                     # Unit + E2E тесты
```

---

## 🎯 Common Patterns

### Добавление нового агента

1. Наследуйте от `BaseComponent`
2. Реализуйте метод `__call__(self, state: DebateState)`
3. Используйте `self.create_chain()` для создания цепи
4. Добавьте промпт в `prompts/`

### Создание кастомного промпта

```bash
# Файл должен содержать только текст промпта
cat > prompts/my_role.txt << 'EOF'
You are a Senior Security Expert.
Your expertise: application security, threat modeling, secure coding.
Your tone: professional but accessible.
EOF

# Использование
python document_debate_cli.py \
  --text "Использовать ли 2FA?" \
  --pro-prompt 'prompts/my_role.txt'
```

---

## 📞 Поддержка

**Документация обновлена**: Февраль 2025
**Версия**: 1.0
**Статус**: Active Development

Для вопросов и предложений используйте GitHub Issues.
