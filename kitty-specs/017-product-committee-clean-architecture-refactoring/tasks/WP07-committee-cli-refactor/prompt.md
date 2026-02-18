# WP07: Product Committee CLI Refactoring

**Work Package**: 017-product-committee-clean-architecture-refactoring / WP07
**Status**: TODO
**Dependencies**: WP04, WP05, WP06

## Overview

Refactor `product_committee.py` to use the new clean architecture, reducing it from ~1970 lines to ~200 lines while preserving all functionality.

## Context

This is the MAIN EVENT - where everything comes together. The refactored CLI will:
1. Use Pydantic validation (WP06)
2. Invoke RunProductCommittee use case (WP04)
3. Use shared ports and adapters (WP02, WP03)
4. Generate reports via new generators (WP05)

## Implementation Requirements

### Refactored `product_committee.py`

```python
#!/usr/bin/env python3
"""
Product Committee Orchestrator

Simulates a virtual product committee by running four sequential debate rooms (TPM vs CPO/CFO/CTO/BDM)
using the Clean Architecture refactored system.

Usage:
    python product_committee.py --prd <path> --question <text> [--model <name>]
"""

from __future__ import annotations

import asyncio
import logging
import sys
from pathlib import Path

from src.committee.adapters.cli import parse_arguments, CommitteeCliInput
from src.committee.application.run_committee import RunProductCommittee
from src.committee.adapters.reports import CommitteeReportGenerator
from src.shared.debate.infrastructure.executors.cli_executor import CliDebateExecutor
from src.shared.debate.infrastructure.storage.local_storage import LocalFileStorage

logger = logging.getLogger(__name__)


def setup_logging(verbose: bool = False, quiet: bool = False) -> None:
    """Configure logging based on verbosity flags."""
    if quiet:
        logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")
    elif verbose:
        logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")
    else:
        logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


async def main_async() -> int:
    """Main async entry point."""
    # Parse arguments
    args = parse_arguments()

    # Validate input
    try:
        cli_input = CommitteeCliInput.from_args(args)
    except Exception as e:
        logger.error(f"Validation error: {e}")
        return 1

    # Setup logging
    setup_logging(verbose=cli_input.verbose, quiet=cli_input.quiet)

    logger.info("Product Committee Orchestrator starting...")
    logger.info(f"PRD: {cli_input.prd}")
    logger.info(f"Question: {cli_input.question}")

    # Create adapters
    executor = CliDebateExecutor()
    generator = CommitteeReportGenerator()
    storage = LocalFileStorage()

    # Create use case
    use_case = RunProductCommittee(executor, generator, storage)

    # Execute committee
    try:
        result = await use_case.execute(
            prd_path=cli_input.prd,
            question=cli_input.question,
            roles_dir=cli_input.roles_dir,
            model=cli_input.model,
            language=cli_input.language,
            max_retries=cli_input.max_retries,
            max_concurrency=cli_input.max_concurrency,
            output_dir=Path(cli_input.output_dir),
            manual_run_id=cli_input.run_id
        )

        logger.info(f"Product Committee Orchestrator completed successfully!")
        logger.info(f"Artifacts saved to: {Path(cli_input.output_dir) / result.run_id.value}")
        logger.info(f"TPM wins: {result.tpm_wins}/{len(result.successful_rooms)}")

        # Exit with error if any rooms failed
        if result.failed_rooms:
            logger.warning(f"Some rooms failed: {len(result.failed_rooms)}")
            return 1

        return 0

    except Exception as e:
        logger.error(f"Committee execution failed: {e}")
        return 1


def main() -> int:
    """Main entry point."""
    return asyncio.run(main_async())


if __name__ == "__main__":
    sys.exit(main())
```

## Migration Checklist

### Remove from Old Code
- [ ] Remove `run_debate_room_with_retry()` function (replaced by CliDebateExecutor)
- [ ] Remove `run_debate_room_async()` function (consolidated into single async path)
- [ ] Remove `_run_all_rooms_sequential()` function (logic in RunProductCommittee)
- [ ] Remove `run_all_rooms_parallel()` function (logic in RunProductCommittee)
- [ ] Remove `run_reflection_subprocess()` function (TPM reflection removed per spec)
- [ ] Remove duplicate sync/async execution paths
- [ ] Remove intermediate report retry logic (moved to infrastructure)
- [ ] Remove report generation functions (moved to adapters/reports/)

### Preserve Functionality
- [ ] All CLI arguments work identically
- [ ] PRD file reading (.docx and .txt with encoding support)
- [ ] Role prompt validation
- [ ] Parallel execution with semaphore control
- [ ] Intermediate report saving
- [ ] Error categorization and messages
- [ ] Output file structure unchanged

### Validation Tests

```bash
# Test basic functionality
python3 product_committee.py \
  --prd ./test_prd.txt \
  --question 'заработает ли этот проект 100 млн за 2 дня' \
  --max-concurrency 0 \
  --language 'русский кратко, в формате буллетлистов'

# Test validation
python3 product_committee.py --prd nonexistent.txt --question "test"
# Should error with clear message

python3 product_committee.py --prd ./test_prd.txt --question ""
# Should error with clear message

# Test edge cases
python3 product_committee.py --prd ./test_prd.txt --question "test" --max-concurrency 1
# Sequential execution

python3 product_committee.py --prd ./test_prd.txt --question "test" --max-concurrency 0
# Parallel execution (all rooms at once)
```

## Snapshot Testing

Ensure output matches old implementation exactly:

```bash
# Generate snapshots from old implementation first
OLD_COMMIT=<commit_before_refactoring>
git checkout $OLD_COMMIT
python3 product_committee.py --prd ./test_prd.txt --question "test question" > old_output.txt
# Save committee_output/{run-id}/ files as snapshots

# Test new implementation
git checkout main
python3 product_committee.py --prd ./test_prd.txt --question "test question" > new_output.txt
diff old_output.txt new_output.txt  # Should be identical

# Compare report files
diff committee_output/{old_run_id}/final_report.md committee_output/{new_run_id}/final_report.md
diff committee_output/{old_run_id}/conclusion.md committee_output/{new_run_id}/conclusion.md
```

## Performance Benchmark

Verify parallel execution performance:

```python
# tests/performance/test_concurrent_execution.py
import time
import asyncio
from src.committee.application.run_committee import RunProductCommittee

async def test_parallel_faster_than_sequential():
    """Verify parallel execution completes in <=60% of sequential time."""

    # Sequential
    start = time.time()
    sequential = await run_committee(max_concurrency=1)
    sequential_time = time.time() - start

    # Parallel
    start = time.time()
    parallel = await run_committee(max_concurrency=0)
    parallel_time = time.time() - start

    # Parallel should be <= 60% of sequential
    assert parallel_time <= (sequential_time * 0.6), \
        f"Parallel took {parallel_time}s, sequential took {sequential_time}s"
```

## Acceptance Criteria

- [ ] All existing CLI arguments work identically
- [ ] All existing tests pass without modification
- [ ] Snapshot tests match old implementation exactly
- [ ] Code reduced to <500 lines
- [ ] Zero duplicate code blocks >10 lines
- [ ] Performance: parallel <= 60% of sequential time
- [ ] TPM reflection feature removed
- [ ] Output file structure unchanged
- [ ] All error messages preserved

## Files to Modify

1. `product_committee.py` - Complete rewrite using new architecture

## Files to Preserve (Don't Modify)

- `document_debate_cli.py` - Keep as-is (used by CliDebateExecutor)
- `tests/test_product_committee.py` - Existing tests must pass unchanged

## Testing Commands

```bash
# Run all existing tests
pytest tests/test_product_committee.py

# Run snapshot tests
pytest tests/snapshots/test_committee_output/

# Performance benchmark
pytest tests/performance/test_concurrent_execution.py

# Full test suite
pytest
```

## Notes

- This is the BIG CHANGE - all previous work packages come together here
- Test thoroughly before committing
- Keep old code commented out temporarily for comparison
- Document any behavioral differences (there should be NONE)
- Use git bisect if bugs appear to find breaking change

## Rollback Strategy

If tests fail:
1. Keep old `product_committee.py` as `product_committee.py.old`
2. Run side-by-side comparisons
3. Use git to identify specific breaking change
4. Fix and re-test until parity achieved

## Next Steps

After completing this work package:
1. Run FULL test suite: `pytest`
2. Verify snapshot tests pass
3. Run performance benchmarks
4. Compare output with old implementation
5. Test all CLI argument combinations
6. Document any differences
7. Commit with message "feat: refactor product_committee.py to clean architecture (WP07)"
8. Create PR for review
9. Move to WP08 (Documentation)
