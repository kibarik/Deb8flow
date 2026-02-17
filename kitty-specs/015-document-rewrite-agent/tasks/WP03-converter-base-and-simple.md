---
work_package_id: "WP03"
subtasks:
  - "T012"
  - "T013"
  - "T014"
  - "T015"
  - "T016"
title: "Format Converter Base Interface"
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
dependencies: ["WP01"]
---

# Work Package Prompt: WP03 – Format Converter Base Interface

## Objectives & Success Criteria

- **Goal**: Define the converter interface and implement simple converters (markdown, txt) that don't require external libraries.
- **Success Criteria**:
  - `FormatConverter` abstract base class defined with clear interface
  - Markdown converter handles passthrough (no conversion needed)
  - Text converter handles UTF-8 encoding/decoding
  - All converters return `ConversionResult` with appropriate fields
  - Unit tests verify correct behavior

## Context & Constraints

- **Prerequisites**: WP01 (types must be defined)
- **Supporting Documents**:
  - `kitty-specs/015-document-rewrite-agent/data-model.md` - ConversionResult structure
  - `kitty-specs/015-document-rewrite-agent/contracts/converter_interface.json` - Converter capabilities registry
  - `kitty-specs/015-document-rewrite-agent/research.md` - Markdown intermediate format strategy
- **Constraints**:
  - Must implement interface defined in contracts
  - Markdown is the lingua franca (intermediate format)
  - Handle UTF-8 encoding issues gracefully
  - Follow existing codebase patterns

## Subtasks & Detailed Guidance

### Subtask T012 – Create converter base interface

**Purpose**: Define the abstract interface that all format converters must implement.

**Steps**:
1. Create `src/converters/converter_base.py` (new file)
2. Import `ABC`, `abstractmethod` from `abc`
3. Import types: `ConversionResult` from `src.types.conversion_types`, `DocumentFormat` from `src.types.rewrite_types`
4. Create `ConverterCapabilities` dataclass:
   - `format: str` - Format identifier
   - `supports_bidirectional: bool` - Both to/from markdown
   - `supports_metadata_preservation: bool` - Can preserve metadata
   - `preserves_formatting: bool` - Formatting preserved
5. Create `FormatConverter` abstract base class:
   - Abstract method: `to_markdown(source_path: str) -> ConversionResult`
   - Abstract method: `from_markdown(markdown: str, output_path: str, metadata: Optional[dict] = None) -> ConversionResult`
   - Method: `capabilities() -> ConverterCapabilities` (override in subclasses)
6. Add docstrings explaining the interface and usage

**Files**:
- `src/converters/converter_base.py` (new, ~80 lines)

**Validation**:
- [ ] ABC properly defined with abstract methods
- [ ] Cannot instantiate `FormatConverter` directly (raises TypeError)
- [ ] `ConverterCapabilities` dataclass has all required fields

**Notes**:
- Use `@abstractmethod` decorator for methods that must be implemented
- The `capabilities()` method should return static capabilities (no runtime checks)
- Consider adding `supports_format(format: DocumentFormat) -> bool` helper

---

### Subtask T013 – Create markdown converter

**Purpose**: Implement converter for markdown files (essentially passthrough since markdown is the intermediate format).

**Steps**:
1. Create `src/converters/markdown_converter.py` (new file)
2. Import `FormatConverter` from `src.converters.converter_base`
3. Import types: `ConversionResult`, `DocumentFormat`
4. Create `MarkdownConverter` class inheriting from `FormatConverter`:
   - Implement `to_markdown(source_path: str) -> ConversionResult`:
     - Read file with UTF-8 encoding
     - Return `ConversionResult(success=True, markdown_content=content)`
   - Implement `from_markdown(markdown: str, output_path: str, metadata: Optional[dict] = None) -> ConversionResult`:
     - Write markdown content to output_path with UTF-8 encoding
     - Return `ConversionResult(success=True, output_path=output_path, bytes_written=len(content.encode()))`
   - Implement `capabilities()` returning ConverterCapabilities for markdown:
     - `format="md"`, `supports_bidirectional=True`, `preserves_formatting=True`
5. Add error handling for file not found, encoding errors

**Files**:
- `src/converters/markdown_converter.py` (new, ~80 lines)

**Validation**:
- [ ] Can read markdown file and return content unchanged
- [ ] Can write markdown content to new file
- [ ] Returns correct `ConverterCapabilities`
- [ ] Handles encoding errors gracefully

**Notes**:
- Markdown is the native format, so "conversion" is essentially file I/O
- No formatting loss since markdown stays markdown
- Metadata parameter accepted but not used (markdown files don't support embedded metadata)

---

### Subtask T014 – Create text converter

**Purpose**: Implement converter for plain text files with UTF-8 encoding handling.

**Steps**:
1. Create `src/converters/txt_converter.py` (new file)
2. Import `FormatConverter` from `src.converters.converter_base`
3. Import types: `ConversionResult`, `DocumentFormat`
4. Create `TextConverter` class inheriting from `FormatConverter`:
   - Implement `to_markdown(source_path: str) -> ConversionResult`:
     - Try multiple encodings: utf-8, cp1251, iso-8859-1, windows-1252
     - Return `ConversionResult(success=True, markdown_content=content)`
     - On failure, return `ConversionResult(success=False, error_message="...")`
   - Implement `from_markdown(markdown: str, output_path: str, metadata: Optional[dict] = None) -> ConversionResult`:
     - Write markdown content to output_path as plain text (UTF-8)
     - Return `ConversionResult(success=True, output_path=output_path)`
   - Implement `capabilities()` returning ConverterCapabilities for text:
     - `format="txt"`, `supports_bidirectional=True`, `preserves_formatting=False`
5. Add helper method: `_try_encodings(file_path: str) -> tuple[bool, str, str]` returning (success, content, encoding_used)

**Files**:
- `src/converters/txt_converter.py` (new, ~100 lines)

**Validation**:
- [ ] Can read text files with UTF-8 encoding
- [ ] Falls back to alternative encodings if UTF-8 fails
- [ ] Can write text content to new file
- [ ] Returns correct `ConverterCapabilities`

**Notes**:
- Text files don't have formatting, so `preserves_formatting=False`
- The fallback encoding chain handles common Cyrillic and Western European encodings
- Consider logging which encoding was used (helpful for debugging)

---

### Subtask T015 – Markdown converter tests

**Purpose**: Test markdown converter for correct passthrough behavior.

**Steps**:
1. Create `tests/converters/test_markdown_converter.py` (new file)
2. Create test fixture: sample markdown file with headers, bold, italics, lists
3. Test `to_markdown()`:
   - `test_to_markdown_passthrough()` - Content unchanged
   - `test_to_markdown_preserves_formatting()` - Markdown syntax intact
   - `test_to_markdown_file_not_found()` - Error handling
4. Test `from_markdown()`:
   - `test_from_markdown_writes_file()` - File created
   - `test_from_markdown_preserves_content()` - Content unchanged
   - `test_from_markdown_creates_directories()` - Path creation
5. Test `capabilities()`:
   - `test_capabilities_returns_correct_values()` - All fields correct

**Files**:
- `tests/converters/test_markdown_converter.py` (new, ~80 lines)

**Commands**:
```bash
pytest tests/converters/test_markdown_converter.py -v
```

**Fixtures**:
```python
@pytest.fixture
def sample_markdown_file(tmp_path):
    content = "# Header\n\nBold **text** and italic *text*\n"
    file_path = tmp_path / "sample.md"
    file_path.write_text(content, encoding="utf-8")
    return file_path
```

---

### Subtask T016 – Text converter tests

**Purpose**: Test text converter encoding handling and file operations.

**Steps**:
1. Create `tests/converters/test_txt_converter.py` (new file)
2. Create test fixtures: UTF-8 file, CP1251 file (Cyrillic), ISO-8859-1 file
3. Test `to_markdown()`:
   - `test_to_markdown_utf8()` - UTF-8 encoding works
   - `test_to_markdown_fallback_encoding()` - CP1251 fallback works
   - `test_to_markdown_all_encodings_fail()` - Returns error result
   - `test_to_markdown_empty_file()` - Empty file handled
4. Test `from_markdown()`:
   - `test_from_markdown_writes_utf8()` - UTF-8 output
   - `test_from_markdown_creates_directories()` - Path creation
5. Test `capabilities()`:
   - `test_capabilities_formatting_not_preserved()` - Formatting is False

**Files**:
- `tests/converters/test_txt_converter.py` (new, ~100 lines)

**Commands**:
```bash
pytest tests/converters/test_txt_converter.py -v
```

**Notes**:
- Use `tmp_path` fixture for temporary files
- Test with actual Cyrillic content for CP1251 fallback verification

---

## Test Strategy

All converters should have:
- Unit tests for both `to_markdown()` and `from_markdown()` methods
- Tests for error conditions (file not found, encoding errors)
- Tests for `capabilities()` return values
- Cross-platform encoding tests (different text files)

---

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Encoding issues break text conversion | Multiple encoding fallbacks, clear error messages |
| Empty files cause issues | Handle gracefully, return empty content |
| Path separator issues on different OS | Use pathlib for cross-platform compatibility |
| Markdown converter has edge cases | Document that it's essentially passthrough, keep simple |

---

## Review Guidance

**Key acceptance checkpoints**:
- [ ] `FormatConverter` ABC properly defined with abstract methods
- [ ] `MarkdownConverter` implements passthrough behavior correctly
- [ ] `TextConverter` handles UTF-8 and fallback encodings
- [ ] All converters return `ConversionResult` with appropriate fields
- [ ] Unit tests pass for both converters
- [ ] `capabilities()` returns correct values per `converter_interface.json`

**Context for reviewers**:
- Verify that converter interface matches the contract specification
- Check that text converter encoding fallback chain covers common cases
- Confirm that markdown converter truly is passthrough (no unwanted transformations)
- Ensure error messages are helpful for debugging

---

## Activity Log

- 2026-02-17T21:00:00Z – system – lane=planned – Prompt created.
