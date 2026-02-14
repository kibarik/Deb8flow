# Feature Specification: Debate Conclusion Report

**Feature Branch**: `009-debate-conclusion-report`
**Created**: 2025-02-15
**Status**: Draft
**Input**: User description: "хочу по результатам дебатов дополнительно видеть файл Conclusion.md в котором выводится краткая информация: вопрос -> ответ. А далее краткий чеклист что нужно сделать чтобы улучшить документ перед следующими дебатами чтобы TPM получить победу перед всеми остальными участниками. Список доработок в формате "От BDM: ____", "от CPO: ____" и тд далее. От каждого агента может быть бесконечное количество рекомендаций и замечаний которые нужно доработать"

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

- What happens when a debate ends without a clear winner (judge cannot decide)?
- How does the system handle debates where participants provide no specific improvement recommendations?
- What happens when the debate output directory doesn't exist or isn't writable?
- How are recommendations formatted when an agent provides feedback in a language other than Russian?
- What happens when the debate is interrupted or fails to complete?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST create a Conclusion.md file in the debate output directory after every completed debate
- **FR-002**: Conclusion.md MUST contain the debate question/topic prominently at the top
- **FR-003**: Conclusion.md MUST contain the final verdict/outcome indicating which participant won
- **FR-004**: System MUST extract and format improvement recommendations from each debate participant
- **FR-005**: Recommendations MUST be attributed to specific agents using the format "От [Role]: [recommendation text]"
- **FR-006**: Each agent MAY provide zero, one, or multiple recommendations
- **FR-007**: System MUST support both standard debates and document-based debates
- **FR-008**: The recommendations section MUST focus on actionable improvements for the Product Manager to win future debates
- **FR-009**: Conclusion.md MUST be formatted as Markdown for easy reading
- **FR-010**: System MUST handle the case where no clear winner is determined by indicating the outcome appropriately

### Key Entities

- **Debate Conclusion**: The output document containing question, verdict, and recommendations; generated after each debate; attributes include question, verdict, recommendations list
- **Recommendation**: A specific improvement suggestion from a debate participant; attributes include source agent role, recommendation text, and optional priority/context
- **Agent Role**: The role/identity of a debate participant (e.g., TPM, BDM, CPO, PRO, CON); used to attribute recommendations

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Product Managers can read the complete debate outcome and recommendations in under 2 minutes
- **SC-002**: 100% of completed debates generate a Conclusion.md file without errors
- **SC-003**: 90% of recommendations are actionable and specific enough to guide document/product improvements
- **SC-004**: Product Managers can identify which participant provided each recommendation with 100% accuracy
- **SC-005**: The time from debate completion to Conclusion.md availability is under 5 seconds
