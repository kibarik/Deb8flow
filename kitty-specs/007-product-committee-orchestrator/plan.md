# Implementation Plan: Product Committee Orchestrator

**Branch**: `007-product-committee-orchestrator` | **Date**: 2026-02-14 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/kitty-specs/007-product-committee-orchestrator/spec.md`

## Summary

Build a CLI orchestrator (`product_committee.py`) that runs four sequential debate rooms (TPM vs CPO/CFO/CTO/BDM) using the existing `document_debate_cli.py` script, followed by a TPM self-reflection step. The system handles partial failures gracefully, produces structured JSON outputs per room, and generates a comprehensive markdown report with multi-perspective analysis and actionable recommendations.

**Technical Approach (MVP → Target)**:
- **MVP**: Subprocess invocation of `document_debate_cli.py` for fastest delivery
- **Target**: Refactor to shared library (`debate_core.py`) with clean `run_debate()` API
- **PRD Handling**: Skip compression for MVP (pass full text to self-reflection)
- **Testing**: Unit tests for orchestrator logic + minimal E2E smoke tests
- **Logging**: Configurable via `--verbose`/`--quiet` flags with sensible default

## Technical Context

**Language/Version**: Python 3.12+
**Primary Dependencies**: Existing LangGraph-based debate system (`document_debate_cli.py`), click/argparse for CLI
**Storage**: File-based JSON outputs (room results, metadata, reflection) + markdown report
**Testing**: pytest for unit tests, minimal E2E smoke tests with real LLM
**Target Platform**: Cross-platform (Linux, macOS, Windows) - local execution
**Project Type**: Single CLI utility extending existing debate framework
**Performance Goals**: Full run (4 rooms + reflection) in ~5-10 minutes on local laptop (soft target, not hard SLA)
**Constraints**: Sequential execution only (no parallel rooms in MVP), graceful degradation on partial failures, retry logic (1-2 retries per room)
**Scale/Scope**: Single orchestrator script, 4 role prompt files, output directory with timestamped runs, metadata tracking

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Standards from [constitution.md](.kittify/memory/constitution.md)**:

### ✓ Languages and Frameworks
- **Python 3.12+** with modern CLI libraries - **COMPLIANT**: Feature uses Python 3.12+ consistent with project standard
- Modern Python stack for CLI applications - **COMPLIANT**: Will use existing CLI patterns from `document_debate_cli.py`

### ✓ Testing Requirements
- **pytest is required** for all features - **COMPLIANT**: Planning includes pytest-based unit tests + minimal E2E smoke tests
- No strict coverage requirement, but tests should cover critical paths - **COMPLIANT**: Focus on orchestrator logic coverage (sequential execution, retries, status handling)

### ✓ Performance and Scale
- Performance is **not critical** for prototype development - **COMPLIANT**: 5-10 minute runtime is acceptable for orchestration layer
- Rapid iteration and hypothesis testing are prioritized over optimization - **COMPLIANT**: MVP uses subprocess for fastest delivery

### ✓ Deployment and Constraints
- **pip installable** package - **COMPLIANT**: New CLI script integrates with existing package structure
- **Cross-platform**: Linux, macOS, Windows - **COMPLIANT**: File-based outputs work across platforms

### ✓ Code Quality
- **Self-documenting code** preferred - **COMPLIANT**: Will follow existing code patterns from debate system
- **Spec-driven development**: Always work from written specifications - **COMPLIANT**: Implementation follows approved spec.md
- **TDD (Test-Driven Development)**: Write tests first to prevent bugs - **COMPLIANT**: Unit tests written before orchestrator logic

**Constitution Status**: ✓ COMPLIANT - No violations detected

## Project Structure

### Documentation (this feature)

```
kitty-specs/007-product-committee-orchestrator/
├── spec.md              # Feature specification (completed)
├── plan.md              # This file (/spec-kitty.plan command output)
├── research.md          # Phase 0 output - to be created
├── data-model.md        # Phase 1 output - to be created
├── quickstart.md        # Phase 1 output - to be created
├── contracts/           # Phase 1 output - to be created (JSON schemas)
├── checklists/
│   └── requirements.md  # Requirements validation checklist
└── meta.json            # Feature metadata
```

### Source Code (repository root)

```
project_root/
├── product_committee.py              # New CLI orchestrator (main entry point)
├── prompts/
│   └── roles/
│       ├── tpm.txt                    # TPM role prompt (must exist)
│       ├── cpo.txt                    # CPO role prompt
│       ├── cfo.txt                    # CFO role prompt
│       ├── cto.txt                    # CTO role prompt
│       └── bdm.txt                    # BDM role prompt
├── tests/
│   ├── test_product_committee.py    # Unit tests for orchestrator logic
│   └── test_e2e_committee.py       # E2E smoke tests (minimal)
└── [existing debate system files remain unchanged]
```

**Structure Decision**: Single project structure (Option 1) - this is a CLI utility extending the existing single-project debate framework. The orchestrator script lives at repository root alongside `document_debate_cli.py`, with tests in the existing `tests/` directory.

## Complexity Tracking

*No violations requiring justification - feature aligns with constitution standards.*

## Parallel Work Analysis

*Single developer feature - no parallel work coordination required.*

## Phase 0: Research & Technical Decisions

### 0.1 Integration Pattern Research

**Question**: Subprocess vs. module import for invoking `document_debate_cli.py`?

**Decision**: **Subprocess invocation (MVP) → Module import (Target)**

**Rationale**:
- Subprocess allows fastest MVP delivery with minimal changes to existing code
- Module import provides better error control, testing, and clean API for future iterations
- Phased approach aligns with rapid prototyping philosophy while enabling refactoring

**Alternatives Considered**:
- Pure subprocess only: Rejected due to poor error handling and testing limitations
- Pure module import only: Rejected for MVP due to required refactoring of existing script

**Action Items**:
- [ ] Implement subprocess wrapper in `product_committee.py` (MVP)
- [ ] Document `run_debate()` API signature for future library refactor
- [ ] Track refactoring debt in tech backlog

### 0.2 PRD Compression Research

**Question**: How to generate "compressed PRD brief" for self-reflection?

**Decision**: **Skip compression for MVP** (pass full PRD text to self-reflection)

**Rationale**:
- Removes LLM integration complexity from MVP critical path
- Self-reflection can process full PRD; compression is optimization, not requirement
- Can be added later as enhancement when UX pain point is validated

**Alternatives Considered**:
- Separate LLM summarization step: Rejected for MVP due to added complexity
- Use existing summary from debate output: Rejected as not always available

**Action Items**:
- [ ] Update FR-009 in spec to reflect MVP approach (done)
- [ ] Document `--summarize-prd` flag for future enhancement
- [ ] Track compression feature in backlog

### 0.3 Retry Logic Research

**Question**: What retry strategy for failed rooms?

**Decision**: **Exponential backoff with max_retries configurable via CLI flag (default: 2)**

**Rationale**:
- Exponential backoff handles transient network/LLM issues effectively
- Configurable retry count allows tuning for different environments
- Continues after max retries (graceful degradation) per spec requirements

**Alternatives Considered**:
- Fixed delay between retries: Rejected due to inefficiency
- Fail-fast on first error: Rejected due to spec requirement for graceful degradation

**Action Items**:
- [ ] Implement exponential backoff in subprocess wrapper
- [ ] Add `--max-retries` CLI flag with default=2
- [ ] Log retry attempts in verbose mode

### 0.4 JSON Schema Research

**Question**: What schema for room JSON outputs and metadata?

**Decision**: **Define explicit JSON schemas for validation and documentation** (full validation is enhancement; MVP may use simplified presence checks)

**Rationale**:
- Explicit schemas enable validation and clear contracts
- Helps with testing and future refactoring
- Documented in `contracts/` directory for reference
- **MVP pragmatism**: Schemas defined but validation may be simplified (check presence of key fields vs strict schema compliance)

**Alternatives Considered**:
- Implicit/undefined schema: Rejected due to ambiguity and testing challenges
- Use existing debate output format: Rejected as not designed for orchestrator consumption

**Action Items**:
- [ ] Define `room_result_schema.json` (room_id, positions, verdict, takeaways, status)
- [ ] Define `metadata_schema.json` (run info, room statuses, warning flags)
- [ ] Define `reflection_schema.json` (learned insights, recommendations, accepted/rejected arguments)
- [ ] Add JSON validation to unit tests (MVP: presence checks; enhancement: full schema validation)

### 0.5 Self-Reflection Prompt Research

**Question**: What prompt structure for TPM self-reflection LLM call?

**Decision**: **Dedicated reflection prompt consuming PRD + question + room results**

**Rationale**:
- Separate prompt allows tailored reflection behavior vs. debate prompts
- Explicit context about which rooms succeeded/failed enables adaptation
- Produces structured output (learned insights, recommendations, argument acceptance)

**Alternatives Considered**:
- Reuse existing debate prompts: Rejected as not designed for synthesis/reflection
- Manual reflection without LLM: Rejected as not scalable

**Action Items**:
- [ ] Create `prompts/tpm_reflection.txt` with structured output instructions
- [ ] Define JSON output schema for reflection results
- [ ] Add unit test for reflection prompt parsing

## Phase 1: Design & Contracts

### 1.1 Data Model

See [data-model.md](data-model.md) for detailed entity definitions, relationships, and state transitions.

**Key Entities**:
- **CommitteeRun**: Single execution with PRD, question, metadata
- **DebateRoom**: Individual room (TPM vs role) with status and results
- **TPMReflection**: Synthesized analysis with recommendations
- **RoomStatus**: Enum (success/failed/skipped_missing_prompt)

### 1.2 API/CLI Contracts

See [contracts/](contracts/) directory for JSON schemas and CLI specifications.

**CLI Interface**:
```bash
product_committee.py \
  --prd <path> \
  --question <text> \
  [--model <name>] \
  [--max-retries <count>] \
  [--output-dir <path>] \
  [--roles-dir <path>] \
  [--run-id <id>] \
  [--allow-short-prd] \
  [--verbose] \
  [--quiet]
```

**JSON Output Contracts**:
- `tpm_*.json`: Room result with status, positions, verdict, takeaways
- `tpm_reflection.json`: Reflection with learned insights, recommendations
- `metadata.json`: Run info, room statuses, warning flags, timestamps

### 1.3 Testing Strategy

**Unit Tests** (`tests/test_product_committee.py`):
- Sequential room execution logic
- Retry logic with exponential backoff
- Status handling (success/failed/skipped)
- Metadata generation
- JSON schema validation
- Input validation (PRD existence, question non-empty)
- Edge cases (missing prompts, short PRD, all rooms fail)

**E2E Smoke Tests** (`tests/test_e2e_committee.py`):
- Happy path: Small PRD, all rooms succeed, verify artifacts created
- Failure scenario: One room fails, verify graceful degradation and partial report

**Test Doubles/Mocks**:
- Mock `document_debate_cli.py` subprocess calls
- Mock LLM responses for deterministic testing

**TDD Expectations**:
- Write unit tests **before** implementing key orchestrator logic branches (sequential execution, retries, status handling, metadata generation)
- Minimum: cover retry logic and status handling before implementation
- Full TDD: all unit tests written before corresponding code
- This aligns with constitution requirement and prevents bugs in complex branching logic

### 1.4 Logging Strategy

**Default (normal)**:
- Orchestrator start (PRD, question, model)
- Room start/completion with timestamps and status
- Self-reflection start/completion
- Final output paths

**--verbose**:
- All default logging
- Retry attempts (attempt number, previous failure reason)
- Key parameters passed to `document_debate_cli.py`
- Input/output size summaries (PRD length, response length)

**--quiet**:
- Start/finish only
- Critical errors only
- Final "Run finished. See: <path>" message

**Implementation**: Use Python logging module with configurable levels via CLI flags.

### 1.5 Error Handling Strategy

**Fatal Errors (non-zero exit)**:
- PRD file missing/unreadable
- Question empty
- TPM prompt file missing
- Output directory not writable

**Recoverable Errors (continue with warning)**:
- Individual room failure (after retries)
- Non-TPM role prompt file missing
- PRD too short (< 100 chars) → **Exception**: If `--allow-short-prd` flag is set, PRD < 100 chars is treated as fatal error (abort with message)
- Question very short (< 5 chars but non-empty)

**Retry Logic**:
- Exponential backoff: 1s, 2s, 4s, ... up to max_retries
- Log each retry attempt in verbose mode
- Mark room as failed after max retries exhausted

## Implementation Notes

### Dependencies on Existing System

**Requires**:
- `document_debate_cli.py` must exist and be executable
- Role prompt files must exist at specified paths
- Existing LLM configuration and authentication

**Assumes**:
- `document_debate_cli.py` accepts `--docx`, `--request`, `--pro-prompt`, `--con-prompt` flags
- **MVP**: `document_debate_cli.py` produces parsable output (stdout/stderr) or returns appropriate exit codes; orchestrator parses/format this into room JSON
- **Target**: `run_debate()` function returns ready-to-use `DebateRoom` structure directly

**Future Refactoring Targets**:
- Extract `run_debate()` function to `debate_core.py` shared library
- Replace subprocess calls with direct function imports
- Add `--summarize-prd` enhancement for PRD compression

### File Creation Conventions

**Output Directory Structure**:
```
<output-dir>/RUN_<timestamp>_<slug>/
├── tpm_cpo.json
├── tpm_cfo.json
├── tpm_cto.json
├── tpm_bdm.json
├── tpm_reflection.json
├── final_report.md
└── metadata.json
```

**Timestamp Format**: `YYYY-MM-DD_HHMMSS` (e.g., `2026-02-14_033700`)

**Slug Generation**: First 3-5 words from question, lowercased, hyphenated (e.g., "what is the potential" → "what-is-potential")

## Next Steps

**Phase 1 Complete** - Ready for `/spec-kitty.tasks` to generate work packages.

**Recommended WPs** (subject to task generation):
1. **WP01**: CLI scaffolding and argument parsing
2. **WP02**: Subprocess wrapper and retry logic
3. **WP03**: Room orchestration and metadata tracking
4. **WP04**: Self-reflection integration
5. **WP05**: Report generation and formatting
6. **WP06**: Testing and validation
