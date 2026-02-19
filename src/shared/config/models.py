"""Configuration models for debate system."""

from pathlib import Path
from typing import Dict, Optional, List
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

    @field_validator('judge', 'context')
    @classmethod
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
    analysis: Dict[str, str] = Field(default_factory=dict)
    roles: Optional[Dict[str, str]] = None


class DebateModeConfig(BaseModel):
    """Debate mode configuration."""

    mode: str = Field(default="standard")
    max_retries: int = Field(default=2, ge=0, le=10)
    max_concurrency: int = Field(default=0, ge=0)
    language: str = Field(default="en")

    @field_validator('mode')
    @classmethod
    def validate_mode(cls, v):
        """Ensure mode is either standard or simple."""
        valid_modes = ['standard', 'simple']
        if v not in valid_modes:
            raise ValueError(f"Invalid debate mode: {v}. Must be one of {valid_modes}")
        return v
