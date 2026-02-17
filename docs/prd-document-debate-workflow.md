# PRD Document Debate Workflow

## Overview

The PRD Document Debate Workflow enables AI agents to analyze any .docx document through structured debate. Users provide a .docx file, and the system extracts text content and generates a comprehensive analysis highlighting both strengths and weaknesses through adversarial discussion between PRO and CON agents.

While designed for PRD analysis, the workflow is document-agnostic and can process any .docx content.

## What It Does

This feature:

- Reads PRD content from .docx files
- Conducts structured debate between PRO agent (arguing strengths) and CON agent (arguing weaknesses)
- Maintains the existing 4-stage debate structure (opening, rebuttal, counter, final_argument)
- Includes fact-checking for all claims
- Produces a comprehensive result.md with debate transcript and judge's verdict
- Evaluates both rhetorical performance AND document viability for management presentation

## How It Works

### Architecture

The document debate workflow is implemented as a standalone `document_debate_workflow.py` that coexists with the existing `debate_workflow.py`. Both workflows operate independently.

```
.docx File → DocumentTopicNode → PRO/CON Debate Stages → Fact-Checking → Judge → result.md
```

### Data Flow

1. **Document Input**: User provides .docx file path via CLI
2. **Text Extraction**: DocumentTopicNode extracts text using python-docx library
3. **Topic Generation**: Debate topic is derived from document content
4. **Debate Stages**: PRO and CON agents argue through 4 stages with document context
5. **Fact-Checking**: Each statement is validated after every stage
6. **Verdict**: Judge evaluates both rhetoric and document viability
7. **Output**: result.md generated with full transcript and verdict

### State Management

The workflow extends the existing `DebateState` with:

- `document_input`: Contains filepath and extracted content from .docx
- `debate_topic`: Derived from document content
- All standard debate state fields (positions, messages, stage, speaker, etc.)

## Usage

### Running Document Debates

```bash
# Document-based debate with direct text topic
python3 document_debate_cli.py --text "GitHub полезен для разработчиков"

# Document-based debate with .docx file
python3 document_debate_cli.py --docx '/path/to/document.docx' --request "какой потенциал у этого проекта?"
```

### Input Requirements

- **File Format**: Must be .docx format
- **File Size**: Typical documents 1-20 pages (larger documents may be truncated)
- **Content**: Non-empty text content required
- **Language**: Any language supported by the configured LLM

### Output

The workflow generates `result.md` with:

- All agent arguments with stage labels
- Fact-check results
- Judge's final verdict with:
  - Winner declaration
  - Document viability assessment
  - Rhetorical performance evaluation

## Configuration

### Dependencies

- **python-docx**: Library for reading .docx files
- **Existing debate infrastructure**: Reuses BaseComponent, StateGraph, prompts

### Prompts

The system extends existing prompts with document-specific instructions:

- **PRO agent**: Defends document validity (strengths, opportunities, positive aspects)
- **CON agent**: Critiques document (weaknesses, risks, gaps, concerns)
- **Both agents**: Reference specific content via `document_text` variable

## Debate Stages

The workflow maintains the standard 4-stage structure:

1. **Opening Stage**: PRO presents initial strengths of the document
2. **Rebuttal Stage**: CON presents weaknesses and counter-points
3. **Counter Stage**: PRO addresses CON's concerns
4. **Final Argument Stage**: CON presents final critique

Each stage is followed by fact-checking.

## Fact-Checking

Claims with numbers, statistics, or specific references are validated:
- Failed fact-checks require agent revision
- Three consecutive failures result in disqualification

## Edge Cases

| Scenario | Expected Behavior |
|----------|------------------|
| Empty .docx file | Workflow exits with error message indicating empty document |
| Corrupted .docx file | Workflow exits with error message indicating file read failure |
| Non-.docx file | Workflow exits with error message indicating unsupported format |
| Very large PRD (>100 pages) | Workflow completes but may take longer; content is truncated if exceeding token limits |
| PRD with no clear requirements | Agents note ambiguity and highlight it as a weakness |

## Success Criteria

| Criterion | Metric |
|-----------|--------|
| Analysis completeness | All PRD sections are referenced in debate |
| Output consistency | result.md format matches existing workflow output |
| Processing time | Workflow completes within 3 minutes for typical PRD |
| Actionability | Judge's verdict provides clear, actionable recommendations |

## Out of Scope

The following items are explicitly out of scope for this feature:

- Support for other document formats (PDF, markdown, plain text)
- Multi-document comparison debates
- Integration with external project management tools
- Real-time debate streaming
- Web UI for document upload
- Automated PRD generation or improvement suggestions beyond debate analysis
