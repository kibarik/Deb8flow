---
work_package_id: WP02
title: Prompt Configuration Schema
lane: "doing"
dependencies: []
base_branch: main
base_commit: e5a40914c1039c351e8fef4d2bfb51ea3c7309f5
created_at: '2026-02-19T07:04:01.076775+00:00'
subtasks: [T007, T008, T009, T010]
shell_pid: "75216"
agent: "claude-code"
history:
- timestamp: '2025-02-19T00:00:00Z'
  action: Created
  agent: spec-kitty
---

# WP02: Prompt Configuration Schema

## Objective

Create the configuration schema for prompt file paths in `config/debate_config.yaml` and add Pydantic models for prompt configuration validation. This enables the system to locate and validate prompt files.

## Context

Now that prompt files exist (from WP01), we need to:
1. Configure the system to find these prompt files
2. Add configuration for debate mode selection (standard/simple)
3. Validate configuration at startup to fail fast on errors
4. Maintain backward compatibility with existing config structure

The configuration system uses:
- YAML for human-readable configuration
- Pydantic for validation and type safety
- Environment variable substitution for sensitive values

## Implementation Guidance

### T007: Add Prompts Section to Config YAML

**Purpose:** Extend `config/debate_config.yaml` with prompt file path mappings.

**Steps:**
1. Open `config/debate_config.yaml`
2. Add the following `prompts:` section before the `output:` section:
   ```yaml
   # Prompts Configuration
   # Map prompt types to their file paths
   prompts:
     # Debate stage prompts
     stages:
       opening_pro: "src/prompts/debate/stages/opening_pro.md"
       opening_con: "src/prompts/debate/stages/opening_con.md"
       rebuttal_pro: "src/prompts/debate/stages/rebuttal_pro.md"
       rebuttal_con: "src/prompts/debate/stages/rebuttal_con.md"
       counter_pro: "src/prompts/debate/stages/counter_pro.md"
       counter_con: "src/prompts/debate/stages/counter_con.md"
       final_pro: "src/prompts/debate/stages/final_pro.md"
       final_con: "src/prompts/debate/stages/final_con.md"

     # Judge prompt
     judge: "src/prompts/debate/judge/verdict.md"

     # Context template
     context: "src/prompts/debate/context/debate_context.md"

     # Analysis prompts
     analysis:
       system: "src/prompts/analysis/system_prompt.md"
       takeaway: "src/prompts/analysis/takeaway_analysis.md"

     # Role prompts (optional - fallback to config/prompts/roles/)
     roles:
       tpm: "src/prompts/roles/tpm.md"
       cpo: "src/prompts/roles/cpo.md"
       cfo: "src/prompts/roles/cfo.md"
       cto: "src/prompts/roles/cto.md"
       bdm: "src/prompts/roles/bdm.md"
   ```

3. Also update the `debate:` section to add mode configuration:
   ```yaml
   # Debate Settings
   debate:
     # Debate mode: standard (multi-turn) or simple (single-call)
     mode: "standard"

     # Maximum number of retry attempts per room
     max_retries: 2

     # Maximum concurrent debate rooms (0 = all at once, 1 = sequential)
     max_concurrency: 0

     # Language for debate output (optional)
     # Examples: en, ru, zh, es, fr, de
     language: "ru"
   ```

4. Preserve all existing configuration sections
5. Ensure YAML syntax is correct (indentation, colons, quotes)

**Files:**
- `config/debate_config.yaml` (modify, add ~40 lines)

**Validation:**
- [ ] YAML is valid (can be parsed)
- [ ] All prompt file paths match WP01 structure
- [ ] Debate mode is added with default "standard"
- [ ] Existing config sections are preserved
- [ ] Configuration can be loaded by existing ConfigLoader

**Test Command:**
```bash
python -c "import yaml; yaml.safe_load(open('config/debate_config.yaml'))"
```

---

### T008: Create Pydantic Configuration Models

**Purpose:** Add Pydantic models for prompt configuration validation.

**Steps:**
1. Open or create `src/shared/config/models.py`
2. Add the following Pydantic models:
   ```python
   """Configuration models for debate system."""

   from pathlib import Path
   from typing import Dict, Optional, List
   from pydantic import BaseModel, Field, validator


   class PromptPathsConfig(BaseModel):
       """Configuration for prompt file paths."""

       stages: Dict[str, str] = Field(default_factory=dict)
       judge: str
       context: str
       analysis: Dict[str, str] = Field(default_factory=dict)
       roles: Optional[Dict[str, str]] = None

       @validator('stages')
       def validate_required_stages(cls, v):
           """Ensure all required stage prompts are configured."""
           required_stages = [
               'opening_pro', 'opening_con',
               'rebuttal_pro', 'rebuttal_con',
               'counter_pro', 'counter_con',
               'final_pro', 'final_con'
           ]
           missing = [s for s in required_stages if s not in v]
           if missing:
               raise ValueError(f"Missing required stage prompts: {missing}")
           return v

       @validator('judge', 'context', pre=True)
       def validate_path_exists(cls, v):
           """Validate that file paths exist (or will exist at runtime)."""
           if not v:
               raise ValueError("Path cannot be empty")
           return v


   class PromptsConfig(BaseModel):
       """Top-level prompts configuration."""

       stages: Dict[str, str]
       judge: str
       context: str
       analysis: Dict[str, str]
       roles: Optional[Dict[str, str]] = None


   class DebateConfig(BaseModel):
       """Debate settings configuration."""

       mode: str = Field(default="standard", regex="^(standard|simple)$")
       max_retries: int = Field(default=2, ge=0, le=10)
       max_concurrency: int = Field(default=0, ge=0)
       language: str = Field(default="en")

       @validator('mode')
       def validate_mode(cls, v):
           """Ensure mode is either standard or simple."""
           valid_modes = ['standard', 'simple']
           if v not in valid_modes:
               raise ValueError(f"Invalid debate mode: {v}. Must be one of {valid_modes}")
           return v


   class LLMConfig(BaseModel):
       """LLM provider configuration."""

       base_url: Optional[str] = None
       model: str = "gpt-4o"
       api_key: Optional[str] = None
       temperature: float = Field(default=0.8, ge=0.0, le=2.0)
       max_tokens: int = Field(default=1500, ge=1)
       timeout: int = Field(default=60, ge=1)


   class AgentsConfig(BaseModel):
       """Agent configuration."""

       main: Dict[str, str]
       opponents: List[Dict[str, str]] = Field(default_factory=list)


   class DebateConfigFull(BaseModel):
       """Full debate configuration."""

       llm: LLMConfig
       debate: DebateConfig
       agents: AgentsConfig
       prompts: PromptsConfig
       output: Optional[Dict[str, any]] = None
       logging: Optional[Dict[str, any]] = None
   ```

3. Add import for these models in `src/shared/config/__init__.py`:
   ```python
   from .models import (
       PromptsConfig,
       DebateConfig,
       LLMConfig,
       AgentsConfig,
       DebateConfigFull,
       PromptPathsConfig
   )

   __all__ = [
       "PromptsConfig",
       "DebateConfig",
       "LLMConfig",
       "AgentsConfig",
       "DebateConfigFull",
       "PromptPathsConfig"
   ]
   ```

**Files:**
- `src/shared/config/models.py` (create or modify, ~100 lines)
- `src/shared/config/__init__.py` (modify, add ~15 lines)

**Validation:**
- [ ] All Pydantic models compile without errors
- [ ] Validators work correctly (test with invalid input)
- [ ] Required stages are validated
- [ ] Debate mode validation works
- [ ] Models can be instantiated from config dict

**Example Usage:**
```python
from shared.config.models import DebateConfigFull
import yaml

config_dict = yaml.safe_load(open('config/debate_config.yaml'))
config = DebateConfigFull(**config_dict)
```

---

### T009: Add Debate Mode Configuration

**Purpose:** Add and validate the debate mode configuration option.

**Note:** This is already done in T007 as part of the config YAML update.

**Validation:**
- [ ] `debate.mode` exists in config
- [ ] Default value is "standard"
- [ ] Validation accepts both "standard" and "simple"
- [ ] Invalid modes raise clear error

---

### T010: Create Configuration Unit Tests

**Purpose:** Test prompt configuration loading and validation.

**Steps:**
1. Create `tests/shared/config/test_prompt_config.py`:
   ```python
   """Tests for prompt configuration."""

   import pytest
   from pathlib import Path
   from pydantic import ValidationError

   from shared.config.models import (
       PromptsConfig,
       DebateConfig,
       DebateConfigFull
   )


   class TestPromptsConfig:
       """Test prompt configuration validation."""

       def test_valid_prompts_config(self):
           """Test loading valid prompts configuration."""
           config = {
               "stages": {
                   "opening_pro": "src/prompts/debate/stages/opening_pro.md",
                   "opening_con": "src/prompts/debate/stages/opening_con.md",
                   "rebuttal_pro": "src/prompts/debate/stages/rebuttal_pro.md",
                   "rebuttal_con": "src/prompts/debate/stages/rebuttal_con.md",
                   "counter_pro": "src/prompts/debate/stages/counter_pro.md",
                   "counter_con": "src/prompts/debate/stages/counter_con.md",
                   "final_pro": "src/prompts/debate/stages/final_pro.md",
                   "final_con": "src/prompts/debate/stages/final_con.md"
               },
               "judge": "src/prompts/debate/judge/verdict.md",
               "context": "src/prompts/debate/context/debate_context.md",
               "analysis": {
                   "system": "src/prompts/analysis/system_prompt.md",
                   "takeaway": "src/prompts/analysis/takeaway_analysis.md"
               }
           }
           prompts_config = PromptsConfig(**config)
           assert prompts_config.judge == "src/prompts/debate/judge/verdict.md"
           assert len(prompts_config.stages) == 8

       def test_missing_required_stages(self):
           """Test that missing stages raise validation error."""
           config = {
               "stages": {
                   "opening_pro": "src/prompts/debate/stages/opening_pro.md"
               },
               "judge": "src/prompts/debate/judge/verdict.md",
               "context": "src/prompts/debate/context/debate_context.md"
           }
           with pytest.raises(ValidationError):
               PromptsConfig(**config)

       def test_empty_judge_path_raises_error(self):
           """Test that empty judge path raises error."""
           config = {
               "stages": {...},
               "judge": "",
               "context": "src/prompts/debate/context/debate_context.md"
           }
           with pytest.raises(ValidationError):
               PromptsConfig(**config)


   class TestDebateConfig:
       """Test debate configuration validation."""

       def test_valid_standard_mode(self):
           """Test standard mode is valid."""
           config = DebateConfig(mode="standard")
           assert config.mode == "standard"

       def test_valid_simple_mode(self):
           """Test simple mode is valid."""
           config = DebateConfig(mode="simple")
           assert config.mode == "simple"

       def test_invalid_mode_raises_error(self):
           """Test invalid mode raises validation error."""
           with pytest.raises(ValidationError):
               DebateConfig(mode="invalid")

       def test_default_mode_is_standard(self):
           """Test default mode is standard."""
           config = DebateConfig()
           assert config.mode == "standard"


   class TestConfigLoading:
       """Test loading full configuration from file."""

       def test_load_debate_config_yaml(self):
           """Test loading config from YAML file."""
           import yaml

           config_path = Path("config/debate_config.yaml")
           assert config_path.exists()

           with open(config_path) as f:
               config_dict = yaml.safe_load(f)

           # Should have prompts section
           assert "prompts" in config_dict
           assert "stages" in config_dict["prompts"]
           assert "judge" in config_dict["prompts"]

           # Should have debate mode
           assert "debate" in config_dict
           assert "mode" in config_dict["debate"]

           # Validate with Pydantic
           config = DebateConfigFull(**config_dict)
           assert config.prompts.judge
           assert config.debate.mode in ["standard", "simple"]
   ```

2. Ensure tests directory exists:
   ```bash
   mkdir -p tests/shared/config
   ```

**Files:**
- `tests/shared/config/test_prompt_config.py` (new, ~120 lines)

**Validation:**
- [ ] All tests pass
- [ ] Tests cover valid and invalid configurations
- [ ] Tests verify required stages validation
- [ ] Tests verify debate mode validation
- [ ] Tests verify YAML loading

**Run Tests:**
```bash
pytest tests/shared/config/test_prompt_config.py -v
```

---

## Test Strategy

**Unit tests for configuration:**
- Test valid configuration loading
- Test missing required stages
- Test invalid debate modes
- Test empty path validation
- Test YAML file loading

**No integration tests** - those will come in subsequent WPs when PromptLoader uses this configuration.

---

## Definition of Done

- [ ] `config/debate_config.yaml` has `prompts:` section with all paths
- [ ] `config/debate_config.yaml` has `debate.mode` configuration
- [ ] Pydantic models for configuration validation exist
- [ ] Models validate required stages
- [ ] Models validate debate mode (standard/simple)
- [ ] Models export in `__init__.py`
- [ ] Unit tests for configuration exist and pass
- [ ] YAML file can be loaded and validated
- [ ] Existing configuration structure is preserved
- [ ] Backward compatibility maintained

---

## Risks

1. **Breaking Existing Config**: Mitigated by preserving all existing sections
2. **YAML Syntax Errors**: Mitigated by validation in tests
3. **Path Errors**: Mitigated by Pydantic validators

---

## Reviewer Guidance

**Check these specific items:**
1. YAML syntax is correct (indentation matters)
2. All prompt paths match WP01 structure exactly
3. Pydantic validators cover all required fields
4. Debate mode has proper validation
5. Tests cover both success and failure cases
6. No breaking changes to existing config structure
7. Models can be imported from `shared.config`

**Files to Review:**
- `config/debate_config.yaml`
- `src/shared/config/models.py`
- `src/shared/config/__init__.py`
- `tests/shared/config/test_prompt_config.py`

**Common Issues to Look For:**
- YAML indentation errors
- Missing required stage prompts
- Invalid debate mode values
- Weak validation in Pydantic models
- Missing imports in `__init__.py`

## Activity Log

- 2026-02-19T07:04:01Z – claude-code – shell_pid=75216 – lane=doing – Assigned agent via workflow command
