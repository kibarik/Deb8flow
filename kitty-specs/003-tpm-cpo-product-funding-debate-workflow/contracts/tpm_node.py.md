# Contract: TPM Node

**Component**: TPM Advocate Agent
**File**: `nodes/tpm_node.py`

## Interface Specification

### Class: TPMNode

```python
from base_component import BaseComponent
from typing import Dict

class TPMNode(BaseComponent):
    """Technical Product Manager agent advocating for project funding."""
    
    def __init__(self, llm_config: dict):
        """Initialize TPM node with LLM configuration."""
        super().__init__(llm_config)
    
    def generate_opening(self, state: TpmCpoDebateState) -> str:
        """Generate opening statement advocating for project funding.
        
        Args:
            state: Current debate state with prd_input and debate_topic
            
        Returns:
            Opening statement text
        """
        pass
    
    def generate_counter(self, state: TpmCpoDebateState) -> str:
        """Generate counter-argument to CPO's rebuttal.
        
        Args:
            state: Current debate state with CPO's rebuttal in messages
            
        Returns:
            Counter-argument text
        """
        pass
```

## Responsibilities

- Generate opening statement highlighting project strengths
- Present market opportunity, technical feasibility, business value
- Counter CPO's concerns with additional evidence
- Advocate for resource allocation and funding approval

## Prompt Integration

Uses prompts from `prompts/tpm_prompts.py`:
- `OPENING_PROMPT_TEMPLATE` - Opening statement guidance
- `COUNTER_PROMPT_TEMPLATE` - Counter-argument guidance
