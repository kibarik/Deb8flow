---
work_package_id: "WP01"
subtasks:
  - "T001"
  - "T002"
  - "T003"
  - "T004"
  - "T005"
  - "T006"
title: "Foundation Setup"
phase: "Phase 1 - Foundation"
lane: "planned"  # DO NOT EDIT - use: spec-kitty agent tasks move-task <WPID> --to <lane>
assignee: ""      # Optional friendly name when in doing/for_review
agent: ""         # CLI agent identifier (claude, codex, etc.)
shell_pid: ""     # PID captured when the task moved to the current lane
review_status: "" # empty | has_feedback | acknowledged (populated by reviewers/implementers)
reviewed_by: ""   # Agent ID of the reviewer (if reviewed)
history:
  - timestamp: "2026-02-17T21:00:00Z"
    lane: "planned"
    agent: "system"
    shell_pid: ""
    action: "Prompt created via /spec-kitty.tasks"
dependencies: []
---

# Work Package Prompt: WP01 – Foundation Setup

## Objectives & Success Criteria

- **Goal**: Establish project structure, dependencies, and core data models for the Document Rewrite Agent feature.
- **Success Criteria**:
  - New directories `src/agents/` and `src/converters/` created with proper `__init__.py` files
  - `mammoth>=1.8.0` added to `requirements.txt` and successfully installable
  - All data model classes (`RewriteRequest`, `RewriteResult`, `ConversionResult`, etc.) can be imported without errors
  - Exception hierarchy (`RewriteError`, `ConversionError`, `LLMError`, `ValidationError`) defined and importable

## Context & Constraints

- **Prerequisites**: None (foundation package)
- **Supporting Documents**:
  - `.kittify/memory/constitution.md` - Python 3.12+, pytest required, minimal dependencies
  - `kitty-specs/015-document-rewrite-agent/plan.md` - Architecture decisions (standalone script, markdown intermediate)
  - `kitty-specs/015-document-rewrite-agent/data-model.md` - Complete entity definitions
  - `kitty-specs/015-document-rewrite-agent/research.md` - Technical decisions (mammoth library, error handling)
  - `kitty-specs/015-document-rewrite-agent/contracts/` - JSON schema contracts
- **Constraints**:
  - Must follow existing codebase patterns (see `src/types/conclusion_types.py` for reference)
  - Use Python 3.12+ type hints and dataclasses
  - Keep dependencies minimal (only mammoth addition justified)
  - Cross-platform compatibility (Linux, macOS, Windows)

## Subtasks & Detailed Guidance

### Subtask T001 – Create directory structure

**Purpose**: Establish the new directories needed for agents and converters.

**Steps**:
1. Create `src/agents/` directory at project root
2. Create `src/converters/` directory at project root
3. Add `__init__.py` to each new directory (empty file with docstring)
4. Verify directory structure: `ls -la src/agents/` and `ls -la src/converters/`

**Files**:
- `src/agents/__init__.py` (new)
- `src/converters/__init__.py` (new)

**Notes**:
- Follow existing directory patterns in `src/`
- Add module docstrings to `__init__.py` files explaining the module's purpose

---

### Subtask T002 – Add mammoth dependency

**Purpose**: Add the mammoth library for .docx to markdown conversion.

**Steps**:
1. Open `requirements.txt` at project root
2. Add `mammoth>=1.8.0` to the dependencies section
3. Verify no version conflicts with existing dependencies
4. Test installation: `pip install -r requirements.txt` (should succeed without errors)

**Files**:
- `requirements.txt` (modify)

**Validation**:
- [ ] `mammoth>=1.8.0` added to requirements.txt
- [ ] `pip install -r requirements.txt` succeeds
- [ ] `import mammoth` works in Python REPL

---

### Subtask T003 – Create core dataclasses

**Purpose**: Define the core data structures for rewriter requests and results.

**Steps**:
1. Create `src/types/rewrite_types.py` (new file)
2. Import `dataclass`, `Optional` from `typing`
3. Create `RewriteRequest` dataclass with fields:
   - `original_document_path: str`
   - `conclusion_path: str`
   - `output_directory: str`
   - `original_filename: str`
   - `format: DocumentFormat`
   - `model_config: LLMConfig`
   - `validate_recommendations: bool = True`
4. Create `RewriteResult` dataclass with fields:
   - `success: bool`
   - `error_message: Optional[str]`
   - `rewritten_document_path: str`
   - `recommendations_count: int`
   - `recommendations_applied: int`
   - `inline_notes_count: int`
   - `processing_time_seconds: float`
   - `validation_passed: bool`
   - `validation_details: Optional[str]`
5. Create `RewriteOptions` dataclass with fields:
   - `aggressive_mode: bool = True`
   - `resolve_contradictions: bool = True`
   - `preserve_formatting: bool = True`
   - `add_inline_notes: bool = True`
   - `validate_completeness: bool = True`
   - `fallback_on_error: bool = True`

**Files**:
- `src/types/rewrite_types.py` (new, ~80 lines)

**Notes**:
- Follow the pattern from `src/types/conclusion_types.py`
- Use Python 3.12+ type syntax (e.g., `str` instead of `typing.String`)
- Add docstrings to each dataclass explaining its purpose
- Use `Optional[str]` for nullable fields

---

### Subtask T004 – Create supporting types

**Purpose**: Define enums and configuration types used throughout the rewriter system.

**Steps**:
1. In `src/types/rewrite_types.py`, create `DocumentFormat` enum:
   - Values: `DOCX = "docx"`, `MARKDOWN = "md"`, `TEXT = "txt"`, `RTF = "rtf"`
   - Class method: `from_extension(extension: str) -> DocumentFormat`
   - Method: `supports_markdown_intermediate() -> bool`
2. Create `ActionType` enum:
   - Values: `REMOVE = "remove"`, `UPDATE = "update"`, `ADD = "add"`, `REPLACE = "replace"`, `RESTRUCTURE = "restructure"`
3. Create `LLMConfig` dataclass:
   - `model_name: str`
   - `temperature: float = 0.7`
   - `max_tokens: int = 4096`
   - `provider: str = "openai"`
   - `api_key: Optional[str] = None`

**Files**:
- `src/types/rewrite_types.py` (append to existing file from T003)

**Notes**:
- The `from_extension()` method should handle both with and without dot (e.g., "docx" and ".docx")
- `supports_markdown_intermediate()` returns True for DOCX, MARKDOWN, TEXT
- LLMConfig reuses existing patterns from `configurations/llm_config.py`

---

### Subtask T005 – Create conversion types

**Purpose**: Define data structures for format conversion operations.

**Steps**:
1. Create `src/types/conversion_types.py` (new file)
2. Import `dataclass`, `Optional`, `List`, `Dict`, `Any` from `typing`
3. Create `ConversionResult` dataclass with fields:
   - `success: bool`
   - `error_message: Optional[str]`
   - `markdown_content: Optional[str]`
   - `original_content: Optional[bytes]`
   - `metadata_preserved: Dict[str, Any]`
   - `formatting_warnings: List[str]`
4. Create `FileMetadata` dataclass with fields:
   - `original_path: str`
   - `original_filename: str`
   - `original_extension: str`
   - `created_at: Optional[str]`
   - `modified_at: Optional[str]`
   - `copied_at: str`
   - `author: Optional[str]`
   - `size_bytes: int`
   - `doc_properties: Optional[Dict[str, Any]]`
5. Create `Recommendation` dataclass with fields:
   - `section_reference: Optional[str]`
   - `action_type: ActionType`
   - `target_content: Optional[str]`
   - `new_content: Optional[str]`
   - `priority: int`
   - `rationale: Optional[str]`

**Files**:
- `src/types/conversion_types.py` (new, ~80 lines)

**Notes**:
- Follow existing type patterns from `src/types/`
- Add `from src.types.rewrite_types import ActionType` for the Recommendation class
- All timestamp strings should be ISO 8601 format

---

### Subtask T006 – Create exception hierarchy

**Purpose**: Define custom exceptions for error handling throughout the rewriter system.

**Steps**:
1. In `src/types/rewrite_types.py`, create base `RewriteError` exception:
   - Inherit from `Exception`
   - Accept `message: str` and `recoverable: bool = True` in `__init__`
   - Store as instance attributes
2. Create `FileNotFoundError` (alias to avoid conflict with builtin):
   - Inherit from `RewriteError`
   - Set `recoverable = False` as class attribute
3. Create `ConversionError`:
   - Inherit from `RewriteError`
   - Set `recoverable = True` as class attribute
4. Create `LLMError`:
   - Inherit from `RewriteError`
   - Set `recoverable = True` as class attribute
5. Create `ValidationError`:
   - Inherit from `RewriteError`
   - Set `recoverable = True` as class attribute
6. Create `WriteError`:
   - Inherit from `RewriteError`
   - Set `recoverable = False` as class attribute

**Files**:
- `src/types/rewrite_types.py` (append to existing file from T003, T004)

**Notes**:
- Use `_FileNotFoundError` as internal name to avoid shadowing builtin, export as `FileNotFoundError`
- The `recoverable` attribute determines whether the main workflow can continue
- Each exception should have a clear docstring explaining when it's raised

---

## Test Strategy

**Note**: Tests are required per project constitution (pytest). Create basic import/initialization tests.

### Unit Tests (T001-T006 validation)

Create `tests/types/test_rewrite_types.py` with:
- `test_can_import_all_types()` - Verify all new types can be imported
- `test_rewrite_request_creation()` - Verify RewriteRequest can be instantiated
- `test_rewrite_result_creation()` - Verify RewriteResult can be instantiated
- `test_document_format_enum()` - Test DocumentFormat enum values and from_extension()
- `test_action_type_enum()` - Test ActionType enum values
- `test_exception_hierarchy()` - Verify all exceptions inherit from RewriteError
- `test_exception_recoverable_attribute()` - Verify recoverable attribute is set correctly

**Files**:
- `tests/types/test_rewrite_types.py` (new, ~80 lines)

**Commands**:
```bash
pytest tests/types/test_rewrite_types.py -v
```

---

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Mammoth installation fails on some systems | Document in README, add troubleshooting note |
| Type conflicts with existing types | Use distinct naming, namespace in separate modules |
| Python version compatibility | Use Python 3.12+ syntax, verify type hints work |
| Import path issues | Verify all `__init__.py` files are in place |

---

## Review Guidance

**Key acceptance checkpoints**:
- [ ] Directory structure exists at `src/agents/` and `src/converters/`
- [ ] `mammoth>=1.8.0` added to requirements.txt and installs successfully
- [ ] All dataclass types can be imported: `from src.types.rewrite_types import *` and `from src.types.conversion_types import *`
- [ ] Each dataclass matches the specification in `data-model.md`
- [ ] Exception hierarchy properly defined with `recoverable` attribute
- [ ] Unit tests pass: `pytest tests/types/test_rewrite_types.py`

**Context for reviewers**:
- This is the foundation package - all other WPs depend on these types
- Verify dataclass fields match the contracts in `contracts/rewriter_agent_contract.json`
- Check that `DocumentFormat.from_extension()` handles edge cases (uppercase, with/without dot)
- Confirm exception `recoverable` attributes align with error handling strategy in `research.md`

---

## Activity Log

- 2026-02-17T21:00:00Z – system – lane=planned – Prompt created.

### Valid lanes

`planned` → `doing` → `for_review` → `done`
