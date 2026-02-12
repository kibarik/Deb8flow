import json
import re
from nodes.base_component import BaseComponent
from prompts.judge_prompts import JUDGE_SYSTEM_PROMPT, JUDGE_HUMAN_PROMPT
from configurations.debate_constants import SPEAKER_JUDGE
from debate_state import DebateState
from typing import Dict, Any

class JudgeNode(BaseComponent):
    def __init__(self, llm_config, temperature: float = 0.3):
        super().__init__(llm_config, temperature)
        # Use regular chain instead of structured output
        self.chain = self.create_chain(
            JUDGE_SYSTEM_PROMPT,
            JUDGE_HUMAN_PROMPT + "\n\nRespond with JSON in this exact format:\n{{\n  \"winner\": \"pro\" or \"con\",\n  \"justification\": \"your reasoning\"\n}}"
        )

    def _parse_verdict_response(self, response: str) -> Dict[str, Any]:
        """Parse the LLM response to extract winner and justification."""
        # Try to extract JSON from response
        json_match = re.search(r'\{[^}]*"winner"\s*:\s*"[^"]*"[^}]*"justification"\s*:\s*"[^"]*"[^}]*\}', response, re.DOTALL | re.MULTILINE)
        if json_match:
            try:
                result = json.loads(json_match.group())
                if result.get("winner") in ["pro", "con"]:
                    return result
            except json.JSONDecodeError:
                pass

        # Fallback: try to find winner in text
        winner = "pro"  # default
        justification = response

        # Look for winner patterns
        for speaker in ["pro", "con"]:
            patterns = [
                rf'["\']?winner["\']?\s*[:=]\s*["\']?{speaker}["\']?',
                rf'["\']?winner["\']?\s*[:=]\s*\*\*{speaker}\*\*',
                rf'(?:the\s+)?winner\s+(?:is\s+:)?\s*["\']?{speaker}["\']?',
            ]
            for pattern in patterns:
                if re.search(pattern, response, re.IGNORECASE):
                    winner = speaker
                    break
            if winner == speaker:
                break

        return {
            "winner": winner,
            "justification": justification
        }

    def __call__(self, state: DebateState) -> Dict[str, Any]:
        super().__call__(state)

        debate_topic = state.get("debate_topic")
        messages = state.get("messages", [])

        # Format debate history for the prompt
        debate_history = ""
        for msg in messages:
            speaker = msg.get("speaker", "unknown").upper()
            content = msg.get("content", "")
            debate_history += f"{speaker}: {content}\n\n"

        response = self.execute_chain({
            "debate_topic": debate_topic,
            "debate_history": debate_history
        })

        result = self._parse_verdict_response(response)

        return {
            "judge_verdict": result,
            "messages": messages + [{
                "speaker": SPEAKER_JUDGE,
                "content": f"WINNER: {result['winner'].upper()}\n\nREASON: {result['justification']}",
                "validated": True,
                "stage": "verdict"
            }]
        }
