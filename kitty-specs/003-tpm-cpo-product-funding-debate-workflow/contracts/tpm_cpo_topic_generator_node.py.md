# Contract: TPM-CPO Topic Generator Node

**Component**: PRD Topic Extraction
**File**: `nodes/tpm_cpo_topic_generator_node.py`

## Interface Specification

### Class: TpmCpoTopicGeneratorNode

```python
from base_component import BaseComponent
from typing import Dict

class TpmCpoTopicGeneratorNode(BaseComponent):
    """Generates debate topic from PRD input text."""
    
    def __init__(self, llm_config: dict):
        """Initialize topic generator with LLM configuration."""
        super().__init__(llm_config)
    
    def generate_topic(self, prd_text: str) -> str:
        """Extract and format the core project proposal from PRD.
        
        Args:
            prd_text: Full PRD document text content
            
        Returns:
            Concise topic statement summarizing the project proposal
            Format: "Should [project description] receive funding and be launched?"
        """
        pass
```

## Responsibilities

- Parse PRD text to identify the core project concept
- Extract key elements: problem, solution, target market, value proposition
- Format as a debatable topic question
- Handle variable PRD lengths (short idea to full specification)

## Prompt Integration

Uses prompts from `prompts/tpm_cpo_topic_generator_prompts.py`:
- `TOPC_GENERATION_PROMPT_TEMPLATE` - Topic extraction guidance

## Examples

| Input PRD | Output Topic |
|------------|-------------|
| "We should build an AI-powered email sorter that saves users 2 hours/week" | "Should an AI-powered email automation tool that saves users 2 hours weekly receive funding?" |
| Full 20-page PRD for B2B analytics platform | Concise summary of core value proposition and funding request |
