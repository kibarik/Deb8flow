# Language Flag Feature - Testing Guide

**Feature**: 012-language-and-style-configuration
**Status**: Implementation complete, awaiting merge of all WPs

## Testing After Merge

After all work packages (WP01, WP02, WP03) are merged to main, run these commands to verify the feature:

### 1. Verify CLI Help

```bash
# Standard debate
python main.py --help | grep language

# Document debate
python document_debate_cli.py --help | grep language
```

Expected output: Should show `--language LANGUAGE` flag with description.

### 2. Test Language Flag with Russian

```bash
# Standard debate in Russian
python main.py --language "Русский официальный стиль"
```

Expected: All agents (PRO, CON, Judge, Fact Checker) respond in formal Russian.

### 3. Test Language Flag with Concise English

```bash
# Concise English style
python main.py --language "English, concise and factual, no fluff"
```

Expected: All agents respond in English with minimal verbiage.

### 4. Test Document Debate with Language Flag

```bash
# Document debate with language flag
python document_debate_cli.py --text "GitHub полезен для разработчиков" --language "Русский как другу"
```

Expected: Document-based debate in casual Russian tone.

### 5. Test Validation

```bash
# Should fail - too long
python main.py --language "$(python -c 'print("a" * 501)')"
# Expected: ❌ --language value too long (max 500 characters)

# Should pass - exactly 500 chars
python main.py --language "$(python -c 'print("a" * 500)')"
# Expected: Proceeds with validation passed
```

### 6. Test Backward Compatibility

```bash
# No language flag - should work as before
python main.py

# Empty string - treated as None
python main.py --language ""
```

Expected: Both commands work without language-related errors.

## Unit Tests

```bash
# Run language flag tests
pytest tests/test_language_flag.py -v

# Run contract tests
pytest tests/contract/test_debate_state.py -k language_setting -v

# Run BaseComponent language tests
pytest tests/test_base_component_language.py -v
```

## Expected Test Results

After merge:
- All 9 contract tests for language_setting should pass
- All 9 BaseComponent language injection tests should pass
- All 13 language flag integration tests should pass
- All existing E2E tests should continue to pass (backward compatibility)

## Customer Journey Example

```bash
# User wants Russian official style debate
python main.py --language "пиши все на русском"

# Output preview:
# 🌐 Language setting: пиши все на русском
#
# 🏛️ Topic: [debate topic in Russian]
# 👥 Positions:
#    ▸ PRO: [position in Russian]
#    ▸ CON: [position in Russian]
#
# PRO OPENING [in Russian]
# ...
```
