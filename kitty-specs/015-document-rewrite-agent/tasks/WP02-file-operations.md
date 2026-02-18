---
work_package_id: WP02
title: File Operations & Metadata
lane: "doing"
dependencies: [WP01]
base_branch: 015-document-rewrite-agent-WP01
base_commit: 472fe15b4083bb46f18729bd679a1f1430e885a9
created_at: '2026-02-18T12:40:00.799384+00:00'
subtasks:
- T007
- T008
- T009
- T010
- T011
phase: Phase 1 - Foundation
assignee: ''
agent: "claude-opus-4-6"
shell_pid: "44565"
review_status: ''
reviewed_by: ''
history:
- timestamp: '2026-02-17T21:00:00Z'
  lane: planned
  agent: system
  shell_pid: ''
  action: Prompt created via /spec-kitty.tasks
---

# Work Package Prompt: WP02 – File Operations & Metadata

## Objectives & Success Criteria

- **Goal**: Implement file copying with metadata preservation, output filename generation, and metadata JSON storage.
- **Success Criteria**:
  - Can copy files to run-id directory with preserved metadata (author, dates)
  - Generate correctly formatted output filenames with UTC timestamps
  - Save and load metadata JSON files with all preserved information
  - Handle edge cases (missing files, permission errors) gracefully

## Context & Constraints

- **Prerequisites**: WP01 (types must be defined)
- **Supporting Documents**:
  - `kitty-specs/015-document-rewrite-agent/data-model.md` - FileMetadata structure
  - `kitty-specs/015-document-rewrite-agent/contracts/file_operation_contract.json` - File operation contracts
  - `kitty-specs/015-document-rewrite-agent/research.md` - Metadata preservation strategy
- **Constraints**:
  - Must preserve metadata bit-for-bit in original copy
  - Use UTC timezone for all timestamps
  - Cross-platform file operations (Linux, macOS, Windows)
  - Follow existing patterns from `src/utils/conclusion_writer.py`

## Subtasks & Detailed Guidance

### Subtask T007 – Copy document with metadata

**Purpose**: Copy the original document to the run-id directory while preserving all file metadata.

**Steps**:
1. Create `src/utils/file_utils.py` (new file)
2. Import `shutil`, `os`, `pathlib`, `datetime`, `timezone`
3. Import types: `FileMetadata` from `src.types.conversion_types`
4. Implement `copy_document_with_metadata(source_path: str, destination_directory: str) -> tuple[str, FileMetadata]`:
   - Validate source file exists (raise FileNotFoundError if not)
   - Create destination directory if it doesn't exist using `Path.mkdir(parents=True, exist_ok=True)`
   - Get original filename using `Path(source_path).name`
   - Copy using `shutil.copy2()` to preserve metadata
   - Extract metadata using `os.stat()` and platform-specific calls
   - Return tuple of (copied_file_path, FileMetadata object)

**Files**:
- `src/utils/file_utils.py` (new, ~120 lines)

**Validation**:
- [ ] File copied with identical content (hash comparison)
- [ ] Metadata preserved (created/modified times, author where available)
- [ ] Returns correct FileMetadata object

**Notes**:
- Use `shutil.copy2()` instead of `shutil.copy()` for metadata preservation
- For .docx files, additional metadata can be extracted using `python-docx` core_properties
- Handle permission errors gracefully (log and return error)

---

### Subtask T008 – Extract file metadata

**Purpose**: Extract comprehensive metadata from source files for preservation.

**Steps**:
1. In `src/utils/file_utils.py`, implement `extract_file_metadata(file_path: str) -> FileMetadata`:
   - Get file stats using `os.stat()`: st_size, st_ctime, st_mtime
   - Convert timestamps to ISO 8601 format using `datetime.fromtimestamp().astimezone(timezone.utc).isoformat()`
   - Extract filename and extension using `Path(file_path).stem` and `Path(file_path).suffix`
   - For .docx files: extract author, title, properties using `python-docx.Document().core_properties`
   - Set `copied_at` to current UTC time
   - Return populated `FileMetadata` object

**Files**:
- `src/utils/file_utils.py` (append to existing file from T007)

**Validation**:
- [ ] All FileMetadata fields populated correctly
- [ ] Timestamps in ISO 8601 format with UTC timezone
- [ ] .docx metadata extraction works (author, title, etc.)

**Notes**:
- Different OS platforms preserve different metadata - document limitations
- For .txt/.md files, author may not be available (set to None)
- Handle Unicode errors in metadata gracefully

---

### Subtask T009 – Generate output filename

**Purpose**: Generate timestamped output filenames following the naming convention.

**Steps**:
1. In `src/utils/file_utils.py`, implement `generate_output_filename(original_filename: str, timestamp: Optional[datetime] = None) -> str`:
   - Extract name and extension: `Path(original_filename).stem` and `Path(original_filename).suffix`
   - Use provided timestamp or generate current UTC time: `datetime.now(timezone.utc)`
   - Format timestamp as `YYYYMMDD_HHMMSS`: `dt.strftime("%Y%m%d_%H%M%S")`
   - Return formatted string: `{name}_{timestamp}{ext}` (note: extension includes dot)

**Files**:
- `src/utils/file_utils.py` (append to existing file from T007)

**Validation**:
- [ ] Output format matches `{name}_{YYYYMMDD_HHMMSS}.{ext}` pattern
- [ ] Timestamp uses UTC timezone
- [ ] Handles filenames with multiple dots correctly (only last dot is extension)

**Examples**:
- `prd.docx` → `prd_20260217_123456.docx`
- `document.v2.md` → `document.v2_20260217_123456.md`

**Notes**:
- Use `Path.suffix` which gets the last dot-separated extension
- The timestamp should be when the rewrite completes, not when it starts

---

### Subtask T010 – Save metadata JSON

**Purpose**: Save preserved metadata and rewrite statistics to a JSON file for audit trail.

**Steps**:
1. In `src/utils/file_utils.py`, implement `save_metadata_json(metadata: dict, output_directory: str, filename: str = "file_metadata.json") -> str`:
   - Validate output directory exists
   - Create output file path: `Path(output_directory) / filename`
   - Write metadata to JSON with `json.dump(metadata, f, indent=2, ensure_ascii=False)`
   - Use UTF-8 encoding
   - Return absolute path to saved file

**Files**:
- `src/utils/file_utils.py` (append to existing file from T007)

**Metadata structure** (per contract):
```json
{
  "original_file": "path/to/original.docx",
  "copied_file": "original.docx",
  "rewritten_file": "original_20260217_123456.docx",
  "preserved_metadata": {
    "author": "...",
    "created": "...",
    "modified": "..."
  },
  "rewrite_metadata": {
    "started_at": "...",
    "completed_at": "...",
    "duration_seconds": 45.2,
    "llm_model": "gpt-4",
    "recommendations_count": 7,
    "recommendations_applied": 7
  }
}
```

**Validation**:
- [ ] JSON file created in output directory
- [ ] File is valid JSON (can be parsed)
- [ ] Contains all expected fields

**Notes**:
- Create metadata dict before calling this function (pass as dict, not FileMetadata object)
- Rewrite metadata populated later by rewriter agent

---

### Subtask T011 – File utils unit tests

**Purpose**: Test all file operation functions for correctness and edge cases.

**Steps**:
1. Create `tests/utils/test_file_utils.py` (new file)
2. Create test fixtures: temporary test files (.txt, .md, .docx if available)
3. Test `copy_document_with_metadata()`:
   - `test_copy_preserves_content()` - Hash comparison
   - `test_copy_preserves_metadata()` - Timestamp comparison
   - `test_copy_creates_directory()` - Dir creation
   - `test_copy_file_not_found()` - Exception handling
4. Test `extract_file_metadata()`:
   - `test_extract_basic_metadata()` - Size, timestamps
   - `test_extract_docx_metadata()` - Author, properties
   - `test_extract_handles_missing_fields()` - None values
5. Test `generate_output_filename()`:
   - `test_filename_format()` - Pattern matching
   - `test_timestamp_utc()` - Timezone verification
   - `test_custom_timestamp()` - Provided timestamp
6. Test `save_metadata_json()`:
   - `test_json_created()` - File exists
   - `test_json_valid()` - Parseable
   - `test_json_contains_fields()` - Structure validation

**Files**:
- `tests/utils/test_file_utils.py` (new, ~150 lines)

**Commands**:
```bash
pytest tests/utils/test_file_utils.py -v
```

**Fixtures**:
- Use `tmp_path` pytest fixture for temporary files
- Create minimal .docx fixture for testing

---

## Test Strategy

All functions should have corresponding unit tests with:
- Happy path tests (normal operation)
- Edge case tests (missing files, empty files, special characters in filenames)
- Error handling tests (permission errors, invalid paths)
- Cross-platform considerations (different path separators)

---

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Metadata preservation varies by OS | Document limitations, store JSON fallback |
| Timestamp collisions unlikely but possible | Document as acceptable risk, could add counter if needed |
| Permission errors on copy | Log error, raise exception with helpful message |
| Special characters in filenames | Test with various characters, use Pathlib for cross-platform |

---

## Review Guidance

**Key acceptance checkpoints**:
- [ ] All functions implemented in `src/utils/file_utils.py`
- [ ] `copy_document_with_metadata()` preserves file content and metadata
- [ ] `generate_output_filename()` produces correct format with UTC timestamps
- [ ] `save_metadata_json()` creates valid JSON files
- [ ] Unit tests pass with >80% coverage
- [ ] Cross-platform compatibility verified (path handling works on Linux/macOS/Windows)

**Context for reviewers**:
- Verify filename format matches specification: `{name}_{YYYYMMDD_HHMMSS}.{ext}`
- Check that metadata extraction handles both .docx and plain text files
- Confirm JSON structure matches `file_operation_contract.json`
- Ensure error messages are actionable for users

---

## Activity Log

- 2026-02-17T21:00:00Z – system – lane=planned – Prompt created.
- 2026-02-18T12:40:00Z – claude-opus-4-6 – shell_pid=44565 – lane=doing – Assigned agent via workflow command
