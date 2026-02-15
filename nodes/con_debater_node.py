from nodes.base_component import BaseComponent
from debate_state import DebateState
from typing import Dict, Any, Optional
from langchain_core.runnables.base import RunnableSequence
from configurations.debate_constants import (
    STAGE_REBUTTAL, STAGE_FINAL_ARGUMENT,
    SPEAKER_CON, SPEAKER_PRO
)
from prompts.con_debater_prompts import (
    SYSTEM_PROMPT,
    REBUTTAL_HUMAN_PROMPT,
    REBUTTAL_RETRY_HUMAN_PROMPT,
    FINAL_ARGUMENT_HUMAN_PROMPT,
    FINAL_ARGUMENT_RETRY_HUMAN_PROMPT,
    DOCUMENT_REBUTTAL_HUMAN_PROMPT,
    DOCUMENT_FINAL_ARGUMENT_HUMAN_PROMPT
)
from utils import create_debate_message, get_debate_history

class ConDebaterNode(BaseComponent):
    def __init__(self, llm_config, temperature: float = 0.7):
        super().__init__(llm_config, temperature)
        self.base_system_prompt = SYSTEM_PROMPT
        self._last_custom_prompt = None
        self.chains_initialized = False
        # Note: CON node creates chains in __init__, not lazily
        # We'll update this pattern to support custom prompts

    def _create_chain_with_custom_prompt(
        self,
        custom_prompt: Optional[str],
        base_system_prompt: str,
        human_prompt: str
    ) -> RunnableSequence:
        """Create a chain with optional custom prompt injection.

        Args:
            custom_prompt: Optional custom prompt content to inject
            base_system_prompt: Base system prompt
            human_prompt: Human prompt template

        Returns:
            RunnableSequence chain for LLM invocation
        """
        if custom_prompt:
            # Prepend custom prompt to base system prompt
            enhanced_system_prompt = f"{custom_prompt}\n\n{base_system_prompt}"
        else:
            enhanced_system_prompt = base_system_prompt

        return self.create_chain(enhanced_system_prompt, human_prompt)

    def _init_chains_with_custom_prompt(self, custom_prompt: Optional[str]):
        """Initialize or re-create all chains with custom prompt injection."""
        # Base system prompt
        base_system_prompt = self.base_system_prompt

        # Log once when using custom prompt
        if custom_prompt:
            self.log_debate_event(f"Using custom CON prompt ({len(custom_prompt)} chars injected)", prefix="CON")

        # Create all chains with custom prompt injection
        self.rebuttal_chain = self._create_chain_with_custom_prompt(
            custom_prompt, base_system_prompt, REBUTTAL_HUMAN_PROMPT
        )
        self.rebuttal_retry_chain = self._create_chain_with_custom_prompt(
            custom_prompt, base_system_prompt, REBUTTAL_RETRY_HUMAN_PROMPT
        )
        self.final_argument_chain = self._create_chain_with_custom_prompt(
            custom_prompt, base_system_prompt, FINAL_ARGUMENT_HUMAN_PROMPT
        )
        self.final_argument_retry_chain = self._create_chain_with_custom_prompt(
            custom_prompt, base_system_prompt, FINAL_ARGUMENT_RETRY_HUMAN_PROMPT
        )
        # Document-aware chains
        self.document_rebuttal_chain = self._create_chain_with_custom_prompt(
            custom_prompt, base_system_prompt, DOCUMENT_REBUTTAL_HUMAN_PROMPT
        )
        self.document_final_argument_chain = self._create_chain_with_custom_prompt(
            custom_prompt, base_system_prompt, DOCUMENT_FINAL_ARGUMENT_HUMAN_PROMPT
        )
        self.chains_initialized = True

    def __call__(self, state: DebateState) -> Dict[str, Any]:
        super().__call__(state)

        # Extract custom prompt from state
        con_custom_prompt = state.get("con_custom_prompt")

        # Initialize or re-create chains with custom prompt
        # Re-initialize if chains aren't initialized OR if custom prompt has changed
        if not self.chains_initialized or con_custom_prompt != getattr(self, "_last_custom_prompt", None):
            self._init_chains_with_custom_prompt(con_custom_prompt)
            self._last_custom_prompt = con_custom_prompt

        debate_topic = state["debate_topic"]
        messages = state.get("messages", [])
        stage = state["stage"]
        speaker = state["speaker"]
        document_context = state.get("document_context")

        # Determine if the CON agent is retrying due to a failed fact check
        last_msg = messages[-1] if messages else None
        retrying = last_msg and last_msg["speaker"] == SPEAKER_CON and not last_msg["validated"]

        if stage == STAGE_REBUTTAL and speaker == SPEAKER_CON:
            opponent_msg = self._get_last_message_by(SPEAKER_PRO, messages)
            if document_context and document_context.strip():
                # Use document-aware prompt
                chain = self.rebuttal_retry_chain if retrying else self.document_rebuttal_chain
                result = chain.invoke({
                    "debate_topic": debate_topic,
                    "opponent_statement": opponent_msg,
                    "document_text": document_context
                })
            else:
                chain = self.rebuttal_retry_chain if retrying else self.rebuttal_chain
                result = chain.invoke({
                    "debate_topic": debate_topic,
                    "opponent_statement": opponent_msg
                })

        elif stage == STAGE_FINAL_ARGUMENT and speaker == SPEAKER_CON:
            debate_history = get_debate_history(messages)
            if document_context and document_context.strip():
                # Use document-aware prompt
                chain = self.final_argument_retry_chain if retrying else self.document_final_argument_chain
                result = chain.invoke({
                    "debate_topic": debate_topic,
                    "debate_history": debate_history,
                    "document_text": document_context
                })
            else:
                chain = self.final_argument_retry_chain if retrying else self.final_argument_chain
                result = chain.invoke({
                    "debate_topic": debate_topic,
                    "debate_history": debate_history
                })

        else:
            raise ValueError(f"Unknown turn for ConDebater: stage={stage}, speaker={speaker}")

        new_message = create_debate_message(speaker=SPEAKER_CON, content=result, stage=stage)
        self.log_debate_event(
            f"[bold]{stage.upper()}[/] {'🔁 (Retry)' if retrying else ''}\n"
            f"{result}\n",
            prefix="CON"
        )
        return {
            "messages": messages + [new_message]
        }

    def _get_last_message_by(self, speaker: str, messages: list) -> str:
        for m in reversed(messages):
            if m["speaker"] == speaker:
                return m["content"]
        return ""
