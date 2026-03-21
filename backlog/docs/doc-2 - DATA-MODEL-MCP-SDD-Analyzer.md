---
id: doc-2
title: 'DATA-MODEL: MCP SDD Analyzer'
type: other
created_date: '2026-03-19 21:11'
---
# Data Model: MCP SDD Analyzer

**Task:** TASK-1  
**Date:** 2026-03-19

---

## Entities

### SDDAnalysisResult

Main output of the `analyze_specification` MCP tool.

```
SDDAnalysisResult
├── weak_points: List[WeakPoint]
├── recommendations: List[Recommendation]
├── unclear_sections: List[UnclearSection]
├── overall_score: float (0.0 - 1.0)
└── verdict: enum ("AI-READY" | "NEEDS-CLARIFICATION" | "NOT-READY")
```

### WeakPoint

Individual issue found in specification.

```
WeakPoint
├── section: str          # Section name or identifier
├── issue: str            # Description of the problem
├── severity: enum        # "critical" | "major" | "minor"
└── suggestion: str       # How to fix
```

### Recommendation

Actionable improvement suggestion.

```
Recommendation
├── priority: enum        # "high" | "medium" | "low"
├── action: str           # What to do
└── rationale: str        # Why it matters
```

### UnclearSection

Ambiguous or missing information.

```
UnclearSection
├── location: str         # Line range or section name
├── question: str         # What's unclear
└── suggested_clarification: str  # What to add
```

---

## Relationships

```
SDDAnalysisResult 1 --* WeakPoint
SDDAnalysisResult 1 --* Recommendation
SDDAnalysisResult 1 --* UnclearSection
```

---

## Integration with Existing Domain

```
Existing:                    New:
─────────────────────────────────────────────
DebateRoom            →      SDDAnalysisResult
DebateMessage         →      WeakPoint (extracted)
Verdict               →      verdict (mapped)
Speaker               →      Agent (Architect, DevLead, QA, Security)
```

---

## MCP Tool Schema

### analyze_specification

**Input:**
```json
{
  "spec_path": "path/to/spec.md"
}
```

**Output:**
```json
{
  "weak_points": [
    {
      "section": "Authentication",
      "issue": "Missing error handling",
      "severity": "major",
      "suggestion": "Add error scenarios"
    }
  ],
  "recommendations": [
    {
      "priority": "high",
      "action": "Add API error codes",
      "rationale": "Required for client implementation"
    }
  ],
  "unclear_sections": [
    {
      "location": "Lines 45-52",
      "question": "What is the session timeout?",
      "suggested_clarification": "Specify timeout in minutes"
    }
  ],
  "overall_score": 0.72,
  "verdict": "NEEDS-CLARIFICATION"
}
```

---

## SDD Agents (New)

| Agent | Role | Position |
|-------|------|----------|
| Architect | Argues spec is complete | PRO |
| DevLead | Finds gaps, ambiguities | CON |
| QA | Identifies untestable requirements | CON |
| Security | Points out security concerns | CON |

---

## Configuration Model

### sdd_config.yaml

```yaml
llm:
  model: "${SDD_MODEL:gpt-4o-mini}"
  temperature: 0.7

debate:
  mode: "simple"  # Fast single-call analysis

agents:
  main:
    name: "Architect"
    prompt: "src/prompts/sdd/architect.md"
  opponents:
    - name: "DevLead"
      prompt: "src/prompts/sdd/devlead.md"
    - name: "QA"
      prompt: "src/prompts/sdd/qa.md"
    - name: "Security"
      prompt: "src/prompts/sdd/security.md"

output:
  format: "json"
  include_suggestions: true
```
