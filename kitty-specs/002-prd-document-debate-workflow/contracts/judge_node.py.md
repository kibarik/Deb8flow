# Contract: JudgeNode Extension

**Feature:** 002-prd-document-debate-workflow
**Status:** Draft
**Version:** 1.0

## Purpose

Extend existing `JudgeNode` to evaluate document viability in addition to rhetorical performance.

## Changes

### Existing JudgeNode (in `nodes/judge_node.py`)

```python
class DebateVerdict(BaseModel):
    winner: Literal["pro", "con"]
    justification: str
```

### Extended Verdict Model

```python
class DebateVerdict(BaseModel):
    winner: Literal["pro", "con"]
    justification: str
    document_viability: str  # NEW: Business viability assessment
```

## Prompt Extensions

### Judge Human Prompt

```python
JUDGE_HUMAN_PROMPT = """
Debate topic: {debate_topic}

Document content:
{document_text}

Here is the debate so far:
{debate_history}

You are the Judge. Evaluate the debate and provide a verdict.

Consider BOTH:
1. Rhetorical performance - which side argued more persuasively?
2. Document viability - is this product strategy worth presenting to management?

Provide:
- Winner: pro or con
- Justification: concise explanation of your decision
- Document viability: clear assessment of the document's business merit (e.g., "Ready for presentation with revisions", "Needs significant rework", "Fundamentally flawed")
"""
```

## Chain Invocation

```python
result = self.execute_chain({
    "debate_topic": debate_topic,
    "document_text": state.get("document_input", ""),  # NEW
    "debate_history": debate_history
})
```

## Output State

```python
return {
    "judge_verdict": result.dict(),  # Now includes document_viability
    "messages": messages + [{
        "speaker": SPEAKER_JUDGE,
        "content": f"WINNER: {result.winner.upper()}\n\nREASON: {result.justification}\n\nDOCUMENT VIABILITY: {result.document_viability}",
        "validated": True,
        "stage": "verdict"
    }]
}
```

## Testing

- Verify verdict includes all three components (winner, justification, viability)
- Test with documents of varying quality
- Ensure viability assessment is actionable for product managers
