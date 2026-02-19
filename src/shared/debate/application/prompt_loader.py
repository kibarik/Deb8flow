"""PromptLoader service for loading and rendering prompt templates."""

import logging
import re
from pathlib import Path
from typing import Dict, Optional, Any, List
from dataclasses import dataclass, field
from threading import Lock

from shared.config.models import PromptsConfig


logger = logging.getLogger(__name__)


@dataclass
class PromptContext:
    """Context variables for prompt template rendering."""

    question: str
    topic: str = ""
    prd_content: str = ""
    language: str = "en"
    recent_context: str = ""
    pro_prompt: str = ""
    con_prompt: str = ""
    dialogue_summary: str = ""
    verdict_explanation: str = ""
    winner: str = ""
    min_takeaways: int = 3
    max_takeaways: int = 10

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for template rendering."""
        return {
            "question": self.question,
            "topic": self.topic,
            "prd_content": self.prd_content,
            "language": self.language,
            "recent_context": self.recent_context,
            "pro_prompt": self.pro_prompt,
            "con_prompt": self.con_prompt,
            "dialogue_summary": self.dialogue_summary,
            "verdict_explanation": self.verdict_explanation,
            "winner": self.winner,
            "min_takeaways": self.min_takeaways,
            "max_takeaways": self.max_takeaways,
        }


@dataclass
class ValidationResult:
    """Result of prompt validation."""

    is_valid: bool
    prompt_id: str
    missing_variables: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


class PromptLoader:
    """
    Service for loading, caching, and rendering prompt templates.

    Features:
    - Loads prompts from files
    - Caches templates in memory
    - Validates template variables
    - Renders templates with context substitution
    - Thread-safe operations
    """

    # Required template variables by prompt type
    REQUIRED_VARS = {
        "debate.stages.opening_pro": ["question", "topic"],
        "debate.stages.opening_con": ["question", "topic"],
        "debate.stages.rebuttal_pro": ["question", "recent_context"],
        "debate.stages.rebuttal_con": ["question", "recent_context"],
        "debate.stages.counter_pro": ["question", "recent_context"],
        "debate.stages.counter_con": ["question", "recent_context"],
        "debate.stages.final_pro": ["question", "recent_context"],
        "debate.stages.final_con": ["question", "recent_context"],
        "debate.judge": ["question", "recent_context"],
        "debate.context": ["question", "topic", "prd_content", "language"],
        "analysis.takeaway": ["question", "dialogue_summary", "min_takeaways", "max_takeaways"],
    }

    def __init__(self, config: PromptsConfig, base_path: Path = None):
        """
        Initialize the PromptLoader.

        Args:
            config: Prompt configuration with file paths
            base_path: Base path for resolving relative file paths (default: current working directory)
        """
        self.config = config
        self.base_path = base_path or Path.cwd()
        self._cache: Dict[str, str] = {}
        self._lock = Lock()

        # Preload all prompts on initialization
        self._load_all_prompts()

    def _load_all_prompts(self) -> None:
        """Load all prompts into cache."""
        logger.info("Loading prompts into cache...")

        # Load stage prompts
        for stage_name, path in self.config.stages.items():
            prompt_id = f"debate.stages.{stage_name}"
            self._load_file(prompt_id, path)

        # Load judge prompt
        self._load_file("debate.judge", self.config.judge)
        self._load_file("debate.context", self.config.context)

        # Load analysis prompts
        for analysis_type, path in self.config.analysis.items():
            prompt_id = f"analysis.{analysis_type}"
            self._load_file(prompt_id, path)

        # Load role prompts if configured
        if self.config.roles:
            for role_name, path in self.config.roles.items():
                prompt_id = f"roles.{role_name}"
                self._load_file(prompt_id, path)

        logger.info(f"Loaded {len(self._cache)} prompts into cache")

    def _load_file(self, prompt_id: str, file_path: str) -> None:
        """
        Load a single prompt file into cache.

        Args:
            prompt_id: Unique identifier for the prompt
            file_path: Path to the prompt file

        Raises:
            FileNotFoundError: If the file doesn't exist
            ValueError: If the file is empty
        """
        path = self._resolve_path(file_path)

        if not path.exists():
            # Try fallback to old location
            old_path = self._resolve_path(file_path.replace("src/prompts", "config/prompts"))
            if old_path.exists():
                logger.warning(f"Using deprecated path for {prompt_id}: {old_path}")
                path = old_path
            else:
                raise FileNotFoundError(f"Prompt file not found: {path}")

        content = path.read_text(encoding='utf-8').strip()

        if not content:
            raise ValueError(f"Prompt file is empty: {path}")

        with self._lock:
            self._cache[prompt_id] = content

        logger.debug(f"Loaded prompt: {prompt_id} from {path}")

    def _resolve_path(self, file_path: str) -> Path:
        """Resolve a file path relative to base path."""
        path = Path(file_path)
        if not path.is_absolute():
            path = self.base_path / path
        return path

    def load(self, prompt_id: str) -> str:
        """
        Load a prompt template from cache.

        Args:
            prompt_id: Unique identifier for the prompt (e.g., "debate.context")

        Returns:
            The prompt template string

        Raises:
            KeyError: If the prompt_id is not found
        """
        if prompt_id not in self._cache:
            available = list(self._cache.keys())
            raise KeyError(
                f"Prompt not found: {prompt_id}. "
                f"Available prompts: {available}"
            )

        return self._cache[prompt_id]

    def load_with_context(self, prompt_id: str, context: PromptContext) -> str:
        """
        Load and render a prompt template with context variables.

        Args:
            prompt_id: Unique identifier for the prompt
            context: Context variables for template rendering

        Returns:
            The rendered prompt with variables substituted

        Raises:
            KeyError: If the prompt_id is not found
            ValueError: If a required variable is missing from context
        """
        template = self.load(prompt_id)
        return self._render_template(template, context.to_dict())

    def _render_template(self, template: str, context: Dict[str, Any]) -> str:
        """
        Render a template with variable substitution.

        Uses Python's str.format() for simple variable substitution.
        Variables are specified as {variable_name} in templates.

        Args:
            template: The template string with {variable} placeholders
            context: Dictionary of variable names to values

        Returns:
            The rendered template with variables substituted

        Raises:
            ValueError: If a required variable is missing from context
        """
        try:
            return template.format(**context)
        except KeyError as e:
            missing_var = str(e).strip("'")
            raise ValueError(
                f"Missing required variable '{missing_var}' in context. "
                f"Template requires: {self._extract_variables(template)}"
            )

    def _extract_variables(self, template: str) -> List[str]:
        """Extract all variable names from a template."""
        return re.findall(r'\{([^}]+)\}', template)

    def validate(self, prompt_id: str) -> ValidationResult:
        """
        Validate a prompt template.

        Checks that:
        - Prompt exists in cache
        - Template is well-formed
        - Required variables are present (if configured)

        Args:
            prompt_id: Unique identifier for the prompt

        Returns:
            ValidationResult with validation status and any errors
        """
        errors = []
        missing_vars = []

        try:
            template = self.load(prompt_id)
            variables = set(self._extract_variables(template))

            # Check required variables if configured
            if prompt_id in self.REQUIRED_VARS:
                required = set(self.REQUIRED_VARS[prompt_id])
                missing = required - variables
                if missing:
                    missing_vars = list(missing)
                    errors.append(f"Missing required variables: {missing}")

        except KeyError as e:
            errors.append(str(e))
        except Exception as e:
            errors.append(f"Validation error: {e}")

        return ValidationResult(
            is_valid=len(errors) == 0,
            prompt_id=prompt_id,
            missing_variables=missing_vars,
            errors=errors
        )

    def reload(self) -> None:
        """
        Reload all prompts from disk.

        Clears the cache and reloads all prompts.
        Useful for development when prompts are being edited.
        """
        logger.info("Reloading prompts...")
        with self._lock:
            self._cache.clear()
        self._load_all_prompts()
        logger.info("Prompts reloaded")

    def get_cached_prompt_ids(self) -> List[str]:
        """Get list of all cached prompt IDs."""
        return list(self._cache.keys())


def create_prompt_loader(config: PromptsConfig, base_path: Path = None) -> PromptLoader:
    """
    Factory function to create a PromptLoader instance.

    Args:
        config: Prompt configuration
        base_path: Base path for resolving relative file paths

    Returns:
        Configured PromptLoader instance
    """
    return PromptLoader(config, base_path)
