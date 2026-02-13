# Claude Opus Context

**Last Updated**: 2025-02-14
**Purpose**: Project context for Claude Opus agent when working on this codebase

## Project Overview

**Deb8flow** is an AI-powered document debate system using LangGraph workflows. Users provide documents (via .docx files) and the system generates debate topics, runs PRO/CON debates with fact-checking, and provides a judge's verdict.

## Technology Stack

- **Language**: Python 3.11+
- **Framework**: LangGraph for workflow orchestration
- **LLM**: OpenAI API (configurable via requesty_llm_config_map)
- **CLI**: argparse with rich for terminal output
- **Testing**: pytest
- **Document Input**: python-docx for .docx file parsing

**Key Dependencies**:
```
langchain_community==0.3.20
langchain_core==0.3.49
langchain_openai==0.3.11
langgraph==0.3.21
openai==1.69.0
pydantic==2.11.1
pytest==8.3.5
python-dotenv==1.1.0
python-docx==1.1.2
rich==14.0.0
typing_extensions>=4.0.0
aiofiles>=24.1.0  # NEW: Added for feature 004
```

## Project Structure

```
Deb8flow/
├── document_debate_cli.py          # Main CLI entry point
├── debate_state.py                # TypedDict for DebateState
├── requirements.txt                # Dependencies
│
├── src/                           # NEW: Feature modules
│   └── output/                   # NEW: Feature 004 - debate output recording
│       ├── __init__.py
│       ├── async_file_writer.py    # Async file writer with error handling
│       └── transcript_formatter.py  # Plain text formatting
│
├── nodes/                         # LangGraph node implementations
│   ├── __init__.py
│   ├── document_topic_node.py       # Generates topic from document
│   ├── pro_debater_node.py         # PRO debater
│   ├── con_debater_node.py         # CON debater
│   ├── judge_node.py               # Judge verdict
│   ├── debate_moderator_node.py    # Moderates debate flow
│   ├── fact_checker_node.py        # Fact checking
│   └── fact_check_router_node.py   # Routes based on fact check results
│
├── workflow/
│   ├── debate_workflow.py           # Base debate workflow
│   └── document_debate_workflow.py  # Document-specific debate workflow
│
├── prompts/                        # LLM prompts for each node
│   ├── topic_generator_prompts.py
│   ├── pro_debater_prompts.py
│   ├── con_debater_prompts.py
│   ├── judge_prompts.py
│   └── ...
│
├── configurations/
│   └── llm_config.py              # LLM configuration mapping
│
└── tests/
    ├── unit/
    ├── integration/
    └── e2e/                        # E2E tests for workflows
```

## Key Patterns

### State Management

All workflow nodes share and mutate a `DebateState` TypedDict:

```python
class DebateState(TypedDict):
    debate_topic: str
    positions: dict[str, str]
    messages: list[dict[str, Any]]
    stage: str  # "opening", "rebuttal", "final_argument"
    # ... optional fields for document input, direct_topic, etc.
```

### Node Pattern

Each node is a class with a `__call__` method that accepts state and returns state updates:

```python
class ProDebaterNode:
    def __init__(self, llm_config: dict):
        self.llm = llm_config

    def __call__(self, state: DebateState) -> dict:
        # ... generate argument ...
        return {"messages": state["messages"] + [new_message]}
```

### Async Workflow

The main CLI and workflow are fully async:

```python
async def main():
    workflow = DocumentDebateWorkflow()
    result = await workflow.run(initial_state=initial_state)

if __name__ == "__main__":
    asyncio.run(main())
```

## Feature 004: Non-Blocking Debate Output

**New in feature 004**: Add `--output` flag to record debate transcripts to file

**Key Design Decisions**:
- Uses `aiofiles` for native async file I/O
- Writes are queued and processed in background task
- Write failures are logged but don't crash the debate
- Plain text format: `[SPEAKER] ISO_TIMESTAMP\ncontent\n\n`

**Integration Points**:
- `document_debate_cli.py`: Add `--output` argument, create `AsyncFileWriter`
- Node functions: Accept optional `output_writer` parameter, write each message
- `src/output/`: New module for output recording logic

---

## DO NOT EDIT BETWEEN THESE MARKERS - AUTOMATIC UPDATES

<!-- SPEC_KITTY_AUTO_UPDATE_START -->
<!-- SPEC_KITTY_AUTO_UPDATE_END -->

## Manual Additions

<!-- SPEC_KITTY_MANUAL_START -->
*Add project-specific context that should persist between updates here*

**Important Notes**:
- Russian language is used in some user prompts/specs
- The workflow supports both document-based topics and direct topic input
- Fact checking is integrated into the debate flow (not separate)
<!-- SPEC_KITTY_MANUAL_END -->
