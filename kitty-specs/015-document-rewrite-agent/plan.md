# Implementation Plan: Document Rewrite Agent

**Branch**: `015-document-rewrite-agent` | **Date**: 2026-02-17 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/kitty-specs/015-document-rewrite-agent/spec.md`

## Summary

Add a `--make-review` CLI flag to the document debate workflow that automatically rewrites source documents based on debate conclusions. After the debate completes and `conclusion.md` is generated, a standalone rewriter agent reads both the original document and conclusion report, applies all recommendations, and outputs an updated document with timestamp-based filename. The implementation uses markdown as an intermediate format for multi-format support (.docx, .md, .txt) and reuses the existing LLM configuration.

## Technical Context

**Language/Version**: Python 3.12+ (existing project standard)
**Primary Dependencies**:
- `python-docx` (existing) for .docx file handling
- `langchain` + `langgraph` (existing) for LLM integration
- `pandoc` or `mammoth` (NEW) for format conversion
**Storage**: File system (output directories: `{run-id}/`)
**Testing**: pytest (existing project standard)
**Target Platform**: Cross-platform CLI (Linux, macOS, Windows)
**Project Type**: CLI utility (single project structure)
**Performance Goals**:
- Rewrite completion within 60 seconds after debate concludes
- Support documents up to 10MB in size
**Constraints**:
- Must not block existing workflow (invoked after completion)
- Must handle errors gracefully without crashing main workflow
- Must preserve file metadata where format allows
**Scale/Scope**:
- Single new agent (~500-1000 LOC)
- 3-4 file format handlers
- Integration with 2 existing CLIs (product_committee.py, document_debate_cli.py)

### Architecture Decisions

**Decision 1: Standalone Script vs LangGraph Node**
- **Choice**: Standalone script (`rewriter_agent.py`)
- **Rationale**: Simplifies implementation, avoids workflow modification, allows asynchronous invocation after debate completion

**Decision 2: LLM Configuration**
- **Choice**: Use same LLM model/config as debate participants
- **Rationale**: Consistency, no additional configuration needed, leverages existing infrastructure

**Decision 3: Format Handling Approach**
- **Choice**: Markdown intermediate format (convert → apply → convert back)
- **Rationale**: Unified processing logic, simpler than format-specific handlers, markdown is already the project's lingua franca

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Requirement | Status | Notes |
|-------------|--------|-------|
| Python 3.12+ | ✅ PASS | Uses existing Python version |
| pytest required | ✅ PASS | Tests will be added for all components |
| Cross-platform | ✅ PASS | CLI with file operations, no platform-specific code |
| Minimal dependencies | ⚠️ VIOLATION | Requires format conversion library (justified below) |
| Self-documenting code | ✅ PASS | Clear function names and structure |
| Spec-driven development | ✅ PASS | Implementation follows spec.md |

**Justification for Minimal Dependencies Violation**:
- Adding `pandoc` (or alternative) is necessary for robust format conversion
- Alternatives considered:
  1. **Manual parsing**: Too complex, error-prone for .docx
  2. **API service**: Adds external dependency, offline requirement
  3. **Limited formats only**: Rejects user requirement for multi-format support
- `pandoc` is industry standard, widely available, and can be bundled
- Single additional dependency is acceptable for this functionality

**All other requirements met**. No blocking violations.

## Project Structure

### Documentation (this feature)

```
kitty-specs/015-document-rewrite-agent/
├── spec.md              # Feature specification
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── rewriter_agent_contract.json
└── tasks.md             # Phase 2 output (created by /spec-kitty.tasks)
```

### Source Code (repository root)

```
src/
├── agents/                  # NEW: AI agent implementations
│   ├── __init__.py
│   ├── rewriter_agent.py    # NEW: Standalone rewriter agent
│   └── base_agent.py        # NEW: Base class for agents (optional)
├── converters/              # NEW: Format conversion utilities
│   ├── __init__.py
│   ├── docx_converter.py    # NEW: .docx ↔ markdown
│   ├── txt_converter.py     # NEW: .txt ↔ markdown
│   └── converter_base.py    # NEW: Base converter interface
├── utils/
│   └── file_utils.py        # MODIFIED: Add file copying, metadata preservation
├── cli/
│   └── cli_extensions.py    # MODIFIED: Add --make-review flag handling
└── prompts/
    └── rewriter_prompts.md  # NEW: System prompts for rewriter agent

tests/
├── unit/
│   ├── agents/              # NEW: Agent unit tests
│   │   └── test_rewriter_agent.py
│   └── converters/          # NEW: Converter unit tests
│       ├── test_docx_converter.py
│       └── test_txt_converter.py
├── integration/
│   └── test_rewriter_integration.py  # NEW: Full workflow integration tests
└── contract/
    └── test_rewriter_contract.py     # NEW: Contract tests

product_committee.py         # MODIFIED: Add --make-review flag and rewriter invocation
document_debate_cli.py       # MODIFIED: Add --make-review flag and rewriter invocation
requirements.txt             # MODIFIED: Add format conversion dependencies
```

**Structure Decision**: Single project structure (existing pattern). The rewriter agent adds new `src/agents/` and `src/converters/` directories following the existing `src/` organization. Tests follow the existing `tests/` structure with unit/integration/contract separation.

## Complexity Tracking

*No violations requiring justification. Minimal dependency addition is justified in Constitution Check.*

## Phase 0: Research Questions

### Outstanding Technical Decisions

1. **Format Conversion Library Selection**
   - **Question**: Which library to use for .docx ↔ markdown conversion?
   - **Options**: `mammoth` (.docx → markdown only), `pandoc` (full bidirectional, external dependency), custom python-docx implementation
   - **Impact**: Code complexity, dependency count, conversion quality

2. **Prompt Strategy for Rewriter**
   - **Question**: How to structure the rewriter prompt for best results?
   - **Options**: Single prompt with full document, chunked processing with section-level prompts, few-shot examples in prompt
   - **Impact**: Token usage, rewrite quality, consistency

3. **Metadata Preservation Strategy**
   - **Question**: How to preserve file metadata (author, dates) across formats?
   - **Options**: Preserve in copy only, preserve in rewritten output, both
   - **Impact**: Implementation complexity, user experience

4. **Error Recovery Mechanism**
   - **Question**: What happens when conversion fails mid-process?
   - **Options**: Fail fast, attempt partial rewrite with warnings, retry with fallback strategy
   - **Impact**: User experience, code complexity

5. **Conclusion Parsing Strategy**
   - **Question**: How to extract actionable recommendations from conclusion.md?
   - **Options**: Parse structured sections, use LLM to extract recommendations, regex patterns
   - **Impact**: Robustness, maintenance burden

## Phase 1: Design Artifacts

### Data Model

**Entities to be defined in `data-model.md`**:
- `RewriteRequest`: Input parameters for rewriter agent
- `RewriteResult`: Output from rewriter agent
- `ConversionResult`: Result from format converters
- `Recommendation`: Parsed recommendation from conclusion.md
- `FileMetadata`: Preserved metadata from source file

### Contracts

**API contracts to be defined in `contracts/`**:
- `rewriter_agent_contract.json`: Input/output contract for rewriter agent
- `converter_interface.json`: Interface for format converters
- `file_operation_contract.json`: File copying and metadata operations

### Quickstart Guide

**User-facing documentation in `quickstart.md`**:
- How to use `--make-review` flag
- Supported file formats
- Expected output structure
- Troubleshooting common issues

## Implementation Phases

### Phase 0: Research (Current)
- [ ] Research format conversion libraries
- [ ] Research prompt engineering strategies
- [ ] Research metadata preservation techniques
- [ ] Document findings in `research.md`

### Phase 1: Design
- [ ] Define data model in `data-model.md`
- [ ] Define contracts in `contracts/`
- [ ] Write quickstart guide
- [ ] Update agent context files

### Phase 2: Task Generation (via `/spec-kitty.tasks`)
- [ ] Generate work packages
- [ ] Create task files with prompts
- [ ] Define implementation order

---

**Plan Status**: Ready for Phase 0 research execution
