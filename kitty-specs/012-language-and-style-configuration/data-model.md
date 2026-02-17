# Data Model: Language and Style Configuration

## Entity: DebateState.language_setting

**Field**: `language_setting`
**Type**: `NotRequired[Optional[str]]`
**Location**: `debate_state.py` → `DebateState` TypedDict

### Field Definition

```python
class DebateState(TypedDict):
    # ... existing fields ...
    language_setting: NotRequired[Optional[str]]  # NEW FIELD
```

### Validation Rules

| Rule | Description |
|------|-------------|
| Optional | Field may be absent from state |
| Nullable | Value may be None |
| Max length | 500 characters (enforced at CLI level) |
| No validation | Content is free-form text, passed directly to prompts |

### State Flow

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

### Example States

**Default (no language setting)**:
```python
state = {
    "debate_topic": "AI safety",
    "positions": {},
    "messages": []
    # language_setting absent
}
```

**With language setting**:
```python
state = {
    "debate_topic": "AI safety",
    "positions": {},
    "messages": [],
    "language_setting": "Русский официальный стиль"
}
```

### Migration

**No migration required** - `NotRequired[Optional[str]]` is backward compatible:
- Existing states without the field continue to work
- Existing code that doesn't reference the field is unaffected
