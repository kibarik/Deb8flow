# Feature Specification: Enhanced Committee Debate Conclusion Report

**Feature Branch**: `011-enhanced-committee-debate-conclusion`
**Created**: 2025-02-15
**Status**: Draft
**Mission**: software-dev
**Input**: User wants to transform the conclusion report from a generic summary into an actionable product improvement plan with role-specific analysis, prioritized recommendations, and evidence-based insights.

---

## Executive Summary

The current conclusion report (feature 009) produces generic, low-value summaries that don't provide actionable insights. This enhancement transforms the conclusion report into the **most valuable output** of the debate system by:

1. **Clear Verdict**: Direct answer to the user's question with confidence level
2. **Role-Based Analysis**: Strengths and weaknesses extracted from each participant's perspective (TPM, CPO, CFO, CTO, BDM)
3. **Evidence-Based Recommendations**: Only include recommendations directly grounded in actual debate findings
4. **Prioritized Action Plan**: "Problem → Action → Metric" format for measurable improvements
5. **Concise but Comprehensive**: Actionable insights without verbosity

**Scope**: Committee debates first (multi-role debates) with extensible architecture for future standard/document debate support.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Generate Actionable Conclusion from Committee Debate (Priority: P1)

As a Product Manager who just ran a committee debate on a product question, I want to receive a concise, actionable conclusion report that summarizes the verdict and provides specific PRD/strategy improvements, so that I can immediately understand what changes to make without reading hundreds of lines of debate transcripts.

**Why this priority**: This is the core value proposition - turning debate data into actionable product improvements.

**Independent Test**: Run a complete committee debate and verify the generated conclusion.md contains clear verdict, role-based analysis, and prioritized recommendations with problem→action→metric linkage.

**Acceptance Scenarios**:

1. **Given** a completed committee debate with TPM vs. CPO/CFO/CTO/BDM rooms, **When** the debate finishes, **Then** conclusion.md contains a clear verdict answering the user's question with confidence level
2. **Given** multiple debate rooms with different winners, **When** reading the conclusion, **Then** the report summarizes overall outcomes and identifies patterns across rooms
3. **Given** debate content contains specific criticisms from different roles, **When** reading the role analysis section, **Then** strengths and weaknesses are attributed to specific roles with supporting evidence
4. **Given** actionable recommendations are generated, **When** reading the action plan, **Then** each item follows the format "Problem → Action → Metric" with clear priority

---

### User Story 2 - Evidence-Based Recommendations Only (Priority: P1)

As a Product Manager, I want recommendations that are directly grounded in actual debate findings rather than generic advice, so that I can trust the recommendations are relevant to my specific product context.

**Why this priority**: Without evidence grounding, recommendations become generic noise rather than actionable insights.

**Independent Test**: Verify that every recommendation in the conclusion report references specific debate content (arguments, criticisms, judge feedback).

**Acceptance Scenarios**:

1. **Given** a recommendation is included in the conclusion, **When** examining its source, **Then** it must be traceable to specific arguments or criticisms raised during the debate
2. **Given** a debate reveals no specific gaps in a certain area, **When** reading recommendations, **Then** no generic recommendations appear for that area
3. **Given** the judge provides specific feedback on weaknesses, **When** recommendations are generated, **Then** they directly address the judge's identified weaknesses

---

### User Story 3 - Prioritized Action Plan with Metrics (Priority: P2)

As a Product Manager, I want recommendations prioritized by impact with measurable success criteria, so that I can focus on high-value improvements first and track completion.

**Why this priority**: Prioritization and metrics transform insights from interesting to actionable.

**Independent Test**: Verify the action plan section contains prioritized items where each recommendation has an associated metric for validation.

**Acceptance Scenarios**:

1. **Given** multiple recommendations are generated, **When** reading the action plan, **Then** items are ordered by priority (high/medium/low)
2. **Given** a recommendation is listed, **When** examining its format, **Then** it includes "Problem → Action → Metric" structure
3. **Given** a recommendation like "Add Risks & Mitigations section", **When** reading the metric, **Then** it specifies something like "Section added to PRD with 5+ identified risks and mitigation strategies"

---

### Edge Cases

- **Tie / No clear winner**: Verdict shows split decision with breakdown by room and summary of conflicting perspectives
- **Single room debate**: Role-based analysis still applies, but only includes participants from that room
- **Mixed language content**: Preserve original language for quotes/recommendations; analysis can be in primary language
- **No actionable findings**: Report states "No actionable recommendations generated - debate did not reveal specific gaps"
- **Judge provides minimal feedback**: System still extracts insights from debate content, not just verdict
- **Debate interruption**: If debate fails or is incomplete, enhanced conclusion MUST NOT be generated

---

## Workflow & Process *(mandatory)*

The enhanced conclusion report extends the existing conclusion report workflow with deeper analysis:

**Process Flow**:
1. Debate completes all rounds → Judge generates final verdict
2. final_report.md is generated and becomes immutable
3. **NEW**: Enhanced analysis phase extracts:
   - Verdict with confidence level
   - Role-specific strengths/weaknesses
   - Evidence-based gaps
   - Prioritized recommendations with metrics
4. Enhanced conclusion.md is written to debate output directory

**Workflow Requirements**:
- **WF-001**: Enhanced conclusion generation MUST use final_report.md as single source of truth
- **WF-002**: Enhanced conclusion generation MUST be implemented as extensible pipeline with role-agnostic core
- **WF-003**: Role-specific analysis MUST be optional module that can be disabled for non-committee debates
- **WF-004**: Every recommendation MUST be traceable to specific debate content (quotes, arguments, verdict)
- **WF-005**: System MUST support both Russian and English debate content with proper character encoding
- **WF-006**: Enhanced conclusion.md MUST be written to `committee_output/{run_id}/conclusion.md` (same directory as final_report.md)

---

## Requirements *(mandatory)*

### Functional Requirements

#### Verdict & Summary
- **FR-001**: Conclusion MUST start with clear verdict answering the user's original question
- **FR-002**: Verdict MUST include confidence level (High/Medium/Low) based on debate outcome clarity
- **FR-003**: For committee debates, verdict MUST summarize overall outcomes across all rooms (e.g., "Opponents won 3/4 rooms")
- **FR-004**: Summary MUST be concise (3-5 sentences maximum) while capturing key insights

#### Role-Based Analysis
- **FR-005**: System MUST extract and analyze strengths by role (TPM, CPO, CFO, CTO, BDM)
- **FR-006**: System MUST extract and analyze weaknesses by role
- **FR-007**: Each strength/weakness MUST include supporting evidence (quote or reference to specific argument)
- **FR-008**: Role analysis MUST identify patterns across rooms (e.g., "CFO consistently raised unit economics concerns")
- **FR-009**: System MUST handle roles that appear in some rooms but not others

#### Critical Gaps Identification
- **FR-010**: System MUST identify critical gaps revealed across debate rooms
- **FR-011**: Gaps MUST be ranked by severity based on:
  - Number of roles who raised the concern
  - Strength of arguments/evidence
  - Judge emphasis on the issue
- **FR-012**: Each gap MUST include description and source attribution

#### Actionable Recommendations
- **FR-013**: System MUST generate recommendations ONLY when directly grounded in debate findings
- **FR-014**: Each recommendation MUST follow format: "Problem → Action → Metric"
- **FR-015**: Recommendations MUST be prioritized (High/Medium/Low)
- **FR-016**: Metric MUST be specific and measurable (e.g., "PRD includes X with Y criteria")
- **FR-017**: If no actionable gaps found, system MUST explicitly state "No actionable recommendations"

#### Content & Structure
- **FR-018**: Enhanced conclusion.md MUST be written to `committee_output/{run_id}/conclusion.md` (same directory as final_report.md)
- **FR-019**: Enhanced conclusion.md MUST replace existing conclusion.md format
- **FR-020**: Report MUST be formatted as Markdown for readability
- **FR-021**: Report MUST support both Russian and English content properly
- **FR-022**: Report structure MUST follow the template defined in Output Structure section

### Extensibility Requirements
- **FR-023**: Analysis pipeline MUST have role-agnostic core for future standard/document debate support
- **FR-024**: Role-specific analysis MUST be optional module that can be disabled
- **FR-025**: System MUST support custom role definitions beyond standard committee roles

### Quality Requirements
- **FR-026**: Every recommendation MUST be traceable to specific debate content
- **FR-027**: System MUST NOT generate generic "best practices" recommendations unsupported by debate findings
- **FR-028**: Report generation time MUST be under 10 seconds for typical committee debate
- **FR-029**: Confidence level MUST be calculated using: unanimous victory (4-0 or 0-4) = High; 3-1 split = Medium; 2-2 tie = Low; strong contradictions in judge rationales reduce confidence by one level
- **FR-030**: Each section MUST observe length limits for 60-second readability: Verdict max 120-150 words; per-role strengths/weaknesses max 3-5 bullets; Critical Gaps max 5 items; High Priority actions max 5 items
- **FR-031**: Every evidence_reference MUST include: room_id, speaker_role, turn_index, and supporting quote (max 200 characters) for traceability and validation

### Key Entities

- **Enhanced Conclusion Report**: The output document containing verdict, role analysis, gaps, and recommendations; generated after committee debates; attributes include verdict, confidence_level, role_analyses, critical_gaps, recommendations
- **Verdict**: Clear answer to the user's question; attributes include answer_text, confidence_level (calculated per FR-029), supporting_rationale
- **Evidence Reference**: Traceable reference to debate content; attributes include room_id, speaker_role, turn_index, quote (max 200 characters)
- **Role Analysis**: Analysis of strengths/weaknesses from a specific role's perspective; attributes include role_name, strengths[] (3-5 bullets max), weaknesses[] (3-5 bullets max), evidence_references[] (per FR-031)
- **Critical Gap**: A significant weakness or risk identified across multiple debate participants; attributes include description, severity_level, source_roles[], supporting_evidence[] (per FR-031); max 5 gaps total
- **Actionable Recommendation**: A specific improvement with problem→action→metric structure; attributes include priority, problem_description, action_text, success_metric, source_evidence (per FR-031); max 5 high-priority items

---

## Output Structure

The Enhanced Conclusion.md file MUST follow this structure:

```markdown
# Enhanced Conclusion: <Debate Question>

## Verdict
**Answer**: <Direct answer to user's question>
**Confidence**: <High | Medium | Low>
**Rationale**: <2-3 sentence explanation based on debate outcomes>

**Room Outcomes**: <For committee debates - e.g., "Opponents won 3/4 rooms (TPM won only vs CTO)">

**Length Limit**: 120-150 words total

---

## Analysis by Role

### TPM (Technical Product Manager)
**Strengths**:
- <Strength 1>: <Supporting evidence: [room_id, speaker_role, turn_index, quote (max 200 chars)]>
- <Strength 2>: <Supporting evidence: [room_id, speaker_role, turn_index, quote (max 200 chars)]>

**Weaknesses**:
- <Weakness 1>: <Supporting evidence: [room_id, speaker_role, turn_index, quote (max 200 chars)]>
- <Weakness 2>: <Supporting evidence: [room_id, speaker_role, turn_index, quote (max 200 chars)]>

**Length Limit**: 3-5 bullets each for Strengths and Weaknesses

### CPO (Chief Product Officer)
**Strengths**:
- <Strength 1>: <Supporting evidence: [room_id, speaker_role, turn_index, quote (max 200 chars)]>

**Weaknesses**:
- <Weakness 1>: <Supporting evidence: [room_id, speaker_role, turn_index, quote (max 200 chars)]>

**Length Limit**: 3-5 bullets each for Strengths and Weaknesses

[... repeat for CFO, CTO, BDM as applicable]

---

## Critical Gaps Identified

<Ranked list of gaps by severity>

1. **<Gap Title>** (Severity: High)
   - **Description**: <What gap was identified>
   - **Sources**: <Which roles raised this>
   - **Evidence**: [room_id, speaker_role, turn_index, quote (max 200 chars)]

2. **<Gap Title>** (Severity: Medium)
   - **Description**: <What gap was identified>
   - **Sources**: <Which roles raised this>
   - **Evidence**: [room_id, speaker_role, turn_index, quote (max 200 chars)]

**Length Limit**: Maximum 5 critical gaps

---

## Action Plan (Prioritized)

### High Priority
1. **<Problem>** → **<Action>** → **<Metric>**
   - *Source: [room_id, speaker_role, turn_index, quote (max 200 chars)]*

2. **<Problem>** → **<Action>** → **<Metric>**
   - *Source: [room_id, speaker_role, turn_index, quote (max 200 chars)]*

**Length Limit**: Maximum 5 High Priority items

### Medium Priority
[... same format ...]

### Low Priority
[... same format ...]

---

## Metadata
- **Debate Type**: Committee
- **Rooms Analyzed**: <number and list>
- **Generated At**: <timestamp>
- **Confidence Score**: <0.0-1.0>
```

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Product Managers can read the complete conclusion report and understand the verdict in under 60 seconds (enforced via FR-030 length limits)
- **SC-002**: 100% of recommendations include specific, measurable success criteria (metric field populated)
- **SC-003**: 95% of recommendations are traceable to specific debate content (evidence reference with room_id, speaker_role, turn_index per FR-031)
- **SC-004**: Report generation time is under 10 seconds for typical committee debate (4 rooms)
- **SC-005**: Zero generic "best practices" recommendations - all grounded in actual debate findings
- **SC-006**: Role-based analysis correctly attributes strengths/weaknesses with 90% accuracy (validated against manual review of sample debates)
- **SC-007**: 100% of evidence references include all required fields: room_id, speaker_role, turn_index, quote (max 200 chars)

### Quality Indicators

- **QI-001**: Users rate the conclusion report as "actionable" or "very actionable" in 80%+ of use cases
- **QI-002**: Users report they can implement improvements without re-reading the full debate transcript in 90%+ of cases
- **QI-003**: Report format is consistent across 100% of committee debates

---

## Assumptions

1. **final_report.md is the single source of truth**: All analysis builds from this document; no direct access to raw state needed
2. **Committee debate structure**: Assumes standard committee roles (TPM, CPO, CFO, CTO, BDM) but designed for extensibility
3. **Language support**: Assumes Russian and English content; proper UTF-8 encoding required
4. **Judge verdict format**: Assumes judge provides winner + justification; system extracts insights from both
5. **Existing conclusion report infrastructure**: Feature 009 provides base infrastructure; this feature enhances analysis depth

---

## Dependencies

### Technical Dependencies
- **Feature 009 (Debate Conclusion Report)**: Base infrastructure for conclusion report generation
- **final_report.md generation**: Must complete successfully before enhanced conclusion
- **LangGraph state management**: For accessing debate completion status and output paths
- **LLM API access**: For generating analysis and recommendations

### Data Dependencies
- **Committee debate output**: Multiple rooms with TPM vs. other roles
- **Judge verdicts**: Winner + justification from each room
- **Full debate transcripts**: For extracting evidence and quotes

---

## Clarifications

### Session 2025-02-15
- Q: Where should the conclusion.md file be located? → A: committee_output/{run_id}/conclusion.md
- Q: What is the explicit formula for confidence level calculation? → A: unanimous (4-0) = High, 3-1 = Medium, 2-2 = Low; strong contradictions in judge rationales reduce confidence by one level
- Q: What are the length limits for each section to ensure 60-second readability? → A: Verdict: 120-150 words; per-role strengths/weaknesses: 3-5 bullets; Critical gaps: max 5; High-priority actions: max 5
- Q: What is the format for evidence references? → A: Must include room_id, speaker_role, turn_index, and short quote (max 200 characters)

---

## Open Questions / Considerations

1. ~~**Verdict confidence calculation**: Should confidence be based on vote unanimity (4-0 split = high, 3-1 = medium, 2-2 = low) or judge justification quality?~~
   - **RESOLVED**: FR-029 defines explicit formula: unanimous (4-0 or 0-4) = High; 3-1 split = Medium; 2-2 tie = Low; strong contradictions in judge rationales reduce confidence by one level

2. **Role analysis depth**: How much detail per role? Bullet points or paragraph summaries?
   - **RESOLVED**: FR-030 specifies 3-5 bullets per role for strengths/weaknesses

3. **Recommendation prioritization methodology**: Should priority be based on severity, frequency mentioned, or combination?
   - **Assumption**: Combination - severity weighted by number of roles who raised the concern

4. **Standard debate support**: Should this feature immediately support standard debates or phase after committee debates?
   - **Assumption**: Committee debates first (as specified), with extensible architecture for future phases

5. **File output location**: ~~conclusion.md MUST be written to committee_output/{run_id}/conclusion.md~~
   - **RESOLVED**: FR-018 specifies exact output path

6. **Evidence reference format**: ~~You require traceability, but no format is specified~~
   - **RESOLVED**: FR-031 defines format: room_id, speaker_role, turn_index, quote (max 200 chars)
