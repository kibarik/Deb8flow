# Feature Specification: Debate Conclusion Report

**Feature Branch**: `009-debate-conclusion-report`
**Created**: 2025-02-15
**Status**: Draft
**Input**: User description: "хочу по результатам дебатов дополнительно видеть файл Conclusion.md в котором выводится краткая информация: вопрос -> ответ. А далее краткий чеклист что нужно сделать чтобы улучшить документ перед следующими дебатами чтобы TPM получить победу перед всеми остальными участниками. Список доработок в формате "От BDM: ____", "от CPO: ____" и тд далее. От каждого агента может быть бесконечное количество рекомендаций и замечаний которые нужно доработать"

## Clarifications

### Session 2025-02-15

- **Q**: What is the data source for generating Conclusion.md? → **A**: final_report.md is the single source of truth; all analysis builds from this document
- **Q**: How is TPM victory defined? → **A**: Victory = TPM's position wins when combined argument strength and risk coverage outweigh negative factors from other participants
- **Q**: What is the primary goal of Conclusion.md? → **A**: Highlight weak points in TPM's argumentation and provide concrete steps to reduce risks and strengthen position for future debates
- **Q**: When should Conclusion.md be generated? → **A**: As a separate post-processing step after final_report.md is completed and immutable
- **Q**: How should multi-language content be handled? → **A**: Preserve original language of each recommendation; auto-translation is not required

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Generate Conclusion Report After Debate (Priority: P1)

As a Product Manager preparing for a real product defense, I want to receive a structured Conclusion.md file after each debate that summarizes the debate outcome and provides specific improvement recommendations from each debate participant, so that I can enhance my product vision and argumentation before the actual presentation.

**Why this priority**: This is the core value of the feature - without the conclusion report, the product manager cannot systematically improve their product defense based on debate feedback.

**Independent Test**: Can be fully tested by running a complete debate (standard or document-based) and verifying that a Conclusion.md file is created in the expected output location with proper content structure.

**Acceptance Scenarios**:

1. **Given** a completed debate with a winner declared, **When** the debate finishes, **Then** a Conclusion.md file is created in the debate output directory containing the debate question, final verdict, and structured recommendations from each participant
2. **Given** a debate where TPM (Product Manager) wins, **When** reading the Conclusion.md, **Then** the report clearly indicates TPM victory and lists improvement areas that could strengthen the defense further
3. **Given** a debate where TPM loses to another participant, **When** reading the Conclusion.md, **Then** the report identifies the winner and provides specific recommendations from each agent on what TPM should improve

---

### User Story 2 - Agent-Specific Improvement Recommendations (Priority: P2)

As a Product Manager, I want to see detailed recommendations attributed to specific debate participants (BDM, CPO, etc.), so that I can understand which stakeholders raised which concerns and address them systematically.

**Why this priority**: Attribution helps the product manager understand different perspectives - BDM focuses on business viability, CPO on product strategy, etc. This is valuable but the feature still provides value without detailed attribution.

**Independent Test**: Can be tested by verifying that recommendations in the Conclusion.md are properly grouped by agent role and formatted with the "От [Role]: [recommendation]" pattern.

**Acceptance Scenarios**:

1. **Given** a debate with multiple participants, **When** reading the recommendations section, **Then** each recommendation is clearly attributed to its source agent with the format "От BDM: [recommendation]" or "От CPO: [recommendation]"
2. **Given** an agent provides multiple recommendations, **When** reading the Conclusion.md, **Then** all recommendations from that agent are listed under their attribution
3. **Given** a debate with only standard PRO/CON debaters, **When** recommendations are generated, **Then** they are attributed to the appropriate debater role

---

### Edge Cases

- **No clear winner**: Verdict shows "No clear winner" with 2-3 sentence summary explaining why there's no unambiguous winner
- **No recommendations from agent**: Each agent subsection MUST exist with "Нет рекомендаций" note when agent provides none
- **Missing output directory**: System MUST handle non-existent or non-writable output directories gracefully with explicit error messaging
- **Mixed language content**: System SHOULD preserve original language of each recommendation; auto-translation is optional
- **Incomplete debate**: If debate is interrupted or fails, Conclusion.md MUST NOT be generated
- **final_report.md failure**: If final_report.md generation fails or is incomplete, system MUST NOT attempt to generate Conclusion.md and MUST return explicit error status

## Workflow & Process *(mandatory)*

The Conclusion.md generation is implemented as a separate post-processing step in the debate pipeline:

**Process Flow**:
1. Debate completes all rounds → Judge generates final verdict
2. final_report.md is generated and becomes immutable
3. Conclusion.md post-processing step analyzes final_report.md
4. Conclusion.md is written to debate output directory

**Workflow Requirements**:
- **WF-001**: Generation of final_report.md MUST be completed successfully before Conclusion.md generation step can start
- **WF-002**: Conclusion.md MUST be generated only from the final, immutable final_report.md after all agents have completed the debate and final verdict is recorded
- **WF-003**: If final_report.md generation fails or is incomplete, system MUST NOT attempt to generate Conclusion.md and MUST return explicit error status for the debate pipeline
- **WF-004**: Conclusion generation SHOULD be implemented as a separate post-processing step that can be reused (regenerate Conclusion.md without repeating the entire debate)

## Requirements *(mandatory)*

### Functional Requirements

**Data Source & Extraction**:
- **FR-001**: System MUST create a Conclusion.md file in the debate output directory after every completed debate
- **FR-017**: System MUST use final_report.md as the single source of truth for generating Conclusion.md
- **FR-018**: System MUST parse final_report.md to extract:
  - Key debate question/topic
  - Winner information and verdict logic
  - Arguments for and against TPM position
  - Agent comments/remarks from which recommendations are formed

**Content & Structure**:
- **FR-002**: Conclusion.md MUST contain the debate question/topic prominently at the top
- **FR-003**: Conclusion.md MUST contain the final verdict/outcome indicating which participant won
- **FR-011**: Q&A Summary section MUST contain 3-10 key "question-answer" pairs aggregated from final_report.md (key discussion points, not full log)
- **FR-004**: System MUST extract and format improvement recommendations from each debate participant
- **FR-005**: Recommendations MUST be attributed to specific agents using the format "От [Role]: [recommendation text]"
- **FR-006**: Each agent MAY provide zero, one, or multiple recommendations
- **FR-013**: Recommendations section SHOULD be formatted as Markdown checklists using `- [ ]` for easy transfer to task trackers
- **FR-015**: If an agent has no recommendations, their subsection MUST still exist with a note "Нет рекомендаций"
- **FR-007**: System MUST support both standard debates and document-based debates
- **FR-009**: Conclusion.md MUST be formatted as Markdown for easy reading
- **FR-010**: System MUST handle the case where no clear winner is determined by indicating the outcome appropriately

**TPM Victory Analysis**:
- **FR-019**: System MUST explicitly highlight weak points in TPM's case (unjustified assumptions, uncovered risks, weak connection to metrics/business results)
- **FR-020**: Each recommendation in Conclusion.md SHOULD either strengthen a strong point (add data, cases, arguments) or close a specific weakness/risk (clarify, recalculate, rephrase)

**"How TPM Can Win Next Time" Section**:
- **FR-021**: Section "How TPM Can Win Next Time" MUST contain:
  - Subsection listing key weaknesses in TPM position
  - Subsection with actionable improvements (formatted as list/checklist)

### Key Entities

- **Debate Conclusion**: The output document containing question, verdict, and recommendations; generated after each debate; attributes include question, verdict, recommendations list
- **Recommendation**: A specific improvement suggestion from a debate participant; attributes include source agent role, recommendation text, and optional priority/context
- **Agent Role**: The role/identity of a debate participant (e.g., TPM, BDM, CPO, PRO, CON); used to attribute recommendations
- **TPM Victory**: Victory occurs when the position defended by the TPM (or equivalent role) agent wins, based on combined argument strength and risk coverage outweighing negative factors from other participants

### Conclusion.md Structure

The Conclusion.md file MUST follow this structure:

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
[... 3-10 key Q&A pairs aggregated from final_report.md]

## 4. How TPM Can Win Next Time

### 4.1 Key Weaknesses in TPM Position
- <weakness 1>
- <weakness 2>
[... list of identified weaknesses]

### 4.2 Recommended Improvements
- [ ] <improvement 1>
- [ ] <improvement 2>
[... actionable improvements as checklist]

## 5. Recommendations by Agent

### От TPM
- [ ] От TPM: <recommendation>
[... or "Нет рекомендаций" if none]

### От BDM
- [ ] От BDM: <recommendation>
[... or "Нет рекомендаций" if none]

### От CPO
- [ ] От CPO: <recommendation>
[... or "Нет рекомендаций" if none]

### От PRO
- [ ] От PRO: <recommendation>
[... or "Нет рекомендаций" if none]

### От CON
- [ ] От CON: <recommendation>
[... or "Нет рекомендаций" if none]

### От Judge / Other
- [ ] От Judge: <recommendation>
[... or "Нет рекомендаций" if none]
```

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Product Managers can read the complete debate outcome and recommendations in under 2 minutes
- **SC-002**: 100% of completed debates generate a Conclusion.md file without errors
- **SC-003**: 90% of recommendations are actionable and specific enough to guide document/product improvements
- **SC-004**: Product Managers can identify which participant provided each recommendation with 100% accuracy
- **SC-005**: The time from debate completion to Conclusion.md availability is under 5 seconds
