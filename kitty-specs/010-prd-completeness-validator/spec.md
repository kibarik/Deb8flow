# Specification: PRD Completeness Validator

**Feature Number**: 010
**Slug**: prd-completeness-validator
**Status**: Draft
**Mission**: software-dev
**Created**: 2025-02-15
**Target Branch**: main

## Overview

Add a `--check-prd` CLI command that uses an AI agent to validate Product Requirements Documents (PRDs) against a predefined template structure. The validator analyzes completeness, scores the document, identifies gaps, and provides actionable improvement suggestions.

## Problem Statement

Users preparing PRDs for debate lack automated validation to ensure their documents are complete and well-structured before starting debates. Incomplete PRDs lead to unfocused debates and wasted time as participants identify missing requirements during the session rather than beforehand.

## Goals

1. Provide automated PRD completeness checking before debates
2. Score PRDs objectively (X/10) based on coverage depth
3. Identify specific sections requiring additional work
4. Deliver actionable suggestions for improvement
5. Support both standalone usage and optional pipeline integration

## Non-Goals

1. Automatic PRD generation (only validation)
2. Modifying original PRD files (read-only analysis)
3. Enforcing specific writing styles or formats beyond structure
4. Validating technical feasibility of requirements

## User Scenarios & Testing

### Primary Scenario: Standalone PRD Validation

**Actor**: Product Manager or TPM preparing for a debate

**Flow**:
1. User has a PRD document (markdown format)
2. User runs: `python main.py --check-prd path/to/prd.md`
3. System analyzes PRD against predefined template
4. System displays console output with:
   - Overall score (X/10)
   - List of missing sections
   - List of underdeveloped sections
   - Top 3-5 improvement suggestions
5. System generates `prd_review.md` alongside original with detailed analysis
6. User can address gaps and re-run validation

**Success**: User receives clear, actionable feedback on PRD completeness

### Secondary Scenario: Pipeline Integration

**Actor**: Debate system running pre-flight checks

**Flow**:
1. User runs debate with PRD: `python main.py --debate-mode=committee --prd path/to/prd.md`
2. System optionally runs `--check-prd` if configured (via flag or config)
3. If PRD score below threshold (e.g., 6/10), system warns user and offers to:
   - Continue anyway
   - View recommendations and abort
   - View recommendations and continue
4. Debate proceeds normally if user confirms

**Success**: System prevents debates based on severely incomplete PRDs while allowing user discretion

### Edge Cases

1. **Empty PRD file**: Score 0/10, error message indicating file is empty or missing content
2. **Malformed markdown**: Best-effort parsing, score based on detectable structure
3. **Non-existent file**: Clear error message with file path
4. **PRD in non-markdown format**: Warning message, attempt basic text analysis
5. **Mixed language content**: Preserve original language in analysis, don't auto-translate
6. **PRD exceeds token limits**: Truncate or summarize sections, warn about length limitation

## Functional Requirements

### FR-001: Predefined PRD Template
System MUST validate PRDs against a predefined template containing the following required sections:

1. **Executive Summary** (Problem, Solution, Success Criteria)
2. **Background & Context** (Market situation, User pain points)
3. **Goals & Success Metrics** (SMART objectives, Key metrics)
4. **User Personas** (Target users, Use cases)
5. **Functional Requirements** (Core features, User stories)
6. **Non-Functional Requirements** (Performance, Security, Scalability)
7. **Technical Constraints** (Tech stack limitations, Integrations)
8. **Risks & Mitigations** (Known risks, Contingency plans)
9. **Timeline & Milestones** (Phases, Key dates)
10. **Open Questions** (Unresolved items, Decision points)

### FR-002: Completeness Scoring
System MUST assign a score from 0-10 based on:

- **Presence (40%)**: Each required section present earns points
- **Depth (40%)**: Content quality within each section (measured by content length, detail level)
- **Coherence (20%)**: Logical flow between sections and consistency

**Scoring rubric**:
- 9-10: All sections present with comprehensive content
- 7-8: All sections present with adequate content, some gaps
- 5-6: Most sections present, significant content gaps
- 3-4: Many sections missing or minimal content
- 0-2: PRD is essentially empty or severely incomplete

### FR-003: Console Output Format
When run with `--check-prd`, system MUST display to console:

```
📋 PRD Validation Report
═══════════════════════════════════════════
File: path/to/prd.md
Score: 7/10

✅ Present Sections (8/10):
  • Executive Summary
  • Background & Context
  • Goals & Success Metrics
  • User Personas
  • Functional Requirements
  • Non-Functional Requirements
  • Technical Constraints
  • Timeline & Milestones

❌ Missing Sections (2/10):
  • Risks & Mitigations
  • Open Questions

⚠️  Underdeveloped Sections:
  • User Personas (insufficient detail on use cases)
  • Functional Requirements (missing user story format)

💡 Top Recommendations:
  1. Add "Risks & Mitigations" section with identified project risks
  2. Add "Open Questions" section for unresolved decisions
  3. Expand "User Personas" with specific use case scenarios

📄 Detailed report: prd_review.md
```

### FR-004: Markdown Report Generation
System MUST generate a detailed `prd_review.md` file containing:

1. **Executive Summary**: Overall score, one-paragraph assessment
2. **Section-by-Section Analysis**: For each template section
   - Status (Present/Missing/Underdeveloped)
   - Specific feedback on content quality
   - Suggestions for improvement
3. **Structured Recommendations**: Grouped by priority (High/Medium/Low)
4. **Best Practices Reference**: Links or examples of well-written sections
5. **Next Steps**: Actionable checklist for improving the PRD

### FR-005: CLI Interface
System MUST provide the following command-line interface:

```bash
# Basic usage
python main.py --check-prd <path-to-prd>

# With output customization
python main.py --check-prd <path-to-prd> --output-format console|file|both

# With custom template (future enhancement)
python main.py --check-prd <path-to-prd> --template <template-name>

# Integrated with debate
python main.py --debate-mode=committee --prd <path> --check-prd --min-score 6
```

### FR-006: Optional Pipeline Integration
System MAY support integration with debate workflow:

- If `--check-prd` flag present with debate command, validate PRD before debate
- If score below `--min-score` threshold, prompt user with options
- User can choose to continue despite low score
- System logs validation result in debate metadata

### FR-007: Error Handling
System MUST handle errors gracefully:

- Invalid file path: Clear error with example usage
- Unreadable file: Specific error message (permissions, encoding)
- Parse failure: Warning, attempt best-effort analysis
- AI API failure: Fallback to basic structural validation (regex/keyword matching)

## Success Criteria

1. **Accuracy**: Validation correctly identifies 90%+ of missing sections in test PRDs
2. **Actionability**: 80%+ of users report recommendations help them improve their PRDs
3. **Performance**: Validation completes in under 30 seconds for typical PRD (<5000 words)
4. **Reliability**: 95%+ success rate for valid markdown files (no crashes)
5. **User Satisfaction**: Users can improve PRD score by 2+ points after one iteration of recommendations

## Key Entities

### PRD Document
- **Source**: User-provided markdown file
- **Content**: Product requirements following template structure
- **Format**: Markdown with section headers (##, ###)

### Validation Template
- **Definition**: Predefined list of required sections with validation criteria
- **Structure**: Section name, required subsections, quality indicators
- **Storage**: Configuration file or hardcoded (initially hardcoded, future: external template)

### Validation Report
- **Output**: `prd_review.md` generated alongside source PRD
- **Contents**: Score, section analysis, recommendations, best practices
- **Format**: Markdown with structured sections

### Scoring Rubric
- **Components**: Presence (40%), Depth (40%), Coherence (20%)
- **Range**: 0-10 scale
- **Bands**: Excellent (9-10), Good (7-8), Adequate (5-6), Poor (3-4), Fail (0-2)

## Open Questions

[None - initial implementation uses hardcoded template]

## Assumptions

1. PRDs are written in markdown format
2. Section headers use markdown ## or ### syntax
3. Content language may vary (English, Russian, mixed)
4. Users have basic familiarity with PRD structure
5. AI analysis uses existing LLM configuration (OpenAI/Requesty)
6. Initial template is hardcoded; future versions may support custom templates

## Dependencies

1. **Existing LLM Infrastructure**: Reuses `BaseComponent` and LLM configs from `configurations/llm_config.py`
2. **Debate System**: Optional integration with `main.py` CLI
3. **Markdown Parser**: Library for parsing markdown structure (e.g., `markdown-it-py` or standard library)

## Risks & Mitigations

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| AI scoring inconsistency | Medium | Medium | Use structured prompts with clear rubric; validate against test cases |
| Token limits for large PRDs | Low | Medium | Implement chunking for large documents; warn about length |
| Template mismatch with user PRDs | Medium | Low | Document template clearly; provide examples; allow future custom templates |
| False positives in validation | Low | Low | Emphasize "recommendations" over hard requirements; user discretion always respected |

## Out of Scope

1. PRD generation or auto-completion of missing sections
2. Validation of technical feasibility or architectural soundness
3. Integration with external PRD tools (Jira, Confluence, Notion)
4. Version control or change tracking for PRDs
5. Collaborative editing or review workflows
6. Custom template definition (future enhancement)
7. Multi-language support (analysis works with mixed languages, UI is English)

## References

1. **Existing Debate System**: `main.py`, `workflow/debate_workflow.py`
2. **LLM Infrastructure**: `nodes/base_component.py`, `configurations/llm_config.py`
3. **PRD Best Practices**: Industry-standard PRD templates (Marty Cagan, Inspired)
