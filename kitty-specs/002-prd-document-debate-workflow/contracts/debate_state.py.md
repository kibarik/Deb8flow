# Contract: DebateState Extension

**Feature:** 002-prd-document-debate-workflow
**Status:** Draft
**Version:** 1.0

## Purpose

Extend existing `DebateState` TypedDict to support document input for the new document debate workflow.

## Changes

### Existing Definition (in `debate_state.py`)

```python
class DebateState(TypedDict):
    debate_topic: str
    positions: Dict[str, str]
    messages: NotRequired[List[DebateMessage]]
    stage: NotRequired[str]
    speaker: NotRequired[str]
    opening_statement_pro_agent: NotRequired[str]
    times_pro_fact_checked: NotRequired[int]
    times_con_fact_checked: NotRequired[int]
```

### New Definition

Add the following field to `DebateState`:

```python
class DebateState(TypedDict):
    # ... existing fields ...
    document_input: NotRequired[str]  # NEW: File path or pre-extracted text
```

## Usage

### In main.py

```python
# Pass document via initial_state
workflow = DocumentDebateWorkflow()
workflow_result = await workflow.run(
    initial_state={"document_input": doc_text}
)
```

### In DocumentTopicNode

```python
# Access document content
doc_text = state.get("document_input", "")

# If it's a file path, read it
if doc_text.endswith(".docx"):
    doc = Document(doc_text)
    doc_text = "\n".join(p.text for p in doc.paragraphs)
```

### In Debater Nodes

```python
# Access for prompts
result = chain.invoke({
    "debate_topic": debate_topic,
    "document_text": state.get("document_input", ""),  # NEW variable
    "opponent_statement": opponent_msg,
    "debate_history": debate_history
})
```

## Backward Compatibility

- Existing `debate_workflow.py` continues to use original `DebateState`
- New `document_debate_workflow.py` uses extended state
- Both workflows operate independently

## Testing

- Verify extended state serializes correctly with LangGraph
- Test with both file paths and pre-extracted text
- Ensure `document_input` propagates through all stages
