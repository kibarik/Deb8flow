# Quickstart: Language and Style Configuration

## Basic Usage

### Standard Debate

```bash
# Default (no language setting)
python main.py

# Russian formal style
python main.py --language "Русский официальный стиль"

# English, concise
python main.py --language "English, concise and factual, no fluff"

# Casual Russian
python main.py --language "Русский как другу"
```

### Document Debate

```bash
# With direct topic
python document_debate_cli.py --text "GitHub полезен для разработчиков" \
    --language "Русский официальный стиль"

# With document context
python document_debate_cli.py --docx project.docx --request "какой потенциал?" \
    --language "кратко и по-факту, без лишней воды"
```

## Examples

### Russian Formal Debate

```bash
$ python document_debate_cli.py \
    --text "GitHub полезен для разработчиков" \
    --language "Русский официальный стиль"

# All agents (PRO, CON, Judge, Fact Checker) respond in formal Russian
```

### Multi-Language Context

```bash
$ python main.py --language "English professional tone with citations"

# Debate in English with professional tone and citation requirements
```

### Style Modifiers

```bash
# Concise style
--language "Short responses, bullet points where possible"

# Academic style
--language "Academic tone with citations and formal language"

# Casual style
--language "Conversational tone, explain like I'm 12"
```

## Testing

```bash
# Run all tests
pytest

# Run specific language test
pytest tests/e2e/test_full_debate_flow.py::test_language_flag

# Run with coverage
pytest --cov=nodes --cov=workflow
```

## Troubleshooting

**Problem**: Language setting not applied

**Solution**: Check that:
1. `--language` flag is correctly passed to CLI
2. `language_setting` is in initial state
3. `BaseComponent.create_chain()` is called (not bypassed)

**Problem**: Empty language setting causes issues

**Solution**: Empty strings are treated as None - use `if args.language:` check
