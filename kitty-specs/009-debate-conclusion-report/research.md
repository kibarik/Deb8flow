# Research: Debate Conclusion Report Feature

**Feature**: 009-debate-conclusion-report
**Date**: 2025-02-15
**Mission**: software-dev

## Executive Summary

This research documents the technical foundation for implementing a debate conclusion report feature that generates a structured `Conclusion.md` file after each debate. The conclusion report extracts key information from `final_report.md` (for committee debates) or the debate state (for standard/document debates) and provides actionable recommendations for the Product Manager.

**Key Decision**: The implementation will use a hybrid approach:
- For **committee debates**: Parse existing `final_report.md` files (single source of truth)
- For **standard/document debates**: Extract conclusion data directly from debate state at verdict stage

**Rationale**: Committee debates already generate comprehensive `final_report.md` files, while standard/document debates currently only output to console. By extracting from the debate state for the latter, we ensure consistent conclusion generation across all debate types.

---

## 1. Data Source Analysis

### 1.1 Committee Debates (final_report.md)

**Location**: `committee_output/{run_id}/final_report.md`

**Generation Function**: `product_committee.py:generate_final_report()` (lines 1258-1432)

**Structure Documentation**:

```markdown
# Product Committee Report

**Run ID:** RUN_20260214_112438_----100
**Generated:** 2026-02-14T11:26:45.480653+00:00

---

## Committee Question
[debate topic text]

---

## Executive Summary
This report synthesizes debate results from 4 committee rooms:
- **Successful rooms:** 4
- **Failed rooms:** 0
- **Skipped rooms:** 0

---

## Room-by-Room Analysis

### TPM_vs_CPO
**Status:** success
**Winner:** CON
**Judge Explanation:** [verdict text]
**Key Takeaways:**
- [bullet points]

**Full Dialogue:**
**PRO** (opening) ✓: [message]
**CON** (rebuttal) ✓: [message]
...

### TPM_vs_CFO
[Similar structure]

### TPM_vs_CTO
[Similar structure]

### TPM_vs_BDM
[Similar structure]

---

## TPM Reflection
### Learned Insights
- [insights]

### Potential Assessment
**Overall:** medium
**Confidence:** 0.7

### Recommendations
1. [recommendation]
2. [recommendation]
...

---

## Metadata
- **PRD:** [path]
- **Roles directory:** [path]
- **Model:** [model name]
- **Start time:** [timestamp]
- **End time:** [timestamp]
```

**Parsing Strategy**:
1. Use regex to extract sections by header pattern `## (.+)`
2. Parse room results from "Room-by-Room Analysis" section
3. Extract TPM reflection from "TPM Reflection" section
4. Map room IDs (e.g., "TPM_vs_CPO") to opponent roles

**Evidence**: See `research/source-register.csv` entries for committee report examples.

### 1.2 Standard/Document Debates (Debate State)

**State Structure** (from `debate_state.py`):

```python
class DebateState(TypedDict):
    debate_topic: str              # Debate question
    positions: Dict[str, str]      # PRO/CON positions
    messages: List[DebateMessage]  # Full debate history
    stage: str                     # Current stage
    speaker: str                   # Current speaker
    document_input: str            # Document content (if applicable)
    document_context: str          # Extracted context (if applicable)
    pro_custom_prompt: str         # PRO role prompt (if applicable)
    con_custom_prompt: str         # CON role prompt (if applicable)
```

**Extraction Strategy**:
1. Extract `debate_topic` for the question
2. Parse `messages` for Q&A pairs (filter by `stage` and `validated`)
3. Extract judge verdict from message with `speaker == "judge"` and `stage == "verdict"`
4. Use `pro_custom_prompt` presence to detect role-based debates

**Evidence**: See `debate_state.py` and workflow implementations.

---

## 2. TPM Role Detection

### 2.1 Committee Debates

**Detection Method**: Parse room IDs from `final_report.md`

**Room Naming Convention**: `TPM_vs_{ROLE}`

**Opponent Roles**:
- `CPO` - Chief Product Officer
- `CFO` - Chief Financial Officer
- `CTO` - Chief Technology Officer
- `BDM` - Business Development Manager

**TPM Position**: Always the PRO debater in committee debates

**Extraction Logic**:
```python
# From room ID "TPM_vs_CPO"
opponent_role = room_id.split("_vs_")[1]  # "CPO"
tpm_position = "PRO"  # Always PRO in committee debates
```

**Evidence**: See `product_committee.py` room creation logic (lines 300-350).

### 2.2 Standard Debates

**Detection Method**: Check `pro_custom_prompt` field in state

**Role Prompts Location**: `prompts/roles/`

**Available Roles**:
- `tpm.txt` - Technical Product Manager
- `cpo.txt` - Chief Product Officer
- `cfo.txt` - Chief Financial Officer
- `cto.txt` - Chief Technology Officer
- `bdm.txt` - Business Development Manager

**Detection Logic**:
```python
# If pro_custom_prompt contains "TPM" or "Technical Product Manager"
is_tpm = "TPM" in state.get("pro_custom_prompt", "") or "Technical Product Manager" in state.get("pro_custom_prompt", "")

# For standard debates without custom prompts, treat PRO as generic debater
```

**Default Behavior**: If no custom prompt detected, treat PRO as generic debater (no specific role)

**Evidence**: See role prompt loading in `document_debate_cli.py` (lines 159-178).

---

## 3. Verdict Analysis

### 3.1 Judge Verdict Structure

**Location**: `nodes/judge_node.py`

**Output Format**:
```python
{
    "winner": "pro" | "con",  # Always lowercase in JSON
    "justification": "explanation text"
}
```

**Message Format**:
```python
{
    "speaker": "judge",
    "content": "WINNER: CON\n\nREASON: [explanation]",
    "validated": True,
    "stage": "verdict"
}
```

### 3.2 TPM Victory Determination

**Committee Debates**:
- TPM wins if winner == "PRO" (TPM is always PRO)
- TPM loses if winner == "CON" (opponent)

**Standard Debates**:
- If TPM detected: same logic as committee
- If no TPM: generic PRO/CON victory

**Parsing Logic**:
```python
# From final_report.md room verdict section
winner = room_verdict.get("winner")  # "PRO" or "CON"
tpm_wins = (winner == "PRO") if is_committee_debate else None

# From debate state judge message
judge_msg = [m for m in messages if m.get("speaker") == "judge"][-1]
winner = parse_winner_from_content(judge_msg["content"])  # Extract from "WINNER: PRO/CON"
```

### 3.3 "No Clear Winner" Handling

**Current Behavior**: Judge always returns a winner (no draw option)

**Proposed Enhancement**:
- Detect inconclusive verdicts from justification text
- Keywords: "unclear", "close", "mixed", "debatable", "ambiguous"
- If detected, set winner to "No clear winner"

**Evidence**: See `judge_node.py` verdict parsing (lines 18-51).

---

## 4. Q&A Extraction Strategy

### 4.1 Source Identification

**Committee Debates**: Extract from "Full Dialogue" sections in room analysis

**Standard Debates**: Extract from `messages` array in debate state

### 4.2 Key Q&A Selection Criteria

**Definition of "Key"**: Q&A pairs that represent:
1. **Major argument shifts**: When PRO/CON positions evolve
2. **Fact-check moments**: When claims are challenged
3. **Judge interventions**: When judge provides feedback
4. **Opening statements**: Initial position presentations
5. **Closing arguments**: Final summaries

**Extraction Algorithm**:
```python
key_pairs = []

# Extract opening statements
key_pairs.append(("Opening PRO", extract_opening_pro(messages)))
key_pairs.append(("Opening CON", extract_opening_con(messages)))

# Extract fact-check challenges
for msg in messages:
    if msg["validated"] == False:
        question = f"Challenge to {msg['speaker']}"
        answer = msg["content"]
        key_pairs.append((question, answer))

# Extract judge verdict
judge_msg = get_judge_message(messages)
key_pairs.append(("Final Verdict", judge_msg["content"]))

# Limit to 3-10 pairs (prioritize by stage and validation status)
return key_pairs[:10]
```

### 4.3 Aggregation Strategy

**Group Similar Questions**: Use embedding similarity or keyword matching

**Priority Order**:
1. Judge verdict (always included)
2. Opening statements (if available)
3. Fact-check challenges (validated == False)
4. Major position shifts (detected by content similarity)
5. Closing arguments

**Evidence**: See dialogue format in committee reports and message structure in `debate_state.py`.

---

## 5. Weakness Detection

### 5.1 TPM Weakness Sources

**Committee Debates**:
1. **Judge verdicts**: From "Judge Explanation" in each room
2. **Key takeaways**: Negative points in "Key Takeaways" sections
3. **TPM reflection**: Self-identified weaknesses in "TPM Reflection"

**Standard Debates**:
1. **Judge justification**: From verdict message
2. **Fact-check failures**: Messages with `validated == False`
3. **CON arguments**: Criticisms raised by opponent

### 5.2 Weakness Categories

**From Specification** (FR-019):
- Unjustified assumptions
- Uncovered risks
- Weak connection to metrics/business results
- Missing data/evidence
- Logical fallacies

**Extraction Logic**:
```python
weaknesses = []

# From judge verdict
if "lack" in verdict or "insufficient" in verdict:
    weaknesses.append({
        "category": "insufficient_evidence",
        "description": verdict.lower(),
        "severity": "high"
    })

# From fact-check failures
for msg in messages:
    if msg["validated"] == False:
        weaknesses.append({
            "category": "unverified_claim",
            "description": msg["content"],
            "severity": "medium"
        })

# From TPM reflection (if available)
if reflection:
    for insight in reflection.get("insights", []):
        if "weak" in insight.lower() or "lack" in insight.lower():
            weaknesses.append({
                "category": "self_identified",
                "description": insight,
                "severity": "low"
            })
```

### 5.3 Severity Assessment

**High**: Directly contradicted by evidence or judge
**Medium**: Criticized by opponent without refutation
**Low**: Self-identified weakness

**Evidence**: See verdict patterns in committee reports and fact-check logic in `fact_check_node.py`.

---

## 6. Workflow Integration

### 6.1 Integration Point

**Location**: After `judge_node`, before `END`

**Current Flow**:
```
... → fact_check_node → fact_check_router_node → counter → ...
→ final_argument → fact_check → judge_node → END
```

**Proposed Flow**:
```
... → judge_node → conclusion_report_node → END
```

### 6.2 State Availability

**Available at Conclusion Node**:
```python
{
    "debate_topic": str,           # Question
    "messages": List[DebateMessage], # Full history
    "document_context": str,        # If document-based
    "pro_custom_prompt": str,       # Role detection
    "con_custom_prompt": str,       # Role detection
}
```

**No Additional State Fields Needed**: All required data is available

### 6.3 Output Directory Handling

**Committee Debates**:
- Base: `committee_output/{run_id}/`
- Output: `committee_output/{run_id}/Conclusion.md`

**Standard/Document Debates**:
- Current: No output directory
- Proposed: Create `debates_output/{run_id}/` directory
- Output: `debates_output/{run_id}/Conclusion.md`

**Directory Creation**:
```python
from pathlib import Path

output_dir = Path("debates_output") / run_id
output_dir.mkdir(parents=True, exist_ok=True)
```

**Evidence**: See committee output handling in `product_committee.py` (lines 1457-1459).

---

## 7. Recommendation Generation

### 7.1 Source Attribution

**Committee Debates**:
- Extract from "Key Takeaways" in each room
- Extract from "TPM Reflection" recommendations
- Attribute by room opponent role (CPO, CFO, CTO, BDM)

**Standard Debates**:
- Extract from CON arguments
- Extract from judge justification
- Attribute by speaker role (pro/con/judge)

### 7.2 Recommendation Format

**Specification Requirement** (FR-005): `"От [Role]: [recommendation text]"`

**Examples**:
- "От CPO: Add specific user metrics to validate market need"
- "От Judge: Provide more evidence for the claimed 50% improvement"
- "От TPM: Need to clarify the revenue model assumptions"

### 7.3 Extraction Logic

```python
recommendations = []

# From room takeaways (committee)
for room in rooms:
    opponent_role = extract_opponent_role(room["room_id"])  # "CPO", "CFO", etc.
    for takeaway in room["key_takeaways"]:
        if is_actionable(takeaway):
            recommendations.append({
                "agent_role": opponent_role,
                "text": takeaway,
                "priority": assess_priority(takeaway)
            })

# From TPM reflection
for rec in reflection.get("recommendations", []):
    recommendations.append({
        "agent_role": "TPM",
        "text": rec,
        "priority": "medium"
    })
```

### 7.4 Actionability Assessment

**Criteria for Actionable**:
- Specific (not "do better", but "add X metric")
- Concrete (not "improve", but "increase by 20%")
- Testable (can be verified in future debate)

**Evidence**: See recommendation patterns in committee reports.

---

## 8. Open Questions & Risks

### 8.1 Open Questions

1. **Multi-language Handling**: How to detect and preserve non-Russian text?
   - **Current Approach**: Preserve original language without translation
   - **Risk**: May create mixed-language output files

2. **final_report.md Format Changes**: What if committee report structure changes?
   - **Mitigation**: Parse defensively with multiple regex patterns
   - **Fallback**: Extract from debate state if parsing fails

3. **Standard Debate Output**: Should standard debates generate any output files?
   - **Decision**: Create `debates_output/` directory for consistency
   - **Rationale**: Enables conclusion generation for all debate types

### 8.2 Technical Risks

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| final_report.md format changes | Medium | High | Defensive parsing; fallback to state |
| TPM role not identifiable | Low | Medium | Default to PRO; log warning |
| Performance degradation | Low | Low | Cache parsed data; stream output |
| File system permissions | Low | Medium | Explicit error handling; create dirs |

### 8.3 Implementation Risks

| Risk | Mitigation |
|------|------------|
| Breaking existing workflows | Add as optional post-processing step |
| Increased latency | Optimize parsing; cache results |
| Test coverage gaps | Follow TDD; write tests first |

---

## 9. Decisions & Rationale

### Decision 1: Hybrid Data Source Approach

**Decision**: Use `final_report.md` for committee debates, debate state for standard/document debates

**Rationale**:
- Committee debates already have comprehensive reports
- Standard debates have no file output
- Avoid re-processing debate history for committee debates
- Ensure consistent conclusion generation across all types

**Evidence**: See committee report structure in `product_committee.py`.

### Decision 2: Post-Processing Node Pattern

**Decision**: Implement as separate node after judge verdict

**Rationale**:
- Reusable without repeating debates
- Clear separation of concerns
- Follows existing BaseComponent pattern
- Can be disabled/enable easily

**Evidence**: See node pattern in `nodes/base_component.py`.

### Decision 3: No New State Fields

**Decision**: Use existing state fields; no new fields required

**Rationale**:
- All required data is available
- Minimize state complexity
- Backward compatible with existing workflows
- Reduces migration risk

**Evidence**: See `DebateState` definition in `debate_state.py`.

### Decision 4: Defensive Parsing Strategy

**Decision**: Parse `final_report.md` with multiple fallback patterns

**Rationale**:
- Committee report format may evolve
- Need robustness against format changes
- Graceful degradation if parsing fails

**Evidence**: See room parsing logic in `product_committee.py`.

---

## 10. Next Steps

1. **Create data-model.md**: Define entity structures based on research findings
2. **Update source-register.csv**: Log all referenced code locations
3. **Update evidence-log.csv**: Document parsing strategies and examples
4. **Proceed to Phase 1**: Create design artifacts (contracts, quickstart guide)
5. **Generate work packages**: Use `/spec-kitty.tasks` to create implementation tasks

---

## Appendix: Research Methods

**Methods Used**:
1. **Code exploration**: Examined node implementations, workflow definitions
2. **File analysis**: Studied committee report structure and format
3. **State analysis**: Reviewed debate state definition and transitions
4. **Pattern recognition**: Identified role detection and verdict patterns

**Tools Used**:
- File exploration agents
- Code search and analysis
- Structure documentation

**Limitations**:
- Limited access to actual committee report examples
- No access to production debate logs
- Standard debate output not fully documented

**Validation Needed**:
- Test parsing against real committee reports
- Verify role detection with various configurations
- Validate weakness detection accuracy
