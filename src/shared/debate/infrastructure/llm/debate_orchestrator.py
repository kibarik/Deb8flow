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
        temperature: float = 0.7,
        max_tokens: int = 1000,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        language: str = "en",
        room_id: Optional[str] = None  # For logging
    ):
        """
        Initialize the debate orchestrator.

        Args:
            prompt_loader: PromptLoader for loading prompts (optional, for backward compatibility)
            model: Model name (e.g., "gpt-4o", "gpt-3.5-turbo")
            temperature: Sampling temperature for creativity
            max_tokens: Maximum tokens per response
            api_key: OpenAI API key (or compatible)
            base_url: Custom API base URL for compatible APIs
            language: Language code for debate output (e.g., "en", "ru", "de")
            room_id: Room identifier for logging (optional)
        """
        self.prompt_loader = prompt_loader  # Store PromptLoader (may be None)
        self.model = model or "gpt-4o"
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.language = language
        self.room_id = room_id or "Debate"

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

        # Debate history
        self.messages: List[DebateMessage] = []
        self._current_stage = 0
        self._total_stages = 9  # 8 debate stages + verdict

    def _log_stage(self, stage_name: str, speaker: str, action: str = "generating"):
        """Log debate stage progress to stderr for realtime feedback."""
        stage_symbols = ["⚪", "🟡", "🟠", "🔴", "🟤", "🔵", "🟣", "⚫", "🟢"]
        symbol = stage_symbols[self._current_stage % len(stage_symbols)]
        print(f"{symbol} [{self.room_id}] Stage {self._current_stage + 1}/{self._total_stages}: {speaker} - {stage_name} ({action})...", file=sys.stderr, flush=True)

    def _log_completed(self, message: str):
        """Log completion message to stderr for realtime feedback."""
        print(f"  ✓ {message}", file=sys.stderr, flush=True)

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
        self._log_stage("Opening Statement", "PRO")
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
        print(f"  ✓ PRO opening completed ({len(pro_response)} chars)", file=sys.stderr, flush=True)

        # CON opening
        self._current_stage = 2
        self._log_stage("Opening Statement", "CON")
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
        self._log_completed(f"CON opening completed ({len(con_response)} chars)")

    async def _run_rebuttals(self, context: str, pro_prompt: str, con_prompt: str):
        """Run rebuttal stage."""
        # Get recent messages for context
        recent_context = self._get_recent_context()

        # CON rebuttal (responds to PRO's opening)
        self._current_stage = 3
        self._log_stage("Rebuttal", "CON")
        con_rebuttal = await self._generate_response(
            system_prompt=con_prompt,
            human_prompt=f"{context}\n\n{recent_context}\n\nNow provide your rebuttal to the PRO's opening statement. Address their specific points and explain why you disagree.",
            stage="rebuttal",
            speaker="CON"
        )
        self.messages.append(DebateMessage("CON", con_rebuttal, "rebuttal", validated=True))
        self._log_completed(f"CON rebuttal completed ({len(con_rebuttal)} chars)")

        # PRO rebuttal
        self._current_stage = 4
        self._log_stage("Rebuttal", "PRO")
        recent_context = self._get_recent_context()
        pro_rebuttal = await self._generate_response(
            system_prompt=pro_prompt,
            human_prompt=f"{context}\n\n{recent_context}\n\nNow provide your rebuttal to the CON's opening statement and rebuttal. Address their specific concerns.",
            stage="rebuttal",
            speaker="PRO"
        )
        self.messages.append(DebateMessage("PRO", pro_rebuttal, "rebuttal", validated=True))
        self._log_completed(f"PRO rebuttal completed ({len(pro_rebuttal)} chars)")

    async def _run_counter_arguments(self, context: str, pro_prompt: str, con_prompt: str):
        """Run counter-argument stage."""
        recent_context = self._get_recent_context()

        # PRO counter
        self._current_stage = 5
        self._log_stage("Counter-argument", "PRO")
        pro_counter = await self._generate_response(
            system_prompt=pro_prompt,
            human_prompt=f"{context}\n\n{recent_context}\n\nNow provide a counter-argument. Offer new perspectives or evidence that strengthens your position while directly addressing the opponent's latest points.",
            stage="counter",
            speaker="PRO"
        )
        self.messages.append(DebateMessage("PRO", pro_counter, "counter", validated=True))
        self._log_completed(f"PRO counter-argument completed ({len(pro_counter)} chars)")

        # CON counter
        self._current_stage = 6
        self._log_stage("Counter-argument", "CON")
        recent_context = self._get_recent_context()
        con_counter = await self._generate_response(
            system_prompt=con_prompt,
            human_prompt=f"{context}\n\n{recent_context}\n\nNow provide a counter-argument. Offer new perspectives or evidence that strengthens your position while directly addressing the opponent's latest points.",
            stage="counter",
            speaker="CON"
        )
        self.messages.append(DebateMessage("CON", con_counter, "counter", validated=True))
        self._log_completed(f"CON counter-argument completed ({len(con_counter)} chars)")

    async def _run_final_arguments(self, context: str, pro_prompt: str, con_prompt: str):
        """Run final argument stage."""
        recent_context = self._get_recent_context()

        # PRO final
        self._current_stage = 7
        self._log_stage("Final Argument", "PRO")
        pro_final = await self._generate_response(
            system_prompt=pro_prompt,
            human_prompt=f"{context}\n\n{recent_context}\n\nThis is your final argument. Summarize your strongest points and explain why your position should prevail. Be compelling but fair.",
            stage="final_argument",
            speaker="PRO"
        )
        self.messages.append(DebateMessage("PRO", pro_final, "final_argument", validated=True))
        self._log_completed(f"PRO final completed ({len(pro_final)} chars)")

        # CON final
        self._current_stage = 8
        self._log_stage("Final Argument", "CON")
        recent_context = self._get_recent_context()
        con_final = await self._generate_response(
            system_prompt=con_prompt,
            human_prompt=f"{context}\n\n{recent_context}\n\nThis is your final argument. Summarize your strongest points and explain why your position should prevail. Be compelling but fair.",
            stage="final_argument",
            speaker="CON"
        )
        self.messages.append(DebateMessage("CON", con_final, "final_argument", validated=True))
        self._log_completed(f"CON final completed ({len(con_final)} chars)")

    async def _run_verdict(self, context: str) -> str:
        """Run the judge's verdict using PromptLoader."""
        recent_context = self._get_recent_context()

        # Load judge template
        question = context.split("Question:")[-1].strip() if "Question:" in context else ""

        self._current_stage = 9
        self._log_stage("Verdict", "JUDGE")

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
        self._log_completed(f"JUDGE verdict completed ({len(verdict)} chars)")

        # Extract winner from verdict
        if "WINNER: PRO" in verdict.upper():
            return "PRO"
        elif "WINNER: CON" in verdict.upper():
            return "CON"
        else:
            # Try to determine from context
            if "pro wins" in verdict.lower() or "proposition wins" in verdict.lower():
                return "PRO"
            elif "con wins" in verdict.lower() or "opposition wins" in verdict.lower():
                return "CON"
            # Default to PRO if unclear
            return "PRO"

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

            content = response.content.strip()
            logger.debug(f"{speaker} ({stage}): {content[:100]}...")

            return content

        except Exception as e:
            logger.error(f"Error generating response for {speaker} at {stage}: {e}")
            raise


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
        temperature: float = 0.8,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        language: str = "en"
    ):
        """Initialize the simple debate orchestrator."""
        self.prompt_loader = prompt_loader  # Store PromptLoader (may be None)
        self.model = model or "gpt-4o"
        self.temperature = temperature
        self.language = language

        llm_kwargs = {
            "model": self.model,
            "temperature": temperature,
            "max_tokens": 1500,
        }

        if api_key:
            llm_kwargs["api_key"] = api_key
        if base_url:
            llm_kwargs["base_url"] = base_url

        self.llm = ChatOpenAI(**llm_kwargs)

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

        try:
            response = await asyncio.to_thread(
                self.llm.invoke,
                [HumanMessage(content=debate_prompt)]
            )

            content = response.content.strip()

            # Parse the response into structured dialogue
            dialogue = self._parse_debate_response(content)

            # Extract winner
            winner = self._extract_winner_from_dialogue(dialogue)

            return dialogue, winner

        except Exception as e:
            logger.error(f"Simple debate execution failed: {e}")
            raise

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
