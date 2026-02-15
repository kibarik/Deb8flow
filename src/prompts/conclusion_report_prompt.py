"""
Conclusion Report Prompt Module.

This module provides the conclusion report prompt for LLM-based conclusion generation.
"""

from typing import Optional
from pathlib import Path

# Read the markdown prompt file
PROMPT_PATH = Path(__file__).parent / "conclusion_report_prompt.md"


def get_conclusion_report_prompt(debate_type: str) -> str:
    """Get the conclusion report prompt for a given debate type.

    Args:
        debate_type: Type of debate ('standard', 'document', 'committee')

    Returns:
        Prompt text for LLM conclusion generation
    """
    with open(PROMPT_PATH, "r", encoding="utf-8") as f:
        prompt_template = f.read()

    # Add debate type context to the prompt
    type_context = {
        "standard": "standard AI debate",
        "document": "document-based debate",
        "committee": "committee meeting debate",
    }

    debate_context = type_context.get(debate_type, "debate")
    prompt = f"{prompt_template}\n\nDebate Type: {debate_context}"

    return prompt


def get_raw_prompt() -> str:
    """Get the raw prompt template without modifications.

    Returns:
        Raw prompt text from markdown file
    """
    with open(PROMPT_PATH, "r", encoding="utf-8") as f:
        return f.read()
