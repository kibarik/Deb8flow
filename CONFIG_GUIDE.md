# Debate Configuration Guide

This guide explains how to configure and use the product committee with different LLM providers.

## Quick Start

1. Set up your `.env` file with API keys
2. Optionally edit `debate_config.yaml` for custom settings
3. Run: `python product_committee.py --prd prd.txt --question "Your question"`

## Environment Variable Substitution

The configuration supports automatic environment variable substitution from your `.env` file using `${VAR_NAME}` syntax:

```yaml
llm:
  base_url: "${DEBATE_BASE_URL:}"          # Empty default
  model: "${DEBATE_MODEL:gpt-4o-mini}"     # Default: gpt-4o-mini
  api_key: "${OPENAI_API_KEY:}"           # From .env file
  temperature: ${DEBATE_TEMPERATURE:0.8}   # Default: 0.8
```

**Syntax:**
- `${VAR_NAME}` - Use environment variable (empty if not set)
- `${VAR_NAME:default}` - Use environment variable with default fallback

**Supported .env variables:**
- `OPENAI_API_KEY` - API key for OpenAI-compatible APIs
- `DEBATE_MODEL` - Model name override
- `DEBATE_TEMPERATURE` - Temperature override
- `DEBATE_BASE_URL` - Custom API endpoint

## Configuration File Structure

The `debate_config.yaml` file has the following sections:

### LLM Provider Configuration

```yaml
llm:
  base_url: ""          # API base URL (empty for OpenAI default)
  model: "gpt-4o-mini"  # Model name
  api_key: ""           # API key (or use ${OPENAI_API_KEY:})
  temperature: 0.8      # Sampling temperature (0.0 - 1.0)
  max_tokens: 1500      # Maximum tokens per response
  timeout: 60           # Request timeout in seconds
```

### Debate Settings

```yaml
debate:
  max_retries: 2        # Retry attempts per room
  max_concurrency: 2    # Parallel rooms (0 = all, 1 = sequential)
  language: ""          # Output language (optional)
```

### Output Settings

```yaml
output:
  directory: "./committee_output"  # Output directory
  save_dialogues: true             # Save JSON dialogues
  save_metadata: true              # Save metadata
```

## Provider-Specific Configurations

### OpenAI

```yaml
llm:
  base_url: ""          # Empty for default
  model: "gpt-4o-mini"  # or gpt-4o, gpt-3.5-turbo
  api_key: "sk-..."     # Your OpenAI API key
  temperature: 0.8
```

### DeepSeek (via Requesty)

```yaml
llm:
  base_url: "https://api.requesty.ai/v1"
  model: "deepseek-chat"
  api_key: "rqsty-sk-..."
  temperature: 0.8
```

### Zhipu AI

```yaml
llm:
  base_url: "https://open.bigmodel.cn/api/paas/v4"
  model: "glm-4"
  api_key: "your-zhipu-key"
  temperature: 0.8
```

### Ollama (Local)

```yaml
llm:
  base_url: "http://localhost:11434/v1"
  model: "llama3"
  api_key: "ollama"  # Not used but required
  temperature: 0.8
```

### Other OpenAI-Compatible APIs

```yaml
llm:
  base_url: "https://your-api-endpoint.com/v1"
  model: "your-model-name"
  api_key: "your-api-key"
  temperature: 0.8
```

## Usage Examples

### Using Default Config

```bash
# Uses debate_config.yaml in current directory
python product_committee.py --prd prd.txt --question "Should we build this?"
```

### Using Custom Config

```bash
python product_committee.py --prd prd.txt --question "Should we build this?" --config my_config.yaml
```

### Overriding Config Values

```bash
# Override model from CLI
python product_committee.py --prd prd.txt --question "Should we build this?" --model gpt-4o

# Override multiple settings
python product_committee.py \
  --prd prd.txt \
  --question "Should we build this?" \
  --base-url https://api.requesty.ai/v1 \
  --model deepseek-chat \
  --temperature 0.9
```

### Using Environment Variables

**Option 1: Using .env file (recommended)**

Create a `.env` file in your project root:

```bash
# API Keys
OPENAI_API_KEY=sk-your-key-here

# Optional: Override model settings
DEBATE_MODEL=gpt-4o-mini
DEBATE_TEMPERATURE=0.8
DEBATE_BASE_URL=
```

Then use `${VAR_NAME}` in `debate_config.yaml`:

```yaml
llm:
  api_key: "${OPENAI_API_KEY:}"
  model: "${DEBATE_MODEL:gpt-4o-mini}"
  temperature: ${DEBATE_TEMPERATURE:0.8}
```

**Option 2: Export directly**

```bash
# Set API key via environment
export OPENAI_API_KEY="sk-..."
python product_committee.py --prd prd.txt --question "Should we build this?"

# Or use DEBATE_* variables
export DEBATE_API_KEY="sk-..."
export DEBATE_MODEL="gpt-4o"
export DEBATE_TEMPERATURE="0.9"
python product_committee.py --prd prd.txt --question "Should we build this?"
```

## Configuration Priority

Settings are applied in the following priority (highest first):

1. CLI arguments
2. DEBATE_* environment variables
3. OPENAI_* environment variables
4. YAML config file
5. Defaults

## Example Configurations

See `config/examples/` for complete configuration examples:

- `openai.yaml` - OpenAI configuration
- `deepseek.yaml` - DeepSeek via Requesty
- `zhipu.yaml` - Zhipu AI (GLM models)
- `ollama.yaml` - Ollama local models

## Troubleshooting

### API Key Errors

```
Error: API key not provided
```

**Solution:** Set `OPENAI_API_KEY` environment variable or add `api_key` to config.

### Connection Errors

```
Error: Connection refused
```

**Solution:** Check `base_url` in config and ensure the API endpoint is accessible.

### Model Not Found

```
Error: Model not found
```

**Solution:** Verify the model name is correct for your provider.

### Timeout Errors

```
Error: Request timeout
```

**Solution:** Increase `timeout` in config or reduce `max_tokens`.

## Best Practices

1. **Never commit API keys** - Use environment variables instead
2. **Create separate configs** for different environments (dev, prod)
3. **Test with smaller models** first (gpt-4o-mini vs gpt-4o)
4. **Adjust temperature** based on your needs:
   - 0.0-0.3: Focused, deterministic
   - 0.4-0.7: Balanced
   - 0.8-1.0: Creative, varied
5. **Use appropriate concurrency** based on your rate limits:
   - Local models: 1-2
   - Paid APIs: 2-4
