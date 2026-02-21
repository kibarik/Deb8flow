"""
LLM-based Debate Orchestrator

This module provides real AI-powered debate execution using LangChain
and OpenAI-compatible APIs.
"""

import asyncio
import json
import logging
import sys
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from ...application.prompt_loader import PromptLoader, PromptContext


logger = logging.getLogger(__name__)


class DebateMessage:
    """A single message in a debate."""

    def __init__(self, speaker: str, content: str, stage: str, validated: bool = False):
        self.speaker = speaker
        self.content = content
        self.stage = stage
        self.timestamp = datetime.now(timezone.utc).isoformat()
        self.validated = validated

    def to_dict(self) -> Dict[str, Any]:
        return {
            "speaker": self.speaker,
            "content": self.content,
            "stage": self.stage,
            "timestamp": self.timestamp,
            "validated": self.validated
        }


class LLMDebateOrchestrator:
    """
    Orchestrates AI-powered debates between PRO and CON participants.

    This class manages the full debate lifecycle:
    1. Opening statements (PRO and CON)
    2. Rebuttals
    3. Counter-arguments
    4. Final arguments
    5. Judge's verdict
    """

    DEBATE_STAGES = [
        "opening",
        "rebuttal",
        "counter",
        "final_argument",
        "verdict"
    ]

    def __init__(
        self,
        prompt_loader=None,  # Optional PromptLoader
        model: Optional[str] = None,
        fallback_models: Optional[list[str]] = None,
        temperature: float = 0.7,
        max_tokens: int = 5000,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        language: str = "en",
        room_id: Optional[str] = None,  # For logging
        json_output_path: Optional[Path] = None  # For progressive saving
    ):
        """
        Initialize the debate orchestrator.

        Args:
            prompt_loader: PromptLoader for loading prompts (optional, for backward compatibility)
            model: Primary model name (e.g., "gpt-4o", "gpt-3.5-turbo")
            fallback_models: List of fallback models to try on rate limits
            temperature: Sampling temperature for creativity
            max_tokens: Maximum tokens per response
            api_key: OpenAI API key (or compatible)
            base_url: Custom API base URL for compatible APIs
            language: Language code for debate output (e.g., "en", "ru", "de")
            room_id: Room identifier for logging (optional)
            json_output_path: Path to save progressive JSON state (optional)
        """
        self.prompt_loader = prompt_loader  # Store PromptLoader (may be None)
        self.primary_model = model or "gpt-4o"
        self.fallback_models = fallback_models or []
        self.all_models = [self.primary_model] + self.fallback_models
        self.current_model_index = 0  # Start with primary model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.language = language
        self.room_id = room_id or "Debate"
        self.json_output_path = json_output_path
        self.api_key = api_key
        self.base_url = base_url

        # Initialize LLM with primary model
        self.llm = self._create_llm(self.primary_model)

        # Debate history
        self.messages: List[DebateMessage] = []
        self._current_stage = 0
        self._total_stages = 9  # 8 debate stages + verdict

    def _create_llm(self, model: str) -> ChatOpenAI:
        """Create a ChatOpenAI instance for the given model."""
        llm_kwargs = {
            "model": model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "max_retries": 0,  # Disable built-in retry - we handle retries at orchestration level
        }

        if self.api_key:
            llm_kwargs["api_key"] = self.api_key
        if self.base_url:
            llm_kwargs["base_url"] = self.base_url

        return ChatOpenAI(**llm_kwargs)

    def _switch_to_next_model(self) -> bool:
        """Switch to next available model. Returns True if successful, False if no more models."""
        if self.current_model_index + 1 < len(self.all_models):
            self.current_model_index += 1
            new_model = self.all_models[self.current_model_index]
            self.llm = self._create_llm(new_model)
            print(f"  ⚠️ Switching to fallback model: {new_model}", file=sys.stderr, flush=True)
            return True
        return False

    @property
    def model(self) -> str:
        """Get current model name."""
        return self.all_models[self.current_model_index]

    def _log_stage(self, stage_name: str, speaker: str, action: str = "generating"):
        """Log debate stage progress to stderr for realtime feedback."""
        stage_symbols = ["⚪", "🟡", "🟠", "🔴", "🟤", "🔵", "🟣", "⚫", "🟢"]
        symbol = stage_symbols[self._current_stage % len(stage_symbols)]
        print(f"{symbol} [{self.room_id}] Stage {self._current_stage + 1}/{self._total_stages}: {speaker} - {stage_name} ({action})...", file=sys.stderr, flush=True)

    def _log_completed(self, message: str):
        """Log completion message to stderr for realtime feedback."""
        print(f"  ✓ {message}", file=sys.stderr, flush=True)

    async def _save_progressive_state(self, winner: Optional[str] = None):
        """Save current debate state to JSON file for progressive saving.

        Args:
            winner: Optional winner string if verdict is complete

        Note:
            Errors during saving are logged but DO NOT fail the debate.
            The debate result (winner, messages) is still returned to the caller
            even if saving fails. This prevents losing completed debates due to
            disk space issues.
        """
        if not self.json_output_path:
            return

        try:
            # Create output data with current state
            output_data = {
                "messages": [msg.to_dict() for msg in self.messages],
                "winner": winner,  # Will be None until verdict stage
                "stage": f"{self._current_stage}/{self._total_stages}",
                "in_progress": winner is None  # True if debate still ongoing
            }

            # Ensure parent directory exists
            self.json_output_path.parent.mkdir(parents=True, exist_ok=True)

            # Write to temp file first, then move (atomic operation)
            # Use asyncio.to_thread to ensure synchronous operations complete
            import shutil

            temp_path = self.json_output_path.with_suffix('.tmp')

            # Write and flush synchronously to ensure data is on disk
            await asyncio.to_thread(
                temp_path.write_text,
                json.dumps(output_data, indent=2, ensure_ascii=False),
                encoding="utf-8"
            )

            # Move atomically (ensuring data is persisted)
            await asyncio.to_thread(
                shutil.move,
                str(temp_path),
                str(self.json_output_path)
            )

            # Verify the file was written (read back to confirm)
            verification = await asyncio.to_thread(
                self.json_output_path.read_text,
                encoding="utf-8"
            )
            if not verification:
                logger.warning(f"Verification failed: JSON file appears empty after write")

            # Log successful save with current stage for debugging
            stage_symbols = ["⚪", "🟡", "🟠", "🔴", "🟤", "🔵", "🟣", "⚫", "🟢"]
            symbol = stage_symbols[min(self._current_stage, len(stage_symbols) - 1)]
            print(f"{symbol} [{self.room_id}] Stage {self._current_stage}/{self._total_stages} - json_updated - {self.json_output_path}", file=sys.stderr, flush=True)
            logger.debug(f"Progressive state saved: stage {self._current_stage}/{self._total_stages}, messages: {len(self.messages)}")

        except OSError as e:
            # Specifically handle disk space errors
            if e.errno == 28:  # ENOSPC - No space left on device
                logger.error(f"Disk full - cannot save debate state to {self.json_output_path}. Debate will continue without saving.")
            else:
                logger.warning(f"OS error saving progressive state: {e}")
        except Exception as e:
            # Don't fail the debate if saving fails
            logger.warning(f"Failed to save progressive state: {e}")

    async def execute_debate(
        self,
        topic: str,
        pro_prompt: str,
        con_prompt: str,
        question: str,
        prd_content: str
    ) -> Tuple[List[Dict[str, Any]], str]:
        """
        Execute a full debate between PRO and CON participants.

        Args:
            topic: The debate topic/context
            pro_prompt: System prompt for PRO debater
            con_prompt: System prompt for CON debater
            question: The specific question to debate
            prd_content: Full PRD content for context

        Returns:
            Tuple of (dialogue as list of dicts, winner)
        """
        self.messages = []

        # Build context for the debate
        debate_context = self._build_debate_context(topic, question, prd_content)

        try:
            # Stage 1: Opening statements
            await self._run_opening_statements(debate_context, pro_prompt, con_prompt)

            # Stage 2: Rebuttals
            await self._run_rebuttals(debate_context, pro_prompt, con_prompt)

            # Stage 3: Counter-arguments
            await self._run_counter_arguments(debate_context, pro_prompt, con_prompt)

            # Stage 4: Final arguments
            await self._run_final_arguments(debate_context, pro_prompt, con_prompt)

            # Stage 5: Judge's verdict
            winner = await self._run_verdict(debate_context)

            return [msg.to_dict() for msg in self.messages], winner

        except Exception as e:
            logger.error(f"Debate execution failed: {e}")
            raise

    def _build_debate_context(self, topic: str, question: str, prd_content: str) -> str:
        """Build the context string for the debate using PromptLoader."""
        # Get language instruction
        language_instruction = self._get_language_instruction()

        # Load context template and render with variables if PromptLoader is available
        if self.prompt_loader:
            try:
                context = self.prompt_loader.load_with_context(
                    "debate.context",
                    PromptContext(
                        question=question,
                        topic=topic[:500],  # Truncate as before
                        prd_content=prd_content[:2000],  # Truncate as before
                        language=language_instruction
                    )
                )
                return context
            except Exception as e:
                logger.warning(f"Failed to load context from PromptLoader: {e}, using fallback")

        # Fallback to hardcoded context
        return f"""{language_instruction}

Question: {question}

Topic/Context:
{topic[:500]}

PRD Content:
{prd_content[:2000]}
"""

    def _get_language_instruction(self) -> str:
        """Get language instruction string."""
        language_instructions = {
            "ru": "Вы должны вести дебаты на РУССКОМ языке. All responses must be in Russian.",
            "en": "You must conduct the debate in ENGLISH.",
            "de": "Sie müssen die Debatte auf DEUTSCH führen.",
            "fr": "Vous devez mener le débat en FRANÇAIS.",
            "es": "Debe realizar el debate en ESPAÑOL.",
            "zh": "您必须用中文进行辩论。",
        }
        return language_instructions.get(
            self.language.lower(),
            f"You must conduct the debate in {self.language.upper()}."
        )

    async def _run_opening_statements(self, context: str, pro_prompt: str, con_prompt: str):
        """Run opening statements from both sides using PromptLoader."""
        # Build base context for rendering
        base_context = PromptContext(
            question=context.split("Question:")[-1].strip() if "Question:" in context else "",
            topic=context.split("Topic/Context:")[-1].strip() if "Topic/Context:" in context else context,
            language=self.language
        )

        # PRO opening
        self._current_stage = 1
        if self.prompt_loader:
            try:
                pro_template = self.prompt_loader.load_with_context(
                    "debate.stages.opening_pro",
                    base_context
                )
            except Exception as e:
                logger.warning(f"Failed to load PRO opening prompt: {e}, using context")
                pro_template = context
        else:
            pro_template = context

        pro_response = await self._generate_response(
            system_prompt=pro_prompt,
            human_prompt=pro_template,
            stage="opening",
            speaker="PRO"
        )
        self.messages.append(DebateMessage("PRO", pro_response, "opening", validated=True))
        await self._save_progressive_state()  # Save after PRO opening

        # CON opening
        self._current_stage = 2
        if self.prompt_loader:
            try:
                con_template = self.prompt_loader.load_with_context(
                    "debate.stages.opening_con",
                    base_context
                )
            except Exception as e:
                logger.warning(f"Failed to load CON opening prompt: {e}, using context")
                con_template = context
        else:
            con_template = context

        con_response = await self._generate_response(
            system_prompt=con_prompt,
            human_prompt=con_template,
            stage="opening",
            speaker="CON"
        )
        self.messages.append(DebateMessage("CON", con_response, "opening", validated=True))
        await self._save_progressive_state()  # Save after CON opening

    async def _run_rebuttals(self, context: str, pro_prompt: str, con_prompt: str):
        """Run rebuttal stage."""
        # Get recent messages for context
        recent_context = self._get_recent_context()

        # CON rebuttal (responds to PRO's opening)
        self._current_stage = 3
        con_rebuttal = await self._generate_response(
            system_prompt=con_prompt,
            human_prompt=f"{context}\n\n{recent_context}\n\nNow provide your rebuttal to the PRO's opening statement. Address their specific points and explain why you disagree.",
            stage="rebuttal",
            speaker="CON"
        )
        self.messages.append(DebateMessage("CON", con_rebuttal, "rebuttal", validated=True))
        await self._save_progressive_state()  # Save after CON rebuttal

        # PRO rebuttal
        self._current_stage = 4
        recent_context = self._get_recent_context()
        pro_rebuttal = await self._generate_response(
            system_prompt=pro_prompt,
            human_prompt=f"{context}\n\n{recent_context}\n\nNow provide your rebuttal to the CON's opening statement and rebuttal. Address their specific concerns.",
            stage="rebuttal",
            speaker="PRO"
        )
        self.messages.append(DebateMessage("PRO", pro_rebuttal, "rebuttal", validated=True))
        await self._save_progressive_state()  # Save after PRO rebuttal

    async def _run_counter_arguments(self, context: str, pro_prompt: str, con_prompt: str):
        """Run counter-argument stage."""
        recent_context = self._get_recent_context()

        # PRO counter
        self._current_stage = 5
        pro_counter = await self._generate_response(
            system_prompt=pro_prompt,
            human_prompt=f"{context}\n\n{recent_context}\n\nNow provide a counter-argument. Offer new perspectives or evidence that strengthens your position while directly addressing the opponent's latest points.",
            stage="counter",
            speaker="PRO"
        )
        self.messages.append(DebateMessage("PRO", pro_counter, "counter", validated=True))
        await self._save_progressive_state()  # Save after PRO counter

        # CON counter
        self._current_stage = 6
        recent_context = self._get_recent_context()
        con_counter = await self._generate_response(
            system_prompt=con_prompt,
            human_prompt=f"{context}\n\n{recent_context}\n\nNow provide a counter-argument. Offer new perspectives or evidence that strengthens your position while directly addressing the opponent's latest points.",
            stage="counter",
            speaker="CON"
        )
        self.messages.append(DebateMessage("CON", con_counter, "counter", validated=True))
        await self._save_progressive_state()  # Save after CON counter

    async def _run_final_arguments(self, context: str, pro_prompt: str, con_prompt: str):
        """Run final argument stage."""
        recent_context = self._get_recent_context()

        # PRO final
        self._current_stage = 7
        pro_final = await self._generate_response(
            system_prompt=pro_prompt,
            human_prompt=f"{context}\n\n{recent_context}\n\nThis is your final argument. Summarize your strongest points and explain why your position should prevail. Be compelling but fair.",
            stage="final_argument",
            speaker="PRO"
        )
        self.messages.append(DebateMessage("PRO", pro_final, "final_argument", validated=True))
        await self._save_progressive_state()  # Save after PRO final

        # CON final
        self._current_stage = 8
        recent_context = self._get_recent_context()
        con_final = await self._generate_response(
            system_prompt=con_prompt,
            human_prompt=f"{context}\n\n{recent_context}\n\nThis is your final argument. Summarize your strongest points and explain why your position should prevail. Be compelling but fair.",
            stage="final_argument",
            speaker="CON"
        )
        self.messages.append(DebateMessage("CON", con_final, "final_argument", validated=True))
        await self._save_progressive_state()  # Save after CON final

    async def _run_verdict(self, context: str) -> str:
        """Run the judge's verdict using PromptLoader."""
        recent_context = self._get_recent_context()

        # Load judge template
        question = context.split("Question:")[-1].strip() if "Question:" in context else ""

        self._current_stage = 9

        if self.prompt_loader:
            try:
                judge_template = self.prompt_loader.load_with_context(
                    "debate.judge",
                    PromptContext(
                        question=question,
                        recent_context=recent_context,
                        language=self.language
                    )
                )
            except Exception as e:
                logger.warning(f"Failed to load judge prompt: {e}, using fallback")
                judge_template = f"""Evaluate the following debate and declare a winner.

Question: {question}

{recent_context}

Provide your verdict with:
1. Analysis of both sides' arguments
2. A clear declaration of "WINNER: PRO" or "WINNER: CON"
3. Brief reasoning for your decision"""
        else:
            judge_template = f"""Evaluate the following debate and declare a winner.

Question: {question}

{recent_context}

Provide your verdict with:
1. Analysis of both sides' arguments
2. A clear declaration of "WINNER: PRO" or "WINNER: CON"
3. Brief reasoning for your decision"""

        verdict = await self._generate_response(
            system_prompt=judge_template,
            human_prompt=f"Based on the debate above, provide your verdict.",
            stage="verdict",
            speaker="JUDGE"
        )
        self.messages.append(DebateMessage("JUDGE", verdict, "verdict", validated=True))

        # Extract winner from verdict
        if "WINNER: PRO" in verdict.upper():
            winner = "PRO"
        elif "WINNER: CON" in verdict.upper():
            winner = "CON"
        else:
            # Try to determine from context
            if "pro wins" in verdict.lower() or "proposition wins" in verdict.lower():
                winner = "PRO"
            elif "con wins" in verdict.lower() or "opposition wins" in verdict.lower():
                winner = "CON"
            # Default to PRO if unclear
            winner = "PRO"

        # Save final state with winner
        await self._save_progressive_state(winner=winner)

        return winner

    def _get_recent_context(self) -> str:
        """Get recent debate messages for context."""
        recent = self.messages[-4:] if len(self.messages) > 4 else self.messages
        context_parts = []
        for msg in recent:
            context_parts.append(f"{msg.speaker}: {msg.content}")
        return "\n\n".join(context_parts)

    async def _generate_response(
        self,
        system_prompt: str,
        human_prompt: str,
        stage: str,
        speaker: str
    ) -> str:
        """Generate a response using the LLM with fallback to other models on rate limits."""
        max_model_attempts = len(self.all_models)

        for attempt in range(max_model_attempts):
            try:
                messages = [
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=human_prompt)
                ]

                # Estimate request tokens (rough approximation: 1 token ~= 4 chars)
                request_text = system_prompt + human_prompt
                estimated_req_tokens = len(request_text) // 4

                # Normalize stage name for display (uppercase, replace final_argument with FINAL)
                stage_display = stage.upper().replace("FINAL_ARGUMENT", "FINAL")

                # Log request tokens BEFORE API call
                stage_symbols = ["⚪", "🟡", "🟠", "🔴", "🟤", "🔵", "🟣", "⚫", "🟢"]
                symbol = stage_symbols[self._current_stage % len(stage_symbols)]
                # For verdict (stage 9), display stage 9, not 10
                display_stage = self._current_stage if self._current_stage == 9 else self._current_stage + 1
                print(f"{symbol} [{self.room_id}] Stage {display_stage}/{self._total_stages} - {speaker} - {stage_display} - {self.model} - {estimated_req_tokens} req/tokens", file=sys.stderr, flush=True)

                response = await asyncio.to_thread(
                    self.llm.invoke,
                    messages
                )

                content = response.content.strip()
                logger.debug(f"{speaker} ({stage}): {content[:100]}...")

                # Extract response tokens from LangChain response metadata
                res_tokens = 0
                if hasattr(response, 'response_metadata'):
                    # Check for OpenAI format usage
                    if 'usage' in response.response_metadata:
                        usage = response.response_metadata['usage']
                        if isinstance(usage, dict):
                            res_tokens = usage.get('completion_tokens', 0)
                if hasattr(response, 'usage_metadata'):
                    # LangChain's usage_metadata
                    res_tokens = response.usage_metadata.get('output_tokens', 0) or response.usage_metadata.get('completion_tokens', 0)

                # Fallback: estimate from response content
                if res_tokens == 0:
                    res_tokens = len(content) // 4

                # Log response tokens AFTER API call
                # For verdict (stage 9), display stage 9, not 10
                display_stage = self._current_stage if self._current_stage == 9 else self._current_stage + 1
                print(f"{symbol} [{self.room_id}] Stage {display_stage}/{self._total_stages} - {speaker} - {stage_display} - {self.model} - {res_tokens} res/tokens", file=sys.stderr, flush=True)

                # Successfully generated response
                if attempt > 0:
                    print(f"  ✓ Generated using model: {self.model}", file=sys.stderr, flush=True)

                return content

            except Exception as e:
                error_str = str(e).lower()

                # Check if this is a rate limit error (429)
                is_rate_limit = (
                    "429" in error_str or
                    "rate limit" in error_str or
                    "resource exhausted" in error_str
                )

                if is_rate_limit and self._switch_to_next_model():
                    # Try next model
                    logger.warning(f"Rate limit hit for {self.all_models[self.current_model_index - 1]}, switching to {self.model}")
                    continue
                else:
                    # Not a rate limit or no more models - fail
                    logger.error(f"Error generating response for {speaker} at {stage}: {e}")
                    raise

        # All models failed
        raise RuntimeError(f"Failed to generate response for {speaker} at {stage} after trying all models")


class SimpleDebateOrchestrator:
    """
    Simplified debate orchestrator using a single LLM call per stage.

    This is more efficient than the full orchestrator but still provides
    realistic AI-generated debates.
    """

    def __init__(
        self,
        prompt_loader=None,  # Optional PromptLoader
        model: Optional[str] = None,
        fallback_models: Optional[list[str]] = None,
        temperature: float = 0.8,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        language: str = "en",
        json_output_path: Optional[Path] = None  # For compatibility (not used in simple mode)
    ):
        """Initialize the simple debate orchestrator."""
        self.prompt_loader = prompt_loader  # Store PromptLoader (may be None)
        self.primary_model = model or "gpt-4o"
        self.fallback_models = fallback_models or []
        self.all_models = [self.primary_model] + self.fallback_models
        self.current_model_index = 0  # Start with primary model
        self.temperature = temperature
        self.language = language
        self.json_output_path = json_output_path  # Stored for compatibility
        self.api_key = api_key
        self.base_url = base_url

        self.llm = self._create_llm(self.primary_model)

    def _create_llm(self, model: str) -> ChatOpenAI:
        """Create a ChatOpenAI instance for the given model."""
        llm_kwargs = {
            "model": model,
            "temperature": self.temperature,
            "max_tokens": 5000,
            "max_retries": 0,  # Disable built-in retry - we handle retries at orchestration level
        }

        if self.api_key:
            llm_kwargs["api_key"] = self.api_key
        if self.base_url:
            llm_kwargs["base_url"] = self.base_url

        return ChatOpenAI(**llm_kwargs)

    def _switch_to_next_model(self) -> bool:
        """Switch to next available model. Returns True if successful, False if no more models."""
        if self.current_model_index + 1 < len(self.all_models):
            self.current_model_index += 1
            new_model = self.all_models[self.current_model_index]
            self.llm = self._create_llm(new_model)
            print(f"  ⚠️ Switching to fallback model: {new_model}", file=sys.stderr, flush=True)
            return True
        return False

    @property
    def model(self) -> str:
        """Get current model name."""
        return self.all_models[self.current_model_index]

    async def execute_debate(
        self,
        topic: str,
        pro_prompt: str,
        con_prompt: str,
        question: str,
        prd_content: str
    ) -> Tuple[List[Dict[str, Any]], str]:
        """
        Execute a debate using a single structured LLM call.

        Now uses PromptLoader to load the simple mode debate template.
        Falls back to hardcoded prompt if PromptLoader is not available.
        """
        # Get language instruction
        language_instruction = self._get_language_instruction()

        # Load and render debate template if PromptLoader is available
        if self.prompt_loader:
            try:
                debate_prompt = self.prompt_loader.load_with_context(
                    "debate.modes.simple",
                    PromptContext(
                        question=question,
                        topic=topic[:800],
                        prd_content=prd_content[:1500],
                        language=language_instruction,
                        pro_prompt=pro_prompt[:300],
                        con_prompt=con_prompt[:300]
                    )
                )
            except Exception as e:
                logger.warning(f"Failed to load prompt from PromptLoader: {e}, using fallback")
                debate_prompt = self._get_fallback_prompt(question, topic, prd_content, language_instruction, pro_prompt, con_prompt)
        else:
            debate_prompt = self._get_fallback_prompt(question, topic, prd_content, language_instruction, pro_prompt, con_prompt)

        # Try with primary model and fallbacks
        max_model_attempts = len(self.all_models)

        for attempt in range(max_model_attempts):
            try:
                response = await asyncio.to_thread(
                    self.llm.invoke,
                    [HumanMessage(content=debate_prompt)]
                )

                content = response.content.strip()

                # Successfully generated response
                if attempt > 0:
                    print(f"  ✓ Generated using model: {self.model}", file=sys.stderr, flush=True)

                # Parse the response into structured dialogue
                dialogue = self._parse_debate_response(content)

                # Extract winner
                winner = self._extract_winner_from_dialogue(dialogue)

                return dialogue, winner

            except Exception as e:
                error_str = str(e).lower()

                # Check if this is a rate limit error (429)
                is_rate_limit = (
                    "429" in error_str or
                    "rate limit" in error_str or
                    "resource exhausted" in error_str
                )

                if is_rate_limit and self._switch_to_next_model():
                    # Try next model
                    logger.warning(f"Rate limit hit for {self.all_models[self.current_model_index - 1]}, switching to {self.model}")
                    continue
                else:
                    # Not a rate limit or no more models - fail
                    logger.error(f"Simple debate execution failed: {e}")
                    raise

        # All models failed
        raise RuntimeError(f"Failed to generate debate after trying all models")

    def _get_language_instruction(self) -> str:
        """Get language instruction string."""
        language_instructions = {
            "ru": "Вы должны вести дебаты на РУССКОМ языке. All responses must be in Russian.",
            "en": "You must conduct the debate in ENGLISH.",
            "de": "Sie müssen die Debatte auf DEUTSCH führen.",
            "fr": "Vous devez mener le débat en FRANÇAIS.",
            "es": "Debe realizar el debate en ESPAÑOL.",
            "zh": "您必须用中文进行辩论。",
        }

        return language_instructions.get(
            self.language.lower(),
            f"You must conduct the debate in {self.language.upper()}."
        )

    def _get_fallback_prompt(self, question: str, topic: str, prd_content: str,
                             language_instruction: str, pro_prompt: str, con_prompt: str) -> str:
        """Get fallback prompt when PromptLoader is not available."""
        return f"""{language_instruction}

You are simulating a structured debate between two participants on the following topic:

Question: {question}

Topic/Context:
{topic[:800]}

PRD Content:
{prd_content[:1500]}

PRO Position: {pro_prompt[:300]}
CON Position: {con_prompt[:300]}

Please conduct a complete debate with the following structure:

1. PRO Opening Statement
2. CON Opening Statement
3. PRO Rebuttal
4. CON Rebuttal
5. PRO Counter-argument
6. CON Counter-argument
7. PRO Final Argument
8. CON Final Argument
9. JUDGE Verdict

Format each section clearly with speaker labels like "PRO (opening):", "CON (rebuttal):", etc.

At the end, the JUDGE should:
- Evaluate both sides' arguments
- Consider evidence, logic, and persuasiveness
- Declare a clear winner with "WINNER: PRO" or "WINNER: CON"
- Provide brief reasoning

Make arguments realistic, thoughtful, and well-structured."""

    def _parse_debate_response(self, response: str) -> List[Dict[str, Any]]:
        """Parse the LLM response into structured dialogue."""
        dialogue = []
        now = datetime.now(timezone.utc).isoformat()

        # Split by speaker labels
        sections = response.split("PRO (")
        for i, section in enumerate(sections[1:], 1):  # Skip first empty section
            if ")" in section:
                stage_end = section.index(")") + 1
                stage = section[:stage_end - 1].strip()
                content = section[stage_end:].strip()

                # Extract content until next speaker label or end
                for next_speaker in ["CON (", "JUDGE:"]:
                    if next_speaker in content:
                        content = content[:content.index(next_speaker)].strip()
                        break

                if content:
                    dialogue.append({
                        "speaker": "PRO",
                        "content": content,
                        "stage": stage,
                        "timestamp": now,
                        "validated": True
                    })

        # Parse CON sections
        sections = response.split("CON (")
        for section in sections[1:]:
            if ")" in section:
                stage_end = section.index(")") + 1
                stage = section[:stage_end - 1].strip()
                content = section[stage_end:].strip()

                # Extract content until next speaker label
                for next_speaker in ["PRO (", "JUDGE:"]:
                    if next_speaker in content:
                        content = content[:content.index(next_speaker)].strip()
                        break

                if content:
                    dialogue.append({
                        "speaker": "CON",
                        "content": content,
                        "stage": stage,
                        "timestamp": now,
                        "validated": True
                    })

        # Parse JUDGE section
        if "JUDGE:" in response:
            judge_content = response[response.index("JUDGE:") + 7:].strip()
            dialogue.append({
                "speaker": "JUDGE",
                "content": judge_content,
                "stage": "verdict",
                "timestamp": now,
                "validated": True
            })

        # If parsing failed, create simple structure
        if not dialogue:
            dialogue = self._create_fallback_dialogue(response, now)

        return dialogue

    def _create_fallback_dialogue(self, response: str, now: str) -> List[Dict[str, Any]]:
        """Create a simple dialogue if parsing failed."""
        return [
            {
                "speaker": "PRO",
                "content": response[:500],
                "stage": "opening",
                "timestamp": now,
                "validated": True
            },
            {
                "speaker": "CON",
                "content": response[500:1000] if len(response) > 500 else "Counter-argument not available.",
                "stage": "rebuttal",
                "timestamp": now,
                "validated": True
            },
            {
                "speaker": "JUDGE",
                "content": response[-200:] if len(response) > 200 else response,
                "stage": "verdict",
                "timestamp": now,
                "validated": True
            }
        ]

    def _extract_winner_from_dialogue(self, dialogue: List[Dict[str, Any]]) -> str:
        """Extract the winner from the dialogue."""
        for msg in reversed(dialogue):
            if msg["speaker"] == "JUDGE":
                content = msg["content"].upper()
                if "WINNER: PRO" in content:
                    return "PRO"
                elif "WINNER: CON" in content:
                    return "CON"
        return "PRO"  # Default
