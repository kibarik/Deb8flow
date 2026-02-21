"""
Standard Debate Orchestrator - Multi-turn interactive debates.

This orchestrator executes each debate stage as a separate LLM call,
allowing for deeper, more iterative exchanges than SimpleDebateOrchestrator.
"""

import asyncio
import logging
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
        temperature: float = 0.7,
        max_tokens: int = 5000,  # Allow full responses for proper debate
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        language: str = "en"
    ):
        """Initialize the standard debate orchestrator."""
        self.prompt_loader = prompt_loader
        self.model = model or "gpt-4o"
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.language = language

        # Initialize LLM
        llm_kwargs = {
            "model": self.model,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        if api_key:
            llm_kwargs["api_key"] = api_key
        if base_url:
            llm_kwargs["base_url"] = base_url

        self.llm = ChatOpenAI(**llm_kwargs)

        # Debate state
        self.messages: List[DebateMessage] = []
        self.current_question: str = ""
        self.current_topic: str = ""
        self.current_prd: str = ""

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
            speaker=speaker
        )

        # Store message
        stage_name = stage_prompt_id.split("_")[0]  # "opening", "rebuttal", etc.
        self.messages.append(DebateMessage(
            speaker=speaker,
            content=response,
            stage=stage_name,
            timestamp=datetime.now(timezone.utc).isoformat(),
            validated=True
        ))

        logger.debug(f"{speaker} ({stage_name}): {response[:100]}...")

    async def _execute_judge(self) -> str:
        """Execute the judge's verdict stage."""
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
            return "PRO"
        elif "WINNER: CON" in verdict.upper():
            return "CON"
        else:
            return "PRO"  # Default

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
        speaker: str
    ) -> str:
        """Generate a response using the LLM."""
        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=human_prompt)
            ]

            response = await asyncio.to_thread(
                self.llm.invoke,
                messages
            )

            return response.content.strip()

        except Exception as e:
            logger.error(f"Error generating response for {speaker}: {e}")
            raise
