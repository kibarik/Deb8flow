# Research: Document Rewrite Agent

**Feature**: 015-document-rewrite-agent
**Date**: 2026-02-17
**Phase**: Phase 0 - Research & Technical Decisions

## Overview

This document captures research findings for the Document Rewrite Agent feature, resolving all outstanding technical decisions identified in the implementation plan.

## Research Topic 1: Format Conversion Library Selection

### Decision: Use `mammoth` for .docx → markdown, custom markdown → .docx

**Rationale**:

| Option | Pros | Cons | Verdict |
|--------|------|------|---------|
| `pandoc` (external) | Full bidirectional, industry standard | External dependency, requires installation, not Python-native | ❌ Rejected |
| `mammoth` (Python) | .docx → markdown is excellent, pure Python, pip-installable | One-way conversion only | ✅ Primary choice |
| Custom python-docx | Full control, no new dependencies | Complex, error-prone, reinventing wheel | ⚠️ Fallback |

**Implementation Strategy**:
1. Use `mammoth` for .docx → markdown conversion (read direction)
2. For markdown → .docx (write direction):
   - Use existing `python-docx` library (already a dependency)
   - Implement markdown-to-docx using `python-docx` + `markdown` parsing
   - Preserve basic formatting (headers, bold, italics, lists)
3. For .txt files: Simple read/write with UTF-8 encoding
4. For .md files: Direct manipulation (no conversion needed)

**Dependencies to Add**:
- `mammoth>=1.8.0` - .docx to markdown conversion
- No external pandoc dependency required

**Alternatives Considered**:
- `pandoc` would be ideal but requires external installation
- Could use `pypandoc` (Python wrapper for pandoc) but still requires pandoc installation
- `mammoth` is sufficient for read direction, write direction is simpler to implement

## Research Topic 2: Prompt Strategy for Rewriter Agent

### Decision: Single comprehensive prompt with structured context

**Rationale**:

| Option | Pros | Cons | Verdict |
|--------|------|------|---------|
| Single prompt | Simpler, consistent context, easier to debug | Higher token usage | ✅ Chosen |
| Chunked processing | Lower token usage per call | Complex state management, inconsistency | ❌ Rejected |
| Few-shot examples | Better quality | Token intensive, may overfit | ⚠️ Optional enhancement |

**Implementation Strategy**:
1. **Prompt Structure**:
   ```
   System role: You are a document rewriter. Apply recommendations from conclusion report.

   Context:
   - Original document (as markdown)
   - Conclusion report with recommendations
   - Formatting guidelines

   Task: Rewrite document applying all recommendations.

   Rules:
   - Apply ALL recommendations aggressively
   - Preserve sections without recommendations
   - Resolve contradictions independently
   - Add <!-- REVIEW NOTE: --> only when absolutely necessary
   ```

2. **Token Management**:
   - Documents up to 10MB may exceed context windows
   - Implement chunking for large documents as fallback
   - Use model's maximum context (e.g., 128K tokens for GPT-4)

3. **Quality Assurance**:
   - Include validation step to check all recommendations were applied
   - If recommendations missed, retry with more explicit prompt

**Alternatives Considered**:
- Chunked processing too complex for MVP
- Few-shot examples can be added later if quality insufficient
- Structured output (JSON) could be used but markdown is more flexible

## Research Topic 3: Metadata Preservation Strategy

### Decision: Preserve metadata in original copy, best-effort in rewritten output

**Rationale**:

| Metadata Type | Copy Strategy | Rewrite Strategy |
|---------------|---------------|------------------|
| Author | ✅ Full preservation | ⚠️ Best effort (format-dependent) |
| Created date | ✅ Full preservation | ❌ Not preserved (new document) |
| Modified date | ✅ Full preservation | ✅ Set to rewrite timestamp |
| File permissions | ✅ Full preservation | ⚠️ Best effort |

**Implementation Strategy**:

1. **Original Copy** (saved to `{run-id}/original.ext`):
   - Use `shutil.copy2()` to preserve metadata
   - Capture file stats using `os.stat()`
   - Store metadata in JSON alongside copy

2. **Rewritten Output**:
   - Set creation/modification timestamps to current time
   - Attempt to preserve author for .docx (python-docx supports this)
   - For .txt/.md, timestamps are OS-managed (limited control)

3. **Metadata Storage**:
   ```python
   # Store in {run-id}/file_metadata.json
   {
     "original_file": "path/to/original.docx",
     "copied_file": "original.docx",
     "rewritten_file": "original_20260217_123456.docx",
     "preserved_metadata": {
       "author": "...",
       "created": "...",
       "modified": "..."
     }
   }
   ```

**Alternatives Considered**:
- Full preservation in rewritten output is format-dependent and unreliable
- Not preserving any metadata would break user trust
- Storing metadata separately provides audit trail

## Research Topic 4: Error Recovery Mechanism

### Decision: Graceful degradation with clear error reporting

**Rationale**:

| Error Type | Recovery Strategy |
|------------|-------------------|
| File not found | Log error, skip rewrite, preserve debate results |
| Conversion failure | Log error, copy original with note, continue |
| LLM timeout | Retry once with shorter context, then fail gracefully |
| Write failure | Log error, preserve original copy, report to user |

**Implementation Strategy**:

1. **Error Handling Hierarchy**:
   ```
   try:
       convert_to_markdown()
       call_llm_rewriter()
       convert_back_to_format()
   except FileNotFoundError:
       log_error("Original file missing")
       create_copy_with_note()
   except ConversionError:
       log_error("Format conversion failed")
       create_copy_with_note("Conversion failed - original preserved")
   except LLMError:
       log_error("LLM call failed")
       create_copy_with_note("Rewrite failed - original preserved")
   except WriteError:
       log_error("Output write failed")
       # Original copy already safe
   ```

2. **User Communication**:
   - Always display rewriter status (success/failure)
   - Provide actionable error messages
   - Never crash the main workflow

3. **Fallback Behavior**:
   - If rewrite fails, create `original_rewrite_failed.md` with explanation
   - Preserve all debate artifacts (conclusion.md always created)
   - Log full error details for debugging

**Alternatives Considered**:
- Fail-fast would lose debate results (unacceptable)
- Retry-with-backoff adds complexity for limited benefit
- Graceful degradation provides best user experience

## Research Topic 5: Conclusion Parsing Strategy

### Decision: Use LLM to extract structured recommendations

**Rationale**:

| Option | Pros | Cons | Verdict |
|--------|------|------|---------|
| Parse structured sections | Fast if format is consistent | Brittle, breaks on format changes | ❌ Rejected |
| Regex patterns | Simple, no LLM call | Fragile, misses context | ❌ Rejected |
| LLM extraction | Robust, handles variations | Requires LLM call, adds latency | ✅ Chosen |

**Implementation Strategy**:

1. **Extraction Prompt**:
   ```
   Extract all actionable recommendations from the conclusion report.

   For each recommendation, provide:
   - Section reference (if applicable)
   - Action to take (remove/update/add/replace)
   - Target content (what to change)
   - New content (what to change to)

   Output as JSON list of recommendations.
   ```

2. **Validation**:
   - Check extraction completeness (did we get all recommendations?)
   - Validate JSON structure
   - Fallback to full conclusion text if extraction fails

3. **Fallback Strategy**:
   ```python
   try:
       recommendations = extract_recommendations(conclusion_text)
   except ExtractionError:
       # Use full conclusion text as context
       recommendations = None
       # Let rewriter agent parse from full text
   ```

**Alternatives Considered**:
- Structured parsing assumes fixed conclusion format (risky)
- Regex can't handle semantic variations
- LLM extraction is robust and worth the small latency cost

## Summary of Decisions

| Topic | Decision | Impact |
|-------|----------|--------|
| Format Conversion | `mammoth` + custom `python-docx` | Pure Python, pip-installable |
| Prompt Strategy | Single comprehensive prompt | Simpler implementation |
| Metadata Preservation | Full in copy, best-effort in rewrite | Balance of control and practicality |
| Error Recovery | Graceful degradation | User-friendly, robust |
| Conclusion Parsing | LLM-based extraction | Robust, flexible |

## Dependencies to Add

```txt
# New dependencies for this feature
mammoth>=1.8.0  # .docx to markdown conversion
```

**Note**: `python-docx` is already a dependency, so no new dependency needed for markdown → .docx direction.

## Implementation Risks

| Risk | Mitigation |
|------|------------|
| Large documents exceed context window | Implement chunking as fallback |
| Format conversion loses formatting | Document limitations in user guide |
| LLM fails to apply all recommendations | Validation step with retry |
| Metadata preservation not reliable | Store separately in JSON |

## Open Questions

None - all research questions resolved.

---

**Research Status**: Complete
**Next Phase**: Phase 1 - Design (data-model.md, contracts/, quickstart.md)
