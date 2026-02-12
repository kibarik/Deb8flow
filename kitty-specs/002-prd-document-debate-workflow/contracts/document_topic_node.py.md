# Contract: DocumentTopicNode

**Feature:** 002-prd-document-debate-workflow
**Status:** Draft
**Version:** 1.0

## Purpose

Replace `GenerateTopicNode` in the new document debate workflow. Reads .docx file, extracts text, and generates debate topic from document content.

## Interface

```python
class DocumentTopicNode(BaseComponent):
    def __call__(self, state: DebateState) -> Dict[str, Any]:
        """
        Generates debate topic from document input.

        Args:
            state: DebateState containing document_input field

        Returns:
            Dict with:
                - debate_topic: str - Topic derived from document
                - positions: Dict - PRO/CON positions
                - stage: str - Set to "opening"
                - speaker: str - Set to "pro"
        """
```

## Behavior

### Input Processing

1. Extract `document_input` from state
2. Check if value ends with `.docx` extension
3. If yes, read file using `python-docx.Document`
4. Extract text from all paragraphs: `"\n".join(p.text for p in doc.paragraphs)`
5. Pass extracted text to LLM for topic generation

### Topic Generation

```python
# Execute chain with document text
topic_text = self.execute_chain({"document_text": doc_text})
```

## Prompt Template

Uses existing `topic_generator_prompts.py`:

```python
# SYSTEM_PROMPT
# Keep existing generic debate instruction

# HUMAN_PROMPT
# Extend to include {document_text} variable
topic = self.execute_chain({
    "document_text": doc_text,  # NEW variable
})
```

## Output State

```python
return {
    "debate_topic": topic_text.strip(),
    "positions": {"pro": "In favor", "con": "Against"},
    "stage": "opening",
    "speaker": "pro"
}
```

## Error Handling

| Condition | Behavior |
|-----------|----------|
| `document_input` empty | Log error, exit workflow gracefully |
| `document_input` not .docx and not valid text | Assume pre-extracted text, proceed |
| .docx file corrupted | Catch exception, log error with file path |
| LLM returns empty topic | Retry once, then fail with error |

## Dependencies

- `python-docx` - External library for .docx reading
- `nodes.base_component` - Base class inheritance
- `prompts.topic_generator_prompts` - Existing prompt templates
- `state.debate_state` - Extended DebateState definition
