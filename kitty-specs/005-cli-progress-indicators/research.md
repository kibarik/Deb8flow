# Research: CLI Progress Indicators Implementation

**Feature**: 005-cli-progress-indicators
**Date**: 2025-02-14
**Phase**: 0 - Research & Technology Decisions

## Research Summary

This document consolidates research findings for implementing CLI progress indicators using tqdm with the existing LangGraph workflow.

---

## Topic 1: tqdm Integration with Async/LangGraph

### Findings

**tqdm in Async Contexts**:
- tqdm works seamlessly with async/await patterns
- Use `tqdm.asyncio` for async iteration patterns
- Progress bars update independently without blocking await points

**LangGraph Workflow Integration**:
- LangGraph nodes are async functions by default
- Progress can be tracked at node entry/exit points
- No built-in progress callbacks in LangGraph 0.3.x
- Best approach: Pass progress manager through state or context

**Rich + tqdm Compatibility**:
- Both libraries use terminal control codes
- Must ensure they don't interfere with each other
- Strategy: Use tqdm for progress, Rich for logging only
- Consider `tqdm.rich` integration for Rich-compatible progress bars

### Code Example

```python
from tqdm import tqdm
from tqdm.rich import tqdm as rich_tqdm

class ProgressManager:
    def __init__(self, level: ProgressLevel):
        self.level = level
        self.current_bar = None

    def start_step(self, name: str, total: int, current: int):
        if self.level == ProgressLevel.QUIET:
            return
        self.current_bar = rich_tqdm(
            total=total,
            desc=f"Step {current}: {name}",
            disable=self.level == ProgressLevel.QUIET
        )

    def update_progress(self, increment: int = 1):
        if self.current_bar:
            self.current_bar.update(increment)

    def complete_step(self):
        if self.current_bar:
            self.current_bar.close()
            self.current_bar = None
```

---

## Topic 2: Verbosity Flag Implementation

### Findings

**argparse Verbosity Patterns**:
```python
# Standard pattern using count action
parser.add_argument(
    "-v", "--verbose",
    action="count",
    default=0,
    help="Increase verbosity (can be used: -v, -vv)"
)

# Alternative: explicit verbosity levels
parser.add_argument(
    "--verbose",
    action="store_true",
    help="Enable detailed output"
)
parser.add_argument(
    "--quiet", "-q",
    action="store_true",
    help="Suppress non-critical output"
)
```

**Best Practice for This Project**:
- Use separate `--verbose` and `--quiet` flags as specified in requirements
- Implement priority: quiet > verbose > default
- Mutually exclusive flags (if both provided, quiet wins)

### Code Example

```python
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--verbose", action="store_true")
parser.add_argument("--quiet", "-q", action="store_true")

args = parser.parse_args()

# Determine verbosity level
if args.quiet:
    level = ProgressLevel.QUIET
elif args.verbose:
    level = ProgressLevel.VERBOSE
else:
    level = ProgressLevel.DEFAULT
```

---

## Topic 3: LangGraph Progress Hook Strategy

### Findings

**LangGraph Architecture**:
- Nodes receive state dict and return updated state dict
- No middleware/interceptor pattern in LangGraph 0.3.x
- State is the only shared context between nodes

**Integration Options Evaluated**:

| Option | Pros | Cons | Decision |
|--------|------|-------|----------|
| Pass progress through state | Simple, works with LangGraph model | Pollutes state with UI concerns | ❌ Not recommended |
| Global/singleton progress manager | Easy to implement | Makes testing harder, implicit dependency | ⚠️ Acceptable for CLI |
| Workflow wrapper with callbacks | Clean separation | Requires significant refactoring | ✅ Recommended |

**Recommended Approach**:
- Use dependency injection to pass ProgressManager to workflow
- Modify workflow.run() signature to accept optional progress_manager
- Pass progress_manager to state as a special key (e.g., `_progress_manager`)
- Nodes check for `_progress_manager` in state and use if present
- ProgressManager is not persisted in state (use underscore prefix convention)

### Code Example

```python
# In workflow
async def run(self, initial_state: dict = None, progress_manager: ProgressManager = None):
    if progress_manager:
        initial_state = initial_state or {}
        initial_state["_progress_manager"] = progress_manager

    workflow = self._initialize_workflow()
    graph = workflow.compile()
    return await graph.ainvoke(initial_state)

# In node
async def __call__(self, state: DebateState, config: RunnableConfig):
    progress = state.get("_progress_manager")
    if progress:
        progress.start_step("Generating pro arguments", total=1, current=1)

    # ... node logic ...

    if progress:
        progress.complete_step()

    return updated_state
```

---

## Decisions Made

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Progress library | tqdm (with tqdm.rich) | Lightweight, cross-platform, async-safe |
| Verbosity flags | Separate --verbose and --quiet flags | Matches spec requirements, clearer UX |
| Progress injection | Pass through state with underscore prefix | Works with LangGraph architecture, explicit |
| Progress display | Step-based progress bars | Matches spec "Step N/M: description" requirement |

---

## Alternatives Considered

### Alternative 1: rich.progress
- **Pros**: Already using rich, integrated ecosystem
- **Cons**: More complex API, heavier for simple progress bars
- **Rejected**: tqdm is simpler and sufficient for our needs

### Alternative 2: alive-progress
- **Pros**: Very fancy animations
- **Cons**: Additional dependency, overkill for CLI progress
- **Rejected**: Too feature-rich for our use case

### Alternative 3: Custom spinners only
- **Pros**: No new dependencies
- **Cons**: Reinventing the wheel, less feature-complete
- **Rejected**: tqdm is standard and well-tested

---

## Open Questions

**None** - All research topics resolved.

---

## Next Steps

Proceed to Phase 1 (Design & Contracts):
1. Create `data-model.md` with progress data structures
2. Create interface contracts in `contracts/`
3. Create `quickstart.md` for users
4. Run agent context update scripts
