"""
MCP tool for analyzing Software Design Specifications (SDD) using multi-agent debate.

This tool integrates the debate engine to analyze design specifications
and identify weak points, recommendations, and unclear sections.
"""

import asyncio
import logging
import time
from pathlib import Path
from typing import Optional, Dict, Any, List

from langchain_openai import ChatOpenAI
from langchain_core.exceptions import OutputParserException

from src.mcp.models import (
    AnalyzeSpecInput,
    SDDAnalysisResult,
    WeakPoint,
    Recommendation,
    UnclearSection,
    AnalysisMetadata,
    AnalysisError
)
from src.shared.config.sdd_config_loader import load_sdd_config
from src.shared.debate.infrastructure.llm.factory import DebateOrchestratorFactory
from src.shared.debate.domain.entities import DebateMode
from src.shared.debate.application.prompt_loader import PromptLoader
from src.mcp.tools.result_parser import parse_debate_output_safe


logger = logging.getLogger(__name__)


class SDDAnalyzer:
    """
    Analyzer for Software Design Specifications using multi-agent debate.

    This class orchestrates the full analysis pipeline:
    1. Load SDD configuration
    2. Initialize debate orchestrator
    3. Run debate between Architect (PRO) and opponents (CON)
    4. Parse debate output to extract insights
    5. Return structured analysis results
    """

    # Maximum specification size
    MAX_SPEC_SIZE = 100_000  # characters

    # Chunking threshold
    CHUNK_THRESHOLD = 32_000  # characters (~8000 tokens)

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the SDD analyzer.

        Args:
            config_path: Optional path to sdd_config.yaml
        """
        self.config_path = config_path
        self.config = None
        self.prompt_loader = None
        self.orchestrator = None

    def _load_config(self) -> None:
        """Load SDD configuration from file."""
        try:
            self.config = load_sdd_config(self.config_path)
            logger.info(f"Loaded SDD config from: {self.config_path or 'default location'}")
        except FileNotFoundError as e:
            raise ValueError(f"SDD config file not found: {e}")
        except Exception as e:
            raise ValueError(f"Failed to load SDD config: {e}")

    def _create_prompt_loader(self) -> PromptLoader:
        """
        Create PromptLoader from SDD config.

        Returns:
            PromptLoader instance with configured prompts
        """
        # Convert SddPromptsConfig to PromptsConfig for PromptLoader
        from src.shared.config.models import PromptsConfig

        prompts_config = PromptsConfig(
            stages=self.config.prompts.stages,
            judge=self.config.prompts.judge,
            context=self.config.prompts.context,
            analysis=self.config.prompts.analysis,
            roles=self.config.prompts.roles
        )

        # Get project root for path resolution
        project_root = Path.cwd()

        return PromptLoader(prompts_config, base_path=project_root)

    def _create_orchestrator(self, detail_level: str):
        """
        Create debate orchestrator based on configuration.

        Args:
            detail_level: Analysis detail level (quick/thorough)

        Returns:
            Configured debate orchestrator
        """
        # Determine debate mode
        mode = DebateMode.STANDARD if detail_level == "thorough" else DebateMode.SIMPLE

        # Create orchestrator via factory
        self.orchestrator = DebateOrchestratorFactory.create(
            mode=mode,
            prompt_loader=self.prompt_loader,
            model=self.config.llm.model,
            temperature=self.config.llm.temperature,
            api_key=self.config.llm.api_key or None,
            base_url=self.config.llm.base_url or None,
            language=self.config.debate.language
        )

        logger.info(f"Created {mode.value} debate orchestrator with model {self.config.llm.model}")

    def _load_agent_prompt(self, prompt_path: str, agent_name: str) -> str:
        """
        Load agent prompt from file.

        Args:
            prompt_path: Path to agent prompt file
            agent_name: Name of the agent (for logging)

        Returns:
            Prompt content as string

        Raises:
            FileNotFoundError: If prompt file doesn't exist
        """
        try:
            path = Path(prompt_path)
            if not path.exists():
                logger.warning(f"Agent prompt not found for {agent_name}: {prompt_path}")
                return f"You are {agent_name}, analyzing a software design specification."

            content = path.read_text(encoding='utf-8')
            logger.info(f"Loaded agent prompt for {agent_name}: {len(content)} characters")
            return content

        except Exception as e:
            logger.error(f"Error loading agent prompt for {agent_name}: {e}")
            return f"You are {agent_name}, analyzing a software design specification."

    def _validate_input(self, input_data: AnalyzeSpecInput) -> str:
        """
        Validate input and return specification content.

        Args:
            input_data: Validated input model

        Returns:
            Specification content as string

        Raises:
            ValueError: If validation fails
        """
        input_data.validate_input()

        if input_data.spec_path:
            # Load from file
            spec_path = Path(input_data.spec_path)

            if not spec_path.exists():
                raise ValueError(f"Specification file not found: {input_data.spec_path}")

            if spec_path.suffix not in ['.md', '.txt']:
                raise ValueError(f"Specification file must be .md or .txt, got: {spec_path.suffix}")

            content = spec_path.read_text(encoding='utf-8')

            if len(content) > self.MAX_SPEC_SIZE:
                raise ValueError(
                    f"Specification too large: {len(content)} characters. "
                    f"Maximum is {self.MAX_SPEC_SIZE} characters."
                )

            if not content.strip():
                raise ValueError("Specification file is empty")

            logger.info(f"Loaded specification from {spec_path}: {len(content)} characters")
            return content

        else:
            # Use raw content
            content = input_data.spec_content

            if not content or not content.strip():
                raise ValueError("Specification content is empty")

            if len(content) > self.MAX_SPEC_SIZE:
                raise ValueError(
                    f"Specification too large: {len(content)} characters. "
                    f"Maximum is {self.MAX_SPEC_SIZE} characters."
                )

            logger.info(f"Using provided specification content: {len(content)} characters")
            return content

    async def analyze(self, input_data: AnalyzeSpecInput) -> SDDAnalysisResult:
        """
        Analyze a software design specification.

        Args:
            input_data: Analysis input parameters

        Returns:
            SDDAnalysisResult with analysis findings
        """
        start_time = time.time()

        try:
            # Step 1: Load configuration
            self._load_config()

            # Step 2: Validate input and get content
            spec_content = self._validate_input(input_data)

            # Step 3: Create prompt loader
            self.prompt_loader = self._create_prompt_loader()

            # Step 4: Create orchestrator
            self._create_orchestrator(input_data.detail_level)

            # Step 5: Load agent prompts
            # Main agent (Architect) as PRO
            pro_prompt_path = self.config.agents.main.prompt
            pro_prompt = self._load_agent_prompt(pro_prompt_path, self.config.agents.main.name)

            # Opponents (DevLead, QA, Security) as CON
            # Combine all opponent prompts into a single CON perspective
            opponent_prompts = []
            for opp in self.config.agents.opponents:
                opp_prompt = self._load_agent_prompt(opp.prompt, opp.name)
                opponent_prompts.append(f"## {opp.name}\n{opp_prompt}")

            con_prompt = "\n\n".join(opponent_prompts)

            # Step 6: Execute debate
            timeout = self.config.llm.timeout
            logger.info(f"Starting debate analysis: detail_level={input_data.detail_level}, mode={self.config.debate.mode}, timeout={timeout}s")

            # Get agent information for metadata
            agents_used = [self.config.agents.main.name] + [opp.name for opp in self.config.agents.opponents]

            # Execute debate with timeout
            try:
                dialogue, winner = await asyncio.wait_for(
                    self.orchestrator.execute_debate(
                        topic=f"{input_data.spec_type} Specification Analysis",
                        pro_prompt=pro_prompt,
                        con_prompt=con_prompt,
                        question=f"What are the weak points, risks, and areas for improvement in this {input_data.spec_type} specification?",
                        prd_content=spec_content
                    ),
                    timeout=timeout
                )

                # Log debate completion
                num_rounds = len([m for m in dialogue if m.get('stage') in ['opening', 'rebuttal', 'counter', 'final_argument']])
                logger.info(f"Debate analysis completed: {len(dialogue)} messages generated, {num_rounds} rounds, winner={winner}")

                debate_result = {
                    'dialogue': dialogue,
                    'winner': winner,
                    'num_rounds': num_rounds
                }
            except asyncio.TimeoutError:
                # Return partial result on timeout
                elapsed_ms = int((time.time() - start_time) * 1000)
                logger.warning(f"Debate analysis timed out after {timeout}s, returning partial result")

                return SDDAnalysisResult(
                    status="partial",
                    weak_points=[],
                    recommendations=[],
                    unclear_sections=[],
                    metadata=AnalysisMetadata(
                        model_used=self.config.llm.model,
                        agents_used=agents_used,
                        analysis_time_ms=elapsed_ms,
                        debate_mode=self.config.debate.mode,
                        num_rounds=0,
                        winner=None
                    ),
                    error=AnalysisError(
                        type="timeout",
                        message=f"Analysis timed out after {timeout}s",
                        recoverable=True,
                        suggestion="Try with 'quick' detail_level or smaller specification"
                    ),
                    partial_reason="timeout"
                )

            # Step 7: Parse debate output using result_parser
            logger.info("Parsing debate output...")
            parsed = parse_debate_output_safe(
                debate_result.get('dialogue', []),
                config=self.config.model_dump() if self.config else None
            )

            # Convert ParsedDebateResult to expected dict format
            parsed_dict = {
                'weak_points': parsed.weak_points,
                'recommendations': parsed.recommendations,
                'unclear_sections': parsed.unclear_sections
            }

            # Log any parse errors
            if parsed.parse_errors:
                logger.warning(f"Parse errors encountered: {parsed.parse_errors}")

            # Step 8: Build result
            elapsed_ms = int((time.time() - start_time) * 1000)

            return SDDAnalysisResult(
                status="success",
                weak_points=parsed_dict['weak_points'],
                recommendations=parsed_dict['recommendations'],
                unclear_sections=parsed_dict['unclear_sections'],
                metadata=AnalysisMetadata(
                    model_used=self.config.llm.model,
                    agents_used=agents_used,
                    analysis_time_ms=elapsed_ms,
                    debate_mode=self.config.debate.mode,
                    num_rounds=debate_result.get('num_rounds', 0),
                    winner=debate_result.get('winner')
                )
            )

        except ValueError as e:
            # Input validation error
            elapsed_ms = int((time.time() - start_time) * 1000)

            return SDDAnalysisResult(
                status="error",
                weak_points=[],
                recommendations=[],
                unclear_sections=[],
                metadata=AnalysisMetadata(
                    model_used="unknown",
                    agents_used=[],
                    analysis_time_ms=elapsed_ms,
                    debate_mode="unknown",
                    num_rounds=0
                ),
                error=AnalysisError(
                    type="validation",
                    message=str(e),
                    recoverable=False,
                    suggestion="Fix the input and try again"
                )
            )

        except Exception as e:
            # Unexpected error
            logger.exception(f"Unexpected error during analysis: {e}")
            elapsed_ms = int((time.time() - start_time) * 1000)

            # Determine if error is recoverable
            error_type = type(e).__name__
            recoverable = error_type in ['TimeoutError', 'RateLimitError', 'ConnectionError']

            return SDDAnalysisResult(
                status="error",
                weak_points=[],
                recommendations=[],
                unclear_sections=[],
                metadata=AnalysisMetadata(
                    model_used=self.config.llm.model if self.config else "unknown",
                    agents_used=[],
                    analysis_time_ms=elapsed_ms,
                    debate_mode=self.config.debate.mode if self.config else "unknown",
                    num_rounds=0
                ),
                error=AnalysisError(
                    type="unknown",
                    message=f"{error_type}: {str(e)}",
                    recoverable=recoverable,
                    suggestion="Retry if recoverable, otherwise check configuration"
                )
            )


async def analyze_specification(
    spec_path: Optional[str] = None,
    spec_content: Optional[str] = None,
    spec_type: str = "SDD",
    focus_areas: Optional[List[str]] = None,
    detail_level: str = "thorough",
    config_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Analyze a software design specification using multi-agent debate.

    This is the main entry point for the MCP tool. It runs a debate between
    Architect (PRO) and DevLead/QA/Security (CON) to identify weak points,
    recommendations, and unclear sections in the specification.

    Args:
        spec_path: Path to specification file (.md or .txt)
        spec_content: Raw specification content (alternative to spec_path)
        spec_type: Type of specification (PRD, SDD, TDD, UNKNOWN)
        focus_areas: Optional list of focus areas for analysis
        detail_level: Analysis detail level ('quick' or 'thorough')
        config_path: Optional path to sdd_config.yaml

    Returns:
        Dictionary with analysis results matching SDDAnalysisResult schema

    Example:
        >>> result = await analyze_specification(
        ...     spec_path="docs/spec.md",
        ...     detail_level="thorough"
        ... )
        >>> print(result['status'])
        success
        >>> print(result['metadata']['analysis_time_ms'])
        45000
    """
    # Create input model
    input_data = AnalyzeSpecInput(
        spec_path=spec_path,
        spec_content=spec_content,
        spec_type=spec_type,
        focus_areas=focus_areas,
        detail_level=detail_level,
        config_path=config_path
    )

    # Create analyzer
    analyzer = SDDAnalyzer(config_path=config_path)

    # Run analysis
    result = await analyzer.analyze(input_data)

    # Return as dictionary
    return result.model_dump()
