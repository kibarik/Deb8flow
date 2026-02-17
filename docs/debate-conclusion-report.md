# Debate Conclusion Report

## Overview

The Debate Conclusion Report feature generates a `Conclusion.md` file after each debate that summarizes the debate outcome and provides specific improvement recommendations from each debate participant. This helps product managers enhance their product vision and argumentation before actual presentations.

## What It Does

This feature:

- Creates a Conclusion.md file in the debate output directory after every completed debate
- Summarizes the debate question and final verdict
- Provides Q&A summary with 3-10 key discussion points
- Lists improvement recommendations from each participant
- Highlights weak points in TPM's argumentation
- Suggests concrete steps to improve for future debates

## How It Works

### Architecture

```
Debate Completion → Judge Verdict → final_report.md → Conclusion.md Post-Processing → Output
```

### Data Flow

1. Debate completes all rounds
2. Judge generates final verdict
3. final_report.md is generated and becomes immutable
4. Conclusion.md post-processing step analyzes final_report.md
5. Conclusion.md is written to debate output directory

### Workflow Requirements

- **WF-001**: Generation of final_report.md MUST be completed successfully before Conclusion.md
- **WF-002**: Conclusion.md MUST be generated only from the final, immutable final_report.md
- **WF-003**: If final_report.md generation fails, Conclusion.md MUST NOT be generated
- **WF-004**: Conclusion generation SHOULD be reusable (regenerate without repeating debate)

## Usage

### Automatic Generation

Conclusion.md is automatically generated after every completed debate. No additional CLI flags are required.

### Output Location

- **Standard debates**: `{output_dir}/Conclusion.md`
- **Document debates**: `{output_dir}/Conclusion.md`
- **Committee debates**: `committee_output/{run_id}/Conclusion.md`

## Report Structure

The Conclusion.md file follows this structure:

```markdown
# Debate Conclusion: <Debate Title>

## 1. Debate Question
<text of the debate question/topic>

## 2. Final Verdict
- **Winner**: <Role / Name or "No clear winner">
- **Summary**: <1–3 sentences explaining the verdict>

## 3. Q&A Summary
- **Вопрос**: <question 1>
  - **Ответ**: <answer 1>
- **Вопрос**: <question 2>
  - **Ответ**: <answer 2>
[... 3-10 key Q&A pairs]

## 4. How TPM Can Win Next Time

### 4.1 Key Weaknesses in TPM Position
- <weakness 1>
- <weakness 2>

### 4.2 Recommended Improvements
- [ ] <improvement 1>
- [ ] <improvement 2>

## 5. Recommendations by Agent

### От TPM
- [ ] От TPM: <recommendation>

### От BDM
- [ ] От BDM: <recommendation>

### От CPO
- [ ] От CPO: <recommendation>

### От PRO
- [ ] От PRO: <recommendation>

### От CON
- [ ] От CON: <recommendation>

### От Judge / Other
- [ ] От Judge: <recommendation>
```

## Key Features

### Verdict Handling

- **Clear winner**: Shows winner role with summary
- **No clear winner**: Shows "No clear winner" with 2-3 sentence explanation
- **TPM victory**: Indicates TPM won and lists areas for further strengthening
- **TPM defeat**: Identifies winner and provides specific improvement recommendations

### Recommendations

- **Attributed by agent**: Each recommendation is attributed to its source role
- **Format**: "От [Role]: [recommendation text]"
- **Multiple per agent**: Each agent may provide zero, one, or multiple recommendations
- **Empty sections**: If an agent has no recommendations, section shows "Нет рекомендаций"

### TPM Victory Analysis

- **Weakness highlighting**: Identifies unjustified assumptions, uncovered risks, weak connections to metrics
- **Improvement focus**: Recommendations either strengthen strong points or close specific weaknesses
- **Actionable format**: Recommendations formatted as Markdown checklists using `- [ ]`

## Edge Cases

| Scenario | Behavior |
|----------|----------|
| No clear winner | Verdict shows "No clear winner" with 2-3 sentence summary |
| No recommendations from agent | Section exists with "Нет рекомендаций" note |
| Missing output directory | Handle with explicit error messaging |
| Mixed language content | Preserve original language; auto-translation optional |
| Incomplete debate | Conclusion.md MUST NOT be generated |
| final_report.md failure | Conclusion.md MUST NOT be generated; explicit error returned |

## Success Criteria

- **SC-001**: Product Managers can read complete outcome in under 2 minutes
- **SC-002**: 100% of completed debates generate Conclusion.md without errors
- **SC-003**: 90% of recommendations are actionable and specific
- **SC-004**: 100% attribution accuracy for recommendation sources
- **SC-005**: Generation time under 5 seconds after debate completion

## Data Source

- **FR-017**: System MUST use final_report.md as the single source of truth
- **FR-018**: System MUST parse final_report.md to extract:
  - Key debate question/topic
  - Winner information and verdict logic
  - Arguments for and against TPM position
  - Agent comments/remarks for recommendations

## TPM Victory Definition

Victory occurs when the position defended by the TPM (or equivalent role) agent wins, based on:
- Combined argument strength
- Risk coverage
- Negative factors from other participants

## Language Support

- Preserves original language of each recommendation
- Auto-translation is not required
- Supports mixed language content (e.g., Russian + English)
