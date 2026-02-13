# Data Model: TPM-CPO Product Funding Debate Workflow

**Feature**: 003-tpm-cpo-product-funding-debate-workflow
**Date**: 2025-02-13

## Entities

### TpmCpoDebateState

The primary state container for TPM-CPO funding debates.

```python
from typing import TypedDict, List, Dict, Literal
from typing_extensions import NotRequired

TpmCpoDebateStage = Literal["opening", "rebuttal", "counter", "final_argument"]

class TpmCpoDebateMessage(TypedDict):
    speaker: str  # "tpm" or "cpo"
    content: str  # The message produced
    validated: bool  # Whether the FactChecker verified this message
    stage: TpmCpoDebateStage  # The stage when this message was produced

class TpmCpoDebateState(TypedDict):
    debate_topic: str  # The project proposal being debated
    positions: Dict[str, str]  # Speaker position summaries
    messages: List[TpmCpoDebateMessage]  # Full debate transcript
    prd_input: str  # The PRD text content (source of truth)
    stage: NotRequired[str]  # Current stage: "opening", "rebuttal", "counter", "final_argument"
    speaker: NotRequired[str]  # Current speaker: "tpm" or "cpo"
    times_tpm_fact_checked: NotRequired[int]  # TPM fact-check count
    times_cpo_fact_checked: NotRequired[int]  # CPO fact-check count
    funding_decision: NotRequired[str]  # Final verdict: "approve" or "deny"
    verdict_reasoning: NotRequired[str]  # Explanation for funding decision
```

## State Transitions

```
[START]
    ↓
[INITIALIZE_STATE]
    debate_topic = "" (to be extracted from PRD)
    prd_input = <user_provided_text>
    messages = []
    stage = "opening"
    speaker = "tpm"
    ↓
[TMP_OPENING] → [FACT_CHECK]
    ↓
[CPO_REBUTTAL] → [FACT_CHECK]
    ↓
[TMP_COUNTER] → [FACT_CHECK]
    ↓
[CPO_FINAL_ARGUMENT] → [FACT_CHECK]
    ↓
[JUDGE_VERDICT]
    funding_decision = "approve" | "deny"
    verdict_reasoning = <explanation>
    ↓
[END]
```

## Relationships

```
TpmCpoDebateState
    ├─ contains → List<TpmCpoDebateMessage>
    ├─ references → prd_input (str)
    ├─ tracks → stage (TpmCpoDebateStage)
    ├─ tracks → speaker ("tpm" | "cpo")
    └─ produces → funding_decision + verdict_reasoning
```

## Validation Rules

| Field | Validation | Rationale |
|-------|------------|-----------|
| prd_input | Required, non-empty | Source material for debate |
| debate_topic | Required, derived from prd_input | Focused debate topic |
| speaker | Must be "tpm" or "cpo" | Prevent invalid state |
| stage | Must follow sequence: opening → rebuttal → counter → final_argument | Enforce debate structure |
| funding_decision | Must be "approve" or "deny" at end | Binary decision required |
