# Work Packages: Review Agent Configuration System

**Feature**: 020-review-agent-configuration-system
**Date**: 2025-02-21
**Spec**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md)

## Overview

This document contains all work packages for implementing the Review Agent Configuration System. Each work package is independently implementable and can be worked on in parallel where marked `[P]`.

**Total Work Packages**: 7
**Estimated Implementation Time**: 3-5 days

## WP Sizes Summary

| WP | Title | Subtasks | Est. Lines |
|----|-------|----------|------------|
| WP01 | Review Config Value Objects | 8 | ~420 |
| WP02 | Config Merge Logic | 5 | ~280 |
| WP03 | Config Loader Infrastructure | 4 | ~240 |
| WP04 | YAML Configuration Update | 4 | ~240 |
| WP05 | Unit Tests | 6 | ~340 |
| WP06 | Integration Tests | 4 | ~240 |
| WP07 | Documentation | 5 | ~300 |

**Size Distribution**: All WPs within ideal range (240-420 lines)
**Average WP Size**: ~290 lines

---

## WP01: Review Config Value Objects

**Priority**: P0 (Foundational) | **Lane**: Planned
**Prompt**: [tasks/WP01-review-config-value-objects.md](tasks/WP01-review-config-value-objects.md)
**Dependencies**: None
**Parallelizable**: No (must be first)

**Summary**: Create all dataclass value objects for review configuration following the existing `RewriteConfig` pattern.

**Included Subtasks**:
- [x] T001: Create LLMConfig dataclass with validation (provider, model, temperature, top_p, max_tokens, timeout)
- [x] T002: Create PromptConfig dataclass (system_prompt, user_prompt, result_template, variables)
- [x] T003: Create RetryConfig dataclass with validation (max_retries, backoff, initial_delay)
- [x] T004: Create CheckConfig dataclass (security, performance, style flags)
- [x] T005: Create OutputConfig dataclass with validation (format, include_snippets, max_comment_length)
- [x] T006: Create ContextConfig dataclass (window_size, include_patterns, exclude_patterns)
- [x] T007: Create LoggingConfig dataclass with validation (level, debug)
- [x] T008: Create ReviewConfig root dataclass with from_dict() classmethod

**Implementation Sketch**:
1. Create `src/rewrite/domain/review_config.py` file
2. Define each config dataclass with frozen=True and __post_init__ validation
3. Implement ReviewConfig.from_dict() that parses nested dict structure
4. Add type hints and docstrings following project style

**Files**:
- `src/rewrite/domain/review_config.py` (new, ~250 lines)

**Definition of Done**:
- All dataclasses defined with proper validation
- from_dict() successfully loads from dict matching YAML structure
- ValueError raised for invalid inputs (temperature out of range, etc.)
- Code matches existing RewriteConfig style
- All imports work correctly

**Risks**:
- Low - follows existing patterns in value_objects.py

---

## WP02: Config Merge Logic

**Priority**: P0 (Foundational) | **Lane**: Planned
**Prompt**: [tasks/WP02-config-merge-logic.md](tasks/WP02-config-merge-logic.md)
**Dependencies**: WP01
**Parallelizable**: No (depends on WP01)

**Summary**: Implement hierarchical merge logic for profiles and CLI overrides with key-based (not full) override behavior.

**Included Subtasks**:
- [x] T009: Implement merge_with_profile() method on ReviewConfig
- [x] T010: Implement merge_with_cli() method on ReviewConfig
- [x] T011: Create deep_merge helper function for nested dict merging
- [x] T012: Implement placeholder substitution (format variables into prompts)
- [x] T013: Add profile validation (profile exists in profiles dict)

**Implementation Sketch**:
1. Add merge_with_profile(profile_name: str) -> ReviewConfig method
2. Add merge_with_cli(overrides: Dict) -> ReviewConfig method
3. Create deep_merge(base: Dict, override: Dict) -> Dict helper
4. Implement substitute_placeholders(template: str, variables: Dict) -> str
5. Add validation that selected profile exists

**Files**:
- `src/rewrite/domain/review_config.py` (modify, add ~150 lines)

**Definition of Done**:
- Profile merge overrides only specified keys (inherits rest)
- CLI overrides have highest priority
- Merge works for nested structures (llm.temperature, checks.security, etc.)
- Placeholders {file_path}, {project_name}, etc. are substituted
- KeyError raised with helpful message for missing profiles
- Immutable pattern preserved (returns new ReviewConfig instances)

**Risks**:
- Medium - merge logic complexity, especially nested structures
- Mitigation: Comprehensive unit tests for edge cases

---

## WP03: Config Loader Infrastructure

**Priority**: P0 (Foundational) | **Lane**: Planned
**Prompt**: [tasks/WP03-config-loader-infrastructure.md](tasks/WP03-config-loader-infrastructure.md)
**Dependencies**: WP01, WP02
**Parallelizable**: [P] Can be done in parallel with WP04 after WP01, WP02 complete

**Summary**: Create config loader with YAML parsing, environment variable expansion, and validation.

**Included Subtasks**:
- [ ] T014: Create config_loader.py with load_config(path: Path) function
- [ ] T015: Add environment variable expansion (${VAR:default} syntax)
- [ ] T016: Implement configuration validation with clear error messages
- [ ] T017: Add error handling for missing files, invalid YAML, validation failures

**Implementation Sketch**:
1. Create `src/rewrite/infrastructure/config_loader.py`
2. Implement load_config() that reads YAML and expands env vars
3. Add validate_config() that checks all constraints
4. Provide helpful error messages for common issues

**Files**:
- `src/rewrite/infrastructure/config_loader.py` (new, ~120 lines)

**Definition of Done**:
- load_config() successfully reads debate_config.yaml
- Environment variables expanded with ${VAR:default} syntax
- Validation errors include: what's wrong, what value was given, valid options
- FileNotFoundError for missing config files
- YAML errors parsed and reported clearly

**Risks**:
- Low - standard YAML loading with PyYAML

---

## WP04: YAML Configuration Update

**Priority**: P1 | **Lane**: Planned
**Prompt**: [tasks/WP04-yaml-configuration-update.md](tasks/WP04-yaml-configuration-update.md)
**Dependencies**: WP01
**Parallelizable**: [P] Can be done in parallel with WP02, WP03 after WP01 complete

**Summary**: Update debate_config.yaml with review section including profiles, prompts, and all configuration options.

**Included Subtasks**:
- [ ] T018: Add review section to debate_config.yaml under rewrite
- [ ] T019: Add three profile presets (strict, balanced, lenient) with appropriate values
- [ ] T020: Document all default values in comments
- [ ] T021: Create example directory structure for custom prompts (src/prompts/review/)

**Implementation Sketch**:
1. Open `config/debate_config.yaml`
2. Add review subsection under rewrite:
   - profile selection
   - llm settings
   - prompts config
   - prompt_variables
   - retry policy
   - checks config
   - output config
   - context config
   - logging config
   - profiles dict with strict/balanced/lenient
3. Create placeholder prompt files
4. Add comments explaining each option

**Files**:
- `config/debate_config.yaml` (modify, add ~60 lines)
- `src/prompts/review/.gitkeep` (new, placeholder directory)

**Definition of Done**:
- YAML is valid and parses correctly
- All config options from spec are present
- Three profiles defined with sensible defaults
- Comments explain what each option does
- Example prompt directory structure created
- Config loader can load the review section

**Risks**:
- Low - straightforward YAML addition

---

## WP05: Unit Tests

**Priority**: P1 | **Lane**: Planned
**Prompt**: [tasks/WP05-unit-tests.md](tasks/WP05-unit-tests.md)
**Dependencies**: WP01, WP02, WP03
**Parallelizable**: [P] Can be done in parallel with WP06 after WP01-WP03 complete

**Summary**: Comprehensive unit tests for all configuration objects and merge logic.

**Included Subtasks**:
- [ ] T022: Test LLMConfig validation (temperature, top_p ranges, etc.)
- [ ] T023: Test profile merge logic (inheritance, override behavior)
- [ ] T024: Test CLI override logic (priority over profile)
- [ ] T025: Test placeholder substitution (file_path, project_name, custom vars)
- [ ] T026: Test configuration validation errors (all error paths)
- [ ] T027: Test edge cases (missing profiles, empty configs, invalid types)

**Implementation Sketch**:
1. Create `tests/unit/rewrite/test_review_config.py`
2. Test each config dataclass validation
3. Test merge scenarios (base only, base+profile, base+profile+cli)
4. Test placeholder substitution with various variable sets
5. Test error conditions with helpful assertions
6. Achieve >80% coverage for review_config.py

**Files**:
- `tests/unit/rewrite/test_review_config.py` (new, ~300 lines)

**Definition of Done**:
- All validation rules tested
- Merge logic tested with various combinations
- Placeholder substitution tested for all variables
- Error messages validated to be helpful
- pytest passes for all tests
- Coverage report shows >80% for review_config.py

**Risks**:
- Low - straightforward unit testing

---

## WP06: Integration Tests

**Priority**: P2 | **Lane**: Planned
**Prompt**: [tasks/WP06-integration-tests.md](tasks/WP06-integration-tests.md)
**Dependencies**: WP01, WP02, WP03, WP04
**Parallelizable**: [P] Can be done in parallel with WP05, WP07 after WP01-WP04 complete

**Summary**: End-to-end tests for configuration loading and merge workflow.

**Included Subtasks**:
- [ ] T028: Test full config loading workflow (YAML → ReviewConfig)
- [ ] T029: Test profile application end-to-end (load with profile)
- [ ] T030: Test CLI override end-to-end (load with CLI flags)
- [ ] T031: Test invalid config handling (bad YAML, missing profiles, etc.)

**Implementation Sketch**:
1. Create `tests/integration/test_review_config_workflow.py`
2. Test loading from actual YAML file
3. Test profile selection and application
4. Test CLI override scenarios
5. Test error handling with invalid configs
6. Use fixtures for test config files

**Files**:
- `tests/integration/test_review_config_workflow.py` (new, ~200 lines)
- `tests/fixtures/review_config/` (new, test YAML files)

**Definition of Done**:
- Full load workflow tested with real YAML
- Profile application verified end-to-end
- CLI override tested with various scenarios
- Invalid config handling tested
- All integration tests pass

**Risks**:
- Low - integration testing is straightforward

---

## WP07: Documentation

**Priority**: P2 | **Lane**: Planned
**Prompt**: [tasks/WP07-documentation.md](tasks/WP07-documentation.md)
**Dependencies**: WP01, WP02, WP03, WP04
**Parallelizable**: [P] Can be done in parallel with WP05, WP06 after WP01-WP04 complete

**Summary**: User documentation for review agent configuration system.

**Included Subtasks**:
- [ ] T032: Create docs/review-agent-config.md with overview
- [ ] T033: Add configuration examples for common scenarios
- [ ] T034: Document profile system and merge behavior
- [ ] T035: Document placeholder system and variables
- [ ] T036: Add migration guide from old config (if applicable)

**Implementation Sketch**:
1. Create `docs/review-agent-config.md`
2. Write overview of configuration system
3. Document all config options with descriptions
4. Provide examples for each profile
5. Explain placeholder substitution
6. Add troubleshooting section

**Files**:
- `docs/review-agent-config.md` (new, ~400 lines)

**Definition of Done**:
- All config options documented
- Examples provided for common use cases
- Profile system clearly explained
- Placeholder system documented
- Migration guide included if needed
- Documentation follows project style (see docs/rewrite.md)
- Constitution requirement met (feature documentation)

**Risks**:
- Low - documentation task

---

## Dependency Graph

```
WP01 (Value Objects)
 ├─→ WP02 (Merge Logic)
 ├─→ WP03 (Config Loader)
 │    └─→ WP04 (YAML Config) [can parallel with WP02]
 ├─→ WP05 (Unit Tests)
 ├─→ WP06 (Integration Tests)
 └─→ WP07 (Documentation)
```

**Parallelization Opportunities**:
- After WP01: WP02, WP03, WP04 can run in parallel
- After WP01-WP04: WP05, WP06, WP07 can run in parallel

---

## MVP Scope

**Minimum Viable Product**: WP01 + WP02 + WP03 + WP04

This provides:
- All value objects defined
- Merge logic for profiles and CLI
- Config loading infrastructure
- Working YAML configuration

**Estimated MVP Time**: 2-3 days

**Full Feature**: Add WP05, WP06, WP07 for production readiness with tests and documentation.

---

## Execution Order

**Suggested sequence for single implementer**:
1. WP01 (foundational)
2. WP02 (depends on WP01)
3. WP03 (depends on WP01, WP02)
4. WP04 (can parallel, but logical order)
5. WP05 (tests after implementation)
6. WP06 (integration tests)
7. WP07 (documentation)

**Suggested sequence for parallel team**:
- **Agent 1**: WP01 → WP02 → WP05
- **Agent 2**: (wait for WP01) → WP03 → WP06
- **Agent 3**: (wait for WP01) → WP04 → WP07
