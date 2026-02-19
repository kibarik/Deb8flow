# Prompt Management System

## Overview

Deb8flow uses a file-based prompt management system that allows easy customization of debate behavior without modifying code. All prompts are stored as Markdown files in the `src/prompts/` directory and loaded dynamically using the `PromptLoader` service.

## Architecture

```
src/prompts/
├── debate/
│   ├── stages/          # Individual debate stage prompts
│   │   ├── opening_pro.md
│   │   ├── opening_con.md
│   │   ├── rebuttal_pro.md
│   │   ├── rebuttal_con.md
│   │   ├── counter_pro.md
│   │   ├── counter_con.md
│   │   ├── final_pro.md
│   │   └── final_con.md
│   ├── judge/           # Judge evaluation prompts
│   │   └── verdict.md
│   ├── context/         # Shared context templates
│   │   └── debate_context.md
│   └── modes/           # Mode-specific prompts
│       └── simple.md
├── analysis/            # Takeaway analysis prompts
│   ├── system_prompt.md
│   └── takeaway_analysis.md
└── roles/               # Agent role descriptions
    ├── tpm.md
    ├── cpo.md
    ├── cfo.md
    ├── cto.md
    └── bdm.md
```

## PromptLoader Service

The `PromptLoader` service (`src/shared/debate/application/prompt_loader.py`) provides:

- **Loading**: Loads prompts from files with validation
- **Caching**: Thread-safe in-memory caching for performance
- **Rendering**: Template variable substitution using `{variable}` syntax
- **Validation**: Checks for missing files, empty content, and required variables

### Basic Usage

```python
from shared.debate.application.prompt_loader import PromptLoader, PromptContext
from shared.config import load_config

# Load configuration
config = load_config()

# Create PromptLoader
prompt_loader = PromptLoader(config.prompts)

# Load a prompt
prompt = prompt_loader.load("debate.judge")

# Load with context variables
rendered = prompt_loader.load_with_context(
    "debate.context",
    PromptContext(
        question="Should we build this?",
        topic="Product Feature X",
        prd_content="Full PRD text...",
        language="You must conduct the debate in ENGLISH."
    )
)
```

## Template Variables

Prompts support dynamic content substitution using these variables:

| Variable | Description | Example |
|----------|-------------|---------|
| `{question}` | Debate question | "Should we build this feature?" |
| `{topic}` | PRD excerpt (truncated) | First 500-800 chars of PRD |
| `{prd_content}` | Full PRD content | Complete PRD text |
| `{language}` | Language instruction | "You must conduct the debate in ENGLISH." |
| `{recent_context}` | Recent debate messages | Last exchanges for context |
| `{pro_prompt}` | PRO role description | TPM agent prompt |
| `{con_prompt}` | CON role description | Opponent agent prompt |
| `{dialogue_summary}` | Debate summary for analysis | Combined dialogue text |
| `{verdict_explanation}` | Judge's verdict reasoning | Winner explanation |
| `{winner}` | Debate winner | "PRO" or "CON" |
| `{min_takeaways}` | Minimum takeaways to generate | 3 |
| `{max_takeaways}` | Maximum takeaways to generate | 15 |

## Configuration

Prompts are configured in `config/debate_config.yaml`:

```yaml
prompts:
  stages:
    opening_pro: "src/prompts/debate/stages/opening_pro.md"
    opening_con: "src/prompts/debate/stages/opening_con.md"
    # ... other stages

  judge: "src/prompts/debate/judge/verdict.md"
  context: "src/prompts/debate/context/debate_context.md"

  analysis:
    system: "src/prompts/analysis/system_prompt.md"
    takeaway: "src/prompts/analysis/takeaway_analysis.md"

  roles:
    tpm: "src/prompts/roles/tpm.md"
    cpo: "src/prompts/roles/cpo.md"
    # ... other roles

debate:
  mode: "standard"  # or "simple"
```

## Debate Modes

### Standard Mode (Multi-turn)

- **9 separate LLM calls** (8 stages + judge)
- Each stage builds on full conversation history
- Better quality and depth
- Slower and more expensive

### Simple Mode (Single-call)

- **1 LLM call** for entire debate
- Faster and cheaper
- Good for quick iterations

Switch modes in `config/debate_config.yaml`:
```yaml
debate:
  mode: "standard"  # or "simple"
```

## Customizing Prompts

### Editing Existing Prompts

1. Navigate to `src/prompts/`
2. Open the relevant `.md` file
3. Edit the prompt content
4. Save the file
5. Run debates - changes take effect immediately

### Adding a New Debate Stage

1. Create prompt file: `src/prompts/debate/stages/clarification_pro.md`
2. Add to config: `config/debate_config.yaml`
3. Update orchestrator to use the new stage
4. Test with sample debates

### Prompt Best Practices

- **Be specific** about word counts and response lengths
- **Require evidence-based arguments** referencing PRD content
- **Emphasize professional, constructive tone**
- **Include examples** in prompts where helpful
- **Test changes** with sample debates before committing
- **Keep prompts focused** and concise

## Backward Compatibility

The system automatically falls back to old prompt paths if new ones don't exist:
- Checks `src/prompts/` first
- Falls back to `config/prompts/roles/` for roles
- Logs deprecation warnings when using old paths

## Migration

If you have prompts in the old `config/prompts/` location:

```bash
python scripts/migrate_prompts.py
```

This will:
- Backup original prompts to `config/prompts.backup/`
- Migrate role prompts to `src/prompts/roles/`
- Convert `.txt` files to `.md` format
- Update `config/debate_config.yaml`

## API Reference

### PromptLoader

```python
class PromptLoader:
    def __init__(self, config: PromptsConfig, base_path: Optional[Path] = None)

    def load(self, prompt_id: str) -> str
        """Load a prompt from cache or file."""

    def load_with_context(self, prompt_id: str, context: PromptContext) -> str
        """Load and render a prompt with context variables."""

    def validate(self, prompt_id: str) -> ValidationResult
        """Validate a prompt file."""

    def reload(self) -> None
        """Clear cache and reload all prompts."""
```

### PromptContext

```python
@dataclass
class PromptContext:
    question: str = ""
    topic: str = ""
    prd_content: str = ""
    language: str = "en"
    recent_context: str = ""
    pro_prompt: str = ""
    con_prompt: str = ""
    dialogue_summary: str = ""
    verdict_explanation: str = ""
    winner: str = ""
    min_takeaways: int = 3
    max_takeaways: int = 15
```

## Troubleshooting

### Prompt not found

```
FileNotFoundError: Prompt file not found: src/prompts/debate/judge/verdict.md
```

**Solution**: Check that the file exists and the path in `config/debate_config.yaml` is correct.

### Missing template variable

```
ValueError: Missing required variable: 'question'
```

**Solution**: Ensure all required variables are provided in `PromptContext` when calling `load_with_context()`.

### Empty prompt error

```
ValueError: Prompt file is empty: src/prompts/debate/stages/opening_pro.md
```

**Solution**: Ensure the prompt file has content (not just whitespace).

## See Also

- [PROMPTS.md](../PROMPTS.md) - Comprehensive prompt management guide
- [README.md](../README.md) - Project overview and quick start
