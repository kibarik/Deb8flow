# Contract: Debater Prompts Extension

**Feature:** 002-prd-document-debate-workflow
**Status:** Draft
**Version:** 1.0

## Purpose

Extend existing PRO and CON debater prompts to include document context for specialized document debate roles.

## Changes

### Existing Prompts (in `prompts/pro_debater_prompts.py`, `prompts/con_debater_prompts.py`)

```python
# Existing variables
{debate_topic}
{opponent_statement}
{debate_history}

# NEW variable to add
{document_text}
```

### PRO Agent Role

**Position:** Defend the document's validity, strengths, opportunities, and positive aspects
**Context:** Acting as product manager presenting this strategy to management

### CON Agent Role

**Position:** Critique the document's weaknesses, risks, gaps, and concerns
**Context:** Acting as critical stakeholder identifying flaws before management review

## Prompt Extensions

### PRO Opening

```python
OPENING_HUMAN_PROMPT = """
Debate topic: {debate_topic}

Document content:
{document_text}

You are arguing the PRO side. Your role is to DEFEND this document as a valid product strategy worth presenting to management.

Give your opening statement. Highlight the document's strengths, opportunities, and positive aspects.
Keep it concise, persuasive, and factual.
"""
```

### PRO Counter

```python
COUNTER_HUMAN_PROMPT = """
Debate topic: {debate_topic}

Document content:
{document_text}

Your opponent (CON) recently said:
"{opponent_statement}"

Here is the debate so far:
{debate_history}

You are the PRO side. Your role is to DEFEND this document against criticism.

Address your opponent's key points directly and reinforce the document's strengths.
Keep your tone formal and factual.
"""
```

### CON Rebuttal

```python
REBUTTAL_HUMAN_PROMPT = """
Debate topic: {debate_topic}

Document content:
{document_text}

Your opponent (PRO side) recently stated:
"{opponent_statement}"

You are representing the CON position. Your role is to CRITIQUE this document and identify its weaknesses.

Craft a clear and logical rebuttal. Use facts, reasoning, and persuasive language to highlight flaws, risks, or gaps in the document.

Keep your tone formal and focused.
"""
```

### CON Final Argument

```python
FINAL_ARGUMENT_HUMAN_PROMPT = """
Debate topic: {debate_topic}

Document content:
{document_text}

Here is the debate so far:
{debate_history}

You are the CON side. This is your final statement.

Summarize the document's weaknesses and reinforce your strongest criticisms.
Deliver a clear and impactful closing statement.
"""
```

## System Prompt

Keep existing `SYSTEM_PROMPT` from both files - no changes needed for generic debate instruction.

## Implementation

Update chain invocations in debater nodes to include `document_text`:

```python
result = chain.invoke({
    "debate_topic": debate_topic,
    "document_text": state.get("document_input", ""),  # NEW
    "opponent_statement": opponent_msg,
    "debate_history": debate_history
})
```

## Validation

- `{document_text}` is optional (debate works without it)
- When present, agents must reference specific document content
- Fact-checker validates claims about document content
