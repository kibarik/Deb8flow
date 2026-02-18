# WP08: Documentation

**Work Package**: 017-product-committee-clean-architecture-refactoring / WP08
**Status**: TODO
**Dependencies**: WP07

## Overview

Create comprehensive documentation for the refactored architecture following constitution requirements.

## Documentation Requirements

Per `.kittify/memory/constitution.md`:

> **Feature documentation required**: Each feature MUST have a documentation file in `docs/{feature-name}.md`
>   - Brief and functional description of what the feature does
>   - Clear explanation of how it works (architecture, data flow)
>   - Usage examples and command reference
>   - Sufficient detail for anyone to understand the feature without diving into code

## Implementation Requirements

### 1. Feature Documentation (`docs/product-committee-refactoring.md`)

```markdown
# Product Committee Clean Architecture Refactoring

## Overview

The product committee system has been refactored from a monolithic 1970-line script into a clean, maintainable architecture using Modular Hexagonal Hybrid design principles.

## What This Feature Does

The product committee simulates a virtual expert committee by running four debate rooms:
- TPM vs CPO (Chief Product Officer)
- TPM vs CFO (Chief Financial Officer)
- TPM vs CTO (Chief Technology Officer)
- TPM vs BDM (Business Development Manager)

Each room debates a PRD document from different perspectives, with a judge determining the winner. The system generates comprehensive reports with executive summaries and detailed analysis.

## Architecture

### Modular Hexagonal Hybrid Design

The refactored system follows Clean Architecture principles with clear layer separation:

```
┌─────────────────────────────────────┐
│         CLI Layer                   │
│  product_committee.py (~200 lines)  │
└─────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────┐
│      Application Layer              │
│  RunProductCommittee use case       │
│  - Coordinates debate rooms         │
│  - Manages metadata                 │
│  - Generates reports                │
└─────────────────────────────────────┘
              │
      ┌───────┴───────┐
      ▼               ▼
┌─────────────┐  ┌──────────────┐
│ Domain Layer│  │ Shared Core  │
│             │  │              │
│ CommitteeRun│  │ DebateRoom   │
│ Committee   │  │ Verdict      │
│ Report      │  │ DebateMessage│
└─────────────┘  └──────────────┘
      │               │
      └───────┬───────┘
              ▼
┌─────────────────────────────────────┐
│   Infrastructure Layer              │
│  - CliDebateExecutor (subprocess)   │
│  - LocalFileStorage (async I/O)     │
│  - CommitteeReportGenerator         │
└─────────────────────────────────────┘
```

### Key Principles

1. **Domain Purity**: Domain entities use plain dataclasses (no Pydantic, no external dependencies)
2. **Dependency Inversion**: Application layer depends on port interfaces, not implementations
3. **Adapter Pattern**: Infrastructure adapters implement ports (Protocol interfaces)
4. **Async-First**: Single async execution path (eliminated sync/async duplication)

### Module Structure

```
src/
├── shared/debate/              # Shared debate framework
│   ├── domain/                 # Pure domain entities
│   ├── application/            # Use cases & ports
│   └── infrastructure/         # Adapters (executors, storage)
│
└── committee/                 # Product committee specific
    ├── domain/                 # Committee entities
    ├── application/            # RunProductCommittee use case
    └── adapters/               # CLI, reports
```

## Usage Examples

### Basic Usage

```bash
python3 product_committee.py \
  --prd ./test_prd.txt \
  --question 'заработает ли этот проект 100 млн за 2 дня' \
  --max-concurrency 0 \
  --language 'русский кратко, в формате буллетлистов'
```

### Sequential Execution

```bash
python3 product_committee.py \
  --prd ./test_prd.txt \
  --question "What's the potential of this project?" \
  --max-concurrency 1
```

### Parallel Execution (All Rooms)

```bash
python3 product_committee.py \
  --prd ./test_prd.txt \
  --question "Evaluate this PRD" \
  --max-concurrency 0
```

### Custom Model

```bash
python3 product_committee.py \
  --prd ./test_prd.txt \
  --question "Test question" \
  --model gpt-4 \
  --max-retries 3
```

## Command Reference

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `--prd` | Yes | - | Path to PRD document (.docx or .txt) |
| `--question` | Yes | - | Committee question for all rooms |
| `--model` | No | default | LLM model name |
| `--max-retries` | No | 2 | Maximum retry attempts per room |
| `--max-concurrency` | No | 2 | Max parallel rooms (0=all, 1=sequential) |
| `--output-dir` | No | ./committee_output | Output directory |
| `--roles-dir` | No | prompts/roles/ | Role prompts directory |
| `--run-id` | No | auto | Manual run identifier |
| `--language` | No | - | Language/style setting |
| `--verbose` | No | false | Enable verbose logging |
| `--quiet` | No | false | Quiet mode |

## Output Structure

Each run creates a `{run-id}` folder in the output directory:

```
committee_output/RUN_20250118_120000-test-question/
├── metadata.json                          # Run configuration and results
├── TPM_vs_CPO.json                        # Room result summary
├── TPM_vs_CPO_dialogue.json               # Full dialogue transcript
├── TPM_vs_CFO.json
├── TPM_vs_CFO_dialogue.json
├── TPM_vs_CTO.json
├── TPM_vs_CTO_dialogue.json
├── TPM_vs_BDM.json
├── TPM_vs_BDM_dialogue.json
├── final_report.md                        # Comprehensive analysis
└── conclusion.md                           # Executive summary
```

## Data Flow

1. **Input**: PRD document + committee question
2. **Validation**: Pydantic validates all inputs
3. **Execution**: 4 debate rooms run in parallel/sequence
4. **Collection**: Results collected with judge verdicts
5. **Generation**: Reports generated from results
6. **Output**: JSON logs + markdown reports saved to disk

## Error Handling

The system handles errors gracefully:

| Error Type | Behavior |
|------------|----------|
| Missing PRD file | Clear error before execution |
| Empty question | Validation error |
| Missing role prompt | Room skipped, others continue |
| LLM timeout | Room fails gracefully, retry logic |
| All rooms fail | Detailed error analysis in conclusion.md |

## Performance

- **Parallel execution**: Completes in ~40-50% of sequential time
- **Non-blocking I/O**: File writes don't block execution
- **Concurrent rooms**: Up to 4 rooms run simultaneously

## Migration Notes

### From Old Implementation

The refactored system maintains **100% functional equivalence**:
- All CLI arguments preserved
- Output format unchanged
- All existing tests pass
- Same behavior, better architecture

### Key Improvements

| Before | After |
|--------|-------|
| 1970 lines in one file | ~200 lines CLI + focused modules |
| Sync/async duplication | Single async path |
| Mixed concerns | Clear layer separation |
| Hard to test | Fully testable domain |
| Impossible to maintain | Easy to evolve |

## See Also

- [Implementation Plan](../kitty-specs/017-product-committee-clean-architecture-refactoring/plan.md)
- [Data Model](../kitty-specs/017-product-committee-clean-architecture-refactoring/data-model.md)
- [Quick Start Guide](../kitty-specs/017-product-committee-clean-architecture-refactoring/quickstart.md)
```

### 2. Update README.md

Add architecture section to main README:

```markdown
## Architecture

Deb8flow uses **Clean Architecture** principles for maintainable, testable code:

### Shared Debate Framework

The `src/shared/debate/` module provides reusable debate infrastructure:
- **Domain**: Pure business logic (DebateRoom, Verdict, etc.)
- **Application**: Use cases and port interfaces
- **Infrastructure**: Adapters for subprocess execution and file storage

### Committee Module

The `src/committee/` module implements product committee orchestration:
- Runs 4 debate rooms in parallel or sequence
- Generates comprehensive reports
- Validates inputs with Pydantic

### Key Design Principles

1. **Domain Isolation**: Domain entities have zero external dependencies
2. **Dependency Inversion**: Depend on interfaces (Protocols), not implementations
3. **Async-First**: Single async execution path for consistency
4. **Testability**: All layers independently testable
```

### 3. Update CLAUDE.md

Add architecture notes for AI agents:

```markdown
## Architecture

### Clean Architecture (Feature 017+)

The codebase follows Clean Architecture principles:
- Domain layer uses plain dataclasses (no Pydantic)
- Application layer defines port interfaces using `typing.Protocol`
- Infrastructure layer implements ports (adapters)
- CLI layer is thin orchestration

### Module Structure

```
src/
├── shared/debate/         # Shared debate framework
│   ├── domain/            # Entities (no external deps)
│   ├── application/       # Use cases & ports
│   └── infrastructure/    # Adapters
└── committee/             # Product committee specific
    ├── domain/
    ├── application/
    └── adapters/
```
```

## Acceptance Criteria

- [ ] Documentation follows constitution standards
- [ ] Clear explanation of architecture for new developers
- [ ] Usage examples match actual CLI behavior
- [ ] Architecture diagrams accurate to implementation
- [ ] Command reference complete and accurate
- [ ] Migration notes explain differences
- [ ] Cross-references to planning artifacts

## Files to Create

1. `docs/product-committee-refactoring.md`
2. Update `README.md` with architecture section
3. Update `CLAUDE.md` with architecture notes

## Files to Update

1. `README.md` - Add architecture overview
2. `CLAUDE.md` - Add clean architecture notes

## Notes

- Follow constitution documentation requirements
- Include practical examples for all CLI arguments
- Document architecture decisions and rationale
- Provide migration notes for users
- Cross-reference planning artifacts for details

## Next Steps

After completing this work package:
1. Review documentation for completeness
2. Verify all examples work as documented
3. Check links to planning artifacts
4. Commit with message "docs: add product committee refactoring documentation (WP08)"
5. Move to WP09 (Final Validation and Cleanup)
