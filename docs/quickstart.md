# Quickstart Guide

Get started with Deb8flow's debate quality enhancement and prompt management system.

## Installation

```bash
# Clone the repository
git clone <repo-url>
cd Deb8flow

# Install dependencies using Poetry
poetry install

# Or using pip
pip install -r requirements.txt
```

## Configuration

1. **Set your API key:**

```bash
export OPENAI_API_KEY=your_openai_key_here
```

Or create a `.env` file:
```bash
OPENAI_API_KEY=your_openai_key_here
```

2. **Configure debate settings** in `config/debate_config.yaml`:

```yaml
llm:
  model: "gpt-4o-mini"
  temperature: 0.8
  base_url: ""  # Leave empty for OpenAI

debate:
  mode: "standard"  # or "simple"
  language: "ru"

prompts:
  stages:
    opening_pro: "src/prompts/debate/stages/opening_pro.md"
    # ... (auto-configured)
```

## Running Your First Debate

### Option 1: Product Committee (Recommended)

```bash
# Basic committee run
poetry run python main.py committee \
  --prd examples/sample_prd.txt \
  --question "Заработает ли этот проект?"

# With automatic conclusion generation
poetry run python main.py committee \
  --prd examples/sample_prd.txt \
  --question "Заработает ли этот проект?" \
  --run-conclusion
```

### Option 2: Document Debate

```bash
poetry run python main.py debate \
  --text "GitHub is essential for modern software development" \
  --pro-prompt config/prompts/roles/tpm.txt \
  --con-prompt config/prompts/roles/cpo.txt
```

## Customizing Prompts

### Quick Edit

1. Navigate to `src/prompts/`
2. Open any `.md` file (e.g., `src/prompts/debate/stages/opening_pro.md`)
3. Edit the content
4. Save - changes take effect immediately!

### Example: Make debates more concise

Edit `src/prompts/debate/stages/opening_pro.md`:

```markdown
# PRO Opening Statement

...

## Instructions
1. Focus on why this project should proceed
2. Be concise (aim for 150-200 words)  # CHANGED from 250-400
3. Make specific, evidence-based arguments
...
```

### Example: Change debate language

Edit `src/prompts/debate/context/debate_context.md`:

```markdown
## Language

LANGUAGE: {language}  # This variable is set from config
```

Set `language: "ru"` in `config/debate_config.yaml` to get Russian debates.

## Choosing Debate Mode

### Standard Mode (High Quality)

**Use when:** Quality matters more than speed
- Formal product reviews
- Important decisions
- Complex topics

```yaml
debate:
  mode: "standard"
```

**Performance:** 9 LLM calls per debate (~30-60 seconds)

### Simple Mode (Fast)

**Use when:** Quick iterations needed
- Exploratory analysis
- Testing prompt changes
- Cost-sensitive applications

```yaml
debate:
  mode: "simple"
```

**Performance:** 1 LLM call per debate (~5-10 seconds)

## Working with Prompts Programmatically

### Load a Prompt

```python
from shared.debate.application.prompt_loader import PromptLoader
from shared.config import load_config

config = load_config()
loader = PromptLoader(config.prompts)

# Load raw prompt
judge_prompt = loader.load("debate.judge")
print(judge_prompt)
```

### Load with Variables

```python
from shared.debate.application.prompt_loader import PromptContext

context = PromptContext(
    question="Should we use microservices?",
    topic="E-commerce platform architecture",
    prd_content="The system needs to handle...",
    language="You must conduct the debate in ENGLISH."
)

rendered = loader.load_with_context("debate.context", context)
print(rendered)
```

### Validate Prompts

```python
result = loader.validate("debate.judge")

if result.is_valid:
    print("✓ Judge prompt is valid")
else:
    print("✗ Judge prompt has errors:")
    for error in result.errors:
        print(f"  - {error}")
```

## Migration from Old Prompts

If you have custom prompts in the old `config/prompts/` location:

```bash
# Run migration script
python scripts/migrate_prompts.py

# Preview first (dry-run)
python scripts/migrate_prompts.py --dry-run
```

## Common Tasks

### Add a New Debate Stage

1. Create prompt file:
   ```bash
   touch src/prompts/debate/stages/clarification_pro.md
   ```

2. Add stage content (use existing prompts as template)

3. Add to orchestrator (requires code changes)

### Change Model Provider

**For OpenAI-compatible APIs (DeepSeek, etc.):**

```yaml
llm:
  base_url: "https://api.requesty.ai/v1"
  model: "deepseek-chat"
```

**For local models (Ollama):**

```yaml
llm:
  base_url: "http://localhost:11434/v1"
  model: "llama3"
```

### Export Debate Results

```bash
# Committee automatically saves to:
./committee_output/RUN_YYYYMMDD_HHMMSS_slug/

# Or specify output directory:
poetry run python main.py committee \
  --prd examples/sample_prd.txt \
  --output-dir ./my_results
```

## Troubleshooting

### "Prompt file not found"

**Problem:** `FileNotFoundError: src/prompts/debate/judge/verdict.md`

**Solution:**
```bash
# Check prompt exists
ls src/prompts/debate/judge/verdict.md

# Check config path matches file
grep "judge:" config/debate_config.yaml
```

### "Empty prompt error"

**Problem:** Prompt file exists but is empty

**Solution:** Add content to the prompt file

### "Missing template variable"

**Problem:** `ValueError: Missing required variable: 'question'`

**Solution:** Provide all required variables in PromptContext

## Next Steps

- Read [Prompt Management Guide](prompt-management.md) for advanced customization
- Read [API Reference](api-reference.md) for programmatic usage
- Read [PROMPTS.md](../PROMPTS.md) for prompt editing guide
- Explore example prompts in `src/prompts/`

## Getting Help

- Check existing issues on GitHub
- Review example configurations in `config/examples/`
- Run tests: `poetry run pytest`

---

**Default Configuration Examples:**

| Setting | Default | Common Alternative |
|---------|---------|-------------------|
| Model | `gpt-4o-mini` | `gpt-4o`, `deepseek-chat`, `llama3` |
| Temperature | `0.8` | `0.7` (more focused), `1.0` (more creative) |
| Mode | `standard` | `simple` (faster) |
| Language | `en` | `ru`, `zh`, `de`, `fr`, `es` |
| Max Tokens | `1500` | `2000` (longer responses), `1000` (shorter) |
