# Contract: TPM-CPO Judge Prompts

**Component**: Funding Decision Judge Prompts
**File**: `prompts/tpm_cpo_judge_prompts.py`

## Interface Specification

```python
VERDICT_PROMPT_TEMPLATE = """
You are the judge evaluating a product funding debate.

Context:
- Project Topic: {debate_topic}
- PRD Input: {prd_input}
- Full Debate Transcript: {debate_history}

Your role: Render a funding decision (Approve or Deny) with clear reasoning.

Evaluate both sides:
- TPM: Did they demonstrate market need, technical feasibility, and business value?
- CPO: Did they identify real risks, resource concerns, or completeness gaps?

Decision format:
- Funding Decision: [APPROVE | DENY]
- Reasoning: [2-4 paragraphs explaining your decision]

If TPM made a compelling case that addresses CPO's concerns, Approve.
If CPO identified critical gaps or risks TPM couldn't address, Deny.
"""
```

## Prompt Design Notes

- Binary decision required: APPROVE or DENY
- Reasoning must reference specific arguments from debate
- Consider both evidence quality and rhetorical effectiveness
