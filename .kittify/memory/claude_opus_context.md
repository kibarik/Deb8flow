# Claude Opus Context

**Last Updated**: 2025-02-18
**Purpose**: Project context for Claude Opus agent when working on this codebase

## Project Overview

**Deb8flow** is an AI-powered document debate system using LangGraph workflows. Users provide documents (via .docx files) and the system generates debate topics, runs PRO/CON debates with fact-checking, and provides a judge's verdict. The system also includes a product committee orchestrator that simulates multi-room expert debates.

## Technology Stack

- **Language**: Python 3.12+
- **Framework**: LangGraph for workflow orchestration
- **Architecture**: Modular Hexagonal Hybrid (Clean Architecture) - NEW for feature 017
- **LLM**: OpenAI API (configurable via requesty_llm_config_map)
- **CLI**: argparse with rich for terminal output
- **Testing**: pytest with syrupy for snapshot testing - NEW for feature 017
- **Document Input**: python-docx for .docx file parsing
- **Domain Modeling**: Plain dataclasses (no Pydantic in domain) - NEW for feature 017

**Key Dependencies**:
```
langchain_community==0.3.20
langchain_core==0.3.49
langchain_openai==0.3.11
langgraph==0.3.21
openai==1.69.0
pydantic==2.11.1  # Used only at boundaries (CLI/config/IO), NOT in domain
pytest==8.3.5
syrupy>=4.0.0  # NEW: Added for feature 017 - snapshot testing
python-dotenv==1.1.0
python-docx==1.1.2
rich==14.0.0
typing_extensions>=4.0.0
aiofiles>=24.1.0  # Added for feature 004
tqdm>=4.66.0  # Added for feature 005 - progress indicators
mammoth>=1.8.0  # Added for feature 015 - .docx to markdown conversion
```

## Project Structure

```
Deb8flow/
├── document_debate_cli.py          # Main CLI entry point
├── product_committee.py           # Product committee orchestrator (refactoring)
├── debate_state.py                # TypedDict for DebateState
├── requirements.txt                # Dependencies
│
├── src/                           # Feature modules
│   ├── shared/debate/             # NEW: Feature 017 - Shared debate framework
│   │   ├── domain/                # Domain layer (no external deps)
│   │   │   ├── entities.py        # DebateRoom, Verdict, DebateMessage
│   │   │   ├── value_objects.py   # RoomId, RunId, Speaker, RoomStatus
│   │   │   └── services.py        # Domain rules, validation logic
│   │   ├── application/           # Application layer
│   │   │   ├── ports.py           # DebateExecutor, ReportGenerator, FileStorage
│   │   │   └── use_cases/         # ExecuteDebate, GenerateReport, RunSession
│   │   └── infrastructure/        # Infrastructure (implementation details)
│   │       ├── executors/         # Debate execution adapters
│   │       │   └── cli_executor.py  # Calls document_debate_cli.py
│   │       ├── storage/           # File storage adapters
│   │       │   └── local_storage.py
│   │       └── retry.py           # Retry logic with exponential backoff
│   │
│   ├── committee/                 # NEW: Feature 017 - Product committee specific
│   │   ├── domain/                # Committee-specific entities
│   │   │   └── entities.py        # CommitteeRun, CommitteeRoom, CommitteeReport
│   │   ├── application/           # Committee use cases
│   │   │   └── run_committee.py   # RunProductCommittee use case
│   │   └── adapters/              # Committee adapters
│   │       ├── cli.py             # CLI argument parsing and orchestration
│   │       └── reports/           # Report generation
│   │           ├── final_report.py
│   │           └── conclusion.py
│   │
│   ├── output/                   # Feature 004 - debate output recording
│   │   ├── __init__.py
│   │   ├── async_file_writer.py    # Async file writer with error handling
│   │   └── transcript_formatter.py  # Plain text formatting
│   │
│   ├── progress/                 # Feature 005 - CLI progress indicators
│   │   ├── __init__.py
│   │   ├── progress_manager.py     # ProgressManager class with tqdm
│   │   └── cli_output.py          # CLIOutput class for verbosity filtering
│   │
│   ├── agents/                    # Feature 015 - AI agent implementations
│   │   ├── __init__.py
│   │   ├── rewriter_agent.py       # Standalone document rewriter agent
│   │   └── base_agent.py          # Base class for agents (optional)
│   │
│   └── converters/                # Feature 015 - Format conversion utilities
│       ├── __init__.py
│       ├── docx_converter.py       # .docx ↔ markdown conversion
│       ├── txt_converter.py        # .txt ↔ markdown conversion
│       └── converter_base.py       # Base converter interface
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
    ├── snapshots/                 # NEW: Feature 017 - Snapshot tests
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

## Feature 005: CLI Progress Indicators

**New in feature 005**: Add real-time progress tracking to CLI workflow using tqdm

**Key Design Decisions**:
- Uses `tqdm` (with `tqdm.rich`) for progress bars
- Three verbosity levels: quiet, default, verbose
- `ProgressManager` passed through workflow state
- Progress display integrated into existing nodes

**Integration Points**:
- `document_debate_cli.py`: Add `--verbose` and `--quiet` flags
- `workflow/`: Accept optional `progress_manager` parameter
- `nodes/`: Check `state["_progress_manager"]` and use if present
- `src/progress/`: New module for `ProgressManager` and `CLIOutput`

---

## Feature 015: Document Rewrite Agent

**New in feature 015**: Add `--make-review` flag to automatically rewrite source documents based on debate conclusions

**Key Design Decisions**:
- Standalone script invoked after workflow completion (NOT a LangGraph node)
- Uses same LLM configuration as debate participants
- Markdown intermediate format for multi-format support (.docx, .md, .txt)
- `mammoth` library for .docx → markdown, custom `python-docx` for markdown → .docx
- Graceful error handling (preserves debate results even if rewrite fails)

**Integration Points**:
- `product_committee.py`: Add `--make-review` flag and rewriter invocation
- `document_debate_cli.py`: Add `--make-review` flag and rewriter invocation
- `src/agents/`: New module for `rewriter_agent.py`
- `src/converters/`: New module for format converters
- `prompts/rewriter_prompts.md`: System prompts for rewriter agent

**Output Structure**:
```
{run-id}/
├── conclusion.md                    # Debate conclusions
├── {original_name}.{ext}            # Original copy (preserved)
├── {original_name}_{timestamp}.{ext} # Rewritten document
└── file_metadata.json               # Preserved metadata
```

---

## Feature 017: Product Committee Clean Architecture Refactoring

**New in feature 017**: Refactor product_committee.py using Modular Hexagonal Hybrid architecture (Clean Architecture)

**Key Design Decisions**:
- **Shared debate framework** in `src/shared/debate/` used by both product_committee and document_debate
- **Domain layer** uses plain dataclasses (no Pydantic) for purity and testability
- **Port interfaces** using `typing.Protocol` for dependency inversion
- **Async-only execution** with sync wrapper for CLI (eliminates sync/async duplication)
- **Snapshot testing** with syrupy for CLI output validation
- **File I/O via asyncio.to_thread** for non-blocking writes
- **Pydantic only at boundaries** (CLI/config/IO validation, not in domain)

**Architecture Layers**:
```
Domain Layer (src/shared/debate/domain/, src/committee/domain/)
  - Pure business logic, no external dependencies
  - Entities: DebateRoom, Verdict, CommitteeRun, etc.
  - Value Objects: RoomId, RunId, Speaker, RoomStatus
  - Plain dataclasses only

Application Layer (src/shared/debate/application/, src/committee/application/)
  - Use cases orchestrate domain logic
  - Port interfaces: DebateExecutor, ReportGenerator, FileStorage
  - No implementation details

Infrastructure Layer (src/shared/debate/infrastructure/, src/committee/adapters/)
  - CliDebateExecutor: Calls document_debate_cli.py as subprocess
  - LocalFileStorage: File I/O with asyncio.to_thread
  - CommitteeReportGenerator: Markdown report generation
  - Pydantic models for CLI validation

CLI Layer (product_committee.py, document_debate_cli.py)
  - Argument parsing and validation
  - Thin orchestration layer
  - Delegates to use cases
```

**Migration Order** (core-to-edges):
1. Domain entities (shared framework)
2. Debate execution abstraction
3. Report generation system
4. CLI and orchestration layer

**Integration Points**:
- `src/shared/debate/`: New shared debate framework
- `src/committee/`: Product committee specific logic
- `product_committee.py`: Reduced to ~200 lines (CLI + orchestration)
- `document_debate_cli.py`: Migrated to use shared framework (minimal changes)

**Testing Strategy**:
- Parallel test & refactor with snapshot testing
- Unit tests for domain (no external dependencies)
- Integration tests for use cases (with mock adapters)
- Snapshot tests for CLI output validation

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
