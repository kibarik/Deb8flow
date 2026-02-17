# Feature Specification: Document Rewrite Agent

**Feature Branch**: `015-document-rewrite-agent`
**Created**: 2026-02-17
**Status**: Draft
**Input**: User description: "я хочу результатом дебатов получать доработанный документ. ASIS я получаю conclusion.md ПРОБЛЕМА: мне нужно далее самому отсматривать первоначальный документ и тратить часы на доработку файлов TOBE: появляется отдельная роль 'rewriter', которая на основании conclusion.md и первоначального документа создает новый документ с учетом всех правок и замечаний. Я как пользователь в папке с conclusion.md вижу еще один файл с доработками. РЕШЕНИЕ: технически я хочу чтобы это управлялось флагом "--make-review", если этот флаг добавлен, то в обязательном порядке в папку {run-id} сохраняется исходных файл (условный old_input.md, prd.docx). После окончания генерации conclusion.md запускается отдельный AI-агент, который читает исходный файл, читает conclusion.md и создает новый файл на основе старого с правками из conclusion.md. Затем сохраняет его рядом с пометкой {old_name}_datetime.{old_extension}"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - CLI Flag for Document Rewrite (Priority: P1)

As a user, I want to run the committee debate with a `--make-review` flag so that the original document is automatically updated based on the debate conclusions without manual editing.

**Why this priority**: This is the core feature - without the flag, the entire functionality cannot be triggered. It provides the primary user value.

**Independent Test**: Can be fully tested by running `python product_committee.py --prd <path> --question <text> --make-review` and verifying that:
1. The original file is copied to the run-id directory
2. After conclusion.md is created, a rewritten document is created
3. The rewritten document has the correct naming format with timestamp

**Acceptance Scenarios**:

1. **Given** a PRD document at `/path/to/prd.docx`, **When** I run `python product_committee.py --prd /path/to/prd.docx --question "What's the potential?" --make-review`, **Then** the system creates a `{run-id}/prd.docx` copy and `{run-id}/prd_YYYYMMDD_HHMMSS.docx` rewritten document
2. **Given** the `--make-review` flag is set, **When** the debate completes, **Then** the rewriter agent automatically processes the document without requiring user confirmation
3. **Given** a successful debate run, **When** I check the output directory, **Then** I see three files: `conclusion.md`, original file copy, and the rewritten document

---

### User Story 2 - Original Document Preservation (Priority: P1)

As a user, I want the original document to be preserved in the run-id directory so that I can compare the rewritten version with the original.

**Why this priority**: Without preserving the original, users cannot verify what changes were made or revert if needed. This is critical for transparency.

**Independent Test**: Can be fully tested by running with `--make-review` and verifying the original file exists in the output directory with identical content to the input file.

**Acceptance Scenarios**:

1. **Given** a PRD document with content "Original content", **When** I run with `--make-review`, **Then** the output directory contains a file with identical "Original content"
2. **Given** the original file is copied to output directory, **When** I compare file hashes, **Then** the input file and output copy have identical hashes
3. **Given** a .docx file with metadata (author, created date), **When** copied to output directory, **Then** the metadata is preserved in the copy

---

### User Story 3 - Rewriter Agent Processing (Priority: P1)

As a user, I want the rewriter agent to read both the original document and conclusion.md to create an updated document incorporating all recommendations.

**Why this priority**: This is the core AI processing logic - without it, no rewriting happens.

**Independent Test**: Can be tested by providing a document with known issues, running a debate that identifies those issues in conclusion.md, and verifying the rewritten document addresses them.

**Acceptance Scenarios**:

1. **Given** a conclusion.md with recommendations to "remove section 3" and "update terminology", **When** the rewriter agent runs, **Then** the output document has section 3 removed and terminology updated
2. **Given** conclusion.md contains no recommendations for a specific section, **When** the rewriter agent runs, **Then** that section remains unchanged in the output
3. **Given** contradictory recommendations in conclusion.md, **When** the rewriter agent runs, **Then** it resolves conflicts by choosing the most consistent option without asking the user
4. **Given** recommendations that cannot be applied unambiguously, **When** the rewriter agent runs, **Then** it adds inline comments like `<!-- REVIEW NOTE: ... -->` only when absolutely necessary

---

### User Story 4 - Multi-Format Support (Priority: P2)

As a user, I want the rewriter to support various text file formats (.docx, .md, .txt, .rtf) so that I can use it with different document types.

**Why this priority**: Important for flexibility but .docx and .md cover most use cases. Other formats are enhancements.

**Independent Test**: Can be tested by running debates with different input file formats and verifying each produces a correctly rewritten output.

**Acceptance Scenarios**:

1. **Given** a .md input file, **When** I run with `--make-review`, **Then** the output is a .md file with proper markdown formatting
2. **Given** a .txt input file, **When** I run with `--make-review`, **Then** the output is a .txt file with recommendations applied
3. **Given** an unsupported file format, **When** I run with `--make-review`, **Then** the system provides a clear error message listing supported formats

---

### User Story 5 - Error Handling and Resilience (Priority: P2)

As a user, I want the system to handle errors gracefully so that a single failure doesn't break the entire debate workflow.

**Why this priority**: Important for robustness but the core feature works without perfect error handling.

**Independent Test**: Can be tested by simulating various error conditions (corrupted files, missing files) and verifying appropriate behavior.

**Acceptance Scenarios**:

1. **Given** the original file is corrupted or unreadable, **When** the rewriter agent attempts to process it, **Then** the agent logs an error but doesn't crash the entire run
2. **Given** conclusion.md is missing or empty, **When** the rewriter agent runs, **Then** it creates a copy of the original with a note that no changes were made
3. **Given** the rewriter agent fails partway through processing, **When** an error occurs, **Then** the debate results (conclusion.md) are still preserved and available

---

### Edge Cases

- What happens when the original document file is deleted or moved during the debate?
- How does the system handle conclusion.md with malformed or unparseable recommendations?
- What happens when the rewritten document would exceed file size limits?
- How does the rewriter handle documents with mixed languages (e.g., Russian and English)?
- What happens when the document contains binary data or embedded images?
- How does the system handle very large documents (>100 pages)?
- What happens when the user provides the same input file path multiple times with `--make-review`?
- How does the rewriter preserve complex document structures (tables, images, formatting) in .docx files?
- What happens when the output directory already contains a file with the same timestamped name?
- How does the system handle documents with tracked changes or comments?

## Requirements *(mandatory)*

### Functional Requirements

#### CLI Integration

- **FR-001**: System MUST accept a `--make-review` flag on the document debate CLI
- **FR-002**: When `--make-review` is provided, the system MUST copy the original document to the `{run-id}` output directory before running the debate
- **FR-003**: The original document copy MUST use the same filename as the input (e.g., `prd.docx`)
- **FR-004**: When `--make-review` is NOT provided, the system MUST NOT invoke the rewriter agent
- **FR-005**: The system MUST validate that the input file exists before copying

#### Rewriter Agent Invocation

- **FR-006**: After conclusion.md is successfully generated, the system MUST automatically invoke the rewriter agent
- **FR-007**: The rewriter agent MUST receive as input: (1) the original document copy, (2) the conclusion.md file
- **FR-008**: The rewriter agent MUST process documents without requiring user interaction or confirmation
- **FR-009**: The rewriter agent MUST apply all recommendations from conclusion.md aggressively without asking clarifying questions
- **FR-010**: The rewriter agent MUST resolve contradictions in recommendations independently by choosing the most consistent option

#### Rewriter Behavior

- **FR-011**: The rewriter agent MUST preserve sections of the document that have no corresponding recommendations in conclusion.md
- **FR-012**: The rewriter agent MUST NOT remove important sections unless explicitly instructed in conclusion.md
- **FR-013**: The rewriter agent MUST preserve the document structure unless conclusion.md recommends a different structure
- **FR-014**: When unable to apply a recommendation unambiguously, the rewriter agent MAY add inline comments (e.g., `<!-- REVIEW NOTE: ... -->`) only as a last resort
- **FR-015**: The rewriter agent MUST avoid leaving "TODO" or placeholder text in the final output

#### Output File Generation

- **FR-016**: The rewritten document MUST be saved in the same `{run-id}` directory as conclusion.md
- **FR-017**: The rewritten filename MUST follow the format: `{original_name}_{YYYYMMDD_HHMMSS}.{extension}`
- **FR-018**: The timestamp MUST use UTC timezone
- **FR-019**: The rewritten document MUST use the same file extension as the original
- **FR-020**: The system MUST preserve file metadata (author, creation/modification dates) where supported by the file format

#### File Format Support

- **FR-021**: System MUST support .docx files for rewriting
- **FR-022**: System MUST support .md (markdown) files for rewriting
- **FR-023**: System MUST support .txt files for rewriting
- **FR-024**: System SHOULD support other text-based formats (.rtf, .odt)
- **FR-025**: System MUST provide a clear error message when an unsupported format is provided

#### Error Handling

- **FR-026**: If the original file cannot be read, the system MUST log the error and continue without crashing
- **FR-027**: If conclusion.md is missing or empty, the rewriter MUST create a copy of the original with a note that no changes were applied
- **FR-028**: If the rewriter agent fails, the system MUST preserve the debate results (conclusion.md, metadata.json)
- **FR-029**: The system MUST report rewriter errors in the CLI output with sufficient detail for debugging
- **FR-030**: The system MUST NOT delete the original document copy even if rewriting fails

### Key Entities

- **Original Document**: The input file provided by the user (.docx, .md, .txt, etc.) containing the content to be debated and potentially rewritten
- **Document Copy**: A bit-for-bit copy of the original document saved to the `{run-id}` directory for reference and rewriting
- **Conclusion Report**: The markdown file (`conclusion.md`) generated by the debate containing recommendations, weaknesses, and improvement suggestions
- **Rewritten Document**: The output document generated by the rewriter agent that incorporates all recommendations from the conclusion report
- **Rewriter Agent**: The AI agent that reads the original document and conclusion report to generate an updated document
- **Run ID Directory**: The time-stamped output directory (e.g., `RUN_20260217_123456_question`) containing all artifacts from a single debate run
- **Recommendation**: A specific change suggestion from the conclusion report (e.g., "remove section 3", "update terminology")

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can obtain a rewritten document by adding a single CLI flag without any manual editing
- **SC-002**: The rewriter agent applies at least 95% of recommendations from conclusion.md without user intervention
- **SC-003**: The rewritten document is generated within 60 seconds after the debate concludes
- **SC-004**: Document sections without recommendations remain unchanged 100% of the time
- **SC-005**: The system handles corrupted or unreadable files without crashing the main workflow
- **SC-006**: Users receive clear error messages for unsupported file formats 100% of the time
- **SC-007**: File metadata (author, dates) is preserved where the format allows 90% of the time
- **SC-008**: The rewriter agent resolves contradictory recommendations without asking the user in 100% of cases
- **SC-009**: The original document copy is bit-for-bit identical to the input file
- **SC-010**: The rewritten document filename follows the specified format with valid timestamps 100% of the time

## Assumptions

1. Users will have the original document available at the time of debate execution
2. The conclusion.md will contain actionable recommendations (not just general feedback)
3. The LLM used for the rewriter agent will have sufficient context window to process the document and conclusion together
4. Document formatting (bold, italics, tables) will be preserved on a "best effort" basis for .docx files
5. The rewriter agent will use the same LLM configuration as other debate participants unless specified otherwise
6. Inline comments will only be added when absolutely necessary (estimated <5% of rewrites)
7. The timestamp format will use UTC to avoid timezone ambiguity
8. Users will compare original and rewritten documents manually if needed (no diff tool is provided)
9. The rewriter agent will not verify that applied changes are semantically correct (e.g., it won't fact-check)
10. Large files (>10MB) may require special handling or timeouts
