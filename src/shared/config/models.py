"""Configuration models for debate system.

This module provides Pydantic models for validating prompt configuration
and debate settings.
"""

from pathlib import Path
from typing import Dict, Optional, List, Any
from pydantic import BaseModel, Field, field_validator


class PromptPathsConfig(BaseModel):
    """Configuration for prompt file paths."""

    stages: Dict[str, str] = Field(default_factory=dict)
    judge: str
    context: str
    analysis: Dict[str, str] = Field(default_factory=dict)
    roles: Optional[Dict[str, str]] = None

    @field_validator('stages')
    @classmethod
    def validate_required_stages(cls, v: Dict[str, str]) -> Dict[str, str]:
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

    @field_validator('judge', 'context', mode='before')
    @classmethod
    def validate_path_not_empty(cls, v: str) -> str:
        """Validate that file paths are not empty."""
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


class DebateModeConfig(BaseModel):
    """Debate mode configuration."""

    mode: str = Field(default="standard")
    max_retries: int = Field(default=2, ge=0, le=10)
    max_concurrency: int = Field(default=0, ge=0)
    language: str = Field(default="en")

    @field_validator('mode')
    @classmethod
    def validate_mode(cls, v: str) -> str:
        """Ensure mode is either standard or simple."""
        valid_modes = ['standard', 'simple']
        if v not in valid_modes:
            raise ValueError(f"Invalid debate mode: {v}. Must be one of {valid_modes}")
        return v


class LLMConfigModel(BaseModel):
    """LLM provider configuration."""

    base_url: Optional[str] = None
    model: str = "gpt-4o"
    api_key: Optional[str] = None
    temperature: float = Field(default=0.8, ge=0.0, le=2.0)
    max_tokens: int = Field(default=1500, ge=1)
    timeout: int = Field(default=60, ge=1)


class AgentsConfigModel(BaseModel):
    """Agent configuration."""

    main: Dict[str, str]
    opponents: List[Dict[str, str]] = Field(default_factory=list)


class DebateConfigFull(BaseModel):
    """Full debate configuration."""

    llm: LLMConfigModel
    debate: DebateModeConfig
    agents: AgentsConfigModel
    prompts: PromptsConfig
    output: Optional[Dict[str, Any]] = None
    logging: Optional[Dict[str, Any]] = None
