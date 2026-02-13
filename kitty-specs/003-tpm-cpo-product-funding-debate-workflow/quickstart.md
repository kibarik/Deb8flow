# Quickstart: TPM-CPO Product Funding Debate Workflow

**Feature**: 003-tpm-cpo-product-funding-debate-workflow

## Overview

The TPM-CPO debate workflow evaluates product funding proposals through structured debate between a Technical Product Manager (advocate) and Chief Product Officer (skeptic), with fact-checking and a final funding decision.

## Usage

### Basic Example

```python
from workflow.tpm_cpo_debate_workflow import TmpCpoDebateWorkflow

# Initialize and run workflow
workflow = TmpCpoDebateWorkflow()
prd_text = """
We should build an AI-powered email automation tool.
Market: 50M knowledge workers spending 2 hours/day on email
Solution: AI prioritization and response drafting
ROI: Save 10 hours/week per user, price $50/month
"""

result = await workflow.run(prd_input=prd_text)

# Access verdict
print(result["funding_decision"])  # "approve" or "deny"
print(result["verdict_reasoning"])  # Explanation
```

### Output Structure

```python
{
    "debate_topic": "Should an AI-powered email automation tool...",
    "prd_input": "<original PRD text>",
    "messages": [
        {"speaker": "tpm", "content": "...", "validated": true, "stage": "opening"},
        {"speaker": "cpo", "content": "...", "validated": true, "stage": "rebuttal"},
        # ... more messages
    ],
    "funding_decision": "approve",  # or "deny"
    "verdict_reasoning": "The TPM demonstrated clear market need..."
}
```

## Debate Flow

1. **Topic Generation**: Extract project proposal from PRD
2. **TPM Opening**: Advocate for project launch
3. **Fact-Check**: Verify TPM's claims
4. **CPO Rebuttal**: Challenge completeness and resource impact
5. **Fact-Check**: Verify CPO's claims
6. **TPM Counter**: Address CPO's concerns
7. **Fact-Check**: Verify TPM's counter
8. **CPO Final**: Summarize skeptical position
9. **Fact-Check**: Verify final claims
10. **Judge Verdict**: Render funding decision (Approve/Deny)

## Input Requirements

- **Format**: Plain text (any PRD content pasted as text)
- **Length**: Handles short ideas to full specifications
- **Content**: Should describe problem, solution, market, and value proposition

## Verdict Criteria

| Decision | Criteria |
|----------|----------|
| **Approve** | TPM demonstrates: clear market need, technical feasibility, business value; addresses CPO's concerns |
| **Deny** | CPO identifies: critical gaps, unrealistic assumptions, resource risks that TPM cannot address |
