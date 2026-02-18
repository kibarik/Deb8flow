---
work_package_id: "WP04"
title: "Committee Domain and Use Cases"
lane: "done"
dependencies: ["WP01", "WP02"]
base_branch: main
created_at: '2025-02-18T17:00:00Z'
subtasks:
  - "T001: Create CommitteeRun, CommitteeMetadata, CommitteeReport entities"
  - "T002: Create RunProductCommittee use case"
  - "T003: Add business logic properties (tpm_wins, successful_rooms, etc.)"
  - "T004: Write unit tests for committee domain"
shell_pid: ""
review_status: "approved"
reviewed_by: "ALeks ishmanov"
history:
  - timestamp: "2025-02-18T17:00:00Z"
    lane: "for_review"
    agent: "claude"
    action: "Implementation complete, 5 tests passing"
---

# WP04: Committee Domain and Use Cases

## Implementation Status: ✅ COMPLETE

### Files Created
- `src/committee/domain/__init__.py`
- `src/committee/domain/entities.py` - CommitteeRun, CommitteeMetadata, CommitteeReport
- `src/committee/application/__init__.py`
- `src/committee/application/run_committee.py` - RunProductCommittee use case

### Test Coverage
- `tests/unit/committee/domain/test_entities.py` - 5 tests
- **Total: 5 tests, all passing**

### Key Features Implemented

#### Committee Domain Entities (entities.py)
```python
@dataclass
class CommitteeRun:
    """Represents a complete product committee run."""

    run_id: RunId
    question: str
    prd_path: str
    max_retries: int
    max_concurrency: int
    rooms: List[DebateRoom]
    start_time: str
    end_time: Optional[str] = None

    @property
    def tpm_wins(self) -> int:
        """Count of rooms where TPM (PRO) won."""

    @property
    def opponent_wins(self) -> int:
        """Count of rooms where opponents (CON) won."""

    @property
    def successful_rooms(self) -> List[DebateRoom]:
        """Filter rooms with successful status."""

    @property
    def failed_rooms(self) -> List[DebateRoom]:
        """Filter rooms with failed status."""

    def mark_complete(self, end_time: Optional[str] = None) -> None:
        """Mark the committee run as complete."""

@dataclass
class CommitteeMetadata:
    """Metadata for committee run."""

    run_id: str
    prd_path: str
    question: str
    model: Optional[str]
    start_time: str
    end_time: Optional[str] = None
    room_statuses: Dict[str, str] = field(default_factory=dict)
    # ... more fields

    @classmethod
    def from_run(cls, run: CommitteeRun) -> "CommitteeMetadata":
        """Create metadata from CommitteeRun."""

    def to_json(self) -> str:
        """Serialize metadata to JSON."""

@dataclass
class CommitteeReport:
    """Generated markdown report for committee run."""

    content: str
    output_path: Path

    def save(self) -> None:
        """Save report to file."""
```

#### RunProductCommittee Use Case (run_committee.py)
```python
class RunProductCommittee:
    """Orchestrates 4 debate rooms with concurrency control."""

    def __init__(
        self,
        executor: DebateExecutor,
        generator: ReportGenerator,
        storage: FileStorage
    ):
        self.executor = executor
        self.generator = generator
        self.storage = storage

    async def execute(
        self,
        prd_path: str,
        question: str,
        roles_dir: str = "prompts/roles/",
        model: Optional[str] = None,
        language: Optional[str] = None,
        max_retries: int = 2,
        max_concurrency: int = 2,
        run_id: Optional[str] = None,
        output_dir: str = "./committee_output"
    ) -> CommitteeRun:
        """Execute product committee with 4 debate rooms."""
```

### Test Results
```
tests/unit/committee/domain/test_entities.py::test_committee_run_tpm_wins PASSED
tests/unit/committee/domain/test_entities.py::test_committee_run_validation PASSED
tests/unit/committee/domain/test_entities.py::test_committee_metadata_from_run PASSED
tests/unit/committee/domain/test_entities.py::test_committee_metadata_to_json PASSED
tests/unit/committee/domain/test_entities.py::test_committee_run_successful_and_failed_rooms PASSED

============================== 5 passed in 0.02s ===============================
```

### Design Principles Applied
- ✅ Domain Logic: Business rules in domain entities (tpm_wins, successful_rooms)
- ✅ Dependency Injection: Uses injected executor, generator, storage
- ✅ Async-First: All operations are async
- ✅ Concurrency Control: Semaphore-based parallel/sequential execution

### Commit
- `4bc0546` - feat: Complete WP03, WP05, WP06 - Infrastructure, Reports, and CLI validation
  (includes WP04 files from earlier commits)

## Activity Log

- 2026-02-18T21:29:54Z – unknown – lane=done – Review passed: 5 tests passing, complete committee domain (CommitteeRun, CommitteeMetadata, CommitteeReport, RunProductCommittee use case)
