# Deb8flow: Product Committee Framework with Clean Architecture

**Deb8flow** is a multi-agent AI debate framework for analyzing product requirements. It simulates a virtual product committee by running structured debates between AI agents with different perspectives (TPM vs CPO/CFO/CTO/BDM).

Built with **Clean Architecture** principles for maintainability and testability.

---

## Quick Start

### 1. Install Poetry (if not already installed)

```bash
curl -sSL https://install.python-poetry.org | python3 -
```

### 2. Install Dependencies

```bash
poetry install
```

### 3. Configure Environment

Create a `.env` file with your API key:

```
OPENAI_API_KEY=your_openai_key_here
```

### 4. Run Product Committee

```bash
poetry run product-committee \
  --prd test_prd.txt \
  --question "What is the potential of this project?"
```

---

## Clean Architecture

```
src/
├── committee/                    # Product Committee bounded context
│   ├── application/              # Use cases
│   │   └── run_committee.py     # RunProductCommittee
│   ├── adapters/                 # Interface adapters
│   │   ├── cli.py               # Pydantic validation
│   │   └── reports/             # Report generators
│   └── domain/                   # Committee domain logic
│       └── entities.py          # Committee-specific entities
│
└── shared/debate/                # Shared Debate Kernel
    ├── domain/                   # Domain layer
    │   ├── value_objects.py     # RoomId, RunId, Speaker, etc.
    │   ├── entities.py          # DebateRoom, Verdict, etc.
    │   └── services.py          # Domain services
    ├── application/              # Application layer
    │   ├── ports.py             # Protocol interfaces
    │   └── use_cases/           # Use cases
    └── infrastructure/           # Infrastructure layer
        ├── executors/           # CLI executor
        └── storage/             # File storage
```

---

## Product Committee CLI

The `product_committee.py` runs four debate rooms to analyze a PRD from multiple perspectives.

### Basic Usage

```bash
# With Poetry
poetry run product-committee --prd ./test_prd.txt --question "заработает ли этот проект?"

# Or directly
python3 product_committee.py --prd ./test_prd.txt --question "заработает ли этот проект?"
```

### CLI Arguments

| Argument | Description |
|----------|-------------|
| `--prd <file>` | Path to PRD document (.docx or .txt) |
| `--question <text>` | Committee question |
| `--model <name>` | LLM model name |
| `--language <text>` | Language for output |
| `--max-retries <n>` | Max retry attempts (default: 2) |
| `--max-concurrency <n>` | Max parallel rooms (0-4, default: 2) |
| `--output-dir <path>` | Output directory (default: ./committee_output) |
| `--roles-dir <path>` | Roles directory (default: prompts/roles/) |
| `--run-id <id>` | Manual run identifier |
| `--verbose` | Verbose logging |
| `--quiet` | Quiet mode |

### Committee Rooms

1. **TPM vs CPO**: Product strategy, market fit, prioritization
2. **TPM vs CFO**: Business model, unit economics, monetization
3. **TPM vs CTO**: Technical feasibility, architecture, risks
4. **TPM vs BDM**: Market potential, competition, go-to-market

### Output Structure

```
committee_output/
└── RUN_YYYYMMDD_HHMMSS_slug/
    ├── TPM_vs_CPO_dialogue.json   # CPO debate dialogue
    ├── TPM_vs_CFO_dialogue.json   # CFO debate dialogue
    ├── TPM_vs_CTO_dialogue.json   # CTO debate dialogue
    ├── TPM_vs_BDM_dialogue.json   # BDM debate dialogue
    ├── final_report.md            # Human-readable summary
    ├── conclusion.md              # Executive conclusion
    └── metadata.json              # Run metadata
```

---

## Conclusion Generator

Standalone script to regenerate `conclusion.md` from existing `final_report.md`:

```bash
poetry run conclusion-results committee_output/RUN_XXX/final_report.md
```

---

## Testing

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=src

# Run specific test
poetry run pytest tests/unit/shared/debate/domain/test_value_objects.py
```

**Current Status**: 102 tests passing

---

## Dependencies

- Python 3.12+
- Poetry (dependency management)
- langgraph (agent workflows)
- langchain-openai (LLM integration)
- pydantic (validation)
- pytest (testing)
- rich (CLI formatting)

---

## License

MIT License
