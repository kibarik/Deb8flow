---
work_package_id: "WP04"
subtasks:
  - "T017"
  - "T018"
  - "T019"
  - "T020"
  - "T021"
title: "DOCX Format Converter"
phase: "Phase 2 - Implementation"
lane: "planned"
assignee: ""
agent: ""
shell_pid: ""
review_status: ""
reviewed_by: ""
history:
  - timestamp: "2026-02-17T21:00:00Z"
    lane: "planned"
    agent: "system"
    shell_pid: ""
    action: "Prompt created via /spec-kitty.tasks"
dependencies: ["WP03"]
---

# Work Package Prompt: WP04 – DOCX Format Converter

## Objectives & Success Criteria

- **Goal**: Implement .docx ↔ markdown conversion using mammoth (read) and python-docx (write).
- **Success Criteria**:
  - Can convert .docx files to markdown using mammoth
  - Can convert markdown to .docx using python-docx with formatting preservation
  - Extracts metadata (author, title, properties) from .docx files
  - Handles formatting warnings for complex structures (tables, images)
  - Unit tests verify roundtrip conversion

## Context & Constraints

- **Prerequisites**: WP03 (converter base interface)
- **Supporting Documents**:
  - `kitty-specs/015-document-rewrite-agent/data-model.md` - ConversionResult structure
  - `kitty-specs/015-document-rewrite-agent/contracts/converter_interface.json` - DOCX converter capabilities
  - `kitty-specs/015-document-rewrite-agent/research.md` - Mammoth + python-docx strategy
- **Constraints**:
  - Use mammoth for .docx → markdown (read direction)
  - Use python-docx for markdown → .docx (write direction)
  - Preserve basic formatting: headers, bold, italics, lists
  - Handle complex formatting as best-effort (tables, images may not preserve)

## Subtasks & Detailed Guidance

### Subtask T017 – Create DOCX to markdown conversion

**Purpose**: Implement .docx → markdown conversion using mammoth library.

**Steps**:
1. Create `src/converters/docx_converter.py` (new file)
2. Import `FormatConverter` from `src.converters.converter_base`
3. Import `mammoth` (new dependency)
4. Import types: `ConversionResult`, `DocumentFormat`, `FileMetadata`
5. Create `DocxConverter` class inheriting from `FormatConverter`:
6. Implement `to_markdown(source_path: str) -> ConversionResult`:
   - Validate file has `.docx` extension
   - Use `mammoth.convert_to_markdown(path=source_path)` to convert
   - Extract text using `extract_raw_text=True` option
   - Store markdown content in `ConversionResult.markdown_content`
   - Track formatting warnings in `ConversionResult.formatting_warnings`
   - Return success or error result based on conversion

**Files**:
- `src/converters/docx_converter.py` (new, ~150 lines total with other subtasks)

**Validation**:
- [ ] .docx file converted to markdown
- [ ] Markdown content contains text from .docx
- [ ] Formatting warnings tracked (if any)
- [ ] Error handling for invalid files

**Notes**:
- Mammoth handles .docx structure reasonably well
- Some formatting may be lost (tables, complex layouts) - document in warnings
- Use `mammoth.convert_to_markdown(extract_raw_text=True)` for better text extraction

---

### Subtask T018 – Create markdown to DOCX conversion

**Purpose**: Implement markdown → .docx conversion using python-docx.

**Steps**:
1. In `src/converters/docx_converter.py`, implement `from_markdown(markdown: str, output_path: str, metadata: Optional[dict] = None) -> ConversionResult`:
   - Create `Document()` from `python-docx`
   - Parse markdown into lines/structure
   - For each line:
     - Headers (# ## ###) → `add_heading(level, text)`
     - Bold (**text**) → `add_run().bold = True`
     - Italic (*text*) → `add_run().italic = True`
     - Lists (- or *) → `add_paragraph(style='List Bullet')`
     - Regular text → `add_paragraph()`
   - Save document using `doc.save(output_path)`
   - If metadata provided, set core_properties (author, title)
   - Return `ConversionResult(success=True, output_path=output_path, bytes_written=...)`

**Files**:
- `src/converters/docx_converter.py` (append to existing file from T017)

**Validation**:
- [ ] Markdown converted to valid .docx file
- [ ] File can be opened in Microsoft Word/LibreOffice
- [ ] Basic formatting preserved (headers, bold, italics, lists)
- [ ] Output file path returned correctly

**Notes**:
- This is a simplified implementation - not all markdown features supported
- Tables, code blocks, links may not preserve correctly
- Consider adding formatting warning for unsupported features

---

### Subtask T019 – Implement markdown-to-docx formatting

**Purpose**: Add proper markdown parsing and formatting preservation for common elements.

**Steps**:
1. In `src/converters/docx_converter.py`, create `_parse_markdown_line(line: str) -> dict` helper:
   - Detect header: `^#{1,6}\s+(.+)$` → `{'type': 'heading', 'level': n, 'text': text}`
   - Detect bold: `\*\*(.+?)\*\*` → `{'type': 'bold', 'text': text}`
   - Detect italic: `(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)` → `{'type': 'italic', 'text': text}`
   - Detect list: `^\s*[-*+]\s+(.+)$` → `{'type': 'list', 'text': text}`
   - Default: `{'type': 'paragraph', 'text': line}`
2. Update `from_markdown()` to use parser:
   - For each parsed element, apply appropriate python-docx formatting
   - Handle nested formatting (bold+italic): `\*\*\*text\*\*\*`
   - Track unsupported features in formatting_warnings
3. Add `_apply_inline_formatting(run, text)` helper:
   - Parse markdown inline syntax (bold, italic, code)
   - Apply multiple runs to document for mixed formatting

**Files**:
- `src/converters/docx_converter.py` (append to existing file from T017)

**Validation**:
- [ ] Headers converted to Word headings
- [ ] Bold text appears bold in .docx
- [ ] Italic text appears italic in .docx
- [ ] Lists converted to Word bullets
- [ ] Mixed formatting handled (bold+italic)

**Notes**:
- Regex for italic must avoid matching bold: use negative lookbehind/lookahead
- Code blocks (```) not supported in MVP - add warning
- Links `[text](url)` not supported - add warning

---

### Subtask T020 – Extract DOCX metadata

**Purpose**: Extract document metadata (author, title, properties) from .docx files.

**Steps**:
1. In `src/converters/docx_converter.py`, create `_extract_docx_metadata(doc_path: str) -> FileMetadata` helper:
   - Use `python-docx.Document(doc_path)` to open file
   - Access `doc.core_properties` for metadata:
     - `author` → `core_properties.author`
     - `title` → `core_properties.title`
     - `created` → `core_properties.created`
     - `modified` → `core_properties.modified`
     - `last_modified_by` → `core_properties.last_modified_by`
   - Combine with file stats for `FileMetadata` object
   - Return populated `FileMetadata`
2. Update `to_markdown()` to call `_extract_docx_metadata()` and include in `ConversionResult.metadata_preserved`

**Files**:
- `src/converters/docx_converter.py` (append to existing file from T017)

**Validation**:
- [ ] Author extracted from .docx if present
- [ ] Title extracted from .docx if present
- - [ ] Created/modified timestamps extracted
- - [ ] Returns None for missing metadata fields

**Notes**:
- Not all .docx files have all metadata fields
- Use `getattr()` with defaults for missing fields
- Timestamps from `core_properties` are datetime objects, convert to ISO 8601 strings

---

### Subtask T021 – DOCX converter unit tests

**Purpose**: Test .docx conversion functionality for correctness and edge cases.

**Steps**:
1. Create `tests/converters/test_docx_converter.py` (new file)
2. Create test fixtures: sample .docx file with headers, bold, italics, lists
3. Test `to_markdown()`:
   - `test_to_markdown_converts()` - Basic conversion
   - `test_to_markdown_extracts_metadata()` - Author/title extracted
   - `test_to_markdown_formatting_warnings()` - Complex structures tracked
4. Test `from_markdown()`:
   - `test_from_markdown_creates_docx()` - .docx file created
   - `test_from_markdown_preserves_headers()` - Heading levels correct
   - `test_from_markdown_preserves_bold_italic()` - Formatting applied
   - `test_from_markdown_preserves_lists()` - Lists converted
5. Test roundtrip:
   - `test_roundtrip_preserves_content()` - .docx → md → .docx content preserved
   - `test_roundtrip_formatting_loss()` - Document limitations
6. Test `capabilities()`:
   - `test_capabilities_docx()` - Values match contract

**Files**:
- `tests/converters/test_docx_converter.py` (new, ~150 lines)

**Commands**:
```bash
pytest tests/converters/test_docx_converter.py -v
```

**Fixtures**:
- Use `python-docx` to create test .docx files programmatically
- Or embed minimal .docx fixture in test data directory

---

## Test Strategy

DOCX converter tests should verify:
- Successful conversion in both directions
- Metadata extraction and preservation
- Formatting preservation for supported elements
- Warnings for unsupported features
- Roundtrip conversion quality

---

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Complex .docx formatting may not preserve | Add to formatting_warnings, document limitations |
| Large .docx files may timeout | Add size check, warn user for files >5MB |
| Mammoth or python-docx installation fails | Document in README, verify in requirements.txt |
| Roundtrip loses significant formatting | Accept as known limitation, document in user guide |

---

## Review Guidance

**Key acceptance checkpoints**:
- [ ] .docx → markdown conversion works using mammoth
- [ ] Markdown → .docx conversion works using python-docx
- [ ] Metadata (author, title) extracted and can be preserved
- [ ] Formatting warnings tracked for unsupported features
- [ ] Unit tests pass including roundtrip test
- [ ] `capabilities()` returns correct values per contract

**Context for reviewers**:
- Verify that mammoth is used for read direction only (not write)
- Check that markdown parsing handles common formatting correctly
- Confirm metadata extraction uses `python-docx` core_properties
- Ensure error messages are actionable for unsupported .docx features

---

## Activity Log

- 2026-02-17T21:00:00Z – system – lane=planned – Prompt created.
