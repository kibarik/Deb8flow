# API Reference

## PromptLoader Module

### Classes

#### `PromptLoader`

Service for loading, caching, and rendering prompt templates.

**Location:** `src/shared/debate/application/prompt_loader.py`

```python
from shared.debate.application.prompt_loader import PromptLoader
from shared.config.models import PromptsConfig
from pathlib import Path

# Initialize with configuration
config = PromptsConfig(
    stages={
        "opening_pro": "src/prompts/debate/stages/opening_pro.md",
        # ...
    },
    judge="src/prompts/debate/judge/verdict.md",
    context="src/prompts/debate/context/debate_context.md"
)

prompt_loader = PromptLoader(config, base_path=Path("src"))
```

**Methods:**

| Method | Description | Returns |
|--------|-------------|---------|
| `load(prompt_id: str) -> str` | Load a prompt from cache or file | Prompt content |
| `load_with_context(prompt_id: str, context: PromptContext) -> str` | Load and render with variables | Rendered prompt |
| `validate(prompt_id: str) -> ValidationResult` | Validate prompt file | Validation result |
| `reload() -> None` | Clear cache and reload all prompts | None |
| `get_cached_prompt_ids() -> List[str]` | Get list of cached prompt IDs | List of IDs |

**Prompt IDs:**

- `debate.stages.opening_pro` - PRO opening statement
- `debate.stages.opening_con` - CON opening statement
- `debate.stages.rebuttal_pro` - PRO rebuttal
- `debate.stages.rebuttal_con` - CON rebuttal
- `debate.stages.counter_pro` - PRO counter-argument
- `debate.stages.counter_con` - CON counter-argument
- `debate.stages.final_pro` - PRO final argument
- `debate.stages.final_con` - CON final argument
- `debate.judge` - Judge verdict
- `debate.context` - Debate context template
- `debate.modes.simple` - Simple mode debate template
- `analysis.system` - Analyst system prompt
- `analysis.takeaway` - Takeaway generation template

---

#### `PromptContext`

Dataclass for template variable substitution.

```python
from shared.debate.application.prompt_loader import PromptContext

context = PromptContext(
    question="Should we build this feature?",
    topic="Product Feature X description...",
    prd_content="Full PRD text...",
    language="You must conduct the debate in ENGLISH.",
    recent_context="Previous debate messages...",
    min_takeaways=3,
    max_takeaways=10
)
```

**Fields:**

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `question` | str | `""` | Debate question |
| `topic` | str | `""` | PRD topic excerpt |
| `prd_content` | str | `""` | Full PRD content |
| `language` | str | `"en"` | Output language instruction |
| `recent_context` | str | `""` | Recent debate messages |
| `pro_prompt` | str | `""` | PRO role description |
| `con_prompt` | str | `""` | CON role description |
| `dialogue_summary` | str | `""` | Combined dialogue text |
| `verdict_explanation` | str | `""` | Judge's verdict reasoning |
| `winner` | str | `""` | Debate winner |
| `min_takeaways` | int | `3` | Minimum takeaways |
| `max_takeaways` | int | `15` | Maximum takeaways |

**Methods:**

| Method | Description |
|--------|-------------|
| `to_dict() -> Dict[str, Any]` | Convert to dictionary for template rendering |

---

#### `ValidationResult`

Result of prompt validation.

```python
from shared.debate.application.prompt_loader import ValidationResult

result = ValidationResult(
    prompt_id="debate.judge",
    is_valid=True,
    errors=[],
    missing_variables=[]
)

if not result.is_valid:
    for error in result.errors:
        print(f"Error: {error}")
```

**Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `prompt_id` | str | ID of the validated prompt |
| `is_valid` | bool | Whether validation passed |
| `errors` | List[str] | List of validation errors |
| `missing_variables` | List[str] | Required variables not found in template |

---

### Factory Function

#### `create_prompt_loader()`

Convenience function to create PromptLoader from configuration.

```python
from shared.debate.application.prompt_loader import create_prompt_loader
from shared.config import load_config

config = load_config()
prompt_loader = create_prompt_loader(config.prompts)
```

---

## Debate Orchestrators

### `SimpleDebateOrchestrator`

Single-call debate orchestrator (faster, simpler).

**Location:** `src/shared/debate/infrastructure/llm/debate_orchestrator.py`

```python
from shared.debate.infrastructure.llm import SimpleDebateOrchestrator
from shared.debate.application.prompt_loader import PromptLoader

orchestrator = SimpleDebateOrchestrator(
    prompt_loader=PromptLoader(config),
    model="gpt-4o-mini",
    temperature=0.8,
    language="en"
)

dialogue, winner = await orchestrator.execute_debate(
    topic="Product Feature X",
    pro_prompt="You are the PRO debater...",
    con_prompt="You are the CON debater...",
    question="Should we build this?",
    prd_content="Full PRD text..."
)
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `prompt_loader` | PromptLoader | `None` | Prompt loader instance |
| `model` | str | `"gpt-4o"` | LLM model name |
| `temperature` | float | `0.8` | Sampling temperature |
| `max_tokens` | int | `1500` | Maximum tokens per response |
| `api_key` | str | `None` | OpenAI API key |
| `base_url` | str | `None` | Custom API base URL |
| `language` | str | `"en"` | Output language |

---

### `StandardDebateOrchestrator`

Multi-turn debate orchestrator (higher quality, slower).

**Location:** `src/shared/debate/infrastructure/llm/standard_orchestrator.py`

```python
from shared.debate.infrastructure.llm import StandardDebateOrchestrator

orchestrator = StandardDebateOrchestrator(
    prompt_loader=PromptLoader(config),
    model="gpt-4o",
    temperature=0.7,
    max_tokens=1200,
    language="en"
)

dialogue, winner = await orchestrator.execute_debate(
    topic="Product Feature X",
    pro_prompt="You are the PRO debater...",
    con_prompt="You are the CON debater...",
    question="Should we build this?",
    prd_content="Full PRD text..."
)
```

**Stages executed:**
1. Opening statements (PRO, CON)
2. Rebuttals (CON, PRO)
3. Counter-arguments (PRO, CON)
4. Final arguments (PRO, CON)
5. Judge verdict

---

### `DebateOrchestratorFactory`

Factory for creating orchestrators based on debate mode.

**Location:** `src/shared/debate/infrastructure/llm/factory.py`

```python
from shared.debate.infrastructure.llm import create_orchestrator, DebateMode
from shared.debate.application.prompt_loader import PromptLoader

orchestrator = create_orchestrator(
    mode=DebateMode.STANDARD,  # or DebateMode.SIMPLE
    prompt_loader=PromptLoader(config),
    model="gpt-4o",
    temperature=0.7
)
```

---

## Configuration Models

### `PromptsConfig`

Configuration for prompt file paths.

**Location:** `src/shared/config/models.py`

```python
from shared.config.models import PromptsConfig

config = PromptsConfig(
    stages={
        "opening_pro": "src/prompts/debate/stages/opening_pro.md",
        "opening_con": "src/prompts/debate/stages/opening_con.md",
        # ... all 8 stages required
    },
    judge="src/prompts/debate/judge/verdict.md",
    context="src/prompts/debate/context/debate_context.md",
    analysis={
        "system": "src/prompts/analysis/system_prompt.md",
        "takeaway": "src/prompts/analysis/takeaway_analysis.md"
    },
    roles={
        "tpm": "src/prompts/roles/tpm.md",
        # ... other roles
    }
)
```

**Validation:**
- All 8 stage prompts must be present
- `judge` and `context` paths must be non-empty

---

### `DebateModeConfig`

Configuration for debate execution mode.

```python
from shared.config.models import DebateModeConfig

config = DebateModeConfig(
    mode="standard",  # or "simple"
    max_retries=2,
    max_concurrency=0,
    language="en"
)
```

**Fields:**

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `mode` | str | `"standard"` | Debate mode: "standard" or "simple" |
| `max_retries` | int | `2` | Maximum retry attempts (0-10) |
| `max_concurrency` | int | `0` | Max parallel rooms (0 = unlimited) |
| `language` | str | `"en"` | Output language |

**Validation:**
- `mode` must be "standard" or "simple"
- `max_retries` must be between 0 and 10

---

## Domain Entities

### `DebateMode`

Enum for debate execution modes.

**Location:** `src/shared/debate/domain/entities.py`

```python
from shared.debate.domain.entities import DebateMode

mode = DebateMode.STANDARD  # or DebateMode.SIMPLE

if mode.is_standard():
    print("Using multi-turn mode")

# Parse from string
mode = DebateMode.from_string("simple")  # Validates input
```

**Values:**
- `DebateMode.STANDARD` - Multi-turn debate (9 LLM calls)
- `DebateMode.SIMPLE` - Single-call debate (1 LLM call)

**Methods:**
- `from_string(value: str) -> DebateMode` - Parse string with validation
- `is_standard() -> bool` - Check if standard mode
- `is_simple() -> bool` - Check if simple mode

---

## CLI Usage

### Document Debate CLI

**Script:** `scripts/document_debate_cli.py`

```bash
python scripts/document_debate_cli.py \
  --text "Debate topic text" \
  --pro-prompt config/prompts/roles/tpm.txt \
  --con-prompt config/prompts/roles/cpo.txt \
  --model gpt-4o-mini \
  --language en \
  --json-output debate_results.json
```

**Environment Variables:**
- `OPENAI_API_KEY` - OpenAI API key
- `DEBATE_API_KEY` - Alternative API key variable
- `DEBATE_BASE_URL` - Custom API base URL
- `DEBATE_MODEL` - Default model
- `DEBATE_TEMPERATURE` - Default temperature
- `DEBATE_MODE` - Debate mode (standard/simple)

---

### Product Committee CLI

**Command:** `main.py committee`

Run multi-agent product committee with multiple debate rooms.

```bash
# Basic committee run
python main.py committee \
  --prd examples/sample_prd.txt \
  --question "What is the potential of this project?"

# With custom output directory
python main.py committee \
  --prd examples/sample_prd.txt \
  --question "Should we build this?" \
  --output-dir ./my_results
```

**Arguments:**

| Argument | Type | Description |
|----------|------|-------------|
| `--prd <file>` | required | Path to PRD document (.docx or .txt) |
| `--question <text>` | required | Committee question |
| `--config <file>` | optional | Path to YAML config file |
| `--model <name>` | optional | LLM model name (overrides config) |
| `--base-url <url>` | optional | API base URL (overrides config) |
| `--api-key <key>` | optional | API key (overrides config) |
| `--temperature <n>` | optional | Sampling temperature (overrides config) |
| `--language <text>` | optional | Language for output |
| `--max-retries <n>` | optional | Max retry attempts (default: 2) |
| `--max-concurrency <n>` | optional | Max parallel rooms 0-4 (default: 2) |
| `--output-dir <path>` | optional | Output directory (default: ./committee_output) |
| `--roles-dir <path>` | optional | Roles directory fallback |
| `--run-id <id>` | optional | Manual run identifier |
| `--verbose` | flag | Enable verbose logging |
| `--quiet` | flag | Enable quiet mode |

---

### Conclusion CLI

**Command:** `main.py conclusion`

Generate conclusion from existing committee results.

```bash
python main.py conclusion \
  --run-dir ./committee_output/RUN_20260218_234755

# With custom prompt
python main.py conclusion \
  --run-dir ./committee_output/RUN_20260218_234755 \
  --prompt /path/to/custom_prompt.txt
```

**Arguments:**

| Argument | Type | Description |
|----------|------|-------------|
| `--run-dir <path>` | required | Path to committee run directory |
| `--prompt <file>` | optional | Path to custom prompt file |

---

## Examples

### Loading a Custom Prompt

```python
from shared.debate.application.prompt_loader import PromptLoader, PromptContext
from shared.config import load_config

config = load_config()
loader = PromptLoader(config.prompts)

# Load with custom context
context = PromptContext(
    question="What is the market potential?",
    topic="SaaS platform for SMEs",
    prd_content="The product targets small businesses...",
    language="You must conduct the debate in RUSSIAN."
)

prompt = loader.load_with_context("debate.context", context)
print(prompt)
```

### Creating a Custom Orchestrator

```python
from shared.debate.infrastructure.llm import create_orchestrator, DebateMode
from shared.debate.application.prompt_loader import PromptLoader
from shared.config import load_config

config = load_config()
loader = PromptLoader(config.prompts)

# Create orchestrator based on config mode
mode = DebateMode.from_string(config.debate.mode)
orchestrator = create_orchestrator(
    mode=mode,
    prompt_loader=loader,
    model=config.llm.model,
    temperature=config.llm.temperature
)

# Execute debate
dialogue, winner = await orchestrator.execute_debate(...)
```

### Validating Prompts

```python
from shared.debate.application.prompt_loader import PromptLoader
from shared.config import load_config

config = load_config()
loader = PromptLoader(config.prompts)

# Validate all stage prompts
for stage in ["opening_pro", "opening_con", "rebuttal_pro", "rebuttal_con",
              "counter_pro", "counter_con", "final_pro", "final_con"]:
    prompt_id = f"debate.stages.{stage}"
    result = loader.validate(prompt_id)

    if not result.is_valid:
        print(f"{prompt_id}: FAILED")
        for error in result.errors:
            print(f"  - {error}")
    else:
        print(f"{prompt_id}: OK")
```

---

## Error Handling

### Common Exceptions

| Exception | Cause | Solution |
|-----------|-------|----------|
| `FileNotFoundError` | Prompt file doesn't exist | Check file paths in config |
| `ValueError` (empty prompt) | Prompt file is empty | Add content to prompt file |
| `ValueError` (missing variable) | Required variable not provided | Add to PromptContext |
| `ValueError` (invalid mode) | Invalid debate mode | Use "standard" or "simple" |

### Example Error Handling

```python
from shared.debate.application.prompt_loader import PromptLoader, PromptContext
from shared.config import load_config

config = load_config()

try:
    loader = PromptLoader(config.prompts)
    prompt = loader.load_with_context(
        "debate.judge",
        PromptContext(question="Should we proceed?", recent_context="...")
    )
except FileNotFoundError as e:
    print(f"Prompt file not found: {e}")
    # Check file paths in config/debate_config.yaml
except ValueError as e:
    print(f"Invalid prompt configuration: {e}")
    # Check prompt file has content and variables are provided
```

---

## See Also

- [Prompt Management Guide](prompt-management.md) - System overview
- [PROMPTS.md](../PROMPTS.md) - Comprehensive prompt editing guide
- [README.md](../README.md) - Project quick start
