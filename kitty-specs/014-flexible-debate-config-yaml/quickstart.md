# Quickstart Guide: Flexible Debate Configuration

**Feature**: #014 - Flexible Debate Configuration with YAML
**Target Audience**: Developers, Researchers, Product Teams
**Prerequisites**: Python 3.12+, OpenAI API key (or compatible)

## Table of Contents

1. [Installation](#installation)
2. [Your First Debate](#your-first-debate)
3. [Custom Configuration](#custom-configuration)
4. [Common Patterns](#common-patterns)
5. [Troubleshooting](#troubleshooting)

---

## Installation

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Environment Variables

```bash
# Required: OpenAI API key (or compatible)
export OPENAI_API_KEY="your-api-key-here"

# Optional: Requesty API key for DeepSeek
export REQ_API_KEY="your-requesty-key-here"
```

### 3. Verify Installation

```bash
python main.py
```

You should see a debate start with the default PRD reviewer roles.

---

## Your First Debate

### Running with Default Configuration

The system includes a default `debate.yml` that preserves the original PRD review behavior:

```bash
# Runs debate with default configuration
python main.py
```

**Expected Output**:
```
🏆 WINNER: PRO
(or CON, depending on the debate)
```

### Understanding the Default Configuration

The default `debate.yml` includes:

- **2 roles**: PRO (argues for) and CON (argues against)
- **3 rounds**: Opening → Rebuttal → Counter → Final Argument
- **Fact-checking**: Enabled after each speaker
- **Model**: Requesty DeepSeek (or OpenAI if configured)

---

## Custom Configuration

### Creating Your First Custom Config

Create a file `my-debate.yml`:

```yaml
debate_config_version: "1.0"

workflow:
  mode: standard
  rounds: 2  # Shorter debate

roles:
  - name: optimist
    side: pro
    prompt: |-
      You are an optimist who sees the best in every situation.
      Focus on opportunities, benefits, and positive outcomes.
    model: deepseek-chat
    temperature: 0.8

  - name: skeptic
    side: con
    prompt: |-
      You are a skeptic who questions assumptions and identifies risks.
      Focus on potential problems, limitations, and challenges.
    model: deepseek-chat
    temperature: 0.8

models:
  deepseek-chat:
    provider: requesty
    model_name: deepseek-chat
    api_key_env: REQ_API_KEY
```

### Running Your Custom Debate

```bash
python main.py --debate-config my-debate.yml
```

---

## Common Patterns

### Pattern 1: File-Based Prompts

For reusable prompts, store them in separate files:

**File Structure**:
```
project/
├── debate.yml
└── prompts/
    ├── roles/
    │   ├── legal_pro.md
    │   └── legal_con.md
```

**Configuration** (`debate.yml`):
```yaml
roles:
  - name: prosecutor
    side: pro
    prompt_file: prompts/roles/legal_pro.md
    model: deepseek-chat

  - name: defense
    side: con
    prompt_file: prompts/roles/legal_con.md
    model: deepseek-chat
```

### Pattern 2: Auxiliary Roles

Add domain experts who participate at specific points:

```yaml
auxiliary_roles:
  - name: medical_expert
    side: auxiliary
    prompt: |-
      You are a medical doctor reviewing this healthcare proposal.
      Comment on clinical feasibility and patient safety.
    model: deepseek-chat
    trigger:
      after_round: 2  # Speaks after round 2
```

### Pattern 3: Document Analysis

For document-based debates, use the document workflow mode:

```yaml
workflow:
  mode: document  # Enables document context
  rounds: 3

roles:
  - name: analyst_bullish
    side: pro
    prompt: |-
      Analyze this document from an optimistic perspective.
      Focus on positive indicators and growth potential.
      Document: {document_content}
    model: deepseek-chat

  - name: analyst_bearish
    side: con
    prompt: |-
      Analyze this document from a critical perspective.
      Focus on risks and concerns.
      Document: {document_content}
    model: deepseek-chat
```

Run with document:
```bash
python document_debate_cli.py \
  --debate-config financial-analysis.yml \
  --docx report.docx
```

### Pattern 4: Multiple Models

Use different models for different roles:

```yaml
roles:
  - name: researcher
    side: pro
    prompt: "Conduct thorough research..."
    model: gpt-4  # Uses more capable model

  - name: critic
    side: con
    prompt: "Provide concise critiques..."
    model: deepseek-chat  # Uses faster model

models:
  gpt-4:
    provider: openai
    model_name: gpt-4
    api_key_env: OPENAI_API_KEY

  deepseek-chat:
    provider: requesty
    model_name: deepseek-chat
    api_key_env: REQ_API_KEY
```

---

## Configuration Reference

### Required Fields

| Field | Description | Example |
|-------|-------------|---------|
| `workflow.mode` | "standard" or "document" | `standard` |
| `workflow.rounds` | Number of rounds (≥1) | `3` |
| `roles` | List of role definitions | See below |
| `models` | Model configurations | See below |

### Role Definition

```yaml
roles:
  - name: string              # Unique identifier
    side: string              # "pro" | "con" | "neutral"
    prompt: string            # Inline prompt (or use prompt_file)
    prompt_file: string       # Path to prompt file
    model: string             # Model name from models section
    temperature: float        # 0.0-2.0, default 0.7
    max_tokens: int           # Token limit, default 1000
```

### Model Definition

```yaml
models:
  model_name:
    provider: string          # "openai" | "azure" | "zhipu" | "requesty"
    model_name: string        # Model identifier
    api_key_env: string       # Environment variable with API key
```

---

## Troubleshooting

### Error: Configuration file not found

**Problem**: System can't find your configuration file.

**Solution**:
```bash
# Use absolute path
python main.py --debate-config /full/path/to/config.yml

# Or relative path from project root
python main.py --debate-config configs/my-debate.yml
```

### Error: Prompt file not found

**Problem**: Referenced prompt file doesn't exist.

**Solution**:
- Check that prompt file paths are relative to the config file directory
- Verify the file exists at the specified path
- Use absolute paths if needed

### Error: Model not found

**Problem**: Role references a model that isn't defined.

**Solution**:
```yaml
# Add the missing model to models section
models:
  your-model-name:  # Must match role.model
    provider: openai
    model_name: gpt-4
    api_key_env: OPENAI_API_KEY
```

### Error: Missing required role

**Problem**: Configuration doesn't include required PRO or CON role.

**Solution**:
```yaml
roles:
  - name: pro
    side: pro  # Required
    # ...

  - name: con
    side: con  # Required
    # ...
```

### Debate isn't using my custom prompts

**Problem**: Prompts aren't being applied as expected.

**Solution**:
1. Check prompt precedence: `prompt_file` overrides `prompt`
2. Verify prompt files are UTF-8 encoded
3. Check for YAML syntax errors in multiline strings
4. Use `|` or `|-` for multiline prompts in YAML

### How do I see what configuration is loaded?

Add debug output:

```python
# In main.py, before running workflow
import yaml
with open(args.debate_config) as f:
    config = yaml.safe_load(f)
    print("Loaded config:", yaml.dump(config, default_flow_style=False))
```

---

## Example Configurations

### Legal Debate

```yaml
# examples/legal-debate.yml
debate_config_version: "1.0"

workflow:
  mode: standard
  rounds: 3

roles:
  - name: prosecutor
    side: pro
    prompt_file: prompts/roles/prosecutor.md
    model: deepseek-chat

  - name: defense
    side: con
    prompt_file: prompts/roles/defense.md
    model: deepseek-chat

models:
  deepseek-chat:
    provider: requesty
    model_name: deepseek-chat
    api_key_env: REQ_API_KEY
```

### Financial Analysis

```yaml
# examples/financial-analysis.yml
debate_config_version: "1.0"

workflow:
  mode: document
  rounds: 2

roles:
  - name: bull_analyst
    side: pro
    prompt: |-
      You are a bullish financial analyst.
      Analyze the document for positive indicators, growth opportunities,
      and strong fundamentals. Use {document_content} placeholder.
    model: deepseek-chat

  - name: bear_analyst
    side: con
    prompt: |-
      You are a bearish financial analyst.
      Analyze the document for risks, red flags, and concerns.
      Use {document_content} placeholder.
    model: deepseek-chat

models:
  deepseek-chat:
    provider: requesty
    model_name: deepseek-chat
    api_key_env: REQ_API_KEY
```

---

## Next Steps

1. **Explore Examples**: Check `examples/` directory for more configurations
2. **Customize Prompts**: Edit role prompts to match your use case
3. **Adjust Parameters**: Experiment with temperature, rounds, and token limits
4. **Add Auxiliary Roles**: Introduce domain experts for specialized perspectives
5. **Document Your Work**: Version control your configurations for reproducibility

---

## Getting Help

- **Documentation**: See `CLAUDE.md` for architecture details
- **Examples**: Check `examples/` directory for sample configurations
- **Issues**: Report bugs or request features via GitHub issues

---

**End of Quickstart Guide**
