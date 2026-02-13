# Contract: CPO Node

**Component**: CPO Skeptic Agent
**File**: `nodes/cpo_node.py`

## Interface Specification

### Class: CPONode

```python
from base_component import BaseComponent
from typing import Dict

class CPONode(BaseComponent):
    """Chief Product Officer agent challenging project value and resource allocation."""
    
    def __init__(self, llm_config: dict):
        """Initialize CPO node with LLM configuration."""
        super().__init__(llm_config)
    
    def generate_rebuttal(self, state: TpmCpoDebateState) -> str:
        """Generate rebuttal challenging TPM's opening statement.
        
        Args:
            state: Current debate state with TPM's opening in messages
            
        Returns:
            Rebuttal text questioning completeness, value, resource impact
        """
        pass
    
    def generate_final_argument(self, state: TpmCpoDebateState) -> str:
        """Generate final argument maintaining skeptical position.
        
        Args:
            state: Current debate state with full debate history
            
        Returns:
            Final argument summarizing concerns and recommendation
        """
        pass
```

## Responsibilities

- Challenge TPM's claims about completeness and market readiness
- Question resource allocation impact and team focus risks
- Highlight gaps in product strategy or competitive analysis
- Maintain skeptical position throughout debate
- Recommend deny if concerns outweigh benefits

## Prompt Integration

Uses prompts from `prompts/cpo_prompts.py`:
- `REBUTTAL_PROMPT_TEMPLATE` - Rebuttal guidance
- `FINAL_ARGUMENT_PROMPT_TEMPLATE` - Final argument guidance
