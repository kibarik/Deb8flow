# Research: Product Committee Orchestrator

**Feature**: 007-product-committee-orchestrator
**Date**: 2026-02-14
**Status**: Complete

## Overview

This document consolidates research findings for the Product Committee Orchestrator feature, resolving all technical questions from the planning phase. Each research section addresses a key unknown with a decision, rationale, and action items.

## 0.1 Integration Pattern Research

### Question
Subprocess vs. module import for invoking `document_debate_cli.py`?

### Decision
**Subprocess invocation (MVP) → Module import (Target)**

### Rationale
- **Subprocess allows fastest MVP delivery** with minimal changes to existing code
- **Module import provides better error control**, testing, and clean API for future iterations
- **Phased approach aligns with rapid prototyping philosophy** while enabling refactoring
- **Constitution compliance**: Performance not critical for prototype development

### Alternatives Considered
| Alternative | Why Rejected |
|-------------|---------------|
| Pure subprocess only | Poor error handling and testing limitations; difficult to mock for unit tests |
| Pure module import only | Requires immediate refactoring of existing script; delays MVP delivery |

### Action Items
- [x] Document subprocess wrapper approach in plan
- [x] Document `run_debate()` API signature for future library refactor
- [x] Track refactoring debt in plan implementation notes

### Implementation Notes
- Use `subprocess.run()` with appropriate timeout and capture settings
- Parse stdout/stderr from `document_debate_cli.py` for room results
- Return structured `DebateRoom` result objects with status, positions, verdict
- Design API signature: `run_debate(prd_path, question, pro_prompt, con_prompt, model=None) -> DebateResult`

## 0.2 PRD Compression Research

### Question
How to generate "compressed PRD brief" for self-reflection?

### Decision
**Skip compression for MVP** (pass full PRD text to self-reflection)

### Rationale
- **Removes LLM integration complexity** from MVP critical path
- **Self-reflection can process full PRD**; compression is optimization, not requirement
- **Can be added later as enhancement** when UX pain point is validated
- **Spec already allows this**: FR-009 clarified to support direct PRD text in MVP

### Alternatives Considered
| Alternative | Why Rejected |
|-------------|---------------|
| Separate LLM summarization step | Adds complexity to MVP; requires additional LLM integration and error handling |
| Use existing summary from debate output | Not always available; different format than reflection requires |

### Action Items
- [x] Update FR-009 in spec to reflect MVP approach
- [x] Document `--summarize-prd` flag for future enhancement
- [x] Track compression feature in backlog

### Implementation Notes
- Pass full PRD text content to self-reflection prompt
- Self-reflection prompt should handle variable input length gracefully
- Future enhancement: Add `--summarize-prd` flag to trigger separate summarization call
- Future enhancement: Auto-trigger summarization when PRD exceeds character threshold (e.g., 5000 chars)

## 0.3 Retry Logic Research

### Question
What retry strategy for failed rooms?

### Decision
**Exponential backoff with max_retries configurable via CLI flag (default: 2)**

### Rationale
- **Exponential backoff handles transient network/LLM issues effectively**
- **Configurable retry count** allows tuning for different environments
- **Continues after max retries** (graceful degradation) per spec requirements
- **Industry standard**: Exponential backoff is proven pattern for distributed systems

### Alternatives Considered
| Alternative | Why Rejected |
|-------------|---------------|
| Fixed delay between retries | Inefficient; may not give system enough time to recover |
| Fail-fast on first error | Violates spec requirement for graceful degradation and multi-perspective analysis |

### Action Items
- [x] Document exponential backoff strategy in plan
- [x] Add `--max-retries` CLI flag with default=2 to spec
- [x] Specify retry logging in verbose mode

### Implementation Notes
- Exponential backoff sequence: 1s, 2s, 4s, 8s, ... (up to max_retries)
- Log each retry attempt with attempt number and previous failure reason (in verbose mode)
- Mark room as `failed` after max retries exhausted
- Room failure should not prevent other rooms from running
- Self-reflection always runs regardless of room failures

## 0.4 JSON Schema Research

### Question
What schema for room JSON outputs and metadata?

### Decision
**Define explicit JSON schemas for validation and documentation**

### Rationale
- **Explicit schemas enable validation** and clear contracts between components
- **Helps with testing** through schema validation in unit tests
- **Future refactoring** easier with clear contracts
- **Documentation benefit**: Schemas serve as living documentation

### Alternatives Considered
| Alternative | Why Rejected |
|-------------|---------------|
| Implicit/undefined schema | Ambiguity leads to integration issues; difficult to test |
| Use existing debate output format | Not designed for orchestrator consumption; lacks required fields |

### Action Items
- [x] Define `room_result_schema.json` (room_id, positions, verdict, takeaways, status)
- [x] Define `metadata_schema.json` (run info, room statuses, warning flags)
- [x] Define `reflection_schema.json` (learned insights, recommendations, accepted/rejected arguments)
- [x] Add JSON validation to unit tests
- [x] Document schemas in contracts/ directory

### Implementation Notes
- Use `jsonschema` library for validation in tests
- Schemas should be versioned (v1 initially)
- All JSON outputs must validate against schemas
- Schema validation errors should be logged and fail gracefully

## 0.5 Self-Reflection Prompt Research

### Question
What prompt structure for TPM self-reflection LLM call?

### Decision
**Dedicated reflection prompt consuming PRD + question + room results**

### Rationale
- **Separate prompt allows tailored reflection behavior** vs. debate prompts
- **Explicit context about which rooms succeeded/failed** enables adaptation
- **Produces structured output** (learned insights, recommendations, argument acceptance)
- **Consistent with existing pattern**: Separate prompts for different agent roles

### Alternatives Considered
| Alternative | Why Rejected |
|-------------|---------------|
| Reuse existing debate prompts | Not designed for synthesis/reflection; lacks context about multiple rooms |
| Manual reflection without LLM | Not scalable; doesn't leverage existing LLM infrastructure |

### Action Items
- [x] Create `prompts/tpm_reflection.txt` with structured output instructions
- [x] Define JSON output schema for reflection results
- [x] Add unit test for reflection prompt parsing
- [x] Document reflection prompt format in contracts/

### Implementation Notes
- Reflection prompt should request JSON output matching schema
- Prompt should include context about successful/failed rooms
- Prompt should ask for: learned insights, recommendations, argument acceptance/rejection
- Structured output enables automated report generation

## Summary

All research questions resolved. No blockers for proceeding to Phase 1 design and contracts.

**Key Decisions**:
1. **MVP: Subprocess → Target: Module import** (phased approach)
2. **Skip PRD compression** for MVP (enhancement later)
3. **Exponential backoff retries** with configurable max
4. **Explicit JSON schemas** for all outputs
5. **Dedicated reflection prompt** with structured output

**Next Phase**: Generate data-model.md and contracts/
