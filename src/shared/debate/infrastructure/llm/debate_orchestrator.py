"""
LLM-based Debate Orchestrator

This module provides real AI-powered debate execution using LangChain
and OpenAI-compatible APIs.
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder


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
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        language: str = "en"
    ):
        """
        Initialize the debate orchestrator.

        Args:
            model: Model name (e.g., "gpt-4o", "gpt-3.5-turbo")
            temperature: Sampling temperature for creativity
            max_tokens: Maximum tokens per response
            api_key: OpenAI API key (or compatible)
            base_url: Custom API base URL for compatible APIs
            language: Language code for debate output (e.g., "en", "ru", "de")
        """
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

        # Debate history
        self.messages: List[DebateMessage] = []

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
        """Build the context string for the debate."""
        # Language instruction mapping
        language_instructions = {
            "ru": "Вы должны вести дебаты на РУССКОМ языке. All responses must be in Russian.",
            "en": "You must conduct the debate in ENGLISH.",
            "de": "Sie müssen die Debatte auf DEUTSCH führen.",
            "fr": "Vous devez mener le débat en FRANÇAIS.",
            "es": "Debe realizar el debate en ESPAÑOL.",
            "zh": "您必须用中文进行辩论。",
        }

        language_instruction = language_instructions.get(
            self.language.lower(),
            f"You must conduct the debate in {self.language.upper()}."
        )

        return f"""DEBATE CONTEXT:

Question: {question}

Topic/Context: {topic[:500]}

Full PRD Content (for reference):
{prd_content[:2000]}

---

LANGUAGE: {language_instruction}

You are participating in a formal product committee debate. Follow these rules:
1. Stay in character as defined by your role prompt
2. Make specific, evidence-based arguments
3. Reference the actual content from the PRD when relevant
4. Be concise but thorough (aim for 200-400 words per response)
5. Address the other party's arguments directly
6. Maintain professional, constructive tone
"""

    async def _run_opening_statements(self, context: str, pro_prompt: str, con_prompt: str):
        """Run opening statements from both sides."""
        # PRO opening
        pro_response = await self._generate_response(
            system_prompt=pro_prompt,
            human_prompt=f"{context}\n\nPlease present your opening statement arguing FOR this project (PRO position). Focus on why this project should proceed.",
            stage="opening",
            speaker="PRO"
        )
        self.messages.append(DebateMessage("PRO", pro_response, "opening", validated=True))

        # CON opening
        con_response = await self._generate_response(
            system_prompt=con_prompt,
            human_prompt=f"{context}\n\nPlease present your opening statement arguing AGAINST this project (CON position). Focus on concerns, risks, and why this might not succeed.",
            stage="opening",
            speaker="CON"
        )
        self.messages.append(DebateMessage("CON", con_response, "opening", validated=True))

    async def _run_rebuttals(self, context: str, pro_prompt: str, con_prompt: str):
        """Run rebuttal stage."""
        # Get recent messages for context
        recent_context = self._get_recent_context()

        # CON rebuttal (responds to PRO's opening)
        con_rebuttal = await self._generate_response(
            system_prompt=con_prompt,
            human_prompt=f"{context}\n\n{recent_context}\n\nNow provide your rebuttal to the PRO's opening statement. Address their specific points and explain why you disagree.",
            stage="rebuttal",
            speaker="CON"
        )
        self.messages.append(DebateMessage("CON", con_rebuttal, "rebuttal", validated=True))

        # PRO rebuttal
        recent_context = self._get_recent_context()
        pro_rebuttal = await self._generate_response(
            system_prompt=pro_prompt,
            human_prompt=f"{context}\n\n{recent_context}\n\nNow provide your rebuttal to the CON's opening statement and rebuttal. Address their specific concerns.",
            stage="rebuttal",
            speaker="PRO"
        )
        self.messages.append(DebateMessage("PRO", pro_rebuttal, "rebuttal", validated=True))

    async def _run_counter_arguments(self, context: str, pro_prompt: str, con_prompt: str):
        """Run counter-argument stage."""
        recent_context = self._get_recent_context()

        # PRO counter
        pro_counter = await self._generate_response(
            system_prompt=pro_prompt,
            human_prompt=f"{context}\n\n{recent_context}\n\nNow provide a counter-argument. Offer new perspectives or evidence that strengthens your position while directly addressing the opponent's latest points.",
            stage="counter",
            speaker="PRO"
        )
        self.messages.append(DebateMessage("PRO", pro_counter, "counter", validated=True))

        # CON counter
        recent_context = self._get_recent_context()
        con_counter = await self._generate_response(
            system_prompt=con_prompt,
            human_prompt=f"{context}\n\n{recent_context}\n\nNow provide your counter-argument. Offer new perspectives or evidence that strengthens your position while directly addressing the opponent's latest points.",
            stage="counter",
            speaker="CON"
        )
        self.messages.append(DebateMessage("CON", con_counter, "counter", validated=True))

    async def _run_final_arguments(self, context: str, pro_prompt: str, con_prompt: str):
        """Run final argument stage."""
        recent_context = self._get_recent_context()

        # PRO final
        pro_final = await self._generate_response(
            system_prompt=pro_prompt,
            human_prompt=f"{context}\n\n{recent_context}\n\nThis is your final argument. Summarize your strongest points and explain why your position should prevail. Be compelling but fair.",
            stage="final_argument",
            speaker="PRO"
        )
        self.messages.append(DebateMessage("PRO", pro_final, "final_argument", validated=True))

        # CON final
        recent_context = self._get_recent_context()
        con_final = await self._generate_response(
            system_prompt=con_prompt,
            human_prompt=f"{context}\n\n{recent_context}\n\nThis is your final argument. Summarize your strongest points and explain why your position should prevail. Be compelling but fair.",
            stage="final_argument",
            speaker="CON"
        )
        self.messages.append(DebateMessage("CON", con_final, "final_argument", validated=True))

    async def _run_verdict(self, context: str) -> str:
        """Run the judge's verdict and determine winner."""
        recent_context = self._get_recent_context()

        judge_prompt = """You are an IMPARTIAL JUDGE evaluating a product committee debate.

Your task:
1. Review the entire debate above
2. Consider the strength of arguments, evidence presented, and how well each side addressed concerns
3. Provide a verdict

IMPORTANT - Your response MUST follow this exact format:
WINNER: PRO (or CON)

Explanation: [Your reasoning - 2-3 sentences]

Be fair and objective. The winner is whoever made stronger, more convincing arguments."""

        verdict = await self._generate_response(
            system_prompt=judge_prompt,
            human_prompt=f"{context}\n\n{recent_context}\n\nBased on the debate above, provide your verdict.",
            stage="verdict",
            speaker="JUDGE"
        )
        self.messages.append(DebateMessage("JUDGE", verdict, "verdict", validated=True))

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
        model: Optional[str] = None,
        temperature: float = 0.8,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        language: str = "en"
    ):
        """Initialize the simple debate orchestrator."""
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

        This is more efficient than the multi-stage approach while
        still providing realistic results.
        """
        # Language instruction mapping
        language_instructions = {
            "ru": "Вы должны вести дебаты на РУССКОМ языке. All responses must be in Russian.",
            "en": "You must conduct the debate in ENGLISH.",
            "de": "Sie müssen die Debatte auf DEUTSCH führen.",
            "fr": "Vous devez mener le débat en FRANÇAIS.",
            "es": "Debe realizar el debate en ESPAÑOL.",
            "zh": "您必须用中文进行辩论。",
        }

        language_instruction = language_instructions.get(
            self.language.lower(),
            f"You must conduct the debate in {self.language.upper()}."
        )

        debate_prompt = f"""You are simulating a product committee debate about the following question:

QUESTION: {question}

CONTEXT (PRD excerpt): {topic[:800]}

Full PRD Content: {prd_content[:1500]}

---

LANGUAGE: {language_instruction}

You need to generate a realistic debate between two participants:
- PRO (arguing FOR the project): {pro_prompt[:300]}
- CON (arguing AGAINST the project): {con_prompt[:300]}

Generate a debate following this structure:

PRO (opening): [200-300 words arguing for the project]

CON (opening): [200-300 words arguing against the project]

PRO (rebuttal): [150-200 words responding to CON's opening]

CON (rebuttal): [150-200 words responding to PRO's rebuttal]

PRO (final): [100-150 words closing argument]

CON (final): [100-150 words closing argument]

JUDGE: After reviewing both arguments, WINNER: [PRO or CON]. [Brief 2-3 sentence explanation]

Make the arguments specific to the actual PRD content. The PRO should focus on technical feasibility and benefits, while CON should focus on risks, costs, and concerns. The winner should be determined by who made stronger, more convincing arguments.

Begin the debate now:"""

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
