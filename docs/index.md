# Documentation

Welcome to the Deb8flow documentation. This system uses file-based prompts for AI-powered product committee debates.

## 📚 Documentation Index

### Getting Started
- **[Quickstart Guide](quickstart.md)** - Get up and running in 5 minutes
- [README.md](../README.md) - Project overview and installation

### Core Concepts
- **[Prompt Management System](prompt-management.md)** - Architecture and usage
- **[API Reference](api-reference.md)** - Complete API documentation
- **[PROMPTS.md](../PROMPTS.md)** - Prompt editing and customization guide

### Configuration
- `config/debate_config.yaml` - Main configuration file
- `config/examples/` - Example configurations for different scenarios

### Prompts Reference
- `src/prompts/README.md` - Prompt directory structure guide
- `src/prompts/debate/` - Debate stage prompts
- `src/prompts/roles/` - Agent role definitions

## 🚀 Quick Links

### For Developers
- **[API Reference](api-reference.md)** - PromptLoader, Orchestrators, Configuration
- **[Quickstart](quickstart.md)** - Running your first debate
- **[Prompt Management](prompt-management.md)** - Customizing prompts

### For Users
- **[Quickstart](quickstart.md)** - Get started now
- [README.md](../README.md) - What is Deb8flow?

### For Contributors
- `src/prompts/` - Edit prompts directly
- `tests/shared/debate/application/test_prompt_loader.py` - Example tests
- `scripts/migrate_prompts.py` - Migration utility

## 📖 Documentation by Topic

### Prompt System
- **[Quickstart](quickstart.md#customizing-prompts)** - Edit prompts
- **[Prompt Management](prompt-management.md#template-variables)** - Template variables reference
- **[API Reference](api-reference.md#promptloader-module)** - PromptLoader API

### Debate Execution
- **[Quickstart](quickstart.md#choosing-debate-mode)** - Standard vs Simple mode
- **[Prompt Management](prompt-management.md#debate-modes)** - Mode comparison
- **[API Reference](api-reference.md#debate-orchestrators)** - Orchestrator API

### Configuration
- **[Prompt Management](prompt-management.md#configuration)** - Config file reference
- **[API Reference](api-reference.md#configuration-models)** - Configuration models
- `config/examples/` - Example configurations

## 🎯 Common Tasks

| Task | Documentation | Time |
|------|---------------|------|
| Run first debate | [Quickstart](quickstart.md) | 5 min |
| Edit a prompt | [Quickstart](quickstart.md#customizing-prompts) | 2 min |
| Change debate mode | [Quickstart](quickstart.md#choosing-debate-mode) | 1 min |
| Use custom API | [Quickstart](quickstart.md#change-model-provider) | 3 min |
| Migrate old prompts | [Prompt Management](prompt-management.md#migration) | 5 min |
| Create custom stage | [Prompt Management](prompt-management.md#adding-a-new-debate-stage) | 15 min |

## 📦 File Structure

```
Deb8flow/
├── docs/                      # This directory
│   ├── index.md               # This file
│   ├── quickstart.md           # Getting started guide
│   ├── prompt-management.md    # System documentation
│   └── api-reference.md        # API documentation
├── src/
│   ├── prompts/                # Prompt templates
│   │   ├── debate/            # Debate prompts
│   │   ├── analysis/          # Analysis prompts
│   │   └── roles/             # Role definitions
│   └── shared/
│       ├── config/            # Configuration models
│       └── debate/            # Debate framework
│           ├── application/   # Use cases
│           └── infrastructure/ # Implementations
├── config/
│   ├── debate_config.yaml     # Main configuration
│   └── examples/              # Example configs
├── scripts/
│   └── migrate_prompts.py     # Migration utility
└── tests/                     # Test suite
```

## 🔧 Tools & Utilities

### CLI Tools
- `main.py committee` - Run product committee debates
- `main.py debate` - Run document debates
- `main.py conclusion` - Generate conclusions from results
- `scripts/migrate_prompts.py` - Migrate old prompts

### Python API
- `PromptLoader` - Load and render prompts
- `SimpleDebateOrchestrator` - Single-call debates
- `StandardDebateOrchestrator` - Multi-turn debates
- `create_orchestrator()` - Factory for orchestrators

## 🤝 Contributing

When contributing to Deb8flow:

1. **Edit prompts** in `src/prompts/` - no code changes needed
2. **Add features** - follow clean architecture patterns
3. **Write tests** - see `tests/` for examples
4. **Update docs** - keep documentation in sync

See [README.md](../README.md) for contribution guidelines.

## 📞 Support

- **Issues:** Report bugs on GitHub
- **Questions:** Check documentation first
- **Examples:** See `config/examples/`

---

**Last Updated:** 2025-02-19
**Deb8flow Version:** 0.18.0
