# CLI Contract: --language Flag

## Interface Specification

### main.py

```bash
python main.py [--language LANGUAGE]
```

### document_debate_cli.py

```bash
python document_debate_cli.py --docx FILE --request REQUEST [--language LANGUAGE]
python document_debate_cli.py --text TOPIC [--language LANGUAGE]
```

## Argument Specification

| Flag | Type | Required | Max Length | Default | Description |
|------|------|----------|------------|---------|-------------|
| `--language` | str | No | 500 chars | None | Free-form language/style instruction |

## Error Handling

| Scenario | Behavior |
|----------|----------|
| Flag not provided | Workflow runs normally (no language injection) |
| Empty string (`--language ""`) | Treated as None (no language injection) |
| Exceeds 500 chars | argparse error before workflow starts |
| Special characters | Passed through as-is |

## Implementation Pattern

```python
parser.add_argument(
    "--language",
    type=str,
    help="Language and style setting for all agents (e.g., 'Русский официальный стиль', 'English, concise')"
)

# Usage
language_setting = args.language if args.language else None
if language_setting:
    # Validate length
    if len(language_setting) > 500:
        logger.error("❌ --language value too long (max 500 characters)")
        sys.exit(1)

# Pass to initial state
initial_state = {
    # ... other fields ...
    "language_setting": language_setting
}
```
