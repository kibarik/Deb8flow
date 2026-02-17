---
work_package_id: WP03
title: Stage 1A - Verdict Extractor with Confidence Calculation
lane: "done"
dependencies: []
base_branch: main
base_commit: 9d5705de96b438c1c93f45e8d9bcaad029b92cfe
created_at: '2026-02-15T22:43:44.590268+00:00'
subtasks:
- T012
- T013
- T014
- T015
- T016
- T017
phase: Phase 1 - Core Pipeline
assignee: ''
agent: "claude"
shell_pid: "85084"
review_status: "approved"
reviewed_by: "ALeks ishmanov"
history:
- timestamp: '2025-02-16T12:00:00Z'
  lane: planned
  agent: system
  shell_pid: ''
  action: Prompt generated via /spec-kitty.tasks
---

# Work Package Prompt: WP03 – Stage 1A - Verdict Extractor with Confidence Calculation

## ⚠️ IMPORTANT: Review Feedback Status

**Read this first if you are implementing this task!**

- **Has review feedback?**: Check the `review_status` field above. If it says `has_feedback`, scroll to the **Review Feedback** section immediately (right below this notice).
- **You must address all feedback** before your work is complete. Feedback items are your implementation TODO list.
- **Mark as acknowledged**: When you understand the feedback feedback and begin addressing it, update `review_status: acknowledged` in the frontmatter.
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
1. Implement verdict extraction from final_report.md with room outcomes parsing
2. Implement confidence level calculation per FR-029 formula
3. Implement contradiction detection in judge rationales
4. Create verdict extraction prompt template

**Success Criteria**:
- VerdictExtractor parses final_report.md and extracts all room outcomes
- Confidence calculated correctly: unanimous=High, 3-1=Medium, 2-2=Low
- Contradictions detected and reduce confidence by 1 level
- Verdict answer extracted with 120-150 word limit
- Unit tests cover all confidence scenarios

---

## Context & Constraints

**Supporting Documents**:
- Spec: `kitty-specs/011-enhanced-committee-debate-conclusion/spec.md` (FR-001 to FR-004, FR-029)
- Data Model: `kitty-specs/011-enhanced-committee-debate-conclusion/data-model.md` (Verdict model)
- Plan: `kitty-specs/011-enhanced-committee-debate-conclusion/plan.md` (Stage 1A design)

**Dependencies**:
- WP01: Pydantic types (Verdict model)
- WP02: Analyzer base class
- WP05: Confidence calculator (can be implemented in this WP for simplicity)

**Constraints**:
- Must use final_report.md as single source of truth
- Must handle varying final_report.md formats
- Must support both Russian and English content
- Performance target: < 3 seconds for verdict extraction

**Architectural Decisions**:
- VerdictExtractor extends EnhancedAnalyzer
- Parse final_report.md using regex/string parsing (no external parsers)
- Confidence calculation implemented in this WP (not separate utility)

---

## Subtasks & Detailed Guidance

### Subtask T012 – Create VerdictExtractor Class
- **Purpose**: Main analyzer for verdict extraction from committee debates
- **Steps**:
  1. Create `src/analyzers/verdict_extractor.py`
  2. Import dependencies:
     ```python
     from src.analyzers.base_analyzer import EnhancedAnalyzer
     from src.types.enhanced_conclusion_types import Verdict
     from typing import Dict, Any
     import re
     import logging
     ```
  3. Define VerdictExtractor class:
     ```python
     class VerdictExtractor(EnhancedAnalyzer):
         """Extract verdict from committee debate final_report.md.

         Parses room outcomes and calculates confidence level per FR-029:
         - Unanimous (4-0 or 0-4) = High
         - Split (3-1 or 1-3) = Medium
         - Tie (2-2) = Low
         - Strong contradictions reduce by 1 level
         """

         def __init__(self, llm_config=None):
             super().__init__(llm_config)
             self.logger = logging.getLogger(self.__class__.__name__)

         def __call__(self, final_report_text: str) -> Verdict:
             """Extract verdict with confidence calculation.

             Args:
                 final_report_text: Full text of final_report.md

             Returns:
                 Verdict object with answer, confidence, rationale, room_outcomes
             """
             self.logger.info("Extracting verdict from final_report.md")

             # Extract room outcomes
             room_outcomes = self._extract_room_outcomes(final_report_text)

             # Extract judge rationales
             judge_rationales = self._extract_judge_rationales(final_report_text)

             # Calculate confidence
             confidence = self._calculate_confidence(room_outcomes, judge_rationales)

             # Generate verdict answer using LLM
             verdict_data = self._generate_verdict_answer(
                 final_report_text, room_outcomes, confidence
             )

             return Verdict(**verdict_data)
     ```

**Files**:
- `src/analyzers/verdict_extractor.py` (new file, ~150 lines)

**Parallel?**: No

**Notes**:
- Follow EnhancedAnalyzer pattern from WP02
- All methods are private except __call__

---

### Subtask T013 – Extract Room Outcomes from final_report.md
- **Purpose**: Parse winner/loser for each debate room
- **Steps**:
  1. Implement `_extract_room_outcomes()`:
     ```python
     def _extract_room_outcomes(self, final_report_text: str) -> Dict[str, str]:
         """Extract winner for each room from final_report.md.

         Args:
             final_report_text: Full text of final_report.md

         Returns:
             Dict mapping room_id to winner (e.g., {"TPM_vs_CPO": "CON"})
         """
         room_outcomes = {}

         # Pattern to match room headers
         # Example: "## TPM vs CPO" or "## Room 1: TPM vs CPO"
         room_pattern = r'##\s*(?:Room\s+\d+:\s*)?(TPM\s+vs\s+(CPO|CFO|CTO|BDM))'

         # Find all room sections
         rooms = re.finditer(room_pattern, final_report_text, re.IGNORECASE)

         for match in rooms:
             room_name = match.group(1).replace(" ", "_")  # "TPM_vs_CPO"
             room_start = match.end()

             # Find next room header or end of document
             next_room = re.search(room_pattern, final_report_text[room_start:], re.IGNORECASE)
             room_end = room_start + next_room.start() if next_room else len(final_report_text)

             room_section = final_report_text[room_start:room_end]

             # Extract winner from room section
             winner = self._extract_winner_from_room(room_section)
             room_outcomes[room_name] = winner

         self.logger.info(f"Extracted {len(room_outcomes)} room outcomes: {room_outcomes}")
         return room_outcomes

     def _extract_winner_from_room(self, room_section: str) -> str:
         """Extract winner from a single room section.

         Looks for patterns like:
         - "Winner: CON" or "Победитель: CON"
         - "The judge rules in favor of CON"
         - "Verdict: CON wins"
         """
         # Try explicit "Winner:" pattern
         winner_pattern = r'(?:Winner|Победитель)\s*:\s*(PRO|CON|TPM|CPO|CFO|CTO|BDM)'
         match = re.search(winner_pattern, room_section, re.IGNORECASE)
         if match:
             return match.group(1).upper()

         # Try "rules in favor of" pattern
         favor_pattern = r'rules?\s+in\s+favor\s+of\s+(PRO|CON)'
         match = re.search(favor_pattern, room_section, re.IGNORECASE)
         if match:
             return match.group(1).upper()

         # Try "Verdict:" pattern
         verdict_pattern = r'Verdict\s*:?\s*(?:\w+\s+)?(?:wins?|victorious)\s*\((PRO|CON)\)'
         match = re.search(verdict_pattern, room_section, re.IGNORECASE)
         if match:
             return match.group(1).upper()

         # Default: log warning and return "UNCLEAR"
         self.logger.warning("Could not determine winner from room section")
         return "UNCLEAR"
     ```

**Files**:
- `src/analyzers/verdict_extractor.py` (extend, ~80 lines)

**Parallel?**: No

**Notes**:
- Handle both English and Russian room headers
- Case-insensitive matching for robustness
- Return "UNCLEAR" if winner cannot be determined

---

### Subtask T014 – Implement Confidence Calculation (FR-029)
- **Purpose**: Calculate confidence level from room outcomes and judge rationales
- **Steps**:
  1. Implement `_calculate_confidence()`:
     ```python
     def _calculate_confidence(
         self,
         room_outcomes: Dict[str, str],
         judge_rationales: list[str]
     ) -> str:
         """Calculate confidence level per FR-029.

         Formula:
         - Unanimous (4-0 or 0-4) = High
         - Split (3-1 or 1-3) = Medium
         - Tie (2-2) = Low
         - Strong contradictions reduce by 1 level

         Args:
             room_outcomes: Dict mapping room_id to winner
             judge_rationales: List of judge rationale texts

         Returns:
             "High", "Medium", or "Low"
         """
         if not room_outcomes:
             return "Low"

         # Count PRO vs CON wins
         pro_wins = sum(1 for winner in room_outcomes.values() if winner == "PRO")
         con_wins = sum(1 for winner in room_outcomes.values() if winner == "CON")
         total_rooms = len(room_outcomes)

         # For committee debates, TPM is always PRO position
         # So we count TPM wins as PRO wins
         tpm_wins = pro_wins

         # Calculate base confidence
         if total_rooms == 0:
             base_confidence = "Low"
         elif tpm_wins == total_rooms or tpm_wins == 0:
             # Unanimous (4-0 or 0-4)
             base_confidence = "High"
         elif abs(tpm_wins - total_rooms / 2) <= 0.5:
             # Tie (2-2)
             base_confidence = "Low"
         else:
             # Split (3-1 or 1-3)
             base_confidence = "Medium"

         # Check for contradictions and reduce confidence
         has_contradictions = self._detect_contradictions(judge_rationales)

         if has_contradictions:
             if base_confidence == "High":
                 return "Medium"
             elif base_confidence == "Medium":
                 return "Low"

         return base_confidence
     ```

**Files**:
- `src/analyzers/verdict_extractor.py` (extend, ~50 lines)

**Parallel?**: No

**Notes**:
- FR-029 formula is explicit - implement exactly as specified
- Contradiction detection implemented in T015

---

### Subtask T015 – Detect Contradictions in Judge Rationales
- **Purpose**: Identify conflicting assessments across judge rationales
- **Steps**:
  1. Implement `_extract_judge_rationales()`:
     ```python
     def _extract_judge_rationales(self, final_report_text: str) -> list[str]:
         """Extract judge rationales from final_report.md.

         Looks for sections containing judge explanations/verdicts.

         Args:
             final_report_text: Full text of final_report.md

         Returns:
             List of judge rationale texts
         """
         rationales = []

         # Pattern to match judge verdict sections
         # Example: "### Judge's Verdict" or "### Verdict"
         verdict_pattern = r'###\s*(?:Judge[\'s]?\s+)?Verdict'

         # Find all verdict sections
         verdicts = re.finditer(verdict_pattern, final_report_text, re.IGNORECASE)

         for match in verdicts:
             verdict_start = match.end()

             # Find next section header or end of document
             next_section = re.search(r'^#+\s', final_report_text[verdict_start:], re.MULTILINE)
             verdict_end = verdict_start + next_section.start() if next_section else len(final_report_text)

             verdict_section = final_report_text[verdict_start:verdict_end].strip()

             if verdict_section:
                 rationales.append(verdict_section)

         self.logger.info(f"Extracted {len(rationales)} judge rationales")
         return rationales
     ```
  2. Implement `_detect_contradictions()`:
     ```python
     def _detect_contradictions(self, rationales: list[str]) -> bool:
         """Detect if judge rationales contain strong contradictions.

         Looks for contradiction indicators like:
         - "however", "but", "although" (contrast)
         - "contradicts", "inconsistent", "conflicting" (explicit contradiction)
         - "on the other hand", "conversely" (opposing views)

         Args:
             rationales: List of judge rationale texts

         Returns:
             True if 2+ contradiction indicators found, False otherwise
         """
         if not rationales:
             return False

         # Combine all rationales
         combined = " ".join(rationales).lower()

         # Contradiction keywords
         strong_contradictions = ["contradicts", "inconsistent", "conflicting"]
         contrast_words = ["however", "but", "although", "conversely", "on the other hand"]

         # Count strong contradictions
         strong_count = sum(1 for word in strong_contradictions if word in combined)

         # Count contrast words (but require 2+ to avoid false positives)
         contrast_count = sum(1 for word in contrast_words if word in combined)

         # Return True if strong contradictions OR 2+ contrast words
         return strong_count >= 1 or contrast_count >= 2
     ```

**Files**:
- `src/analyzers/verdict_extractor.py` (extend, ~70 lines)

**Parallel?**: No

**Notes**:
- Contradiction detection is heuristic-based
- Lower threshold for strong contradictions (1 is enough)
- Higher threshold for contrast words (avoid false positives)

---

### Subtask T016 – Create Verdict Extraction Prompt Template
- **Purpose**: LLM prompt for generating verdict answer text
- **Steps**:
  1. Create `src/prompts/enhanced_conclusion/` directory
  2. Create `src/prompts/enhanced_conclusion/verdict_extraction_prompt.md`:
     ```markdown
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
     ```

**Files**:
- `src/prompts/enhanced_conclusion/verdict_extraction_prompt.md` (new file, ~60 lines)

**Parallel?**: No

**Notes**:
- Prompt emphasizes word count constraint (120-150 words)
- Confidence level is provided as input (not calculated by LLM)
- Room outcomes summary helps LLM generate accurate text

---

### Subtask T017 – Unit Tests for Verdict Extractor
- **Purpose**: Verify verdict extraction and confidence calculation
- **Steps**:
  1. Create `tests/test_enhanced_conclusion/test_verdict_extractor.py`
  2. Create test fixtures:
     - `fixtures/unanimous_final_report.md` (4-0 outcome)
     - `fixtures/split_final_report.md` (3-1 outcome)
     - `fixtures/tie_final_report.md` (2-2 outcome)
  3. Test room outcome extraction:
     - Extract 4 rooms correctly
     - Handle missing room (return "UNCLEAR")
     - Handle English and Russian headers
  4. Test confidence calculation:
     - Unanimous (4-0) → High
     - Unanimous (0-4) → High
     - Split (3-1) → Medium
     - Split (1-3) → Medium
     - Tie (2-2) → Low
     - Unanimous with contradictions → Medium
     - Split with contradictions → Low
  5. Test contradiction detection:
     - No contradictions → False
     - Strong contradiction ("contradicts") → True
     - Multiple contrast words → True
  6. Test verdict answer generation:
     - Verify answer is 120-150 words
     - Verify confidence matches calculated value
     - Verify rationale is present

**Files**:
- `tests/test_enhanced_conclusion/test_verdict_extractor.py` (new file, ~200 lines)
- `tests/fixtures/unanimous_final_report.md` (new file, ~100 lines)
- `tests/fixtures/split_final_report.md` (new file, ~100 lines)
- `tests/fixtures/tie_final_report.md` (new file, ~100 lines)

**Parallel?**: Yes

**Notes**:
- Use actual final_report.md excerpts as fixtures
- Mock LLM for answer generation tests (focus on logic, not LLM)
- Test word count validator explicitly

---

## Test Strategy

**Test Location**: `tests/test_enhanced_conclusion/test_verdict_extractor.py`

**Test Commands**:
```bash
# Run all verdict extractor tests
pytest tests/test_enhanced_conclusion/test_verdict_extractor.py -v

# Run specific test
pytest tests/test_enhanced_conclusion/test_verdict_extractor.py::test_confidence_unanimous -v

# Run with coverage
pytest tests/test_enhanced_conclusion/test_verdict_extractor.py --cov=src/analyzers/verdict_extractor
```

**Fixtures Needed**:
- Sample final_report.md with 4 rooms (unanimous outcome)
- Sample final_report.md with 4 rooms (split outcome)
- Sample final_report.md with 4 rooms (tie outcome)
- Sample final_report.md with contradictions in judge rationales

**Coverage Target**: > 90%

---

## Risks & Mitigations

**Risk 1**: final_report.md format varies across debates
- **Mitigation**: Use flexible regex patterns, handle multiple header formats

**Risk 2**: Contradiction detection has false positives
- **Mitigation**: Use 2+ threshold for contrast words, only 1 for strong contradictions

**Risk 3**: Word count validation fails on non-English text
- **Mitigation**: Test with Russian text, use simple split() which works for most languages

**Risk 4**: LLM generates answer outside word count limits
- **Mitigation**: Pydantic validator will catch this, prompt emphasizes constraint

---

## Review Guidance

**Key Acceptance Checkpoints**:
1. VerdictExtractor extends EnhancedAnalyzer correctly
2. Room outcomes extracted correctly from final_report.md
3. Confidence calculated per FR-029 formula exactly
4. Contradictions detected and reduce confidence appropriately
5. Verdict answer is 120-150 words (validated by Pydantic)
6. Unit tests cover all confidence scenarios
7. Both English and Russian content supported

**Review Before Approval**:
- Verify FR-029 formula is implemented exactly
- Check room outcome parsing handles edge cases (missing winner, unclear format)
- Verify contradiction detection is not too aggressive
- Test with actual final_report.md samples

---

## Activity Log

> **CRITICAL**: Activity log entries MUST be in chronological order (oldest first, newest last).

### How to Add Activity Log Entries

**When adding an entry**:
1. Scroll to the bottom of this file (Activity Log section below "Valid lanes")
2. **APPEND the new entry at the END** (do NOT prepend or insert in middle)
3. Use exact format: `- YYYY-MM-DDTHH:MM:SSZ – agent_id – lane=<lane> – <action>`
4. Timestamp MUST be current time in UTC (check with `date -u "+%Y-%m-%dT%H:%M:%SZ"`)
5. Lane MUST match the frontmatter `lane:` field exactly
6. Agent ID should identify who made the change (claude-sonnet-4-5, codex, etc.)

**Format**:
```
- YYYY-MM-DDTHH:MM:SSZ – <agent_id> – lane=<lane> – <brief action description>
```

**Initial entry**:
- 2025-02-16T12:00:00Z – system – lane=planned – Prompt created.

---

### Updating Lane Status

To change a work package's lane, either:

1. **Edit directly**: Change the `lane:` field in frontmatter AND append activity log entry (at the end)
2. **Use CLI**: `spec-kitty agent tasks move-task <WPID> --to <lane> --note "message"` (recommended)

The CLI command updates both frontmatter and activity log automatically.

**Valid lanes**: `planned`, `doing`, `for_review`, `done`

### Optional Phase Subdirectories

For large features, organize prompts under `tasks/` to keep bundles grouped while maintaining lexical ordering.
- 2026-02-15T22:43:44Z – claude-sonnet-4-5 – shell_pid=75662 – lane=doing – Assigned agent via workflow command
- 2026-02-15T22:48:24Z – claude-sonnet-4-5 – shell_pid=75662 – lane=for_review – Ready for review: Implemented VerdictExtractor with FR-029 confidence calculation. Room outcome extraction from final_report.md with English/Russian support. Contradiction detection in judge rationales. Verdict extraction prompt with 120-150 word constraint. 43 unit tests passing.
- 2026-02-15T23:40:42Z – claude – shell_pid=85084 – lane=doing – Started review via workflow command
- 2026-02-15T23:40:44Z – claude – shell_pid=85084 – lane=done – Review passed: 43/43 tests passing
