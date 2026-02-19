# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Deb8flow** is a multi-agent AI debate framework built with LangGraph. It simulates structured debates between two autonomous AI agents (PRO and CON), orchestrated by a moderator and finalized with a judge's verdict. The system includes fact-checking capabilities and supports both standard and document-based debates.

**Project Goal:** Rapid development and hypothesis validation through AI agent debates.

## Development Commands

### Environment Setup
```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file with required keys:
# OPENAI_API_KEY=your_openai_key_here
# Optional: LANGCHAIN_API_KEY, LANGCHAIN_TRACING_V2, LANGCHAIN_PROJECT
# Optional for Requesty (DeepSeek): REQ_API_KEY
```

### Running the Application
```bash
# Standard debate (uses default topic generator)
python main.py

# Document-based debate with direct text topic
python3 document_debate_cli.py --text "GitHub полезен для разработчиков"

# Document-based debate with .docx file
python3 document_debate_cli.py --docx '/path/to/document.docx' --request "какой потенциал у этого проекта?"
```

### Testing
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_full_workflow.py

# Run with coverage (if coverage installed)
pytest --cov=.

# Run specific test
pytest tests/test_full_workflow.py::test_specific_function
```

## Architecture Overview

### Core Architectural Patterns

1. **BaseComponent Pattern**: All nodes inherit from `BaseComponent` (in `nodes/base_component.py`), which provides:
   - Multi-LLM support (OpenAI, Azure OpenAI, Zhipu AI, Requesty/DeepSeek)
   - Token tracking and retry logic with exponential backoff
   - Rich-formatted logging
   - Chain creation methods for structured/unstructured outputs
   - OpenTelemetry tracing support

2. **LangGraph State Machine**: The debate flow is orchestrated via LangGraph's `StateGraph`:
   - State is managed through `DebateState` (TypedDict in `debate_state.py`)
   - Transitions between stages are controlled by router nodes using `Command` objects
   - Supports both standard (`workflow/debate_workflow.py`) and document-based (`workflow/document_debate_workflow.py`) flows

3. **Debate Stages**:
   ```
   topic_generation → opening (PRO) → fact_check → rebuttal (CON) → fact_check
   → counter (PRO) → fact_check → final_argument (CON) → fact_check → judge_verdict
   ```

### Key Components

- **`nodes/`**: LangGraph node implementations
  - `base_component.py`: Base class for all nodes
  - `topic_generator_node.py`: Generates debate topics
  - `pro_debater_node.py` / (implicit CON node): PRO/CON debaters
  - `fact_checker_node.py`: Validates claims with web search
  - `fact_check_router_node.py`: Routes based on fact-check results (restatement vs continuation)
  - `debate_moderator_node.py`: Orchestrates debate flow and stage transitions
  - `judge_node.py`: Determines debate winner

- **`configurations/`**:
  - `llm_config.py`: LLM provider configurations (OpenAI, Azure, Zhipu AI, Requesty)
  - `debate_constants.py`: Debate stage and speaker constants

- **`prompts/`**: System and human prompts for each agent role

- **`workflow/`**: LangGraph workflow definitions for both debate types

### Fact-Checking System

- Integrated after **every speaker's turn**
- Uses OpenAI's web search capability for claim validation
- Tracks fact-check failures per agent (max 3 before automatic disqualification)
- Forces correction/restatement of false statements via router logic

### Document Intelligence

- The `document_debate_cli.py` can analyze .docx files to generate relevant debate topics
- Uses the topic generator node with document context as input
- Supports both `--text` (direct topic) and `--docx` (document file) input modes

## Project Standards (from `.kittify/memory/constitution.md`)

### Technical Standards
- **Python 3.12+** with modern CLI libraries (asyncio support)
- **pytest** is required for all features
- Cross-platform support (Linux, macOS, Windows)
- Performance is not critical; prioritize rapid iteration

### Development Conventions
- **Spec-driven development**: Always work from written specifications (use spec-kitty)
- **TDD (Test-Driven Development)**: Write tests first to prevent bugs
- Minimal dependencies: Each dependency adds complexity and risk
- Self-documenting code preferred over extensive comments

### Code Quality
- Self-merge after CI passes for maintainers
- Code review checklist: **specification compliance** + **tests**
- Follow PEP 8 guidelines
- Use typed dictionaries for state management

### Testing Strategy
- End-to-end tests verify full debate workflows
- Contract tests validate state definitions
- Mock LLMs for predictable test behavior
- Current status: 19/19 E2E tests passing (see `E2E_TEST_REPORT.md`)

## Multi-LLM Configuration

The system supports multiple LLM providers via configuration classes in `configurations/llm_config.py`:
- `OpenAILLMConfig`: Standard OpenAI models
- `AzureOpenAILLMConfig`: Azure OpenAI deployments
- `ZaiLLMConfig`: Zhipu AI models
- `RequestyLLMConfig`: Custom API endpoints (e.g., DeepSeek)

When adding LLM support or modifying node behavior, extend `BaseComponent` and leverage its built-in chain creation methods.

## Workflow Modification Guidelines

When modifying debate flows:
1. Update the relevant workflow file in `workflow/`
2. Ensure state transitions use proper `Command` objects
3. Add/update corresponding prompts in `prompts/`
4. Add tests in `tests/` covering the new flow
5. Update `debate_state.py` if state structure changes

## Adding New Nodes

1. Inherit from `BaseComponent` in `nodes/base_component.py`
2. Implement the `__call__` method with proper state handling
3. Add prompts to `prompts/` directory
4. Integrate into the appropriate workflow in `workflow/`
5. Add tests for the new node

## Related Documentation

- `README.md`: Project overview and usage examples
- `CONTRIBUTING.md`: Contribution guidelines and code style
- `.kittify/memory/constitution.md`: Full project constitution and standards
- `E2E_TEST_REPORT.md`: End-to-end test results
