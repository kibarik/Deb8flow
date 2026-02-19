# Quick Provider Switching Guide

This guide shows how to quickly switch between different LLM providers by updating your `.env` file.

## Quick Switch Matrix

| Provider | `.env` DEBATE_BASE_URL | `.env` DEBATE_MODEL | Notes |
|----------|------------------------|---------------------|-------|
| **OpenAI** | (leave empty) | `gpt-4o-mini` | Default |
| **DeepSeek** | `https://api.requesty.ai/v1` | `deepseek-chat` | Via Requesty |
| **Zhipu AI** | `https://open.bigmodel.cn/api/paas/v4` | `glm-4` | Chinese AI |
| **Ollama** | `http://localhost:11434/v1` | `llama3` | Local only |

## Step-by-Step: Switching Providers

### Option 1: Edit `.env` file (Recommended)

1. Open `.env` file in your project root
2. Update the values:

```bash
# For OpenAI (default)
DEBATE_BASE_URL=
DEBATE_MODEL=gpt-4o-mini

# For DeepSeek
DEBATE_BASE_URL=https://api.requesty.ai/v1
DEBATE_MODEL=deepseek-chat

# For Zhipu AI
DEBATE_BASE_URL=https://open.bigmodel.cn/api/paas/v4
DEBATE_MODEL=glm-4

# For Ollama (local)
DEBATE_BASE_URL=http://localhost:11434/v1
DEBATE_MODEL=llama3
```

3. Save and run:
```bash
poetry run product-committee --prd prd.txt --question "Your question"
```

### Option 2: CLI Override (Temporary)

```bash
# DeepSeek
poetry run product-committee \
  --prd prd.txt \
  --question "Your question" \
  --base-url https://api.requesty.ai/v1 \
  --model deepseek-chat

# Ollama
poetry run product-committee \
  --prd prd.txt \
  --question "Your question" \
  --base-url http://localhost:11434/v1 \
  --model llama3
```

## Current Configuration Check

To see what's currently configured:

```bash
python -c "
from src.shared.config import DebateConfigFile
config = DebateConfigFile.from_yaml('debate_config.yaml')
print(f'Model: {config.llm.model}')
print(f'Base URL: {config.llm.base_url or \"(OpenAI default)\"}')
print(f'Temperature: {config.llm.temperature}')
"
```

## API Key Setup

### OpenAI
```bash
# In .env
OPENAI_API_KEY=sk-your-openai-key
```

### DeepSeek (via Requesty)
```bash
# In .env
OPENAI_API_KEY=rqsty-sk-your-requesty-key
DEBATE_BASE_URL=https://api.requesty.ai/v1
DEBATE_MODEL=deepseek-chat
```

### Zhipu AI
```bash
# In .env
ZHIPUAI_API_KEY=your-zhipu-key
DEBATE_BASE_URL=https://open.bigmodel.cn/api/paas/v4
DEBATE_MODEL=glm-4
```

### Ollama (Local - No API Key Needed)
```bash
# In .env
DEBATE_BASE_URL=http://localhost:11434/v1
DEBATE_MODEL=llama3
# Ollama doesn't require a real API key
```

## Advanced: Custom Provider

For any OpenAI-compatible API:

```bash
# In .env
DEBATE_BASE_URL=https://your-custom-endpoint.com/v1
DEBATE_MODEL=your-model-name
OPENAI_API_KEY=your-api-key
```

## Troubleshooting

### "API key not found"
- Check that `OPENAI_API_KEY` is set in `.env`
- Verify `.env` file is in project root
- Ensure no typos in variable names

### "Model not found"
- Verify model name is correct for your provider
- Check `DEBATE_MODEL` in `.env`
- Try CLI override: `--model your-model`

### "Connection refused"
- Check `DEBATE_BASE_URL` in `.env`
- Verify API endpoint is accessible
- For local models (Ollama), ensure service is running

### "Timeout"
- Local models may be slower: reduce `max_concurrency` in config
- Increase `timeout` in `debate_config.yaml`
- Try a smaller/faster model
