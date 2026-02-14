# Tasks: PRD Completeness Validator

**Feature**: 010-prd-completeness-validator
**Status**: In Progress
**Last Updated**: 2025-02-15

## Overview

This document organizes implementation work for the PRD Completeness Validator feature into work packages. Each work package (WP) represents a cohesive unit of work that can be implemented independently.

**Work Package Statistics**:
- Total Work Packages: 5
- Total Subtasks: 26
- Average Subtasks per WP: 5.2
- Estimated Prompt Size Range: 250-450 lines per WP

**WP Size Distribution**:
- WP01: 5 subtasks (~300 lines)
- WP02: 7 subtasks (~450 lines)
- WP03: 4 subtasks (~250 lines)
- WP04: 4 subtasks (~250 lines)
- WP05: 6 subtasks (~350 lines)

## Phase 1: Foundation

### WP01: Foundation & Data Models

**Prompt File**: [tasks/WP01-foundation-models.md](tasks/WP01-foundation-models.md)

**Summary**: Set up the foundational infrastructure for PRD validation including CLI argument parsing, data models, and utility functions.

**Priority**: P0 (Blocking)

**Included Subtasks**:
- [ ] T001: Add --check-prd CLI arguments to main.py argument parser
- [ ] T002: Create PRD template constant with 10 required sections
- [ ] T003: Create Pydantic models (PRDValidationResult, SectionAnalysis)
- [ ] T004: Create markdown parser utility using re module
- [ ] T005: Add Rich console output utility functions

**Implementation Sketch**:
1. Extend main.py's argparse with --check-prd, --output-format, --min-score arguments
2. Define PRD_TEMPLATE dict with all 10 sections from spec.md FR-001
3. Create models/prd_validation.py with PRDValidationResult and SectionAnalysis Pydantic models
4. Create utils/markdown_parser.py with extract_sections() function
5. Create utils/console_formatter.py with Rich-based output helpers

**Parallel Opportunities**: None (foundational work)

**Dependencies**: None

**Risks**: None

**Definition of Done**:
- CLI arguments are parseable without errors
- PRD_TEMPLATE matches spec.md FR-001 exactly
- Pydantic models validate successfully
- Markdown parser extracts sections from test PRD
- Console formatter displays colored output

---

## Phase 2: Core Implementation

### WP02: Core Validation Logic

**Prompt File**: [tasks/WP02-core-validation-node.md](tasks/WP02-core-validation-node.md)

**Summary**: Implement the PRDValidatorNode class with all validation logic including section extraction, quantitative scoring, LLM assessment, and overall score calculation.

**Priority**: P0 (Blocking)

**Included Subtasks**:
- [ ] T006: Create PRDValidatorNode class inheriting from BaseComponent
- [ ] T007: Implement _extract_sections method using markdown parser
- [ ] T008: Implement _calculate_quantitative_scores method
- [ ] T009: Create system prompt for PRD validation in prompts/
- [ ] T010: Implement _get_llm_assessment with structured output
- [ ] T011: Implement _calculate_overall_score method
- [ ] T012: Add error handling and fallback validation

**Implementation Sketch**:
1. Create nodes/prd_validator_node.py with PRDValidatorNode class
2. Implement validate_prd() as main entry point
3. Use markdown parser from WP01 to extract sections
4. Calculate presence (40%) and depth (40%) scores quantitatively
5. Create prompts/prd_validator_system.md with validation instructions
6. Use BaseComponent.create_structured_output_chain() for LLM assessment
7. Combine scores: presence + depth + coherence = overall score
8. Handle API failures with fallback to regex-based validation

**Parallel Opportunities**: None (sequential within node)

**Dependencies**: WP01 (needs models, parser, formatter)

**Risks**:
- LLM structured output may be inconsistent
- Fallback logic needs thorough testing

**Definition of Done**:
- PRDValidatorNode instantiates with LLM config
- validate_prd() returns dict with validation_result, report_file_path, tokens
- Quantitative scoring matches rubric from spec.md FR-002
- LLM assessment generates SectionAnalysis for each section
- Fallback validation works when LLM fails

---

### WP03: Report Generation

**Prompt File**: [tasks/WP03-report-generation.md](tasks/WP03-report-generation.md)

**Summary**: Implement console and markdown report generation with proper formatting, section-by-section analysis, and actionable recommendations.

**Priority**: P1 (High)

**Included Subtasks**:
- [ ] T013: Implement _print_console_report with Rich formatting
- [ ] T014: Implement _generate_markdown_report method
- [ ] T015: Create report template with all required sections
- [ ] T016: Add report file writing with error handling

**Implementation Sketch**:
1. Create console formatter with emoji-based sections matching spec.md FR-003
2. Generate markdown report with Executive Summary, Section Analysis, Recommendations
3. Write report to prd_review.md adjacent to source PRD
4. Handle file write errors gracefully

**Parallel Opportunities**: None (builds on WP02 output)

**Dependencies**: WP02 (needs validation result data structure)

**Risks**:
- Report formatting may not match spec exactly
- File write permissions issues

**Definition of Done**:
- Console output matches format in spec.md FR-003 exactly
- Markdown report contains all sections from spec.md FR-004
- Report file created in correct location
- Errors handled with clear messages

---

## Phase 3: Integration

### WP04: CLI Integration

**Prompt File**: [tasks/WP04-cli-integration.md](tasks/WP04-cli-integration.md)

**Summary**: Wire up the PRD validator to main.py CLI with proper argument handling, threshold checking, and user prompts for below-threshold PRDs.

**Priority**: P1 (High)

**Included Subtasks**:
- [ ] T017: Wire up --check-prd mode in main.py
- [ ] T018: Implement handle_low_score threshold check
- [ ] T019: Add user choice prompt for below-threshold PRDs
- [ ] T020: Set proper exit codes for different scenarios

**Implementation Sketch**:
1. Add conditional branch in main.py for --check-prd mode
2. Instantiate PRDValidatorNode with LLM config
3. Call validate_prd() with parsed arguments
4. Check --min-score threshold and prompt user if below
5. Exit with code 0 (success), 1 (error), or 2 (invalid args)

**Parallel Opportunities**: None (modifies main.py entry point)

**Dependencies**: WP02, WP03 (needs complete validator implementation)

**Risks**:
- Integration with existing debate workflow may conflict
- Exit code logic needs careful handling

**Definition of Done**:
- `python main.py --check-prd path/to/prd.md` works standalone
- `python main.py --check-prd path/to/prd.md --output-format console` shows only console
- `python main.py --check-prd path/to/prd.md --output-format file` creates only report
- `python main.py --check-prd path/to/prd.md --min-score 6` prompts when below threshold
- Exit codes are correct for success, error, and invalid arguments

---

## Phase 4: Testing & Validation

### WP05: Testing Coverage

**Prompt File**: [tasks/WP05-testing-coverage.md](tasks/WP05-testing-coverage.md)

**Summary**: Create comprehensive test coverage including unit tests for parser and scoring, contract tests for CLI interface, and integration tests for full validation flow.

**Priority**: P1 (High)

**Included Subtasks**:
- [ ] T021: Create test fixtures directory with sample PRDs
- [ ] T022: Write unit tests for markdown parser
- [ ] T023: Write unit tests for scoring algorithm
- [ ] T024: Write unit tests for report generation
- [ ] T025: Write contract tests for CLI interface
- [ ] T026: Write integration test for full validation flow

**Implementation Sketch**:
1. Create tests/fixtures/prd_samples/ with complete, incomplete, and edge case PRDs
2. Test markdown parser with various PRD formats
3. Test scoring algorithm with known inputs/outputs
4. Test report generation formatting
5. Test CLI argument parsing and exit codes
6. Test end-to-end validation flow

**Parallel Opportunities**: T022-T025 can be developed in parallel (different test files)

**Dependencies**: WP01-WP04 (needs complete implementation)

**Risks**:
- LLM mocking may be complex for tests
- Test fixtures may not cover all edge cases

**Definition of Done**:
- All unit tests pass with >80% coverage
- Contract tests validate CLI behavior
- Integration test runs full validation successfully
- Tests cover edge cases from spec.md (empty PRD, malformed markdown, etc.)

---

## Dependencies Graph

```
WP01 (Foundation)
  ├─→ WP02 (Core Validation)
  │     ├─→ WP03 (Report Generation)
  │     └─→ WP04 (CLI Integration)
  │           └─→ WP05 (Testing)
  └─→ WP05 (Testing)
```

**Critical Path**: WP01 → WP02 → WP03 → WP04 → WP05

**Parallelizable**: None (sequential dependencies)

## MVP Scope

**Minimum Viable Product**: WP01 + WP02 + WP04

This combination provides:
- Basic PRD validation functionality
- Console output with score and recommendations
- CLI integration for standalone use
- No markdown report generation (WP03)
- No comprehensive tests (WP05)

**Production Readiness**: All 5 work packages required

## Progress Tracking

| WP | Title | Subtasks | Status | Prompt File |
|----|-------|----------|--------|-------------|
| WP01 | Foundation & Models | 5 | Planned | [WP01-foundation-models.md](tasks/WP01-foundation-models.md) |
| WP02 | Core Validation Logic | 7 | Planned | [WP02-core-validation-node.md](tasks/WP02-core-validation-node.md) |
| WP03 | Report Generation | 4 | Planned | [WP03-report-generation.md](tasks/WP03-report-generation.md) |
| WP04 | CLI Integration | 4 | Planned | [WP04-cli-integration.md](tasks/WP04-cli-integration.md) |
| WP05 | Testing Coverage | 6 | Planned | [WP05-testing-coverage.md](tasks/WP05-testing-coverage.md) |

**Total Progress**: 0/26 subtasks (0%)

## Notes

- All work packages are sized within ideal range (3-7 subtasks)
- Estimated prompt sizes: 250-450 lines per WP
- No WP exceeds 10 subtasks or 700 estimated lines
- Sequential dependencies require implementation in order
- Testing (WP05) should be developed alongside implementation for TDD approach
