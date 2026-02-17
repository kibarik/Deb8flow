# Role-Based Analysis Extraction

You are analyzing a committee debate to extract strengths and weaknesses for a specific role.

## Debate Content

{final_report_text}

## Role to Analyze

{role}

## Your Task

Extract 3-5 strengths and 3-5 weaknesses for this role based on the debate content.

For each strength/weakness, you MUST provide:
- description: Clear explanation of the point (10-500 characters)
- evidence: Complete evidence reference with:
  - room_id: Which room this came from (e.g., "TPM_vs_CPO")
  - speaker_role: Who made this point (e.g., "CPO")
  - turn_index: Turn number (estimate if not explicit)
  - quote: Supporting quote (max 200 characters)

## Output Format

Output ONLY valid JSON with this exact structure:

```json
{
  "strengths": [
    {
      "description": "Clear explanation of what was strong...",
      "evidence": {
        "room_id": "TPM_vs_CPO",
        "speaker_role": "CPO",
        "turn_index": 3,
        "quote": "Supporting quote text (max 200 chars)..."
      }
    }
    // 3-5 strengths total
  ],
  "weaknesses": [
    {
      "description": "Clear explanation of what was weak...",
      "evidence": {
        "room_id": "TPM_vs_CFO",
        "speaker_role": "CFO",
        "turn_index": 5,
        "quote": "Supporting quote text (max 200 chars)..."
      }
    }
    // 3-5 weaknesses total
  ]
}
```

## Constraints

- Extract 3-5 strengths (minimum 3, maximum 5)
- Extract 3-5 weaknesses (minimum 3, maximum 5)
- EVERY strength/weakness MUST have complete evidence reference
- Quotes MUST be truncated to 200 characters max
- room_id format: "TPM_vs_CPO", "TPM_vs_CFO", etc.
- speaker_role must be actual role name from debate
- turn_index must be non-negative integer
- Output ONLY the JSON, no markdown formatting
- Use only information from the debate content provided
