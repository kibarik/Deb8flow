---
work_package_id: WP04
title: Stage 1B - Role Analyzer with Evidence Extraction
lane: "done"
dependencies: []
base_branch: main
base_commit: 9d5705de96b438c1c93f45e8d9bcaad029b92cfe
created_at: '2026-02-15T23:16:16.862826+00:00'
subtasks:
- T018
- T019
- T020
- T021
- T022
- T023
- T024
phase: Phase 1 - Core Pipeline
assignee: ''
agent: "claude"
shell_pid: "78821"
review_status: "approved"
reviewed_by: "ALeks ishmanov"
history:
- timestamp: '2025-02-16T12:00:00Z'
  lane: planned
  agent: system
  shell_pid: ''
  action: Prompt generated via /spec-kitty.tasks
---

# Work Package Prompt: WP04 – Stage 1B - Role Analyzer with Evidence Extraction

## ⚠️ IMPORTANT: Review Feedback Status

**Read this first if you are implementing this task!**

- **Has review feedback?**: Check the `review_status` field above. If it says `has_feedback`, scroll to the **Review Feedback** section immediately (right below this notice).
- **You must address all feedback** before your work is complete. Feedback items are your implementation TODO list.
- **Mark as acknowledged**: When you understand the feedback and begin addressing it, update `review_status: acknowledged` in the frontmatter.
- **Report progress**: As you address each feedback item, update the Activity Log explaining what you changed.

---

## Review Feedback

> **Populated by `/spec-kitty.review`** – Reviewers add detailed feedback here when work needs changes. Implementation must address every item listed below before returning for re-review.

*[This section is empty initially. Reviewers will populate it if the work is returned from review. If you see feedback here, treat each item as a must-do before completion.]*

---

## Markdown Formatting
Wrap HTML/XML tags in backticks: `` `<div>` ``, `` `<script>` ``
Use language identifiers in code blocks: ````python`, ````bash`

---

## Objectives & Success Criteria

**Objectives**:
1. Implement role-based analysis extraction (strengths/weaknesses per role)
2. Extract evidence references with FR-031 compliance (room_id, speaker_role, turn_index, quote)
3. Enforce 3-5 bullet limit per role (FR-030)
4. Create role analysis prompt template

**Success Criteria**:
- RoleAnalyzer parses final_report.md and identifies all participating roles
- 3-5 strengths extracted per role with complete evidence references
- 3-5 weaknesses extracted per role with complete evidence references
- All evidence references include: room_id, speaker_role, turn_index, quote (max 200 chars)
- Roles that appear in some rooms but not others are handled correctly
- Unit tests verify evidence extraction completeness

---

## Context & Constraints

**Supporting Documents**:
- Spec: `kitty-specs/011-enhanced-committee-debate-conclusion/spec.md` (FR-005 to FR-009, FR-031)
- Data Model: `kitty-specs/011-enhanced-committee-debate-conclusion/data-model.md` (RoleAnalysis, EvidenceReference)
- Plan: `kitty-specs/011-enhanced-committee-debate-conclusion/plan.md` (Stage 1B design)

**Dependencies**:
- WP01: Pydantic types (RoleAnalysis, EvidenceReference models)
- WP02: Analyzer base class

**Constraints**:
- Must use final_report.md as single source of truth
- Must extract complete evidence references (FR-031: 100% compliance required)
- Must enforce 3-5 bullet limit per role (FR-030)
- Must support both Russian and English content
- Performance target: < 5 seconds for role analysis

**Architectural Decisions**:
- RoleAnalyzer extends EnhancedAnalyzer
- Parse final_report.md using regex/string parsing
- Use LLM to extract strengths/weaknesses with evidence references
- Validate evidence reference completeness in post-processing

---

## Subtasks & Detailed Guidance

### Subtask T018 – Create RoleAnalyzer Class
- **Purpose**: Main analyzer for role-based analysis extraction
- **Steps**:
  1. Create `src/analyzers/role_analyzer.py`
  2. Import dependencies:
     ```python
     from src.analyzers.base_analyzer import EnhancedAnalyzer
     from src.types.enhanced_conclusion_types import RoleAnalysis, EvidenceReference, Strength, Weakness
     from typing import List, Dict, Any
     import re
     import logging
     ```
  3. Define RoleAnalyzer class:
     ```python
     class RoleAnalyzer(EnhancedAnalyzer):
         """Extract role-based analysis from committee debate final_report.md.

         For each role (TPM, CPO, CFO, CTO, BDM):
         - Extract 3-5 strengths with supporting evidence
         - Extract 3-5 weaknesses with supporting evidence
         - Each strength/weakness must have complete evidence reference (FR-031)
         """

         def __init__(self, llm_config=None):
             super().__init__(llm_config)
             self.logger = logging.getLogger(self.__class__.__name__)

         def __call__(self, final_report_text: str) -> List[RoleAnalysis]:
             """Extract role-based analysis from final_report.md.

             Args:
                 final_report_text: Full text of final_report.md

             Returns:
                 List of RoleAnalysis objects (one per participating role)
             """
             self.logger.info("Extracting role-based analysis from final_report.md")

             # Identify participating roles
             participating_roles = self._identify_participating_roles(final_report_text)

             # Extract role analyses
             role_analyses = []
             for role in participating_roles:
                 analysis = self._extract_role_analysis(final_report_text, role)
                 role_analyses.append(analysis)

             self.logger.info(f"Extracted {len(role_analyses)} role analyses")
             return role_analyses
     ```

**Files**:
- `src/analyzers/role_analyzer.py` (new file, ~200 lines)

**Parallel?**: No

**Notes**:
- Follow EnhancedAnalyzer pattern from WP02
- Process each role independently

---

### Subtask T019 – Identify Participating Roles
- **Purpose**: Parse final_report.md to identify all participating roles
- **Steps**:
  1. Implement `_identify_participating_roles()`:
     ```python
     def _identify_participating_roles(self, final_report_text: str) -> List[str]:
         """Identify all roles participating in the debate.

         Args:
             final_report_text: Full text of final_report.md

         Returns:
             List of role names (e.g., ["TPM", "CPO", "CFO", "CTO", "BDM"])
         """
         # Standard committee roles
         committee_roles = {"TPM", "CPO", "CFO", "CTO", "BDM"}

         # Find all mentioned roles in room headers
         room_pattern = r'##\s*(?:Room\s+\d+:\s*)?(TPM\s+vs\s+(CPO|CFO|CTO|BDM))'
         matches = re.findall(room_pattern, final_report_text, re.IGNORECASE)

         # Extract mentioned roles
         mentioned_roles = {"TPM"}  # TPM is always in committee debates
         for opponent in matches:
             mentioned_roles.add(opponent.upper())

         # Return only standard committee roles that were mentioned
         participating = [role for role in committee_roles if role in mentioned_roles]

         self.logger.info(f"Identified participating roles: {participating}")
         return participating
     ```

**Files**:
- `src/analyzers/role_analyzer.py` (extend, ~30 lines)

**Parallel?**: No

**Notes**:
- TPM is always included in committee debates
- Only return standard committee roles that were mentioned

---

### Subtask T020 & T021 – Extract Strengths and Weaknesses with Evidence
- **Purpose**: Extract 3-5 strengths and 3-5 weaknesses per role with evidence references
- **Steps**:
  1. Implement `_extract_role_analysis()`:
     ```python
     def _extract_role_analysis(self, final_report_text: str, role: str) -> RoleAnalysis:
         """Extract analysis for a single role.

         Args:
             final_report_text: Full text of final_report.md
             role: Role name to analyze (e.g., "TPM", "CPO")

         Returns:
             RoleAnalysis object with strengths and weaknesses
         """
         # Load prompt template
         prompt_template = self._load_prompt('role_analysis_prompt.md')

         # Format prompt with role and final_report_text
         formatted_prompt = self._format_prompt(
             prompt_template,
             role=role,
             final_report_text=final_report_text
         )

         # Invoke LLM with retry
         llm_response = self._invoke_with_retry(
             self._create_text_chain(),
             {"input": formatted_prompt}
         )

         # Parse response
         analysis_data = self._parse_role_analysis_response(llm_response, role)

         # Create RoleAnalysis object (validates 3-5 limit)
         return RoleAnalysis(**analysis_data)

     def _parse_role_analysis_response(self, response: str, role: str) -> Dict[str, Any]:
         """Parse LLM response into RoleAnalysis data.

         Args:
             response: JSON response from LLM
             role: Role name for this analysis

         Returns:
             Dict with role_name, strengths, weaknesses
         """
         import json

         # Clean response (remove markdown code blocks)
         cleaned = response.strip()
         if cleaned.startswith("```"):
             lines = cleaned.split('\n')
             if lines[0].startswith("```"):
                 lines = lines[1:]
             if lines and lines[-1].strip() == "```":
                 lines = lines[:-1]
             cleaned = '\n'.join(lines).strip()

         # Parse JSON
         try:
             data = json.loads(cleaned)
         except json.JSONDecodeError as e:
             self.logger.error(f"Failed to parse role analysis response: {e}")
             raise ValueError(f"Invalid JSON from LLM: {e}")

         # Validate structure
         if "strengths" not in data or "weaknesses" not in data:
             raise ValueError("Missing required fields in LLM response")

         # Convert to proper format
         strengths = [
             Strength(
                 description=s["description"],
                 evidence=EvidenceReference(**s["evidence"])
             )
             for s in data["strengths"][:5]  # Max 5
         ]

         weaknesses = [
             Weakness(
                 description=w["description"],
                 evidence=EvidenceReference(**w["evidence"])
             )
             for w in data["weaknesses"][:5]  # Max 5
         ]

         return {
             "role_name": role,
             "strengths": strengths,
             "weaknesses": weaknesses
         }
     ```

**Files**:
- `src/analyzers/role_analyzer.py` (extend, ~80 lines)

**Parallel?**: No

**Notes**:
- Limit to 5 items per category (enforced by slice [:5])
- Pydantic validator will raise error if > 5

---

### Subtask T022 – Extract Evidence References (FR-031 Compliance)
- **Purpose**: Parse evidence references from final_report.md with all required fields
- **Steps**:
  1. Implement evidence extraction helper:
     ```python
     def _extract_evidence_reference(
         self,
         final_report_text: str,
         role: str,
         quote_text: str
     ) -> EvidenceReference:
         """Extract complete evidence reference for a quote.

         Args:
             final_report_text: Full text of final_report.md
             role: Role being analyzed
             quote_text: Quote to locate in final_report

         Returns:
             EvidenceReference with room_id, speaker_role, turn_index, quote
         """
         # Find the quote in final_report_text
         # This is a simplified implementation - production would use more sophisticated matching

         # Try to find the room containing this quote
         room_id = self._find_room_for_quote(final_report_text, quote_text)

         # Try to identify the speaker
         speaker_role = self._identify_speaker_for_quote(final_report_text, quote_text, role)

         # Estimate turn index (simplified)
         turn_index = self._estimate_turn_index(final_report_text, quote_text)

         # Truncate quote to 200 chars
         truncated_quote = quote_text[:200] if len(quote_text) > 200 else quote_text

         return EvidenceReference(
             room_id=room_id,
             speaker_role=speaker_role,
             turn_index=turn_index,
             quote=truncated_quote
         )

     def _find_room_for_quote(self, final_report_text: str, quote: str) -> str:
         """Find which room contains a given quote."""
         # Split into room sections
         room_pattern = r'##\s*(TPM\s+vs\s+(CPO|CFO|CTO|BDM))'
         rooms = list(re.finditer(room_pattern, final_report_text, re.IGNORECASE))

         for i, match in enumerate(rooms):
             room_start = match.end()
             room_name = match.group(1).replace(" ", "_")

             # Find next room or end of document
             next_room = rooms[i + 1] if i + 1 < len(rooms) else None
             room_end = next_room.start() if next_room else len(final_report_text)

             room_section = final_report_text[room_start:room_end]

             # Check if quote is in this room
             if quote[:50] in room_section:  # Match first 50 chars
                 return room_name

         # Default: return "UNKNOWN"
         return "UNKNOWN"

     def _identify_speaker_for_quote(
         self,
         final_report_text: str,
         quote: str,
         context_role: str
     ) -> str:
         """Identify speaker for a quote."""
         # Simplified: use context role as default
         # In production, would parse speaker labels from transcript
         return context_role

     def _estimate_turn_index(self, final_report_text: str, quote: str) -> int:
         """Estimate turn index for a quote."""
         # Simplified: count occurrence position
         # In production, would parse actual turn numbers from transcript
         position = final_report_text.find(quote[:50])
         if position == -1:
             return 0

         # Rough estimate: assume ~500 chars per turn
         return max(0, position // 500)
     ```

**Files**:
- `src/analyzers/role_analyzer.py` (extend, ~70 lines)

**Parallel?**: No

**Notes**:
- Evidence extraction is heuristic-based
- Production implementation would use more sophisticated parsing
- FR-031 requires all fields, so defaults are provided when extraction fails

---

### Subtask T023 – Create Role Analysis Prompt Template
- **Purpose**: LLM prompt for extracting role-based analysis with evidence
- **Steps**:
  1. Create `src/prompts/enhanced_conclusion/role_analysis_prompt.md`:
     ```markdown
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
     ```

**Files**:
- `src/prompts/enhanced_conclusion/role_analysis_prompt.md` (new file, ~80 lines)

**Parallel?**: No

**Notes**:
- Emphasizes evidence reference requirements (FR-031)
- Specifies exact room_id format
- Limits to 3-5 per category

---

### Subtask T024 – Unit Tests for Role Analyzer
- **Purpose**: Verify role analysis extraction and evidence references
- **Steps**:
  1. Create `tests/test_enhanced_conclusion/test_role_analyzer.py`
  2. Test role identification:
     - Extract all 5 committee roles
     - Handle missing role (only 4 roles present)
  3. Test strength/weakness extraction:
     - Extract 3-5 strengths per role
     - Extract 3-5 weaknesses per role
     - Verify limits enforced (6 items fails)
  4. Test evidence references (FR-031):
     - All strengths have evidence references
     - All weaknesses have evidence references
     - Each reference has: room_id, speaker_role, turn_index, quote
     - Quotes truncated to 200 chars
  5. Test role analysis parsing:
     - Valid JSON parsed correctly
     - Invalid JSON raises error
     - Missing fields raises error

**Files**:
- `tests/test_enhanced_conclusion/test_role_analyzer.py` (new file, ~180 lines)

**Parallel?**: Yes

**Notes**:
- Mock LLM for extraction tests (focus on logic)
- Test evidence reference completeness thoroughly
- Test with both English and Russian content

---

## Test Strategy

**Test Location**: `tests/test_enhanced_conclusion/test_role_analyzer.py`

**Test Commands**:
```bash
# Run all role analyzer tests
pytest tests/test_enhanced_conclusion/test_role_analyzer.py -v

# Run specific test
pytest tests/test_enhanced_conclusion/test_role_analyzer.py::test_evidence_completeness -v

# Run with coverage
pytest tests/test_enhanced_conclusion/test_role_analyzer.py --cov=src/analyzers/role_analyzer
```

**Fixtures Needed**:
- Sample final_report.md with all 5 committee roles
- Sample final_report.md with 4 roles (one missing)
- Mock LLM response with valid role analysis JSON
- Mock LLM response with invalid JSON

**Coverage Target**: > 90%

---

## Risks & Mitigations

**Risk 1**: Evidence extraction fails to find room_id or speaker
- **Mitigation**: Provide default values ("UNKNOWN", context_role) when extraction fails

**Risk 2**: LLM generates more than 5 strengths/weaknesses
- **Mitigation**: Slice to first 5 items before creating RoleAnalysis object

**Risk 3**: Evidence reference format varies across final_report.md
- **Mitigation**: Use flexible parsing, provide defaults for missing fields

**Risk 4**: Quote truncation loses important context
- **Mitigation**: Truncate to 200 chars as required by FR-031, log warning

---

## Review Guidance

**Key Acceptance Checkpoints**:
1. RoleAnalyzer extends EnhancedAnalyzer correctly
2. All participating roles identified correctly
3. 3-5 strengths extracted per role with evidence
4. 3-5 weaknesses extracted per role with evidence
5. 100% of evidence references include all required fields (FR-031)
6. Quotes truncated to 200 chars max
7. Unit tests verify evidence completeness
8. Both English and Russian content supported

**Review Before Approval**:
- Verify evidence reference extraction handles edge cases
- Check 3-5 limit is enforced (Pydantic validator)
- Test with actual final_report.md samples
- Verify FR-031 compliance (100% evidence field completeness)

---

## Activity Log

> **CRITICAL**: Activity log entries MUST be in chronological order (oldest first, newest last).

**Initial entry**:
- 2025-02-16T12:00:00Z – system – lane=planned – Prompt created.

---

### Updating Lane Status

To change a work package's lane, either:

1. **Edit directly**: Change the `lane:` field in frontmatter AND append activity log entry (at the end)
2. **Use CLI**: `spec-kitty agent tasks move-task <WPID> --to <lane> --note "message"` (recommended)

The CLI command updates both frontmatter and activity log automatically.

**Valid lanes**: `planned`, `doing`, `for_review`, `done`
- 2026-02-15T23:16:17Z – claude – shell_pid=78821 – lane=doing – Assigned agent via workflow command
- 2026-02-15T23:18:51Z – claude – shell_pid=78821 – lane=for_review – Ready for review: RoleAnalyzer implemented with evidence extraction per FR-031, 32 unit tests passing
- 2026-02-15T23:40:51Z – claude – shell_pid=78821 – lane=done – Review passed: 32/32 tests passing
