# WP09: Final Validation and Cleanup

**Work Package**: 017-product-committee-clean-architecture-refactoring / WP09
**Status**: TODO
**Dependencies**: WP07, WP08

## Overview

Final validation, performance testing, and code cleanup to ensure the refactored system meets all success criteria.

## Validation Checklist

### 1. Functional Equivalence

```bash
# Run all existing tests - must pass 100%
pytest tests/test_product_committee.py -v

# Run integration tests
pytest tests/integration/ -v

# Run snapshot tests
pytest tests/snapshots/ -v

# Full test suite
pytest -v
```

**Acceptance**: All tests pass without modification.

### 2. Code Quality Metrics

```bash
# Check line counts
wc -l product_committee.py  # Should be <500 lines
find src/shared/debate -name "*.py" -exec wc -l {} +  # Check module sizes
find src/committee -name "*.py" -exec wc -l {} +

# Check for duplicate code
# (Manual review or use tools like pylint/radon)

# Check cyclomatic complexity
radon cc src/ -a

# Check coupling
pylint src/shared/debate/ src/committee/
```

**Acceptance**:
- `product_committee.py` < 500 lines
- Each module < 500 lines
- Zero duplicate code blocks >10 lines
- Cyclomatic complexity acceptable (<10 per function)

### 3. Performance Benchmarks

```python
# tests/performance/benchmark_concurrent_execution.py
import time
import asyncio
from pathlib import Path
from src.committee.application.run_committee import RunProductCommittee
from src.shared.debate.infrastructure.executors.cli_executor import CliDebateExecutor
from src.shared.debate.infrastructure.storage.local_storage import LocalFileStorage
from src.committee.adapters.reports import CommitteeReportGenerator

async def benchmark():
    """Benchmark parallel vs sequential execution."""
    executor = CliDebateExecutor()
    generator = CommitteeReportGenerator()
    storage = LocalFileStorage()
    use_case = RunProductCommittee(executor, generator, storage)

    # Sequential benchmark
    start = time.time()
    sequential = await use_case.execute(
        prd_path="test_prd.txt",
        question="Test question",
        roles_dir="prompts/roles/",
        model=None,
        language=None,
        max_retries=2,
        max_concurrency=1,  # Sequential
        output_dir=Path("./benchmark_output"),
        manual_run_id=None
    )
    sequential_time = time.time() - start

    # Parallel benchmark
    start = time.time()
    parallel = await use_case.execute(
        prd_path="test_prd.txt",
        question="Test question",
        roles_dir="prompts/roles/",
        model=None,
        language=None,
        max_retries=2,
        max_concurrency=0,  # All rooms at once
        output_dir=Path("./benchmark_output"),
        manual_run_id=None
    )
    parallel_time = time.time() - start

    print(f"Sequential: {sequential_time:.2f}s")
    print(f"Parallel: {parallel_time:.2f}s")
    print(f"Ratio: {parallel_time / sequential_time:.1%}")

    # Parallel should be <= 60% of sequential
    assert parallel_time <= (sequential_time * 0.6), \
        f"Parallel too slow: {parallel_time}s vs {sequential_time}s"

if __name__ == "__main__":
    asyncio.run(benchmark())
```

**Acceptance**: Parallel execution completes in ≤60% of sequential time.

### 4. Architecture Compliance

```python
# tests/architecture/test_layer_compliance.py
import ast
import importlib
from pathlib import Path

def test_domain_layer_no_external_deps():
    """Verify domain layer has zero external dependencies."""
    domain_files = Path("src/shared/debate/domain/").glob("*.py")

    for file in domain_files:
        if file.name == "__init__.py":
            continue

        with open(file) as f:
            tree = ast.parse(f.read())

        # Check imports
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    # Only standard library allowed
                    assert alias.name in [
                        "dataclasses", "typing", "enum", "json",
                        "re", "datetime", "pathlib"
                    ], f"{file} has external import: {alias.name}"

def test_application_uses_protocols():
    """Verify application layer uses typing.Protocol."""
    ports_file = Path("src/shared/debate/application/ports.py")
    with open(ports_file) as f:
        content = f.read()

    # Should use Protocol, not ABC
    assert "Protocol" in content
    assert "ABC" not in content

def test_no_infrastructure_in_domain():
    """Verify domain doesn't import from infrastructure."""
    domain_files = Path("src/shared/debate/domain/").glob("*.py")

    for file in domain_files:
        with open(file) as f:
            content = f.read()

        # Should not import infrastructure
        assert "infrastructure" not in content
        assert "adapters" not in content
```

**Acceptance**: All architecture compliance tests pass.

### 5. Constitution Requirements

```bash
# Verify all requirements met
grep -r "pytest" requirements.txt  # pytest required
grep -r "import pydantic" src/shared/debate/domain/  # Should be empty
```

**Acceptance**:
- pytest required ✓
- Pydantic only at boundaries ✓
- No DI framework ✓
- Minimal dependencies ✓

### 6. Code Cleanup

Remove any remaining issues:

```bash
# Remove commented-out code
find src/ -name "*.py" -exec grep -l "^# " {} \;  # Review and clean

# Remove unused imports
autoflake --in-place --remove-all-unused-imports src/

# Sort imports
isort src/

# Format code
black src/

# Lint
pylint src/ --max-line-length=100

# Type check
mypy src/
```

### 7. Final Test Suite

```bash
# Complete test run
pytest --cov=src/shared --cov=src/committee --cov-report=html

# Check coverage is acceptable (>80%)
```

## Success Criteria Validation

| Criterion | Method | Target | Actual |
|-----------|--------|--------|--------|
| Functional Equivalence | All existing tests pass | 100% | ___ |
| Code Quality | Line count per module | <500 | ___ |
| Duplication | Code analysis | 0 blocks >10 lines | ___ |
| Architecture | Layer dependency analysis | Clear separation | ___ |
| Test Coverage | pytest --cov | Domain 100% | ___ |
| Performance | Benchmark | ≤60% time | ___ |
| Test Suite | pytest | 100% pass | ___ |

## PR Preparation

### Create Pull Request

```markdown
# Refactor Product Committee to Clean Architecture

## Summary

Refactored `product_committee.py` from 1970-line monolith to clean architecture with:
- Shared debate framework (`src/shared/debate/`)
- Committee module (`src/committee/`)
- Clear layer separation (Domain → Application → Infrastructure → CLI)

## Changes

### New Modules
- `src/shared/debate/domain/` - Pure domain entities
- `src/shared/debate/application/` - Use cases & ports
- `src/shared/debate/infrastructure/` - Adapters
- `src/committee/` - Product committee specific

### Refactored
- `product_committee.py` - Reduced from 1970 to ~200 lines

### Removed
- TPM self-reflection feature (per spec FR11)
- Duplicate sync/async execution paths
- ~1500 lines of duplicate/dead code

## Testing

- All existing tests pass
- Snapshot tests validate output equivalence
- Performance: parallel ≤60% of sequential
- Architecture compliance tests added

## Breaking Changes

None - 100% functional equivalence maintained.

## Docs

- `docs/product-committee-refactoring.md` - Complete feature documentation
- `README.md` - Updated architecture section
- Planning artifacts in `kitty-specs/017-*/`

Closes #[issue-number]
```

## Final Checklist

- [ ] All tests pass (pytest)
- [ ] Snapshot tests match
- [ ] Performance benchmarks pass
- [ ] Code quality metrics acceptable
- [ ] Architecture compliance verified
- [ ] Constitution requirements satisfied
- [ ] Documentation complete
- [ ] PR description ready
- [ ] No commented-out code
- [ ] No unused imports
- [ ] Code formatted (black, isort)
- [ ] Type checking passes (mypy)

## Rollback Plan

If validation fails:

1. **Tests failing**: Fix the specific failing code, don't revert entire WP
2. **Performance regression**: Profile and optimize hot paths
3. **Architecture violation**: Refactor to comply with layer boundaries
4. **Complete failure**: Use `git revert` to undo WP07 changes, fix issues, re-apply

## Files to Check

All files from previous work packages:
- `src/shared/debate/**/*.py`
- `src/committee/**/*.py`
- `product_committee.py`
- `docs/product-committee-refactoring.md`
- `README.md`
- `CLAUDE.md`

## Notes

- This is the FINAL work package - take time to be thorough
- Run complete validation before committing
- Document any deviations from success criteria
- Get code review before merging
- Tag release after merge

## Next Steps

After completing this work package:

1. **Create PR** with comprehensive description
2. **Request review** from maintainers
3. **Address feedback** if any
4. **Merge** after approval
5. **Tag release**: `git tag -a v0.17.0 -m "Product committee clean architecture refactoring"`
6. **Close feature**: Update meta.json with completed status
7. **Celebrate** - 🎉 Major refactoring complete!

## Feature Complete

Upon successful completion of WP09:
- Update `kitty-specs/017-product-committee-clean-architecture-refactoring/meta.json`:
  ```json
  {
    "status": "completed",
    "completed_at": "2025-02-18T..."
  }
  ```
- Mark feature as done in project tracking
- Archive planning artifacts if desired
