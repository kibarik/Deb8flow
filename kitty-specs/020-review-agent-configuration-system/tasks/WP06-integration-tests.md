---
work_package_id: WP06
title: Integration Tests
lane: planned
dependencies: []
subtasks: [T028, T029, T030, T031]
history:
- version: 1.0.0
  date: '2025-02-21'
  author: spec-kitty.tasks
  changes: [Initial work package definition]
---

# WP06: Integration Tests

**Priority**: P2
**Estimated Size**: ~240 lines (4 subtasks × ~55 lines each)
**Implementation Command**: `spec-kitty implement WP06 --base WP04`

## Objective

End-to-end tests for configuration loading, profile application, and CLI override workflow.

## Context

Integration tests verify the complete workflow from loading YAML files to applying profiles and CLI overrides using real config files.

**Reference**:
- Parent WPs: WP01-WP04 (all must be complete)
- Config file: `config/debate_config.yaml`

## Subtasks

### T028: Test full config loading workflow

**Purpose**: Test loading from actual YAML file.

**Implementation**:

Create `tests/integration/test_review_config_workflow.py`:

```python
"""Integration tests for review configuration loading workflow."""
import os
import tempfile
from pathlib import Path
import pytest
import yaml

from src.rewrite.infrastructure.config_loader import load_config
from src.rewrite.domain.review_config import ReviewConfig


class TestConfigLoadingWorkflow:
    """Tests for complete config loading workflow."""

    def test_load_full_config(self, tmp_path):
        """Test loading complete configuration from YAML file."""
        config_content = {
            "rewrite": {
                "review": {
                    "profile": "strict",
                    "llm": {
                        "provider": "anthropic",
                        "model": "claude-3-5-sonnet-20241022",
                        "temperature": 0.3,
                    },
                    "checks": {
                        "security": True,
                        "performance": True,
                        "style": False,
                    },
                    "profiles": {
                        "strict": {
                            "llm": {"temperature": 0.1}
                        }
                    }
                }
            }
        }

        config_file = tmp_path / "config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(config_content, f)

        config = load_config(config_file)

        assert config.profile == "strict"
        assert config.llm.provider == "anthropic"
        assert config.llm.model == "claude-3-5-sonnet-20241022"
        assert config.llm.temperature == 0.3
        assert config.checks.security == True
        assert config.checks.style == False

    def test_load_minimal_config_with_defaults(self, tmp_path):
        """Test loading minimal config uses all defaults."""
        config_content = {"rewrite": {"review": {}}}
        config_file = tmp_path / "config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(config_content, f)

        config = load_config(config_file)

        assert config.profile == "balanced"
        assert config.llm.provider == "openai"
        assert config.llm.model == "gpt-4o-mini"
        assert config.llm.temperature == 0.7

    def test_load_with_env_var_expansion(self, tmp_path):
        """Test environment variable expansion in config."""
        os.environ["TEST_PROVIDER"] = "anthropic"
        os.environ["TEST_MODEL"] = "claude-3-opus-20240229"

        config_content = {
            "rewrite": {
                "review": {
                    "llm": {
                        "provider": "${TEST_PROVIDER}",
                        "model": "${TEST_MODEL}",
                    }
                }
            }
        }

        config_file = tmp_path / "config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(config_content, f)

        config = load_config(config_file)

        assert config.llm.provider == "anthropic"
        assert config.llm.model == "claude-3-opus-20240229"

        # Cleanup
        del os.environ["TEST_PROVIDER"]
        del os.environ["TEST_MODEL"]

    def test_load_with_env_var_default(self, tmp_path):
        """Test env var default value when variable not set."""
        config_content = {
            "rewrite": {
                "review": {
                    "llm": {
                        "temperature": "${UNSET_VAR:0.5}",
                    }
                }
            }
        }

        config_file = tmp_path / "config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(config_content, f)

        config = load_config(config_file)

        assert config.llm.temperature == 0.5
```

**Validation**:
- [ ] Full config loads correctly
- [ ] Minimal config uses defaults
- [ ] Env vars expanded
- [ ] Default values used for unset vars

---

### T029: Test profile application end-to-end

**Purpose**: Test profile selection and merge with real config.

**Implementation**:

```python
class TestProfileApplication:
    """Tests for profile application workflow."""

    def test_apply_strict_profile(self, tmp_path):
        """Test applying strict profile changes settings."""
        config_content = {
            "rewrite": {
                "review": {
                    "profile": "balanced",
                    "llm": {"temperature": 0.5},
                    "profiles": {
                        "strict": {
                            "llm": {"temperature": 0.1, "top_p": 0.5},
                            "checks": {"security": True, "performance": True, "style": True},
                            "output": {"format": "json"}
                        },
                        "balanced": {}
                    }
                }
            }
        }

        config_file = tmp_path / "config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(config_content, f)

        config = load_config(config_file, profile="strict")

        assert config.profile == "strict"
        assert config.llm.temperature == 0.1  # Overridden
        assert config.llm.top_p == 0.5  # Overridden
        assert config.output.format == "json"  # Overridden

    def test_apply_balanced_profile(self, tmp_path):
        """Test applying balanced profile."""
        config_content = {
            "rewrite": {
                "review": {
                    "llm": {"temperature": 0.5},
                    "profiles": {
                        "balanced": {
                            "llm": {"temperature": 0.5, "top_p": 0.8},
                            "checks": {"security": True, "performance": True, "style": False},
                            "output": {"format": "markdown"}
                        }
                    }
                }
            }
        }

        config_file = tmp_path / "config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(config_content, f)

        config = load_config(config_file, profile="balanced")

        assert config.llm.temperature == 0.5
        assert config.llm.top_p == 0.8
        assert config.checks.style == False
        assert config.output.format == "markdown"

    def test_profile_inheritance_behavior(self, tmp_path):
        """Test that profile inherits unspecified values."""
        config_content = {
            "rewrite": {
                "review": {
                    "llm": {"temperature": 0.5, "model": "gpt-4o-mini"},
                    "profiles": {
                        "custom": {
                            "llm": {"temperature": 0.2}  # Only temperature specified
                        }
                    }
                }
            }
        }

        config_file = tmp_path / "config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(config_content, f)

        config = load_config(config_file, profile="custom")

        assert config.llm.temperature == 0.2  # Overridden
        assert config.llm.model == "gpt-4o-mini"  # Inherited
```

**Validation**:
- [ ] Profiles apply correctly
- [ ] Inheritance works
- [ ] Profile name set in config

---

### T030: Test CLI override end-to-end

**Purpose**: Test CLI flag override workflow.

**Implementation**:

```python
class TestCLIOverride:
    """Tests for CLI override workflow."""

    def test_cli_overrides_base_config(self, tmp_path):
        """Test CLI override of base configuration."""
        config_content = {
            "rewrite": {
                "review": {
                    "llm": {"temperature": 0.5}
                }
            }
        }

        config_file = tmp_path / "config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(config_content, f)

        config = load_config(
            config_file,
            cli_overrides={"llm.temperature": 0.1}
        )

        assert config.llm.temperature == 0.1

    def test_cli_overrides_profile(self, tmp_path):
        """Test CLI override has highest priority over profile."""
        config_content = {
            "rewrite": {
                "review": {
                    "profiles": {
                        "strict": {"llm": {"temperature": 0.1}}
                    }
                }
            }
        }

        config_file = tmp_path / "config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(config_content, f)

        config = load_config(
            config_file,
            profile="strict",
            cli_overrides={"llm.temperature": 0.05}
        )

        assert config.llm.temperature == 0.05  # CLI wins

    def test_multiple_cli_overrides(self, tmp_path):
        """Test multiple CLI overrides applied."""
        config_content = {
            "rewrite": {
                "review": {
                    "llm": {"temperature": 0.5, "top_p": 0.9},
                    "checks": {"security": True, "performance": True}
                }
            }
        }

        config_file = tmp_path / "config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(config_content, f)

        config = load_config(
            config_file,
            cli_overrides={
                "llm.temperature": 0.3,
                "llm.top_p": 0.7,
                "checks.security": False
            }
        )

        assert config.llm.temperature == 0.3
        assert config.llm.top_p == 0.7
        assert config.checks.security == False
        assert config.checks.performance == True  # Unchanged
```

**Validation**:
- [ ] CLI overrides base config
- [ ] CLI overrides profile
- [ ] Multiple overrides work together

---

### T031: Test invalid config handling

**Purpose**: Test error handling for invalid configurations.

**Implementation**:

```python
class TestInvalidConfigHandling:
    """Tests for invalid configuration handling."""

    def test_missing_config_file(self, tmp_path):
        """Test error when config file doesn't exist."""
        config_file = tmp_path / "nonexistent.yaml"

        with pytest.raises(FileNotFoundError) as exc_info:
            load_config(config_file)

        assert "Configuration file not found" in str(exc_info.value)

    def test_invalid_yaml_syntax(self, tmp_path):
        """Test error when YAML has invalid syntax."""
        config_file = tmp_path / "invalid.yaml"
        with open(config_file, "w") as f:
            f.write("rewrite:\n  review:\n    llm:\n      temperature: 0.5\n\n  bad indent\n")

        with pytest.raises(Exception) as exc_info:
            load_config(config_file)

        # Error should mention YAML parsing
        assert "YAML" in str(exc_info.value).upper() or "parse" in str(exc_info.value).lower()

    def test_invalid_temperature_value(self, tmp_path):
        """Test validation error for invalid temperature."""
        config_content = {
            "rewrite": {
                "review": {
                    "llm": {"temperature": 1.5}  # Invalid
                }
            }
        }

        config_file = tmp_path / "config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(config_content, f)

        with pytest.raises(ValueError) as exc_info:
            load_config(config_file)

        assert "temperature" in str(exc_info.value)

    def test_missing_profile_error(self, tmp_path):
        """Test error when specified profile doesn't exist."""
        config_content = {
            "rewrite": {
                "review": {
                    "profiles": {}
                }
            }
        }

        config_file = tmp_path / "config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(config_content, f)

        with pytest.raises(KeyError) as exc_info:
            load_config(config_file, profile="nonexistent")

        assert "nonexistent" in str(exc_info.value)

    def test_all_checks_disabled_error(self, tmp_path):
        """Test error when all checks are disabled."""
        config_content = {
            "rewrite": {
                "review": {
                    "checks": {
                        "security": False,
                        "performance": False,
                        "style": False
                    }
                }
            }
        }

        config_file = tmp_path / "config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(config_content, f)

        with pytest.raises(ValueError) as exc_info:
            load_config(config_file)

        assert "At least one check" in str(exc_info.value)
```

**Validation**:
- [ ] Missing file raises FileNotFoundError
- [ ] Invalid YAML raises parse error
- [ ] Invalid values raise ValueError
- [ ] Missing profile raises KeyError
- [ ] All checks disabled raises ValueError

## Files Created

- `tests/integration/test_review_config_workflow.py` (new, ~200 lines)
- `tests/fixtures/review_config/` (directory for test YAML files)

## Test Fixtures

Create `tests/fixtures/review_config/` directory with example configs:

```
tests/fixtures/review_config/
├── minimal.yaml          # Minimal config (defaults)
├── full_config.yaml      # Complete config with all options
├── profiles_only.yaml    # Config with only profiles defined
└── invalid.yaml          # Invalid YAML for error testing
```

## Test Execution

```bash
# Run integration tests
pytest tests/integration/test_review_config_workflow.py -v

# Run with verbose output
pytest tests/integration/test_review_config_workflow.py -vv -s
```

## Definition of Done

- [ ] Full load workflow tested with real YAML
- [ ] Profile application verified end-to-end
- [ ] CLI override tested with priority verification
- [ ] Invalid config handling tested
- [ ] All integration tests pass

## Reviewer Guidance

**Verify**:
1. Tests use tmp_path fixture for file isolation
2. Real YAML files are used (not mocks)
3. Error messages are asserted
4. Cleanup is done (env vars, temp files)

**Common Issues**:
- Not using tmp_path → Tests leave files behind
- Not cleaning env vars → Tests interfere with each other
- Not asserting error messages → Unclear what went wrong

## Risks

- **Low Risk**: Integration testing is straightforward
- **Mitigation**: Use pytest fixtures for file isolation
