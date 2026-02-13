# Data Model: Custom Prompt Debate Workflow

**Feature**: 003-tpm-cpo-product-funding-debate-workflow
**Date**: 2025-02-13

## Entities

### DebateState (Extended)

The existing state container, extended with custom prompt fields.

```python
from typing import TypedDict, List, Dict, Literal, Optional
from typing_extensions import NotRequired

DebateStage = Literal["opening", "rebuttal", "counter", "final_argument"]

class DebateMessage(TypedDict):
    speaker: str  # "pro" or "con"
    content: str  # The message produced
    validated: bool  # Whether FactChecker verified this message
    stage: DebateStage  # The stage when this message was produced

class DebateState(TypedDict):
    debate_topic: str  # The topic being debated
    positions: Dict[str, str]  # Speaker position summaries
    messages: List[DebateMessage]  # Full debate transcript
    # NEW FIELDS:
    pro_custom_prompt: NotRequired[Optional[str]]  # Custom PRO debater prompt content
    con_custom_prompt: NotRequired[Optional[str]]  # Custom CON debater prompt content
    # EXISTING FIELDS:
    stage: NotRequired[str]  # Current stage: "opening", "rebuttal", "counter", "final_argument"
    speaker: NotRequired[str]  # Current speaker: "pro" or "con"
    times_pro_fact_checked: NotRequired[int]  # PRO fact-check count
    times_con_fact_checked: NotRequired[int]  # CON fact-check count
    verdict: NotRequired[str]  # Final verdict
```

### PromptFile (CLI Input)

Represents a custom prompt file provided via CLI flags.

```python
class PromptFile:
    path: str  # File system path
    content: str  # File content (max 5000 characters)
    exists: bool  # Whether file exists
    is_valid: bool  # Whether file passes validation
    error: Optional[str]  # Validation error message if any
```

## State Transitions

```
[START]
    ↓
[VALIDATE_PROMPT_FILES]
    Check if --pro-prompt and --con-prompt files exist
    Validate file sizes and content
    ↓
[INITIALIZE_STATE]
    debate_topic = "" (to be extracted from text/document)
    pro_custom_prompt = <content from --pro-prompt file or None>
    con_custom_prompt = <content from --con-prompt file or None>
    messages = []
    stage = "opening"
    speaker = "pro"
    ↓
[PRO_OPENING] (uses pro_custom_prompt if provided) → [FACT_CHECK]
    ↓
[CON_REBUTTAL] (uses con_custom_prompt if provided) → [FACT_CHECK]
    ↓
[PRO_COUNTER] (uses pro_custom_prompt if provided) → [FACT_CHECK]
    ↓
[CON_FINAL_ARGUMENT] (uses con_custom_prompt if provided) → [FACT_CHECK]
    ↓
[JUDGE_VERDICT]
    verdict = <explanation>
    ↓
[END]
```

## Relationships

```
DebateState
    ├─ contains → List<DebateMessage>
    ├─ references → pro_custom_prompt (Optional[str])
    ├─ references → con_custom_prompt (Optional[str])
    ├─ tracks → stage (DebateStage)
    ├─ tracks → speaker ("pro" | "con")
    └─ produces → verdict

PromptFile (CLI)
    ├─ provided by → --pro-prompt flag
    ├─ provided by → --con-prompt flag
    ├─ validated by → File validation logic
    └─ injected into → DebateState.pro_custom_prompt OR DebateState.con_custom_prompt
```

## Validation Rules

### File Validation (CLI)

| Field | Validation | Rationale |
|-------|------------|-----------|
| --pro-prompt file | Must exist, non-empty, <= 5000 chars | Prevent invalid inputs |
| --con-prompt file | Must exist, non-empty, <= 5000 chars | Prevent invalid inputs |

### State Validation

| Field | Validation | Rationale |
|-------|------------|-----------|
| pro_custom_prompt | Optional, None or non-empty string | Allow default behavior |
| con_custom_prompt | Optional, None or non-empty string | Allow default behavior |
| debate_topic | Required, derived from input | Focused debate topic |
| speaker | Must be "pro" or "con" | Prevent invalid state |
| stage | Must follow sequence: opening → rebuttal → counter → final_argument | Enforce debate structure |

### Prompt Injection Rules

| Rule | Implementation |
|------|----------------|
| Custom prompt is None | Use base system prompt only |
| Custom prompt provided | Prepend custom prompt to base system prompt |
| Both prompts None | Standard debate (backward compatibility) |
| Only PRO prompt | PRO uses custom, CON uses base |
| Only CON prompt | CON uses custom, PRO uses base |
