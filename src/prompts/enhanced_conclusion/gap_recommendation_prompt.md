# Gap & Recommendation Generation

You are analyzing committee debate outputs to identify critical gaps and generate actionable recommendations.

## Mode: {mode}

% if mode == "gaps" %}
## Weaknesses from Role Analyses

{weaknesses}

## Verdict Context

{verdict_rationale}

## Your Task

Identify 3-5 critical gaps by analyzing weaknesses across multiple roles. Look for:
- The same weakness mentioned by multiple roles
- Recurring themes across different perspectives
- Issues that would significantly impact the proposal if not addressed

For each gap, provide:
- title: Short, descriptive title (5-100 characters)
- severity: Gap severity (High/Medium/Low)
- description: Detailed explanation (20-500 characters)
- sources: List of role names who raised this gap (at least 1)
- evidence: Supporting evidence references (at least 1)

## Output Format

```json
{
  "gaps": [
    {
      "title": "Gap title here",
      "severity": "High",
      "description": "Detailed explanation of the gap...",
      "sources": ["CFO", "CTO"],
      "evidence": [
        {
          "room_id": "TPM_vs_CFO",
          "speaker_role": "CFO",
          "turn_index": 3,
          "quote": "Supporting quote (max 200 chars)..."
        }
      ]
    }
    // 3-5 gaps total
  ]
}
```

% elif mode == "recommendations" %}
## Critical Gaps

{gaps}

## Verdict Context

{verdict_rationale}

## Your Task

Generate actionable recommendations to address the critical gaps above.

For each recommendation, you MUST provide:
- priority: Priority level (High/Medium/Low) - base on gap severity
- problem: Problem statement (10-300 characters)
- action: Action to take (10-300 characters)
- metric: Success metric, must be measurable (10-200 characters)
- source_evidence: Evidence reference for this recommendation

## CRITICAL: Problem → Action → Metric Format

Every recommendation MUST follow this exact format:
- **Problem**: What is wrong? (specific issue from gaps)
- **Action**: What should be done? (specific, actionable step)
- **Metric**: How do we know it's fixed? (measurable outcome)

## Constraints

- Maximum 5 high-priority recommendations
- Every recommendation must be traceable to a gap
- Metrics MUST be measurable (specific numbers, dates, or outcomes)
- NO generic "best practices" - be specific to this proposal

## Output Format

```json
{
  "recommendations": [
    {
      "priority": "High",
      "problem": "The PRD lacks specific technical architecture details...",
      "action": "Add a detailed 'Technical Architecture' section to the PRD...",
      "metric": "PRD includes complete technical architecture with component diagram...",
      "source_evidence": {
        "room_id": "TPM_vs_CTO",
        "speaker_role": "CTO",
        "turn_index": 4,
        "quote": "Technical architecture was not adequately defined..."
      }
    }
    // Up to 5 high-priority + unlimited medium/low
  ]
}
```
% endif %