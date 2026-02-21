"""
Standard Debate Orchestrator - Multi-turn interactive debates.

This orchestrator executes each debate stage as a separate LLM call,
allowing for deeper, more iterative exchanges than SimpleDebateOrchestrator.
"""

import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timezone

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from ...application.prompt_loader import PromptLoader, PromptContext
from ...domain.entities import DebateMessage


logger = logging.getLogger(__name__)


class StandardDebateOrchestrator:
    """
    Multi-turn debate orchestrator with separate LLM calls per stage.

    This orchestrator provides higher quality debates by:
    - Executing each stage independently
    - Accumulating full conversation context
    - Allowing each response to build on all previous exchanges
    - Providing richer context to the judge

    Trade-offs:
    - More API calls (9 vs 1 per debate)
    - Slower execution time
    - Higher cost
    - Better debate quality and depth
    """

    DEBATE_STAGES = [
        "opening_pro",
        "opening_con",
        "rebuttal_con",
        "rebuttal_pro",
        "counter_pro",
        "counter_con",
        "final_pro",
        "final_con"
    ]

    def __init__(
        self,
        prompt_loader: PromptLoader,
        model: Optional[str] = None,
        fallback_models: Optional[list[str]] = None,
        temperature: float = 0.7,
        max_tokens: int = 5000,  # Allow full responses for proper debate
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        language: str = "en",
        room_id: Optional[str] = None,  # For logging
        json_output_path: Optional[Path] = None  # For progressive saving
    ):
        """Initialize the standard debate orchestrator."""
        self.prompt_loader = prompt_loader
        self.primary_model = model or "gpt-4o"
        self.fallback_models = fallback_models or []
        self.all_models = [self.primary_model] + self.fallback_models
        self.current_model_index = 0  # Start with primary model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.language = language
        self.api_key = api_key
        self.base_url = base_url
        self.room_id = room_id or "Debate"
        self.json_output_path = json_output_path

        # Initialize LLM
        self.llm = self._create_llm(self.primary_model)

        # Debate state
        self.messages: List[DebateMessage] = []
        self.current_question: str = ""
        self.current_topic: str = ""
        self.current_prd: str = ""
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
        Execute a full debate with separate LLM calls per stage.

        Args:
            topic: The debate topic/context
            pro_prompt: System prompt for PRO debater
            con_prompt: System prompt for CON debater
            question: The specific question to debate
            prd_content: Full PRD content for context

        Returns:
            Tuple of (dialogue as list of dicts, winner)
        """
        # Initialize state
        self.messages = []
        self.current_question = question
        self.current_topic = topic
        self.current_prd = prd_content

        try:
            # Execute each stage
            await self._execute_stage("opening_pro", pro_prompt, "PRO")
            await self._execute_stage("opening_con", con_prompt, "CON")
            await self._execute_stage("rebuttal_con", con_prompt, "CON")
            await self._execute_stage("rebuttal_pro", pro_prompt, "PRO")
            await self._execute_stage("counter_pro", pro_prompt, "PRO")
            await self._execute_stage("counter_con", con_prompt, "CON")
            await self._execute_stage("final_pro", pro_prompt, "PRO")
            await self._execute_stage("final_con", con_prompt, "CON")

            # Judge verdict
            winner = await self._execute_judge()

            return [msg.to_dict() for msg in self.messages], winner

        except Exception as e:
            logger.error(f"Standard debate execution failed: {e}")
            raise

    async def _execute_stage(
        self,
        stage_prompt_id: str,
        role_prompt: str,
        speaker: str
    ) -> None:
        """
        Execute a single debate stage.

        Args:
            stage_prompt_id: Prompt ID for this stage (e.g., "opening_pro")
            role_prompt: System prompt for the speaker's role
            speaker: "PRO" or "CON"
        """
        # Increment stage counter
        self._current_stage += 1
        stage_name = stage_prompt_id.split("_")[0]  # "opening", "rebuttal", etc.

        # Build context with full conversation history
        context = self._build_context_for_stage(speaker)

        # Load stage prompt
        try:
            stage_prompt = self.prompt_loader.load_with_context(
                f"debate.stages.{stage_prompt_id}",
                context
            )
        except KeyError:
            logger.warning(f"Stage prompt {stage_prompt_id} not found, using fallback")
            stage_prompt = self._get_fallback_stage_prompt(stage_prompt_id, context)

        # Generate response
        response = await self._generate_response(
            system_prompt=role_prompt,
            human_prompt=stage_prompt,
            stage=stage_name,
            speaker=speaker
        )

        # Store message
        self.messages.append(DebateMessage(
            speaker=speaker,
            content=response,
            stage=stage_name,
            timestamp=datetime.now(timezone.utc).isoformat(),
            validated=True
        ))

        logger.debug(f"{speaker} ({stage_name}): {response[:100]}...")

        # Save progressive state after each stage
        await self._save_progressive_state()

    async def _execute_judge(self) -> str:
        """Execute the judge's verdict stage."""
        # Increment stage counter for verdict
        self._current_stage = 9

        # Build full context for judge
        context = self._build_context_for_stage("JUDGE")

        # Load judge prompt
        try:
            judge_prompt = self.prompt_loader.load_with_context(
                "debate.judge",
                context
            )
        except KeyError:
            logger.warning("Judge prompt not found, using fallback")
            judge_prompt = self._get_fallback_judge_prompt(context)

        # Generate verdict
        verdict = await self._generate_response(
            system_prompt=judge_prompt,
            human_prompt="Based on the debate above, provide your verdict.",
            stage="verdict",
            speaker="JUDGE"
        )

        self.messages.append(DebateMessage(
            speaker="JUDGE",
            content=verdict,
            stage="verdict",
            timestamp=datetime.now(timezone.utc).isoformat(),
            validated=True
        ))

        # Extract winner
        if "WINNER: PRO" in verdict.upper():
            winner = "PRO"
        elif "WINNER: CON" in verdict.upper():
            winner = "CON"
        else:
            winner = "PRO"  # Default

        # Save final state with winner
        await self._save_progressive_state(winner=winner)

        return winner

    def _build_context_for_stage(self, speaker: str) -> PromptContext:
        """
        Build context for a stage with full conversation history.

        In standard mode, we provide the ENTIRE conversation history,
        not just recent messages. This enables deeper, more contextual
        responses that reference earlier arguments.
        """
        # Build full conversation history
        conversation_parts = []
        for msg in self.messages:
            conversation_parts.append(
                f"{msg.speaker} ({msg.stage}): {msg.content}"
            )

        full_history = "\n\n".join(conversation_parts)

        # Create context with all available information
        return PromptContext(
            question=self.current_question,
            topic=self.current_topic[:500],
            prd_content=self.current_prd[:2000],
            recent_context=full_history,  # FULL history, not just recent
            language=self.language,
            pro_prompt="",  # Not needed for stage prompts
            con_prompt=""
        )

    def _get_fallback_stage_prompt(self, stage_id: str, context: PromptContext) -> str:
        """Fallback stage prompt when PromptLoader fails."""
        stage_name = stage_id.split("_")[0]
        return f"""{context.language}

You are participating in a debate on the following topic:

Question: {context.question}

Topic: {context.topic}

PRD Content:
{context.prd_content}

Previous conversation:
{context.recent_context}

This is the {stage_name} stage. Provide your argument focusing on:
- Opening: Introduce your main position
- Rebuttal: Address opponent's points directly
- Counter: Offer new evidence/perspectives
- Final: Summarize your strongest points

Be concise but thorough."""

    def _get_fallback_judge_prompt(self, context: PromptContext) -> str:
        """Fallback judge prompt when PromptLoader fails."""
        return f"""{context.language}

You are the judge for this debate.

Question: {context.question}

Full debate transcript:
{context.recent_context}

Provide your verdict with:
1. Analysis of both sides' arguments
2. A clear declaration of "WINNER: PRO" or "WINNER: CON"
3. Brief reasoning for your decision"""

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

                # Get stage display name (uppercase, replace final_argument with FINAL)
                stage_display = stage.upper().replace("FINAL_ARGUMENT", "FINAL") if stage else stage

                # Log request tokens BEFORE API call
                stage_symbols = ["⚪", "🟡", "🟠", "🔴", "🟤", "🔵", "🟣", "⚫", "🟢"]
                symbol = stage_symbols[self._current_stage % len(stage_symbols)]
                print(f"{symbol} [{self.room_id}] Stage {self._current_stage}/{self._total_stages} - {speaker} - {stage_display} - {self.model} - {estimated_req_tokens} req/tokens", file=sys.stderr, flush=True)

                response = await asyncio.to_thread(
                    self.llm.invoke,
                    messages
                )

                content = response.content.strip()
                logger.debug(f"{speaker}: {content[:100]}...")

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
                print(f"{symbol} [{self.room_id}] Stage {self._current_stage}/{self._total_stages} - {speaker} - {stage_display} - {self.model} - {res_tokens} res/tokens", file=sys.stderr, flush=True)

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
                    logger.error(f"Error generating response for {speaker}: {e}")
                    raise

        # All models failed
        raise RuntimeError(f"Failed to generate response for {speaker} after trying all models")
