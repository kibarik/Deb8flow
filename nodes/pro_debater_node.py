from nodes.base_component import BaseComponent
from debate_state import DebateState
from typing import Dict, Any
from prompts.pro_debater_prompts import (
    SYSTEM_PROMPT,
    OPENING_HUMAN_PROMPT,
    COUNTER_HUMAN_PROMPT,
    OPENING_RETRY_HUMAN_PROMPT,
    COUNTER_RETRY_HUMAN_PROMPT,
    DOCUMENT_OPENING_HUMAN_PROMPT,
    DOCUMENT_COUNTER_HUMAN_PROMPT
)
from utils import create_debate_message, get_debate_history
from configurations.debate_constants import (
    STAGE_OPENING,
    STAGE_COUNTER,
    SPEAKER_PRO,
    SPEAKER_CON
)

class ProDebaterNode(BaseComponent):
    def __init__(self, llm_config, temperature: float = 0.7):
        super().__init__(llm_config, temperature)
        # Create chains dynamically for each call to avoid variable caching issues
        self.llm_config = llm_config
        self.temperature = temperature
        self.chains_initialized = False

    def _ensure_chains_initialized(self):
        """Initialize chains lazily when first needed."""
        if not self.chains_initialized:
            self.opening_chain = self.create_chain(SYSTEM_PROMPT, OPENING_HUMAN_PROMPT)
            self.opening_retry_chain = self.create_chain(SYSTEM_PROMPT, OPENING_RETRY_HUMAN_PROMPT)
            self.counter_chain = self.create_chain(SYSTEM_PROMPT, COUNTER_HUMAN_PROMPT)
            self.counter_retry_chain = self.create_chain(SYSTEM_PROMPT, COUNTER_RETRY_HUMAN_PROMPT)
            # Document-aware chains - created separately to avoid variable overlap
            self.document_opening_chain = self.create_chain(SYSTEM_PROMPT, DOCUMENT_OPENING_HUMAN_PROMPT)
            self.document_counter_chain = self.create_chain(SYSTEM_PROMPT, DOCUMENT_COUNTER_HUMAN_PROMPT)
            self.chains_initialized = True

    def __call__(self, state: DebateState) -> Dict[str, Any]:
        super().__call__(state)
        self._ensure_chains_initialized()

        debate_topic = state.get("debate_topic")
        messages = state.get("messages", [])
        stage = state.get("stage")
        speaker = state.get("speaker")
        document_context = state.get("document_context")

        # Check if retrying (last message was by pro and not validated)
        last_msg = messages[-1] if messages else None
        retrying = last_msg and last_msg["speaker"] == SPEAKER_PRO and not last_msg["validated"]

        if stage == STAGE_OPENING and speaker == SPEAKER_PRO:
            if document_context and document_context.strip():
                # Use document-aware prompt
                chain = self.opening_retry_chain if retrying else self.document_opening_chain
                result = chain.invoke({
                    "debate_topic": debate_topic,
                    "document_text": document_context
                })
            else:
                chain = self.opening_retry_chain if retrying else self.opening_chain
                result = chain.invoke({
                    "debate_topic": debate_topic
                })
        elif stage == STAGE_COUNTER and speaker == SPEAKER_PRO:
            opponent_msg = self._get_last_message_by(SPEAKER_CON, messages)
            debate_history = get_debate_history(messages)
            if document_context and document_context.strip():
                # Use document-aware prompt
                chain = self.counter_retry_chain if retrying else self.document_counter_chain
                result = chain.invoke({
                    "debate_topic": debate_topic,
                    "opponent_statement": opponent_msg,
                    "debate_history": debate_history,
                    "document_text": document_context
                })
            else:
                chain = self.counter_retry_chain if retrying else self.counter_chain
                result = chain.invoke({
                    "debate_topic": debate_topic,
                    "opponent_statement": opponent_msg,
                    "debate_history": debate_history
                })
        else:
            raise ValueError(f"Unknown turn for ProDebater: stage={stage}, speaker={speaker}")
        new_message = create_debate_message(speaker=SPEAKER_PRO, content=result, stage=stage)
        self.log_debate_event(
            f"[bold]{stage.upper()}[/] {'🔁 (Retry)' if retrying else ''}\n"
            f"{result}\n",
            prefix="PRO"
        )

        return {
            "messages": messages + [new_message]
        }

    def _get_last_message_by(self, speaker_prefix, messages):
        for m in reversed(messages):
            if m.get("speaker") == speaker_prefix:
                return m["content"]
        return ""
