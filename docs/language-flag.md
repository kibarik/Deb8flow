# --language Flag Documentation

## Overview

The `--language` flag allows you to control the language and communication style of all AI agents participating in debates. This setting is applied globally to all agents (PRO, CON, Judge, Fact Checker, Moderator, Topic Generator) ensuring consistent language and tone throughout the debate.

## Quick Start

```bash
# Standard debate with Russian official style
python main.py --language "Русский официальный стиль"

# Document debate with casual Russian
python document_debate_cli.py --text "GitHub полезен" --language "Русский как другу"

# Concise English style
python main.py --language "English, concise and factual, no fluff"
```

## How It Works

### Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│ CLI --language  │────▶│ DebateState      │────▶│ BaseComponent   │
│                 │     │ .language_setting│     │ .create_chain() │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                                                            │
                                                            ▼
                                                    ┌───────────────┐
                                                    │ SYSTEM_PROMPT │
                                                    │ + language    │
                                                    │ injection     │
                                                    └───────────────┘
```

1. **CLI Layer**: The `--language` flag is parsed from command-line arguments
2. **State Layer**: `language_setting` is stored in `DebateState` and propagated through the workflow
3. **Agent Layer**: `BaseComponent.create_chain()` injects the language instruction into each agent's system prompt

### Injection Format

When a language setting is provided, it's prepended to the system prompt using this format:

```

**Language and Style Setting**: {your_language_setting}

{original_system_prompt}
...
```

This ensures the language instruction appears at the top of every agent's system prompt, maximizing visibility and compliance.

## Usage Examples

### 1. Russian Language Styles

#### Official/Formal Style
```bash
python main.py --language "Русский официальный стиль"
```
**Use case**: Professional debates, formal presentations, academic discussions

#### Casual/Friendly Style
```bash
python main.py --language "Русский как другу"
```
**Use case**: Informal debates, conversational tone, approachable explanations

### 2. English Language Styles

#### Concise Style
```bash
python main.py --language "English, concise and factual, no fluff"
```
**Use case**: Quick debates, bullet-point responses, business presentations

#### Professional Style
```bash
python main.py --language "English professional tone with citations"
```
**Use case**: Academic debates, research discussions, formal presentations

### 3. Style Modifiers (Language-Independent)

```bash
# Short and direct
python main.py --language "Short responses, bullet points where possible"

# Academic style
python main.py --language "Academic tone with citations and formal language"

# Explainer style
python main.py --language "Conversational tone, explain like I'm 12"
```

### 4. Document-Based Debates

```bash
# With direct topic
python document_debate_cli.py --text "GitHub полезен для разработчиков" \
    --language "Русский официальный стиль"

# With document file
python document_debate_cli.py --docx project.docx --request "какой потенциал?" \
    --language "кратко и по-факту, без лишней воды"
```

## Command Reference

### Standard Debate (`main.py`)

```bash
python main.py [--language LANGUAGE]
```

| Flag | Type | Required | Max Length | Default |
|------|------|----------|------------|---------|
| `--language` | str | No | 500 chars | None |

### Document Debate (`document_debate_cli.py`)

```bash
python document_debate_cli.py --text TOPIC [--language LANGUAGE]
python document_debate_cli.py --docx FILE --request REQUEST [--language LANGUAGE]
```

| Flag | Type | Required | Max Length | Default |
|------|------|----------|------------|---------|
| `--language` | str | No | 500 chars | None |

## Behavior & Validation

### Validation Rules

| Scenario | Behavior |
|----------|----------|
| Flag not provided | System runs normally (no language injection) |
| Empty string (`--language ""`) | Treated as None (no injection) |
| Exceeds 500 characters | Error: `❌ --language value too long (max 500 characters)` |
| Special characters | Passed through as-is |

### Backward Compatibility

The `--language` flag is **100% backward compatible**:

- Without the flag, the system behaves exactly as before
- All existing E2E tests pass without modification
- No breaking changes to API or state structure

## Technical Details

### State Field Definition

```python
class DebateState(TypedDict):
    # ... existing fields ...
    language_setting: NotRequired[Optional[str]]  # Language/style instruction
```

### BaseComponent Integration

```python
def create_chain(
    self, system_template: str, human_template: str, language_setting: Optional[str] = None
) -> RunnableSequence:
    # Use provided language_setting or fall back to self.language_setting from state
    if language_setting is None and hasattr(self, 'language_setting'):
        language_setting = self.language_setting

    # Inject language setting into system template if provided
    if language_setting:
        injection = f"\n\n**Language and Style Setting**: {language_setting}\n\n"
        system_template = injection + system_template
    # ... rest of implementation
```

## Limitations

### What's Supported

- ✅ Free-form language/style descriptions
- ✅ Global setting for all agents
- ✅ Up to 500 characters
- ✅ All debate modes (standard and document-based)

### What's NOT Supported

- ❌ Per-agent language configuration (different languages for PRO vs CON)
- ❌ Language validation or detection
- ❌ Multi-language debates (agents using different languages)
- ❌ Formal language codes (e.g., en-US, ru-RU)
- ❌ Language-specific prompt templates

## Tips & Best Practices

### 1. Be Specific

Better: `"Russian formal style with professional terminology"`
Good: `"Russian"`

### 2. Combine Language and Style

Best: `"Russian official style, use formal titles, avoid slang"`
Good: `"Русский"`

### 3. Test Before Important Debates

Always run a test debate with your language setting before using it for important discussions:

```bash
python main.py --language "Your language setting here"
```

### 4. Use Consistent Settings

For reproducible results, use the same language setting across multiple debates on the same topic.

## Troubleshooting

### Language Setting Not Applied

**Problem**: Agents don't seem to follow the language setting.

**Solutions**:
1. Check that the flag is properly formatted: `--language "your setting"` (quotes required)
2. Verify the setting is logged: Look for `🌐 Language setting: ...` in output
3. Try a simpler/more explicit setting
4. Remember: AI models have varying degrees of language compliance

### Empty Language Setting Causes Issues

**Problem**: Using `--language ""` causes unexpected behavior.

**Solution**: Empty strings are treated as None (no language injection). Omit the flag entirely for default behavior.

### Special Characters

**Problem**: Special characters in language text cause issues.

**Solution**: Special characters are passed through as-is. If issues occur, try simpler text or escape special characters.

## Examples Gallery

### Academic Debate in Russian

```bash
python main.py --language "Русский академический стиль с цитатами и формальной терминологией"
```

### Casual Explainer in English

```bash
python main.py --language "English, explain like I'm 12, use simple words and analogies"
```

### Business Presentation Style

```bash
python main.py --language "Professional business tone, focus on ROI and metrics, bullet points preferred"
```

### Socratic Method

```bash
python main.py --language "Use Socratic method - ask questions to explore the topic, guide toward conclusions"
```

## Related Documentation

- [README.md](../README.md) - Project overview
- [CONTRIBUTING.md](../CONTRIBUTING.md) - Contribution guidelines
- [Feature Specification](../kitty-specs/012-language-and-style-configuration/spec.md) - Technical specification
