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

**Option A: Using YAML config (recommended)**

Edit `config/debate_config.yaml` with your provider settings:

```yaml
llm:
  base_url: ""  # Empty for OpenAI, or set your provider URL
  model: "gpt-4o-mini"
  api_key: ""  # Or use OPENAI_API_KEY environment variable
  temperature: 0.8
```

See [docs/CONFIG_GUIDE.md](docs/CONFIG_GUIDE.md) for provider examples (OpenAI, DeepSeek, Zhipu AI, Ollama).

**Option B: Using environment variables**

```bash
export OPENAI_API_KEY=your_openai_key_here
```

### 4. Run Debates

```bash
# Product Committee (recommended for PRD analysis)
poetry run python main.py committee \
  --prd test_prd.txt \
  --question "What is the potential of this project?"

# Document-based Debate (for single topics)
poetry run python main.py debate \
  --text "GitHub is useful for developers" \
  --pro-prompt prompts/pro.txt \
  --con-prompt prompts/con.txt

# Generate Conclusion from existing results
poetry run python main.py conclusion \
  --run-dir ./committee_output/RUN_20260218_234755
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

The `main.py committee` command runs four debate rooms to analyze a PRD from multiple perspectives.

### Basic Usage

```bash
# With Poetry
poetry run python main.py committee --prd ./test_prd.txt --question "заработает ли этот проект?"

# Or directly
python main.py committee --prd ./test_prd.txt --question "заработает ли этот проект?"
```

### CLI Arguments

| Argument | Description |
|----------|-------------|
| `--prd <file>` | Path to PRD document (.docx or .txt) |
| `--question <text>` | Committee question |
| `--config <file>` | Path to YAML config file (default: config/debate_config.yaml) |
| `--model <name>` | LLM model name (overrides config) |
| `--base-url <url>` | API base URL (overrides config) |
| `--api-key <key>` | API key (overrides config) |
| `--temperature <n>` | Sampling temperature (overrides config) |
| `--language <text>` | Language for output |
| `--max-retries <n>` | Max retry attempts (default: 2) |
| `--max-concurrency <n>` | Max parallel rooms (0-4, default: 2) |
| `--output-dir <path>` | Output directory (default: ./committee_output) |
| `--roles-dir <path>` | Roles directory (default: prompts/roles/) |
| `--run-id <id>` | Manual run identifier |
| `--verbose` | Verbose logging |
| `--quiet` | Quiet mode |

### Configuration Priority

Settings are applied in this order (highest priority first):
1. CLI arguments
2. `DEBATE_*` environment variables
3. `OPENAI_*` environment variables
4. YAML config file (`config/debate_config.yaml`)
5. Built-in defaults

### Example Configurations

**OpenAI (default):**
```yaml
llm:
  base_url: ""
  model: "gpt-4o-mini"
```

**DeepSeek (via Requesty):**
```yaml
llm:
  base_url: "https://api.requesty.ai/v1"
  model: "deepseek-chat"
```

**Ollama (local):**
```yaml
llm:
  base_url: "http://localhost:11434/v1"
  model: "llama3"
```

See `config/examples/` for more configuration examples.

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

Regenerate `conclusion.md` from existing committee results:

```bash
poetry run python main.py conclusion --run-dir committee_output/RUN_XXX
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
