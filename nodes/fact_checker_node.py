import textwrap
import json
import re
from typing import Dict, Any
from debate_state import DebateState
from configurations.debate_constants import SPEAKER_PRO, SPEAKER_CON
from configurations.llm_config import requesty_llm_config_map, LLMConfig
from utils import create_debate_message

from nodes.base_component import BaseComponent


class FactCheckNode(BaseComponent):
    def __init__(self, llm_config: LLMConfig = None):
        # Use Requesty config by default
        if llm_config is None:
            llm_config = requesty_llm_config_map["deepseek-chat"]
        super().__init__(llm_config=llm_config, temperature=0.0)

    def _parse_fact_check_response(self, response: str) -> Dict[str, str]:
        """Parse the LLM response to extract binary_score and justification."""
        # Try to extract JSON from response
        json_match = re.search(r'\{[^}]*"binary_score"\s*:\s*"[^"]*"[^}]*"justification"\s*:\s*"[^"]*"[^}]*\}', response, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass

        # Fallback: parse line by line
        binary_score = "yes"  # default
        justification = response

        # Look for score patterns
        score_patterns = [
            r'(?:binary_score|score)\s*[:=]\s*["\']?([a-z]+)["\']?',
            r'(?:binary_score|score)\s*[:=]\s*\*\*([a-z]+)\*\*',
        ]
        for pattern in score_patterns:
            match = re.search(pattern, response, re.IGNORECASE)
            if match:
                score = match.group(1).lower()
                if score in ['yes', 'no']:
                    binary_score = score
                    break

        return {
            "binary_score": binary_score,
            "justification": justification
        }

    def __call__(self, state: DebateState) -> Dict[str, Any]:
        messages = state.get("messages", [])
        last_message = messages[-1]
        claim = last_message["content"]
        speaker = last_message["speaker"]
        stage = state["stage"]

        self.log_debate_event(
            f"Fact-Checking {speaker.upper()}'s {stage.title()} Claim:\n"
            f"{textwrap.shorten(claim, width=150, placeholder='...')}",
            prefix="FACT"
        )

        # Create regular chain (not structured output)
        chain = self.create_chain(
            system_template="You are a fact-checker for a debate. Analyze claims and determine if they contain verifiable factual information that should be checked.",
            human_template=(
                "Consider the following statement from a debate.\n"
                "If the statement contains numbers, statistics, or specific references to studies, "
                "assess whether these claims appear plausible and accurate.\n\n"
                "Statement:\n\"{claim}\"\n\n"
                "Provide your response in this exact format:\n"
                "{{\n"
                '  "binary_score": "yes" or "no",\n'
                '  "justification": "your reasoning here"\n'
                "}}\n\n"
                "Guidelines:\n"
                '- Use "yes" if the statement is plausible or has no specific factual claims\n'
                '- Use "no" if it contains suspicious numbers or questionable claims\n'
                "- If the statement doesn't contain references to studies or numbers, "
                'consider it successfully fact-checked with a "yes" score.'
            )
        )

        response = self.execute_chain({"claim": claim})
        result = self._parse_fact_check_response(response)

        if result["binary_score"] == "yes":
            self.log_debate_event(f"Verified\n{result['justification']}", prefix="FACT")
            last_message["validated"] = True
            return {
                "messages": messages,
                "validated": True
            }
        else:
            self.log_debate_event(
                f"Disputed\nReason: {result['justification']}\n"
                f"{speaker.upper()} now has {state.get(f'times_{speaker}_fact_checked', 0) + 1}/3 failed checks",
                prefix="FACT"
            )
            fact_checker_msg = create_debate_message(
                speaker="fact_checker",
                content=result["binary_score"],
                stage=state["stage"]
            )
            if speaker == SPEAKER_PRO:
                return {
                    "messages": messages + [fact_checker_msg],
                    "validated": False,
                    "times_pro_fact_checked": state.get("times_pro_fact_checked", 0) + 1,
                }
            elif speaker == SPEAKER_CON:
                return {
                    "messages": messages + [fact_checker_msg],
                    "validated": False,
                    "times_con_fact_checked": state.get("times_con_fact_checked", 0) + 1,
                }
