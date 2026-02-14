---
work_package_id: WP01
title: Foundation & CLI Scaffolding
lane: "done"
dependencies: []
base_branch: main
base_commit: 68851a5663dd0af255eb97f3cc86f99d76ed5536
created_at: '2026-02-14T01:08:21.189494+00:00'
subtasks:
- T001
- T002
- T003
- T004
- T005
- T006
- T007
phase: Foundation
shell_pid: "67247"
reviewed_by: "ALeks ishmanov"
review_status: "approved"
---

## Work Package Prompt: WP01 – Foundation & CLI Scaffolding

**Summary**: Set up foundational CLI structure for `product_committee.py` with all required and optional arguments, logging infrastructure, and basic project skeleton.

**Priority**: P1 (Foundation - must complete first)

**Independent Test**: Run `product_committee.py --help` and see all CLI arguments with proper descriptions and defaults.

## Context & Constraints

**Reference Documents**:
- [spec.md](spec.md) - Functional requirements FR-026 through FR-032
- [plan.md](plan.md) - Technical context, CLI interface section
- [data-model.md](data-model.md) - Input validation requirements

**Architectural Decisions**:
- **MVP approach**: Subprocess invocation of `document_debate_cli.py` (no library refactor yet)
- **Logging**: Three-level configurable system (default, verbose, quiet)
- **Error handling**: Fatal errors exit non-zero; recoverable errors log warnings
- **File structure**: Single script at repository root alongside existing debate CLI

**Constraints**:
- Must not modify existing `document_debate_cli.py` in this WP
- Use Python 3.12+ argparse or click (match existing patterns)
- All CLI flags must have sensible defaults per spec

## Subtasks & Detailed Guidance

### Subtask T001 – Create product_committee.py with basic structure

**Purpose**: Establish the main orchestrator script file with proper shebang, imports, and basic scaffolding.

**Steps**:
1. Create `product_committee.py` at repository root (same level as `document_debate_cli.py`)
2. Add Python shebang: `#!/usr/bin/env python3`
3. Import required modules: `sys`, `os`, `json`, `pathlib`, `subprocess`, `argparse` or `click`, `logging`, `datetime`
4. Create basic `if __name__ == "__main__":` block with `main()` call
5. Add docstring describing the orchestrator's purpose

**Files**:
- `product_committee.py` (new file, ~50 lines)

**Validation**:
- [ ] File exists at repository root
- [ ] Shebang is correct for Python 3
- [ ] All imports are standard library or project-local
- [ ] `if __name__` block present

**Notes**:
- Keep imports minimal for now; add more as functionality grows
- Docstring should reference the feature specification

---

### Subtask T002 – Implement argparse/click argument parsing

**Purpose**: Define all CLI arguments per FR-026 through FR-032 with proper validation and defaults.

**Steps**:
1. Choose argparse or click based on existing project patterns (check `document_debate_cli.py`)
2. Define required arguments:
   - `--prd` / `--docx` (synonyms, required): Path to PRD document
   - `--question` (required): Committee question text
3. Define optional arguments:
   - `--model`: LLM model name (passed through to debate CLI)
   - `--max-retries`: Retry count per room (default: 2)
   - `--output-dir`: Output directory (default: `./committee_output`)
   - `--roles-dir`: Role prompts directory (default: `prompts/roles/`)
   - `--run-id`: Manual run identifier (auto-generate if omitted)
   - `--allow-short-prd`: Enforce minimum PRD length flag
   - `--verbose`: Enable verbose logging
   - `--quiet`: Enable quiet mode (minimal output)
4. Add argument validation:
   - PRD path must exist if provided
   - Question must be non-empty string
   - max-retries must be >= 0
   - verbose and quiet are mutually exclusive
5. Add `--help` argument with descriptive usage message

**Files**:
- `product_committee.py` (modify, add ~80 lines)

**Validation**:
- [ ] All required arguments defined
- [ ] All optional arguments defined with correct defaults
- [ ] Help text displays correctly
- [ ] Mutually exclusive flags enforced (--verbose vs --quiet)

**Notes**:
- Match existing CLI argument style from `document_debate_cli.py`
- Use descriptive help texts that explain each argument's purpose

---

### Subtask T003 – Add --prd/--docx required argument with validation

**Purpose**: Implement the primary input argument for PRD document path with existence validation.

**Steps**:
1. Add argument definition accepting both `--prd` and `--docx` as synonyms
2. Mark argument as required
3. Implement validation function that checks:
   - File exists at specified path
   - File is readable (os.access(path, os.R_OK))
   - Exit with error code 1 if validation fails
4. Add clear error message: "Error: PRD file not found or unreadable: {path}"

**Files**:
- `product_committee.py` (modify, add ~30 lines)

**Validation**:
- [ ] `--prd` and `--docx` both work
- [ ] Required argument enforced
- [ ] Non-existent file triggers error with clear message
- [ ] Unreadable file triggers error with clear message
- [ ] Exit code 1 on validation failure

**Notes**:
- This is a fatal error per spec FR-033
- Must run before any rooms are executed

---

### Subtask T004 – Add --question required argument with validation

**Purpose**: Implement the committee question argument with non-empty validation.

**Steps**:
1. Add `--question` argument definition (string type)
2. Mark argument as required
3. Implement validation that question string is not empty after stripping
4. Add clear error message: "Error: Question cannot be empty. Please provide a question for the committee."

**Files**:
- `product_committee.py` (modify, add ~20 lines)

**Validation**:
- [ ] Required argument enforced
- [ ] Empty string validation implemented
- [ ] Clear error message displayed
- [ ] Exit code 1 on validation failure

**Notes**:
- This is a fatal error per spec FR-034
- Must run before any rooms are executed

---

### Subtask T005 – Add optional arguments: --model, --max-retries, --output-dir

**Purpose**: Implement secondary optional arguments for model selection, retry configuration, and output location.

**Steps**:
1. Add `--model` argument (optional, string): LLM model name, passed through to debate CLI
2. Add `--max-retries` argument (optional, int, default=2): Maximum retry attempts per room
3. Add `--output-dir` argument (optional, string, default="./committee_output"): Base output directory
4. Implement validation:
   - max-retries must be >= 0
   - output-dir parent directory must exist (or create it)
5. Use argparse/click features for defaults and help text

**Files**:
- `product_committee.py` (modify, add ~40 lines)

**Validation**:
- [ ] All three arguments defined with correct types
- [ ] Defaults applied correctly
- [ ] Validation for max-retries >= 0
- [ ] output-dir defaults to ./committee_output

**Notes**:
- These are optional, so no validation failure if omitted
- Model name pass-through is for future use; may not work in MVP

---

### Subtask T006 – Add optional arguments: --roles-dir, --run-id, --allow-short-prd

**Purpose**: Implement remaining optional arguments for role customization and PRD validation behavior.

**Steps**:
1. Add `--roles-dir` argument (optional, string, default="prompts/roles/"): Role prompts location
2. Add `--run-id` argument (optional, string): Manual run identifier (auto-generate if omitted)
3. Add `--allow-short-prd` argument (optional, boolean flag): Enforce minimum PRD length (100 chars)
4. Implement run-id slug generation if not provided:
   - Extract first 3-5 words from question
   - Lowercase and hyphenate (e.g., "what is potential" → "what-is-potential")
   - Generate timestamp: YYYY-MM-DD_HHMMSS
5. Implement --allow-short-prd behavior:
   - If set, PRD < 100 chars is fatal error (not warning)
   - Exit with clear message about minimum length

**Files**:
- `product_committee.py` (modify, add ~50 lines)

**Validation**:
- [ ] All three arguments defined
- [ ] roles-dir defaults to prompts/roles/
- [ ] run-id auto-generation works when omitted
- [ ] --allow-short-prd changes PRD < 100 chars from warning to error
- [ ] Slug generation produces valid format (3-5 words, hyphenated)

**Notes**:
- Slug generation affects output directory name
- --allow-short-prd is for strict validation mode per FR-041

---

### Subtask T007 – Implement --verbose/--quiet logging flags and basic logging setup

**Purpose**: Set up Python logging infrastructure with three configurable levels (normal, verbose, quiet) per logging strategy.

**Steps**:
1. Import logging module and configure basic logger
2. Add `--verbose` flag (optional, boolean): Enable detailed logging
3. Add `--quiet` flag (optional, boolean): Minimal logging (start/finish/errors only)
4. Implement mutual exclusivity: verbose and quiet cannot both be set
5. Configure logging levels:
   - **Default (normal)**: INFO level - show room start/completion, timestamps, statuses, output paths
   - **Verbose**: DEBUG level - show retries, CLI parameters, file sizes
   - **Quiet**: WARNING level - show only critical errors and final path
6. Set up logging format: timestamp + level + message

**Files**:
- `product_committee.py` (modify, add ~60 lines)

**Validation**:
- [ ] Logger configured with correct format
- [ ] All three modes work (default, verbose, quiet)
- [ ] Verbose and quiet are mutually exclusive
- [ ] Log levels match spec (Section 1.4 Logging Strategy)
- [ ] Run `product_committee.py --verbose` and `--quiet` to test

**Notes**:
- Use Python's built-in logging module (not custom logger)
- Log to stdout (not files) for MVP
- This logging infrastructure supports all subsequent WPs

---

## Test Strategy

Not applicable for this WP (foundation work).

## Risks & Mitigations

**Risk**: Argument parsing complexity may grow with many flags.
- **Mitigation**: Group related arguments (input args, config args, logging args) in help text

**Risk**: Defaults must match spec exactly.
- **Mitigation**: Cross-reference FR-026 through FR-032 in spec when implementing

**Risk**: Mutual exclusivity validation (--verbose vs --quiet) may be tricky.
- **Mitigation**: Use argparse/click built-in mutually exclusive groups

## Review Guidance

**Acceptance Criteria**:
- [ ] `product_committee.py --help` shows all arguments with clear descriptions
- [ ] All required arguments enforce presence
- [ ] All defaults match spec (output-dir=./committee_output, max-retries=2, roles-dir=prompts/roles/)
- [ ] --verbose and --quiet flags work correctly
- [ ] Help text is comprehensive and user-friendly

**Key Checkpoints**:
- CLI structure matches existing project patterns
- All functional requirements for CLI (FR-026 to FR-032) addressed
- Argument validation prevents invalid starts

## Activity Log

- 2026-02-14T08:34:54Z – unknown – shell_pid=67247 – lane=done – Review passed: All WP01 requirements met - CLI scaffolding complete with all required/optional arguments, validation, logging infrastructure. Implementation also completed WP02-WP06 (subprocess wrapper, orchestration, reflection, report generation, tests).
