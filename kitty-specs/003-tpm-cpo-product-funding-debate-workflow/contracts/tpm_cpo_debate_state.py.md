# Contract: TpmCpoDebateState

**Component**: State Management
**File**: `debate_state.py` (extend existing file)

## Interface Specification

### TypedDict: TpmCpoDebateState

```python
from typing import TypedDict, List, Dict, Literal, NotRequired

TpmCpoDebateStage = Literal["opening", "rebuttal", "counter", "final_argument"]

class TpmCpoDebateMessage(TypedDict):
    """A single message in the TPM-CPO debate."""
    speaker: str  # "tpm" or "cpo"
    content: str  # Message text
    validated: bool  # Fact-check result
    stage: TpmCpoDebateStage  # Debate stage

class TpmCpoDebateState(TypedDict):
    """State for TPM-CPO funding debate workflow."""
    debate_topic: str
    positions: Dict[str, str]
    messages: List[TpmCpoDebateMessage]
    prd_input: str  # PRD text content
    stage: NotRequired[str]
    speaker: NotRequired[str]
    times_tpm_fact_checked: NotRequired[int]
    times_cpo_fact_checked: NotRequired[int]
    funding_decision: NotRequired[str]  # "approve" or "deny"
    verdict_reasoning: NotRequired[str]
```

## Implementation Notes

- Add to existing `debate_state.py` file
- Follow pattern of existing `DebateState` and `DebateMessage`
- The `prd_input` field is the key addition for PRD-based debates
