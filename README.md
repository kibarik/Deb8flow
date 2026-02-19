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

## Prompt Management

Deb8flow uses file-based prompts for easy customization and debate quality enhancement.

### Prompt Location

All prompts are stored in `src/prompts/`:
- `debate/stages/` - Individual stage prompts (opening, rebuttal, counter, final)
- `debate/judge/` - Judge evaluation prompts
- `debate/context/` - Context templates
- `debate/modes/` - Mode-specific prompts (simple, standard)
- `analysis/` - Takeaway analysis prompts
- `roles/` - Agent role descriptions (TPM, CPO, CFO, CTO, BDM)

### Editing Prompts

1. Navigate to `src/prompts/`
2. Open the relevant `.md` file
3. Edit the prompt content
4. Run debates - changes take effect immediately

### Template Variables

Prompts support variables using `{variable}` syntax:
- `{question}` - Debate question
- `{topic}` - PRD topic (excerpt)
- `{prd_content}` - Full PRD content
- `{language}` - Output language instruction
- `{recent_context}` - Recent debate messages
- `{pro_prompt}` - PRO agent role
- `{con_prompt}` - CON agent role
- `{dialogue_summary}` - Debate summary for analysis
- `{verdict_explanation}` - Judge's verdict explanation
- `{winner}` - Debate winner
- `{min_takeaways}` - Minimum takeaways to generate
- `{max_takeaways}` - Maximum takeaways to generate

### Debate Modes

Two debate execution modes are available:

**Simple Mode** (`debate.modes.simple`):
- Single LLM call for entire debate
- Faster and cheaper
- Good for quick iterations

**Standard Mode** (`debate.modes.standard`):
- 9 separate LLM calls (8 stages + judge)
- Better quality and depth
- Each stage builds on full conversation history

Configure mode in `config/debate_config.yaml`:
```yaml
debate:
  mode: "standard"  # or "simple"
```

### Migration

If you have prompts in the old `config/prompts/` location:
```bash
python scripts/migrate_prompts.py
```

The system will automatically fall back to old locations if needed.

See [PROMPTS.md](PROMPTS.md) for detailed prompt management guide.

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
| `--roles-dir <path>` | Roles directory (fallback if agents not configured) |
| `--run-id <id>` | Manual run identifier |
| `--verbose` | Verbose logging |
| `--quiet` | Quiet mode |

### Agent Configuration

**NEW**: Agents are now configured via `debate_config.yaml` under the `agents` section:

```yaml
agents:
  # Main agent (PRO position) - REQUIRED
  main:
    name: "TPM"
    prompt: "config/prompts/roles/tpm.txt"

  # Opponents (CON position) - OPTIONAL
  opponents:
    - name: "CPO"
      prompt: "config/prompts/roles/cpo.txt"
    - name: "CFO"
      prompt: "config/prompts/roles/cfo.txt"
    - name: "CTO"
      prompt: "config/prompts/roles/cto.txt"
    - name: "BDM"
      prompt: "config/prompts/roles/bdm.txt"
```

**Benefits:**
- Configure any number of opponents
- Custom agent names and prompts
- No code changes needed for different debate scenarios

**Fallback:** If `agents` section is not configured, the system falls back to the `--roles-dir` parameter and looks for standard role files (`tpm.txt`, `cpo.txt`, etc.).

See `config/examples/` for configuration examples:
- `minimal.yaml` - Single opponent for quick debates
- `custom_agents.yaml` - Custom roles (Finance Director, Security Officer, etc.)
- `russian.yaml` - Russian-language configuration

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

Debate rooms are created dynamically based on your agent configuration. Each opponent debates against the main agent in a separate room.

**Default configuration (TPM vs CPO/CFO/CTO/BDM):**
1. **TPM vs CPO**: Product strategy, market fit, prioritization
2. **TPM vs CFO**: Business model, unit economics, monetization
3. **TPM vs CTO**: Technical feasibility, architecture, risks
4. **TPM vs BDM**: Market potential, competition, go-to-market

**Custom configurations**: You can define any agents in your config. For example, with `config/examples/custom_agents.yaml`:
- PRODUCT_OWNER vs FINANCE_DIRECTOR
- PRODUCT_OWNER vs LEAD_ARCHITECT
- PRODUCT_OWNER vs SECURITY_OFFICER
- PRODUCT_OWNER vs UX_RESEARCHER
- PRODUCT_OWNER vs LEGAL_COUNSEL

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
