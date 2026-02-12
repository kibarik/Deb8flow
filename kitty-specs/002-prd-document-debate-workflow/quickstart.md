# Quickstart: PRD Document Debate Workflow

**Feature:** 002-prd-document-debate-workflow
**Date:** 2025-02-13

## Overview

This quickstart guide demonstrates how to use the new document debate workflow to analyze a .docx file through adversarial AI debate.

## Prerequisites

1. Install dependencies:
   ```bash
   pip install python-docx
   ```

2. Set environment variable:
   ```bash
   export OPENAI_API_KEY=your_key_here
   ```

## Usage

### Basic Command

```bash
# Run document debate workflow
python -m workflow.document_debate_workflow --docx path/to/document.docx
```

### Command Arguments

| Argument | Required | Description |
|-----------|-----------|-------------|
| `--docx` | Yes | Path to .docx file for analysis |

## Workflow Stages

The document debate workflow executes the following stages:

```
┌─────────────────────────────────────────────────────────────────────────┐
│  1. Document Upload & Topic Generation                           │
│     - User provides .docx file path                            │
│     - DocumentTopicNode extracts text and generates topic            │
│     - Stage: opening, Speaker: pro                               │
└───────────────────────┬─────────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  2. Opening Statement (PRO)                                   │
│     - ProDebaterNode presents strengths of document                │
│     - FactCheckNode validates claims                             │
│     - If validated: continue; if failed: retry                    │
└───────────────────────┬─────────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  3. Rebuttal (CON)                                          │
│     - ConDebaterNode critiques document weaknesses                │
│     - FactCheckNode validates claims                             │
│     - If validated: continue; if failed: retry                    │
└───────────────────────┬─────────────────────────────────────────────┘
                       │
                       ▼
              ┌────────────────────────────────────────────────────────────────┐
              │  4. Counter Argument (PRO)                        │
              │     - ProDebaterNode addresses CON's criticisms          │
              │     - FactCheckNode validates claims                   │
              └───────────────────────┬─────────────────────────────────┘
                             │
                             ▼
                ┌────────────────────────────────────────────────────────────────────────┐
                │  5. Final Argument (CON)                              │
                │     - ConDebaterNode presents final critique                │
                │     - FactCheckNode validates claims                          │
                └───────────────────────┬─────────────────────────────────────────┘
                                   │
                                   ▼
                         ┌───────────────────────────────────────────────────────────────────────────┐
                         │  6. Verdict (Judge)                                        │
                         │     - JudgeNode evaluates rhetoric AND document viability            │
                         │     - Declares winner with justification                        │
                         │     - Provides viability assessment                               │
                         └───────────────────────────────────────────────────────────────────────────────────┘
```

## Output

The workflow generates `result.md` with:

- Complete debate transcript with stage labels
- Fact-check results for each argument
- Judge's verdict including:
  - Winner (PRO or CON)
  - Reasoning for decision
  - **Document viability assessment** (NEW)

### Example Output

```markdown
# Document Debate Analysis

## Debate Transcript

### Opening (PRO)
The document presents a compelling vision for [X]...

### Rebuttal (CON)
While the vision is strong, there are significant risks...

### Counter (PRO)
The risks identified are mitigated by...

### Final Argument (CON)
After analysis, the document requires revision...

## Fact Check Results

All claims were successfully validated.

## Verdict

**WINNER: PRO**

**REASON:** The PRO side effectively defended the document's strengths while acknowledging valid concerns raised by CON.

**DOCUMENT VIABILITY:** Ready for presentation with minor revisions. The strategy is sound but would benefit from clarifying the implementation timeline.

```

## Result File Location

After execution, `result.md` is created in the current working directory.

## Error Handling

| Error | Message | Action |
|--------|---------|--------|
| File not found | "Error: .docx file not found at [path]" | Check file path |
| Empty document | "Error: Document contains no text content" | Verify file has content |
| Corrupted file | "Error: Unable to read .docx file" | Check file format |
| API failure | "Error: LLM request failed" | Check API key and quota |

## Integration Notes

- This workflow coexists with `debate_workflow.py` - both can be used independently
- Uses same `DebateState` structure extended with `document_input`
- All nodes inherit from `BaseComponent` for consistent behavior
