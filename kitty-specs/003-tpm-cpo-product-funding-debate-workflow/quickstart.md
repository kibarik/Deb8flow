# Quickstart: Custom Prompt Debate Workflow

**Feature**: 003-tpm-cpo-product-funding-debate-workflow

## Overview

The custom prompt debate workflow enables role-based debates through CLI prompt injection. Instead of creating new node classes, users provide custom prompt files that are injected into existing PRO and CON debater nodes, enabling flexible role combinations like TPM vs CPO funding debates.

## Usage

### Basic Example (TPM vs CPO)

First, create two prompt files:

**tpm_prompt.txt:**
```
You are a Technical Product Manager advocating for project funding.
Focus on technical feasibility, market opportunity, and user value.
Emphasize execution speed and competitive advantage.
```

**cpo_prompt.txt:**
```
You are a Chief Product Officer evaluating resource allocation.
Focus on completeness, strategic alignment, and ROI.
Challenge assumptions about timeline and market fit.
```

Then run the debate:

```bash
python3 document_debate_cli.py \
  --text "We should build an AI-powered email automation tool" \
  --pro-prompt tpm_prompt.txt \
  --con-prompt cpo_prompt.txt
```

### Standard Debate (No Custom Prompts)

```bash
# Uses default PRO/CON prompts
python3 document_debate_cli.py \
  --text "GitHub полезен для разработчиков"
```

### PRO-Only Custom Prompt

```bash
# Customize only PRO debater, CON uses default
python3 document_debate_cli.py \
  --docx prd.docx \
  --pro-prompt engineer_prompt.txt
```

### Document-Based Debate with Custom Prompts

```bash
# Analyze .docx file with TPM vs CPO roles
python3 document_debate_cli.py \
  --docx project_proposal.docx \
  --request "какой потенциал у этого проекта?" \
  --pro-prompt tpm_prompt.txt \
  --con-prompt cpo_prompt.txt
```

### Output Structure

```python
{
    "debate_topic": "Should an AI-powered email automation tool...",
    "messages": [
        {"speaker": "pro", "content": "...", "validated": true, "stage": "opening"},
        {"speaker": "con", "content": "...", "validated": true, "stage": "rebuttal"},
        # ... more messages
    ],
    "verdict": "The PRO debater demonstrated clear market need..."
}
```

## Debate Flow

1. **Topic Generation**: Extract debate topic from text or document
2. **PRO Opening**: Advocate using custom prompt (if provided)
3. **Fact-Check**: Verify PRO's claims
4. **CON Rebuttal**: Challenge using custom prompt (if provided)
5. **Fact-Check**: Verify CON's claims
6. **PRO Counter**: Address CON's concerns
7. **Fact-Check**: Verify PRO's counter
8. **CON Final**: Summarize position
9. **Fact-Check**: Verify final claims
10. **Judge Verdict**: Render verdict with role context

## Input Requirements

### Debate Topic/Document
- **Format**: Plain text (--text) or .docx file (--docx)
- **Length**: Handles short ideas to full specifications
- **Content**: Should describe problem, solution, market, and value proposition

### Custom Prompt Files
- **Format**: Plain text files (.txt)
- **Size**: Maximum 5000 characters
- **Content**: Role description, personality, context, and perspective
- **Structure**: Free-form text describing the debater's role

## Prompt File Examples

### TPM Role (tpm_prompt.txt)
```
You are a Technical Product Manager advocating for project funding.
Focus on technical feasibility, market opportunity, and user value.
Emphasize execution speed and competitive advantage.
```

### CPO Role (cpo_prompt.txt)
```
You are a Chief Product Officer evaluating resource allocation.
Focus on completeness, strategic alignment, and ROI.
Challenge assumptions about timeline and market fit.
```

### Engineer Role (engineer_prompt.txt)
```
You are a Senior Software Engineer evaluating technical proposals.
Focus on code quality, maintainability, and technical debt.
Challenge unrealistic timelines and architectural decisions.
```

## Error Handling

### Invalid Prompt File
```bash
# File doesn't exist
python3 document_debate_cli.py --text "Topic" --pro-prompt missing.txt
# Error: Prompt file not found: missing.txt
```

### Empty Prompt File
```bash
# File is empty
python3 document_debate_cli.py --text "Topic" --pro-prompt empty.txt
# Error: Prompt file is empty: empty.txt
```

### File Too Large
```bash
# File exceeds 5000 characters
python3 document_debate_cli.py --text "Topic" --pro-prompt huge.txt
# Error: Prompt file too large (max 5000 characters): huge.txt
```

## Best Practices

1. **Prompt Specificity**: Be specific about role, context, and perspective
2. **Balanced Roles**: Ensure both prompts have similar detail levels for fair debate
3. **Character Limits**: Keep prompts under 5000 characters for optimal performance
4. **Test First**: Try custom prompts with simple topics before complex documents
5. **Role Consistency**: Maintain consistent role perspective across all debate stages
