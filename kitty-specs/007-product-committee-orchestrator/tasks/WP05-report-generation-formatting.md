---
work_package_id: WP05
title: Report Generation & Formatting
lane: "doing"
dependencies: []
subtasks:
- T025
- T026
- T027
- T028
- T029
- T030
phase: Foundation
---

## Work Package Prompt: WP05 – Report Generation & Formatting

**Summary**: Implement final markdown report generator that synthesizes all room results, reflection, and metadata into human-readable committee report with all required sections.

**Priority**: P1 (Reporting - primary user output)

**Independent Test**: Report generator can process mock room/reflecton data and produce valid final_report.md with all sections populated.

## Context & Constraints

**Reference Documents**:
- [spec.md](spec.md) - Functional requirements FR-037 through FR-040 (report content)
- [plan.md](plan.md) - Section 1.5 "Error Handling Strategy" for failure reporting
- [data-model.md](data-model.md) - CommitteeRun, DebateRoom, TPMReflection entities
- [contracts/room_result_schema.json](contracts/room_result_schema.json) - Room result structure
- [contracts/reflection_schema.json](contracts/reflection_schema.json) - Reflection result structure
- [contracts/metadata_schema.json](contracts/metadata_schema.json) - Metadata structure

**Architectural Decisions**:
- **Markdown generation**: Use Python markdown library or f-string templates
- **Report structure**: Fixed sections per spec (Executive Summary, Room-by-Room Analysis, TPM Reflection, Recommendations, Missing Perspectives)
- **Slug generation**: Lowercase, hyphenated first 3-5 words from question
- **Graceful degradation**: Explicitly note which rooms failed/skipped with reasons

**Constraints**:
- Must process all inputs from previous WPs (room results, reflection, metadata)
- Must handle edge case of zero successful rooms
- Report must be readable and actionable (not generic)

## Subtasks & Detailed Guidance

### Subtask T025 – Implement markdown report structure

**Purpose**: Create report template with all required sections per spec and quickstart guide.

**Steps**:
1. Define report sections in order:
   - Title: "Product Committee Report - {question}"
   - Executive Summary (brief overview)
   - Room-by-Room Analysis (one section per room)
   - TPM Reflection (synthesized insights)
   - Recommendations (actionable items)
   - Missing Perspectives (if any rooms failed)
   - Metadata (run info, timestamps)
2. Create template function `generate_report_template()` using f-strings
3. Add placeholder subsections for each room (TPM vs CPO/CFO/CTO/BDM)
4. Include metadata footer with generation timestamp

**Files**:
- `product_committee.py` (add report generation functions, ~150 lines)
- Create separate report module? No - keep in main file for MVP

**Validation**:
- [ ] All required sections defined
- [ ] Template function produces valid markdown
- [ ] Sections match spec requirements (FR-037 through FR-040)
- [ ] Room subsections are placeholder for data injection
- [ ] Markdown syntax is valid

**Notes**:
- Use f-strings for multi-line templates
- Consider external markdown library if template complexity grows
- Template must be flexible for variable numbers of rooms (3-4 successful)

---

### Subtask T026 – Format room summaries for report

**Purpose**: Transform DebateRoom results into formatted markdown sections with positions, verdict, and takeaways.

**Steps**:
1. Create `format_room_summary(room_result)` function
2. Extract and format key fields:
   - Room ID as header (e.g., "### TPM vs CPO")
   - TPM position: paragraph or bullet list
   - Opponent position: paragraph or bullet list
   - Judge verdict: bold winner + explanation
   - Takeaways: numbered list (3-5 items)
3. Handle special cases:
   - Status="success": Show all content
   - Status="failed": Show error message, no details
   - Status="skipped_missing_prompt": Show skip reason
4. Return formatted markdown string

**Files**:
- `product_committee.py` (add formatting function, ~120 lines)

**Validation**:
- [ ] Successful rooms show full details (positions, verdict, takeaways)
- [ ] Failed rooms show error message only
- [ ] Skipped rooms show skip reason clearly
- [ ] Markdown formatting is clean and readable
- [ ] Takeaways are numbered 3-5 list

**Parallel?**: No (function is pure data transformation)

**Notes**:
- Room summaries are core of report - invest in quality
- Consistent formatting across all rooms important for readability
- Consider color coding or emoji for visual separation (optional)

---

### Subtask T027 – Format reflection content for report

**Purpose**: Transform TPMReflection result into formatted markdown section with learned insights, recommendations, and decisions.

**Steps**:
1. Create `format_reflection(reflection_result)` function
2. Extract and format key sections:
   - **Learned Insights**: By role (what TPM learned from CPO, CFO, CTO, BDM)
   - **Potential Assessment**: Overall + confidence + reasoning
   - **Recommendations**: Numbered list with priorities (high/medium/low)
   - **Argument Decisions**: Table or list showing which arguments accepted/rejected
   - **Missing Perspectives**: Note which roles are missing
3. Handle empty/zero-rooms case:
   - Add explicit note: "No rooms succeeded. Reflection based solely on PRD analysis."
4. Format recommendations as actionable items with category tags

**Files**:
- `product_committee.py` (add formatting function, ~150 lines)

**Validation**:
- [ ] Learned insights shown by role (if rooms succeeded)
- [ ] Potential assessment includes overall + confidence
- [ ] Recommendations are numbered with priorities
- [ ] Argument decisions clearly formatted (accepted/rejected)
- [ ] Missing perspectives section appears when needed
- [ ] Zero-rooms case handled explicitly
- [ ] Markdown formatting is clean

**Parallel?**: No (function is pure data transformation)

**Notes**:
- Reflection content is where value is synthesized - clarity critical
- Recommendations should be copy-pasteable for PRD author
- Categories help organize recommendations (strategy, product, technical, financial, GTM)

---

### Subtask T028 – Generate and write final_report.md

**Purpose**: Create final markdown report file by combining template, formatted sections, and metadata.

**Steps**:
1. Create `generate_final_report(metadata, room_results, reflection_result)` function
2. Build report content by sections:
   - Call template function for structure
   - Inject formatted room summaries (T026)
   - Inject formatted reflection (T027)
   - Add executive summary (2-3 sentences)
   - Add metadata footer
3. Generate output filename: `<output_dir>/RUN_<timestamp>_<slug>/final_report.md`
4. Write file with proper encoding (UTF-8)
5. Return absolute path for user confirmation

**Files**:
- `product_committee.py` (add report writer, ~100 lines)

**Validation**:
- [ ] final_report.md created in correct location
- [ ] Filename matches spec (final_report.md)
- [ ] All required sections populated
- [ ] UTF-8 encoding used
- [ ] Absolute path returned correctly
- [ ] Existing file not overwritten without warning

**Parallel?**: No (single file write operation)

**Notes**:
- This is the primary user-facing output - quality matters
- Report should be readable in plain text editors (VS Code, etc.)
- Consider adding "Generated by Product Committee Orchestrator" footer

---

### Subtask T029 – Implement slug generation from question

**Purpose**: Generate URL-friendly slug from question text for output directory naming (e.g., "what is potential" → "what-is-potential").

**Steps**:
1. Create `generate_slug(question)` function
2. Process question text:
   - Lowercase all characters
   - Remove/split on non-alphanumeric characters (except spaces, hyphens)
   - Split on whitespace to words
   - Take first 3-5 words
   - Join with hyphens
3. Handle edge cases:
   - Question < 3 words: use all words
   - Question with special chars: clean before processing
   - Empty or whitespace-only: return "committee-report"
4. Return generated slug

**Files**:
- `product_committee.py` (add slug generation, ~60 lines)

**Validation**:
- [ ] Slugs are 3-20 characters (reasonable length)
- [ ] Slugs contain only lowercase, hyphens, numbers
- [ ] Special characters stripped correctly
- [ ] Short questions (< 3 words) use all available words
- [ ] Empty/invalid questions produce "committee-report" fallback
- [ ] Slugs are consistent for same question input

**Parallel?**: No (pure function)

**Notes**:
- Slug quality affects directory readability
- Consider word list for common words to skip (the, a, an, is, etc.)
- Hyphenation style should match URL conventions

---

### Subtask T030 – Create output directory with error handling

**Purpose**: Implement output directory creation with proper error handling per spec (fatal error if not writable).

**Steps**:
1. In `generate_final_report()`, call `create_output_directory(output_dir)` before writing
2. Implement directory creation logic:
   - Check if directory exists using `os.path.exists()`
   - If not, create using `os.makedirs(output_dir, exist_ok=True)`
   - Verify writability using `os.access()`
   - If not writable: raise SystemExit with clear error message
3. Log directory creation in verbose mode:
   - Normal: "Creating output directory: {path}"
   - Verbose: "Created output directory: {path}"
4. Return absolute path for validation

**Files**:
- `product_committee.py` (add directory creation, ~50 lines)

**Validation**:
- [ ] Directory created if not exists
- [ ] Writability verified before use
- [ ] Fatal error raised if not writable (exit code 1)
- [ ] Error message is clear and actionable
- [ ] Absolute path returned
- [ ] Verbose logging works correctly

**Parallel?**: No (single filesystem operation)

**Notes**:
- This must happen before any room execution (validates environment early)
- Error is fatal per spec FR-033: "Output directory not writable → Error before any rooms run"
- Consider adding `--create-output-dir` flag for future (skip existence check)

---

## Test Strategy

Not applicable for this WP (tested in WP06).

## Risks & Mitigations

**Risk**: Report formatting may be complex and error-prone with manual string concatenation.
- **Mitigation**: Use f-string templates or markdown library; add tests for various room counts (0-4 successful).

**Risk**: Slug generation may produce duplicates for similar questions.
- **Mitigation**: Consider adding timestamp component to ensure uniqueness regardless of slug.

**Risk**: Large PRDs may create very long reports affecting readability.
- **Mitigation**: This is expected; reports are comprehensive by design. Consider adding `--executive-summary-only` flag for future.

## Review Guidance

**Acceptance Criteria**:
- [ ] final_report.md generated in correct location with proper structure
- [ ] All required sections present (Executive Summary, Room Analysis, Reflection, Recommendations)
- [ ] Room summaries include positions, verdict, takeaways
- [ ] Reflection includes learned insights, recommendations, argument decisions
- [ ] Missing perspectives section appears when applicable
- [ ] Slug generation produces valid directory names
- [ ] Output directory creation fails appropriately if not writable

**Key Checkpoints**:
- [ ] Report structure matches spec requirements FR-037 through FR-040
- [ ] Graceful degradation visible in report (failed rooms noted)
- [ ] Markdown is valid and readable in common editors
- [ ] Report is standalone (no missing sections or broken links)
- [ ] Executive summary provides concise overview
- [ ] Recommendations are actionable and concrete

**Context for Reviewers**:
- This WP produces primary user-facing output
- Report quality directly impacts user satisfaction
- Test with 0, 1, 2, 3, and 4 successful rooms to verify formatting
- Verify failed room handling produces clear messages

## Activity Log

- 2026-02-14T08:38:49Z – unknown – lane=doing – Starting implementation
