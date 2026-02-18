# Product Committee Clean Architecture Refactoring

**Feature Number:** 017
**Status:** Planning
**Created:** 2025-02-18
**Mission:** software-dev

## Problem Statement

The current `product_committee.py` file (~1970 lines) has severe maintainability issues:
- **Spaghetti code**: Business logic mixed with CLI parsing, file I/O, and subprocess orchestration
- **Code duplication**: Room execution logic duplicated between sync/async implementations (~200 lines each)
- **Unclear responsibilities**: Single file handles argument parsing, room orchestration, report generation, and file management
- **Outdated functions**: TPM reflection feature is stubbed/disabled with TODO comments
- **Impossible to maintain**: Changes in one area inadvertently affect other functionality

## Desired Outcome

A refactored codebase that:
- Uses **Modular Hexagonal Hybrid** architecture based on Clean Architecture principles
- Maintains **100% functional equivalence** - all existing features work as before
- Provides clear boundaries between domain, application, and adapter layers
- Eliminates code duplication and outdated functionality
- Makes future maintenance and evolution straightforward

## User Scenarios & Testing

### Primary Scenario: Run Product Committee Analysis

**Actor:** Product Manager or Technical Lead

**Goal:** Evaluate a PRD document through simulated expert committee debate

**Steps:**
1. User prepares a PRD document (.docx or .txt)
2. User executes command with required parameters:
   ```
   python3 product_committee.py \
     --prd ./test_prd.txt \
     --question 'заработает ли этот проект 100 млн за 2 дня' \
     --max-concurrency 0 \
     --language 'русский кратко, в формате буллетлистов'
   ```
3. System runs 4 debate rooms (TPM vs CPO/CFO/CTO/BDM) in parallel
4. System generates output in `{run-id}` folder:
   - JSON files with full negotiation dialogue for each room
   - `final_report.md` with comprehensive analysis
   - `conclusion.md` with executive summary
5. User reviews results to make go/no-go decision

**Success Criteria:**
- Command completes without errors
- All 4 rooms execute successfully
- Output folder contains all expected files
- Reports are readable and actionable

### Edge Cases & Error Handling

| Scenario | Expected Behavior |
|----------|------------------|
| Missing PRD file | Clear error message pointing to missing file |
| Empty question | Validation error before execution starts |
| Missing role prompts | Room skipped with warning; other rooms continue |
| LLM API timeout | Room fails gracefully; retry logic kicks in |
| Concurrent execution failure | Falls back to sequential if needed |
| File write permission error | Clear error with permission guidance |

## Functional Requirements

### FR1: CLI Interface Preservation
- The system MUST accept all existing CLI arguments: `--prd`, `--question`, `--model`, `--max-retries`, `--max-concurrency`, `--output-dir`, `--roles-dir`, `--run-id`, `--language`, `--verbose`, `--quiet`
- The system MUST validate required arguments before execution
- The system MUST provide clear error messages for invalid inputs

### FR2: Debate Room Orchestration
- The system MUST orchestrate 4 debate rooms: TPM vs CPO, TPM vs CFO, TPM vs CTO, TPM vs BDM
- The system MUST support parallel execution with configurable concurrency (`--max-concurrency`)
- The system MUST support sequential execution when concurrency is set to 1
- The system MUST implement retry logic with exponential backoff for failed rooms
- The system MUST capture full dialogue history for each room in JSON format

### FR3: Document Processing
- The system MUST read and parse .docx files using python-docx
- The system MUST read and parse .txt files with UTF-8, cp1251, iso-8859-1, and windows-1252 encoding support
- The system MUST validate PRD content is readable before processing

### FR4: Output Generation
- The system MUST create a unique `{run-id}` folder for each execution
- The system MUST save JSON files with negotiation dialogue for each completed room
- The system MUST generate `final_report.md` with comprehensive analysis including:
  - Executive summary with room outcomes
  - Room-by-room analysis with winners and judge explanations
  - Full dialogue transcripts
- The system MUST generate `conclusion.md` with executive summary including:
  - Overall verdict (TPM wins vs opponent wins)
  - Room results summary
  - Potential assessment (if available)

### FR5: Metadata Management
- The system MUST track run metadata: timestamps, configuration, room statuses
- The system MUST save `metadata.json` with all run parameters
- The system MUST generate unique run IDs with timestamp and question slug

### FR6: Error Handling & Resilience
- The system MUST continue executing remaining rooms if one room fails
- The system MUST provide detailed error messages in conclusion.md when all rooms fail
- The system MUST categorize errors (Regex, Timeout, JSON, LLM/API) with specific recommendations

### FR7: Language Support
- The system MUST accept `--language` parameter and pass it to underlying debate execution
- The system MUST support language customization for all agent responses

### FR8: Intermediate Reporting
- The system MUST save intermediate `final_report.md` after each room completes
- The system MUST retry file writes with exponential backoff on I/O errors

### FR9: Code Architecture
- The system MUST implement Modular Hexagonal Hybrid architecture with clear layer separation
- The system MUST define domain entities independent of external dependencies
- The system MUST implement use cases in application layer that orchestrate domain logic
- The system MUST provide adapters for LLM clients, file storage, and CLI interfaces
- The system MUST eliminate code duplication between sync and async execution paths

### FR10: Shared Abstractions
- The system MUST provide shared abstractions between `product_committee.py` and `document_debate_cli.py`
- The system MUST define common interfaces for debate execution, report generation, and file operations

### FR11: Removal of Outdated Features
- The system MUST remove the TPM self-reflection feature (currently stubbed/disabled)
- The system MUST remove duplicate code patterns and consolidate logic

## Non-Functional Requirements

### NFR1: Maintainability
- Code MUST follow single responsibility principle
- Each module MUST have clear, focused responsibility
- Changes to one layer MUST NOT require changes to other layers

### NFR2: Testability
- Domain logic MUST be testable without external dependencies
- Adapters MUST be replaceable with mocks for testing
- Use cases MUST have deterministic behavior

### NFR3: Performance
- Parallel execution MUST complete faster than sequential (when concurrency > 1)
- The system MUST support running all 4 rooms simultaneously (max-concurrency = 0)
- File I/O MUST NOT block debate execution

### NFR4: Backward Compatibility
- All existing CLI arguments MUST continue to work
- Output file structure MUST remain unchanged
- Existing test cases MUST continue to pass

## Success Criteria

1. **Functional Equivalence**: All existing functionality works identically to the current implementation
2. **Code Quality Reduction**: `product_committee.py` reduced from ~1970 lines to <500 lines per module
3. **Duplication Elimination**: Zero duplicate code blocks >10 lines between sync/async paths
4. **Architecture Compliance**: Clear separation between domain, application, and adapter layers
5. **Test Coverage**: All domain logic unit testable without external dependencies
6. **Maintainability Score**: New code receives passing grade on maintainability metrics (cyclomatic complexity, coupling)
7. **Performance**: Parallel execution completes in ≤60% of sequential time for 4 rooms
8. **Test Suite**: All existing tests pass without modification

## Key Entities

### CommitteeRun
- **Properties**: run_id, question, prd_path, model, language, max_retries, max_concurrency
- **Behaviors**: validate_configuration, generate_output_path

### DebateRoom
- **Properties**: room_id, participants (PRO/CON), status, verdict, dialogue_history, takeaways
- **Behaviors**: execute, capture_result, check_success

### RoomResult
- **Properties**: status, winner, explanation, takeaways, dialogue, error
- **Behaviors**: to_json, is_successful

### CommitteeReport
- **Properties**: run_metadata, room_results, conclusion
- **Behaviors**: generate_markdown, save_to_file

## Architecture Overview

### Domain Layer
- **Entities**: `CommitteeRun`, `DebateRoom`, `RoomResult`, `CommitteeReport`
- **Value Objects**: `RoomId`, `RunId`, `Verdict`
- **Domain Services**: `RoomExecutionRules`, `ReportGenerationRules`

### Application Layer
- **Use Cases**: `RunProductCommittee`, `GenerateCommitteeReport`, `ExecuteDebateRoom`
- **Ports (Interfaces)**: `DebateExecutor`, `ReportGenerator`, `FileStorage`

### Adapter Layer
- **LLM Adapters**: `DocumentDebateExecutor` (calls document_debate_cli.py)
- **Storage Adapters**: `LocalFileStorage` (creates directories, writes files)
- **CLI Adapter**: `ProductCommitteeCLI` (parses arguments, invokes use case)

### Shared Core
- **Common Interfaces**: Debate execution, report generation, file operations
- **Utilities**: Retry logic, error handling, logging configuration

## Out of Scope

- Refactoring `document_debate_cli.py` internal implementation (only creating shared abstractions)
- Modifying the LangGraph workflow for debate execution
- Changing the output file format or structure
- Adding new features beyond existing functionality
- Performance optimization beyond architectural improvements
- Database or cloud storage integration

## Assumptions

1. The existing `document_debate_cli.py` will continue to work as the underlying debate engine
2. Role prompt files remain in `prompts/roles/` directory
3. Output directory structure remains `committee_output/{run-id}/`
4. Python 3.12+ runtime environment
5. Existing test suite provides adequate coverage for regression testing

## Dependencies

### Internal
- `document_debate_cli.py` - Debate execution engine
- `workflow/document_debate_workflow.py` - LangGraph workflow
- `prompts/roles/*.txt` - Role definitions

### External
- `python-docx` - .docx file parsing
- `langgraph` - Workflow orchestration (indirect via document_debate_cli.py)
- LLM provider (OpenAI, Anthropic, etc.)

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Refactoring breaks existing functionality | High | Comprehensive test suite; feature flags for gradual migration |
| Architecture complexity increases learning curve | Medium | Clear documentation; examples;循序渐进 refactoring |
| Performance degradation from abstraction layers | Low | Benchmarks before/after; optimize hot paths if needed |
| Incomplete shared abstractions require further refactoring | Medium | Iterative approach; validate abstractions with both use cases |
