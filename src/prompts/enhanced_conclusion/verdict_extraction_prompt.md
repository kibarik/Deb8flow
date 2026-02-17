# Verdict Extraction Prompt

You are analyzing a committee debate to extract the verdict and generate a clear answer to the user's question.

## Debate Content

{final_report_text}

## Room Outcomes

{room_outcomes_summary}

## Confidence Level

{confidence_level}

## Your Task

Generate a verdict that includes:

1. **Answer**: Direct answer to the user's question (120-150 words)
   - Must be between 120-150 words exactly
   - Clearly state the overall outcome
   - Summarize key reasoning

2. **Rationale**: 2-3 sentence explanation of the verdict (50-500 characters)
   - Explain why this verdict was reached
   - Reference the room outcomes

3. **Room Outcomes Summary**: Brief summary of which side won each room

## Output Format

Output ONLY valid JSON with this exact structure:

```json
{
  "answer": "Direct answer to the question (120-150 words)...",
  "confidence": "High|Medium|Low",
  "rationale": "2-3 sentence explanation...",
  "room_outcomes": "e.g., 'Opponents won 3/4 rooms (TPM won only vs CTO)'"
}
```

## Constraints

- Answer MUST be 120-150 words (not characters, words)
- Confidence MUST match the provided confidence level
- Room outcomes must accurately reflect the data provided
- Output ONLY the JSON, no markdown formatting
