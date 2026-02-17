# PRD Completeness Validator

## Overview

The PRD Completeness Validator is an automated tool that validates Product Requirements Documents (PRDs) against a predefined template structure. It analyzes completeness, scores the document, identifies gaps, and provides actionable improvement suggestions.

## What It Does

This feature:

- Validates PRDs against a predefined template structure
- Scores PRDs objectively (X/10) based on coverage depth
- Identifies specific sections requiring additional work
- Delivers actionable suggestions for improvement
- Supports both standalone usage and optional pipeline integration

## How It Works

### Architecture

```
PRD File → Template Validation → AI Analysis → Scoring → Report Generation
```

### Data Flow

1. User provides PRD file path
2. System validates file exists and is readable
3. PRD is parsed and analyzed against template
4. AI agent assesses completeness and depth
5. Score is calculated based on presence, depth, and coherence
6. Report is generated with findings and recommendations

### Scoring Rubric

The score (0-10) is calculated from three components:

- **Presence (40%)**: Each required section present earns points
- **Depth (40%)**: Content quality within each section
- **Coherence (20%)**: Logical flow between sections and consistency

**Score Bands**:
- 9-10: All sections present with comprehensive content
- 7-8: All sections present with adequate content, some gaps
- 5-6: Most sections present, significant content gaps
- 3-4: Many sections missing or minimal content
- 0-2: PRD is essentially empty or severely incomplete

## Usage

### Standalone Validation

```bash
# Basic usage
python main.py --check-prd path/to/prd.md

# With output customization
python main.py --check-prd path/to/prd.md --output-format console|file|both

# With custom template (future enhancement)
python main.py --check-prd path/to/prd.md --template <template-name>
```

### Pipeline Integration

```bash
# Integrated with debate
python main.py --debate-mode=committee --prd <path> --check-prd --min-score 6
```

If score is below threshold, system prompts user to:
- Continue anyway
- View recommendations and abort
- View recommendations and continue

## Required Template Sections

The validator checks for these 10 required sections:

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

## Console Output Format

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

## Report Generation

The system generates `prd_review.md` with:

1. **Executive Summary**: Overall score, one-paragraph assessment
2. **Section-by-Section Analysis**: For each template section
   - Status (Present/Missing/Underdeveloped)
   - Specific feedback on content quality
   - Suggestions for improvement
3. **Structured Recommendations**: Grouped by priority (High/Medium/Low)
4. **Best Practices Reference**: Links or examples of well-written sections
5. **Next Steps**: Actionable checklist for improving the PRD

## Edge Cases

| Scenario | Behavior |
|----------|----------|
| Empty PRD file | Score 0/10, error message indicating file is empty |
| Malformed markdown | Best-effort parsing, score based on detectable structure |
| Non-existent file | Clear error message with file path |
| PRD in non-markdown format | Warning message, attempt basic text analysis |
| Mixed language content | Preserve original language in analysis |
| PRD exceeds token limits | Truncate or summarize sections, warn about length |

## Error Handling

- **Invalid file path**: Clear error with example usage
- **Unreadable file**: Specific error message (permissions, encoding)
- **Parse failure**: Warning, attempt best-effort analysis
- **AI API failure**: Fallback to basic structural validation (regex/keyword matching)

## Success Criteria

- **Accuracy**: 90%+ accuracy in identifying missing sections
- **Actionability**: 80%+ of users report recommendations help improve PRDs
- **Performance**: Validation completes in under 30 seconds for typical PRD (<5000 words)
- **Reliability**: 95%+ success rate for valid markdown files
- **User Satisfaction**: Users can improve PRD score by 2+ points after one iteration

## Dependencies

- **Existing LLM Infrastructure**: Reuses `BaseComponent` and LLM configs
- **Debate System**: Optional integration with `main.py` CLI
- **Markdown Parser**: Library for parsing markdown structure

## Out of Scope

The following items are explicitly out of scope:

- PRD generation or auto-completion of missing sections
- Validation of technical feasibility or architectural soundness
- Integration with external PRD tools (Jira, Confluence, Notion)
- Version control or change tracking for PRDs
- Collaborative editing or review workflows
- Custom template definition (future enhancement)
- Multi-language support (UI is English, analysis works with mixed languages)
